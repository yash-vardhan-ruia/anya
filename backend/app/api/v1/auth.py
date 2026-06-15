"""
Authentication endpoints - login, register, and current user info.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AdminRole
from app.core.security import (
    RoleChecker,
    create_access_token,
    get_current_admin,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.auth import AdminCreate, AdminResponse, LoginRequest, TokenResponse, AdminUpdate, PasswordUpdate

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate admin user",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate an admin user with username/email and password, returning a JWT."""
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    access_token = create_access_token(
        data={"sub": str(user.id), "role": role_value}
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
    )


@router.post(
    "/register",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new admin user",
)
async def register(
    payload: AdminCreate,
    db: AsyncSession = Depends(get_db),
) -> AdminResponse:
    """Create a new admin user."""
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == payload.email)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Admin with email {payload.email} already exists",
        )

    new_admin = AdminUser(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)
    return AdminResponse.model_validate(new_admin)


@router.get(
    "/me",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current admin info",
)
async def get_me(
    current_admin: AdminUser = Depends(get_current_admin),
) -> AdminResponse:
    """Return the currently authenticated admin user's profile."""
    return AdminResponse.model_validate(current_admin)


@router.put(
    "/me",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current admin profile",
)
async def update_me(
    payload: AdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AdminResponse:
    """Update the currently authenticated admin user's name and/or email."""
    if payload.email is not None:
        # Check if email is already taken
        if payload.email != current_admin.email:
            result = await db.execute(
                select(AdminUser).where(AdminUser.email == payload.email)
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Admin with email {payload.email} already exists",
                )
            current_admin.email = payload.email

    if payload.full_name is not None:
        current_admin.full_name = payload.full_name

    await db.commit()
    await db.refresh(current_admin)
    return AdminResponse.model_validate(current_admin)


@router.put(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Update current admin password",
)
async def update_my_password(
    payload: PasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> dict:
    """Change the currently authenticated admin user's password."""
    if not verify_password(payload.current_password, current_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_admin.hashed_password = hash_password(payload.new_password)
    await db.commit()
    return {"status": "success", "message": "Password updated successfully"}
