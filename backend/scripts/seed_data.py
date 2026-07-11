"""
CareVoice AI Hospital Platform - Database Seeding Script.

Clears ALL existing data, then seeds the database with comprehensive sample data:
  - 1  admin user (credentials from ADMIN_EMAIL / ADMIN_PASSWORD env vars)
  - 14 departments
  - 28 doctors (2 per department) with realistic consultation fees
  - Weekly schedules + auto-generated 30-min slots (past 30 days → next 14 days)
  - 20 patients
  - 45 appointments (8 today, 15 last week, 22 last month) with invoices & payments
  - 15 call sessions with transcript snippets for CSAT scoring
  - Appointment notifications

Run with:  python -m scripts.seed_data
"""

import asyncio
import datetime
import random
import uuid

import structlog
from sqlalchemy import delete, select, func

from app.config import settings
from app.core.constants import (
    AdminRole,
    AppointmentStatus,
    CallStatus,
    ConversationState,
    PaymentStatus,
    SlotStatus,
)
from app.core.security import hash_password
from app.database import async_session_factory, engine
from app.models.admin_user import AdminUser
from app.models.appointment import Appointment
from app.models.base import Base
from app.models.call_session import CallSession
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.invoice import Invoice
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.payment import Payment
from app.models.schedule import DoctorSchedule
from app.models.slot import DoctorSlot

logger = structlog.get_logger(__name__)

random.seed(42)  # Deterministic seeding for reproducible demo data

TODAY = datetime.date.today()
NOW = datetime.datetime.now(datetime.timezone.utc)

# ───────────────────────────── DATA DEFINITIONS ──────────────────────────────

DEPARTMENT_NAMES = [
    "Cardiology", "Dermatology", "ENT", "Gastroenterology",
    "General Medicine", "Neurology", "Oncology", "Ophthalmology",
    "Orthopedics", "Pediatrics", "Psychiatry", "Pulmonology",
    "Radiology", "Urology",
]

