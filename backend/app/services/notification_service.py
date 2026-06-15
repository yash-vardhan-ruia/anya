"""
CareVoice AI Hospital Platform - Notification Service.

Handles formatting and dispatching SMS/Email notifications, constructing gorgeous HTML emails
with state-of-the-art styling, and archiving all sent notifications in the database.
"""

import uuid
import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.appointment import Appointment
from app.models.notification import Notification
from app.models.invoice import Invoice
from app.integrations.email_client import email_client

logger = structlog.get_logger(__name__)


class NotificationService:
    """Business logic for outbound patient notification templates and delivery."""

    @staticmethod
    def _get_premium_email_layout(title: str, preheader: str, body_html: str) -> str:
        """Standardized template to render high-aesthetic, professional hospital emails."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
                body {{
                    font-family: 'Inter', sans-serif;
                    background-color: #f3f4f6;
                    margin: 0;
                    padding: 0;
                    color: #1f2937;
                    -webkit-font-smoothing: antialiased;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
                    border: 1px solid #e5e7eb;
                }}
                .header {{
                    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    font-family: 'Outfit', sans-serif;
                    color: #ffffff;
                    font-size: 28px;
                    margin: 0;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .header p {{
                    color: #93c5fd;
                    font-size: 14px;
                    margin: 10px 0 0 0;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 20px;
                    color: #111827;
                }}
                .message-box {{
                    font-size: 15px;
                    line-height: 1.6;
                    color: #4b5563;
                }}
                .details-card {{
                    background: #f8fafc;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 25px 0;
                    border: 1px solid #e2e8f0;
                }}
                .details-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #e2e8f0;
                }}
                .details-row:last-child {{
                    border-bottom: none;
                }}
                .label {{
                    font-weight: 600;
                    color: #475569;
                    font-size: 14px;
                }}
                .val {{
                    color: #0f172a;
                    font-size: 14px;
                    text-align: right;
                }}
                .btn-container {{
                    text-align: center;
                    margin-top: 30px;
                }}
                .btn {{
                    background-color: #3b82f6;
                    color: #ffffff !important;
                    text-decoration: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                    display: inline-block;
                    box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4);
                    transition: all 0.2s ease;
                }}
                .footer {{
                    background-color: #f9fafb;
                    padding: 25px 30px;
                    text-align: center;
                    border-top: 1px solid #f3f4f6;
                    font-size: 12px;
                    color: #9ca3af;
                }}
                .footer a {{
                    color: #3b82f6;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <span style="display:none;font-size:0px;line-height:0px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">{preheader}</span>
            <div class="email-container">
                <div class="header">
                    <h1>CareVoice AI Hospital</h1>
                    <p>Powered by Anya, Your Voice Booking Assistant</p>
                </div>
                <div class="content">
                    {body_html}
                </div>
                <div class="footer">
                    <p>&copy; 2026 CareVoice Hospital Platform. All rights reserved.</p>
                    <p>Need support? Contact us at <a href="mailto:support@carevoice.ai">support@carevoice.ai</a> or call +91 98765 43210</p>
                </div>
            </div>
        </body>
        </html>
        """

    @classmethod
    async def send_appointment_created(cls, db: AsyncSession, appointment_id: uuid.UUID) -> None:
        """Notify patient that their appointment has been booked and a payment is pending."""
        appointment = await db.get(Appointment, appointment_id)
        if not appointment:
            return

        patient = appointment.patient
        doctor = appointment.doctor
        dept = appointment.department
        
        # Calculate consultation amount
        invoice_stmt = select(Invoice).where(Invoice.appointment_id == appointment_id)
        invoice = (await db.execute(invoice_stmt)).scalar_one_or_none()
        amount_str = f"INR {invoice.total_amount:.2f}" if invoice else f"INR {doctor.consultation_fee / 100:.2f}"

        # 1. SMS Dispatch
        sms_body = (
            f"Hello {patient.full_name}, your CareVoice appointment with Dr. {doctor.full_name} "
            f"({dept.name}) is scheduled for {appointment.appointment_date} at {appointment.start_time.strftime('%I:%M %p')}. "
            f"Payment of {amount_str} is pending. Please complete your checkout online."
        )
        # SMS sending bypassed (Twilio disabled)
        try:
            db_sms = Notification(
                patient_id=patient.id,
                type="appointment_created",
                channel="sms",
                message=sms_body,
                sent_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(db_sms)
        except Exception as e:
            logger.error("Failed to send booking creation SMS", error=str(e), appointment_id=str(appointment_id))

        # 2. Email Dispatch (if email is provided)
        if patient.email:
            subject = "Appointment Scheduled - CareVoice AI Hospital"
            preheader = f"Your appointment with Dr. {doctor.full_name} is scheduled. Complete your checkout."
            body_html = f"""
            <div class="greeting">Dear {patient.full_name},</div>
            <div class="message-box">
                <p>We are pleased to inform you that your appointment has been successfully scheduled through our AI Voice Assistant, Anya.</p>
                <p>Please review the details below. Note that your scheduling is currently **pending payment confirmation**.</p>
            </div>
            <div class="details-card">
                <div class="details-row">
                    <span class="label">Doctor</span>
                    <span class="val">Dr. {doctor.full_name} ({doctor.specialization})</span>
                </div>
                <div class="details-row">
                    <span class="label">Department</span>
                    <span class="val">{dept.name}</span>
                </div>
                <div class="details-row">
                    <span class="label">Date</span>
                    <span class="val">{appointment.appointment_date.strftime('%A, %d %B %Y')}</span>
                </div>
                <div class="details-row">
                    <span class="label">Time Slot</span>
                    <span class="val">{appointment.start_time.strftime('%I:%M %p')} - {appointment.end_time.strftime('%I:%M %p')}</span>
                </div>
                <div class="details-row">
                    <span class="label">Consultation Fee (+ GST)</span>
                    <span class="val"><strong>{amount_str}</strong></span>
                </div>
            </div>
            <div class="btn-container">
                <a href="{settings.BASE_URL}/billing/checkout/{invoice.id if invoice else ''}" class="btn">Proceed to Payment</a>
            </div>
            """
            email_content = cls._get_premium_email_layout(subject, preheader, body_html)
            try:
                await email_client.send_email(to_email=patient.email, subject=subject, html_content=email_content)
                db_email = Notification(
                    patient_id=patient.id,
                    type="appointment_created",
                    channel="email",
                    subject=subject,
                    message=email_content,
                    sent_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(db_email)
            except Exception as e:
                logger.error("Failed to send booking creation Email", error=str(e), appointment_id=str(appointment_id))
        
        await db.commit()

    @classmethod
    async def send_appointment_confirmed(cls, db: AsyncSession, appointment_id: uuid.UUID) -> None:
        """Notify patient that their payment was verified and their appointment is confirmed."""
        appointment = await db.get(Appointment, appointment_id)
        if not appointment:
            return

        patient = appointment.patient
        doctor = appointment.doctor
        dept = appointment.department

        # 1. SMS Dispatch
        sms_body = (
            f"Hi {patient.full_name}, payment received! Your appointment with Dr. {doctor.full_name} "
            f"on {appointment.appointment_date} at {appointment.start_time.strftime('%I:%M %p')} is CONFIRMED. "
            f"We look forward to seeing you. Thank you for choosing CareVoice!"
        )
        # SMS sending bypassed (Twilio disabled)
        try:
            db_sms = Notification(
                patient_id=patient.id,
                type="appointment_confirmed",
                channel="sms",
                message=sms_body,
                sent_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(db_sms)
        except Exception as e:
            logger.error("Failed to send confirmation SMS", error=str(e), appointment_id=str(appointment_id))

        # 2. Email Dispatch
        if patient.email:
            subject = "Appointment Confirmed - CareVoice AI Hospital"
            preheader = f"Your appointment with Dr. {doctor.full_name} is confirmed."
            body_html = f"""
            <div class="greeting">Hello {patient.full_name},</div>
            <div class="message-box">
                <p>Great news! We have successfully processed your payment, and your medical consultation has been <strong>officially confirmed</strong>.</p>
                <p>Please arrive at the hospital 15 minutes before your scheduled appointment time.</p>
            </div>
            <div class="details-card">
                <div class="details-row">
                    <span class="label">Appointment Status</span>
                    <span class="val" style="color: #10b981; font-weight: bold;">CONFIRMED</span>
                </div>
                <div class="details-row">
                    <span class="label">Consulting Doctor</span>
                    <span class="val">Dr. {doctor.full_name} ({doctor.specialization})</span>
                </div>
                <div class="details-row">
                    <span class="label">Department</span>
                    <span class="val">{dept.name}</span>
                </div>
                <div class="details-row">
                    <span class="label">Date</span>
                    <span class="val">{appointment.appointment_date.strftime('%A, %d %B %Y')}</span>
                </div>
                <div class="details-row">
                    <span class="label">Time Window</span>
                    <span class="val">{appointment.start_time.strftime('%I:%M %p')} - {appointment.end_time.strftime('%I:%M %p')}</span>
                </div>
            </div>
            <p style="text-align: center; color: #6b7280; font-size: 13px;">A payment receipt has been linked to your medical profile dashboard.</p>
            """
            email_content = cls._get_premium_email_layout(subject, preheader, body_html)
            try:
                await email_client.send_email(to_email=patient.email, subject=subject, html_content=email_content)
                db_email = Notification(
                    patient_id=patient.id,
                    type="appointment_confirmed",
                    channel="email",
                    subject=subject,
                    message=email_content,
                    sent_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(db_email)
            except Exception as e:
                logger.error("Failed to send confirmation Email", error=str(e), appointment_id=str(appointment_id))
        
        await db.commit()

    @classmethod
    async def send_appointment_cancelled(cls, db: AsyncSession, appointment_id: uuid.UUID) -> None:
        """Notify patient that their appointment was cancelled."""
        appointment = await db.get(Appointment, appointment_id)
        if not appointment:
            return

        patient = appointment.patient
        doctor = appointment.doctor
        dept = appointment.department

        # 1. SMS Dispatch
        sms_body = (
            f"Dear {patient.full_name}, your appointment with Dr. {doctor.full_name} "
            f"on {appointment.appointment_date} has been CANCELLED. If this was an error, "
            f"please reply to reschedule or call our help desk."
        )
        # SMS sending bypassed (Twilio disabled)
        try:
            db_sms = Notification(
                patient_id=patient.id,
                type="appointment_cancelled",
                channel="sms",
                message=sms_body,
                sent_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(db_sms)
        except Exception as e:
            logger.error("Failed to send cancellation SMS", error=str(e), appointment_id=str(appointment_id))

        # 2. Email Dispatch
        if patient.email:
            subject = "Appointment Cancelled - CareVoice AI Hospital"
            preheader = f"Your appointment with Dr. {doctor.full_name} was cancelled."
            body_html = f"""
            <div class="greeting">Dear {patient.full_name},</div>
            <div class="message-box">
                <p>This email confirms that your appointment scheduled for {appointment.appointment_date} with Dr. {doctor.full_name} has been <strong>cancelled</strong>.</p>
                <p>If you did not request this cancellation, or if you would like to book a new appointment, you can do so by calling our automated booking line at any time.</p>
            </div>
            <div class="details-card">
                <div class="details-row">
                    <span class="label">Cancellation Date</span>
                    <span class="val">{datetime.date.today().strftime('%B %d, %Y')}</span>
                </div>
                <div class="details-row">
                    <span class="label">Original Doctor</span>
                    <span class="val">Dr. {doctor.full_name}</span>
                </div>
                <div class="details-row">
                    <span class="label">Department</span>
                    <span class="val">{dept.name}</span>
                </div>
            </div>
            """
            email_content = cls._get_premium_email_layout(subject, preheader, body_html)
            try:
                await email_client.send_email(to_email=patient.email, subject=subject, html_content=email_content)
                db_email = Notification(
                    patient_id=patient.id,
                    type="appointment_cancelled",
                    channel="email",
                    subject=subject,
                    message=email_content,
                    sent_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(db_email)
            except Exception as e:
                logger.error("Failed to send cancellation Email", error=str(e), appointment_id=str(appointment_id))
        
        await db.commit()

    @classmethod
    async def send_payment_link_email(
        cls, email: str, patient_name: str, doctor_name: str, amount: float, payment_url: str
    ) -> None:
        """Send a styled email containing the Razorpay payment link to the patient."""
        subject = "Payment Link for Appointment - CareVoice AI Hospital"
        preheader = f"Your appointment with Dr. {doctor_name} is ready. Complete your payment."
        body_html = f"""
        <div class="greeting">Dear {patient_name},</div>
        <div class="message-box">
            <p>Thank you for choosing CareVoice AI Hospital. Your booking request is ready.</p>
            <p>Please complete your payment of <strong>INR {amount:.2f}</strong> to confirm your appointment with <strong>Dr. {doctor_name}</strong>.</p>
        </div>
        <div class="details-card">
            <div class="details-row">
                <span class="label">Consulting Doctor</span>
                <span class="val">Dr. {doctor_name}</span>
            </div>
            <div class="details-row">
                <span class="label">Amount Due</span>
                <span class="val"><strong>INR {amount:.2f}</strong></span>
            </div>
        </div>
        <div class="btn-container">
            <a href="{payment_url}" class="btn">Pay Now & Confirm Booking</a>
        </div>
        <p style="text-align: center; color: #6b7280; font-size: 13px; margin-top: 20px;">
            This link is valid for 15 minutes. Once payment is completed, you will receive a confirmation email.
        </p>
        """
        email_content = cls._get_premium_email_layout(subject, preheader, body_html)
        try:
            await email_client.send_email(to_email=email, subject=subject, html_content=email_content)
            logger.info("Payment link email sent successfully", email=email)
        except Exception as e:
            logger.error("Failed to send payment link email", error=str(e), email=email)
