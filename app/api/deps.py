"""
Database and authentication dependencies for the API.
"""
import uuid
from typing import Optional, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.config import settings
from app.database import get_async_db
from app.models.user import User, UserRole

# Security scheme
security = HTTPBearer()

# Alias for compatibility  
get_db = get_async_db


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required."
        )
    return current_user


async def get_current_accountant_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with accountant or admin role."""
    if current_user.role not in [UserRole.CONTADOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Accountant role required."
        )
    return current_user


async def get_current_manager_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with read-only or higher role."""
    if current_user.role not in [UserRole.SOLO_LECTURA, UserRole.CONTADOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. User role required."
        )
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Decorator factory for role-based access control."""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    return role_checker


# Convenience dependency for different permission levels
require_admin = require_role([UserRole.ADMIN])
require_accountant = require_role([UserRole.CONTADOR, UserRole.ADMIN])
require_manager = require_role([UserRole.SOLO_LECTURA, UserRole.CONTADOR, UserRole.ADMIN])
require_user = require_role([UserRole.SOLO_LECTURA, UserRole.CONTADOR, UserRole.ADMIN])
