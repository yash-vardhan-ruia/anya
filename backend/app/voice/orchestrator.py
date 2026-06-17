"""
CareVoice AI - Voice Conversation Orchestrator.

Manages FSM state transitions driven by tool execution results.
Transcript-based transitions are minimal — tools are the primary driver.
"""

from typing import Tuple
from app.core.constants import ConversationState
from app.voice.prompts import get_state_prompt

EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
    "unconscious", "not breathing", "heart attack", "stroke",
    "severe bleeding", "overdose", "poisoning",
    "sine dard", "saans nahi", "behosh", "dil ka daura",
]


class VoiceOrchestrator:
    """Manages the state transitions for the AI voice system."""

    @classmethod
    def advance_state_after_tool(cls, state: str, tool_name: str, tool_result: dict, session: dict) -> str:
        """Deterministic state transitions based on which tool just ran."""
        
        if tool_name == "check_patient_by_email":
            return ConversationState.SYMPTOMS if tool_result.get("exists") else ConversationState.RETURNING_LOOKUP
            
        elif tool_name == "create_new_patient":
            return ConversationState.SYMPTOMS if tool_result.get("success") else ConversationState.NEW_INFO

        elif tool_name == "update_patient_details":
            # Incrementally updating details; FSM remains in NEW_INFO state until finalized via create_new_patient
            return ConversationState.NEW_INFO
            
        elif tool_name == "find_doctors_by_department":
            if "error" not in tool_result:
                return ConversationState.DOCTOR_SELECT
            return state

        elif tool_name == "select_doctor_by_name":
            if "error" not in tool_result:
                return ConversationState.SLOT_SELECT
            return state

        elif tool_name == "select_appointment_slot":
            if "error" not in tool_result:
                return ConversationState.BOOKING_REVIEW
            return state
            
        elif tool_name == "lock_and_confirm_booking":
            return ConversationState.FAREWELL if tool_result.get("success") else ConversationState.BOOKING_REVIEW
            
        return state

    @classmethod
    async def advance_state_from_browser_input(cls, state: str, field: str, value: any, session: dict) -> Tuple[str, dict]:
        """Handle state transitions triggered by browser UI clicks/inputs (fallback)."""
        updates = {}
        new_state = state

        if field == "email":
            pass
            
        elif field == "doctor":
            if state == ConversationState.DOCTOR_SELECT:
                pass
                
        elif field == "slot":
            if state == ConversationState.SLOT_SELECT:
                new_state = ConversationState.BOOKING_REVIEW

        return new_state, updates

    @classmethod
    def check_emergency(cls, transcript: str) -> bool:
        """Detect emergency keywords in English and Hindi."""
        text = transcript.lower()
        return any(keyword in text for keyword in EMERGENCY_KEYWORDS)

    @classmethod
    def get_state_prompt_injection(cls, state: str, session: dict) -> str:
        """Get the injected system prompt for the current state."""
        return get_state_prompt(state, session)
