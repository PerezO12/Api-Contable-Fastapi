import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import String, Text, ForeignKey, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base
from app.models.user import User


class AuditAction(str, Enum):
    """Tipos de acciones de auditoría"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    LOGIN = "login"
    LOGOUT = "logout"
    POST_ENTRY = "post_entry"
    CANCEL_ENTRY = "cancel_entry"
    APPROVE_ENTRY = "approve_entry"
    EXPORT_REPORT = "export_report"


class AuditLogLevel(str, Enum):
    """Niveles de log de auditoría"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base):
    """
    Modelo para logs de auditoría del sistema
    Registra todas las acciones importantes de los usuarios
    """
    __tablename__ = "audit_logs"

    # Información de la acción
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[AuditAction] = mapped_column(nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Detalles de la acción
    description: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[AuditLogLevel] = mapped_column(default=AuditLogLevel.INFO, nullable=False)
    
    # Información de la sesión
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
      # Metadatos adicionales en JSON
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Timestamp específico (adicional al created_at heredado)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(user='{self.user.email}', action='{self.action}', resource='{self.resource_type}')>"


class ChangeTracking(Base):
    """
    Modelo para tracking detallado de cambios en registros
    Registra cambios campo por campo
    """
    __tablename__ = "change_tracking"

    # Información del registro cambiado
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    # Información del campo cambiado
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tipo de cambio
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    
    # Usuario que realizó el cambio
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Timestamp del cambio
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<ChangeTracking(table='{self.table_name}', field='{self.field_name}', type='{self.change_type}')>"


class SystemConfiguration(Base):
    """
    Modelo para configuración del sistema
    Almacena configuraciones modificables de la aplicación
    """
    __tablename__ = "system_configuration"

    # Clave de configuración
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Valor de configuración (JSON para flexibilidad)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Descripción de la configuración
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tipo de configuración para agrupación
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Si es editable por usuarios o solo por sistema
    is_user_editable: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Usuario que modificó por última vez
    modified_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    modified_by: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<SystemConfiguration(key='{self.key}', category='{self.category}')>"


class CompanyInfo(Base):
    """
    Modelo para información de la empresa
    Datos que aparecen en reportes financieros
    """
    __tablename__ = "company_info"

    # Información básica
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Dirección
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Contacto
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Configuración contable
    fiscal_year_start_month: Mapped[int] = mapped_column(default=1, nullable=False)  # Enero = 1
    default_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Logo y firma digital (rutas de archivos)
    logo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    signature_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
      # Metadatos adicionales
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Si esta es la configuración activa
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<CompanyInfo(name='{self.name}', tax_id='{self.tax_id}')>"


class NumberSequence(Base):
    """
    Modelo para secuencias de numeración automática
    Para generar números consecutivos de asientos, etc.
    """
    __tablename__ = "number_sequences"

    # Tipo de secuencia
    sequence_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Formato del número
    prefix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Configuración de la secuencia
    current_number: Mapped[int] = mapped_column(default=0, nullable=False)
    increment: Mapped[int] = mapped_column(default=1, nullable=False)
    min_digits: Mapped[int] = mapped_column(default=1, nullable=False)
    
    # Si se reinicia cada año/mes
    reset_annually: Mapped[bool] = mapped_column(default=False, nullable=False)
    reset_monthly: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Último reinicio
    last_reset_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Si está activa
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<NumberSequence(type='{self.sequence_type}', current={self.current_number})>"

    def get_next_number(self) -> str:
        """
        Genera el siguiente número en la secuencia
        """
        self.current_number += self.increment
        
        # Formatear el número con ceros a la izquierda
        number_str = str(self.current_number).zfill(self.min_digits)
        
        # Construir el número completo
        full_number = ""
        if self.prefix:
            full_number += self.prefix
        
        full_number += number_str
        
        if self.suffix:
            full_number += self.suffix
            
        return full_number

    def should_reset(self) -> bool:
        """
        Verifica si la secuencia debe reiniciarse
        """
        if not (self.reset_annually or self.reset_monthly):
            return False
            
        now = datetime.now(timezone.utc)
        
        if self.last_reset_date is None:
            return True
            
        if self.reset_monthly:
            return (now.year != self.last_reset_date.year or 
                   now.month != self.last_reset_date.month)
                   
        if self.reset_annually:
            return now.year != self.last_reset_date.year
            
        return False

    def reset_sequence(self) -> None:
        """
        Reinicia la secuencia
        """
        self.current_number = 0
        self.last_reset_date = datetime.now(timezone.utc)
