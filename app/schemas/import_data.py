"""
Schemas para importación de datos contables
Soporte para CSV, XLSX y JSON
"""
import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.account import AccountType, AccountCategory
from app.models.journal_entry import JournalEntryType
from app.utils.enum_validators import create_enum_validator


class ImportFormat(str, Enum):
    """Formatos de importación soportados"""
    CSV = "csv"
    XLSX = "xlsx" 
    JSON = "json"


class ImportDataType(str, Enum):
    """Tipos de datos a importar"""
    ACCOUNTS = "accounts"
    JOURNAL_ENTRIES = "journal_entries"
    MIXED = "mixed"  # Cuentas y asientos juntos


class ImportValidationLevel(str, Enum):
    """Niveles de validación"""
    STRICT = "strict"      # Fallar si hay cualquier error
    TOLERANT = "tolerant"  # Procesar lo que se pueda, reportar errores
    PREVIEW = "preview"    # Solo validar, no importar


# Schemas para importación de cuentas
class AccountImportRow(BaseModel):
    """Schema para una fila de importación de cuenta"""
    code: str = Field(..., min_length=1, max_length=20, description="Código de la cuenta")
    name: str = Field(..., min_length=2, max_length=200, description="Nombre de la cuenta")
    account_type: str = Field(..., description="Tipo de cuenta (ACTIVO, PASIVO, etc.)")
    category: Optional[str] = Field(None, description="Categoría de la cuenta")
    parent_code: Optional[str] = Field(None, description="Código de la cuenta padre")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción")
    is_active: bool = Field(True, description="Si la cuenta está activa")
    allows_movements: bool = Field(True, description="Si permite movimientos")
    requires_third_party: bool = Field(False, description="Si requiere terceros")
    requires_cost_center: bool = Field(False, description="Si requiere centro de costo")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas")
    # Metadatos de importación
    row_number: Optional[int] = Field(None, description="Número de fila en el archivo")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        return v.strip().upper()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return v.strip().title()    @field_validator('account_type', mode='before')
    @classmethod
    def validate_account_type(cls, v):
        """Valida el tipo de cuenta de forma case-insensitive"""
        if isinstance(v, str):
            return create_enum_validator(AccountType)(v)
        return v    
    @field_validator('category', mode='before')
    @classmethod
    def validate_category(cls, v):
        """Valida la categoría de cuenta de forma case-insensitive"""
        if v is None:
            return v
        if isinstance(v, str):
            return create_enum_validator(AccountCategory)(v)
        return v
    
    @field_validator('parent_code')
    @classmethod
    def validate_parent_code(cls, v):
        if v is None:
            return v
        return v.strip().upper()


# Schemas para importación de asientos
class JournalEntryLineImportRow(BaseModel):
    """Schema para una línea de asiento en importación"""
    account_code: str = Field(..., description="Código de la cuenta")
    description: str = Field(..., min_length=1, max_length=500, description="Descripción del movimiento")
    debit_amount: Optional[Decimal] = Field(None, ge=0, description="Monto débito")
    credit_amount: Optional[Decimal] = Field(None, ge=0, description="Monto crédito")
    third_party: Optional[str] = Field(None, max_length=100, description="Tercero")
    cost_center: Optional[str] = Field(None, max_length=50, description="Centro de costo")
    reference: Optional[str] = Field(None, max_length=100, description="Referencia")
    
    @model_validator(mode='after')
    def validate_amounts(self):
        """Valida que solo uno de los montos sea mayor que cero"""
        debit = self.debit_amount or Decimal('0')
        credit = self.credit_amount or Decimal('0')
        
        if (debit > 0 and credit > 0) or (debit == 0 and credit == 0):
            raise ValueError("Una línea debe tener monto en débito O crédito, no ambos o ninguno")
        
        return self


class JournalEntryImportRow(BaseModel):
    """Schema para un asiento en importación"""
    entry_date: date = Field(..., description="Fecha del asiento")
    reference: Optional[str] = Field(None, max_length=100, description="Referencia")
    description: str = Field(..., min_length=1, max_length=1000, description="Descripción del asiento")
    entry_type: str = Field("MANUAL", description="Tipo de asiento")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas")
    lines: List[JournalEntryLineImportRow] = Field(..., min_length=2, description="Líneas del asiento")
    # Metadatos de importación
    row_number: Optional[int] = Field(None, description="Número de fila en el archivo")    
    @field_validator('entry_type', mode='before')
    @classmethod
    def validate_entry_type(cls, v):
        """Valida el tipo de asiento de forma case-insensitive"""
        if isinstance(v, str):
            return create_enum_validator(JournalEntryType)(v)
        return v
    
    @field_validator('entry_date', mode='before')
    @classmethod
    def convert_date(cls, v):
        """Convertir string a date si es necesario"""
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                try:
                    return datetime.strptime(v, '%d/%m/%Y').date()
                except ValueError:
                    raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD o DD/MM/YYYY")
        return v
    
    @field_validator('lines')
    @classmethod
    def validate_lines_balance(cls, v):
        """Valida que el asiento esté balanceado"""
        if len(v) < 2:
            raise ValueError("Un asiento debe tener al menos 2 líneas")
        
        total_debit = sum(line.debit_amount or Decimal('0') for line in v)
        total_credit = sum(line.credit_amount or Decimal('0') for line in v)
        
        if total_debit != total_credit:
            raise ValueError(f"El asiento no está balanceado: Débitos={total_debit}, Créditos={total_credit}")
        
        if total_debit == 0:
            raise ValueError("El asiento debe tener movimientos con montos mayores a cero")
        
        return v


# Schemas para configuración de importación
class ImportConfiguration(BaseModel):
    """Configuración de importación"""
    data_type: ImportDataType = Field(..., description="Tipo de datos a importar")
    format: ImportFormat = Field(..., description="Formato del archivo")
    validation_level: ImportValidationLevel = Field(ImportValidationLevel.STRICT, description="Nivel de validación")
    batch_size: int = Field(100, ge=1, le=1000, description="Tamaño del lote para procesamiento")
    skip_duplicates: bool = Field(True, description="Omitir registros duplicados")
    update_existing: bool = Field(False, description="Actualizar registros existentes")
    continue_on_error: bool = Field(False, description="Continuar procesamiento en caso de errores")
    # Configuraciones específicas de formato
    csv_delimiter: str = Field(',', description="Delimitador para CSV")
    csv_encoding: str = Field('utf-8', description="Codificación para CSV")
    xlsx_sheet_name: Optional[str] = Field(None, description="Nombre de la hoja de Excel")
    xlsx_header_row: int = Field(1, ge=1, description="Número de fila con encabezados")


# Schemas para resultados de importación
class ImportError(BaseModel):
    """Error de importación"""
    row_number: Optional[int] = None
    field_name: Optional[str] = None
    error_code: str
    error_message: str
    error_type: str  # 'validation', 'business', 'system'
    severity: str = 'error'  # 'error', 'warning', 'info'


class ImportRowResult(BaseModel):
    """Resultado de importación por fila"""
    row_number: int
    status: str  # 'success', 'error', 'warning', 'skipped'
    entity_id: Optional[uuid.UUID] = None
    entity_code: Optional[str] = None
    entity_type: Optional[str] = None  # 'account', 'journal_entry'
    errors: List[ImportError] = []
    warnings: List[ImportError] = []


