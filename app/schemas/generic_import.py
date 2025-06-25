"""
Sistema de Importación Genérico Basado en Metadatos
Esquemas Pydantic para el asistente de importación tipo Odoo
"""
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class FieldType(str, Enum):
    """Tipos de datos soportados"""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    EMAIL = "email"
    PHONE = "phone"
    MANY_TO_ONE = "many_to_one"


class ImportPolicy(str, Enum):
    """Políticas de importación"""
    CREATE_ONLY = "create_only"
    UPDATE_ONLY = "update_only"
    UPSERT = "upsert"


class ValidationRule(BaseModel):
    """Regla de validación personalizada"""
    rule_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    error_message: str


class FieldMetadata(BaseModel):
    """Metadatos de un campo del modelo"""
    internal_name: str = Field(..., description="Nombre interno del campo")
    display_label: str = Field(..., description="Etiqueta para mostrar al usuario")
    field_type: FieldType = Field(..., description="Tipo de dato")
    is_required: bool = Field(default=False, description="Si el campo es obligatorio")
    is_unique: bool = Field(default=False, description="Si requiere unicidad")
    max_length: Optional[int] = Field(default=None, description="Longitud máxima para strings")
    min_value: Optional[float] = Field(default=None, description="Valor mínimo para números")
    max_value: Optional[float] = Field(default=None, description="Valor máximo para números")
    related_model: Optional[str] = Field(default=None, description="Modelo destino para relaciones")
    search_field: Optional[str] = Field(default=None, description="Campo clave para buscar en relaciones")
    validation_rules: List[ValidationRule] = Field(default_factory=list)
    description: Optional[str] = Field(default=None, description="Descripción del campo")
    default_value: Optional[str] = Field(default=None, description="Valor por defecto")
    choices: Optional[List[Dict[str, str]]] = Field(default=None, description="Opciones válidas para enums: [{'value': 'customer', 'label': 'Cliente'}]")


class ModelMetadata(BaseModel):
    """Metadatos completos de un modelo"""
    model_name: str = Field(..., description="Nombre del modelo")
    display_name: str = Field(..., description="Nombre para mostrar")
    description: Optional[str] = Field(None, description="Descripción del modelo")
    fields: List[FieldMetadata] = Field(..., description="Lista de campos disponibles")
    import_permissions: List[str] = Field(default_factory=list, description="Permisos requeridos")
    business_key_fields: List[str] = Field(default_factory=list, description="Campos clave para upsert")
    table_name: Optional[str] = Field(None, description="Nombre de la tabla en BD")


# === Esquemas para Upload de Archivo ===

class FileInfo(BaseModel):
    """Información del archivo subido"""
    name: str
    size: int
    encoding: str
    delimiter: Optional[str] = None  # Para CSV
    total_rows: int


class DetectedColumn(BaseModel):
    """Columna detectada en el archivo"""
    name: str
    sample_values: List[str] = Field(default_factory=list, max_length=5)
    data_type_hint: Optional[str] = None  # Tipo detectado automáticamente


class ImportSessionResponse(BaseModel):
    """Respuesta al subir archivo"""
    import_session_token: str
    model: str
    model_display_name: str
    file_info: FileInfo
    detected_columns: List[DetectedColumn]
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list, max_length=10)


# === Esquemas para Mapeo de Campos ===

class MappingSuggestion(BaseModel):
    """Sugerencia automática de mapeo"""
    column_name: str
    suggested_field: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class FieldInfo(BaseModel):
    """Información de campo para mapeo"""
    internal_name: str
    display_label: str
    field_type: str
    is_required: bool
    is_unique: bool = False
    max_length: Optional[int] = None
    related_model: Optional[str] = None
    search_field: Optional[str] = None
    description: Optional[str] = None


class ModelMappingResponse(BaseModel):
    """Respuesta con información del modelo para mapeo"""
    model: str
    model_display_name: str
    available_fields: List[FieldInfo]
    suggested_mappings: List[MappingSuggestion] = Field(default_factory=list)
    available_templates: List[Dict[str, Any]] = Field(default_factory=list)


# === Esquemas para Vista Previa ===

class ColumnMapping(BaseModel):
    """Mapeo de columna a campo"""
    column_name: str
    field_name: Optional[str] = None  # None = ignorar columna
    default_value: Optional[str] = None


class ValidationError(BaseModel):
    """Error de validación específico"""
    field_name: str
    error_type: str
    message: str
    current_value: Optional[str] = None


class PreviewRowData(BaseModel):
    """Datos de una fila en preview"""
    row_number: int
    original_data: Dict[str, Any]
    transformed_data: Dict[str, Any]
    validation_status: str  # "valid", "error", "warning"
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)


class ValidationSummary(BaseModel):
    """Resumen de validación"""
    total_rows_analyzed: int
    valid_rows: int
    rows_with_errors: int
    rows_with_warnings: int
    error_breakdown: Dict[str, int] = Field(default_factory=dict)


