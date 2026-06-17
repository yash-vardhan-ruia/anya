"""
CareVoice AI Hospital Platform - Voice Tool Executor.

Implements the Gemini tool handlers for the hybrid voice + browser flow.
Tools update the Redis session and emit WebSocket events for browser UI updates.
"""

import uuid
import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.slot import DoctorSlot
from app.core.constants import SlotStatus
from app.services.patient_service import PatientService
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService
from app.services.appointment_service import AppointmentService
from app.services.billing_service import BillingService
from app.integrations.razorpay_client import razorpay_client
from app.schemas.appointment import AppointmentCreate

logger = structlog.get_logger(__name__)


async def _handle_check_patient_by_email(tool_args: dict, session: dict, db: AsyncSession) -> tuple[dict, dict, list[dict]]:
    """Check if a returning patient exists based on the email."""
    email = tool_args.get("email") or session.get("email")
    if not email:
        return {"exists": False, "message": "Email not provided."}, {}, []

    email = email.lower().strip()
    stmt = select(Patient).where(Patient.email == email)
    patient = (await db.execute(stmt)).scalar_one_or_none()

    if patient:
        session_updates = {
            "patient_id": str(patient.id),
            "patient_name": patient.full_name,
            "email": email,
            "visit_type": "returning"
        }
        result = {
            "exists": True,
            "patient_id": str(patient.id),
            "patient_name": patient.full_name,
            "message": f"Welcome back, {patient.full_name}!"
        }
        return result, session_updates, []
    else:
        result = {"exists": False, "message": "No patient found with that email. Please check and try again."}
        # In a pure voice workflow, we ask the patient verbally to repeat or check,
        # but we also trigger a voice alert state.
        return result, {}, []


async def _handle_update_patient_details(tool_args: dict, session: dict, db: AsyncSession) -> tuple[dict, dict, list[dict]]:
    """Update patient information in Redis session as they speak each detail."""
    full_name = tool_args.get("full_name")
    age = tool_args.get("age")
    gender = tool_args.get("gender")
    email = tool_args.get("email")

    session_updates = {}
    if full_name:
        session_updates["patient_name"] = full_name
    if age is not None:
        session_updates["age"] = str(age)
    if gender:
        session_updates["gender"] = gender
    if email:
        session_updates["email"] = email.lower().strip()

    result = {
        "success": True,
        "message": f"Updated session fields: {list(session_updates.keys())}"
    }

    # Redis updates will auto-broadcast state to the browser
    return result, session_updates, []


async def _handle_create_new_patient(tool_args: dict, session: dict, db: AsyncSession) -> tuple[dict, dict, list[dict]]:
    """Create a new patient using registration info."""
    full_name = tool_args.get("full_name") or session.get("patient_name")
    age = tool_args.get("age") or session.get("age")
    gender = tool_args.get("gender") or session.get("gender")
    email = tool_args.get("email") or session.get("email")

    if not email:
        return {"success": False, "message": "Email missing from session/args."}, {}, []
    if not full_name:
        return {"success": False, "message": "Full name missing from session/args."}, {}, []

    email = email.lower().strip()
    
    # Check if patient already exists by email
    patient = await PatientService.get_or_create_patient_by_email(db, email=email, full_name=full_name)
    
    # Update gender and other details
    if hasattr(patient, "gender") and gender:
        patient.gender = gender
        await db.commit()
        await db.refresh(patient)

    session_updates = {
        "patient_id": str(patient.id),
        "patient_name": patient.full_name,
        "age": str(age) if age else None,
        "gender": gender,
        "visit_type": "new"
    }
    
    result = {
        "success": True,
        "patient_id": str(patient.id),
        "mrn": patient.medical_record_number,
        "message": f"Patient {full_name} registered successfully."
    }
    return result, session_updates, []


