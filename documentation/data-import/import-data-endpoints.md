# API de Importación de Datos - Documentación Actualizada

## Descripción General

La API de importación de datos proporciona funcionalidades empresariales para importar datos contables desde archivos CSV, XLSX y JSON con validaciones robustas, procesamiento por lotes y manejo de errores avanzado.

### Características Principales

- **Múltiples formatos**: CSV, XLSX, JSON
- **Validación previa** con vista previa de datos
- **Procesamiento por lotes** configurable
- **Detección automática** de formato y estructura
- **Templates predefinidos** para cada tipo de datos
- **Validaciones empresariales** robustas
- **Manejo de duplicados** y actualizaciones
- **Continuidad en errores** opcional

## Autenticación

Todos los endpoints requieren autenticación Bearer Token:

```
Authorization: Bearer <jwt_token>
```

## Permisos Requeridos

- **can_modify_accounts**: Para importar cuentas contables
- **can_create_entries**: Para importar asientos contables
- **can_modify_third_parties**: Para importar terceros

## Tipos de Datos Soportados

| Tipo | Descripción | Permisos Requeridos |
|------|-------------|-------------------|
| `ACCOUNTS` | Cuentas contables | can_modify_accounts |
| `JOURNAL_ENTRIES` | Asientos contables | can_create_entries |
| `THIRD_PARTIES` | Terceros | can_modify_third_parties |
| `COST_CENTERS` | Centros de costo | can_modify_accounts |

## Formatos de Archivo Soportados

| Formato | Extensión | Descripción | Límite de Tamaño |
|---------|-----------|-------------|------------------|
| `CSV` | .csv | Valores separados por comas | 10MB |
| `XLSX` | .xlsx, .xls | Hojas de cálculo Excel | 10MB |
| `JSON` | .json | Formato JSON estructurado | 10MB |

## Niveles de Validación

| Nivel | Descripción |
|-------|-------------|
| `STRICT` | Validación estricta, falla en cualquier error |
| `MODERATE` | Permite algunos errores menores |
| `LENIENT` | Validación flexible, continúa con warnings |

## Endpoints

### 1. Vista Previa de Importación

**POST** `/import-data/preview`

Analiza un archivo y muestra una vista previa sin importar los datos.