# (full_name, email, phone, specialization, qualification, exp_years, fee,
#  department, [(weekdays, start_hour, start_min, end_hour, end_min)])
DOCTORS = [
    ("Dr. Priya Patel",       "priya.patel@carevoice.ai",       "+919876543201", "General Physician",    "MD - Internal Medicine, MBBS",           10, 700.0,  "General Medicine",  [([0,1,2,3,4,5], 9,0,13,0)]),
    ("Dr. Vikram Singh",      "vikram.singh@carevoice.ai",      "+919876543202", "General Physician",    "MD - General Medicine, MBBS",             8, 650.0,  "General Medicine",  [([0,1,2,3,4],  14,0,18,0)]),
    ("Dr. Arvind Sharma",     "arvind.sharma@carevoice.ai",     "+919876543203", "Cardiologist",         "DM - Cardiology, MD, MBBS",              15, 1500.0, "Cardiology",        [([0,2,4],      10,0,14,0)]),
    ("Dr. Kavita Reddy",      "kavita.reddy@carevoice.ai",      "+919876543204", "Cardiologist",         "DM - Cardiology, MD, MBBS",              12, 1400.0, "Cardiology",        [([1,3,5],      10,0,14,0)]),
    ("Dr. Ananya Rao",        "ananya.rao@carevoice.ai",        "+919876543205", "Pediatrician",         "MD - Pediatrics, MBBS",                  12, 800.0,  "Pediatrics",        [([0,1,2,3,4],   9,0,12,0)]),
    ("Dr. Manoj Kumar",       "manoj.kumar@carevoice.ai",       "+919876543206", "Pediatrician",         "MD - Pediatrics, DCH, MBBS",              9, 750.0,  "Pediatrics",        [([0,2,4],      13,0,17,0)]),
    ("Dr. Sarah D'Souza",     "sarah.dsouza@carevoice.ai",      "+919876543207", "Dermatologist",        "DDVL, MD - Dermatology, MBBS",            7, 1000.0, "Dermatology",       [([0,2,5],      14,0,18,0)]),
    ("Dr. Ritu Verma",        "ritu.verma@carevoice.ai",        "+919876543208", "Dermatologist",        "MD - Dermatology, MBBS",                  6, 900.0,  "Dermatology",       [([1,3],        10,0,14,0)]),
    ("Dr. Rohan Mehta",       "rohan.mehta@carevoice.ai",       "+919876543209", "Orthopedic Surgeon",   "MS - Orthopedics, MBBS",                  8, 1200.0, "Orthopedics",       [([1,3,5],      11,0,15,0)]),
    ("Dr. Suresh Nair",       "suresh.nair@carevoice.ai",       "+919876543210", "Orthopedic Surgeon",   "MS - Orthopedics, DNB, MBBS",            14, 1100.0, "Orthopedics",       [([0,2,4],       9,0,13,0)]),
    ("Dr. Rajesh Iyer",       "rajesh.iyer@carevoice.ai",       "+919876543211", "Neurologist",          "DM - Neurology, MD, MBBS",               18, 1800.0, "Neurology",         [([1,4],        10,0,13,0)]),
    ("Dr. Deepa Menon",       "deepa.menon@carevoice.ai",       "+919876543212", "Neurologist",          "DM - Neurology, MD, MBBS",               11, 1700.0, "Neurology",         [([0,2],        14,0,18,0)]),
    ("Dr. Farhan Sheikh",     "farhan.sheikh@carevoice.ai",     "+919876543213", "ENT Specialist",       "MS - ENT, MBBS",                          9, 900.0,  "ENT",               [([0,1,2,3,4],   9,0,12,0)]),
    ("Dr. Anjali Desai",      "anjali.desai@carevoice.ai",      "+919876543214", "ENT Specialist",       "MS - ENT, MBBS",                          7, 850.0,  "ENT",               [([0,2,4],      14,0,17,0)]),
    ("Dr. Arun Bhat",         "arun.bhat@carevoice.ai",         "+919876543215", "Gastroenterologist",   "DM - Gastroenterology, MD, MBBS",        13, 1200.0, "Gastroenterology",  [([0,2,4],      10,0,14,0)]),
    ("Dr. Sneha Kulkarni",    "sneha.kulkarni@carevoice.ai",    "+919876543216", "Gastroenterologist",   "DM - Gastroenterology, MD, MBBS",        10, 1100.0, "Gastroenterology",  [([1,3,5],       9,0,13,0)]),
    ("Dr. Ramya Krishnan",    "ramya.krishnan@carevoice.ai",    "+919876543217", "Ophthalmologist",      "MS - Ophthalmology, MBBS",               11, 1000.0, "Ophthalmology",     [([0,1,2,3,4],   9,0,12,0)]),
    ("Dr. Anil Saxena",       "anil.saxena@carevoice.ai",       "+919876543218", "Ophthalmologist",      "MS - Ophthalmology, DO, MBBS",           15, 950.0,  "Ophthalmology",     [([1,3,5],      14,0,18,0)]),
    ("Dr. Nikhil Chopra",     "nikhil.chopra@carevoice.ai",     "+919876543219", "Pulmonologist",        "DM - Pulmonology, MD, MBBS",             10, 1200.0, "Pulmonology",       [([0,2,4],      10,0,14,0)]),
    ("Dr. Swati Pandey",      "swati.pandey@carevoice.ai",      "+919876543220", "Pulmonologist",        "MD - Pulmonary Medicine, MBBS",           8, 1100.0, "Pulmonology",       [([1,3],         9,0,13,0)]),
    ("Dr. Meera Iyer",        "meera.iyer@carevoice.ai",        "+919876543221", "Psychiatrist",         "MD - Psychiatry, MBBS",                  12, 1500.0, "Psychiatry",        [([0,2,4],      10,0,14,0)]),
    ("Dr. Rahul Deshpande",   "rahul.deshpande@carevoice.ai",   "+919876543222", "Psychiatrist",         "MD - Psychiatry, DPM, MBBS",              9, 1400.0, "Psychiatry",        [([1,3,5],      11,0,15,0)]),
    ("Dr. Sanjay Kapoor",     "sanjay.kapoor@carevoice.ai",     "+919876543223", "Oncologist",           "DM - Medical Oncology, MD, MBBS",        20, 2500.0, "Oncology",          [([0,2,4],      10,0,13,0)]),
    ("Dr. Pooja Agarwal",     "pooja.agarwal@carevoice.ai",     "+919876543224", "Oncologist",           "DM - Medical Oncology, MD, MBBS",        14, 2200.0, "Oncology",          [([1,3],         9,0,13,0)]),
    ("Dr. Tarun Malhotra",    "tarun.malhotra@carevoice.ai",    "+919876543225", "Radiologist",          "MD - Radiology, MBBS",                   16, 2000.0, "Radiology",         [([0,1,2,3,4],   9,0,12,0)]),
    ("Dr. Divya Nambiar",     "divya.nambiar@carevoice.ai",     "+919876543226", "Radiologist",          "MD - Radiology, DMRD, MBBS",             11, 1800.0, "Radiology",         [([0,2,4],      13,0,17,0)]),
    ("Dr. Karthik Srinivasan","karthik.srinivasan@carevoice.ai","+919876543227", "Urologist",            "MCh - Urology, MS, MBBS",                13, 1300.0, "Urology",           [([0,2,4],      10,0,14,0)]),
    ("Dr. Rekha Pillai",      "rekha.pillai@carevoice.ai",      "+919876543228", "Urologist",            "MCh - Urology, MS, MBBS",                10, 1200.0, "Urology",           [([1,3,5],       9,0,13,0)]),
]