async def _handle_find_doctors_by_department(tool_args: dict, session: dict, db: AsyncSession) -> tuple[dict, dict, list[dict]]:
    """Find doctors and trigger browser cards."""
    department_name = tool_args.get("department_name")
    if not department_name:
        return {"error": "Missing department_name"}, {}, []

    # Get department
    dept = await DoctorService.get_department_by_name(db, department_name)
    fallback_used = False
    
    if not dept:
        dept = await DoctorService.get_department_by_name(db, "General Medicine")
        fallback_used = True
        if not dept:
            return {"error": "Department not found"}, {}, []

    # Get doctors
    _, doctors = await DoctorService.list_doctors(db, department_id=dept.id, active_only=True, limit=5)
    
    if not doctors and not fallback_used:
        # Fall back to General Medicine if no doctors in this dept
        dept_gm = await DoctorService.get_department_by_name(db, "General Medicine")
        if dept_gm:
            dept = dept_gm
            fallback_used = True
            _, doctors = await DoctorService.list_doctors(db, department_id=dept.id, active_only=True, limit=5)

    doctor_cards = []
    for doc in doctors:
        fee_inr = round(float(doc.consultation_fee) / 100.0, 0) if doc.consultation_fee else 0
        doctor_cards.append({
            "id": str(doc.id),
            "name": doc.full_name,
            "specialization": doc.specialization or "Specialist",
            "qualification": doc.qualification or "",
            "experience_years": doc.experience_years or 0,
            "fee_inr": fee_inr,
        })

    session_updates = {
        "department_id": str(dept.id),
        "department_name": dept.name,
        "available_doctors": doctor_cards
    }
    
    result = {
        "department": dept.name,
        "doctors": doctor_cards,
        "count": len(doctor_cards),
        "fallback_used": fallback_used
    }
    
    ws_events = [{
        "type": "show_doctors",
        "department": dept.name,
        "doctors": doctor_cards
    }]
    
    return result, session_updates, ws_events


async def _handle_select_doctor_by_name(tool_args: dict, session: dict, db: AsyncSession) -> tuple[dict, dict, list[dict]]:
    """Select a doctor by their spoken name, then automatically fetch their available slots."""
    doctor_name = tool_args.get("doctor_name")
    if not doctor_name:
        return {"error": "Missing doctor_name"}, {}, []

    available_doctors = session.get("available_doctors", [])
    matched_doc = None
    
    # Normalize spoken name
    spoken_norm = doctor_name.lower().replace("dr.", "").replace("doctor", "").strip()
    
    # Try match
    for doc in available_doctors:
        doc_norm = doc["name"].lower().replace("dr.", "").replace("doctor", "").strip()
        if spoken_norm in doc_norm or doc_norm in spoken_norm:
            matched_doc = doc
            break

    if not matched_doc:
        # DB lookup fallback if not in department list
        stmt = select(Doctor).where(and_(Doctor.full_name.ilike(f"%{spoken_norm}%"), Doctor.is_active == True))
        doc_obj = (await db.execute(stmt)).scalars().first()
        if doc_obj:
            matched_doc = {
                "id": str(doc_obj.id),
                "name": doc_obj.full_name,
                "specialization": doc_obj.specialization or "Specialist",
                "fee_inr": round(float(doc_obj.consultation_fee) / 100.0, 0) if doc_obj.consultation_fee else 0,
            }

    if not matched_doc:
        available_docs_str = ", ".join([d["name"] for d in available_doctors]) if available_doctors else "available list"
        return {"error": f"Doctor '{doctor_name}' not found. Please choose from the available doctors: {available_docs_str}."}, {}, []

    doc_id = matched_doc["id"]
    doc_fullname = matched_doc["name"]

    # Trigger slots fetching
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=7)
    await SlotService.generate_slots_for_doctor(db, doctor_id=uuid.UUID(doc_id), start_date=today, end_date=end_date)

    now = datetime.datetime.now(datetime.timezone.utc).time()
    
    stmt = select(DoctorSlot).where(
        and_(
            DoctorSlot.doctor_id == uuid.UUID(doc_id),
            DoctorSlot.status == SlotStatus.AVAILABLE,
            or_(
                DoctorSlot.date > today,
                and_(DoctorSlot.date == today, DoctorSlot.start_time >= now)
            )
        )
    ).order_by(DoctorSlot.date.asc(), DoctorSlot.start_time.asc()).limit(6)
    
    slots_result = await db.execute(stmt)
    slots = list(slots_result.scalars().all())

    slot_cards = []
    for s in slots:
        slot_cards.append({
            "id": str(s.id),
            "date": s.date.strftime("%a, %d %b %Y"),
            "day": s.date.strftime("%A"),
            "start_time": s.start_time.strftime("%I:%M %p"),
            "end_time": s.end_time.strftime("%I:%M %p"),
            "date_iso": s.date.isoformat(),
        })

    session_updates = {
        "doctor_id": doc_id,
        "doctor_name": doc_fullname,
        "available_slots": slot_cards
    }

    if not slot_cards:
        result = {
            "success": True,
            "doctor_name": doc_fullname,
            "slots": [],
            "count": 0,
            "message": "No slots available for this doctor."
        }
        ws_events = [{
            "type": "show_slots",
            "slots": [],
            "message": "No available slots found. Please try another doctor."
        }]
    else:
        result = {
            "success": True,
            "doctor_name": doc_fullname,
            "slots": slot_cards,
            "count": len(slot_cards)
        }
        ws_events = [{
            "type": "show_slots",
            "doctor_name": doc_fullname,
            "slots": slot_cards
        }]

    return result, session_updates, ws_events


