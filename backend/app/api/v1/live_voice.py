"""
CareVoice AI Hospital Platform - Live Voice WebSocket API.

Handles real-time audio streaming with Google's Gemini 2.5 Flash Native Audio Dialog.
Provides a duplex WebSocket proxy between the browser and Gemini Live API.
"""

import asyncio
import base64
import json
import uuid
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import websockets
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.call_session import CallSession, CallStatus
from app.voice.session_manager import VoiceSessionManager
from app.voice.tools import REALTIME_TOOLS
from app.voice.prompts import ANYA_PERSONA
from app.voice.tool_executor import execute_tool
from app.voice.orchestrator import VoiceOrchestrator
from app.core.constants import ConversationState

logger = structlog.get_logger(__name__)
router = APIRouter()


class DashboardConnectionManager:
    """Manages WebSocket connections for the admin dashboard (viewing live call status)."""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        
        for dead in dead_connections:
            self.disconnect(dead)


dashboard_manager = DashboardConnectionManager()


@router.websocket("/api/v1/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """Endpoint for the admin dashboard to listen for live call updates."""
    await dashboard_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)


@router.websocket("/api/v1/ws/live-voice/{session_id}")
async def live_voice_endpoint(websocket: WebSocket, session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Main WebSocket endpoint for real-time voice interaction from the browser.
    Connects to Gemini Live API and streams audio bidirectionally.
    """
    await websocket.accept()
    logger.info("New live voice connection", session_id=session_id)

    # Validate API key
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        await websocket.close(code=1011, reason="Gemini API Key missing")
        return

    session_id_uuid = uuid.UUID(session_id) if len(session_id) == 36 else uuid.uuid4()
    session_uuid_str = str(session_id_uuid)

    # Create CallSession DB record
    call_record = CallSession(
        id=session_id_uuid,
        session_sid=f"web_{session_uuid_str}",
        from_number="web",
        status=CallStatus.IN_PROGRESS,
    )
    db.add(call_record)
    await db.commit()
    await db.refresh(call_record)

    # Initialize Voice Session in Redis
    session = await VoiceSessionManager.get_session(session_uuid_str)

    gemini_ws_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={settings.GEMINI_API_KEY}"

    farewell_event = asyncio.Event()

    try:
        async with websockets.connect(gemini_ws_url) as gemini_ws:
            logger.info("Connected to Gemini Live API", session_id=session_uuid_str)

            # 1. Send Setup Message
            setup_msg = {
                "setup": {
                    "model": "models/gemini-2.5-flash-native-audio-preview-09-2025",
                    "generation_config": {
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {"voice_name": "Aoede"}
                            }
                        },
                    },
                    "input_audio_transcription": {},
                    "output_audio_transcription": {},
                    "system_instruction": {
                        "parts": [{"text": ANYA_PERSONA}]
                    },
                    "tools": [{"function_declarations": REALTIME_TOOLS}],
                }
            }
            await gemini_ws.send(json.dumps(setup_msg))

            # Send initial state prompt injection
            initial_prompt = VoiceOrchestrator.get_state_prompt_injection(session["current_state"], session)
            prompt_injection = {
                "client_content": {
                    "turns": [{
                        "role": "user",
                        "parts": [{"text": f"[SYSTEM INITIALIZATION]: {initial_prompt}"}]
                    }],
                    "turn_complete": True
                }
            }
            await gemini_ws.send(json.dumps(prompt_injection))

            # Wait for setupComplete
            raw_response = await gemini_ws.recv()
            setup_res = json.loads(raw_response)
            if "setupComplete" in setup_res:
                logger.info("Gemini setup complete", session_id=session_uuid_str)
                await websocket.send_json({"type": "status", "status": "listening"})
                await websocket.send_json({"type": "state", "data": session})
            else:
                logger.error("Failed to receive setupComplete from Gemini", response=setup_res)
                await websocket.close(code=1011, reason="Gemini setup failed")
                return

            # --- Concurrency Tasks ---

            async def browser_to_gemini():
                """Receive audio/text from browser and forward to Gemini."""
                try:
                    while True:
                        data = await websocket.receive_json()
                        msg_type = data.get("type")

                        if msg_type == "audio":
                            audio_b64 = data.get("data")
                            if audio_b64:
                                msg = {
                                    "realtime_input": {
                                        "media_chunks": [{
                                            "mime_type": "audio/pcm",
                                            "data": audio_b64
                                        }]
                                    }
                                }
                                await gemini_ws.send(json.dumps(msg))

                        elif msg_type == "input_submit":
                            # Browser sent email
                            email_val = data.get("value", "").strip().lower()
                            # Update Redis
                            updated_session = await VoiceSessionManager.update_session(session_uuid_str, {"email": email_val})
                            await websocket.send_json({"type": "state", "data": updated_session})
                            
                            # Decide on injection instruction based on visit_type
                            visit_type = updated_session.get("visit_type")
                            if visit_type == "new":
                                prompt_suffix = " [SYSTEM INSTRUCTION: Email received. You MUST now call the 'create_new_patient' tool with the patient's full_name, age, and gender parameters to register the patient. If you do not have the patient's name, age, or gender yet, ask the patient for the missing details first, and then call the tool as soon as you have all of them.]"
                            else:
                                prompt_suffix = " [SYSTEM INSTRUCTION: Email received. You MUST now call the 'check_patient_by_email' tool with the email parameter to look up the returning patient. Call the tool first before continuing.]"
                            
                            # Inject text to Gemini
                            text_injection = {
                                "client_content": {
                                    "turns": [{
                                        "role": "user",
                                        "parts": [{"text": f"My email is {email_val}.{prompt_suffix}"}]
                                    }],
                                    "turn_complete": True
                                }
                            }
                            await gemini_ws.send(json.dumps(text_injection))

                        elif msg_type == "selection":
                            field = data.get("field")
                            val = data.get("value")
                            
                            # Update Redis based on field
                            current_state = (await VoiceSessionManager.get_session(session_uuid_str)).get("current_state")
                            new_state, extra_updates = await VoiceOrchestrator.advance_state_from_browser_input(current_state, field, val, session)
                            
                            updates = {"current_state": new_state}
                            updates.update(extra_updates)
                            
                            if field == "doctor":
                                updates["doctor_id"] = val["id"]
                                updates["doctor_name"] = val["name"]
                                inject_text = f"I'd like to see Dr. {val['name']} please. [SYSTEM INSTRUCTION: The patient has selected Dr. {val['name']}. You MUST now call the 'get_available_slots' tool with doctor_id='{val['id']}' to fetch availability. Do not speak about slots until you have called the tool.]"
                            elif field == "slot":
                                updates["slot_id"] = val["id"]
                                updates["slot_date_str"] = val["date"]
                                updates["slot_time_str"] = f"{val['start_time']} - {val['end_time']}"
                                inject_text = f"I'll take the {val['start_time']} slot on {val['date']}. [SYSTEM INSTRUCTION: Slot selected. You MUST now transition to 'booking_review' state, read back the appointment details to the patient, and ask for verbal confirmation to finalize the booking. Do not call the 'lock_and_confirm_booking' tool until they confirm.]"
                            else:
                                inject_text = "I have made my selection."

                            updated_session = await VoiceSessionManager.update_session(session_uuid_str, updates)
                            await websocket.send_json({"type": "state", "data": updated_session})
                            
                            # Inject text to Gemini
                            text_injection = {
                                "client_content": {
                                    "turns": [{
                                        "role": "user",
                                        "parts": [{"text": inject_text}]
                                    }],
                                    "turn_complete": True
                                }
                            }
                            await gemini_ws.send(json.dumps(text_injection))

                            # Inject updated state prompt
                            state_prompt = VoiceOrchestrator.get_state_prompt_injection(new_state, updated_session)
                            prompt_injection = {
                                "client_content": {
                                    "turns": [{
                                        "role": "user",
                                        "parts": [{"text": f"[SYSTEM UPDATE - NEW STATE: {new_state}]: {state_prompt}"}]
                                    }],
                                    "turn_complete": False
                                }
                            }
                            await gemini_ws.send(json.dumps(prompt_injection))

                except WebSocketDisconnect:
                    logger.info("Browser WebSocket disconnected", session_id=session_uuid_str)
                except Exception as e:
                    logger.error("Error in browser_to_gemini task", error=str(e))

            async def gemini_to_browser():
                """Receive audio/events from Gemini and forward to browser."""
                try:
                    async for message in gemini_ws:
                        resp = json.loads(message)

                        if "serverContent" in resp:
                            server_content = resp["serverContent"]

                            # 1. Handle Barge-in
                            if server_content.get("interrupted"):
                                await websocket.send_json({"type": "control", "action": "clear"})

                            # 2. Handle Turn Complete (for farewell tracking)
                            if server_content.get("turnComplete"):
                                if farewell_event.is_set():
                                    # Call should end now
                                    await websocket.send_json({"type": "status", "status": "completed"})
                                    return

                            # 3. Handle Transcripts
                            if "inputTranscription" in server_content:
                                text = server_content["inputTranscription"].get("text", "")
                                if text:
                                    await websocket.send_json({"type": "transcript", "role": "user", "text": text})
                                    
                                    # Conversational FSM transitions based on user input
                                    current_session = await VoiceSessionManager.get_session(session_uuid_str)
                                    current_state = current_session.get("current_state")
                                    if current_state in ["greeting", "type_check"]:
                                        text_lower = text.lower()
                                        if any(x in text_lower for x in ["new", "first time", "naya", "nayi", "fresh"]):
                                            current_session = await VoiceSessionManager.update_session(
                                                session_uuid_str,
                                                {"current_state": "new_info", "visit_type": "new"}
                                            )
                                            await websocket.send_json({"type": "state", "data": current_session})
                                        elif any(x in text_lower for x in ["returning", "follow-up", "purana", "old", "registered", "lookup", "check"]):
                                            current_session = await VoiceSessionManager.update_session(
                                                session_uuid_str,
                                                {"current_state": "returning_lookup", "visit_type": "returning"}
                                            )
                                            await websocket.send_json({"type": "state", "data": current_session})

                            if "outputTranscription" in server_content:
                                text = server_content["outputTranscription"].get("text", "")
                                if text:
                                    await websocket.send_json({"type": "transcript", "role": "assistant", "text": text})


                            # 4. Handle Audio
                            if "modelTurn" in server_content:
                                parts = server_content["modelTurn"].get("parts", [])
                                for part in parts:
                                    if "inlineData" in part:
                                        audio_data = part["inlineData"].get("data")
                                        if audio_data:
                                            await websocket.send_json({"type": "audio", "data": audio_data})

                        # 5. Handle Tool Calls
                        if "toolCall" in resp:
                            tool_calls = resp["toolCall"].get("functionCalls", [])
                            responses = []
                            
                            current_session = await VoiceSessionManager.get_session(session_uuid_str)
                            
                            for call in tool_calls:
                                name = call.get("name")
                                call_id = call.get("id")
                                args = call.get("args", {})
                                
                                # Execute tool
                                result, session_updates, ws_events = await execute_tool(name, args, current_session, db)
                                
                                # Broadcast events to browser
                                for event in ws_events:
                                    await websocket.send_json(event)
                                    if event.get("type") == "redirect_payment":
                                        farewell_event.set()

                                # Update session state
                                current_state = current_session.get("current_state")
                                new_state = VoiceOrchestrator.advance_state_after_tool(current_state, name, result, current_session)
                                
                                updates = {"current_state": new_state}
                                updates.update(session_updates)
                                current_session = await VoiceSessionManager.update_session(session_uuid_str, updates)
                                
                                # Broadcast new state to browser
                                await websocket.send_json({"type": "state", "data": current_session})
                                
                                # Add to tool responses
                                responses.append({
                                    "id": call_id,
                                    "name": name,
                                    "response": {"result": result}
                                })
                                
                                # Inject new prompt if state changed
                                if new_state != current_state:
                                    state_prompt = VoiceOrchestrator.get_state_prompt_injection(new_state, current_session)
                                    prompt_injection = {
                                        "client_content": {
                                            "turns": [{
                                                "role": "user",
                                                "parts": [{"text": f"[SYSTEM UPDATE - NEW STATE: {new_state}]: {state_prompt}"}]
                                            }],
                                            "turn_complete": False
                                        }
                                    }
                                    await gemini_ws.send(json.dumps(prompt_injection))

                            # Send toolResponse back to Gemini
                            tool_response_msg = {
                                "toolResponse": {
                                    "functionResponses": responses
                                }
                            }
                            await gemini_ws.send(json.dumps(tool_response_msg))

                except websockets.exceptions.ConnectionClosed:
                    logger.info("Gemini WebSocket closed", session_id=session_uuid_str)
                except Exception as e:
                    logger.error("Error in gemini_to_browser task", error=str(e))

            # Run tasks concurrently
            task1 = asyncio.create_task(browser_to_gemini())
            task2 = asyncio.create_task(gemini_to_browser())

            done, pending = await asyncio.wait(
                [task1, task2],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

    except Exception as e:
        logger.error("Fatal error in live voice session", error=str(e))
        try:
            await websocket.send_json({"type": "status", "status": "error", "message": "Connection lost"})
        except Exception:
            pass
    finally:
        # Cleanup
        call_record.status = CallStatus.COMPLETED
        call_record.duration_seconds = 0  # Can be calculated from created_at
        await db.commit()
        logger.info("Live voice session ended", session_id=session_uuid_str)
