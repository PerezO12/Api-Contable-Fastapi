# API de Importación de Datos

Este documento describe los endpoints disponibles para la importación de datos en el sistema API Contable.

## Endpoints Principales

### Previsualizar Datos de Importación

```http
POST /api/v1/import/preview
```

Permite previsualizar y validar los datos de importación sin realizar la importación.

**Parámetros del Cuerpo (JSON):**
```json
{
  "file_content": "string (base64)",
  "filename": "string",
  "configuration": {
    "data_type": "accounts | journal_entries",
    "format": "csv | xlsx | json",
    "validation_level": "strict | tolerant | preview",
    "batch_size": 100,
    "skip_duplicates": true,
    "update_existing": false,
    "continue_on_error": false,
    "csv_delimiter": ",",
    "csv_encoding": "utf-8",
    "xlsx_sheet_name": null,
    "xlsx_header_row": 1
  },
  "preview_rows": 10
}
```

**Respuesta:**
```json
{
  "detected_format": "csv | xlsx | json",
  "detected_data_type": "accounts | journal_entries",
  "total_rows": 0,
  "preview_data": [],
  "column_mapping": {},
  "validation_errors": [],
  "recommendations": []
}
```

### Cargar y Previsualizar Archivo

```http
POST /api/v1/import/upload-file
```

Permite cargar un archivo y obtener una previsualización para configurar la importación.

**Parámetros del Formulario:**
- `file`: Archivo a importar (multipart/form-data)
- `data_type`: Tipo de datos a importar (`accounts` o `journal_entries`)
- `validation_level`: Nivel de validación (`strict`, `tolerant`, `preview`)
- `batch_size`: Tamaño del lote para procesamiento (1-1000)
- `preview_rows`: Número de filas a previsualizar (1-100)

**Respuesta:** Igual que en `/preview`

### Importar Datos

```http
POST /api/v1/import/import
```

Importa datos con validación y procesamiento completo.

**Parámetros del Cuerpo (JSON):**
```json
{
  "file_content": "string (base64)",
  "filename": "string",
  "configuration": {
    "data_type": "accounts | journal_entries",
    "format": "csv | xlsx | json",
    "validation_level": "strict | tolerant",
    "batch_size": 100,
    "skip_duplicates": true,
    "update_existing": false,
    "continue_on_error": false,
    "csv_delimiter": ",",
    "csv_encoding": "utf-8",
    "xlsx_sheet_name": null,
    "xlsx_header_row": 1
  }
}
```

**Respuesta:**
```json
{
  "import_id": "string",
  "configuration": {},
  "summary": {
    "total_rows": 0,
    "processed_rows": 0,
    "successful_rows": 0,
    "error_rows": 0,
    "warning_rows": 0,
    "skipped_rows": 0,
    "processing_time_seconds": 0,
    "accounts_created": 0,
    "accounts_updated": 0,
    "journal_entries_created": 0,
    "most_common_errors": {}
  },
  "row_results": [],
  "global_errors": [],
  "started_at": "2023-01-01T00:00:00Z",
  "completed_at": "2023-01-01T00:00:00Z",
  "status": "processing | completed | failed | cancelled"
}
```

### Importar desde Archivo

```http
POST /api/v1/import/import-file
```

Importación directa desde el archivo cargado con configuración automática.

**Parámetros del Formulario:**
- `file`: Archivo a importar (multipart/form-data)
- `data_type`: Tipo de datos a importar (`accounts` o `journal_entries`)
- `validation_level`: Nivel de validación (`strict`, `tolerant`)
- `batch_size`: Tamaño del lote para procesamiento (1-1000)
- `skip_duplicates`: Omitir registros duplicados (boolean)
- `update_existing`: Actualizar registros existentes (boolean)
- `continue_on_error`: Continuar procesando en caso de errores (boolean)

**Respuesta:** Igual que en `/import`

## Endpoints para Plantillas

### Obtener Plantillas de Importación Disponibles (Ruta anterior)

```http
GET /api/v1/import/templates
```

Obtiene las plantillas de importación disponibles con sus formatos y columnas (ruta mantenida por compatibilidad).

