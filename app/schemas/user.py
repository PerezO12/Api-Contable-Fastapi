import uuid
from datetime import datetime
from typing import Optional, List

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

from app.models.user import UserRole


# Esquemas FastAPI-Users compatibles
class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema para leer usuarios - compatible con FastAPI-Users"""
    full_name: str
    role: UserRole
    notes: Optional[str] = None
    last_login: Optional[datetime] = None
    force_password_change: bool = True
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(schemas.BaseUserCreate):
    """Schema para crear usuarios - compatible con FastAPI-Users"""
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.SOLO_LECTURA
    notes: Optional[str] = Field(None, max_length=1000)
    force_password_change: bool = True
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Valida la fortaleza de la contraseña usando la función del utils"""
        from app.utils.security import validate_password_strength
        validation = validate_password_strength(v)
        if not validation["is_valid"]:
            raise ValueError(f"Contraseña débil: {', '.join(validation['errors'])}")
        return v


class UserUpdate(schemas.BaseUserUpdate):
    """Schema para actualizar usuarios - compatible con FastAPI-Users"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    notes: Optional[str] = Field(None, max_length=1000)
    force_password_change: Optional[bool] = None


# Esquemas base adicionales (mantener compatibilidad)
class UserBase(BaseModel):
    """Schema base para usuarios"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.SOLO_LECTURA
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=1000)


class UserUpdatePassword(BaseModel):
    """Schema para cambiar contraseña"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        from app.utils.security import validate_password_strength
        validation = validate_password_strength(v)
        if not validation["is_valid"]:
            raise ValueError(f"Contraseña débil: {', '.join(validation['errors'])}")
        return v


class UserInDB(UserRead):
    """Schema para usuario en base de datos (incluye hash de contraseña)"""
    hashed_password: str


class UserProfile(BaseModel):
    """Schema para el perfil del usuario autenticado"""
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    last_login: Optional[datetime] = None
    force_password_change: bool
    
    model_config = ConfigDict(from_attributes=True)


# Esquemas para autenticación
class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr
    password: str


class UserRegister(UserCreate):
    """Schema para registro de usuario (alias de UserCreate)"""
    pass


class Token(BaseModel):
    """Schema para token de acceso y actualización"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """Schema para solicitud de refresh token"""
    refresh_token: str


class TokenData(BaseModel):
    """Schema para datos del token"""
    email: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    role: Optional[UserRole] = None


# Esquemas para listado paginado
class UserList(BaseModel):
    """Schema para listado de usuarios"""
    users: list[UserRead]
    total: int
    page: int
    size: int
    pages: int


# Esquemas para estadísticas
class UserStatsResponse(BaseModel):
    """Schema para estadísticas de usuarios - corregido nombre"""
    total_users: int
    active_users: int
    locked_users: int
    users_by_role: dict[str, int]
    recent_logins: int  # Últimas 24 horas


class UserCreateByAdmin(BaseModel):
    """Schema para crear usuarios por parte de un administrador"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.SOLO_LECTURA
    notes: Optional[str] = Field(None, max_length=1000)
    temporary_password: str = Field(..., min_length=8, max_length=100)
    force_password_change: bool = True
    
    @field_validator('temporary_password')
    @classmethod
    def validate_temporary_password(cls, v):
        from app.utils.security import validate_password_strength
        validation = validate_password_strength(v)
        if not validation["is_valid"]:        raise ValueError(f"Contraseña temporal débil: {', '.join(validation['errors'])}")
        return v


class UserResponse(BaseModel):
    """Schema de respuesta simplificado para listas de usuarios"""
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeRequest(BaseModel):
    """Schema para cambio de contraseña"""
    current_password: str
    new_password: str
    confirm_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        from app.utils.security import validate_password_strength
        validation = validate_password_strength(v)
        if not validation["is_valid"]:
            raise ValueError(f"Contraseña débil: {', '.join(validation['errors'])}")
        return v


class UserSessionInfo(BaseModel):
    """Schema para información de sesión del usuario"""
    user_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    permissions: dict
    last_login: Optional[datetime] = None
    session_expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Esquemas adicionales para el sistema de autenticación
class UserSessionResponse(BaseModel):
    """Schema para respuesta de información de sesiones activas"""
    session_id: str
    user_id: uuid.UUID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    is_current: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class UserSessionsListResponse(BaseModel):
    """Schema para listar sesiones de un usuario"""
    user_id: uuid.UUID
    active_sessions: List[UserSessionResponse]
    total_sessions: int


class UserCreationResponse(BaseModel):
    """Schema para respuesta después de crear un usuario"""
    user: UserResponse
    temporary_password: Optional[str] = None
    message: str


class UserPasswordResetResponse(BaseModel):
    """Schema para respuesta de reset de contraseña"""
    user_id: uuid.UUID
    email: EmailStr
    temporary_password: str
    message: str
    expires_at: datetime


class UserBulkOperationRequest(BaseModel):
    """Schema para operaciones masivas en usuarios"""
    user_ids: List[uuid.UUID]
    operation: str  # "activate", "deactivate", "reset_password", "delete"
    reason: Optional[str] = None


class UserBulkOperationResponse(BaseModel):
    """Schema para respuesta de operaciones masivas"""
    processed: int
    successful: List[uuid.UUID]
    failed: List[dict]  # {"user_id": uuid, "error": str}
    operation: str


class UserFilters(BaseModel):
    """Schema para filtros de búsqueda de usuarios"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None


class UserSearchResponse(BaseModel):
    """Schema para respuesta de búsqueda paginada de usuarios"""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UserAuditLog(BaseModel):
    """Schema para logs de auditoría de usuarios"""
    user_id: uuid.UUID
    action: str
    details: dict
    timestamp: datetime
    performed_by: uuid.UUID
    ip_address: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
