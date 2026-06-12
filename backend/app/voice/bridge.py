"""
CareVoice AI Hospital Platform - Twilio to OpenAI Realtime WebSocket Bridge.

Maintains bidirectional WebSocket streams:
1. Receives audio packets (g.711 u-law) from Twilio, streams them to OpenAI.
2. Receives output audio from OpenAI, packages it as Twilio media event packets, and streams it back.
3. Coordinates real-time tool execution and state-aware FSM prompt updates on conversational milestones.
"""

import asyncio
import datetime
import json
import random
import uuid
import structlog
import websockets
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
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Handle connection drop silently during broadcast iteration
                pass


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
    """Establishes bidirectional voice stream bridging Twilio and OpenAI Realtime."""
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

    openai_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1",
    }

    try:
        async with websockets.connect(openai_url, extra_headers=headers) as openai_ws:
            logger.info("Connected to OpenAI Realtime API WebSocket", call_sid=call_sid)

            # Establish initial session configurations for Anya
            initial_state = session_data.get("current_state", ConversationState.GREETING.value)
            initial_prompt = get_state_prompt(initial_state, session_data)

            # Configure session
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "instructions": initial_prompt,
                    "input_audio_format": "g711_ulaw",
                    "output_audio_format": "g711_ulaw",
                    "modalities": ["text", "audio"],
                    "voice": "alloy",
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500,
                    },
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "tools": REALTIME_TOOLS,
                    "tool_choice": "auto",
                }
            }))

            stream_sid = None

            async def twilio_to_openai():
                nonlocal stream_sid
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        event = data.get("event")

                        if event == "start":
                            stream_sid = data["start"]["streamSid"]
                            logger.info("Twilio media stream starting", stream_sid=stream_sid, call_sid=call_sid)
                        
                        elif event == "media":
                            payload = data["media"]["payload"]
                            # Directly forward g.711 u-law base64 chunk to OpenAI
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": payload
                            }))

                        elif event == "stop":
                            logger.info("Twilio media stream stopped", call_sid=call_sid)
                            break
                except WebSocketDisconnect:
                    logger.info("Twilio stream WebSocket disconnected", call_sid=call_sid)
                except Exception as e:
                    logger.error("Error in Twilio to OpenAI receiver", error=str(e), call_sid=call_sid)

            async def openai_to_twilio():
                nonlocal stream_sid
                try:
                    async for message in openai_ws:
                        event_data = json.loads(message)
                        event_type = event_data.get("type")

                        if event_type == "response.audio.delta":
                            # Stream raw base64 g.711 u-law delta back to Twilio
                            audio_delta = event_data.get("delta")
                            if stream_sid and audio_delta:
                                await websocket.send_text(json.dumps({
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": audio_delta
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

                        elif event_type == "response.function_call_arguments.done":
                            # A tool call was requested by Anya
                            tool_name = event_data.get("name")
                            call_id = event_data.get("call_id")
                            arguments = json.loads(event_data.get("arguments", "{}"))

                            # Execute tool
                            result = await execute_tool(tool_name, arguments, call_sid)

                            # Advance state machine based on tool milestone
                            updated_session = await VoiceOrchestrator.process_conversational_step(
                                call_sid, executed_tool=tool_name
                            )

                            # Send tool output back to OpenAI Realtime
                            await openai_ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": json.dumps(result),
                                }
                            }))

                            # Update system instructions with the new state FSM prompt
                            new_state = updated_session.get("current_state")
                            new_prompt = get_state_prompt(new_state, updated_session)

                            await openai_ws.send(json.dumps({
                                "type": "session.update",
                                "session": {
                                    "instructions": new_prompt
                                }
                            }))

                            # Trigger model to respond
                            await openai_ws.send(json.dumps({
                                "type": "response.create"
                            }))

                            # Update DB CallSession conversation state
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

                        elif event_type == "conversation.item.input_audio_transcription.completed":
                            # Process patient's transcript to dynamically transition FSM state
                            transcript = event_data.get("transcript", "")
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

                            await openai_ws.send(json.dumps({
                                "type": "session.update",
                                "session": {
                                    "instructions": new_prompt
                                }
                            }))

                except Exception as e:
                    logger.error("Error in OpenAI to Twilio receiver", error=str(e), call_sid=call_sid)

            # Gather both tasks concurrently on the live stream
            await asyncio.gather(twilio_to_openai(), openai_to_twilio())

    except Exception as e:
        logger.error("WebSocket voice bridging session failed", error=str(e), call_sid=call_sid)
    finally:
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
                    # Fetch Redis session data
                    session = await VoiceSessionManager.get_session(call_sid)
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
