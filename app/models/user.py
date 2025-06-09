import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, Enum):
    """Roles de usuario del sistema contable"""
    ADMIN = "admin"
    CONTADOR = "contador" 
    SOLO_LECTURA = "solo_lectura"


class User(Base):
    """
    Modelo de usuario del sistema contable
    Usando SQLAlchemy 2.0+ modern syntax
    """
    __tablename__ = "users"

    # Campos básicos de usuario
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Estado del usuario
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Rol del sistema contable
    role: Mapped[UserRole] = mapped_column(default=UserRole.SOLO_LECTURA, nullable=False)
    
    # Campos de auditoría y seguridad
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )
    
    # Configuración de cuenta
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadatos adicionales
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # Relationships
    created_by: Mapped[Optional["User"]] = relationship(
        "User", 
        remote_side="User.id",
        back_populates="created_users"
    )
    created_users: Mapped[List["User"]] = relationship(
        "User", 
        back_populates="created_by",
        cascade="all, delete-orphan"
    )    
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession", 
        back_populates="user",
        cascade="all, delete-orphan"
    )    
    # Audit relationships (forward references para evitar imports circulares)
    # audit_logs: Mapped[List["AuditLog"]] = relationship(
    #     "AuditLog", 
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )
    # change_tracking_entries: Mapped[List["ChangeTracking"]] = relationship(
    #     "ChangeTracking", 
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )

    def __repr__(self) -> str:
        return f"<User(email='{self.email}', role='{self.role}', full_name='{self.full_name}')>"

    @property
    def is_admin(self) -> bool:
        """Verifica si el usuario es administrador"""
        return self.role == UserRole.ADMIN

    @property
    def is_contador(self) -> bool:
        """Verifica si el usuario es contador"""
        return self.role == UserRole.CONTADOR

    @property
    def can_write(self) -> bool:
        """Verifica si el usuario puede escribir/modificar datos"""
        return self.role in [UserRole.ADMIN, UserRole.CONTADOR]

    @property
    def is_readonly(self) -> bool:
        """Verifica si el usuario es de solo lectura"""
        return self.role == UserRole.SOLO_LECTURA

    @property
    def is_locked(self) -> bool:
        """Verifica si la cuenta está bloqueada temporalmente"""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    @property
    def can_modify_accounts(self) -> bool:
        """Verifica si el usuario puede modificar cuentas"""
        return self.role in [UserRole.ADMIN, UserRole.CONTADOR]

    @property
    def can_create_entries(self) -> bool:
        """Verifica si el usuario puede crear asientos contables"""
        return self.role in [UserRole.ADMIN, UserRole.CONTADOR]

    @property
    def can_manage_users(self) -> bool:
        """Verifica si el usuario puede gestionar otros usuarios"""
        return self.role == UserRole.ADMIN

    def reset_login_attempts(self) -> None:
        """Reinicia el contador de intentos de login"""
        self.login_attempts = 0
        self.locked_until = None

    def increment_login_attempts(self) -> None:
        """Incrementa los intentos fallidos y bloquea si es necesario"""
        self.login_attempts += 1
        if self.login_attempts >= 5:  # Bloquear después de 5 intentos
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

    def update_last_login(self) -> None:
        """Actualiza la fecha del último login"""
        self.last_login = datetime.now(timezone.utc)
        self.reset_login_attempts()


class UserSession(Base):
    """
    Modelo para tracking de sesiones activas de usuarios
    Según especificación de estructura.md
    """
    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(user_id='{self.user_id}', expires_at='{self.expires_at}')>"

    @property
    def is_expired(self) -> bool:
        """Verifica si la sesión ha expirado"""
        return datetime.now(timezone.utc) > self.expires_at