**Request Body:**
```json
{
  "file_content": "base64_encoded_file_content",
  "filename": "cuentas.csv",
  "configuration": {
    "data_type": "ACCOUNTS",
    "format": "CSV",
    "validation_level": "STRICT",
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

**Response (200):**
```json
{
  "filename": "cuentas.csv",
  "total_rows": 500,
  "preview_rows": [
    {
      "row_number": 1,
      "data": {
        "code": "1105",
        "name": "Caja General",
        "account_type": "ASSET",
        "parent_code": "11"
      },
      "validation_status": "VALID",
      "errors": [],
      "warnings": []
    },
    {
      "row_number": 2,
      "data": {
        "code": "1110",
        "name": "Bancos",
        "account_type": "ASSET",
        "parent_code": "11"
      },
      "validation_status": "VALID",
      "errors": [],
      "warnings": []
    }
  ],
  "validation_summary": {
    "total_rows": 500,
    "valid_rows": 485,
    "rows_with_errors": 15,
    "rows_with_warnings": 23
  },
  "detected_structure": {
    "columns": ["code", "name", "account_type", "parent_code"],
    "column_mapping": {
      "code": "account_code",
      "name": "account_name",
      "account_type": "type",
      "parent_code": "parent_account_code"
    }
  },
  "errors": [
    {
      "row": 45,
      "column": "code",
      "message": "Código de cuenta duplicado: 1105",
      "severity": "ERROR"
    }
  ],
  "configuration_suggestions": {
    "recommended_batch_size": 50,
    "encoding_detected": "utf-8",
    "delimiter_detected": ","
  }
}
```

### 2. Subir Archivo y Vista Previa

**POST** `/import-data/upload-file`

Sube un archivo y obtiene automáticamente la vista previa con configuración sugerida.

**Form Data:**
- `file`: Archivo a subir (multipart/form-data)

**Query Parameters:**
- `data_type` (ImportDataType): Tipo de datos a importar
- `validation_level` (ImportValidationLevel): Nivel de validación (default: STRICT)
- `batch_size` (int): Tamaño de lote (default: 100, max: 1000)
- `preview_rows` (int): Filas de vista previa (default: 10, max: 100)

**Response (200):** Igual que el endpoint de preview

### 3. Importar Datos

**POST** `/import-data/import`

Ejecuta la importación completa de datos con validación y procesamiento.

**Request Body:**
```json
{
  "file_content": "base64_encoded_file_content",
  "filename": "cuentas.csv",
  "configuration": {
    "data_type": "ACCOUNTS",
    "format": "CSV",
    "validation_level": "STRICT",
    "batch_size": 100,
    "skip_duplicates": true,
    "update_existing": false,
    "continue_on_error": false,
    "csv_delimiter": ",",
    "csv_encoding": "utf-8"
  }
}
```

**Response (200):**
```json
{
  "import_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "filename": "cuentas.csv",
  "data_type": "ACCOUNTS",
  "started_at": "2024-12-01T10:00:00Z",
  "completed_at": "2024-12-01T10:05:30Z",
  "duration_seconds": 330,
  "statistics": {
    "total_rows_processed": 500,
    "successful_imports": 485,
    "failed_imports": 15,
    "duplicates_skipped": 5,
    "records_updated": 0,
    "batches_processed": 5,
    "records_per_second": 1.5
  },
  "errors": [
    {
      "row": 45,
      "column": "code",
      "message": "Código de cuenta duplicado: 1105",
      "severity": "ERROR",
      "record_data": {
        "code": "1105",
        "name": "Caja General Duplicada"
      }
    }
  ],
  "warnings": [
    {
      "row": 67,
      "column": "parent_code",
      "message": "Cuenta padre no encontrada, se creará automáticamente",
      "severity": "WARNING"
    }
  ],
  "summary": {
    "accounts_created": 450,
    "accounts_updated": 35,
    "accounts_failed": 15,
    "hierarchies_created": 25
  }
}
```

### 4. Importar desde Archivo Subido

**POST** `/import-data/import-file`

Importación directa desde archivo subido con configuración automática.

**Form Data:**
- `file`: Archivo a importar (multipart/form-data)

**Query Parameters:**
- `data_type` (ImportDataType): Tipo de datos a importar
- `validation_level` (ImportValidationLevel): Nivel de validación
- `batch_size` (int): Tamaño de lote
- `skip_duplicates` (bool): Omitir duplicados (default: true)
- `update_existing` (bool): Actualizar existentes (default: false)
- `continue_on_error` (bool): Continuar en errores (default: false)

**Response (200):** Igual que el endpoint de importación completa

### 5. Obtener Templates de Importación

**GET** `/import-data/templates`

Obtiene templates y formatos disponibles para importación.

**Response (200):**
```json
{
  "templates": {
    "ACCOUNTS": {
      "description": "Template para importación de cuentas contables",
      "required_columns": ["code", "name", "account_type"],
      "optional_columns": ["parent_code", "description", "is_active"],
      "column_descriptions": {
        "code": "Código único de la cuenta (máximo 20 caracteres)",
        "name": "Nombre de la cuenta (máximo 255 caracteres)",
        "account_type": "Tipo de cuenta: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE",
        "parent_code": "Código de la cuenta padre para jerarquía",
        "description": "Descripción opcional de la cuenta"
      },
      "examples": [
        {
          "code": "1105",
          "name": "Caja General",
          "account_type": "ASSET",
          "parent_code": "11",
          "description": "Efectivo en caja general"
        },
        {
          "code": "2105",
          "name": "Proveedores",
          "account_type": "LIABILITY",
          "parent_code": "21"
        }
      ],
      "validation_rules": {
        "code": "Único, alfanumérico, máximo 20 caracteres",
        "name": "Requerido, máximo 255 caracteres",
        "account_type": "Debe ser uno de: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE"
      }
    },
    "JOURNAL_ENTRIES": {
      "description": "Template para importación de asientos contables",
      "required_columns": ["entry_date", "account_code", "debit_amount", "credit_amount"],
      "optional_columns": ["reference", "description", "third_party_code", "cost_center_code"],
      "examples": [
        {
          "entry_date": "2024-12-01",
          "reference": "FACT-001",
          "account_code": "1105",
          "debit_amount": "100.00",
          "credit_amount": "0.00",
          "description": "Cobro efectivo",
          "third_party_code": "CLI001"
        }
      ]
    },
    "THIRD_PARTIES": {
      "description": "Template para importación de terceros",
      "required_columns": ["code", "name", "third_party_type"],
      "optional_columns": ["document_type", "document_number", "email", "phone"],
      "examples": [
        {
          "code": "CLI001",
          "name": "Cliente ABC",
          "third_party_type": "CUSTOMER",
          "document_type": "NIT",
          "document_number": "123456789",
          "email": "cliente@abc.com"
        }
      ]
    }
  },
  "supported_formats": {
    "CSV": {
      "extensions": [".csv"],
      "delimiter_options": [",", ";", "|", "\t"],
      "encoding_options": ["utf-8", "latin-1", "cp1252"],
      "notes": "Primera fila debe contener los nombres de columnas"
    },
    "XLSX": {
      "extensions": [".xlsx", ".xls"],
      "sheet_options": "Especificar nombre de hoja o usar la primera",
      "header_row_options": "Especificar fila de encabezados (default: 1)",
      "notes": "Soporta múltiples hojas, usar nombres de columna en la primera fila"
    },
    "JSON": {
      "extensions": [".json"],
      "structure": "Array de objetos con propiedades correspondientes a columnas",
      "example": [
        {
          "code": "1105",
          "name": "Caja General",
          "account_type": "ASSET"
        }
      ]
    }
  }
}
```

## Configuración de Importación

### Configuración CSV

```json
{
  "format": "CSV",
  "csv_delimiter": ",",
  "csv_encoding": "utf-8",
  "csv_quote_char": "\"",
  "csv_escape_char": "\\",
  "skip_empty_rows": true,
  "trim_whitespace": true
}
```

### Configuración XLSX

```json
{
  "format": "XLSX",
  "xlsx_sheet_name": "Cuentas",
  "xlsx_header_row": 1,
  "skip_empty_rows": true,
  "trim_whitespace": true
}
```

### Configuración JSON

```json
{
  "format": "JSON",
  "json_array_path": null,
  "validate_schema": true
}
```

## Validaciones por Tipo de Datos

### Cuentas Contables

- **Código único**: No puede repetirse
- **Tipo de cuenta**: Debe ser ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
- **Jerarquía**: Cuenta padre debe existir o crearse automáticamente
- **Formato de código**: Alfanumérico, máximo 20 caracteres

### Asientos Contables

- **Balance**: Débitos = Créditos por asiento
- **Cuentas existentes**: Deben existir en el sistema
- **Fechas válidas**: Formato correcto y dentro de períodos permitidos
- **Montos positivos**: Valores numéricos válidos

### Terceros

- **Código único**: No puede repetirse
- **Tipo de tercero**: CUSTOMER, SUPPLIER, EMPLOYEE, OTHER
- **Documento**: Formato válido según tipo
- **Email**: Formato válido si se proporciona

## Estados de Importación

| Estado | Descripción |
|--------|-------------|
| `PENDING` | Importación en cola |
| `PROCESSING` | Procesando datos |
| `COMPLETED` | Completada exitosamente |
| `FAILED` | Falló la importación |
| `PARTIAL` | Completada parcialmente |

## Ejemplos de Integración

### Vista Previa e Importación Completa

```python
import requests
import base64