# (full_name, email, phone, dob_str, gender, address)
PATIENTS = [
    ("Rahul Sharma",     "rahul.sharma@gmail.com",     "+919812345001", "1985-03-15", "Male",   "42 Sector 18, Noida, UP"),
    ("Priti Mehta",      "priti.mehta@gmail.com",       "+919812345002", "1992-07-22", "Female", "15 Bandra West, Mumbai, MH"),
    ("Suresh Kumar",     "suresh.kumar@yahoo.com",      "+919812345003", "1978-11-08", "Male",   "78 Koramangala, Bangalore, KA"),
    ("Anjali Singh",     "anjali.singh@gmail.com",      "+919812345004", "1995-04-30", "Female", "23 Dwarka, New Delhi"),
    ("Deepak Verma",     "deepak.verma@gmail.com",      "+919812345005", "1980-01-12", "Male",   "56 Salt Lake, Kolkata, WB"),
    ("Nisha Gupta",      "nisha.gupta@gmail.com",       "+919812345006", "1988-09-18", "Female", "90 Jubilee Hills, Hyderabad, TS"),
    ("Aakash Joshi",     "aakash.joshi@yahoo.com",      "+919812345007", "1975-06-25", "Male",   "34 Aundh, Pune, MH"),
    ("Kavitha Nair",     "kavitha.nair@gmail.com",      "+919812345008", "1990-12-03", "Female", "67 Adyar, Chennai, TN"),
    ("Ramesh Pandey",    "ramesh.pandey@gmail.com",     "+919812345009", "1970-08-14", "Male",   "12 Civil Lines, Lucknow, UP"),
    ("Sunita Deshmukh",  "sunita.deshmukh@gmail.com",   "+919812345010", "1983-05-21", "Female", "45 FC Road, Pune, MH"),
    ("Vijay Malhotra",   "vijay.malhotra@yahoo.com",    "+919812345011", "1968-02-28", "Male",   "89 Defence Colony, New Delhi"),
    ("Pooja Reddy",      "pooja.reddy@gmail.com",       "+919812345012", "1997-11-09", "Female", "23 Madhapur, Hyderabad, TS"),
    ("Amit Saxena",      "amit.saxena@gmail.com",       "+919812345013", "1982-04-17", "Male",   "56 Gomti Nagar, Lucknow, UP"),
    ("Megha Kulkarni",   "megha.kulkarni@gmail.com",    "+919812345014", "1993-08-06", "Female", "78 Kothrud, Pune, MH"),
    ("Rajendra Bhat",    "rajendra.bhat@yahoo.com",     "+919812345015", "1972-10-31", "Male",   "90 JP Nagar, Bangalore, KA"),
    ("Sweta Chopra",     "sweta.chopra@gmail.com",      "+919812345016", "1989-03-24", "Female", "12 Sector 62, Noida, UP"),
    ("Manish Tiwari",    "manish.tiwari@gmail.com",     "+919812345017", "1976-07-19", "Male",   "34 Andheri East, Mumbai, MH"),
    ("Divya Sharma",     "divya.sharma.pt@gmail.com",   "+919812345018", "1994-01-11", "Female", "56 Indiranagar, Bangalore, KA"),
    ("Sanjay Patel",     "sanjay.patel.pt@yahoo.com",   "+919812345019", "1965-12-05", "Male",   "78 Navrangpura, Ahmedabad, GJ"),
    ("Riya Kapoor",      "riya.kapoor@gmail.com",       "+919812345020", "1998-06-28", "Female", "23 Greater Kailash, New Delhi"),
]

