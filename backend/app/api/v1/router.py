"""
V1 API Router - aggregates all v1 sub-routers with appropriate prefixes and tags.
"""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    analytics,
    appointments,
    auth,
    billing,
    calls,
    departments,
    doctors,
    patients,
    payments,
    voice_chat,
)

router = APIRouter(prefix="/v1")

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(patients.router, prefix="/patients", tags=["Patients"])
router.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
router.include_router(departments.router, prefix="/departments", tags=["Departments"])
router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
router.include_router(billing.router, prefix="/billing", tags=["Billing"])
router.include_router(payments.router, prefix="/payments", tags=["Payments"])
router.include_router(calls.router, prefix="/calls", tags=["Calls"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
router.include_router(voice_chat.router, prefix="/voice-chat", tags=["Voice Chat"])