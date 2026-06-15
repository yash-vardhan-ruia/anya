"""
CareVoice AI Hospital Platform - Voice Tool Executor.

Binds the Gemini Live API tool calling system to the async database session
and domain business services, returning clean JSON results to feed back to the AI.
"""

import uuid
import datetime
import structlog
from sqlalchemy import select
from app.database import async_session_factory
from app.core.constants import SlotStatus, ConversationState
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.slot import DoctorSlot
from app.schemas.appointment import AppointmentCreate
from app.services.slot_service import SlotService
from app.services.patient_service import PatientService
from app.services.appointment_service import AppointmentService
from app.services.billing_service import BillingService
from app.voice.session_manager import VoiceSessionManager

logger = structlog.get_logger(__name__)


def map_department_name(dept_name: str) -> str:
    if not dept_name:
        return dept_name
    normalized = dept_name.lower().strip()
    
    # Mapping dictionary to map clinical synonyms or colloquial terms to database department names
    mappings = {
        "general medicine": "General Medicine",
        "general physician": "General Medicine",
        "general practitioner": "General Medicine",
        "physician": "General Medicine",
        "gp": "General Medicine",
        "medicine": "General Medicine",
        "pediatrics": "Pediatrics",
        "pediatrician": "Pediatrics",
        "child": "Pediatrics",
        "kids": "Pediatrics",
        "cardiology": "Cardiology",
        "cardiologist": "Cardiology",
        "heart": "Cardiology",
        "orthopedics": "Orthopedics",
        "orthopedist": "Orthopedics",
        "bone": "Orthopedics",
        "bones": "Orthopedics",
        "joints": "Orthopedics",
        "dermatology": "Dermatology",
        "dermatologist": "Dermatology",
        "skin": "Dermatology",
        "neurology": "Neurology",
        "neurologist": "Neurology",
        "brain": "Neurology",
        "psychiatry": "Psychiatry",
        "psychiatrist": "Psychiatry",
        "mental": "Psychiatry",
        "oncology": "Oncology",
        "oncologist": "Oncology",
        "cancer": "Oncology",
        "ophthalmology": "Ophthalmology",
        "ophthalmologist": "Ophthalmology",
        "eye": "Ophthalmology",
        "eyes": "Ophthalmology",
        "ent": "ENT",
        "ear": "ENT",
        "nose": "ENT",
        "throat": "ENT",
        "pulmonology": "Pulmonology",
        "pulmonologist": "Pulmonology",
        "lungs": "Pulmonology",
        "gastroenterology": "Gastroenterology",
        "gastroenterologist": "Gastroenterology",
        "stomach": "Gastroenterology",
        "urology": "Urology",
        "urologist": "Urology",
    }
    
    # Check for direct or partial match
    for key, value in mappings.items():
        if key in normalized or normalized in key:
            return value
            
    return dept_name


