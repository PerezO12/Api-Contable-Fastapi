# Estructuras de Datos para Importación

Este documento describe las estructuras de datos y esquemas utilizados en el sistema de importación de API Contable.

## Enumeraciones

### ImportFormat

Define los formatos de archivo soportados para importación:

```python
class ImportFormat(str, Enum):
    """Formatos de importación soportados"""
    CSV = "csv"
    XLSX = "xlsx" 
    JSON = "json"
```

### ImportDataType

Define los tipos de datos que pueden ser importados:

```python
class ImportDataType(str, Enum):
    """Tipos de datos a importar"""
    ACCOUNTS = "accounts"
    JOURNAL_ENTRIES = "journal_entries"
    MIXED = "mixed"  # Cuentas y asientos juntos
```

### ImportValidationLevel

Define los niveles de validación disponibles:

```python
class ImportValidationLevel(str, Enum):
    """Niveles de validación"""
    STRICT = "strict"      # Fallar si hay cualquier error
    TOLERANT = "tolerant"  # Procesar lo que se pueda, reportar errores
    PREVIEW = "preview"    # Solo validar, no importar
```

## Esquemas de Datos para Cuentas

### AccountImportRow

Representa una fila de importación para una cuenta contable:

```python
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
    row_number: Optional[int] = Field(None, description="Número de fila en el archivo")
```

## Esquemas de Datos para Asientos Contables

### JournalEntryLineImportRow

Representa una línea de asiento contable en la importación:

```python
class JournalEntryLineImportRow(BaseModel):
    """Schema para una línea de asiento en importación"""
    account_code: str = Field(..., description="Código de la cuenta")
    description: str = Field(..., min_length=1, max_length=500, description="Descripción del movimiento")
    debit_amount: Optional[Decimal] = Field(None, ge=0, description="Monto débito")
    credit_amount: Optional[Decimal] = Field(None, ge=0, description="Monto crédito")
    third_party: Optional[str] = Field(None, max_length=100, description="Tercero")
    cost_center: Optional[str] = Field(None, max_length=50, description="Centro de costo")
    reference: Optional[str] = Field(None, max_length=100, description="Referencia")
```

### JournalEntryImportRow

Representa un asiento contable completo en la importación:

```python
class JournalEntryImportRow(BaseModel):
    """Schema para un asiento en importación"""
    entry_date: date = Field(..., description="Fecha del asiento")
    reference: Optional[str] = Field(None, max_length=100, description="Referencia")
    description: str = Field(..., min_length=1, max_length=1000, description="Descripción del asiento")
    entry_type: str = Field("MANUAL", description="Tipo de asiento")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas")
    lines: List[JournalEntryLineImportRow] = Field(..., min_length=2, description="Líneas del asiento")
    row_number: Optional[int] = Field(None, description="Número de fila en el archivo")
```

## Esquemas de Configuración

### ImportConfiguration

Configuración para personalizar el proceso de importación:

```python
class ImportConfiguration(BaseModel):
    """Configuración de importación"""
    data_type: ImportDataType = Field(..., description="Tipo de datos a importar")
    format: ImportFormat = Field(..., description="Formato del archivo")
    validation_level: ImportValidationLevel = Field(ImportValidationLevel.STRICT, description="Nivel de validación")
    batch_size: int = Field(100, ge=1, le=1000, description="Tamaño del lote para procesamiento")
    skip_duplicates: bool = Field(True, description="Omitir registros duplicados")
    update_existing: bool = Field(False, description="Actualizar registros existentes")
    continue_on_error: bool = Field(False, description="Continuar procesamiento en caso de errores")
    csv_delimiter: str = Field(',', description="Delimitador para CSV")
    csv_encoding: str = Field('utf-8', description="Codificación para CSV")
    xlsx_sheet_name: Optional[str] = Field(None, description="Nombre de la hoja de Excel")
    xlsx_header_row: int = Field(1, ge=1, description="Número de fila con encabezados")
```

## Esquemas de Resultado y Error

### ImportError

Representa un error durante el proceso de importación:

```python
class ImportError(BaseModel):
    """Error de importación"""
    row_number: Optional[int] = None
    field_name: Optional[str] = None
    error_code: str
    error_message: str
    error_type: str  # 'validation', 'business', 'system'
    severity: str = 'error'  # 'error', 'warning', 'info'
```