async def _handle_get_available_slots(tool_args: dict, session: dict, db: AsyncSession) -> tuple[dict, dict, list[dict]]:
    """Fetch slots for doctor and trigger browser cards (retained for backward compatibility)."""
    doctor_id = tool_args.get("doctor_id") or session.get("doctor_id")
    if not doctor_id:
        return {"error": "No doctor_id provided"}, {}, []

    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=7)
    await SlotService.generate_slots_for_doctor(db, doctor_id=uuid.UUID(doctor_id), start_date=today, end_date=end_date)

    now = datetime.datetime.now(datetime.timezone.utc).time()
    
    stmt = select(DoctorSlot).where(
        and_(
            DoctorSlot.doctor_id == uuid.UUID(doctor_id),
            DoctorSlot.status == SlotStatus.AVAILABLE,
            or_(
                DoctorSlot.date > today,
                and_(DoctorSlot.date == today, DoctorSlot.start_time >= now)
            )
        )
    ).order_by(DoctorSlot.date.asc(), DoctorSlot.start_time.asc()).limit(6)
    
    slots_result = await db.execute(stmt)
    slots = list(slots_result.scalars().all())

    slot_cards = []
    for s in slots:
        slot_cards.append({
            "id": str(s.id),
            "date": s.date.strftime("%a, %d %b %Y"),
            "day": s.date.strftime("%A"),
            "start_time": s.start_time.strftime("%I:%M %p"),
            "end_time": s.end_time.strftime("%I:%M %p"),
            "date_iso": s.date.isoformat(),
        })

    session_updates = {
        "doctor_id": doctor_id,
        "available_slots": slot_cards
    }

    if not slot_cards:
        result = {"slots": [], "count": 0, "message": "No slots available"}
        ws_events = [{
            "type": "show_slots",
            "slots": [],
            "message": "No available slots found. Please try another doctor."
        }]
    else:
        result = {"slots": slot_cards, "count": len(slot_cards)}
        ws_events = [{
            "type": "show_slots",
            "doctor_name": session.get("doctor_name", ""),
            "slots": slot_cards
        }]

    return result, session_updates, ws_events


async def _handle_select_appointment_slot(tool_args: dict, session: dict, db: AsyncSession) -> tuple[dict, dict, list[dict]]:
    """Select a slot by spoken time and day, updating the session."""
    time_str = tool_args.get("time_str")
    date_or_day = tool_args.get("date_or_day")

    if not time_str:
        return {"error": "Missing time_str"}, {}, []

    available_slots = session.get("available_slots", [])
    if not available_slots:
        return {"error": "No slots are currently available. Please select a doctor first."}, {}, []

    matched_slot = None
    time_norm = time_str.lower().replace(" ", "").strip()
    day_norm = date_or_day.lower().strip() if date_or_day else None

    # Try match
    for slot in available_slots:
        slot_time_norm = slot["start_time"].lower().replace(" ", "").strip()
        slot_day_norm = slot["day"].lower().strip()
        slot_date_norm = slot["date"].lower().strip()

        # Match time
        time_match = (time_norm in slot_time_norm) or (slot_time_norm in time_norm)
        
        # Match day/date
        day_match = True
        if day_norm:
            day_match = (day_norm in slot_day_norm) or (day_norm in slot_date_norm)

        if time_match and day_match:
            matched_slot = slot
            break

    # fallback to matching just time if day provided but no exact day match found
    if not matched_slot and day_norm:
        for slot in available_slots:
            slot_time_norm = slot["start_time"].lower().replace(" ", "").strip()
            if (time_norm in slot_time_norm) or (slot_time_norm in time_norm):
                matched_slot = slot
                break

    # fallback to first slot if terms like first/any used
    if not matched_slot:
        if "first" in time_norm or "any" in time_norm or "one" in time_norm:
            matched_slot = available_slots[0]
        else:
            available_slots_str = ", ".join([f"{s['day']} at {s['start_time']}" for s in available_slots]) if available_slots else "available list"
            return {"error": f"Slot matching '{time_str}' not found. Please choose from the available slots: {available_slots_str}."}, {}, []

    session_updates = {
        "slot_id": matched_slot["id"],
        "slot_date_str": matched_slot["date"],
        "slot_time_str": f"{matched_slot['start_time']} - {matched_slot['end_time']}"
    }

    result = {
        "success": True,
        "slot_id": matched_slot["id"],
        "date": matched_slot["date"],
        "time": f"{matched_slot['start_time']} - {matched_slot['end_time']}",
        "message": "Slot selected successfully."
    }

    return result, session_updates, []


