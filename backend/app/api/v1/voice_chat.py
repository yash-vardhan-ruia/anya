import re
import uuid
import time
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.voice.session_manager import VoiceSessionManager
from app.voice.orchestrator import VoiceOrchestrator
from app.voice.prompts import get_state_prompt
from app.voice.tool_executor import execute_tool
from app.integrations.razorpay_client import razorpay_client

router = APIRouter()

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Replace with your actual Gemini API key

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


class VoiceChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class VoiceChatResponse(BaseModel):
    session_id: str
    reply: str
    state: str


def extract_patient_updates(message: str) -> dict:
    updates = {}
    text = message.strip()

    name_match = re.search(
        r"(?:my name is|this is)\s+([A-Za-z][A-Za-z\s.'-]{1,80})",
        text,
        re.IGNORECASE,
    )
    if name_match:
        name = name_match.group(1).strip()
        if not re.search(r"\d", name) and len(name.split()) <= 5:
            updates["patient_name"] = name

    age_match = re.search(
        r"\b(?:i am|age is|my age is)\s+(\d{1,3})\b",
        text,
        re.IGNORECASE,
    )
    if age_match:
        updates["age"] = int(age_match.group(1))

    phone_match = re.search(r"(\+91[\s-]?)?[6-9]\d{9}", text)
    if phone_match:
        phone = phone_match.group(0).replace(" ", "").replace("-", "")
        if not phone.startswith("+91"):
            phone = "+91" + phone
        updates["phone"] = phone

    return updates


def detect_department_from_text(text: str) -> str:
    text = text.lower()

    if any(word in text for word in ["chest pain", "heart", "bp", "blood pressure", "palpitation"]):
        return "Cardiology"

    if any(word in text for word in ["child", "baby", "kid", "children"]):
        return "Pediatrics"

    if any(word in text for word in ["bone", "joint", "knee", "back pain", "fracture", "shoulder"]):
        return "Orthopedics"

    if any(word in text for word in ["skin", "rash", "itching", "acne"]):
        return "Dermatology"

    return "General Medicine"


def build_gemini_prompt(system_prompt: str, history: list, user_message: str) -> str:
    history_text = ""

    for item in history[-10:]:
        role = item.get("role", "user")
        content = item.get("content", "")
        history_text += f"{role.upper()}: {content}\n"

    return f"""
{system_prompt}

You are running in browser microphone mode, not Twilio mode.

Rules:
- You are Anya, a hospital receptionist.
- Speak naturally and politely.
- Keep replies short for voice conversation.
- Ask only one question at a time.
- Collect these details step by step:
  1. Patient full name
  2. Age
  3. Phone number
  4. Symptoms or reason for visit
  5. Preferred department, doctor, date, or time
- Do not diagnose disease.
- Do not give medical treatment advice.
- If symptoms sound emergency related, tell the user to call emergency services or visit emergency department immediately.

Conversation history:
{history_text}

Current user message:
USER: {user_message}

Reply as Anya in 1-3 short sentences.
"""


async def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key missing in voice_chat.py",
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 300,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini error: {response.text}",
        )

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return "Sorry, I could not understand that. Could you please say it again?"


