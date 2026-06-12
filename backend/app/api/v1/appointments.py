"""
Appointment management endpoints - create, list, get, update, and cancel appointments.
"""

from __future__ import annotations

import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AppointmentStatus
from app.core.security import get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.services import AppointmentService

router = APIRouter()


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an appointment",
)
async def create_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AppointmentResponse:
    """Create a new appointment for a patient with a doctor at a specific slot."""
    try:
        return await AppointmentService.create_appointment(db=db, schema=payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=AppointmentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List appointments",
)
async def list_appointments(
    patient_id: UUID | None = Query(None, description="Filter by patient ID"),
    doctor_id: UUID | None = Query(None, description="Filter by doctor ID"),
    status_filter: AppointmentStatus | None = Query(
        None, alias="status", description="Filter by appointment status"
    ),
    date_filter: datetime.date | None = Query(
        None, alias="date", description="Filter by appointment date"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AppointmentListResponse:
    """List appointments with optional filters for patient, doctor, status, and date."""
    skip = (page - 1) * page_size
    total, items = await AppointmentService.list_appointments(
        db=db,
        skip=skip,
        limit=page_size,
        patient_id=patient_id,
        doctor_id=doctor_id,
        date_filter=date_filter,
        status=status_filter,
    )
    return AppointmentListResponse(total=total, items=items)


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get appointment by ID",
)
async def get_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AppointmentResponse:
    """Retrieve a single appointment by its unique ID."""
    appointment = await AppointmentService.get_appointment(
        db=db, appointment_id=appointment_id
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return appointment


@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update appointment",
)
async def update_appointment(
    appointment_id: UUID,
    payload: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AppointmentResponse:
    """Update an existing appointment's details or status."""
    appointment = await AppointmentService.update_appointment(
        db=db, appointment_id=appointment_id, schema=payload
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return appointment


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel appointment",
)
async def cancel_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AppointmentResponse:
    """Cancel an existing appointment and release the associated slot."""
    appointment = await AppointmentService.cancel_appointment(
        db=db, appointment_id=appointment_id
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return appointment
