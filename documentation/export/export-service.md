# Servicio de Exportación - Documentación Técnica

## Descripción General

El `ExportService` es el componente central del sistema de exportación que proporciona capacidades robustas y seguras para exportar datos de cualquier tabla del sistema contable en múltiples formatos, con filtrado automático de información sensible.

## Características Principales

### 🔄 Exportación Genérica
- **Soporte universal**: Compatible con todas las tablas del sistema
- **Múltiples formatos**: CSV, JSON, XLSX
- **Filtrado flexible**: Por IDs, fechas, estado y filtros personalizados
- **Metadatos completos**: Información detallada de cada exportación

### 🔒 Seguridad Integrada
- **Filtrado automático**: Omisión de campos sensibles como contraseñas y tokens
- **Control granular**: Configuración específica por tabla
- **Validación de datos**: Verificación de integridad antes de exportar

### ⚡ Rendimiento Optimizado
- **Consultas eficientes**: Uso de SQLAlchemy para optimización
- **Procesamiento en memoria**: Generación de archivos sin almacenamiento temporal
- **Paginación**: Soporte para grandes volúmenes de datos

## Arquitectura del Servicio

```python
class ExportService:
    """Servicio para exportación genérica de datos de la base de datos"""
    
    # Configuración estática
    TABLE_MODEL_MAPPING     # Mapeo tabla → modelo SQLAlchemy
    TABLE_DISPLAY_NAMES     # Nombres amigables para tablas
    SENSITIVE_FIELDS        # Campos sensibles por tabla
    
    # Métodos principales
    get_available_tables()  # Lista tablas disponibles
    get_table_schema()      # Esquema de tabla específica
    export_data()           # Exportación principal
    
    # Métodos auxiliares
    _get_table_columns()    # Columnas de tabla
    _build_query()          # Construcción de consultas
    _model_to_dict()        # Conversión modelo → diccionario
    _filter_sensitive_columns()  # Filtrado de seguridad
    _generate_file()        # Generación de archivos
```

## Configuraciones del Servicio

### Mapeo de Tablas a Modelos

```python
TABLE_MODEL_MAPPING = {
    TableName.USERS: User,
    TableName.ACCOUNTS: Account,
    TableName.JOURNAL_ENTRIES: JournalEntry,
    TableName.JOURNAL_ENTRY_LINES: JournalEntryLine,
    TableName.AUDIT_LOGS: AuditLog,
    TableName.USER_SESSIONS: UserSession,
    TableName.CHANGE_TRACKING: ChangeTracking,
    TableName.SYSTEM_CONFIGURATION: SystemConfiguration,
    TableName.COMPANY_INFO: CompanyInfo,
    TableName.NUMBER_SEQUENCES: NumberSequence,
}
```

### Campos Sensibles por Tabla

```python
SENSITIVE_FIELDS = {
    TableName.USERS: [
        'hashed_password', 'password_hash', 'password',
        'salt', 'secret_key', 'private_key', 'api_key', 'token'
    ],
    TableName.USER_SESSIONS: [
        'session_token', 'refresh_token', 'access_token'
    ],
    TableName.SYSTEM_CONFIGURATION: [
        'secret_value', 'password', 'api_secret', 'private_key'
    ]
}
```

### Nombres de Visualización

```python
TABLE_DISPLAY_NAMES = {
    TableName.USERS: "Usuarios",
    TableName.ACCOUNTS: "Plan de Cuentas",
    TableName.JOURNAL_ENTRIES: "Asientos Contables",
    # ... más tablas
}
```

## Métodos Principales

### `get_available_tables() -> AvailableTablesResponse`

Obtiene información de todas las tablas disponibles para exportación.

**Funcionalidad:**
- Lista todas las tablas configuradas
- Obtiene metadatos de cada tabla (columnas, registros totales)
- Filtra campos sensibles en la información de esquema
- Maneja errores graciosamente

