# API de Exportación de Datos - Documentación Actualizada

## Descripción General

La API de exportación de datos proporciona funcionalidades para exportar datos contables en múltiples formatos (CSV, JSON, XLSX) con filtros avanzados y permisos granulares.

### Características Principales

- **Múltiples formatos**: CSV, JSON, XLSX
- **Exportación por IDs**: Selección específica de registros
- **Filtros avanzados**: Fechas, estados, criterios personalizados
- **Esquemas de tablas**: Información detallada de estructura
- **Permisos granulares**: Control de acceso por rol
- **Metadatos incluidos**: Información de exportación y usuario

## Autenticación

Todos los endpoints requieren autenticación Bearer Token:

```
Authorization: Bearer <jwt_token>
```

## Permisos Requeridos

| Operación | Roles Permitidos |
|-----------|------------------|
| Ver tablas disponibles | ADMIN, CONTADOR |
| Obtener esquemas | ADMIN, CONTADOR |
| Exportar usuarios | ADMIN |
| Exportar datos contables | ADMIN, CONTADOR |
| Exportación avanzada | ADMIN, CONTADOR |

## Formatos de Exportación Soportados

| Formato | Extensión | Tipo MIME | Descripción |
|---------|-----------|-----------|-------------|
| `CSV` | .csv | text/csv | Valores separados por comas |
| `JSON` | .json | application/json | Formato JSON estructurado |
| `XLSX` | .xlsx | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | Hoja de cálculo Excel |

## Tablas Disponibles

| Tabla | Nombre | Descripción |
|-------|--------|-------------|
| `USERS` | users | Usuarios del sistema |
| `ACCOUNTS` | accounts | Cuentas contables |
| `JOURNAL_ENTRIES` | journal_entries | Asientos contables |
| `THIRD_PARTIES` | third_parties | Terceros |
| `COST_CENTERS` | cost_centers | Centros de costo |

## Endpoints

### 1. Obtener Tablas Disponibles

**GET** `/export/tables`

Obtiene la lista de todas las tablas disponibles para exportación con sus esquemas.

**Response (200):**
```json
{
  "tables": [
    {
      "name": "ACCOUNTS",
      "display_name": "Cuentas Contables",
      "description": "Plan de cuentas contables del sistema",
      "record_count": 1250,
      "columns": [
        {
          "name": "id",
          "type": "UUID",
          "nullable": false,
          "description": "Identificador único"
        },
        {
          "name": "code",
          "type": "VARCHAR",
          "nullable": false,
          "max_length": 20,
          "description": "Código de la cuenta"
        },
        {
          "name": "name",
          "type": "VARCHAR",
          "nullable": false,
          "max_length": 255,
          "description": "Nombre de la cuenta"
        },
        {
          "name": "account_type",
          "type": "ENUM",
          "nullable": false,
          "enum_values": ["ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"],
          "description": "Tipo de cuenta"
        }
      ],
      "relationships": [
        {
          "name": "parent",
          "type": "many_to_one",
          "target_table": "accounts",
          "description": "Cuenta padre en la jerarquía"
        }
      ]
    },
    {
      "name": "JOURNAL_ENTRIES",
      "display_name": "Asientos Contables",
      "description": "Asientos contables del sistema",
      "record_count": 5420,
      "columns": [
        {
          "name": "id",
          "type": "UUID",
          "nullable": false
        },
        {
          "name": "entry_number",
          "type": "VARCHAR",
          "nullable": false,
          "description": "Número único del asiento"
        },
        {
          "name": "entry_date",
          "type": "DATE",
          "nullable": false,
          "description": "Fecha del asiento"
        },
        {
          "name": "status",
          "type": "ENUM",
          "nullable": false,
          "enum_values": ["DRAFT", "APPROVED", "POSTED", "CANCELLED"]
        }
      ]
    }
  ],
  "total_tables": 5,
  "export_formats": ["CSV", "JSON", "XLSX"]
}
```

### 2. Obtener Esquema de Tabla

**GET** `/export/tables/{table_name}`

Obtiene información detallada del esquema de una tabla específica.

**Path Parameters:**
- `table_name` (TableName): Nombre de la tabla

