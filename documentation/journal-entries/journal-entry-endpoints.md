# API de Asientos Contables - Documentación Actualizada

## Descripción General

La API de asientos contables proporciona funcionalidades completas para la gestión de asientos contables con validaciones empresariales, flujo de estados, operaciones masivas y seguimiento de auditoría.

### Características Principales

- **CRUD completo** de asientos contables
- **Flujo de estados**: Borrador → Aprobado → Contabilizado → Cancelado
- **Operaciones masivas** con validación previa
- **Líneas de detalle** con cuentas, terceros y centros de costo
- **Validaciones de balance** automáticas
- **Auditoría completa** de cambios
- **Reversión de asientos** contabilizados
- **Búsqueda avanzada** y filtros

## Autenticación

Todos los endpoints requieren autenticación Bearer Token:

```
Authorization: Bearer <jwt_token>
```

## Permisos Requeridos

- **can_create_entries**: Requerido para crear, actualizar, aprobar, contabilizar y cancelar asientos

## Estados de Asientos Contables

| Estado | Descripción | Operaciones Permitidas |
|--------|-------------|----------------------|
| `DRAFT` | Borrador | Editar, Eliminar, Aprobar |
| `APPROVED` | Aprobado | Contabilizar, Reset a Borrador |
| `POSTED` | Contabilizado | Cancelar, Revertir |
| `CANCELLED` | Cancelado | Solo consulta |

## Endpoints

### 1. Crear Asiento Contable

**POST** `/journal-entries/`

Crea un nuevo asiento contable en estado borrador.

**Request Body:**
```json
{
  "entry_date": "2024-12-01",
  "reference": "DOC-001",
  "description": "Compra de mercancía",
  "entry_type": "STANDARD",
  "lines": [
    {
      "account_id": "550e8400-e29b-41d4-a716-446655440000",
      "debit_amount": 100.00,
      "credit_amount": 0.00,
      "description": "Inventario",
      "third_party_id": "660e8400-e29b-41d4-a716-446655440001",
      "cost_center_id": "770e8400-e29b-41d4-a716-446655440002"
    },
    {
      "account_id": "880e8400-e29b-41d4-a716-446655440003",
      "debit_amount": 0.00,
      "credit_amount": 100.00,
      "description": "Cuentas por pagar"
    }
  ]
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "entry_number": "JE-2024-00001",
  "entry_date": "2024-12-01",
  "reference": "DOC-001",
  "description": "Compra de mercancía",
  "entry_type": "STANDARD",
  "status": "DRAFT",
  "total_debit": 100.00,
  "total_credit": 100.00,
  "created_by_id": "user-id",
  "created_at": "2024-12-01T10:00:00Z",
  "lines": [
    {
      "id": "line-id-1",
      "account": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "1435",
        "name": "Inventarios"
      },
      "debit_amount": 100.00,
      "credit_amount": 0.00,
      "description": "Inventario",
      "third_party": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "code": "PROV001",
        "name": "Proveedor ABC"
      },
      "cost_center": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "code": "CC01",
        "name": "Ventas"
      }
    }
  ]
}
```

### 2. Listar Asientos Contables

**GET** `/journal-entries/`

Obtiene una lista paginada de asientos contables con filtros opcionales.

**Query Parameters:**
- `skip` (int): Registros a omitir (default: 0)
- `limit` (int): Registros por página (default: 100, max: 1000)
- `status` (JournalEntryStatus): Filtrar por estado
- `account_id` (UUID): Filtrar por cuenta
- `date_from` (date): Fecha desde
- `date_to` (date): Fecha hasta
- `reference` (string): Filtrar por referencia

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "entry_number": "JE-2024-00001",
      "entry_date": "2024-12-01",
      "status": "DRAFT",
      "total_debit": 100.00,
      "total_credit": 100.00,
      "lines": [...]
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

### 3. Obtener Asiento por ID

**GET** `/journal-entries/{journal_entry_id}`

Obtiene los detalles completos de un asiento contable.

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "entry_number": "JE-2024-00001",
  "entry_date": "2024-12-01",
  "reference": "DOC-001",
  "description": "Compra de mercancía",
  "status": "DRAFT",
  "total_debit": 100.00,
  "total_credit": 100.00,
  "created_by_id": "user-id",
  "created_at": "2024-12-01T10:00:00Z",
  "lines": [
    {
      "id": "line-id-1",
      "account": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "1435",
        "name": "Inventarios"
      },
      "debit_amount": 100.00,
      "credit_amount": 0.00,
      "description": "Inventario",
      "third_party": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "code": "PROV001",
        "name": "Proveedor ABC",
        "document_type": "NIT",
        "document_number": "123456789"
      },
      "cost_center": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "code": "CC01",
        "name": "Ventas"
      }
    }
  ]
}
```

### 4. Actualizar Asiento Contable

**PUT** `/journal-entries/{journal_entry_id}`

Actualiza un asiento contable (solo en estado borrador).

**Request Body:**
```json
{
  "description": "Compra de mercancía - Actualizada",
  "lines": [
    {
      "id": "line-id-1",
      "account_id": "550e8400-e29b-41d4-a716-446655440000",
      "debit_amount": 150.00,
      "credit_amount": 0.00,
      "description": "Inventario actualizado"
    },
    {
      "account_id": "880e8400-e29b-41d4-a716-446655440003",
      "debit_amount": 0.00,
      "credit_amount": 150.00,
      "description": "Cuentas por pagar"
    }
  ]
}
```

### 5. Eliminar Asiento Contable

**DELETE** `/journal-entries/{journal_entry_id}`

Elimina un asiento contable (solo en estado borrador).

**Response (204):** Sin contenido

### 6. Aprobar Asiento Contable

**POST** `/journal-entries/{journal_entry_id}/approve`

Cambia el estado del asiento de borrador a aprobado.

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "APPROVED",
  "approved_by_id": "user-id",
  "approved_at": "2024-12-01T11:00:00Z"
}
```

