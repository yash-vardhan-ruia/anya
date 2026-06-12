"""
Doctor management endpoints - CRUD, schedules, and slot operations.
"""

from __future__ import annotations

import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import RoleChecker, get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.doctor import (
    DoctorCreate,
    DoctorListResponse,
    DoctorResponse,
    DoctorScheduleCreate,
    DoctorScheduleResponse,
    DoctorUpdate,
    SlotListResponse,
    SlotResponse,
)
from app.services import DoctorService, SlotService

router = APIRouter()

require_admin = Depends(RoleChecker(allowed_roles=["ADMIN", "SUPER_ADMIN"]))


@router.get(
    "",
    response_model=DoctorListResponse,
    status_code=status.HTTP_200_OK,
    summary="List doctors",
)
async def list_doctors(
    department_id: UUID | None = Query(None, description="Filter by department ID"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DoctorListResponse:
    """List doctors with optional filters for department and active status."""
    skip = (page - 1) * page_size
    active_only = is_active if is_active is not None else False
    total, items = await DoctorService.list_doctors(
        db=db,
        skip=skip,
        limit=page_size,
        department_id=department_id,
        active_only=active_only,
    )
    return DoctorListResponse(total=total, items=items)


@router.post(
    "",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new doctor",
    dependencies=[require_admin],
)
async def create_doctor(
    payload: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DoctorResponse:
    """Create a new doctor record. Requires ADMIN or SUPER_ADMIN role."""
    try:
        return await DoctorService.create_doctor(db=db, schema=payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get doctor by ID",
)
async def get_doctor(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DoctorResponse:
    """Retrieve a single doctor by their unique ID."""
    doctor = await DoctorService.get_doctor(db=db, doctor_id=doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )
    return doctor


@router.put(
    "/{doctor_id}",
    response_model=DoctorResponse,
    status_code=status.HTTP_200_OK,
    summary="Update doctor",
    dependencies=[require_admin],
)
async def update_doctor(
    doctor_id: UUID,
    payload: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DoctorResponse:
    """Update an existing doctor's information. Requires ADMIN or SUPER_ADMIN role."""
    doctor = await DoctorService.update_doctor(
        db=db, doctor_id=doctor_id, schema=payload
    )
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )
    return doctor


@router.post(
    "/{doctor_id}/schedules",
    response_model=DoctorScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create doctor schedule",
    dependencies=[require_admin],
)
async def create_schedule(
    doctor_id: UUID,
    payload: DoctorScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DoctorScheduleResponse:
    """Create a new schedule entry for a doctor. Requires ADMIN or SUPER_ADMIN role."""
    try:
        return await DoctorService.create_schedule(
            db=db, doctor_id=doctor_id, schema=payload
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{doctor_id}/schedules",
    response_model=list[DoctorScheduleResponse],
    status_code=status.HTTP_200_OK,
    summary="List doctor schedules",
)
async def list_schedules(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> list[DoctorScheduleResponse]:
    """List all schedule entries for a specific doctor."""
    return await DoctorService.list_schedules(db=db, doctor_id=doctor_id)


@router.get(
    "/{doctor_id}/slots",
    response_model=SlotListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get available slots",
)
async def get_available_slots(
    doctor_id: UUID,
    date: datetime.date = Query(..., description="Date to check available slots"),
    db: AsyncSession = Depends(get_db),
) -> SlotListResponse:
    """Get available appointment slots for a doctor on a specific date."""
    slots = await SlotService.list_available_slots(
        db=db, doctor_id=doctor_id, target_date=date
    )
    return SlotListResponse(total=len(slots), items=slots)


@router.post(
    "/{doctor_id}/slots/generate",
    response_model=list[SlotResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate slots for date",
    dependencies=[require_admin],
)
async def generate_slots(
    doctor_id: UUID,
    date: datetime.date = Query(..., description="Date to generate slots for"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> list[SlotResponse]:
    """Generate appointment slots for a doctor on a specific date based on their schedule.
    Requires ADMIN or SUPER_ADMIN role."""
    await SlotService.generate_slots_for_doctor(
        db=db, doctor_id=doctor_id, start_date=date, end_date=date
    )
    # Return list of generated slots for that date
    slots = await SlotService.list_available_slots(
        db=db, doctor_id=doctor_id, target_date=date
    )
    return slots


@router.delete(
    "/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete doctor",
    dependencies=[require_admin],
)
async def delete_doctor(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> Response:
    """Delete a doctor record. Requires ADMIN or SUPER_ADMIN role."""
    success = await DoctorService.delete_doctor(db=db, doctor_id=doctor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

