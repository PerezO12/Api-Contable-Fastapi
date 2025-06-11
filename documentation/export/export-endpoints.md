# API de Exportación - Documentación de Endpoints

## Descripción General

La API de exportación proporciona endpoints REST para exportar datos de cualquier tabla del sistema contable en múltiples formatos. Todos los endpoints requieren autenticación y implementan filtrado automático de datos sensibles.

## Base URL
```
/api/v1/export/
```

## Autenticación
Todos los endpoints requieren token JWT válido en el header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints Disponibles

### 1. Exportación Simple
**Endpoint principal para exportación directa de registros específicos**

#### `POST /export/`

**Descripción:** Exporta registros específicos de una tabla usando una lista de IDs.

**Request Body:**
```json
{
  "table": "users",           // Nombre de la tabla (obligatorio)
  "format": "csv",            // Formato: csv, json, xlsx (obligatorio)
  "ids": [1, 2, 3, 4, 5]     // Lista de IDs a exportar (obligatorio)
}
```

**Response:**
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

**Códigos de Estado:**
- `200`: Exportación exitosa
- `400`: Parámetros inválidos
- `401`: No autenticado
- `403`: Sin permisos
- `404`: Tabla no encontrada
- `500`: Error interno del servidor

---

### 2. Exportación Avanzada
**Endpoint para exportaciones con filtros complejos**

#### `POST /export/advanced`

**Descripción:** Permite exportaciones con filtros avanzados como rangos de fechas, estado activo y filtros personalizados.

**Request Body:**
```json
{
  "table_name": "journal_entries",
  "export_format": "xlsx",
  "filters": {
    "ids": [1, 2, 3],                    // Opcional: IDs específicos
    "date_from": "2024-01-01",           // Opcional: Fecha inicio
    "date_to": "2024-12-31",             // Opcional: Fecha fin
    "active_only": true,                 // Opcional: Solo registros activos
    "custom_filters": {                  // Opcional: Filtros personalizados
      "account_type": "ASSET",
      "status": "ACTIVE"
    },
    "offset": 0,                         // Opcional: Paginación
    "limit": 1000                        // Opcional: Límite de registros
  },
  "columns": [                           // Opcional: Columnas específicas
    {
      "name": "id",
      "include": true
    },
    {
      "name": "description",
      "include": true
    }
  ],
  "file_name": "asientos_2024"           // Opcional: Nombre personalizado
}
```

**Response:** Mismo formato que exportación simple.

---

### 3. Información de Tablas

#### `GET /export/tables/`
**Descripción:** Lista todas las tablas disponibles para exportación.

**Response:**
```json
{
  "tables": [
    {
      "table_name": "users",
      "display_name": "Usuarios",
      "description": "Tabla Usuarios",
      "available_columns": [
        {
          "name": "id",
          "data_type": "number",
          "format": null,
          "include": true
        },
        {
          "name": "email",
          "data_type": "string",
          "format": null,
          "include": true
        }
      ],
      "total_records": 150
    }
  ],
  "total_tables": 10
}
```

#### `GET /export/tables/{table_name}`
**Descripción:** Obtiene información detallada de una tabla específica.

**Parámetros:**
- `table_name`: Nombre de la tabla (users, accounts, journal_entries, etc.)

**Response:**
```json
{
  "table_name": "users",
  "display_name": "Usuarios",
  "description": "Tabla Usuarios",
  "available_columns": [
    {
      "name": "id",
      "data_type": "number",
      "format": null,
      "include": true
    }
  ],
  "total_records": 150,
  "sample_data": [
    {
      "id": 1,
      "email": "user1@example.com",
      "first_name": "John",
      "last_name": "Doe"
    }
  ]
}
```

---

### 4. Formatos Disponibles

#### `GET /export/formats/`
**Descripción:** Lista todos los formatos de exportación disponibles.

**Response:**
```json
{
  "formats": [
    {
      "name": "csv",
      "display_name": "CSV (Comma-Separated Values)",
      "description": "Formato CSV compatible con Excel",
      "content_type": "text/csv",
      "file_extension": "csv"
    },
    {
      "name": "json",
      "display_name": "JSON (JavaScript Object Notation)",
      "description": "Formato JSON para APIs e integraciones",
      "content_type": "application/json",
      "file_extension": "json"
    },
    {
      "name": "xlsx",
      "display_name": "Excel (XLSX)",
      "description": "Formato nativo de Microsoft Excel",
      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "file_extension": "xlsx"
    }
  ]
}
```

---

### 5. Exportaciones Rápidas
**Endpoints de conveniencia para tablas comunes**

#### `POST /export/users/`
**Descripción:** Exportación rápida de usuarios.

#### `POST /export/accounts/`
**Descripción:** Exportación rápida de cuentas.

#### `POST /export/journal-entries/`
**Descripción:** Exportación rápida de asientos contables.

**Request Body para todos:**
```json
{
  "format": "csv",              // Formato de exportación
  "ids": [1, 2, 3, 4, 5]       // IDs a exportar
}
```

**Response:** Mismo formato que exportación simple.

---

## Esquemas de Datos

### SimpleExportRequest
```json
{
  "table": "string",           // Nombre de tabla (enum)
  "format": "string",          // Formato (csv|json|xlsx)
  "ids": ["integer"]           // Array de IDs
}
```