async def execute_tool(name: str, arguments: dict, call_sid: str) -> dict:
    """Route and execute tool calls requested by the Gemini Live API model asynchronously."""
    logger.info("Executing voice tool call", tool_name=name, arguments=arguments, call_sid=call_sid)

    async with async_session_factory() as db:
        try:
            if name == "find_doctor":
                dept_name = arguments.get("department_name")
                search_query = arguments.get("search_query")

                stmt = select(Doctor).join(Department).where(Doctor.is_active == True)
                
                if dept_name:
                    mapped_dept = map_department_name(dept_name)
                    stmt = stmt.where(Department.name.ilike(f"%{mapped_dept}%"))
                if search_query:
                    stmt = stmt.where(
                        Doctor.full_name.ilike(f"%{search_query}%")
                        | Doctor.specialization.ilike(f"%{search_query}%")
                    )

                result = await db.execute(stmt)
                doctors = result.scalars().all()

                doctor_list = []
                for doc in doctors:
                    doctor_list.append({
                        "doctor_id": str(doc.id),
                        "full_name": doc.full_name,
                        "specialization": doc.specialization,
                        "consultation_fee_inr": doc.consultation_fee / 100.0,
                        "experience_years": doc.experience_years,
                        "department_name": doc.department.name,
                    })

                logger.info("Executed find_doctor", count=len(doctor_list))
                return {"success": True, "doctors": doctor_list[:5]}

            elif name == "get_slots":
                doctor_id_str = arguments.get("doctor_id")
                target_date_str = arguments.get("target_date")

                try:
                    doctor_uuid = uuid.UUID(doctor_id_str)
                except (ValueError, TypeError):
                    return {"success": False, "message": f"Invalid doctor ID format: '{doctor_id_str}'"}

                # Parse date (format YYYY-MM-DD)
                try:
                    target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    return {"success": False, "message": f"Invalid target date format: '{target_date_str}' (expected YYYY-MM-DD)"}

                # Generate slots for today/tomorrow automatically on search to ensure they exist
                try:
                    await SlotService.generate_slots_for_doctor(db, doctor_uuid, target_date, target_date)
                except Exception as gen_exc:
                    logger.warning("Failed to auto-generate slots for doctor", error=str(gen_exc), doctor_id=doctor_id_str)

                slots = await SlotService.list_available_slots(db, doctor_uuid, target_date)
                
                slot_list = []
                for slot in slots:
                    slot_status = slot.status.value if hasattr(slot.status, "value") else slot.status
                    slot_list.append({
                        "slot_id": str(slot.id),
                        "start_time": slot.start_time.strftime("%I:%M %p"),
                        "end_time": slot.end_time.strftime("%I:%M %p"),
                        "status": slot_status,
                    })

                logger.info("Executed get_slots", count=len(slot_list), date=target_date_str)
                return {"success": True, "slots": slot_list[:8]}

            elif name == "lock_slot":
                slot_id_str = arguments.get("slot_id")
                try:
                    slot_uuid = uuid.UUID(slot_id_str)
                except (ValueError, TypeError):
                    return {"success": False, "message": f"Invalid slot ID format: '{slot_id_str}'"}

                # Attempt lock
                locked = await SlotService.lock_slot(db, slot_uuid, locked_by=call_sid)
                if not locked:
                    return {"success": False, "message": "Failed to lock slot. It may have been booked or locked already."}

                slot = await db.get(DoctorSlot, slot_uuid)
                
                # Update Redis state
                await VoiceSessionManager.update_session(call_sid, {
                    "doctor_id": str(slot.doctor_id),
                    "doctor_name": slot.doctor.full_name,
                    "department_id": str(slot.doctor.department_id),
                    "department_name": slot.doctor.department.name,
                    "slot_id": slot_id_str,
                    "slot_time_str": slot.start_time.strftime("%I:%M %p"),
                    "slot_date_str": slot.date.strftime("%Y-%m-%d"),
                })

                logger.info("Executed lock_slot", slot_id=slot_id_str, success=True)
                return {
                    "success": True, 
                    "slot_time": slot.start_time.strftime("%I:%M %p"),
                    "slot_date": slot.date.strftime("%Y-%m-%d"),
                    "doctor_name": slot.doctor.full_name,
                    "message": "Slot locked successfully for 5 minutes."
                }

            elif name == "confirm_booking":
                patient_name = arguments.get("patient_name")
                phone = arguments.get("phone")
                slot_id_str = arguments.get("slot_id")

                try:
                    slot_uuid = uuid.UUID(slot_id_str)
                except (ValueError, TypeError):
                    return {"success": False, "message": f"Invalid slot ID format: '{slot_id_str}'"}

                # Normalize phone to +91 E.164-like format
                if phone:
                    phone = phone.replace(" ", "").replace("-", "")
                    if not phone.startswith("+"):
                        if len(phone) == 10:
                            phone = "+91" + phone
                        elif len(phone) == 12 and phone.startswith("91"):
                            phone = "+" + phone

                slot = await db.get(DoctorSlot, slot_uuid)
                if not slot:
                    return {"success": False, "message": "Time slot not found."}

                # 1. Get or create patient
                patient = await PatientService.get_or_create_patient_by_phone(db, phone, patient_name)

                # 2. Book appointment
                appt_schema = AppointmentCreate(
                    patient_id=patient.id,
                    doctor_id=slot.doctor_id,
                    slot_id=slot.id,
                    department_id=slot.doctor.department_id,
                    appointment_date=slot.date,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    symptoms=arguments.get("symptoms"),
                    notes=f"Booked via Anya AI Voice Assistant call session {call_sid}.",
                )

                # Call appointment booking service (this generates invoice + trigger Celery notifications)
                appointment = await AppointmentService.create_appointment(db, appt_schema, locked_by_session=call_sid)
                
                # Fetch created invoice
                invoice = await BillingService.get_invoice_by_appointment(db, appointment.id)

                # 3. Update Redis Session Memory
                await VoiceSessionManager.update_session(call_sid, {
                    "patient_id": str(patient.id),
                    "patient_name": patient.full_name,
                    "invoice_id": str(invoice.id) if invoice else None,
                    "current_state": ConversationState.PAYMENT.value,
                })

                logger.info("Executed confirm_booking", appointment_id=str(appointment.id), success=True)
                return {
                    "success": True,
                    "appointment_id": str(appointment.id),
                    "invoice_id": str(invoice.id) if invoice else None,
                    "total_amount_inr": invoice.total_amount if invoice else 0.0,
                    "message": "Appointment has been booked successfully and invoice is created."
                }

            elif name == "send_payment_link":
                patient_name = arguments.get("patient_name")
                patient_email = arguments.get("patient_email")
                doctor_name = arguments.get("doctor_name")
                amount_inr = arguments.get("amount_inr")
                slot_id_str = arguments.get("slot_id")

                try:
                    slot_uuid = uuid.UUID(slot_id_str)
                except (ValueError, TypeError):
                    return {"success": False, "message": f"Invalid slot ID format: '{slot_id_str}'"}

                # Create Razorpay payment link
                import time
                expire_by = int(time.time()) + (20 * 60) # 20 minutes expiry
                amount_paise = int(round(amount_inr * 100))

                try:
                    # Retrieve slot date for metadata
                    slot = await db.get(DoctorSlot, slot_uuid)
                    slot_date_str = slot.date.isoformat() if slot else datetime.date.today().isoformat()
                    
                    payment_link = razorpay_client.create_payment_link(
                        amount_paise=amount_paise,
                        customer_name=patient_name,
                        customer_phone=None, # We use email primary
                        description=f"Appointment with {doctor_name}",
                        reference_id=call_sid[:40],
                        expire_by=expire_by,
                        notes={
                            "session_id": call_sid,
                            "slot_id": slot_id_str,
                            "patient_name": patient_name,
                            "email": patient_email,
                            "doctor_name": doctor_name,
                            "slot_date": slot_date_str,
                        },
                    )
                except Exception as pay_err:
                    logger.error("Failed to create Razorpay payment link", error=str(pay_err))
                    return {"success": False, "message": f"Failed to create payment link: {str(pay_err)}"}

                payment_url = payment_link.get("short_url")

                # Queue the payment link email asynchronously via Celery
                try:
                    from app.tasks.notification_tasks import send_payment_link_email_task
                    send_payment_link_email_task.delay(
                        email=patient_email,
                        patient_name=patient_name,
                        doctor_name=doctor_name,
                        amount_inr=float(amount_inr),
                        payment_url=payment_url,
                    )
                    logger.info("Queued payment link email via Celery", email=patient_email)
                except Exception as task_err:
                    logger.error("Failed to dispatch Celery send_payment_link_email_task", error=str(task_err))

                # Update Redis Session Memory
                await VoiceSessionManager.update_session(call_sid, {
                    "patient_name": patient_name,
                    "email": patient_email,
                    "slot_id": slot_id_str,
                    "payment_link_id": payment_link.get("id"),
                    "payment_link_url": payment_url,
                    "payment_expires_at": expire_by,
                    "current_state": ConversationState.PAYMENT.value,
                })

                logger.info("Executed send_payment_link tool", success=True, payment_link_id=payment_link.get("id"))
                return {
                    "success": True,
                    "payment_link_id": payment_link.get("id"),
                    "payment_link_url": payment_url,
                    "message": f"Payment link generated successfully and queued for email to {patient_email}."
                }

            else:
                logger.warning("Unknown tool call requested", tool_name=name)
                return {"success": False, "message": f"Tool '{name}' is not registered."}

        except Exception as e:
            logger.exception("Error executing voice tool", tool_name=name)
            return {"success": False, "message": str(e)}