@router.post("/message", response_model=VoiceChatResponse)
async def voice_chat_message(payload: VoiceChatRequest):
    session_id = payload.session_id or f"web-{uuid.uuid4()}"
    user_message = payload.message.strip()

    patient_updates = extract_patient_updates(user_message)

    if patient_updates:
        await VoiceSessionManager.update_session(
            session_id,
            patient_updates,
        )

    updated_session = await VoiceSessionManager.update_session(
        session_id,
        {},
    )

    updated_session = await VoiceOrchestrator.process_conversational_step(
        call_sid=session_id,
        user_transcript=user_message,
    )

    state = updated_session.get("current_state", "greeting")

    if updated_session.get("is_emergency"):
        reply = (
            "This sounds like an emergency. Please call emergency services "
            "or visit the emergency department immediately."
        )

        return VoiceChatResponse(
            session_id=session_id,
            reply=reply,
            state=state,
        )

    symptom_keywords = [
        "fever", "headache", "cough", "cold", "pain", "vomiting",
        "weakness", "chest", "heart", "skin", "rash", "bone",
        "joint", "child", "baby", "stomach"
    ]

    if any(word in user_message.lower() for word in symptom_keywords):
        department_name = detect_department_from_text(user_message)

        doctors_result = await execute_tool(
            "find_doctor",
            {
                "department_name": department_name,
            },
            session_id,
        )

        doctors = doctors_result.get("doctors", [])

        await VoiceSessionManager.update_session(
            session_id,
            {
                "symptoms": user_message,
                "department_name": department_name,
                "available_doctors": doctors,
                "current_state": "doctor",
            },
        )

        if not doctors:
            return VoiceChatResponse(
                session_id=session_id,
                reply=f"Based on your symptoms, {department_name} looks suitable, but I could not find an available doctor right now.",
                state="doctor",
            )

        doctor_lines = []
        for index, doctor in enumerate(doctors[:3], start=1):
            fee = doctor.get("consultation_fee_inr", 0)
            doctor_lines.append(
                f"{index}. {doctor.get('full_name')} ({doctor.get('specialization')}), fee ₹{fee}"
            )

        reply = (
            f"Based on your symptoms, {department_name} looks suitable. "
            f"I found these doctors: {' '.join(doctor_lines)}. "
            "Which doctor would you prefer?"
        )

        return VoiceChatResponse(
            session_id=session_id,
            reply=reply,
            state="doctor",
        )

    if state == "doctor":
        session = await VoiceSessionManager.get_session(session_id)
        available_doctors = session.get("available_doctors", [])

        number_match = re.search(r"\b(\d+)\b", user_message)

        if not number_match:
            return VoiceChatResponse(
                session_id=session_id,
                reply="Please choose a doctor by saying Doctor 1, Doctor 2, or Doctor 3.",
                state="doctor",
            )

        selected_index = int(number_match.group(1)) - 1

        if selected_index < 0 or selected_index >= len(available_doctors):
            return VoiceChatResponse(
                session_id=session_id,
                reply="That doctor option is not available.",
                state="doctor",
            )

        selected_doctor = available_doctors[selected_index]
        target_date = "2026-06-15"

        slots_result = await execute_tool(
            "get_slots",
            {
                "doctor_id": selected_doctor["doctor_id"],
                "target_date": target_date,
            },
            session_id,
        )

        slots = slots_result.get("slots", [])

        await VoiceSessionManager.update_session(
            session_id,
            {
                "doctor_id": selected_doctor["doctor_id"],
                "doctor_name": selected_doctor["full_name"],
                "available_slots": slots,
                "current_state": "slot",
            },
        )

        if not slots:
            return VoiceChatResponse(
                session_id=session_id,
                reply=f"Dr. {selected_doctor['full_name']} is selected, but no slots are available today.",
                state="slot",
            )

        slot_lines = []

        for index, slot in enumerate(slots[:5], start=1):
            slot_lines.append(f"{index}. {slot['start_time']}")

        reply = (
            f"{selected_doctor['full_name']} is selected. "
            f"Available slots are: {' '.join(slot_lines)}. "
            "Which slot would you like?"
        )

        return VoiceChatResponse(
            session_id=session_id,
            reply=reply,
            state="slot",
        )

    if state == "slot":
        session = await VoiceSessionManager.get_session(session_id)
        available_slots = session.get("available_slots", []) if session else []

        number_match = re.search(r"\b(\d+)\b", user_message)

        if not number_match:
            return VoiceChatResponse(
                session_id=session_id,
                reply="Please choose a slot by saying Slot 1, Slot 2, or Slot 3.",
                state="slot",
            )

        selected_index = int(number_match.group(1)) - 1

        if selected_index < 0 or selected_index >= len(available_slots):
            return VoiceChatResponse(
                session_id=session_id,
                reply="That slot option is not available. Please choose from the listed slots.",
                state="slot",
            )

        selected_slot = available_slots[selected_index]

        lock_result = await execute_tool(
            "lock_slot",
            {
                "slot_id": selected_slot["slot_id"],
            },
            session_id,
        )

        if not lock_result.get("success"):
            return VoiceChatResponse(
                session_id=session_id,
                reply="Sorry, that slot could not be locked. Please choose another available slot.",
                state="slot",
            )

        await VoiceSessionManager.update_session(
            session_id,
            {
                "slot_id": selected_slot["slot_id"],
                "slot_time_str": selected_slot["start_time"],
                "slot_date_str": "2026-06-15",
                "current_state": "review",
            },
        )

        session = await VoiceSessionManager.get_session(session_id)


        patient_name = session.get("patient_name", "not provided")
        age = session.get("age", "not provided")
        phone = session.get("phone", "not provided")
        symptoms = session.get("symptoms", "not provided")
        department_name = session.get("department_name", "General Medicine")
        doctor_name = session.get("doctor_name", "the selected doctor")
        slot_time = session.get("slot_time_str", selected_slot["start_time"])
        slot_date = session.get("slot_date_str", "2026-06-15")

        reply = (
            f"Your slot is temporarily locked. Please review the details: "
            f"Patient name: {patient_name}. "
            f"Age: {age}. "
            f"Phone: {phone}. "
            f"Symptoms: {symptoms}. "
            f"Department: {department_name}. "
            f"Doctor: {doctor_name}. "
            f"Date: {slot_date}. "
            f"Time: {slot_time}. "
            "Should I confirm this appointment?"
        )

        return VoiceChatResponse(
            session_id=session_id,
            reply=reply,
            state="review",
        )

    if state == "review":
        if not any(word in user_message.lower() for word in ["yes", "confirm", "book", "okay", "ok"]):
            return VoiceChatResponse(
                session_id=session_id,
                reply="No problem. Please say yes confirm when you want me to book this appointment.",
                state="review",
            )

        session = await VoiceSessionManager.get_session(session_id)

        patient_name = session.get("patient_name")
        phone = session.get("phone")
        doctor_name = session.get("doctor_name")
        slot_id = session.get("slot_id")
        slot_date = session.get("slot_date_str")
        slot_time = session.get("slot_time_str")
        department_name = session.get("department_name")

        if not patient_name or not phone or not slot_id:
            return VoiceChatResponse(
                session_id=session_id,
                reply="Some booking details are missing. Please restart the booking.",
                state="review",
            )

        available_doctors = session.get("available_doctors", [])
        

        if available_doctors:
            fee_inr = available_doctors[0].get("consultation_fee_inr", 500)
            gst_rate = 18
            amount_paise = int(round(fee_inr * 100 * (1 + gst_rate / 100))) 

        expire_by = int(time.time()) + (20 * 60)

        payment_link = razorpay_client.create_payment_link(
            amount_paise=amount_paise,
            customer_name=patient_name,
            customer_phone=phone,
            description=f"Appointment with {doctor_name}",
            reference_id=session_id[:40],
            expire_by=expire_by,
            notes={
                "session_id": session_id,
                "slot_id": slot_id,
                "patient_name": patient_name,
                "phone": phone,
                "doctor_name": doctor_name,
                "department_name": department_name,
                "slot_date": slot_date,
                "slot_time": slot_time,
            },
        )

        await VoiceSessionManager.update_session(
            session_id,
            {
                "current_state": "payment",
                "payment_link_id": payment_link.get("id"),
                "payment_link_url": payment_link.get("short_url"),
                "payment_expires_at": expire_by,
            },
        )


        return VoiceChatResponse(
            session_id=session_id,
            reply=(
                f"Payment link generated successfully. "
                f"Amount is INR 590. "
                f"A payment link has been sent to {phone}. "
                f"Link: {payment_link.get('short_url')}"
            ),
            state="payment",
        )

    history = updated_session.get("chat_history", [])
    system_prompt = get_state_prompt(state, updated_session)
    gemini_prompt = build_gemini_prompt(system_prompt, history, user_message)
    reply = await call_gemini(gemini_prompt)

    new_history = history[-10:] + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    final_session = await VoiceSessionManager.update_session(
        session_id,
        {
            "chat_history": new_history,
        },
    )

    return VoiceChatResponse(
        session_id=session_id,
        reply=reply,
        state=final_session.get("current_state", state),
    )