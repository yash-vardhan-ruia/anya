"""
CareVoice AI Hospital Platform - Twilio to Gemini Multimodal Live WebSocket Bridge.

Maintains bidirectional WebSocket streams:
1. Receives audio packets (g.711 u-law) from Twilio, streams them to Gemini.
2. Receives output audio from Gemini, packages it as Twilio media event packets, and streams it back.
3. Coordinates real-time tool execution and state-aware FSM prompt updates on conversational milestones.
"""

import asyncio
import base64
import audioop
import datetime
import json
import random
import uuid
import structlog
import websockets
from sqlalchemy import select
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config import settings
from app.core.constants import ConversationState, CallStatus
from app.database import async_session_factory
from app.models.call_session import CallSession
from app.voice.session_manager import VoiceSessionManager
from app.voice.orchestrator import VoiceOrchestrator
from app.voice.tools import REALTIME_TOOLS
from app.voice.tool_executor import execute_tool
from app.voice.prompts import get_state_prompt

logger = structlog.get_logger(__name__)
router = APIRouter()


class DashboardConnectionManager:
    """Manages general administrator dashboard WebSocket connections to broadcast telemetry."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Admin dashboard telemetry client connected", count=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("Admin dashboard telemetry client disconnected", count=len(self.active_connections))

    async def broadcast(self, message: dict) -> None:
        """Send JSON telemetry payload to all active dashboard clients."""
        failed_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                failed_connections.append(connection)
        for conn in failed_connections:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


dashboard_manager = DashboardConnectionManager()


@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket) -> None:
    """FastAPI WebSocket endpoint for admin dashboard bento stream listeners."""
    await dashboard_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for standard heartbeats if any
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)


@router.websocket("/ws/voice/{call_sid}")
async def voice_websocket_bridge(
    websocket: WebSocket,
    call_sid: str,
    from_phone: str = "",
    to_phone: str = "",
):
    """Establishes bidirectional voice stream bridging Twilio and Gemini Multimodal Live API."""
    await websocket.accept()
    logger.info("Twilio WebSocket connection established for live stream", call_sid=call_sid, caller=from_phone)

    # Initialize a new booking session memory in Redis
    session_data = await VoiceSessionManager.update_session(call_sid, {
        "phone": from_phone or call_sid
    })

    # Save CallSession to database on call start
    start_time = datetime.datetime.now(datetime.timezone.utc)
    async with async_session_factory() as db:
        try:
            call_session = CallSession(
                twilio_call_sid=call_sid,
                from_number=from_phone or "Unknown",
                status=CallStatus.IN_PROGRESS,
                started_at=start_time,
                conversation_state=ConversationState.GREETING,
                transcript="",
            )
            db.add(call_session)
            await db.commit()
            logger.info("Persisted CallSession to database", call_sid=call_sid)
        except Exception as e:
            logger.error("Failed to create CallSession record", error=str(e), call_sid=call_sid)

    # Broadcast call start event to admin telemetry dashboard
    await dashboard_manager.broadcast({
        "type": "call_start",
        "payload": {
            "id": call_sid,
            "callerId": "unknown",
            "callerName": "Guest Patient",
            "callerPhone": from_phone or "Unknown",
            "agentId": "anya",
            "agentName": "Anya AI",
            "type": "inbound",
            "status": "active",
            "intent": "Hospital Triage & Booking",
            "duration": 0,
            "startedAt": start_time.isoformat(),
            "sentiment": "neutral",
            "aiConfidence": 0.95,
            "department": "Triage",
        }
    })

    # Use v1alpha endpoint for Gemini Live API
    gemini_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={settings.GEMINI_API_KEY}"

    try:
        async with websockets.connect(gemini_url) as gemini_ws:
            logger.info("Connected to Gemini Multimodal Live API WebSocket", call_sid=call_sid)

            # Establish initial session configurations for Anya
            initial_state = session_data.get("current_state", ConversationState.GREETING.value)
            initial_prompt = get_state_prompt(initial_state, session_data)

            # Convert tools to Gemini schema format
            gemini_tools = [
                {
                    "functionDeclarations": [
                        {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": {
                                "type": "OBJECT",
                                "properties": {
                                    k: {
                                        "type": v["type"].upper(),
                                        "description": v.get("description", "")
                                    }
                                    for k, v in tool["parameters"]["properties"].items()
                                },
                                "required": tool["parameters"].get("required", [])
                            }
                        }
                        for tool in REALTIME_TOOLS
                    ]
                }
            ]

            # Setup configuration for Gemini Live API
            setup_msg = {
                "setup": {
                    "model": "models/gemini-2.0-flash-exp",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": "Aoede" # Aoede is a warm female voice matching Anya's persona
                                }
                            }
                        }
                    },
                    "systemInstruction": {
                        "parts": [
                            {
                                "text": initial_prompt
                            }
                        ]
                    },
                    "tools": gemini_tools
                }
            }
            await gemini_ws.send(json.dumps(setup_msg))
            logger.info("Sent initial setup configuration to Gemini", call_sid=call_sid)

            # Wait for setup completion acknowledgment
            setup_resp = await gemini_ws.recv()
            logger.info("Received setup response from Gemini", response=str(setup_resp)[:200], call_sid=call_sid)

            stream_sid = None
            audio_in_state = None
            audio_out_state = None

            async def twilio_to_gemini():
                nonlocal stream_sid, audio_in_state
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        event = data.get("event")

                        if event == "start":
                            stream_sid = data["start"]["streamSid"]
                            logger.info("Twilio media stream starting", stream_sid=stream_sid, call_sid=call_sid)
                        
                        elif event == "media":
                            payload = data["media"]["payload"]
                            try:
                                # Decode G.711 u-law from Twilio (8kHz)
                                ulaw_bytes = base64.b64decode(payload)
                                # Convert to linear 16-bit PCM (8kHz)
                                pcm_8khz = audioop.ulaw2lin(ulaw_bytes, 2)
                                # Resample to 16kHz PCM for Gemini
                                pcm_16khz, audio_in_state = audioop.ratecv(
                                    pcm_8khz, 2, 1, 8000, 16000, audio_in_state
                                )
                                # Base64 encode PCM and stream to Gemini
                                pcm_base64 = base64.b64encode(pcm_16khz).decode("utf-8")
                                await gemini_ws.send(json.dumps({
                                    "realtimeInput": {
                                        "mediaChunks": [
                                            {
                                                "mimeType": "audio/pcm;rate=16000",
                                                "data": pcm_base64
                                            }
                                        ]
                                    }
                                }))
                            except Exception as audio_err:
                                logger.error("Error transcoding input audio to Gemini", error=str(audio_err), call_sid=call_sid)

                        elif event == "stop":
                            logger.info("Twilio media stream stopped", call_sid=call_sid)
                            break
                except WebSocketDisconnect:
                    logger.info("Twilio stream WebSocket disconnected", call_sid=call_sid)
                except Exception as e:
                    logger.error("Error in Twilio to Gemini receiver", error=str(e), call_sid=call_sid)

            async def gemini_to_twilio():
                nonlocal stream_sid, audio_out_state
                try:
                    async for message in gemini_ws:
                        event_data = json.loads(message)
                        
                        # Handle serverContent (Audio output, user transcription, interrupted)
                        if "serverContent" in event_data:
                            server_content = event_data["serverContent"]
                            
                            # 1. Check for user interruption (Barge-in)
                            if server_content.get("interrupted") and stream_sid:
                                logger.info("User interrupted the model (Barge-in). Clearing Twilio buffer.", call_sid=call_sid)
                                await websocket.send_text(json.dumps({
                                    "event": "clear",
                                    "streamSid": stream_sid
                                }))
                                # Reset output resampling filter state to prevent popping/clicking on resumption
                                audio_out_state = None

                            # 2. Check for audio/text model output
                            model_turn = server_content.get("modelTurn")
                            if model_turn:
                                for part in model_turn.get("parts", []):
                                    # Handle audio output (inlineData)
                                    if "inlineData" in part:
                                        inline_data = part["inlineData"]
                                        pcm_24khz_base64 = inline_data.get("data")
                                        if stream_sid and pcm_24khz_base64:
                                            # Decode Gemini's 24kHz PCM output
                                            pcm_24khz_bytes = base64.b64decode(pcm_24khz_base64)
                                            # Resample 24kHz to 8kHz PCM for Twilio
                                            pcm_8khz_bytes, audio_out_state = audioop.ratecv(
                                                pcm_24khz_bytes, 2, 1, 24000, 8000, audio_out_state
                                            )
                                            # Convert 8kHz linear PCM to G.711 u-law
                                            ulaw_bytes = audioop.lin2ulaw(pcm_8khz_bytes, 2)
                                            # Encode u-law to base64
                                            ulaw_base64 = base64.b64encode(ulaw_bytes).decode("utf-8")
                                            
                                            # Stream back to Twilio
                                            await websocket.send_text(json.dumps({
                                                "event": "media",
                                                "streamSid": stream_sid,
                                                "media": {
                                                    "payload": ulaw_base64
                                                }
                                            }))
                                            
                                            # Broadcast active waveform pulse to dashboard
                                            new_wave = [random.randint(25, 90) for _ in range(35)]
                                            await dashboard_manager.broadcast({
                                                "type": "waveform_pulse",
                                                "payload": {
                                                    "waveform": new_wave
                                                }
                                            })

                            # 3. Check for patient's speech transcript (inputTranscription)
                            if "inputTranscription" in server_content:
                                transcript = server_content["inputTranscription"].get("text", "")
                                if transcript:
                                    logger.info("Patient said", transcript=transcript, call_sid=call_sid)

                                    # Save patient transcript in database CallSession record
                                    async with async_session_factory() as db:
                                        try:
                                            stmt = select(CallSession).where(CallSession.twilio_call_sid == call_sid)
                                            res = await db.execute(stmt)
                                            db_sess = res.scalar_one_or_none()
                                            if db_sess:
                                                current_trans = db_sess.transcript or ""
                                                db_sess.transcript = f"{current_trans}\nPatient: {transcript}".strip()
                                                await db.commit()
                                        except Exception as e:
                                            logger.error("Failed to append transcript to DB", error=str(e))

                                    # Broadcast transcript chunk to dashboard
                                    await dashboard_manager.broadcast({
                                        "type": "transcript_chunk",
                                        "payload": {
                                            "text": f"\nPatient: {transcript}"
                                        }
                                    })

                                    # Perform simple sentiment analysis
                                    sentiment = "neutral"
                                    score = 50
                                    cleaned = transcript.lower()
                                    if any(x in cleaned for x in ["worry", "pain", "fever", "hurt", "bad", "sick", "emergency", "cough", "ache"]):
                                        sentiment = "negative"
                                        score = random.randint(20, 42)
                                    elif any(x in cleaned for x in ["yes", "correct", "perfect", "good", "thanks", "thank you", "yeah"]):
                                        sentiment = "positive"
                                        score = random.randint(75, 96)
                                    
                                    await dashboard_manager.broadcast({
                                        "type": "sentiment_change",
                                        "payload": {
                                            "sentiment": sentiment,
                                            "score": score
                                        }
                                    })

                                    # Process implicit state transitions (e.g. greeting to symptoms)
                                    updated_session = await VoiceOrchestrator.process_conversational_step(
                                        call_sid, user_transcript=transcript
                                    )

                                    # Update system instructions with the new state FSM prompt
                                    new_state = updated_session.get("current_state")
                                    new_prompt = get_state_prompt(new_state, updated_session)

                                    # Send FSM system update first as a non-blocking context turn
                                    await gemini_ws.send(json.dumps({
                                        "clientContent": {
                                            "turns": [
                                                {
                                                    "role": "user",
                                                    "parts": [
                                                        {
                                                            "text": f"[SYSTEM UPDATE]\nState: {new_state}\nInstructions: {new_prompt}"
                                                        }
                                                    ]
                                                }
                                            ],
                                            "turnComplete": False
                                        }
                                    }))

                        # Handle toolCall (function calling requested by Gemini)
                        elif "toolCall" in event_data:
                            tool_call = event_data["toolCall"]
                            for function_call in tool_call.get("functionCalls", []):
                                tool_name = function_call.get("name")
                                call_id = function_call.get("id")
                                arguments = function_call.get("args", {})

                                logger.info("Gemini requested tool execution", tool_name=tool_name, call_id=call_id, args=arguments)

                                # Execute tool
                                result = await execute_tool(tool_name, arguments, call_sid)

                                # Advance state machine based on tool milestone
                                updated_session = await VoiceOrchestrator.process_conversational_step(
                                    call_sid, executed_tool=tool_name
                                )

                                # Update DB CallSession conversation state
                                new_state = updated_session.get("current_state")
                                new_prompt = get_state_prompt(new_state, updated_session)

                                async with async_session_factory() as db:
                                    try:
                                        stmt = select(CallSession).where(CallSession.twilio_call_sid == call_sid)
                                        res = await db.execute(stmt)
                                        db_sess = res.scalar_one_or_none()
                                        if db_sess:
                                            db_sess.conversation_state = new_state
                                            await db.commit()
                                    except Exception as e:
                                        logger.error("Failed to update FSM state in DB", error=str(e))

                                # Map state to UI node key
                                state_mapper = {
                                    "greeting": "GREETING",
                                    "identity": "PATIENT_IDENTIFICATION",
                                    "symptoms": "SYMPTOM_TRIAGE",
                                    "dept": "CLINIC_ROUTING",
                                    "doctor": "CLINIC_ROUTING",
                                    "slot": "SLOT_LOOKUP",
                                    "review": "SLOT_LOOKUP",
                                    "payment": "CONFIRMATION",
                                    "confirm": "CONFIRMATION",
                                    "complete": "BOOKING_SUCCESS"
                                }
                                mapped_node = state_mapper.get(new_state, "GREETING")
                                
                                await dashboard_manager.broadcast({
                                    "type": "node_change",
                                    "payload": {
                                        "node": mapped_node
                                    }
                                })

                                # Send the FSM system update first as a non-blocking context turn
                                await gemini_ws.send(json.dumps({
                                    "clientContent": {
                                        "turns": [
                                            {
                                                "role": "user",
                                                "parts": [
                                                    {
                                                        "text": f"[SYSTEM UPDATE]\nState: {new_state}\nInstructions: {new_prompt}"
                                                    }
                                                ]
                                            }
                                        ],
                                        "turnComplete": False
                                    }
                                }))

                                # Send tool output back to Gemini
                                await gemini_ws.send(json.dumps({
                                    "toolResponse": {
                                        "functionResponses": [
                                            {
                                                "id": call_id,
                                                "name": tool_name,
                                                "response": {
                                                    "output": result
                                                }
                                            }
                                        ]
                                    }
                                }))

                except Exception as e:
                    logger.error("Error in Gemini to Twilio receiver", error=str(e), call_sid=call_sid)

            # Gather both tasks concurrently on the live stream
            await asyncio.gather(twilio_to_gemini(), gemini_to_twilio())

    except Exception as e:
        logger.error("WebSocket voice bridging session failed", error=str(e), call_sid=call_sid)
    finally:
        # Fetch Redis session data before clearing it
        session = await VoiceSessionManager.get_session(call_sid)
        
        # Cleanup Redis session
        await VoiceSessionManager.clear_session(call_sid)
        
        # Calculate final duration
        duration = int((datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds())

        # Update database CallSession record to COMPLETED
        async with async_session_factory() as db:
            try:
                stmt = select(CallSession).where(CallSession.twilio_call_sid == call_sid)
                result = await db.execute(stmt)
                call_sess = result.scalar_one_or_none()
                if call_sess:
                    if session:
                        call_sess.conversation_state = session.get("current_state", ConversationState.COMPLETE.value)
                        call_sess.patient_id = uuid.UUID(session["patient_id"]) if session.get("patient_id") else None
                    
                    call_sess.status = CallStatus.COMPLETED
                    call_sess.ended_at = datetime.datetime.now(datetime.timezone.utc)
                    await db.commit()
                    logger.info("Updated CallSession database record on disconnect", call_sid=call_sid, duration=duration)
            except Exception as e:
                logger.error("Failed to update CallSession database record on disconnect", error=str(e), call_sid=call_sid)

        # Broadcast call end to dashboard
        await dashboard_manager.broadcast({
            "type": "call_end",
            "payload": {}
        })

        try:
            await websocket.close()
        except Exception:
            pass
        logger.info("Voice connection closed and memory cleared", call_sid=call_sid)