**Response (200):**
```json
{
  "name": "ACCOUNTS",
  "display_name": "Cuentas Contables",
  "description": "Plan de cuentas contables del sistema",
  "record_count": 1250,
  "columns": [
    {
      "name": "id",
      "type": "UUID",
      "nullable": false,
      "primary_key": true,
      "description": "Identificador único de la cuenta"
    },
    {
      "name": "code",
      "type": "VARCHAR",
      "nullable": false,
      "max_length": 20,
      "unique": true,
      "description": "Código único de la cuenta"
    },
    {
      "name": "name",
      "type": "VARCHAR",
      "nullable": false,
      "max_length": 255,
      "description": "Nombre descriptivo de la cuenta"
    },
    {
      "name": "account_type",
      "type": "ENUM",
      "nullable": false,
      "enum_values": ["ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"],
      "description": "Tipo de cuenta contable"
    },
    {
      "name": "is_active",
      "type": "BOOLEAN",
      "nullable": false,
      "default": true,
      "description": "Indica si la cuenta está activa"
    },
    {
      "name": "created_at",
      "type": "TIMESTAMP",
      "nullable": false,
      "description": "Fecha de creación"
    }
  ],
  "indexes": [
    {
      "name": "idx_accounts_code",
      "columns": ["code"],
      "unique": true
    },
    {
      "name": "idx_accounts_type",
      "columns": ["account_type"]
    }
  ],
  "relationships": [
    {
      "name": "parent",
      "type": "many_to_one",
      "target_table": "accounts",
      "foreign_key": "parent_id",
      "description": "Cuenta padre en la jerarquía"
    },
    {
      "name": "children",
      "type": "one_to_many",
      "target_table": "accounts",
      "description": "Cuentas hijas"
    }
  ]
}
```

### 3. Exportar Datos por IDs

**POST** `/export/export`

Exporta registros específicos de cualquier tabla usando una lista de IDs.

**Request Body:**
```json
{
  "table": "ACCOUNTS",
  "format": "XLSX",
  "ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001",
    "770e8400-e29b-41d4-a716-446655440002"
  ],
  "file_name": "cuentas_seleccionadas"
}
```

**Response (200):**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename=cuentas_seleccionadas.xlsx

