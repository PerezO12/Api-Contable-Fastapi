# Esquemas de Datos de Exportación

## Descripción General

Los esquemas de datos del sistema de exportación proporcionan validación robusta y estructuras de datos bien definidas para todas las operaciones de exportación. Están implementados usando Pydantic para validación automática y generación de documentación.

## Archivo de Esquemas
```
app/schemas/export_generic.py
```

## Enumeraciones Base

### TableName
Enumera todas las tablas disponibles para exportación.

```python
class TableName(str, Enum):
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
```

**Uso:**
```python
# Validación automática
table = TableName.USERS  # ✅ Válido
table = TableName("users")  # ✅ Válido
table = "invalid_table"  # ❌ Error de validación
```

### ExportFormat
Define los formatos de exportación soportados.

```python
class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
```

**Características:**
- **CSV**: Separado por comas, compatible con Excel
- **JSON**: Formato estructurado para APIs
- **XLSX**: Formato nativo de Excel con formateado

## Esquemas de Información

### ColumnInfo
Información detallada de una columna de tabla.

```python
class ColumnInfo(BaseModel):
    name: str                    # Nombre de la columna
    data_type: str              # Tipo de dato (string, number, boolean, date)
    format: Optional[str] = None # Formato específico (opcional)
    include: bool = True         # Si incluir en exportación
```

**Ejemplo:**
```json
{
  "name": "created_at",
  "data_type": "date",
  "format": "ISO8601",
  "include": true
}
```

### TableSchema
Esquema completo de una tabla con metadatos.

```python
class TableSchema(BaseModel):
    table_name: str                           # Nombre técnico de la tabla
    display_name: str                         # Nombre amigable para mostrar
    description: str                          # Descripción de la tabla
    available_columns: List[ColumnInfo]       # Columnas disponibles
    total_records: int                        # Total de registros en la tabla
    sample_data: Optional[List[Dict[str, Any]]] = None  # Datos de muestra
```

**Ejemplo:**
```json
{
  "table_name": "users",
  "display_name": "Usuarios",
  "description": "Tabla de usuarios del sistema",
  "available_columns": [
    {
      "name": "id",
      "data_type": "number",
      "include": true
    },
    {
      "name": "email",
      "data_type": "string",
      "include": true
    }
  ],
  "total_records": 150,
  "sample_data": [
    {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John"
    }
  ]
}
```

### AvailableTablesResponse
Respuesta con todas las tablas disponibles.

```python
class AvailableTablesResponse(BaseModel):
    tables: List[TableSchema]    # Lista de esquemas de tablas
    total_tables: int           # Número total de tablas disponibles
```

## Esquemas de Filtrado

### ExportFilter
Filtros avanzados para la exportación de datos.

```python
class ExportFilter(BaseModel):
    ids: Optional[List[int]] = None                    # IDs específicos
    date_from: Optional[datetime] = None               # Fecha de inicio
    date_to: Optional[datetime] = None                 # Fecha de fin
    active_only: Optional[bool] = None                 # Solo registros activos
    custom_filters: Optional[Dict[str, Any]] = None    # Filtros personalizados
    offset: Optional[int] = None                       # Offset para paginación
    limit: Optional[int] = None                        # Límite de registros
```

**Validaciones:**
- `ids`: Lista no vacía si se proporciona
- `date_from/date_to`: Fechas válidas, date_from < date_to
- `offset/limit`: Números enteros positivos
- `custom_filters`: Diccionario con claves string

**Ejemplo:**
```json
{
  "ids": [1, 2, 3, 4, 5],
  "date_from": "2024-01-01T00:00:00",
  "date_to": "2024-12-31T23:59:59",
  "active_only": true,
  "custom_filters": {
    "account_type": "ASSET",
    "status": "ACTIVE"
  },
  "offset": 0,
  "limit": 1000
}
```

## Esquemas de Request

### SimpleExportRequest
Esquema simplificado para exportaciones básicas.

```python
class SimpleExportRequest(BaseModel):
    table: TableName            # Tabla a exportar
    format: ExportFormat        # Formato de exportación
    ids: List[int]             # Lista de IDs a exportar

    @validator('ids')
    def validate_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('La lista de IDs no puede estar vacía')
        if len(v) > 10000:
            raise ValueError('Máximo 10,000 IDs por solicitud')
        return v
```

**Ejemplo:**
```json
{
  "table": "users",
  "format": "csv",
  "ids": [1, 2, 3, 4, 5]
}
```