### 7. Contabilizar Asiento

**POST** `/journal-entries/{journal_entry_id}/post`

Contabiliza un asiento aprobado, afectando los saldos de las cuentas.

**Request Body (opcional):**
```json
{
  "post_date": "2024-12-01",
  "reason": "Contabilización automática"
}
```

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "POSTED",
  "posted_by_id": "user-id",
  "posted_at": "2024-12-01T12:00:00Z"
}
```

### 8. Cancelar Asiento

**POST** `/journal-entries/{journal_entry_id}/cancel`

Cancela un asiento contable. Para asientos contabilizados, crea un asiento de reversión.

**Request Body:**
```json
{
  "reason": "Error en los datos",
  "cancel_date": "2024-12-01"
}
```

### 9. Revertir Asiento

**POST** `/journal-entries/{journal_entry_id}/reverse`

Crea un asiento de reversión para un asiento contabilizado.

**Query Parameters:**
- `reason` (string, required): Razón de la reversión

**Response (200):**
```json
{
  "id": "new-reversal-entry-id",
  "entry_number": "JE-2024-00002",
  "description": "Reversión de JE-2024-00001 - Error en los datos",
  "status": "DRAFT",
  "original_entry_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### 10. Obtener Estadísticas

**GET** `/journal-entries/statistics/summary`

Obtiene estadísticas de asientos contables.

**Query Parameters:**
- `date_from` (date): Fecha desde
- `date_to` (date): Fecha hasta

**Response (200):**
```json
{
  "total_entries": 1250,
  "draft_entries": 45,
  "approved_entries": 12,
  "posted_entries": 1180,
  "cancelled_entries": 13,
  "total_debit_amount": 2500000.00,
  "total_credit_amount": 2500000.00,
  "average_entry_amount": 2000.00,
  "entries_by_month": [
    {
      "month": "2024-12",
      "count": 85,
      "total_amount": 170000.00
    }
  ]
}
```

### 11. Búsqueda Avanzada

**GET** `/journal-entries/search`

Búsqueda avanzada de asientos contables con filtros múltiples.

**Query Parameters:**
- Filtros de `JournalEntryFilter` como query parameters

**Response (200):**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "entry_number": "JE-2024-00001",
    "status": "POSTED",
    "lines": [...]
  }
]
```

### 12. Creación Masiva

**POST** `/journal-entries/bulk-create`

Crea múltiples asientos contables en una sola operación.

**Request Body:**
```json
[
  {
    "entry_date": "2024-12-01",
    "reference": "DOC-001",
    "description": "Asiento 1",
    "lines": [...]
  },
  {
    "entry_date": "2024-12-01",
    "reference": "DOC-002",
    "description": "Asiento 2",
    "lines": [...]
  }
]
```

### 13. Obtener por Número

**GET** `/journal-entries/by-number/{entry_number}`

Obtiene un asiento contable por su número único.

## Operaciones Masivas

### Validación Previa

Todos los endpoints de operaciones masivas incluyen endpoints de validación correspondientes:

- `POST /journal-entries/validate-deletion` - Validar eliminación
- `POST /journal-entries/validate-approve` - Validar aprobación
- `POST /journal-entries/validate-post` - Validar contabilización
- `POST /journal-entries/validate-cancel` - Validar cancelación
- `POST /journal-entries/validate-reverse` - Validar reversión
- `POST /journal-entries/validate-reset-to-draft` - Validar reset a borrador

### Operaciones Masivas Disponibles

#### 1. Eliminación Masiva

**POST** `/journal-entries/bulk-delete`

```json
{
  "journal_entry_ids": ["id1", "id2", "id3"],
  "force_delete": false,
  "reason": "Corrección de datos"
}
```

#### 2. Aprobación Masiva

**POST** `/journal-entries/bulk-approve`

```json
{
  "journal_entry_ids": ["id1", "id2", "id3"],
  "force_approve": false,
  "reason": "Aprobación en lote"
}
```

#### 3. Contabilización Masiva

**POST** `/journal-entries/bulk-post`

```json
{
  "journal_entry_ids": ["id1", "id2", "id3"],
  "force_post": false,
  "reason": "Contabilización mensual"
}
```

#### 4. Cancelación Masiva

**POST** `/journal-entries/bulk-cancel`

```json
{
  "journal_entry_ids": ["id1", "id2", "id3"],
  "force_cancel": false,
  "reason": "Cancelación por error"
}
```

#### 5. Reversión Masiva

**POST** `/journal-entries/bulk-reverse`

```json
{
  "journal_entry_ids": ["id1", "id2", "id3"],
  "force_reverse": false,
  "reason": "Reversión de cierre"
}
```

#### 6. Reset a Borrador Masivo

**POST** `/journal-entries/bulk-reset-to-draft`

```json
{
  "journal_entry_ids": ["id1", "id2", "id3"],
  "force_reset": false,
  "reason": "Corrección requerida"
}
```

### Respuesta de Operaciones Masivas

Todas las operaciones masivas retornan una respuesta similar:

```json
{
  "total_requested": 5,
  "total_processed": 3,
  "total_succeeded": 2,
  "total_failed": 1,
  "succeeded_entries": [
    {
      "journal_entry_id": "id1",
      "journal_entry_number": "JE-2024-00001",
      "status": "POSTED"
    }
  ],
  "failed_entries": [
    {
      "journal_entry_id": "id2",
      "journal_entry_number": "JE-2024-00002",
      "errors": ["El asiento ya está contabilizado"],
      "warnings": []
    }
  ]
}
```

### Reset a Borrador Individual

**POST** `/journal-entries/{journal_entry_id}/reset-to-draft`

Regresa un asiento individual al estado borrador.

**Request Body:**
```json
{
  "reason": "Corrección requerida",
  "force_reset": false
}
```

## Reglas de Negocio

### Validaciones de Balance

- La suma de débitos debe ser igual a la suma de créditos
- Cada línea debe tener exactamente un valor: débito O crédito, no ambos
- Los montos deben ser positivos

### Flujo de Estados

1. **DRAFT**: Estado inicial, permite todas las modificaciones
2. **APPROVED**: Asiento validado, listo para contabilización
3. **POSTED**: Asiento contabilizado, afecta balances
4. **CANCELLED**: Asiento cancelado, no afecta balances

### Restricciones por Estado

- **DRAFT**: Se puede editar, eliminar, aprobar
- **APPROVED**: Se puede contabilizar, reset a borrador
- **POSTED**: Se puede cancelar (crea reversión), revertir
- **CANCELLED**: Solo lectura

### Auditoría

Todos los cambios de estado quedan registrados con:
- Usuario que realizó el cambio
- Fecha y hora del cambio
- Razón del cambio (cuando aplica)

## Códigos de Error Comunes

| Código | Descripción |
|--------|-------------|
| 400 | Validación de balance fallida |
| 403 | Sin permisos para crear/modificar asientos |
| 404 | Asiento contable no encontrado |
| 422 | Error de validación de datos |
| 500 | Error interno del servidor |

## Ejemplos de Integración

### Crear Asiento Completo

```python
import requests