async def _handle_lock_and_confirm_booking(tool_args: dict, session: dict, db: AsyncSession) -> tuple[dict, dict, list[dict]]:
    """Book appointment and trigger Razorpay redirect in browser."""
    symptoms = tool_args.get("symptoms", "")
    
    p_id = session.get("patient_id")
    d_id = session.get("doctor_id")
    s_id = session.get("slot_id")
    dep_id = session.get("department_id")

    if not all([p_id, d_id, s_id, dep_id]):
        return {"success": False, "error": "Booking info incomplete — patient, doctor, and slot must all be selected first"}, {}, []

    # 1. Lock slot
    try:
        await SlotService.lock_slot(db, slot_id=uuid.UUID(s_id), locked_by=session["session_id"])
    except Exception as e:
        logger.warning("Slot lock error", error=str(e))
        pass  # might already be locked by this session

    # 2. Create appointment
    slot = await db.get(DoctorSlot, uuid.UUID(s_id))
    if not slot:
        return {"success": False, "error": "Slot not found"}, {}, []

    appt_schema = AppointmentCreate(
        patient_id=uuid.UUID(p_id),
        doctor_id=uuid.UUID(d_id),
        slot_id=uuid.UUID(s_id),
        department_id=uuid.UUID(dep_id),
        appointment_date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        symptoms=symptoms,
        notes="Booked via voice assistant Anya",
    )
    
    try:
        appointment = await AppointmentService.create_appointment(
            db, appt_schema, locked_by_session=session["session_id"], commit=False
        )

        # 3. Get invoice
        invoice = await BillingService.get_invoice_by_appointment(db, appointment.id)
        if not invoice:
            invoice = await BillingService.create_invoice(db, appointment.id)
        amount_inr = float(invoice.total_amount)

        # 4. Create Razorpay link
        patient_email = session.get("email", "")
        patient_name = session.get("patient_name", "Patient")
        
        payment_link = razorpay_client.create_payment_link(
            amount_paise=int(round(amount_inr * 100)),
            description=f"Appointment with Dr. {session.get('doctor_name', '')}",
            customer_name=patient_name,
            customer_email=patient_email,
            notes={"appointment_id": str(appointment.id), "session_id": session["session_id"]},
        )
        payment_url = payment_link.get("short_url") or payment_link.get("id", "")

        # Commit everything to the database now that everything succeeded
        await db.commit()
        await db.refresh(appointment)
        
    except Exception as e:
        await db.rollback()
        logger.error("Error confirming booking, rolled back transaction", error=str(e))
        return {"success": False, "error": f"Booking failed: {str(e)}"}, {}, []

    # 5. Build responses
    session_updates = {
        "appointment_id": str(appointment.id),
        "amount_inr": amount_inr,
        "payment_link_url": payment_url,
        "payment_sent": True,
        "symptoms": symptoms,
    }

    result = {
        "success": True,
        "appointment_id": str(appointment.id),
        "doctor_name": session.get("doctor_name"),
        "date": session.get("slot_date_str"),
        "time": session.get("slot_time_str"),
        "amount_inr": amount_inr,
        "payment_url": payment_url,
        "message": "Appointment booked successfully. Payment link generated.",
    }

    ws_events = [{
        "type": "redirect_payment",
        "payment_url": payment_url,
        "amount_inr": amount_inr
    }]

    return result, session_updates, ws_events


async def execute_tool(
    tool_name: str,
    tool_args: dict,
    session: dict,
    db: AsyncSession,
) -> tuple[dict, dict, list[dict]]:
    """Execute a Gemini tool and return (result, session_updates, ws_events)."""
    logger.info("Executing tool", tool_name=tool_name, args=tool_args)

    handlers = {
        "check_patient_by_email": _handle_check_patient_by_email,
        "update_patient_details": _handle_update_patient_details,
        "create_new_patient": _handle_create_new_patient,
        "find_doctors_by_department": _handle_find_doctors_by_department,
        "select_doctor_by_name": _handle_select_doctor_by_name,
        "get_available_slots": _handle_get_available_slots,
        "select_appointment_slot": _handle_select_appointment_slot,
        "lock_and_confirm_booking": _handle_lock_and_confirm_booking,
    }

    handler = handlers.get(tool_name)
    if not handler:
        logger.error("Unknown tool", tool_name=tool_name)
        return {"error": f"Unknown tool: {tool_name}"}, {}, []

    try:
        return await handler(tool_args, session, db)
    except Exception as e:
        logger.exception("Error executing tool", tool_name=tool_name, error=str(e))
        return {"error": str(e)}, {}, []