# Leer archivo
with open('cuentas.csv', 'rb') as file:
    file_content = base64.b64encode(file.read()).decode('utf-8')

# Vista previa
preview_response = requests.post(
    "https://api.contable.com/v1/import-data/preview",
    headers={"Authorization": "Bearer <token>"},
    json={
        "file_content": file_content,
        "filename": "cuentas.csv",
        "configuration": {
            "data_type": "ACCOUNTS",
            "format": "CSV",
            "validation_level": "STRICT",
            "batch_size": 100
        },
        "preview_rows": 10
    }
)

preview = preview_response.json()
print(f"Filas válidas: {preview['validation_summary']['valid_rows']}")

# Si la vista previa es buena, proceder con importación
if preview['validation_summary']['rows_with_errors'] == 0:
    import_response = requests.post(
        "https://api.contable.com/v1/import-data/import",
        headers={"Authorization": "Bearer <token>"},
        json={
            "file_content": file_content,
            "filename": "cuentas.csv",
            "configuration": {
                "data_type": "ACCOUNTS",
                "format": "CSV",
                "validation_level": "STRICT",
                "batch_size": 100,
                "skip_duplicates": True
            }
        }
    )
    
    result = import_response.json()
    print(f"Importados: {result['statistics']['successful_imports']}")
