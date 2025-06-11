"""
Schemas para exportación genérica de datos
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ExportFormat(str, Enum):
    """Formatos de exportación soportados"""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"


class TableName(str, Enum):
    """Tablas disponibles para exportación"""
    USERS = "users"
    ACCOUNTS = "accounts" 
    JOURNAL_ENTRIES = "journal_entries"
    JOURNAL_ENTRY_LINES = "journal_entry_lines"
    AUDIT_LOGS = "audit_logs"
    USER_SESSIONS = "user_sessions"
    CHANGE_TRACKING = "change_tracking"
    SYSTEM_CONFIGURATION = "system_configuration"
    COMPANY_INFO = "company_info"
    NUMBER_SEQUENCES = "number_sequences"


class ExportFilter(BaseModel):
    """Filtros genéricos para exportación"""
    ids: Optional[List[uuid.UUID]] = Field(default=None, description="IDs específicos")
    date_from: Optional[datetime] = Field(default=None, description="Fecha desde")
    date_to: Optional[datetime] = Field(default=None, description="Fecha hasta")
    active_only: Optional[bool] = Field(default=None, description="Solo registros activos")
    custom_filters: Optional[Dict[str, Any]] = Field(default=None, description="Filtros personalizados por campo")
    limit: Optional[int] = Field(default=None, description="Límite de registros", le=10000)
    offset: Optional[int] = Field(default=0, description="Offset para paginación")


class ColumnInfo(BaseModel):
    """Información de columna para exportación"""
    name: str = Field(..., description="Nombre de la columna")
    data_type: str = Field(..., description="Tipo de dato (string, number, date, boolean)")
    format: Optional[str] = Field(None, description="Formato específico")
    include: bool = Field(True, description="Incluir en la exportación")


class ExportRequest(BaseModel):
    """Solicitud de exportación genérica"""
    table_name: TableName = Field(..., description="Tabla a exportar")
    export_format: ExportFormat = Field(..., description="Formato de exportación")
    filters: ExportFilter = Field(default_factory=ExportFilter, description="Filtros a aplicar")
    columns: Optional[List[ColumnInfo]] = Field(default=None, description="Columnas específicas a exportar")
    include_metadata: bool = Field(default=True, description="Incluir metadatos en la exportación")
    file_name: Optional[str] = Field(default=None, description="Nombre personalizado del archivo")


class ExportMetadata(BaseModel):
    """Metadatos de la exportación"""
    export_date: datetime
    user_id: uuid.UUID
    table_name: str
    total_records: int
    exported_records: int
    filters_applied: Dict[str, Any]
    format: ExportFormat
    file_size_bytes: Optional[int] = None
    columns_exported: List[str]


class ExportResponse(BaseModel):
    """Respuesta de exportación"""
    file_name: str
    file_content: Union[str, bytes, dict]  # Contenido según el formato
    content_type: str
    metadata: ExportMetadata
    success: bool = True
    message: Optional[str] = None


class ExportError(BaseModel):
    """Error en exportación"""
    error_code: str
    message: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TableSchema(BaseModel):
    """Schema de tabla para mostrar información disponible"""
    table_name: str
    display_name: str
    description: str
    available_columns: List[ColumnInfo]
    total_records: int
    sample_data: Optional[List[Dict[str, Any]]] = None


class AvailableTablesResponse(BaseModel):
    """Respuesta con tablas disponibles para exportación"""
    tables: List[TableSchema]
    total_tables: int