# Crear asiento
response = requests.post(
    "https://api.contable.com/v1/journal-entries/",
    headers={"Authorization": "Bearer <token>"},
    json={
        "entry_date": "2024-12-01",
        "reference": "FACT-001",
        "description": "Venta a crédito",
        "lines": [
            {
                "account_id": "deudores-id",
                "debit_amount": 119.00,
                "description": "Cliente ABC"
            },
            {
                "account_id": "ventas-id",
                "credit_amount": 100.00,
                "description": "Venta productos"
            },
            {
                "account_id": "iva-id",
                "credit_amount": 19.00,
                "description": "IVA ventas"
            }
        ]
    }
)

asiento = response.json()
print(f"Asiento creado: {asiento['entry_number']}")

# Aprobar asiento
response = requests.post(
    f"https://api.contable.com/v1/journal-entries/{asiento['id']}/approve",
    headers={"Authorization": "Bearer <token>"}
)

# Contabilizar asiento
response = requests.post(
    f"https://api.contable.com/v1/journal-entries/{asiento['id']}/post",
    headers={"Authorization": "Bearer <token>"}
)
```

### Operación Masiva con Validación

```python
entry_ids = ["id1", "id2", "id3"]

# Validar antes de aprobar
validation_response = requests.post(
    "https://api.contable.com/v1/journal-entries/validate-approve",
    headers={"Authorization": "Bearer <token>"},
    json=entry_ids
)

validations = validation_response.json()
valid_ids = [v["journal_entry_id"] for v in validations if v["can_approve"]]

# Aprobar solo los válidos
if valid_ids:
    response = requests.post(
        "https://api.contable.com/v1/journal-entries/bulk-approve",
        headers={"Authorization": "Bearer <token>"},
        json={
            "journal_entry_ids": valid_ids,
            "reason": "Aprobación masiva validada"
        }
    )
```

## Mejores Prácticas

1. **Validar antes de operaciones masivas** usando los endpoints de validación
2. **Usar transacciones** para operaciones críticas
3. **Verificar permisos** antes de realizar cambios
4. **Incluir razones** en operaciones de cambio de estado
5. **Manejar errores** de balance y validación apropiadamente
6. **Usar paginación** para listas grandes de asientos
7. **Filtrar por fechas** para mejorar rendimiento en consultas
