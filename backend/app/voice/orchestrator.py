"""
CareVoice AI Hospital Platform - Voice Agent FSM Orchestrator.

Manages the Finite State Machine (FSM) representing the sequential stages of the booking
conversation. Handles transitions dynamically based on conversational milestones and tool call events.
"""

import structlog
from app.core.constants import ConversationState
from app.voice.session_manager import VoiceSessionManager
from app.voice.emergency import is_emergency

logger = structlog.get_logger(__name__)


class VoiceOrchestrator:
    """Orchestrates FSM state transitions for live voice assistant sessions."""

    @classmethod
    async def process_conversational_step(
        cls,
        call_sid: str,
        user_transcript: str | None = None,
        executed_tool: str | None = None,
    ) -> dict:
        """Analyze conversation events and advance the FSM stage if milestones are hit.

        Args:
            call_sid: Unique Twilio voice session identifier
            user_transcript: Optional newly transcribed utterance from the patient
            executed_tool: Optional name of the tool called in this turn

        Returns:
            dict: The updated session state variables
        """
        # 1. Load current session
        session = await VoiceSessionManager.get_session(call_sid)
        if not session:
            # Initialize default session
            session = await VoiceSessionManager.update_session(call_sid, {})

        current_state = session.get("current_state", ConversationState.GREETING.value)
        logger.info("Orchestrator routing step", call_sid=call_sid, current_state=current_state, tool=executed_tool)

        # 2. Check for emergencies deterministically
        if user_transcript and is_emergency(user_transcript):
            logger.warning("EMERGENCY FLAGGED - Escalating caller session", call_sid=call_sid, input=user_transcript)
            session = await VoiceSessionManager.update_session(call_sid, {
                "is_emergency": True,
                "current_state": ConversationState.COMPLETE.value  # Exit normal flow
            })
            return session

        # 3. Rule-based FSM transition overrides based on tool call milestones
        next_state = current_state

        if executed_tool == "lock_slot":
            next_state = ConversationState.REVIEW.value
        elif executed_tool == "confirm_booking":
            next_state = ConversationState.PAYMENT.value

        # 4. Implicit state transitions based on transcript content analysis if not transitioned by tool
        elif user_transcript and executed_tool is None:
            cleaned = user_transcript.lower().strip()
            
            if current_state == ConversationState.GREETING.value:
                # If name is provided, move to Identity
                if len(cleaned.split()) >= 1:
                    next_state = ConversationState.IDENTITY.value
            
            elif current_state == ConversationState.IDENTITY.value:
                # If they confirmed identity, ask for symptoms
                if any(x in cleaned for x in ["yes", "correct", "yeah", "sure", "that's me"]):
                    next_state = ConversationState.SYMPTOMS.value
            
            elif current_state == ConversationState.SYMPTOMS.value:
                # Once they describe symptoms, we will search doctors (leads to DEPT or DOCTOR)
                if len(cleaned.split()) >= 3:
                    next_state = ConversationState.DEPT.value

            elif current_state == ConversationState.PAYMENT.value:
                # Once checkout link is explained, we can transition to confirm or exit
                if any(x in cleaned for x in ["ok", "received", "got it", "done", "paid", "confirmed"]):
                    next_state = ConversationState.CONFIRM.value

            elif current_state == ConversationState.CONFIRM.value:
                # Say goodbye
                if any(x in cleaned for x in ["thanks", "thank you", "bye", "goodbye"]):
                    next_state = ConversationState.COMPLETE.value

        # 5. Apply transitions in Redis
        if next_state != current_state:
            logger.info("FSM Transition", call_sid=call_sid, from_state=current_state, to_state=next_state)
            session = await VoiceSessionManager.update_session(call_sid, {"current_state": next_state})

        return session