### ExportRequest (Avanzado)
```json
{
  "table_name": "string",      // Nombre de tabla (enum)
  "export_format": "string",   // Formato (csv|json|xlsx)
  "filters": {
    "ids": ["integer"],        // IDs específicos
    "date_from": "date",       // Fecha inicio
    "date_to": "date",         // Fecha fin
    "active_only": "boolean",  // Solo activos
    "custom_filters": {},      // Filtros personalizados
    "offset": "integer",       // Paginación
    "limit": "integer"         // Límite
  },
  "columns": [                 // Columnas específicas
    {
      "name": "string",
      "include": "boolean"
    }
  ],
  "file_name": "string"        // Nombre personalizado
}
```

### ExportResponse
```json
{
  "file_name": "string",       // Nombre del archivo generado
  "file_content": "string",    // Contenido del archivo
  "content_type": "string",    // Tipo MIME
  "metadata": {
    "export_date": "datetime",
    "user_id": "uuid",
    "table_name": "string",
    "total_records": "integer",
    "exported_records": "integer",
    "filters_applied": {},
    "format": "string",
    "file_size_bytes": "integer",
    "columns_exported": ["string"]
  },
  "success": "boolean",
  "message": "string"
}
```

## Tablas Disponibles

| Valor | Nombre de Visualización | Descripción |
|-------|------------------------|-------------|
| `users` | Usuarios | Gestión de usuarios del sistema |
| `accounts` | Plan de Cuentas | Cuentas contables |
| `journal_entries` | Asientos Contables | Asientos del diario |
| `journal_entry_lines` | Líneas de Asientos | Líneas de detalle de asientos |
| `audit_logs` | Logs de Auditoría | Registro de auditoría |
| `user_sessions` | Sesiones de Usuario | Sesiones activas |
| `change_tracking` | Tracking de Cambios | Seguimiento de modificaciones |
| `system_configuration` | Configuración del Sistema | Configuraciones |
| `company_info` | Información de la Empresa | Datos de la empresa |
| `number_sequences` | Secuencias de Numeración | Secuencias automáticas |

## Ejemplos de Uso

### Ejemplo 1: Exportar usuarios específicos en CSV
```bash
curl -X POST "http://localhost:8000/api/v1/export/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "table": "users",
    "format": "csv",
    "ids": [1, 2, 3]
  }'
```

### Ejemplo 2: Exportar asientos del año en Excel
```bash
curl -X POST "http://localhost:8000/api/v1/export/advanced" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "journal_entries",
    "export_format": "xlsx",
    "filters": {
      "date_from": "2024-01-01",
      "date_to": "2024-12-31"
    },
    "file_name": "asientos_2024"
  }'
```

### Ejemplo 3: Consultar esquema de tabla
```bash
curl -X GET "http://localhost:8000/api/v1/export/tables/users" \
  -H "Authorization: Bearer <token>"
```

### Ejemplo 4: Exportación rápida de cuentas
```bash
curl -X POST "http://localhost:8000/api/v1/export/accounts/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "ids": [1, 5, 10, 15]
  }'
```

## Manejo de Errores

### Errores Comunes

#### 400 Bad Request
```json
{
  "detail": "Parámetros inválidos",
  "errors": [
    {
      "field": "table",
      "message": "Tabla no válida"
    }
  ]
}
```

#### 401 Unauthorized
```json
{
  "detail": "Token inválido o expirado"
}
```

#### 403 Forbidden
```json
{
  "detail": "Sin permisos para exportar esta tabla"
}
```

#### 404 Not Found
```json
{
  "detail": "Tabla 'invalid_table' no encontrada"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "ids"],
      "msg": "Lista de IDs no puede estar vacía",
      "type": "value_error"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Error interno del servidor",
  "error_id": "exp_error_123456"
}
```

## Consideraciones de Rendimiento

### Límites Recomendados
- **Exportación simple**: Máximo 10,000 registros por solicitud
- **Exportación avanzada**: Usar paginación para >50,000 registros
- **Formato XLSX**: Límite de 100,000 registros por limitaciones de Excel

### Optimizaciones
- Use filtros específicos para reducir el volumen de datos
- Para grandes exportaciones, considere usar paginación
- Los filtros por ID son más eficientes que otros tipos

### Timeouts
- **Request timeout**: 30 segundos para exportaciones simples
- **Extended timeout**: 300 segundos para exportaciones grandes

## Seguridad

### Datos Sensibles
Los siguientes campos se omiten automáticamente en las exportaciones:

**Tabla Users:**
- `hashed_password`, `password_hash`, `password`
- `salt`, `secret_key`, `private_key`
- `api_key`, `token`

**Tabla User Sessions:**
- `session_token`, `refresh_token`, `access_token`

**Tabla System Configuration:**
- `secret_value`, `password`, `api_secret`, `private_key`

### Auditoría
Todas las exportaciones se registran automáticamente con:
- Usuario que realizó la exportación
- Fecha y hora
- Tabla y filtros utilizados
- Número de registros exportados
- Formato de exportación

### Control de Acceso
- Todos los endpoints requieren autenticación JWT
- Validación de permisos por rol de usuario
- Logs de auditoría para todas las operaciones

## Integración

### SDK / Librerías Cliente
```javascript
// JavaScript/TypeScript
const response = await fetch('/api/v1/export/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    table: 'users',
    format: 'csv',
    ids: [1, 2, 3]
  })
});

const data = await response.json();
```

```python
# Python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/export/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'table': 'users',
        'format': 'csv',
        'ids': [1, 2, 3]
    }
)

data = response.json()
```

### Procesamiento de Respuestas
```python
# Guardar archivo exportado
if response['success']:
    filename = response['file_name']
    content = response['file_content']
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Exportación guardada: {filename}")
    print(f"Registros exportados: {response['metadata']['exported_records']}")
```