class ImportSummary(BaseModel):
    """Resumen de importación"""
    total_rows: int
    processed_rows: int
    successful_rows: int
    error_rows: int
    warning_rows: int
    skipped_rows: int
    processing_time_seconds: float
    
    # Estadísticas por tipo
    accounts_created: int = 0
    accounts_updated: int = 0
    journal_entries_created: int = 0
    
    # Errores más comunes
    most_common_errors: Dict[str, int] = {}
    
    # Propiedades calculadas para feedback mejorado
    @property
    def success_rate(self) -> float:
        """Tasa de éxito como porcentaje"""
        if self.total_rows == 0:
            return 0.0
        return (self.successful_rows / self.total_rows) * 100
    
    @property
    def error_rate(self) -> float:
        """Tasa de error como porcentaje"""
        if self.total_rows == 0:
            return 0.0
        return (self.error_rows / self.total_rows) * 100
    
    @property
    def status_message(self) -> str:
        """Mensaje de estado resumido"""
        if self.error_rows == 0 and self.successful_rows > 0:
            return f"✅ Importación exitosa: {self.successful_rows} filas procesadas correctamente"
        elif self.successful_rows == 0 and self.error_rows > 0:
            return f"❌ Importación fallida: {self.error_rows} filas con errores de {self.total_rows} total"
        elif self.successful_rows > 0 and self.error_rows > 0:
            return f"⚠️ Importación parcial: {self.successful_rows} exitosas, {self.error_rows} con errores"
        elif self.skipped_rows > 0:
            return f"📋 Importación completada: {self.successful_rows} procesadas, {self.skipped_rows} omitidas"
        else:
            return f"📊 Procesamiento completado: {self.processed_rows} filas analizadas"
    
    @property
    def detailed_feedback(self) -> List[str]:
        """Feedback detallado para mostrar al usuario"""
        feedback = []
        
        if self.successful_rows > 0:
            feedback.append(f"✅ {self.successful_rows} filas procesadas exitosamente")
            if self.accounts_created > 0:
                feedback.append(f"   📝 {self.accounts_created} cuentas creadas")
            if self.accounts_updated > 0:
                feedback.append(f"   🔄 {self.accounts_updated} cuentas actualizadas")
            if self.journal_entries_created > 0:
                feedback.append(f"   📋 {self.journal_entries_created} asientos contables creados")
        
        if self.error_rows > 0:
            feedback.append(f"❌ {self.error_rows} filas con errores")
            
            # Mostrar los errores más comunes
            if self.most_common_errors:
                top_errors = sorted(self.most_common_errors.items(), key=lambda x: x[1], reverse=True)[:3]
                feedback.append("   Errores más frecuentes:")
                for error_code, count in top_errors:
                    error_description = self._get_error_description(error_code)
                    feedback.append(f"   • {error_description}: {count} ocurrencias")
        
        if self.warning_rows > 0:
            feedback.append(f"⚠️ {self.warning_rows} filas con advertencias")
        
        if self.skipped_rows > 0:
            feedback.append(f"⏭️ {self.skipped_rows} filas omitidas (duplicados)")
        
        # Estadísticas de rendimiento
        feedback.append(f"⏱️ Tiempo de procesamiento: {self.processing_time_seconds:.2f} segundos")
        
        if self.total_rows > 0:
            feedback.append(f"📊 Tasa de éxito: {self.success_rate:.1f}%")
        
        return feedback
    
    def _get_error_description(self, error_code: str) -> str:
        """Obtener descripción amigable del código de error"""
        error_descriptions = {
            'ACCOUNT_CREATION_ERROR': 'Error de validación en datos de cuenta',
            'ACCOUNT_DUPLICATE': 'Cuenta duplicada',
            'ACCOUNT_NOT_FOUND': 'Cuenta no encontrada',
            'JOURNAL_ENTRY_CREATION_ERROR': 'Error de validación en asiento contable',
            'BALANCE_ERROR': 'Error de balance en asiento contable',
            'VALIDATION_ERROR': 'Error de validación de datos',
            'PARENT_ACCOUNT_NOT_FOUND': 'Cuenta padre no encontrada',
            'INVALID_ACCOUNT_TYPE': 'Tipo de cuenta inválido',
            'INVALID_CATEGORY': 'Categoría de cuenta inválida',
            'INVALID_DATE_FORMAT': 'Formato de fecha inválido',
            'INVALID_AMOUNT': 'Monto inválido',
        }
        return error_descriptions.get(error_code, error_code)


class ImportResult(BaseModel):
    """Resultado completo de importación"""
    import_id: str = Field(..., description="ID único de la importación")
    configuration: ImportConfiguration
    summary: ImportSummary
    row_results: List[ImportRowResult]
    global_errors: List[ImportError] = []  # Errores que afectan toda la importación
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # 'pending', 'processing', 'completed', 'failed', 'cancelled'
    
    model_config = ConfigDict(from_attributes=True)


# Schemas para request/response de API
class ImportRequest(BaseModel):
    """Request para iniciar importación"""
    file_content: str = Field(..., description="Contenido del archivo (base64 para binarios)")
    filename: str = Field(..., description="Nombre del archivo")
    configuration: ImportConfiguration


class ImportPreviewRequest(BaseModel):
    """Request para preview de importación"""
    file_content: str = Field(..., description="Contenido del archivo")
    filename: str = Field(..., description="Nombre del archivo")
    configuration: ImportConfiguration
    preview_rows: int = Field(10, ge=1, le=100, description="Número de filas para preview")


class ImportPreviewResponse(BaseModel):
    """Response de preview de importación"""
    detected_format: ImportFormat
    detected_data_type: ImportDataType
    total_rows: int
    preview_data: List[Dict[str, Any]]
    column_mapping: Dict[str, str]
    validation_errors: List[ImportError]
    recommendations: List[str]


class ImportStatusResponse(BaseModel):
    """Response de estado de importación"""
    import_id: str
    status: str
    progress_percentage: float
    current_row: Optional[int] = None
    estimated_completion: Optional[datetime] = None
    summary: Optional[ImportSummary] = None


# Schemas para templates de importación
class ImportTemplate(BaseModel):
    """Template de importación"""
    data_type: ImportDataType
    format: ImportFormat
    required_columns: List[str]
    optional_columns: List[str]
    column_descriptions: Dict[str, str]
    sample_data: List[Dict[str, Any]]
    validation_rules: List[str]


class ImportTemplateResponse(BaseModel):
    """Response con templates disponibles"""
    templates: List[ImportTemplate]
    supported_formats: List[ImportFormat]
    supported_data_types: List[ImportDataType]