### ImportRowResult

Resultado de la importación para una fila específica:

```python
class ImportRowResult(BaseModel):
    """Resultado de importación por fila"""
    row_number: int
    status: str  # 'success', 'error', 'warning', 'skipped'
    entity_id: Optional[uuid.UUID] = None
    entity_code: Optional[str] = None
    errors: List[ImportError] = []
    warnings: List[ImportError] = []
```

### ImportSummary

Resumen con estadísticas del proceso de importación:

```python
class ImportSummary(BaseModel):
    """Resumen de importación"""
    total_rows: int
    processed_rows: int
    successful_rows: int
    error_rows: int
    warning_rows: int
    skipped_rows: int
    processing_time_seconds: float
    accounts_created: int = 0
    accounts_updated: int = 0
    journal_entries_created: int = 0
    most_common_errors: Dict[str, int] = {}
```

### ImportResult

Resultado completo de una operación de importación:

```python
class ImportResult(BaseModel):
    """Resultado completo de importación"""
    import_id: str = Field(..., description="ID único de la importación")
    configuration: ImportConfiguration
    summary: ImportSummary
    row_results: List[ImportRowResult]
    global_errors: List[ImportError] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # 'pending', 'processing', 'completed', 'failed', 'cancelled'
```

## Esquemas para Requests y Responses

### ImportRequest

Request para iniciar un proceso de importación:

```python
class ImportRequest(BaseModel):
    """Request para iniciar importación"""
    file_content: str = Field(..., description="Contenido del archivo (base64 para binarios)")
    filename: str = Field(..., description="Nombre del archivo")
    configuration: ImportConfiguration
```

### ImportPreviewRequest

Request para previsualizar datos antes de importar:

```python
class ImportPreviewRequest(BaseModel):
    """Request para preview de importación"""
    file_content: str = Field(..., description="Contenido del archivo")
    filename: str = Field(..., description="Nombre del archivo")
    configuration: ImportConfiguration
    preview_rows: int = Field(10, ge=1, le=100, description="Número de filas para preview")
```

### ImportPreviewResponse

Response con previsualización de datos para importar:

```python
class ImportPreviewResponse(BaseModel):
    """Response de preview de importación"""
    detected_format: ImportFormat
    detected_data_type: ImportDataType
    total_rows: int
    preview_data: List[Dict[str, Any]]
    column_mapping: Dict[str, str]
    validation_errors: List[ImportError]
    recommendations: List[str]
```

### ImportStatusResponse

Response con el estado actual de una importación en curso:

```python
class ImportStatusResponse(BaseModel):
    """Response de estado de importación"""
    import_id: str
    status: str
    progress_percentage: float
    current_row: Optional[int] = None
    estimated_completion: Optional[datetime] = None
    summary: Optional[ImportSummary] = None
```

## Plantillas de Importación

### ImportTemplate

Definición de una plantilla de importación:

```python
class ImportTemplate(BaseModel):
    """Template de importación"""
    data_type: ImportDataType
    format: ImportFormat
    required_columns: List[str]
    optional_columns: List[str]
    column_descriptions: Dict[str, str]
    sample_data: List[Dict[str, Any]]
    validation_rules: List[str]
```

### ImportTemplateResponse

Response con plantillas disponibles:

```python
class ImportTemplateResponse(BaseModel):
    """Response con templates disponibles"""
    templates: List[ImportTemplate]
    supported_formats: List[ImportFormat]
    supported_data_types: List[ImportDataType]
```

## Validaciones Principales

Las estructuras de datos incluyen validaciones intrínsecas para garantizar la calidad de los datos importados:

### Para Cuentas:

1. Códigos de cuenta únicos y válidos
2. Tipos de cuenta dentro de los valores permitidos (ACTIVO, PASIVO, etc.)
3. Validación de cuentas padre existentes
4. Categorías correspondientes al tipo de cuenta

### Para Asientos Contables:

1. Cada asiento debe tener al menos 2 líneas
2. El asiento debe estar balanceado (débitos = créditos)
3. Cada línea debe tener monto en débito O crédito, no ambos o ninguno
4. Las cuentas referenciadas deben existir en el sistema
5. Validación de tipos de asiento