SYMPTOMS_POOL = [
    "Persistent headache and dizziness for 3 days",
    "Chest pain and shortness of breath",
    "Skin rash and itching on arms",
    "Frequent urination and lower back pain",
    "Fever and sore throat for a week",
    "Joint pain and stiffness in knees",
    "Blurred vision in left eye",
    "Chronic cough and wheezing",
    "Stomach pain and bloating after meals",
    "Anxiety and difficulty sleeping",
    "Ear pain and reduced hearing",
    "Child has high fever and vomiting",
    "Numbness in fingers and toes",
    "Recurring migraines with aura",
    "Difficulty swallowing and throat discomfort",
]

# Transcripts with CSAT keywords: "thank"/"great"/"perfect" → 5.0, "pain"/"fever"/"bad" → 3.0
CALL_TRANSCRIPTS = [
    # Positive (5 transcripts)
    "Patient: Hi, I need to book an appointment.\nAnya: Welcome! Are you a new or returning patient?\nPatient: Returning. My email is rahul.sharma@gmail.com.\nAnya: Great, I found your records. What symptoms are you experiencing?\nPatient: Persistent headache.\nAnya: Let me find a neurologist. Dr. Rajesh Iyer is available.\nPatient: That works, thank you so much!",
    "Patient: Hello, I want to see a cardiologist.\nAnya: Dr. Arvind Sharma is available on Wednesday at 11 AM.\nPatient: Perfect, please book it.\nAnya: Done! Payment link sent. Thank you for choosing CareVoice!",
    "Patient: I need an appointment for my child.\nAnya: Dr. Ananya Rao in Pediatrics is available tomorrow morning.\nPatient: That's perfect, thank you very much!",
    "Patient: Can I book a dermatology appointment?\nAnya: Dr. Sarah D'Souza has slots at 2 PM and 3 PM.\nPatient: 2 PM works great.\nAnya: Booked! Payment link sent.\nPatient: Thank you, this was easy!",
    "Patient: I'd like to see an ENT specialist.\nAnya: Dr. Farhan Sheikh is available tomorrow at 9:30 AM.\nPatient: Perfect, book it please.\nAnya: Confirmed! Great talking with you.",
    # Negative (4 transcripts)
    "Patient: I'm in a lot of pain, please help.\nAnya: I understand. What kind of pain?\nPatient: Severe chest pain since yesterday.\nAnya: Let me connect you with a cardiologist. Dr. Kavita Reddy is available.\nPatient: OK, book it quickly.",
    "Patient: My child has a high fever.\nAnya: Let me find a pediatrician immediately.\nPatient: We've been feeling bad about this all day.\nAnya: Dr. Manoj Kumar can see your child today at 1 PM.",
    "Patient: I have terrible stomach pain.\nAnya: I'll check gastroenterology availability.\nPatient: The pain is getting worse.\nAnya: Dr. Arun Bhat has a slot at 11 AM tomorrow.",
    "Patient: I've had a fever for 5 days now.\nAnya: That needs attention. Let me find a general physician.\nPatient: I also have body pain all over.\nAnya: Dr. Priya Patel can see you today at 10 AM.",
    # Neutral (6 transcripts)
    "Patient: I need to schedule a routine checkup.\nAnya: Which department?\nPatient: General medicine.\nAnya: Dr. Vikram Singh is available Wednesday at 2 PM.\nPatient: OK, book it.",
    "Patient: Hi, I want an eye checkup.\nAnya: Dr. Ramya Krishnan has slots tomorrow.\nPatient: Book the earliest one.\nAnya: Confirmed for 9 AM.",
    "Patient: Need a psychiatry appointment.\nAnya: Dr. Meera Iyer is available Friday at 10 AM.\nPatient: That works.\nAnya: Booked. Payment link sent.",
    "Patient: I'd like to see a pulmonologist.\nAnya: Dr. Nikhil Chopra is available Monday at 10:30 AM.\nPatient: Fine, schedule it.\nAnya: Done. Appointment confirmed.",
    "Patient: Can I get an orthopedic consultation?\nAnya: Dr. Rohan Mehta has openings Tuesday at 11 AM.\nPatient: Book that slot.\nAnya: Confirmed. Payment link sent.",
    "Patient: I want to book a radiology scan.\nAnya: Dr. Tarun Malhotra is available tomorrow morning.\nPatient: OK, 9 AM.\nAnya: Confirmed.",
]

