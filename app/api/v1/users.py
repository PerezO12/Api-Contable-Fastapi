import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_current_active_user,
    get_current_admin_user,
)
from app.models.user import User, UserRole
from app.schemas.user import (
    PasswordChangeRequest,
    UserCreateByAdmin,
    UserRead,
    UserResponse,
    UserStatsResponse,
    UserUpdate,
    UserSessionInfo,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene información del usuario actual"""
    return current_user


@router.post("/admin/create-user", response_model=UserRead)
async def create_user_by_admin(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreateByAdmin,
    current_user: User = Depends(get_current_admin_user),
):
    """
    Permite a un administrador crear un nuevo usuario con contraseña temporal
    """
    auth_service = AuthService(db)
    return await auth_service.create_user_by_admin(user_in, current_user.id)


@router.get("/admin/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Obtiene estadísticas de usuarios (solo para admins)
    """
    auth_service = AuthService(db)
    return await auth_service.get_user_stats()


@router.get("/admin/list", response_model=List[UserResponse])
async def list_all_users(    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """
    Lista todos los usuarios del sistema (solo para admins)
    """
    auth_service = AuthService(db)
    return await auth_service.get_users_list(skip=skip, limit=limit, role=role)


@router.put("/{user_id}/toggle-active", response_model=UserRead)
async def toggle_user_active(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin_user),
):
    """
    Activa o desactiva un usuario (solo para admins)
    """
    auth_service = AuthService(db)
    return await auth_service.toggle_user_active(user_id)


@router.put("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin_user),
):
    """
    Resetea la contraseña de un usuario y genera una temporal (solo para admins)
    """
    auth_service = AuthService(db)
    temp_password = await auth_service.reset_user_password(user_id)
    return {
        "message": "Contraseña reseteada exitosamente",
        "temporary_password": temp_password
    }


@router.put("/{user_id}/force-password-change", response_model=UserRead)
async def force_password_change(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID,
    force: bool = True,
    current_user: User = Depends(get_current_admin_user),
):
    """
    Fuerza a un usuario a cambiar su contraseña en el próximo login
    """
    auth_service = AuthService(db)
    return await auth_service.force_password_change(user_id, force)


@router.post("/change-password", response_model=dict)
async def change_password(
    *,
    db: AsyncSession = Depends(get_db),
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Permite al usuario cambiar su propia contraseña
    """
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas no coinciden"
        )
    
    auth_service = AuthService(db)
    await auth_service.change_user_password(
        current_user.id,
        password_data
    )
    
    return {"message": "Contraseña cambiada exitosamente"}


@router.get("/roles", response_model=List[dict])
async def get_available_roles(
    current_user: User = Depends(get_current_admin_user),
):
    """
    Obtiene la lista de roles disponibles en el sistema
    """
    return [
        {
            "value": UserRole.ADMIN.value,
            "label": "Administrador",
            "description": "Acceso completo al sistema"
        },
        {
            "value": UserRole.CONTADOR.value,
            "label": "Contador",
            "description": "Puede crear asientos y acceder a reportes"
        },
        {
            "value": UserRole.SOLO_LECTURA.value,
            "label": "Solo Lectura",
            "description": "Solo puede consultar reportes y datos"
        }
    ]
