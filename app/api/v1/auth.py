from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.schemas.user import UserRead, Token, UserLogin, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.utils.exceptions import (
    AuthenticationError,
    UserNotFoundError,
    PasswordValidationError,
    raise_authentication_error,
    raise_user_not_found,
    raise_validation_error
)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Autenticación de usuario con email y contraseña
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.login_user(
            login_data.email, 
            login_data.password
        )
    except AuthenticationError:
        raise_authentication_error("Credenciales inválidas")
    except UserNotFoundError:
        raise_user_not_found()
    except PasswordValidationError as e:
        raise_validation_error(str(e))


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Autenticación compatible con OAuth2PasswordRequestForm
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.login_user(
            form_data.username,  # FastAPI OAuth2 usa username pero enviamos email
            form_data.password
        )
    except AuthenticationError:
        raise_authentication_error("Credenciales inválidas")
    except UserNotFoundError:
        raise_user_not_found()
    except PasswordValidationError as e:
        raise_validation_error(str(e))


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Renueva el token de acceso usando el refresh token
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.refresh_access_token(refresh_data.refresh_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_active_user)
):
    """
    Cierre de sesión del usuario
    """
    try:
        auth_service = AuthService(db)
        await auth_service.logout_user(current_user.id)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during logout"
        )


@router.post("/setup-admin", response_model=UserRead)
async def setup_admin(
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint especial para crear el primer usuario administrador
    Solo funciona si no existe ningún administrador en el sistema
    """
    try:
        auth_service = AuthService(db)
        admin_user = await auth_service.create_default_admin_user()
        
        if admin_user:
            return admin_user
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario administrador en el sistema"
            )
    except Exception as e:
        if "Ya existe un usuario administrador" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando administrador: {str(e)}"
        )
