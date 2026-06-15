"""
CareVoice AI Hospital Platform - Gemini Live API Tools.

Defines the JSON schemas for the tools/functions that Anya can execute in real-time.
"""

REALTIME_TOOLS = [
    {
        "type": "function",
        "name": "find_doctor",
        "description": (
            "Lookup active doctors and departments in the hospital system. "
            "Use this when the patient specifies symptoms, a department, or a doctor's name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "department_name": {
                    "type": "string",
                    "description": "Name of the hospital department, e.g., Cardiology, Orthopedics, Pediatrics",
                },
                "search_query": {
                    "type": "string",
                    "description": "Optional search term for doctor's name or specialization, e.g. Cardiology",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "get_slots",
        "description": "Retrieve available bookable time slots for a specific doctor on a calendar date.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {
                    "type": "string",
                    "description": "The unique UUID of the doctor",
                },
                "target_date": {
                    "type": "string",
                    "description": "ISO date string for slot lookup, e.g. YYYY-MM-DD",
                },
            },
            "required": ["doctor_id", "target_date"],
        },
    },
    {
        "type": "function",
        "name": "lock_slot",
        "description": (
            "Temporarily lock a time slot for 5 minutes during the booking review phase. "
            "Prevents other calls from booking the same slot."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "slot_id": {
                    "type": "string",
                    "description": "The unique UUID of the doctor slot to lock",
                },
            },
            "required": ["slot_id"],
        },
    },
    {
        "type": "function",
        "name": "confirm_booking",
        "description": (
            "Finalize the appointment booking in the database, transition slot to BOOKED, "
            "generate invoice, send SMS payment checkout link, and transition state."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "Full legal name of the patient",
                },
                "phone": {
                    "type": "string",
                    "description": "Patient phone number (format +91XXXXXXXXXX)",
                },
                "slot_id": {
                    "type": "string",
                    "description": "The unique locked UUID of the doctor slot to book",
                },
                "symptoms": {
                    "type": "string",
                    "description": "Brief description of the patient's symptoms",
                },
            },
            "required": ["patient_name", "phone", "slot_id"],
        },
    },
]
