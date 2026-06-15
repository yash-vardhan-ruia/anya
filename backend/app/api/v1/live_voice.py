"""
CareVoice AI Hospital Platform - Browser-direct Gemini Multimodal Live WebSocket Bridge.

Maintains bidirectional WebSocket streams between the user's browser and the Gemini Live API:
1. Receives raw 16kHz PCM audio base64 packets from the browser, relays to Gemini.
2. Receives 24kHz output audio from Gemini, relays directly to the browser.
3. Coordinates tool calls (find_doctor, lock_slot, send_payment_link), FSM transitions,
   and streams state updates back to the browser for the EHR variables debug panel.
4. Gracefully terminates call when Anya finishes speaking the payment checkout instructions.
"""

import asyncio
import base64
import datetime
import json
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

import re

def normalize_voice_email(text: str) -> str | None:
    cleaned = text.lower()
    cleaned = re.sub(r'\s+at\s+', '@', cleaned)
    cleaned = re.sub(r'\s+dot\s+', '.', cleaned)
    cleaned = cleaned.replace(" ", "")
    match = re.search(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b', cleaned)
    if match:
        return match.group(0)
    return None


def detect_department(text: str) -> str | None:
    text = text.lower()
    departments = ["General Medicine", "Pediatrics", "Cardiology", "Orthopedics", "Dermatology", "ENT", "Ophthalmology", "Neurology", "Psychiatry", "Oncology", "Pulmonology", "Gastroenterology", "Urology"]
    
    from app.voice.tool_executor import map_department_name
    for dept in departments:
        if dept.lower() in text:
            return dept
            
    if any(word in text for word in ["chest pain", "heart", "bp", "blood pressure", "palpitation", "cardio"]):
        return "Cardiology"
    if any(word in text for word in ["child", "baby", "kid", "children", "pediatric"]):
        return "Pediatrics"
    if any(word in text for word in ["bone", "joint", "knee", "back pain", "fracture", "shoulder", "ortho"]):
        return "Orthopedics"
    if any(word in text for word in ["skin", "rash", "itching", "acne", "derm"]):
        return "Dermatology"
    if any(word in text for word in ["eye", "eyes", "sight", "ophthalm"]):
        return "Ophthalmology"
    if any(word in text for word in ["ear", "nose", "throat", "ent", "cough", "cold", "sinus"]):
        if "throat" in text or "ear" in text or "nose" in text:
            return "ENT"
    if any(word in text for word in ["brain", "neurolog", "seizure", "stroke"]):
        return "Neurology"
    if any(word in text for word in ["stomach", "gas", "acidity", "indigestion", "gastro"]):
        return "Gastroenterology"
    return None


def extract_live_session_updates(transcript: str) -> dict:
    updates = {}
    text = transcript.strip()
    
    email = normalize_voice_email(text)
    if email:
        updates["email"] = email
        
    name_match = re.search(
        r"(?:my name is|this is|i am)\s+([A-Za-z][A-Za-z\s.'-]{1,80})",
        re.sub(r"\b(?:i am|i'm)\s+\d+", "", text, flags=re.IGNORECASE),
        re.IGNORECASE,
    )
    if name_match:
        name = name_match.group(1).strip()
        name_words = name.split()
        cleaned_words = []
        for w in name_words:
            if w.lower() in ["and", "years", "old", "here", "please", "receptionist", "anya"]:
                break
            cleaned_words.append(w)
        if cleaned_words:
            name = " ".join(cleaned_words)
            if not re.search(r"\d", name) and len(name.split()) <= 4:
                updates["patient_name"] = name
                
    age_match = re.search(
        r"\b(?:i am|age is|my age is|i'm)\s+(\d{1,3})\b",
        text,
        re.IGNORECASE,
    )
    if age_match:
        updates["age"] = int(age_match.group(1))
        
    dept = detect_department(text)
    if dept:
        updates["department_name"] = dept

    # Parse visit type (first-timer vs follow-up)
    cleaned_lower = text.lower()
    if any(word in cleaned_lower for word in ["first", "1st", "new patient", "never been", "first time", "first-time"]):
        updates["visit_type"] = "First-time"
    elif any(word in cleaned_lower for word in ["follow up", "follow-up", "returning", "previous", "again"]):
        updates["visit_type"] = "Follow-up"
        
    return updates


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


@router.websocket("/ws/live-voice/{session_id}")
async def live_voice_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint to proxy real-time voice streaming directly from browser to Gemini."""
    await websocket.accept()
    logger.info("Browser WebSocket connection established for live voice", session_id=session_id)

    # Initialize a new booking session in Redis
    session_data = await VoiceSessionManager.update_session(session_id, {
        "call_sid": session_id,
    })

    # Save CallSession to database on call start
    start_time = datetime.datetime.now(datetime.timezone.utc)
    async with async_session_factory() as db:
        try:
            call_session = CallSession(
                twilio_call_sid=session_id,
                from_number="Browser Microphone",
                status=CallStatus.IN_PROGRESS,
                started_at=start_time,
                conversation_state=ConversationState.GREETING,
                transcript="",
            )
            db.add(call_session)
            await db.commit()
            logger.info("Persisted CallSession to database", session_id=session_id)
        except Exception as e:
            logger.error("Failed to create CallSession record", error=str(e), session_id=session_id)

    # Broadcast call start event to admin telemetry dashboard
    await dashboard_manager.broadcast({
        "type": "call_start",
        "payload": {
            "id": session_id,
            "callerId": "unknown",
            "callerName": "Browser Patient",
            "callerPhone": "Browser Mic",
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

    # Send connected status to browser
    await websocket.send_json({
        "type": "status",
        "status": "connected",
        "message": "WebSocket proxy handshake complete."
    })

    # Use v1beta endpoint for Gemini Live API
    gemini_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={settings.GEMINI_API_KEY}"

    try:
        async with websockets.connect(gemini_url) as gemini_ws:
            logger.info("Connected to Gemini Multimodal Live API WebSocket", session_id=session_id)

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

            setup_msg = {
                "setup": {
                    "model": "models/gemini-2.5-flash-native-audio-preview-09-2025",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": "Aoede"
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
                    "tools": gemini_tools,
                    "inputAudioTranscription": {},
                    "outputAudioTranscription": {},
                    "realtimeInputConfig": {
                        "automaticActivityDetection": {
                            "disabled": False,
                            "silenceDurationMs": 1000
                        }
                    }
                }
            }
            await gemini_ws.send(json.dumps(setup_msg))
            logger.info("Sent initial setup configuration to Gemini", session_id=session_id)

            # Wait for setup completion acknowledgment
            setup_resp = await gemini_ws.recv()
            logger.info("Received setup response from Gemini", response=str(setup_resp)[:200], session_id=session_id)

            # Let browser know we're listening/speaking
            await websocket.send_json({
                "type": "status",
                "status": "listening",
                "message": "Gemini Live API session configured. Speak now."
            })

            # Send initial state variables
            await websocket.send_json({
                "type": "state",
                "data": session_data
            })

            async def browser_to_gemini():
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        msg_type = data.get("type")

                        if msg_type == "audio":
                            pcm_base64 = data.get("data")
                            if pcm_base64:
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
                        elif msg_type == "control":
                            action = data.get("action")
                            logger.info("Control message received from browser", action=action, session_id=session_id)
                except WebSocketDisconnect:
                    logger.info("Browser WebSocket disconnected", session_id=session_id)
                except Exception as e:
                    logger.error("Error in Browser to Gemini receiver", error=str(e), session_id=session_id)

            async def gemini_to_browser():
                try:
                    async for message in gemini_ws:
                        event_data = json.loads(message)

                        # Handle serverContent (Audio output, user transcription, interrupted)
                        if "serverContent" in event_data:
                            server_content = event_data["serverContent"]

                            # 1. User Interruption (Barge-in)
                            if server_content.get("interrupted"):
                                logger.info("User interrupted Gemini. Sending clear command to browser.", session_id=session_id)
                                await websocket.send_json({
                                    "type": "control",
                                    "action": "clear"
                                })

                            # 2. Audio output from model (24kHz PCM)
                            model_turn = server_content.get("modelTurn")
                            if model_turn:
                                for part in model_turn.get("parts", []):
                                    if "inlineData" in part:
                                        inline_data = part["inlineData"]
                                        pcm_24khz_base64 = inline_data.get("data")
                                        if pcm_24khz_base64:
                                            # Relay audio directly to browser
                                            await websocket.send_json({
                                                "type": "audio",
                                                "data": pcm_24khz_base64
                                            })

                            # 4. Turn Complete (Anya finished her speech)
                            if server_content.get("turnComplete"):
                                # If Anya finished speaking and we are in PAYMENT state, end the call
                                session_now = await VoiceSessionManager.get_session(session_id)
                                if session_now and session_now.get("current_state") == ConversationState.PAYMENT.value:
                                    logger.info("Anya finished parting instructions. Gracefully terminating call.", session_id=session_id)
                                    await websocket.send_json({
                                        "type": "status",
                                        "status": "completed",
                                        "message": "Anya has completed the booking and sent the payment link to your email."
                                    })

                        elif "outputTranscription" in event_data or "output_transcription" in event_data:
                            model_trans_obj = event_data.get("outputTranscription") or event_data.get("output_transcription")
                            if model_trans_obj:
                                model_transcript = model_trans_obj.get("text", "")
                                if model_transcript:
                                    logger.info("Anya transcript parsed", transcript=model_transcript, session_id=session_id)
                                    # Send assistant transcript back to browser
                                    await websocket.send_json({
                                        "type": "transcript",
                                        "role": "assistant",
                                        "text": model_transcript
                                    })

                        elif "inputTranscription" in event_data or "input_transcription" in event_data:
                            user_trans_obj = event_data.get("inputTranscription") or event_data.get("input_transcription")
                            if user_trans_obj:
                                transcript = user_trans_obj.get("text", "")
                                if transcript:
                                    logger.info("Patient transcript parsed", transcript=transcript, session_id=session_id)
                                    
                                    # Send transcript turn back to browser
                                    await websocket.send_json({
                                        "type": "transcript",
                                        "role": "user",
                                        "text": transcript
                                    })

                                    # Save patient transcript in database CallSession record
                                    async with async_session_factory() as db:
                                        try:
                                            stmt = select(CallSession).where(CallSession.twilio_call_sid == session_id)
                                            res = await db.execute(stmt)
                                            db_sess = res.scalar_one_or_none()
                                            if db_sess:
                                                current_trans = db_sess.transcript or ""
                                                db_sess.transcript = f"{current_trans}\nPatient: {transcript}".strip()
                                                await db.commit()
                                        except Exception as e:
                                            logger.error("Failed to append transcript to DB", error=str(e))

                                    # Extract patient updates from transcript and update Redis session
                                    live_updates = extract_live_session_updates(transcript)
                                    if live_updates:
                                        logger.info("Extracted live patient updates", updates=live_updates, session_id=session_id)
                                        await VoiceSessionManager.update_session(session_id, live_updates)

                                    # Process implicit state transitions
                                    updated_session = await VoiceOrchestrator.process_conversational_step(
                                        session_id, user_transcript=transcript
                                    )

                                    # Broadcast updated state to browser
                                    await websocket.send_json({
                                        "type": "state",
                                        "data": updated_session
                                    })

                                    # Update system instructions with the new state FSM prompt
                                    new_state = updated_session.get("current_state")
                                    new_prompt = get_state_prompt(new_state, updated_session)

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
                                result = await execute_tool(tool_name, arguments, session_id)

                                # Advance state machine based on tool milestone
                                updated_session = await VoiceOrchestrator.process_conversational_step(
                                    session_id, executed_tool=tool_name
                                )

                                # Update DB CallSession conversation state
                                new_state = updated_session.get("current_state")
                                new_prompt = get_state_prompt(new_state, updated_session)

                                async with async_session_factory() as db:
                                    try:
                                        stmt = select(CallSession).where(CallSession.twilio_call_sid == session_id)
                                        res = await db.execute(stmt)
                                        db_sess = res.scalar_one_or_none()
                                        if db_sess:
                                            db_sess.conversation_state = new_state
                                            await db.commit()
                                    except Exception as e:
                                        logger.error("Failed to update FSM state in DB", error=str(e))

                                # Broadcast updated state to browser
                                await websocket.send_json({
                                    "type": "state",
                                    "data": updated_session
                                })

                                # Send FSM system update prompt to Gemini
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
                    logger.error("Error in Gemini to Browser receiver", error=str(e), session_id=session_id)

            # Gather both tasks concurrently
            await asyncio.gather(browser_to_gemini(), gemini_to_browser())

    except Exception as e:
        logger.error("WebSocket voice bridging session failed", error=str(e), session_id=session_id)
    finally:
        # Calculate final duration
        duration = int((datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds())

        # Update database CallSession record to COMPLETED
        async with async_session_factory() as db:
            try:
                stmt = select(CallSession).where(CallSession.twilio_call_sid == session_id)
                result = await db.execute(stmt)
                call_sess = result.scalar_one_or_none()
                if call_sess:
                    # Retrieve latest Redis session before final delete
                    session = await VoiceSessionManager.get_session(session_id)
                    if session:
                        call_sess.conversation_state = session.get("current_state", ConversationState.COMPLETE.value)
                        call_sess.patient_id = uuid.UUID(session["patient_id"]) if session.get("patient_id") else None

                    call_sess.status = CallStatus.COMPLETED
                    call_sess.ended_at = datetime.datetime.now(datetime.timezone.utc)
                    await db.commit()
                    logger.info("Updated CallSession database record on disconnect", session_id=session_id, duration=duration)
            except Exception as e:
                logger.error("Failed to update CallSession database record on disconnect", error=str(e), session_id=session_id)

        try:
            await websocket.close()
        except Exception:
            pass
        logger.info("Voice connection closed and memory cleared", session_id=session_id)
