import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


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


# Esquemas para logs de auditoría
class AuditLogBase(BaseModel):
    """Schema base para logs de auditoría"""
    action: AuditAction
    resource_type: str  # "user", "account", "journal_entry", etc.
    resource_id: Optional[uuid.UUID] = None
    description: str
    level: AuditLogLevel = AuditLogLevel.INFO
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    """Schema para crear logs de auditoría"""
    user_id: uuid.UUID


class AuditLogRead(AuditLogBase):
    """Schema para leer logs de auditoría"""
    id: uuid.UUID
    user_id: uuid.UUID
    timestamp: datetime
    
    # Información del usuario
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_role: Optional[UserRole] = None
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogFilter(BaseModel):
    """Schema para filtrar logs de auditoría"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[uuid.UUID] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    resource_id: Optional[uuid.UUID] = None
    level: Optional[AuditLogLevel] = None
    search: Optional[str] = None


class AuditLogList(BaseModel):
    """Schema para listado paginado de logs"""
    logs: List[AuditLogRead]
    total: int
    page: int
    size: int
    pages: int


# Esquemas para reportes de auditoría
class UserActivitySummary(BaseModel):
    """Schema para resumen de actividad de usuario"""
    user_id: uuid.UUID
    user_email: str
    user_name: str
    total_actions: int
    last_activity: datetime
    actions_by_type: Dict[str, int]


class SystemActivityReport(BaseModel):
    """Schema para reporte de actividad del sistema"""
    start_date: datetime
    end_date: datetime
    total_actions: int
    unique_users: int
    actions_by_day: Dict[str, int]
    actions_by_type: Dict[str, int]
    top_users: List[UserActivitySummary]


class SecurityReport(BaseModel):
    """Schema para reporte de seguridad"""
    start_date: datetime
    end_date: datetime
    failed_logins: int
    successful_logins: int
    locked_accounts: int
    password_changes: int
    admin_actions: int
    suspicious_activities: List[AuditLogRead]


# Esquemas para tracking de cambios
class ChangeTrackingBase(BaseModel):
    """Schema base para tracking de cambios"""
    table_name: str
    record_id: uuid.UUID
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_type: str  # "INSERT", "UPDATE", "DELETE"


class ChangeTrackingCreate(ChangeTrackingBase):
    """Schema para crear tracking de cambios"""
    user_id: uuid.UUID


class ChangeTrackingRead(ChangeTrackingBase):
    """Schema para leer tracking de cambios"""
    id: uuid.UUID
    user_id: uuid.UUID
    timestamp: datetime
    
    # Información del usuario
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class RecordChangeHistory(BaseModel):
    """Schema para historial de cambios de un registro"""
    table_name: str
    record_id: uuid.UUID
    changes: List[ChangeTrackingRead]
    first_created: datetime
    last_modified: datetime
    total_changes: int


# Esquemas para configuración de auditoría
class AuditConfiguration(BaseModel):
    """Schema para configuración de auditoría"""
    enable_audit_logs: bool = True
    enable_change_tracking: bool = True
    log_retention_days: int = 365
    log_failed_logins: bool = True
    log_successful_logins: bool = True
    log_data_access: bool = False  # Solo para datos sensibles
    log_report_generation: bool = True
    alert_on_suspicious_activity: bool = True
    max_failed_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30


class AuditStats(BaseModel):
    """Schema para estadísticas de auditoría"""
    total_logs: int
    logs_last_24h: int
    logs_last_week: int
    logs_last_month: int
    most_active_users: List[UserActivitySummary]
    most_common_actions: Dict[str, int]
    system_health_score: float  # 0-100
