"""
CareVoice AI Hospital Platform - Security & Authentication.

Provides JWT token management, password hashing, and FastAPI auth dependencies.
"""

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import AdminRole
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload dictionary to encode into the token.
        expires_delta: Optional custom expiration duration. Defaults to
            ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Args:
        token: The JWT token string to verify.

    Returns:
        Decoded payload dictionary.

    Raises:
        HTTPException: If the token is invalid or expired (401).
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("sub") is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


import bcrypt

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt directly.

    Args:
        password: The plaintext password to hash.

    Returns:
        Bcrypt-hashed password string.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain: The plaintext password to verify.
        hashed: The bcrypt-hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI dependency to retrieve the current authenticated admin user.

    Validates the JWT token and loads the corresponding AdminUser from the
    database. Raises 401 if the token is invalid or the user does not exist.

    Args:
        token: JWT bearer token extracted from the Authorization header.
        db: Async database session.

    Returns:
        The authenticated AdminUser instance.

    Raises:
        HTTPException: 401 if authentication fails or user not found/inactive.
    """
    from app.models.admin_user import AdminUser
    import uuid

    payload = verify_token(token)
    admin_id: str | None = payload.get("sub")
    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        admin_uuid = uuid.UUID(admin_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
    admin = result.scalar_one_or_none()

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin


class RoleChecker:
    """FastAPI dependency class that enforces admin role-based access control.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(RoleChecker([AdminRole.ADMIN]))])
        async def admin_only_endpoint(): ...
    """

    def __init__(self, allowed_roles: list[AdminRole]) -> None:
        """Initialize the role checker with a list of allowed roles.

        Args:
            allowed_roles: List of AdminRole values that are permitted access.
        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_admin=Depends(get_current_admin),
    ) -> None:
        """Check if the current admin has one of the allowed roles.

        Args:
            current_admin: The authenticated admin user from the dependency chain.

        Raises:
            HTTPException: 403 if the admin's role is not in the allowed list.
        """
        role_val = current_admin.role.value if hasattr(current_admin.role, 'value') else current_admin.role
        allowed_vals = [r.value if hasattr(r, 'value') else r for r in self.allowed_roles]
        if role_val not in allowed_vals:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_val}' does not have access to this resource",
            )
