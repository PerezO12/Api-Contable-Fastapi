import secrets
import string
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from fastapi_users import BaseUserManager, UUIDIDMixin
from passlib.context import CryptContext
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole, UserSession
from app.schemas.user import (
    UserCreateByAdmin, UserResponse, UserStatsResponse, 
    UserCreate, UserUpdate, UserRead, PasswordChangeRequest
)
from app.utils.security import validate_password_strength
from app.utils.exceptions import UserNotFoundError, UserValidationError, AuthenticationError


class AuthService:
    """
    Servicio para manejar la lógica de autenticación y gestión de usuarios
    Siguiendo las mejores prácticas de FastAPI y arquitectura limpia
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña contra su hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
        
    def _hash_password(self, password: str) -> str:
        """Genera el hash de una contraseña"""
        return self.pwd_context.hash(password)
    
    def generate_temporary_password(self, length: int = 12) -> str:
        """Genera una contraseña temporal segura"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Asegurar que tenga al menos una mayúscula, minúscula, número y símbolo
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        if not any(c in "!@#$%^&*" for c in password):
            password = password[:-1] + secrets.choice("!@#$%^&*")
            
        return password

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Obtiene un usuario por ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Autentica un usuario con email y contraseña"""
        user = await self.get_user_by_email(email)
        
        if not user:
            return None
            
        # Verificar si está bloqueado
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Cuenta bloqueada hasta {user.locked_until}"
            )
        
        # Verificar contraseña
        if not self._verify_password(password, user.hashed_password):
            # Incrementar intentos fallidos
            user.increment_login_attempts()
            await self.db.commit()
            return None        # Login exitoso
        await self._update_successful_login(user)
        return user

    async def login_user(self, email: str, password: str) -> dict:
        """Autentica un usuario y retorna tokens JWT"""
        from app.utils.jwt_manager import create_token_pair
        from app.core.config import settings
        
        user = await self.authenticate_user(email, password)
        
        if not user:
            raise AuthenticationError("Credenciales inválidas")
        
        # Crear tokens
        token_data = create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value
        )
        
        # Crear respuesta con el formato correcto para Token schema
        return {
            "access_token": token_data["access_token"],
            "token_type": token_data["token_type"],
            "expires_in": settings.access_token_expire_minutes * 60,
            "refresh_token": token_data["refresh_token"]
        }
        
        return token_data
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Renueva un token de acceso usando un refresh token"""
        from app.utils.jwt_manager import jwt_manager, create_token_pair
        from app.core.config import settings
        
        # Verificar el refresh token
        payload = jwt_manager.verify_refresh_token(refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationError("Token de actualización inválido")
        
        # Verificar que el usuario aún existe y está activo
        user = await self.get_user_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("Usuario no válido")
          # Crear nuevos tokens
        token_data = create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value
        )
        
        return {
            "access_token": token_data["access_token"],
            "token_type": token_data["token_type"],
            "expires_in": settings.access_token_expire_minutes * 60,
            "refresh_token": token_data["refresh_token"]
        }
    
    async def logout_user(self, user_id: uuid.UUID) -> bool:
        """Cierra sesión del usuario revocando sus sesiones activas"""
        # Revocar todas las sesiones activas del usuario
        sessions_revoked = await self.revoke_all_user_sessions(user_id)
        return sessions_revoked > 0

    async def _update_successful_login(self, user: User) -> None:
        """Actualiza datos después de un login exitoso"""
        user.update_last_login()
        await self.db.commit()

    async def create_user_by_admin(
        self, 
        user_data: UserCreateByAdmin, 
        created_by_id: uuid.UUID
    ) -> User:
        """Crea un nuevo usuario por parte de un administrador"""
        
        # Verificar si el email ya existe
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise UserValidationError("Ya existe un usuario con este email")

        # Validar fortaleza de contraseña temporal
        validation = validate_password_strength(user_data.temporary_password)
        if not validation["is_valid"]:
            raise UserValidationError(f"Contraseña temporal débil: {', '.join(validation['errors'])}")

        # Crear hash de la contraseña temporal
        hashed_password = self._hash_password(user_data.temporary_password)

        # Crear el usuario
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
            notes=user_data.notes,
            created_by_id=created_by_id,
            force_password_change=True,
            is_active=True,
            is_superuser=user_data.role == UserRole.ADMIN,
            is_verified=True,
            password_changed_at=datetime.now(timezone.utc)
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def create_user(self, user_data: UserCreate, created_by_id: uuid.UUID) -> User:
        """Crea un nuevo usuario (método estándar)"""
        
        # Verificar si el email ya existe
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise UserValidationError("Ya existe un usuario con este email")

        # Crear hash de la contraseña
        hashed_password = self._hash_password(user_data.password)

        # Crear el usuario
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
            notes=user_data.notes,
            created_by_id=created_by_id,
            force_password_change=user_data.force_password_change,
            is_active=True,
            is_superuser=user_data.role == UserRole.ADMIN,
            is_verified=True,
            password_changed_at=datetime.now(timezone.utc)
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """Actualiza un usuario existente"""
        user = await self.get_user_by_id(user_id)
        
        if not user:
            return None

        # Actualizar campos
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Si se está actualizando el email, verificar que no exista
        if "email" in update_data and update_data["email"] != user.email:
            existing_user = await self.get_user_by_email(update_data["email"])
            if existing_user:
                raise UserValidationError("Ya existe un usuario con este email")

        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_user_stats(self) -> UserStatsResponse:
        """Obtiene estadísticas de usuarios del sistema"""
        
        # Total de usuarios
        total_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_result.scalar() or 0
        
        # Usuarios activos
        active_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_result.scalar() or 0
        
        # Usuarios bloqueados
        locked_result = await self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.locked_until.is_not(None),
                    User.locked_until > datetime.now(timezone.utc)
                )
            )
        )
        locked_users = locked_result.scalar() or 0
        
        # Usuarios por rol
        users_by_role = {}
        for role in UserRole:
            role_result = await self.db.execute(
                select(func.count(User.id)).where(User.role == role)
            )
            users_by_role[role.value] = role_result.scalar() or 0
        
        # Logins recientes (últimas 24 horas)
        recent_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_result = await self.db.execute(
            select(func.count(User.id)).where(
                User.last_login >= recent_threshold
            )
        )
        recent_logins = recent_result.scalar() or 0

        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            locked_users=locked_users,
            users_by_role=users_by_role,
            recent_logins=recent_logins
        )

    async def get_users_list(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> List[UserResponse]:
        """Obtiene la lista de usuarios con filtros opcionales"""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
            
        if is_active is not None:
            query = query.where(User.is_active == is_active)
            
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                last_login=user.last_login,
                created_at=user.created_at,
            )
            for user in users
        ]

    async def toggle_user_active(self, user_id: uuid.UUID) -> User:
        """Activa o desactiva un usuario"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("Usuario no encontrado")

        user.is_active = not user.is_active
        user.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def reset_user_password(self, user_id: uuid.UUID) -> str:
        """Resetea la contraseña de un usuario y genera una temporal"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("Usuario no encontrado")

        # Generar nueva contraseña temporal
        temp_password = self.generate_temporary_password()
        hashed_password = self._hash_password(temp_password)

        # Actualizar usuario
        user.hashed_password = hashed_password
        user.force_password_change = True
        user.password_changed_at = datetime.now(timezone.utc)
        user.reset_login_attempts()
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

        return temp_password

    async def force_password_change(self, user_id: uuid.UUID, force: bool = True) -> User:
        """Fuerza o no a un usuario a cambiar su contraseña"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("Usuario no encontrado")

        user.force_password_change = force
        user.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def change_user_password(
        self, 
        user_id: uuid.UUID, 
        password_data: PasswordChangeRequest
    ) -> bool:
        """Cambia la contraseña del usuario verificando la actual"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("Usuario no encontrado")

        # Verificar que las contraseñas nuevas coincidan
        if password_data.new_password != password_data.confirm_password:
            raise UserValidationError("Las contraseñas nuevas no coinciden")

        # Verificar contraseña actual
        if not self._verify_password(password_data.current_password, user.hashed_password):
            raise UserValidationError("Contraseña actual incorrecta")

        # Validar fortaleza de la nueva contraseña
        validation = validate_password_strength(password_data.new_password)
        if not validation["is_valid"]:
            raise UserValidationError(f"Contraseña débil: {', '.join(validation['errors'])}")

        # Actualizar con nueva contraseña
        user.hashed_password = self._hash_password(password_data.new_password)
        user.force_password_change = False
        user.password_changed_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

        return True

    async def validate_user_permissions(self, user: User, required_permissions: List[str]) -> bool:
        """Valida si un usuario tiene los permisos requeridos"""
        if not user.is_active:
            return False
            
        if user.is_locked:
            return False
            
        # Mapeo básico de permisos por rol
        role_permissions = {
            UserRole.ADMIN: ["*"],  # Todos los permisos
            UserRole.CONTADOR: [
                "accounts:read", "accounts:write", 
                "entries:read", "entries:write",
                "reports:read", "reports:export"
            ],
            UserRole.SOLO_LECTURA: [
                "accounts:read", "entries:read", "reports:read"
            ]
        }
        
        user_permissions = role_permissions.get(user.role, [])
        
        # Admin tiene todos los permisos
        if "*" in user_permissions:
            return True
            
        # Verificar permisos específicos
        return all(perm in user_permissions for perm in required_permissions)

    async def create_user_session(
        self, 
        user_id: uuid.UUID, 
        token_jti: str, 
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Crea una nueva sesión de usuario"""
        session = UserSession(
            user_id=user_id,
            token_jti=token_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session

    async def revoke_user_session(self, token_jti: str) -> bool:
        """Revoca una sesión de usuario"""
        result = await self.db.execute(
            select(UserSession).where(UserSession.token_jti == token_jti)
        )
        session = result.scalar_one_or_none()
        
        if session:
            await self.db.delete(session)
            await self.db.commit()
            return True
            
        return False

    async def cleanup_expired_sessions(self) -> int:
        """Limpia sesiones expiradas y retorna el número de sesiones eliminadas"""
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(UserSession).where(UserSession.expires_at < now)
        )
        expired_sessions = result.scalars().all()
        
        for session in expired_sessions:
            await self.db.delete(session)
            
        await self.db.commit()
        
        return len(expired_sessions)

    async def get_user_active_sessions(self, user_id: uuid.UUID) -> List[UserSession]:
        """Obtiene todas las sesiones activas de un usuario"""
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.expires_at > now
                )
            ).order_by(UserSession.created_at.desc())
        )
        
        return list(result.scalars().all())

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> int:
        """Revoca todas las sesiones de un usuario"""
        result = await self.db.execute(
            select(UserSession).where(UserSession.user_id == user_id)
        )
        sessions = result.scalars().all()
        
        for session in sessions:
            await self.db.delete(session)
            
        await self.db.commit()
        
        return len(sessions)    
    
    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Elimina un usuario del sistema"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
            
        # Revocar todas las sesiones primero
        await self.revoke_all_user_sessions(user_id)
        
        # Eliminar el usuario
        await self.db.delete(user)
        await self.db.commit()
        
        return True

    async def create_default_admin_user(self) -> Optional[User]:
        """
        Crea el usuario administrador por defecto si no existe ningún admin
        Esta función se ejecuta durante el startup de la aplicación
        """
        from app.config import settings
        
        # Verificar si ya existe algún usuario administrador
        result = await self.db.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            # Ya existe un admin, no crear uno nuevo
            return None
        
        # Verificar si ya existe el email configurado
        existing_user = await self.get_user_by_email(settings.DEFAULT_ADMIN_EMAIL)
        if existing_user:
            # El email ya está en uso, no crear usuario
            return None
        
        # Crear el usuario administrador por defecto
        try:
            hashed_password = self._hash_password(settings.DEFAULT_ADMIN_PASSWORD)
            
            admin_user = User(
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=hashed_password,
                full_name=settings.DEFAULT_ADMIN_FULL_NAME,
                role=UserRole.ADMIN,
                notes="Usuario administrador creado automáticamente durante el startup",
                force_password_change=False,  # No forzar cambio en primera vez
                is_active=True,
                is_superuser=True,
                is_verified=True,
                password_changed_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.db.add(admin_user)
            await self.db.commit()
            await self.db.refresh(admin_user)
            
            return admin_user
            
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Error creando usuario administrador por defecto: {str(e)}")

    @classmethod
    async def ensure_default_admin_exists(cls, db: AsyncSession) -> Optional[User]:
        """
        Método de clase para asegurar que existe un administrador por defecto
        Para uso durante el startup de la aplicación
        """
        auth_service = cls(db)
        return await auth_service.create_default_admin_user()
