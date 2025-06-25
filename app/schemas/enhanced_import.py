"""
Enhanced Import Response Schemas
Dynamic Pydantic schemas for detailed import reporting
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ImportErrorType(str, Enum):
    """Tipos de errores de importación"""
    DUPLICATE_KEY = "duplicate_key"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_REFERENCE = "invalid_reference"
    CONSTRAINT_VIOLATION = "constraint_violation"
    DATABASE_TIMEOUT = "database_timeout"
    VALIDATION_ERROR = "validation_error"
    BULK_INSERT_ERROR = "bulk_insert_error"
    BULK_UPSERT_ERROR = "bulk_upsert_error"
    CRITICAL_ERROR = "critical_error"
    UNKNOWN_ERROR = "unknown_error"


class ImportRecordStatus(str, Enum):
    """Estados de registros importados"""
    CREATED = "created"
    UPDATED = "updated"
    FAILED = "failed"
    SKIPPED = "skipped"


class DetailedImportError(BaseModel):
    """Error detallado de importación"""
    row_number: int = Field(..., description="Número de fila en el archivo")
    error_type: ImportErrorType = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje de error detallado")
    field_name: Optional[str] = Field(None, description="Campo que causó el error")
    field_value: Optional[str] = Field(None, description="Valor que causó el error")
    suggested_fix: Optional[str] = Field(None, description="Sugerencia para corregir el error")


class ImportRecordResult(BaseModel):
    """Resultado de un registro individual"""
    row_number: int = Field(..., description="Número de fila en el archivo")
    status: ImportRecordStatus = Field(..., description="Estado del registro")
    record_data: Optional[Dict[str, Any]] = Field(None, description="Datos del registro")
    error: Optional[DetailedImportError] = Field(None, description="Error si falló")
    processing_time_ms: Optional[float] = Field(None, description="Tiempo de procesamiento en ms")


class ImportBatchSummary(BaseModel):
    """Resumen de un batch de importación"""
    batch_number: int = Field(..., description="Número del batch")
    batch_size: int = Field(..., description="Tamaño del batch")
    total_processed: int = Field(..., description="Total de registros procesados")
    successful: int = Field(..., description="Registros creados exitosamente")
    updated: int = Field(..., description="Registros actualizados")
    failed: int = Field(..., description="Registros fallidos")
    skipped: int = Field(..., description="Registros omitidos")
    processing_time_seconds: float = Field(..., description="Tiempo de procesamiento del batch")
    records_per_second: float = Field(..., description="Registros procesados por segundo")
    errors_by_type: Dict[str, int] = Field(default_factory=dict, description="Errores agrupados por tipo")


class ImportPerformanceMetrics(BaseModel):
    """Métricas de rendimiento de la importación"""
    total_execution_time_seconds: float = Field(..., description="Tiempo total de ejecución")
    average_batch_time_seconds: float = Field(..., description="Tiempo promedio por batch")
    peak_records_per_second: float = Field(..., description="Pico de registros por segundo")
    average_records_per_second: float = Field(..., description="Promedio de registros por segundo")
    database_time_seconds: float = Field(..., description="Tiempo total en base de datos")
    validation_time_seconds: float = Field(..., description="Tiempo total en validaciones")
    memory_usage_mb: Optional[float] = Field(None, description="Uso de memoria en MB")


class ImportQualityReport(BaseModel):
    """Reporte de calidad de datos importados"""
    data_quality_score: float = Field(..., description="Puntuación de calidad (0-100)")
    completeness_score: float = Field(..., description="Puntuación de completitud (0-100)")
    accuracy_score: float = Field(..., description="Puntuación de precisión (0-100)")
    
    # Análisis por campos
    field_quality_analysis: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Análisis de calidad por campo"
    )
    
    # Recomendaciones
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recomendaciones para mejorar la calidad"
    )


class EnhancedImportExecutionResponse(BaseModel):
    """Respuesta mejorada de ejecución de importación"""
    
    # Información básica
    import_session_token: str = Field(..., description="Token de la sesión de importación")
    execution_id: str = Field(..., description="ID único de esta ejecución")
    model: str = Field(..., description="Modelo importado")
    import_policy: str = Field(..., description="Política de importación utilizada")
    
    # Estado y progreso
    status: str = Field(..., description="Estado de la importación")
    completed_at: datetime = Field(..., description="Fecha y hora de finalización")
    
    # Resumen ejecutivo
    summary: ImportBatchSummary = Field(..., description="Resumen ejecutivo")
    
    # Métricas de rendimiento
    performance_metrics: ImportPerformanceMetrics = Field(..., description="Métricas de rendimiento")
    
    # Calidad de datos
    quality_report: ImportQualityReport = Field(..., description="Reporte de calidad")
    
    # Resultados detallados (limitados para la respuesta)
    successful_samples: List[ImportRecordResult] = Field(
        default_factory=list,
        max_length=10,
        description="Muestra de registros exitosos"
    )
    failed_records: List[ImportRecordResult] = Field(
        default_factory=list,
        max_length=50,
        description="Registros fallidos (máximo 50)"
    )
    
    # Errores categorizados
    errors_by_type: Dict[ImportErrorType, List[DetailedImportError]] = Field(
        default_factory=dict,
        description="Errores categorizados por tipo"
    )
    
    # Recomendaciones post-importación
    post_import_actions: List[str] = Field(
        default_factory=list,
        description="Acciones recomendadas después de la importación"
    )
    
    # Enlaces para descargar reportes completos
    download_links: Dict[str, str] = Field(
        default_factory=dict,
        description="Enlaces para descargar reportes detallados"
    )


class ImportValidationPrecheck(BaseModel):
    """Pre-chequeo de validación antes de importar"""
    can_proceed: bool = Field(..., description="Si se puede proceder con la importación")
    estimated_time_minutes: float = Field(..., description="Tiempo estimado en minutos")
    estimated_memory_mb: float = Field(..., description="Memoria estimada requerida en MB")
    
    # Advertencias
    warnings: List[str] = Field(default_factory=list, description="Advertencias importantes")
    blocking_issues: List[str] = Field(default_factory=list, description="Problemas que impiden la importación")
    
    # Análisis de datos
    data_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Análisis preliminar de los datos"
    )
    
    # Configuración recomendada
    recommended_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuración recomendada para la importación"
    )


class AsyncImportStatus(BaseModel):
    """Estado de importación asíncrona en tiempo real"""
    execution_id: str = Field(..., description="ID de ejecución")
    status: str = Field(..., description="Estado actual")
    progress_percentage: float = Field(..., description="Porcentaje de progreso")
    current_batch: int = Field(..., description="Batch actual")
    total_batches: int = Field(..., description="Total de batches")
    
    # Contadores en tiempo real
    processed_records: int = Field(..., description="Registros procesados hasta ahora")
    successful_records: int = Field(..., description="Registros exitosos hasta ahora")
    failed_records: int = Field(..., description="Registros fallidos hasta ahora")
    
    # Estimaciones
    estimated_completion_time: Optional[datetime] = Field(None, description="Tiempo estimado de finalización")
    estimated_remaining_minutes: Optional[float] = Field(None, description="Minutos restantes estimados")
    
    # Performance actual
    current_records_per_second: float = Field(..., description="Velocidad actual de procesamiento")
    average_records_per_second: float = Field(..., description="Velocidad promedio")
    
    # Último error (si hay)
    last_error: Optional[DetailedImportError] = Field(None, description="Último error encontrado")
    
    # Métricas del sistema
    system_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métricas del sistema (CPU, memoria, etc.)"
    )


class ImportTemplateValidation(BaseModel):
    """Validación de plantilla de importación"""
    template_name: str = Field(..., description="Nombre de la plantilla")
    is_valid: bool = Field(..., description="Si la plantilla es válida")
    compatibility_score: float = Field(..., description="Puntuación de compatibilidad (0-100)")
    
    # Mapeos validados
    validated_mappings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Mapeos validados"
    )
    
    # Campos problemáticos
    problematic_fields: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Campos con problemas"
    )
    
    # Sugerencias de mejora
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="Sugerencias para mejorar la plantilla"
    )
