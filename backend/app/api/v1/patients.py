"""
Patient management endpoints - CRUD operations with search and pagination.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.patient import (
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)
from app.services import PatientService

router = APIRouter()


@router.get(
    "/",
    response_model=PatientListResponse,
    status_code=status.HTTP_200_OK,
    summary="List patients",
)
async def list_patients(
    phone: str | None = Query(None, description="Filter by phone number"),
    name: str | None = Query(None, description="Search by patient name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> PatientListResponse:
    """List patients with optional search by phone number or name, with pagination."""
    skip = (page - 1) * page_size
    search_query = name or phone
    total, items = await PatientService.list_patients(
        db=db,
        skip=skip,
        limit=page_size,
        search_query=search_query,
    )
    return PatientListResponse(total=total, items=items)


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new patient",
)
async def create_patient(
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> PatientResponse:
    """Create a new patient record."""
    try:
        return await PatientService.create_patient(db=db, schema=payload)
    except ValueError as e:
        if str(e) == "Phone number already registered":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient by ID",
)
async def get_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> PatientResponse:
    """Retrieve a single patient by their unique ID."""
    patient = await PatientService.get_patient(db=db, patient_id=patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return patient


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Update patient",
)
async def update_patient(
    patient_id: UUID,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> PatientResponse:
    """Update an existing patient's information."""
    patient = await PatientService.update_patient(
        db=db, patient_id=patient_id, schema=payload
    )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return patient


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete patient",
)
async def delete_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> Response:
    """Delete a patient record."""
    success = await PatientService.delete_patient(db=db, patient_id=patient_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