# ─────────────────────────── HELPER FUNCTIONS ────────────────────────────────


def _add_minutes(t: datetime.time, minutes: int) -> datetime.time:
    """Add *minutes* to a datetime.time value and return the result."""
    dt = datetime.datetime.combine(TODAY, t) + datetime.timedelta(minutes=minutes)
    return dt.time()


def _past_datetime(days_ago: int, hour: int = 10) -> datetime.datetime:
    """Return a timezone-aware UTC datetime *days_ago* from today at *hour*:00."""
    d = TODAY - datetime.timedelta(days=days_ago)
    return datetime.datetime.combine(d, datetime.time(hour, 0), tzinfo=datetime.timezone.utc)


# ─────────────────────────── SEEDING FUNCTIONS ───────────────────────────────


async def clear_all_data(session) -> None:
    """Delete ALL rows from every table in FK-safe order."""
    models_ordered = [
        Payment, Invoice, Notification, Appointment, CallSession,
        DoctorSlot, DoctorSchedule, Doctor, Department, Patient, AdminUser,
    ]
    for model in models_ordered:
        await session.execute(delete(model))
    await session.commit()
    logger.info("Cleared all existing data from all tables")


async def seed_admin(session) -> None:
    """Create the default admin user from environment variables."""
    admin = AdminUser(
        email=settings.ADMIN_EMAIL,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        full_name=settings.ADMIN_FULL_NAME,
        role=AdminRole.SUPER_ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.flush()
    logger.info("Seeded admin user", email=settings.ADMIN_EMAIL)


async def seed_departments(session) -> dict[str, uuid.UUID]:
    """Create all 14 hospital departments. Returns {name: id} mapping."""
    dept_ids: dict[str, uuid.UUID] = {}
    for name in DEPARTMENT_NAMES:
        dept = Department(
            name=name,
            description=f"Operational hospital department for {name}.",
            is_active=False,  # will be activated after doctors are assigned
        )
        session.add(dept)
        await session.flush()
        dept_ids[name] = dept.id
    logger.info("Seeded departments", count=len(dept_ids))
    return dept_ids


async def seed_doctors(session, dept_ids: dict[str, uuid.UUID]) -> list[dict]:
    """Create 28 doctors with weekly schedules. Returns list of doctor metadata dicts."""
    doctor_records = []
    for name, email, phone, spec, qual, exp, fee, dept_name, schedules in DOCTORS:
        dept_id = dept_ids[dept_name]
        doc = Doctor(
            department_id=dept_id,
            full_name=name,
            specialization=spec,
            qualification=qual,
            experience_years=exp,
            consultation_fee=fee,
            phone=phone,
            email=email,
            is_active=True,
        )
        session.add(doc)
        await session.flush()

        schedule_records = []
        for weekdays, sh, sm, eh, em in schedules:
            for day in weekdays:
                sched = DoctorSchedule(
                    doctor_id=doc.id,
                    day_of_week=day,
                    start_time=datetime.time(sh, sm),
                    end_time=datetime.time(eh, em),
                    slot_duration_minutes=30,
                    is_active=True,
                )
                session.add(sched)
                await session.flush()
                schedule_records.append(sched)

        doctor_records.append({
            "id": doc.id,
            "name": name,
            "fee": fee,
            "dept_id": dept_id,
            "dept_name": dept_name,
            "schedules": schedule_records,
        })

    await session.commit()
    logger.info("Seeded doctors and schedules", doctors=len(doctor_records))
    return doctor_records


async def generate_slots(session, doctor_records: list[dict]) -> int:
    """Generate 30-minute slots for every doctor from 30 days ago to 14 days ahead."""
    total_slots = 0
    for doc in doctor_records:
        for sched in doc["schedules"]:
            for day_offset in range(-30, 15):
                target_date = TODAY + datetime.timedelta(days=day_offset)
                if target_date.weekday() != sched.day_of_week:
                    continue

                current = sched.start_time
                while current < sched.end_time:
                    end = _add_minutes(current, sched.slot_duration_minutes)
                    slot = DoctorSlot(
                        doctor_id=doc["id"],
                        schedule_id=sched.id,
                        date=target_date,
                        start_time=current,
                        end_time=end,
                        status=SlotStatus.AVAILABLE,
                    )
                    session.add(slot)
                    total_slots += 1
                    current = end

    await session.commit()
    logger.info("Generated doctor slots", total=total_slots)
    return total_slots


async def seed_patients(session) -> list[dict]:
    """Create 20 sample patients. Returns list of patient metadata dicts."""
    patient_records = []
    for idx, (name, email, phone, dob_str, gender, address) in enumerate(PATIENTS, 1):
        dob = datetime.date.fromisoformat(dob_str)
        patient = Patient(
            full_name=name,
            email=email,
            phone=phone,
            date_of_birth=dob,
            gender=gender,
            address=address,
            medical_record_number=f"MRN-2024-{idx:04d}",
        )
        session.add(patient)
        await session.flush()
        patient_records.append({"id": patient.id, "name": name, "email": email})

    await session.commit()
    logger.info("Seeded patients", count=len(patient_records))
    return patient_records


async def seed_appointments_and_billing(
    session,
    doctor_records: list[dict],
    patient_records: list[dict],
) -> int:
    """Create 45 appointments with matching invoices, payments, and notifications."""
    gst_rate = settings.GST_RATE
    invoice_counter = 0
    created_count = 0

    # Build appointment plan: (days_ago, status)
    plan: list[tuple[int, str]] = []
    # 8 today
    plan += [(0, AppointmentStatus.CONFIRMED)] * 8
    # 15 last week
    plan += [(random.randint(1, 7), AppointmentStatus.COMPLETED) for _ in range(8)]
    plan += [(random.randint(1, 7), AppointmentStatus.CONFIRMED) for _ in range(4)]
    plan += [(random.randint(1, 7), AppointmentStatus.CANCELLED) for _ in range(2)]
    plan += [(random.randint(1, 7), AppointmentStatus.NO_SHOW)]
    # 22 last month
    plan += [(random.randint(8, 30), AppointmentStatus.COMPLETED) for _ in range(14)]
    plan += [(random.randint(8, 30), AppointmentStatus.CANCELLED) for _ in range(4)]
    plan += [(random.randint(8, 30), AppointmentStatus.NO_SHOW) for _ in range(4)]

    random.shuffle(plan)

    for idx, (days_ago, status) in enumerate(plan):
        target_date = TODAY - datetime.timedelta(days=days_ago)
        patient = patient_records[idx % len(patient_records)]

        # Try doctors round-robin until we find one with an available slot
        slot = None
        doc = None
        for attempt in range(len(doctor_records)):
            doc_idx = (idx + attempt) % len(doctor_records)
            doc = doctor_records[doc_idx]
            slot_stmt = (
                select(DoctorSlot)
                .where(
                    DoctorSlot.doctor_id == doc["id"],
                    DoctorSlot.date == target_date,
                    DoctorSlot.status == SlotStatus.AVAILABLE,
                )
                .limit(1)
            )
            slot = (await session.execute(slot_stmt)).scalar_one_or_none()
            if slot:
                break

        if not slot or not doc:
            logger.warning("No available slot for appointment", date=str(target_date), idx=idx)
            continue

        # Book the slot
        slot.status = SlotStatus.BOOKED

        # Appointment
        appt_created = _past_datetime(days_ago, hour=random.randint(8, 11))
        appointment = Appointment(
            patient_id=patient["id"],
            doctor_id=doc["id"],
            slot_id=slot.id,
            department_id=doc["dept_id"],
            appointment_date=target_date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            status=status,
            symptoms=random.choice(SYMPTOMS_POOL),
            notes="Booked via CareVoice AI voice assistant",
        )
        if days_ago > 0:
            appointment.created_at = appt_created
        session.add(appointment)
        await session.flush()

        # Invoice
        invoice_counter += 1
        subtotal = doc["fee"]
        gst_amount = round(subtotal * gst_rate / 100, 2)
        total = round(subtotal + gst_amount, 2)

        if status == AppointmentStatus.COMPLETED:
            inv_status = "paid"
        elif status == AppointmentStatus.CANCELLED:
            inv_status = "cancelled"
        else:
            inv_status = "pending"

        invoice = Invoice(
            appointment_id=appointment.id,
            patient_id=patient["id"],
            invoice_number=f"INV-{target_date.strftime('%Y%m%d')}-{invoice_counter:04d}",
            subtotal=subtotal,
            gst_rate=gst_rate,
            gst_amount=gst_amount,
            total_amount=total,
            status=inv_status,
        )
        if days_ago > 0:
            invoice.created_at = appt_created
        session.add(invoice)
        await session.flush()

        # Payment (only for paid invoices)
        if inv_status == "paid":
            payment = Payment(
                invoice_id=invoice.id,
                patient_id=patient["id"],
                amount=total,
                razorpay_order_id=f"plink_seed_{uuid.uuid4().hex[:12]}",
                razorpay_payment_id=f"pay_seed_{uuid.uuid4().hex[:12]}",
                razorpay_signature=f"sig_seed_{uuid.uuid4().hex[:20]}",
                status=PaymentStatus.CAPTURED,
            )
            if days_ago > 0:
                payment.created_at = appt_created
            session.add(payment)

        # Notification
        notification = Notification(
            patient_id=patient["id"],
            type="appointment_created",
            channel="email",
            subject="Appointment Confirmed - CareVoice AI Hospital",
            message=(
                f"Your appointment with {doc['name']} on "
                f"{target_date.strftime('%B %d, %Y')} at "
                f"{slot.start_time.strftime('%I:%M %p')} has been scheduled."
            ),
            sent_at=appt_created if days_ago > 0 else NOW,
            is_read=status == AppointmentStatus.COMPLETED,
        )
        if days_ago > 0:
            notification.created_at = appt_created
        session.add(notification)

        created_count += 1

    await session.commit()
    logger.info(
        "Seeded appointments, invoices, payments, and notifications",
        appointments=created_count,
        invoices=invoice_counter,
    )
    return created_count


async def seed_call_sessions(session, patient_records: list[dict]) -> int:
    """Create 15 call sessions spread over the last 7 days with CSAT-scored transcripts."""
    # Distribution: 10 completed, 3 abandoned (initiated), 2 failed
    statuses = (
        [CallStatus.COMPLETED] * 10
        + [CallStatus.INITIATED] * 3
        + [CallStatus.FAILED] * 2
    )
    random.shuffle(statuses)

    for i, call_status in enumerate(statuses):
        days_ago = i % 7 + 1  # spread across 1–7 days ago
        duration = random.randint(45, 300)
        started_at = _past_datetime(days_ago, hour=random.randint(9, 17))
        ended_at = started_at + datetime.timedelta(seconds=duration) if call_status != CallStatus.INITIATED else None

        # Pick conversation state based on call outcome
        if call_status == CallStatus.COMPLETED:
            conv_state = ConversationState.COMPLETE
        elif call_status == CallStatus.FAILED:
            conv_state = ConversationState.SYMPTOMS
        else:
            conv_state = ConversationState.GREETING

        # Assign patient for ~60% of sessions
        patient_id = patient_records[i % len(patient_records)]["id"] if i < 10 else None

        call = CallSession(
            patient_id=patient_id,
            session_sid=f"web_seed_{uuid.uuid4().hex[:16]}",
            from_number="web" if i % 3 != 0 else f"+9198{random.randint(10000000, 99999999)}",
            status=call_status,
            started_at=started_at,
            ended_at=ended_at,
            conversation_state=conv_state,
            transcript=CALL_TRANSCRIPTS[i % len(CALL_TRANSCRIPTS)],
        )
        call.created_at = started_at
        session.add(call)

    await session.commit()
    logger.info("Seeded call sessions", count=len(statuses))
    return len(statuses)


async def update_department_status(session) -> None:
    """Set each department's is_active based on whether it has active doctors."""
    depts = (await session.execute(select(Department))).scalars().all()
    for dept in depts:
        count_stmt = select(func.count(Doctor.id)).where(
            Doctor.department_id == dept.id, Doctor.is_active == True
        )
        active_count = (await session.execute(count_stmt)).scalar_one()
        dept.is_active = active_count > 0
    await session.commit()
    logger.info("Updated department active status")


# ──────────────────────────── MAIN ENTRY POINT ───────────────────────────────


async def seed() -> None:
    """Clear the database and seed all tables with comprehensive demo data."""
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")

    # Migrate column rename: twilio_call_sid → session_sid (for existing databases)
    from sqlalchemy import text
    async with engine.begin() as conn:
        try:
            await conn.execute(
                text("ALTER TABLE call_sessions RENAME COLUMN twilio_call_sid TO session_sid")
            )
            logger.info("Migrated column twilio_call_sid → session_sid")
        except Exception:
            # Column already renamed or doesn't exist — safe to ignore
            pass

    async with async_session_factory() as session:
        try:
            logger.info("Starting full database clear + reseed...")

            await clear_all_data(session)
            await seed_admin(session)
            dept_ids = await seed_departments(session)
            doctor_records = await seed_doctors(session, dept_ids)
            slot_count = await generate_slots(session, doctor_records)
            patient_records = await seed_patients(session)
            appt_count = await seed_appointments_and_billing(
                session, doctor_records, patient_records
            )
            call_count = await seed_call_sessions(session, patient_records)
            await update_department_status(session)

            logger.info(
                "Database seeding complete!",
                departments=len(dept_ids),
                doctors=len(doctor_records),
                slots=slot_count,
                patients=len(patient_records),
                appointments=appt_count,
                call_sessions=call_count,
            )

        except Exception as e:
            await session.rollback()
            logger.exception("Failed to seed database", error=str(e))
            raise


if __name__ == "__main__":
    asyncio.run(seed())