**Respuesta:**
```json
{
  "templates": [
    {
      "data_type": "accounts",
      "format": "csv",
      "required_columns": ["code", "name", "account_type"],
      "optional_columns": ["category", "parent_code", "description"],
      "column_descriptions": {},
      "sample_data": [],
      "validation_rules": []
    }
  ],
  "supported_formats": ["csv", "xlsx", "json"],
  "supported_data_types": ["accounts", "journal_entries"]
}
```

> **Nota**: Se recomienda usar el nuevo endpoint `/api/v1/templates/` para obtener información más detallada sobre las plantillas disponibles.

### Descargar Plantilla de Importación (Ruta anterior)

```http
GET /api/v1/import/templates/{data_type}/download
```

Descarga una plantilla para el tipo de datos especificado (ruta mantenida por compatibilidad).

**Parámetros de Ruta:**
- `data_type`: Tipo de datos (`accounts` o `journal_entries`)

**Parámetros de Consulta:**
- `format`: Formato de la plantilla (`csv`, `xlsx`, `json`)

**Respuesta:** Archivo de plantilla en el formato solicitado

### Exportar Plantilla de Cuentas

```http
GET /api/v1/templates/accounts/{format}
```

Descarga una plantilla específica para cuentas contables.

**Parámetros de Ruta:**
- `format`: Formato de la plantilla (`csv`, `xlsx`, `json`)

**Respuesta:** Archivo de plantilla de cuentas en el formato solicitado

### Exportar Plantilla de Asientos Contables

```http
GET /api/v1/templates/journal-entries/{format}
```

Descarga una plantilla específica para asientos contables.

**Parámetros de Ruta:**
- `format`: Formato de la plantilla (`csv`, `xlsx`, `json`)

**Respuesta:** Archivo de plantilla de asientos contables en el formato solicitado

### Listar Plantillas Disponibles

```http
GET /api/v1/templates/
```

Obtiene información sobre todas las plantillas disponibles, sus formatos y contenido.

**Respuesta:** Objeto JSON con descripciones detalladas de las plantillas disponibles

## Endpoints para Operaciones Avanzadas

### Validar Estructura de Datos

```http
POST /api/v1/import/validate-data
```

Valida la estructura de datos sin importar.

**Parámetros de Consulta:**
- `data_type`: Tipo de datos a validar (`accounts` o `journal_entries`)

**Parámetros del Cuerpo (JSON):**
```json
{
  "data": []
}
```

**Respuesta:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "suggestions": []
}
```

### Obtener Formatos Soportados

```http
GET /api/v1/import/formats
```

Obtiene la lista de formatos y tipos de datos soportados.

**Respuesta:**
```json
{
  "formats": ["csv", "xlsx", "json"],
  "data_types": ["accounts", "journal_entries"],
  "validation_levels": ["strict", "tolerant", "preview"]
}
```

### Verificar Estado de Importación

```http
GET /api/v1/import/status/{import_id}
```

Obtiene el estado y progreso de una importación en curso.

**Parámetros de Ruta:**
- `import_id`: ID de la importación

**Respuesta:**
```json
{
  "import_id": "string",
  "status": "string",
  "progress_percentage": 0,
  "current_row": null,
  "estimated_completion": null,
  "summary": null
}
```

### Historial de Importaciones

```http
GET /api/v1/import/history
```

Obtiene el historial de importaciones realizadas.

**Parámetros de Consulta:**
- `skip`: Registros a omitir (paginación)
- `limit`: Registros a retornar (paginación)
- `data_type`: Filtrar por tipo de datos
- `status`: Filtrar por estado

**Respuesta:**
```json
{
  "imports": [],
  "total": 0,
  "skip": 0,
  "limit": 50
}
```

### Cancelar Importación

```http
DELETE /api/v1/import/cancel/{import_id}
```

Cancela una operación de importación en curso.

**Parámetros de Ruta:**
- `import_id`: ID de la importación a cancelar

**Respuesta:**
```json
{
  "message": "Import operation cancelled successfully"
}
```

## Permisos y Seguridad

- Para importar cuentas, el usuario debe tener el permiso `can_modify_accounts`
- Para importar asientos, el usuario debe tener el permiso `can_create_entries`
- Todas las operaciones requieren autenticación con token válido
- Los archivos tienen un límite máximo de 10MB