### ExportRequest
Esquema completo para exportaciones avanzadas.

```python
class ExportRequest(BaseModel):
    table_name: TableName                              # Tabla a exportar
    export_format: ExportFormat                        # Formato de salida
    filters: ExportFilter = Field(default_factory=ExportFilter)  # Filtros
    columns: Optional[List[ColumnInfo]] = None         # Columnas específicas
    file_name: Optional[str] = None                    # Nombre personalizado

    @validator('file_name')
    def validate_filename(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Nombre de archivo inválido')
        return v
```

**Ejemplo:**
```json
{
  "table_name": "journal_entries",
  "export_format": "xlsx",
  "filters": {
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "active_only": true
  },
  "columns": [
    {
      "name": "id",
      "include": true
    },
    {
      "name": "description",
      "include": true
    }
  ],
  "file_name": "asientos_2024"
}
```

## Esquemas de Response

### ExportMetadata
Metadatos detallados de la exportación realizada.

```python
class ExportMetadata(BaseModel):
    export_date: datetime                       # Fecha y hora de exportación
    user_id: UUID                              # ID del usuario que exportó
    table_name: str                            # Nombre de la tabla exportada
    total_records: int                         # Total de registros en la tabla
    exported_records: int                      # Registros incluidos en la exportación
    filters_applied: Dict[str, Any]            # Filtros que se aplicaron
    format: ExportFormat                       # Formato de exportación usado
    file_size_bytes: Optional[int] = None      # Tamaño del archivo generado
    columns_exported: List[str]                # Lista de columnas exportadas
```

### ExportResponse
Respuesta completa de una operación de exportación.

```python
class ExportResponse(BaseModel):
    file_name: str                             # Nombre del archivo generado
    file_content: Union[str, bytes]            # Contenido del archivo
    content_type: str                          # Tipo MIME del archivo
    metadata: ExportMetadata                   # Metadatos de la exportación
    success: bool                              # Indicador de éxito
    message: str                               # Mensaje descriptivo
```

**Ejemplo:**
```json
{
  "file_name": "users_20241210_143022.csv",
  "file_content": "id,email,first_name,last_name\n1,user1@example.com,John,Doe\n...",
  "content_type": "text/csv",
  "metadata": {
    "export_date": "2024-12-10T14:30:22.123456",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "table_name": "users",
    "total_records": 1000,
    "exported_records": 5,
    "filters_applied": {
      "ids": [1, 2, 3, 4, 5]
    },
    "format": "csv",
    "file_size_bytes": 256,
    "columns_exported": ["id", "email", "first_name", "last_name"]
  },
  "success": true,
  "message": "Exportación exitosa: 5 registros"
}
```

## Esquemas de Error

### ExportError
Esquema para errores específicos de exportación.

```python
class ExportError(BaseModel):
    error_code: str                            # Código de error único
    message: str                               # Mensaje de error
    details: Optional[Dict[str, Any]] = None   # Detalles adicionales del error
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Códigos de Error Comunes:**
- `INVALID_TABLE`: Tabla no válida o no existe
- `INVALID_FORMAT`: Formato de exportación no soportado
- `EMPTY_RESULT`: No hay datos para exportar
- `SIZE_LIMIT_EXCEEDED`: Límite de tamaño excedido
- `PERMISSION_DENIED`: Sin permisos para la tabla
- `GENERATION_FAILED`: Error al generar el archivo

**Ejemplo:**
```json
{
  "error_code": "INVALID_TABLE",
  "message": "La tabla 'invalid_table' no existe",
  "details": {
    "valid_tables": ["users", "accounts", "journal_entries"],
    "provided_table": "invalid_table"
  },
  "timestamp": "2024-12-10T14:30:22.123456"
}
```

## Validaciones Implementadas

### Validaciones de Entrada

#### TableName Validation
```python
@validator('table_name')
def validate_table_name(cls, v):
    if v not in [table.value for table in TableName]:
        raise ValueError(f'Tabla inválida: {v}')
    return v
```

#### Format Validation
```python
@validator('export_format')
def validate_format(cls, v):
    if v not in [fmt.value for fmt in ExportFormat]:
        raise ValueError(f'Formato inválido: {v}')
    return v
```

#### IDs Validation
```python
@validator('ids')
def validate_ids(cls, v):
    if not v:
        raise ValueError('Lista de IDs requerida')
    if len(v) > 10000:
        raise ValueError('Máximo 10,000 IDs por solicitud')
    if any(id <= 0 for id in v):
        raise ValueError('IDs deben ser números positivos')
    return v
