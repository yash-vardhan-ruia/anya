"""
Department management endpoints - CRUD operations with active-status filtering.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import RoleChecker, get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.department import (
    DepartmentCreate,
    DepartmentListResponse,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.services import DoctorService

router = APIRouter()

require_admin = Depends(RoleChecker(allowed_roles=["ADMIN", "SUPER_ADMIN"]))


@router.get(
    "/",
    response_model=DepartmentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List departments",
)
async def list_departments(
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> DepartmentListResponse:
    """List all departments with optional active-status filtering and pagination."""
    skip = (page - 1) * page_size
    active_only = is_active if is_active is not None else False
    total, items = await DoctorService.list_departments(
        db=db, skip=skip, limit=page_size, active_only=active_only
    )
    return DepartmentListResponse(total=total, items=items)


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department",
    dependencies=[require_admin],
)
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DepartmentResponse:
    """Create a new department. Requires ADMIN or SUPER_ADMIN role."""
    try:
        return await DoctorService.create_department(db=db, schema=payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get department by ID",
)
async def get_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    """Retrieve a single department by its unique ID."""
    department = await DoctorService.get_department(
        db=db, department_id=department_id
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    return department


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update department",
    dependencies=[require_admin],
)
async def update_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DepartmentResponse:
    """Update an existing department. Requires ADMIN or SUPER_ADMIN role."""
    department = await DoctorService.update_department(
        db=db, department_id=department_id, schema=payload
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    return department