```

### Importación con Subida de Archivo

```python
import requests

# Subir archivo directamente
with open('asientos.xlsx', 'rb') as file:
    response = requests.post(
        "https://api.contable.com/v1/import-data/import-file",
        headers={"Authorization": "Bearer <token>"},
        files={"file": file},
        params={
            "data_type": "JOURNAL_ENTRIES",
            "validation_level": "MODERATE",
            "batch_size": 50,
            "continue_on_error": True
        }
    )

result = response.json()
print(f"Estado: {result['status']}")
print(f"Procesados: {result['statistics']['total_rows_processed']}")
print(f"Exitosos: {result['statistics']['successful_imports']}")
```

### Obtener Templates

```python
import requests

# Obtener templates disponibles
response = requests.get(
    "https://api.contable.com/v1/import-data/templates",
    headers={"Authorization": "Bearer <token>"}
)

templates = response.json()
accounts_template = templates['templates']['ACCOUNTS']
print("Columnas requeridas:", accounts_template['required_columns'])
print("Ejemplo:", accounts_template['examples'][0])
```

## Mejores Prácticas

1. **Usar vista previa**: Siempre revisar la vista previa antes de importar
2. **Validar datos**: Limpiar datos antes de la importación
3. **Lotes pequeños**: Usar lotes de 50-100 registros para mejor rendimiento
4. **Backup**: Hacer respaldo antes de importaciones grandes
5. **Monitoreo**: Revisar errores y warnings en el resultado
6. **Templates**: Usar templates predefinidos para garantizar formato correcto
7. **Encoding**: Verificar encoding de archivos CSV (UTF-8 recomendado)
8. **Duplicados**: Configurar manejo de duplicados según necesidades

## Manejo de Errores

### Errores de Validación

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Datos inválidos en el archivo",
  "details": {
    "row": 45,
    "column": "account_type",
    "value": "INVALID_TYPE",
    "expected": "ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE"
  }
}
```

### Errores de Formato

```json
{
  "error": "FORMAT_ERROR",
  "message": "Archivo no válido o corrupto",
  "details": {
    "file_type": "CSV",
    "detected_encoding": "unknown",
    "suggestion": "Verificar encoding del archivo"
  }
}
```

### Errores de Permisos

```json
{
  "error": "PERMISSION_ERROR",
  "message": "Sin permisos para importar este tipo de datos",
  "details": {
    "required_permission": "can_modify_accounts",
    "user_permissions": ["can_view_accounts"]
  }
}
```

## Límites y Restricciones

- **Tamaño máximo de archivo**: 10MB
- **Registros por lote**: 1-1000
- **Filas de vista previa**: 1-100
- **Timeout de procesamiento**: 30 minutos
- **Formatos soportados**: CSV, XLSX, JSON
- **Concurrent imports**: 1 por usuario

## Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Importación exitosa |
| 400 | Error de validación o formato |
| 403 | Sin permisos suficientes |
| 413 | Archivo demasiado grande |
| 422 | Error de procesamiento |
| 500 | Error interno del servidor |