**Retorna:**
```python
AvailableTablesResponse(
    tables=[
        TableSchema(
            table_name="users",
            display_name="Usuarios",
            description="Tabla Usuarios",
            available_columns=[...],
            total_records=150
        )
    ],
    total_tables=10
)
```

### `get_table_schema(table_name: TableName) -> TableSchema`

Obtiene el esquema detallado de una tabla específica.

**Parámetros:**
- `table_name`: Nombre de la tabla (enum TableName)

**Funcionalidad:**
- Inspecciona la estructura de la tabla
- Filtra campos sensibles
- Incluye datos de muestra (5 registros)
- Proporciona metadatos completos

**Retorna:**
```python
TableSchema(
    table_name="users",
    display_name="Usuarios",
    description="Tabla Usuarios",
    available_columns=[
        ColumnInfo(name="id", data_type="number", include=True),
        ColumnInfo(name="email", data_type="string", include=True),
        # hashed_password omitido por seguridad
    ],
    total_records=150,
    sample_data=[{...}, {...}]  # Sin campos sensibles
)
```

### `export_data(request: ExportRequest, user_id: UUID) -> ExportResponse`

Método principal para exportar datos según parámetros especificados.

**Parámetros:**
- `request`: Especificación de la exportación (tabla, formato, filtros)
- `user_id`: ID del usuario que realiza la exportación

**Proceso:**
1. **Validación**: Verifica parámetros de entrada
2. **Consulta**: Construye query con filtros aplicados
3. **Obtención**: Ejecuta consulta y obtiene datos
4. **Transformación**: Convierte modelos a diccionarios con filtrado de seguridad
5. **Generación**: Crea archivo en formato especificado
6. **Metadatos**: Genera información de la exportación
7. **Respuesta**: Retorna archivo y metadatos

**Ejemplo de uso:**
```python
request = ExportRequest(
    table_name=TableName.USERS,
    export_format=ExportFormat.CSV,
    filters=ExportFilter(
        ids=[1, 2, 3],
        active_only=True
    )
)

response = service.export_data(request, user_id)
```

**Retorna:**
```python
ExportResponse(
    file_name="users_20241210_143022.csv",
    file_content="id,email,first_name,last_name\n...",
    content_type="text/csv",
    metadata=ExportMetadata(
        export_date=datetime.utcnow(),
        user_id=user_id,
        table_name="users",
        total_records=150,
        exported_records=3,
        filters_applied={...},
        format=ExportFormat.CSV,
        file_size_bytes=1024,
        columns_exported=["id", "email", "first_name", "last_name"]
    ),
    success=True,
    message="Exportación exitosa: 3 registros"
)
```

## Métodos de Filtrado y Seguridad

### `_filter_sensitive_columns(columns, table_name) -> List[ColumnInfo]`

Filtra automáticamente columnas sensibles según la configuración de la tabla.

**Funcionalidad:**
- Consulta configuración SENSITIVE_FIELDS para la tabla
- Excluye campos sensibles de la lista de columnas
- Registra campos omitidos para auditoría
- Retorna lista filtrada de columnas seguras

### `_model_to_dict(model_instance, selected_columns, table_name) -> Dict`

Convierte instancia de modelo SQLAlchemy a diccionario con filtrado de seguridad.

**Funcionalidad:**
- Maneja conversión de tipos especiales (Decimal, DateTime, UUID)
- Aplica filtrado de campos sensibles automáticamente
- Gestiona relaciones y campos nulos
- Optimiza serialización para exportación

## Métodos de Generación de Archivos

### `_generate_json(data) -> str`
Genera archivo JSON con codificación UTF-8 y formato legible.

### `_generate_csv(data) -> str`
Genera archivo CSV con encabezados y separadores estándar.

### `_generate_xlsx(data) -> bytes`
Genera archivo Excel usando pandas y openpyxl con formato profesional.

## Construcción de Consultas

### `_build_query(model, filters) -> Query`

Construye consultas SQLAlchemy optimizadas con filtros aplicados.