[Contenido binario del archivo Excel]
```

### 4. Obtener Formatos Soportados

**GET** `/export/formats`

Obtiene la lista de formatos de exportación soportados.

**Response (200):**
```json
{
  "formats": [
    {
      "value": "CSV",
      "name": "CSV",
      "description": "Archivo de valores separados por comas",
      "extension": "csv",
      "mime_type": "text/csv"
    },
    {
      "value": "JSON",
      "name": "JSON",
      "description": "Archivo de formato JSON",
      "extension": "json",
      "mime_type": "application/json"
    },
    {
      "value": "XLSX",
      "name": "Excel",
      "description": "Archivo de Excel",
      "extension": "xlsx",
      "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
  ]
}
```

### 5. Exportar Usuarios Específicos

**POST** `/export/export/users`

Exporta usuarios específicos por IDs (solo para ADMIN).

**Query Parameters:**
- `format` (ExportFormat): Formato de exportación
- `ids` (List[str]): Lista de IDs de usuarios
- `file_name` (str, optional): Nombre del archivo (default: "usuarios")

**Request Body:**
```json
{
  "format": "CSV",
  "ids": ["user-id-1", "user-id-2", "user-id-3"],
  "file_name": "usuarios_seleccionados"
}
```

### 6. Exportar Cuentas Específicas

**POST** `/export/export/accounts`

Exporta cuentas contables específicas por IDs.

**Query Parameters:**
- `format` (ExportFormat): Formato de exportación
- `ids` (List[str]): Lista de IDs de cuentas
- `file_name` (str, optional): Nombre del archivo (default: "plan_cuentas")

### 7. Exportar Asientos Específicos

**POST** `/export/export/journal-entries`

Exporta asientos contables específicos por IDs.

**Query Parameters:**
- `format` (ExportFormat): Formato de exportación
- `ids` (List[str]): Lista de IDs de asientos
- `file_name` (str, optional): Nombre del archivo (default: "asientos_contables")

### 8. Exportación Avanzada

**POST** `/export/export/advanced`

Exportación avanzada con filtros complejos y opciones personalizadas.

**Request Body:**
```json
{
  "table_name": "JOURNAL_ENTRIES",
  "export_format": "XLSX",
  "filters": {
    "ids": null,
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "active_only": true,
    "custom_filters": {
      "status": ["POSTED", "APPROVED"],
      "min_amount": 100.00,
      "account_type": "ASSET"
    },
    "limit": 1000,
    "offset": 0
  },
  "columns": [
    "entry_number",
    "entry_date",
    "reference",
    "description",
    "status",
    "total_debit",
    "total_credit"
  ],
  "include_metadata": true,
  "file_name": "asientos_contables_2024"
}
```

**Response (200):**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename=asientos_contables_2024.xlsx

[Contenido del archivo con datos filtrados y metadatos]
```

## Filtros Avanzados

### Filtros por Fecha

```json
{
  "date_from": "2024-01-01",
  "date_to": "2024-12-31"
}
```

### Filtros Personalizados

```json
{
  "custom_filters": {
    "status": ["POSTED", "APPROVED"],
    "account_type": ["ASSET", "LIABILITY"],
    "min_amount": 100.00,
    "max_amount": 10000.00,
    "user_id": "specific-user-id",
    "search_text": "término de búsqueda"
  }
}
```

### Selección de Columnas

```json
{
  "columns": [
    "id",
    "code",
    "name",
    "account_type",
    "created_at"
  ]
}
```

## Metadatos de Exportación

Cuando `include_metadata` es `true`, se incluye información adicional:

```json
{
  "export_metadata": {
    "exported_at": "2024-12-01T10:30:00Z",
    "exported_by": {
      "id": "user-id",
      "username": "admin",
      "role": "ADMIN"
    },
    "table_info": {
      "name": "ACCOUNTS",
      "total_records": 1250,
      "exported_records": 45
    },
    "filters_applied": {
      "date_from": "2024-01-01",
      "date_to": "2024-12-31",
      "custom_filters": {...}
    },
    "export_settings": {
      "format": "XLSX",
      "columns": [...],
      "include_relationships": true
    }
  }
}
```

## Ejemplos de Uso

### Exportar Cuentas Específicas

```python
import requests

# Exportar cuentas en Excel
response = requests.post(
    "https://api.contable.com/v1/export/export/accounts",
    headers={"Authorization": "Bearer <token>"},
    params={
        "format": "XLSX",
        "file_name": "cuentas_activos"
    },
    json={
        "ids": [
            "550e8400-e29b-41d4-a716-446655440000",
            "660e8400-e29b-41d4-a716-446655440001"
        ]
    }
)

# Guardar archivo
with open('cuentas_activos.xlsx', 'wb') as f:
    f.write(response.content)
```

### Exportación Avanzada con Filtros

```python
import requests

# Exportar asientos contables con filtros avanzados
response = requests.post(
    "https://api.contable.com/v1/export/export/advanced",
    headers={"Authorization": "Bearer <token>"},
    json={
        "table_name": "JOURNAL_ENTRIES",
        "export_format": "CSV",
        "filters": {
            "date_from": "2024-01-01",
            "date_to": "2024-03-31",
            "custom_filters": {
                "status": ["POSTED"],
                "min_amount": 1000.00
            },
            "limit": 500
        },
        "columns": [
            "entry_number",
            "entry_date",
            "reference",
            "description",
            "total_debit",
            "total_credit"
        ],
        "include_metadata": true,
        "file_name": "asientos_q1_2024"
    }
)

# Procesar respuesta CSV
csv_data = response.text
print("Datos exportados:")
print(csv_data[:500])  # Primeros 500 caracteres
```

### Obtener Información de Tablas

```python
import requests

# Obtener tablas disponibles
response = requests.get(
    "https://api.contable.com/v1/export/tables",
    headers={"Authorization": "Bearer <token>"}
)

tables = response.json()
for table in tables['tables']:
    print(f"Tabla: {table['display_name']}")
    print(f"Registros: {table['record_count']}")
    print(f"Columnas: {len(table['columns'])}")
    print("---")

# Obtener esquema específico
response = requests.get(
    "https://api.contable.com/v1/export/tables/ACCOUNTS",
    headers={"Authorization": "Bearer <token>"}
)

schema = response.json()
print("Columnas disponibles:")
for col in schema['columns']:
    print(f"- {col['name']}: {col['type']} - {col['description']}")
```

## Formatos de Respuesta

### CSV

```csv
id,code,name,account_type,is_active,created_at
550e8400-e29b-41d4-a716-446655440000,1105,"Caja General",ASSET,true,2024-01-15T10:00:00Z
660e8400-e29b-41d4-a716-446655440001,1110,"Bancos",ASSET,true,2024-01-15T10:00:00Z
```

### JSON

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "1105",
    "name": "Caja General",
    "account_type": "ASSET",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "code": "1110",
    "name": "Bancos",
    "account_type": "ASSET",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

### XLSX

El formato Excel incluye:
- Hoja principal con datos
- Hoja de metadatos (si se solicita)
- Formato de celdas apropiado
- Encabezados descriptivos

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 400 | Parámetros inválidos o tabla no encontrada |
| 403 | Sin permisos para exportar datos |
| 404 | Tabla o registros no encontrados |
| 422 | Error de validación en filtros |
| 500 | Error interno del servidor |

## Mejores Prácticas

1. **Verificar permisos**: Confirmar rol antes de intentar exportaciones
2. **Usar filtros**: Limitar datos para mejorar rendimiento
3. **Seleccionar columnas**: Exportar solo columnas necesarias
4. **Lotes pequeños**: Usar límites para conjuntos grandes de datos
5. **Metadatos**: Incluir metadatos para auditoría
6. **Formatos apropiados**: CSV para datos simples, Excel para análisis
7. **Nombres descriptivos**: Usar nombres de archivo informativos
8. **Manejo de errores**: Implementar retry logic para exportaciones grandes

## Límites y Restricciones

- **Registros por exportación**: 10,000 (configurable)
- **Tamaño máximo de archivo**: 50MB
- **Timeout**: 5 minutos para exportaciones
- **Exportaciones concurrentes**: 2 por usuario
- **Retención de archivos**: No se almacenan en servidor
- **Formatos soportados**: CSV, JSON, XLSX únicamente