```

#### Date Range Validation
```python
@validator('date_to')
def validate_date_range(cls, v, values):
    if v and 'date_from' in values and values['date_from']:
        if v < values['date_from']:
            raise ValueError('date_to debe ser posterior a date_from')
    return v
```

#### File Name Validation
```python
@validator('file_name')
def validate_filename(cls, v):
    if v:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Nombre de archivo contiene caracteres inválidos')
        if len(v) > 50:
            raise ValueError('Nombre de archivo muy largo (máximo 50 caracteres)')
    return v
```

### Validaciones de Negocio

#### Column Selection Validation
```python
@validator('columns')
def validate_columns(cls, v):
    if v:
        included_columns = [col for col in v if col.include]
        if not included_columns:
            raise ValueError('Debe incluir al menos una columna')
    return v
```

#### Filter Combination Validation
```python
@validator('filters')
def validate_filters(cls, v):
    if v.limit and v.limit > 100000:
        raise ValueError('Límite máximo: 100,000 registros')
    if v.offset and v.offset < 0:
        raise ValueError('Offset debe ser positivo')
    return v
```

## Configuración de Serialización

### JSON Encoders
```python
class Config:
    json_encoders = {
        datetime: lambda v: v.isoformat(),
        UUID: lambda v: str(v),
        Decimal: lambda v: float(v)
    }
    
    # Permitir tipos arbitrarios para flexibilidad
    arbitrary_types_allowed = True
    
    # Validar asignaciones
    validate_assignment = True
    
    # Usar enum values en JSON
    use_enum_values = True
```

### Alias de Campos
```python
class ExportRequest(BaseModel):
    table_name: TableName = Field(alias='table')
    export_format: ExportFormat = Field(alias='format')
    
    class Config:
        allow_population_by_field_name = True
```

## Ejemplos de Uso

### Creación de Request Simple
```python
from app.schemas.export_generic import SimpleExportRequest, TableName, ExportFormat

request = SimpleExportRequest(
    table=TableName.USERS,
    format=ExportFormat.CSV,
    ids=[1, 2, 3, 4, 5]
)
```

### Creación de Request Avanzado
```python
from datetime import datetime
from app.schemas.export_generic import ExportRequest, ExportFilter

request = ExportRequest(
    table_name=TableName.JOURNAL_ENTRIES,
    export_format=ExportFormat.XLSX,
    filters=ExportFilter(
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 12, 31),
        active_only=True,
        limit=5000
    ),
    file_name="asientos_2024"
)
```

### Validación de Datos
```python
try:
    request = SimpleExportRequest(
        table="invalid_table",  # ❌ Error
        format="pdf",           # ❌ Error
        ids=[]                  # ❌ Error
    )
except ValidationError as e:
    print(f"Errores de validación: {e.errors()}")
```

### Procesamiento de Response
```python
response = ExportResponse(
    file_name="export.csv",
    file_content="id,name\n1,John\n2,Jane",
    content_type="text/csv",
    metadata=ExportMetadata(
        export_date=datetime.utcnow(),
        user_id=UUID('123e4567-e89b-12d3-a456-426614174000'),
        table_name="users",
        total_records=100,
        exported_records=2,
        filters_applied={"ids": [1, 2]},
        format=ExportFormat.CSV,
        columns_exported=["id", "name"]
    ),
    success=True,
    message="Exportación exitosa"
)

# Serializar a JSON
json_data = response.json()

# Serializar a diccionario
dict_data = response.dict()
```

## Integración con FastAPI

### Dependencias Automáticas
```python
from fastapi import Depends
from app.schemas.export_generic import SimpleExportRequest

@router.post("/export/")
async def export_data(
    request: SimpleExportRequest,  # Validación automática
    current_user: User = Depends(get_current_user)
):
    # request ya está validado
    return export_service.export_data(request, current_user.id)
```

### Documentación Automática
Los esquemas Pydantic generan automáticamente:
- Documentación OpenAPI/Swagger
- Ejemplos de request/response
- Validaciones en la UI
- Tipos TypeScript (si se usa codegen)

### Serialización Automática
```python
# FastAPI serializa automáticamente el response
@router.post("/export/", response_model=ExportResponse)
async def export_data(request: SimpleExportRequest):
    result = export_service.export_data(request, user_id)
    return result  # Serialización automática a JSON
```
