"""
Admin management endpoints - user listing, role updates, deactivation, and audit logs.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AdminRole
from app.core.exceptions import NotFoundError
from app.core.security import RoleChecker, get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.audit_log import AuditLog
from app.schemas.auth import AdminResponse

router = APIRouter()

require_super_admin = Depends(RoleChecker(allowed_roles=[AdminRole.SUPER_ADMIN]))
require_admin = Depends(RoleChecker(allowed_roles=[AdminRole.SUPER_ADMIN, AdminRole.ADMIN]))


@router.get(
    "/users",
    response_model=list[AdminResponse],
    status_code=status.HTTP_200_OK,
    summary="List admin users",
    dependencies=[require_super_admin],
)
async def list_admin_users(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> list[AdminResponse]:
    """List all admin users. Requires SUPER_ADMIN role."""
    result = await db.execute(
        select(AdminUser).order_by(AdminUser.created_at.desc())
    )
    admins = result.scalars().all()
    return [AdminResponse.model_validate(admin) for admin in admins]


@router.put(
    "/users/{user_id}/role",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Update admin role",
    dependencies=[require_super_admin],
)
async def update_admin_role(
    user_id: UUID,
    role: AdminRole = Query(..., description="New role to assign"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AdminResponse:
    """Update an admin user's role. Requires SUPER_ADMIN role."""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot modify their own roles",
        )

    result = await db.execute(
        select(AdminUser).where(AdminUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(f"Admin user {user_id} not found")

    user.role = role
    await db.commit()
    await db.refresh(user)
    return AdminResponse.model_validate(user)


@router.put(
    "/users/{user_id}/deactivate",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate admin user",
    dependencies=[require_super_admin],
)
async def deactivate_admin(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AdminResponse:
    """Deactivate an admin user account. Requires SUPER_ADMIN role."""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot deactivate their own accounts",
        )

    result = await db.execute(
        select(AdminUser).where(AdminUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(f"Admin user {user_id} not found")

    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return AdminResponse.model_validate(user)


@router.get(
    "/audit-logs",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List audit logs",
    dependencies=[require_admin],
)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> dict:
    """List audit logs with pagination. Requires ADMIN or SUPER_ADMIN role."""
    offset = (page - 1) * page_size

    count_result = await db.execute(select(func.count(AuditLog.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "admin_id": str(log.admin_id) if log.admin_id else None,
                "action": log.action,
                "resource_type": log.entity_type,
                "resource_id": str(log.entity_id) if log.entity_id else None,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }
