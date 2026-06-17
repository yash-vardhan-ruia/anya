"""
CareVoice AI Hospital Platform - Voice Tools Schema.

Defines the Gemini function declarations for the hybrid voice + browser booking flow.
These are registered with the Gemini Live API at session setup.
"""

SUPPORTED_DEPARTMENTS = [
    "Cardiology",
    "Dermatology",
    "ENT",
    "Gastroenterology",
    "General Medicine",
    "Neurology",
    "Oncology",
    "Ophthalmology",
    "Orthopedics",
    "Pediatrics",
    "Psychiatry",
    "Pulmonology",
    "Radiology",
    "Urology",
]

REALTIME_TOOLS = [
    {
        "name": "check_patient_by_email",
        "description": (
            "Look up an existing patient by their email address. "
            "Call this immediately when a returning patient speaks their email address."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "email": {
                    "type": "STRING",
                    "description": "The patient's registered email address (e.g. john.doe@example.com).",
                },
            },
            "required": ["email"],
        },
    },
    {
        "name": "update_patient_details",
        "description": (
            "Update patient registration details in the live session. "
            "You MUST call this tool as soon as the patient speaks their name, age, gender, or email. "
            "Do NOT wait to collect all details; call it to update each field in real-time."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "full_name": {
                    "type": "STRING",
                    "description": "Patient's full name if spoken.",
                },
                "age": {
                    "type": "INTEGER",
                    "description": "Patient's age in years if spoken.",
                },
                "gender": {
                    "type": "STRING",
                    "description": "Patient's gender: 'Male', 'Female', or 'Other' if spoken.",
                },
                "email": {
                    "type": "STRING",
                    "description": "Patient's email address if spoken.",
                },
            },
        },
    },
    {
        "name": "create_new_patient",
        "description": (
            "Register a new patient in the database. "
            "Call this tool only AFTER all four registration details (full_name, age, gender, email) "
            "have been collected and updated in the session."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "full_name": {
                    "type": "STRING",
                    "description": "Patient's full name.",
                },
                "age": {
                    "type": "INTEGER",
                    "description": "Patient's age in years.",
                },
                "gender": {
                    "type": "STRING",
                    "description": "Patient's gender: 'Male', 'Female', or 'Other'.",
                },
                "email": {
                    "type": "STRING",
                    "description": "Patient's email address.",
                },
            },
            "required": ["full_name", "age", "gender", "email"],
        },
    },
    {
        "name": "find_doctors_by_department",
        "description": (
            "Find available doctors in a specific medical department. "
            "MUST use only departments from this list: "
            "Cardiology, Dermatology, ENT, Gastroenterology, General Medicine, "
            "Neurology, Oncology, Ophthalmology, Orthopedics, Pediatrics, "
            "Psychiatry, Pulmonology, Radiology, Urology. "
            "If symptoms don't match, use General Medicine. "
            "This will retrieve the list of available doctors for the session."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "department_name": {
                    "type": "STRING",
                    "description": "Exact department name from the supported list.",
                },
            },
            "required": ["department_name"],
        },
    },
    {
        "name": "select_doctor_by_name",
        "description": (
            "Select a doctor from the available doctors list by their spoken name. "
            "This will automatically load that doctor's upcoming available appointment slots."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "doctor_name": {
                    "type": "STRING",
                    "description": "Spoken name of the doctor (e.g. Anil Kumar).",
                },
            },
            "required": ["doctor_name"],
        },
    },
    {
        "name": "select_appointment_slot",
        "description": (
            "Select an appointment slot by its spoken time and day/date from the available slot list."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "time_str": {
                    "type": "STRING",
                    "description": "Spoken start time of the slot (e.g. 10:30 AM).",
                },
                "date_or_day": {
                    "type": "STRING",
                    "description": "Spoken day of week or date (e.g. Monday, 23 Jun).",
                },
            },
            "required": ["time_str"],
        },
    },
    {
        "name": "lock_and_confirm_booking",
        "description": (
            "Book the appointment after the patient has verbally confirmed all details. "
            "This locks the slot, creates a pending appointment, generates an invoice, "
            "and creates a Razorpay payment link. Only call this AFTER the patient says 'yes' or 'confirm'."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "symptoms": {
                    "type": "STRING",
                    "description": "Patient's symptoms as a concise summary for the doctor's notes.",
                },
            },
            "required": ["symptoms"],
        },
    },
]