class ImportPreviewRequest(BaseModel):
    """Request para vista previa"""
    import_session_token: str
    column_mappings: List[ColumnMapping]
    preview_rows: int = Field(default=10, ge=1, le=50)
    batch_size: Optional[int] = Field(default=None, ge=1)
    batch_number: Optional[int] = Field(default=None, ge=0)


class ImportPreviewResponse(BaseModel):
    """Respuesta de vista previa"""
    import_session_token: str
    model: str
    total_rows: int
    preview_data: List[PreviewRowData]
    validation_summary: ValidationSummary
    can_proceed: bool
    blocking_issues: List[str] = Field(default_factory=list)
    can_skip_errors: bool = Field(default=True)  # Indica si los errores se pueden omitir
    skip_errors_available: bool = Field(default=True)  # Indica si la opción está disponible
    batch_info: Optional[Dict[str, Any]] = Field(default=None)  # Información del lote actual


# === Esquemas para Ejecución ===

class ImportOptions(BaseModel):
    """Opciones de importación"""
    batch_size: int = Field(default=100, ge=1, le=1000)
    continue_on_error: bool = Field(default=True)
    validate_foreign_keys: bool = Field(default=True)
    skip_duplicates: bool = Field(default=False)
    create_missing_foreign_keys: bool = Field(default=False)


class ImportExecutionRequest(BaseModel):
    """Request para ejecutar importación"""
    import_session_token: str
    column_mappings: List[ColumnMapping]
    import_policy: ImportPolicy
    options: ImportOptions = Field(default_factory=ImportOptions)


class OperationSummary(BaseModel):
    """Resumen de operaciones realizadas"""
    created: int = 0
    updated: int = 0
    skipped: int = 0


class FailedOperationSummary(BaseModel):
    """Resumen de operaciones fallidas"""
    validation_errors: int = 0
    constraint_violations: int = 0
    system_errors: int = 0
    
    @property
    def total(self) -> int:
        return self.validation_errors + self.constraint_violations + self.system_errors


class ExecutionSummary(BaseModel):
    """Resumen de ejecución completa"""
    total_rows_processed: int
    successful_operations: OperationSummary
    failed_operations: FailedOperationSummary
    processing_time_seconds: float
    throughput_rows_per_second: float


class DetailedError(BaseModel):
    """Error detallado de importación"""
    row_number: int
    error_type: str
    field_name: Optional[str] = None
    message: str
    suggested_action: Optional[str] = None


class ImportExecutionResponse(BaseModel):
    """Respuesta de ejecución"""
    import_session_token: str
    execution_id: str
    status: str  # "completed", "failed", "partial"    execution_summary: ExecutionSummary
    detailed_errors: List[DetailedError] = Field(default_factory=list, max_length=100)
    warnings: List[DetailedError] = Field(default_factory=list, max_length=50)


# === Esquemas para Plantillas ===

class ImportTemplate(BaseModel):
    """Plantilla de mapeo reutilizable"""
    name: str
    model: str
    description: Optional[str] = None
    column_mappings: List[ColumnMapping]
    is_public: bool = Field(default=False)
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


class CreateTemplateRequest(BaseModel):
    """Request para crear plantilla"""
    name: str = Field(..., min_length=1, max_length=100)
    model: str
    description: Optional[str] = Field(None, max_length=500)
    column_mappings: List[ColumnMapping]
    is_public: bool = Field(default=False)


class ApplyTemplateRequest(BaseModel):
    """Request para aplicar plantilla"""
    import_session_token: str
    template_id: str


# === Esquemas para Sesiones ===

class ImportSession(BaseModel):
    """Sesión de importación"""
    token: str
    model: str
    model_metadata: ModelMetadata
    file_info: FileInfo
    detected_columns: List[DetectedColumn]
    sample_rows: List[Dict[str, Any]]
    user_id: str
    created_at: datetime
    expires_at: datetime
    file_path: str  # Ruta temporal del archivo
    column_mappings: Optional[List[ColumnMapping]] = None  # Mapeo de columnas configurado por el usuario


class ImportProgress(BaseModel):
    """Progreso de importación para tracking"""
    status: str  # "uploading", "processing", "completed", "failed"
    processed_rows: int = 0
    total_rows: int = 0
    completion_percentage: float = 0.0
    current_batch: int = 0
    estimated_time_remaining: Optional[int] = None  # segundos
    message: Optional[str] = None


# === Esquemas para Importación Asíncrona ===

class AsyncImportResponse(BaseModel):
    """Respuesta para importación asíncrona"""
    execution_id: str
    status: str  # "queued", "processing", "completed", "failed"
    estimated_completion_time: Optional[datetime] = None
    progress_url: str


class ImportStatusResponse(BaseModel):
    """Estado de importación asíncrona"""
    execution_id: str
    status: str
    progress: ImportProgress
    result: Optional[ImportExecutionResponse] = None
    error_message: Optional[str] = None


# === Aliases for backward compatibility ===
ExecutionRequest = ImportExecutionRequest
ExecutionResponse = ImportExecutionResponse
