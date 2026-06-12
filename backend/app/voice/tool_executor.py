"""
CareVoice AI Hospital Platform - Voice Tool Executor.

Binds the OpenAI Realtime tool calling system to the async database session
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


async def execute_tool(name: str, arguments: dict, call_sid: str) -> dict:
    """Route and execute tool calls requested by the OpenAI Realtime model asynchronously."""
    logger.info("Executing voice tool call", tool_name=name, arguments=arguments, call_sid=call_sid)

    async with async_session_factory() as db:
        try:
            if name == "find_doctor":
                dept_name = arguments.get("department_name")
                search_query = arguments.get("search_query")

                stmt = select(Doctor).join(Department).where(Doctor.is_active == True)
                
                if dept_name:
                    stmt = stmt.where(Department.name.ilike(f"%{dept_name}%"))
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

                doctor_uuid = uuid.UUID(doctor_id_str)
                # Parse date (format YYYY-MM-DD)
                target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()

                # Generate slots for today/tomorrow automatically on search to ensure they exist
                await SlotService.generate_slots_for_doctor(db, doctor_uuid, target_date, target_date)

                slots = await SlotService.list_available_slots(db, doctor_uuid, target_date)
                
                slot_list = []
                for slot in slots:
                    slot_list.append({
                        "slot_id": str(slot.id),
                        "start_time": slot.start_time.strftime("%I:%M %p"),
                        "end_time": slot.end_time.strftime("%I:%M %p"),
                        "status": slot.status.value,
                    })

                logger.info("Executed get_slots", count=len(slot_list), date=target_date_str)
                return {"success": True, "slots": slot_list[:8]}

            elif name == "lock_slot":
                slot_id_str = arguments.get("slot_id")
                slot_uuid = uuid.UUID(slot_id_str)

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

                slot_uuid = uuid.UUID(slot_id_str)
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
                    "total_amount_inr": (invoice.total_amount / 100.0) if invoice else 0.0,
                    "message": "Appointment has been booked successfully and invoice is created."
                }

            else:
                logger.warning("Unknown tool call requested", tool_name=name)
                return {"success": False, "message": f"Tool '{name}' is not registered."}

        except Exception as e:
            logger.exception("Error executing voice tool", tool_name=name)
            return {"success": False, "message": str(e)}