**Filtros soportados:**
- **IDs específicos**: `WHERE id IN (1,2,3)`
- **Rango de fechas**: `WHERE created_at BETWEEN date1 AND date2`
- **Estado activo**: `WHERE is_active = true/false`
- **Filtros personalizados**: Campos específicos con valores
- **Paginación**: OFFSET y LIMIT para grandes datasets

**Optimizaciones:**
- Uso de índices para filtros de ID
- Filtros de fecha optimizados
- Validación de existencia de campos antes de aplicar filtros

## Manejo de Errores

El servicio implementa manejo robusto de errores:

```python
try:
    # Operación de exportación
    result = export_operation()
except SQLAlchemyError as e:
    # Error de base de datos
    raise ExportError(f"Error de base de datos: {str(e)}")
except ValidationError as e:
    # Error de validación
    raise ExportError(f"Datos inválidos: {str(e)}")
except Exception as e:
    # Error general
    raise ExportError(f"Error en la exportación: {str(e)}")
```

## Consideraciones de Rendimiento

### Optimizaciones Implementadas
- **Consultas lazy**: Solo carga datos necesarios
- **Filtros a nivel de base de datos**: Reduce transferencia de datos
- **Generación en memoria**: Evita I/O de archivos temporales
- **Conversión eficiente**: Minimiza transformaciones de datos

### Límites Recomendados
- **CSV/JSON**: Hasta 100,000 registros
- **XLSX**: Hasta 50,000 registros (limitación de Excel)
- **Memoria**: Monitoreo de uso para datasets grandes

## Seguridad y Auditoría

### Medidas de Seguridad
- **Filtrado automático**: Campos sensibles nunca se exportan
- **Validación de entrada**: Todos los parámetros son validados
- **Control de acceso**: Integración con sistema de autenticación
- **Logs de auditoría**: Registro de todas las exportaciones

### Campos Protegidos
- Contraseñas y hashes
- Tokens de sesión y API
- Claves privadas y secretos
- Información de configuración sensible

## Integración con el Sistema

### Dependencias
```python
from sqlalchemy.orm import Session
from app.schemas.export_generic import *
from app.models import *
```

### Inicialización
```python
# En endpoints o servicios
def get_export_service(db: Session = Depends(get_sync_db)):
    return ExportService(db)
```

### Uso en Endpoints
```python
@router.post("/export/", response_model=ExportResponse)
async def export_data(
    request: SimpleExportRequest,
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
):
    return export_service.export_data(request, current_user.id)
```

## Ejemplos de Uso

### Exportación Simple de Usuarios
```python
service = ExportService(db)
request = ExportRequest(
    table_name=TableName.USERS,
    export_format=ExportFormat.CSV,
    filters=ExportFilter(ids=[1, 2, 3])
)
result = service.export_data(request, user_id)
```

### Exportación de Asientos con Filtros
```python
request = ExportRequest(
    table_name=TableName.JOURNAL_ENTRIES,
    export_format=ExportFormat.XLSX,
    filters=ExportFilter(
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 12, 31),
        active_only=True
    )
)
result = service.export_data(request, user_id)
```

### Consulta de Esquema de Tabla
```python
schema = service.get_table_schema(TableName.ACCOUNTS)
print(f"Tabla: {schema.display_name}")
print(f"Columnas disponibles: {len(schema.available_columns)}")
print(f"Total de registros: {schema.total_records}")
```

## Pruebas y Validación

### Casos de Prueba Recomendados
1. **Exportación básica**: Verificar generación correcta de archivos
2. **Filtrado de seguridad**: Confirmar omisión de campos sensibles
3. **Filtros complejos**: Validar aplicación correcta de filtros
4. **Formatos múltiples**: Probar todos los formatos soportados
5. **Manejo de errores**: Verificar respuesta a datos inválidos
6. **Rendimiento**: Medir tiempos con datasets grandes

### Métricas de Calidad
- **Cobertura de código**: >90%
- **Tiempo de respuesta**: <5 segundos para 10,000 registros
- **Memoria**: <500MB para exports grandes
- **Seguridad**: 0 campos sensibles en exports
