# Endpoints de Asientos Contables

Este documento detalla todos los endpoints disponibles para la gestión de asientos contables en el API Contable.

## 📋 Resumen de Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/journal-entries/` | Crear nuevo asiento contable |
| GET | `/journal-entries/` | Listar asientos contables con filtros |
| GET | `/journal-entries/{id}` | Obtener asiento por ID |
| PUT | `/journal-entries/{id}` | Actualizar asiento (solo borradores) |
| DELETE | `/journal-entries/{id}` | Eliminar asiento (solo borradores) |
| POST | `/journal-entries/{id}/approve` | Aprobar asiento |
| POST | `/journal-entries/{id}/post` | Contabilizar asiento |
| POST | `/journal-entries/{id}/cancel` | Cancelar asiento |
| POST | `/journal-entries/{id}/reverse` | Crear asiento de reversión |
| GET | `/journal-entries/statistics/summary` | Obtener estadísticas |
| GET | `/journal-entries/search` | Búsqueda avanzada |
| POST | `/journal-entries/bulk-create` | Crear múltiples asientos |
| GET | `/journal-entries/by-number/{number}` | Obtener asiento por número |

## 📝 Detalle de Endpoints

### 📄 POST /journal-entries/

Crea un nuevo asiento contable.

#### Permisos Requeridos
- El usuario debe tener el permiso `can_create_entries`

#### Request
```json
{
  "entry_date": "2025-06-15",
  "reference": "FAC-12345",
  "description": "Registro de venta a cliente XYZ",
  "entry_type": "manual",
  "notes": "Venta al contado",
  "lines": [
    {
      "account_id": "12345678-1234-1234-1234-123456789012",
      "description": "Ingreso por venta de mercancía",
      "debit_amount": 0,
      "credit_amount": 1000.00,
      "reference": "Factura 12345"
    },
    {
      "account_id": "87654321-4321-4321-4321-987654321098",
      "description": "Cobro por venta de mercancía",
      "debit_amount": 1000.00,
      "credit_amount": 0,
      "reference": "Factura 12345"
    }
  ]
}
```

#### Schema de Request
```python
class JournalEntryCreate(JournalEntryBase):
    """Schema para crear asientos contables"""
    lines: List[JournalEntryLineCreate] = Field(..., min_length=2, description="Líneas del asiento (mínimo 2)")
```

#### Response Exitosa (201)
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "number": "JE-2025-000001",
  "entry_date": "2025-06-15",
  "reference": "FAC-12345",
  "description": "Registro de venta a cliente XYZ",
  "entry_type": "manual",
  "status": "draft",
  "total_debit": 1000.00,
  "total_credit": 1000.00,
  "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "created_at": "2025-06-15T10:30:00Z",
  "updated_at": "2025-06-15T10:30:00Z",
  "is_balanced": true,
  "can_be_posted": false,
  "can_be_edited": true,
  "created_by_name": "Juan Pérez",
  "notes": "Venta al contado"
}
```

#### Códigos de Error
- `400 Bad Request`: Validación fallida (desbalance, montos negativos, etc.)
- `403 Forbidden`: Usuario sin permisos
- `404 Not Found`: Cuenta no encontrada
- `422 Unprocessable Entity`: Error de validación de datos

---

### 📋 GET /journal-entries/

Obtiene una lista paginada de asientos contables con opciones de filtrado.

#### Parámetros de Query
- `skip` (int, opcional): Número de registros a saltar (default: 0)
- `limit` (int, opcional): Número máximo de registros a retornar (default: 100)
- `status` (string, opcional): Filtrar por estado (`draft`, `pending`, `approved`, `posted`, `cancelled`)
- `account_id` (UUID, opcional): Filtrar por cuenta
- `date_from` (date, opcional): Filtrar desde fecha
- `date_to` (date, opcional): Filtrar hasta fecha
- `reference` (string, opcional): Filtrar por referencia

#### Response Exitosa (200)
```json
{
  "items": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "number": "JE-2025-000001",
      "entry_date": "2025-06-15",
      "reference": "FAC-12345",
      "description": "Registro de venta a cliente XYZ",
      "status": "draft",
      "entry_type": "manual",
      "total_debit": 1000.00,
      "created_by_name": "Juan Pérez",
      "created_at": "2025-06-15T10:30:00Z"
    },
    {
      "id": "d47ac10b-58cc-4372-a567-0e02b2c3d123",
      "number": "JE-2025-000002",
      "entry_date": "2025-06-16",
      "reference": "FAC-12346",
      "description": "Registro de compra a proveedor ABC",
      "status": "posted",
      "entry_type": "manual",
      "total_debit": 500.00,
      "created_by_name": "María Rodríguez",
      "created_at": "2025-06-16T09:15:00Z"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 100
}
```

---

### 🔍 GET /journal-entries/{journal_entry_id}

Obtiene un asiento contable por su ID, incluyendo todas las líneas de detalle.

#### Parámetros de Path
- `journal_entry_id` (UUID): ID del asiento contable

#### Response Exitosa (200)
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "number": "JE-2025-000001",
  "entry_date": "2025-06-15",
  "reference": "FAC-12345",
  "description": "Registro de venta a cliente XYZ",
  "entry_type": "manual",
  "status": "draft",
  "total_debit": 1000.00,
  "total_credit": 1000.00,
  "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "created_at": "2025-06-15T10:30:00Z",
  "updated_at": "2025-06-15T10:30:00Z",
  "is_balanced": true,
  "can_be_posted": false,
  "can_be_edited": true,
  "created_by_name": "Juan Pérez",
  "notes": "Venta al contado",
  "lines": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "journal_entry_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "account_id": "12345678-1234-1234-1234-123456789012",
      "description": "Ingreso por venta de mercancía",
      "debit_amount": 0,
      "credit_amount": 1000.00,
      "line_number": 1,
      "created_at": "2025-06-15T10:30:00Z",
      "updated_at": "2025-06-15T10:30:00Z",
      "account_code": "4.1.01",
      "account_name": "Ingresos por Ventas",
      "amount": 1000.00,
      "movement_type": "credit",
      "reference": "Factura 12345"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f1234567890a",
      "journal_entry_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "account_id": "87654321-4321-4321-4321-987654321098",
      "description": "Cobro por venta de mercancía",
      "debit_amount": 1000.00,
      "credit_amount": 0,
      "line_number": 2,
      "created_at": "2025-06-15T10:30:00Z",
      "updated_at": "2025-06-15T10:30:00Z",
      "account_code": "1.1.01",
      "account_name": "Caja General",
      "amount": 1000.00,
      "movement_type": "debit",
      "reference": "Factura 12345"
    }
  ]
}
```

#### Códigos de Error
- `404 Not Found`: Asiento no encontrado

---

### ✏️ PUT /journal-entries/{journal_entry_id}

Actualiza un asiento contable existente (solo si está en estado borrador).

#### Parámetros de Path
- `journal_entry_id` (UUID): ID del asiento contable

#### Permisos Requeridos
- El usuario debe tener el permiso `can_create_entries`

#### Request
```json
{
  "entry_date": "2025-06-16",
  "reference": "FAC-12345-CORREGIDO",
  "description": "Registro de venta a cliente XYZ (corregido)",
  "notes": "Venta al contado - corregido"
}
```

#### Schema de Request
```python
class JournalEntryUpdate(BaseModel):
    """Schema para actualizar asientos contables (solo borradores)"""
    entry_date: Optional[date] = None
    reference: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)
```

#### Response Exitosa (200)
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "number": "JE-2025-000001",
  "entry_date": "2025-06-16",
  "reference": "FAC-12345-CORREGIDO",
  "description": "Registro de venta a cliente XYZ (corregido)",
  "entry_type": "manual",
  "status": "draft",
  "total_debit": 1000.00,
  "total_credit": 1000.00,
  "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "created_at": "2025-06-15T10:30:00Z",
  "updated_at": "2025-06-15T11:45:00Z",
  "is_balanced": true,
  "can_be_posted": false,
  "can_be_edited": true,
  "created_by_name": "Juan Pérez",
  "notes": "Venta al contado - corregido"
}
```

#### Códigos de Error
- `403 Forbidden`: Usuario sin permisos
- `404 Not Found`: Asiento no encontrado
- `422 Unprocessable Entity`: Error de validación o asiento no editable

---

### 🗑️ DELETE /journal-entries/{journal_entry_id}

Elimina un asiento contable (solo si está en estado borrador).

#### Parámetros de Path
- `journal_entry_id` (UUID): ID del asiento contable

#### Permisos Requeridos
- El usuario debe tener el permiso `can_create_entries`

#### Response Exitosa (204)
Sin contenido

#### Códigos de Error
- `403 Forbidden`: Usuario sin permisos
- `404 Not Found`: Asiento no encontrado
- `422 Unprocessable Entity`: Asiento no eliminable (no está en borrador)

---

### ✅ POST /journal-entries/{journal_entry_id}/approve

Aprueba un asiento contable para su posterior contabilización.

#### Parámetros de Path
- `journal_entry_id` (UUID): ID del asiento contable

#### Permisos Requeridos
- El usuario debe tener el permiso `can_create_entries`

#### Response Exitosa (200)
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "number": "JE-2025-000001",
  "entry_date": "2025-06-16",
  "reference": "FAC-12345",
  "description": "Registro de venta a cliente XYZ",
  "entry_type": "manual",
  "status": "approved",
  "total_debit": 1000.00,
  "total_credit": 1000.00,
  "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "approved_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "created_at": "2025-06-15T10:30:00Z",
  "updated_at": "2025-06-15T11:45:00Z",
  "is_balanced": true,
  "can_be_posted": true,
  "can_be_edited": false,
  "created_by_name": "Juan Pérez",
  "notes": "Venta al contado"
}
```

#### Códigos de Error
- `403 Forbidden`: Usuario sin permisos
- `404 Not Found`: Asiento no encontrado
- `422 Unprocessable Entity`: Errores de validación o asiento no aprobable

---

### 📊 POST /journal-entries/{journal_entry_id}/post

Contabiliza un asiento aprobado, afectando los saldos de las cuentas involucradas.

#### Parámetros de Path
- `journal_entry_id` (UUID): ID del asiento contable

#### Permisos Requeridos
- El usuario debe tener el permiso `can_create_entries`

#### Request
```json
{
  "reason": "Contabilizado después de verificar documentación"
}
```

#### Schema de Request
```python
class JournalEntryPost(BaseModel):
    """Schema para contabilizar asiento"""
    reason: Optional[str] = Field(None, max_length=500, description="Razón para contabilizar")
```

#### Response Exitosa (200)
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "number": "JE-2025-000001",
  "entry_date": "2025-06-16",
  "reference": "FAC-12345",
  "description": "Registro de venta a cliente XYZ",
  "entry_type": "manual",
  "status": "posted",
  "total_debit": 1000.00,
  "total_credit": 1000.00,
  "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "approved_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "posted_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "created_at": "2025-06-15T10:30:00Z",
  "updated_at": "2025-06-15T11:45:00Z",
  "posted_at": "2025-06-15T12:00:00Z",
  "is_balanced": true,
  "can_be_posted": false,
  "can_be_edited": false,
  "created_by_name": "Juan Pérez",
  "posted_by_name": "Juan Pérez",
  "notes": "Venta al contado\n\nContabilizado: Contabilizado después de verificar documentación"
}
```

#### Códigos de Error
- `403 Forbidden`: Usuario sin permisos
- `404 Not Found`: Asiento no encontrado
- `422 Unprocessable Entity`: Asiento no contabilizable o desbalanceado

---

### ❌ POST /journal-entries/{journal_entry_id}/cancel

Cancela un asiento contable (con o sin reversión automática).

#### Parámetros de Path
- `journal_entry_id` (UUID): ID del asiento contable

#### Permisos Requeridos
- El usuario debe tener el permiso `can_create_entries`

#### Request
```json
{
  "reason": "Cancelado por error en factura"
}
```

#### Schema de Request
```python
class JournalEntryCancel(BaseModel):
    """Schema para cancelar asiento"""
    reason: str = Field(..., min_length=1, max_length=500, description="Razón para cancelar")
```

#### Response Exitosa (200)
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "number": "JE-2025-000001",
  "entry_date": "2025-06-16",
  "reference": "FAC-12345",
  "description": "Registro de venta a cliente XYZ",
  "entry_type": "manual",
  "status": "cancelled",
  "total_debit": 1000.00,
  "total_credit": 1000.00,
  "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "approved_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "posted_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "cancelled_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "created_at": "2025-06-15T10:30:00Z",
  "updated_at": "2025-06-15T11:45:00Z",
  "posted_at": "2025-06-15T12:00:00Z",
  "cancelled_at": "2025-06-15T14:30:00Z",
  "is_balanced": true,
  "can_be_posted": false,
  "can_be_edited": false,
  "created_by_name": "Juan Pérez",
  "posted_by_name": "Juan Pérez",
  "notes": "Venta al contado\n\nCancelado: Cancelado por error en factura"
}
```

#### Códigos de Error
- `403 Forbidden`: Usuario sin permisos
- `404 Not Found`: Asiento no encontrado
- `422 Unprocessable Entity`: Error en proceso de cancelación o asiento ya cancelado

---

### ↩️ POST /journal-entries/{journal_entry_id}/reverse

Crea un asiento de reversión a partir de un asiento existente.

#### Parámetros de Path
- `journal_entry_id` (UUID): ID del asiento contable a revertir

#### Parámetros de Query
- `reason` (string): Razón para la reversión (obligatorio)

#### Permisos Requeridos
- El usuario debe tener el permiso `can_create_entries`

#### Response Exitosa (200)
```json
{
  "id": "g58bd21c-69dd-5483-b678-1f13c3d4580",
  "number": "JE-2025-000003",
  "entry_date": "2025-06-16",
  "reference": "REV-JE-2025-000001",
  "description": "Reversión de asiento JE-2025-000001",
  "entry_type": "reversal",
  "status": "posted",
  "total_debit": 1000.00,
  "total_credit": 1000.00,
  "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "approved_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "posted_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "created_at": "2025-06-16T09:30:00Z",
  "updated_at": "2025-06-16T09:30:00Z",
  "posted_at": "2025-06-16T09:30:00Z",
  "is_balanced": true,
  "can_be_posted": false,
  "can_be_edited": false,
  "created_by_name": "Juan Pérez",
  "posted_by_name": "Juan Pérez",
  "notes": "Cancelado por error en factura"
}
```

#### Códigos de Error
- `403 Forbidden`: Usuario sin permisos
- `404 Not Found`: Asiento original no encontrado
- `422 Unprocessable Entity`: Error en proceso de reversión

---

### 📊 GET /journal-entries/statistics/summary

Obtiene estadísticas resumidas de asientos contables.

#### Parámetros de Query
- `date_from` (date, opcional): Estadísticas desde fecha
- `date_to` (date, opcional): Estadísticas hasta fecha

#### Response Exitosa (200)
```json
{
  "total_entries": 125,
  "draft_entries": 15,
  "approved_entries": 10,
  "posted_entries": 95,
  "cancelled_entries": 5,
  "total_debit_amount": "240500.00",
  "total_credit_amount": "240500.00",
  "entries_this_month": 45,
  "entries_this_year": 125
}
```

---

### 🔍 GET /journal-entries/search

Búsqueda avanzada de asientos contables con múltiples filtros.

#### Parámetros de Query
Cualquier combinación de los siguientes:
- `start_date` (date): Desde fecha
- `end_date` (date): Hasta fecha
- `status` (string): Estado del asiento
- `entry_type` (string): Tipo de asiento
- `account_id` (UUID): Filtrar por cuenta específica
- `created_by_id` (UUID): Filtrar por creador
- `search` (string): Texto libre para buscar en descripción/referencia

#### Response Exitosa (200)
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "number": "JE-2025-000001",
    "entry_date": "2025-06-15",
    "reference": "FAC-12345",
    "description": "Registro de venta a cliente XYZ",
    "status": "posted",
    "entry_type": "manual",
    "total_debit": 1000.00,
    "created_by_name": "Juan Pérez",
    "created_at": "2025-06-15T10:30:00Z"
  },
  {
    "id": "d47ac10b-58cc-4372-a567-0e02b2c3d123",
    "number": "JE-2025-000002",
    "entry_date": "2025-06-16",
    "reference": "FAC-12346",
    "description": "Registro de compra a proveedor ABC",
    "status": "posted",
    "entry_type": "manual",
    "total_debit": 500.00,
    "created_by_name": "María Rodríguez",
    "created_at": "2025-06-16T09:15:00Z"
  }
]
```

---

### 📦 POST /journal-entries/bulk-create

Crea múltiples asientos contables en una sola operación.

#### Permisos Requeridos
- El usuario debe tener el permiso `can_create_entries`

#### Request
```json
[
  {
    "entry_date": "2025-06-15",
    "reference": "FAC-12345",
    "description": "Registro de venta a cliente XYZ",
    "entry_type": "manual",
    "notes": "Venta al contado",
    "lines": [
      {
        "account_id": "12345678-1234-1234-1234-123456789012",
        "description": "Ingreso por venta de mercancía",
        "debit_amount": 0,
        "credit_amount": 1000.00,
        "reference": "Factura 12345"
      },
      {
        "account_id": "87654321-4321-4321-4321-987654321098",
        "description": "Cobro por venta de mercancía",
        "debit_amount": 1000.00,
        "credit_amount": 0,
        "reference": "Factura 12345"
      }
    ]
  },
  {
    "entry_date": "2025-06-16",
    "reference": "FAC-12346",
    "description": "Registro de compra a proveedor ABC",
    "entry_type": "manual",
    "notes": "Compra a crédito",
    "lines": [
      {
        "account_id": "23456789-2345-2345-2345-234567890123",
        "description": "Compra de inventario",
        "debit_amount": 500.00,
        "credit_amount": 0,
        "reference": "Factura Prov-987"
      },
      {
        "account_id": "34567890-3456-3456-3456-345678901234",
        "description": "Cuenta por pagar",
        "debit_amount": 0,
        "credit_amount": 500.00,
        "reference": "Factura Prov-987"
      }
    ]
  }
]
```

#### Response Exitosa (200)
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "number": "JE-2025-000001",
    "entry_date": "2025-06-15",
    "reference": "FAC-12345",
    "description": "Registro de venta a cliente XYZ",
    "entry_type": "manual",
    "status": "draft",
    "total_debit": 1000.00,
    "total_credit": 1000.00,
    "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
    "created_at": "2025-06-15T10:30:00Z",
    "updated_at": "2025-06-15T10:30:00Z",
    "is_balanced": true,
    "can_be_posted": false,
    "can_be_edited": true,
    "created_by_name": "Juan Pérez",
    "notes": "Venta al contado"
  },
  {
    "id": "d47ac10b-58cc-4372-a567-0e02b2c3d123",
    "number": "JE-2025-000002",
    "entry_date": "2025-06-16",
    "reference": "FAC-12346",
    "description": "Registro de compra a proveedor ABC",
    "entry_type": "manual",
    "status": "draft",
    "total_debit": 500.00,
    "total_credit": 500.00,
    "created_by_id": "abcdef12-3456-7890-abcd-ef1234567890",
    "created_at": "2025-06-15T10:30:00Z",
    "updated_at": "2025-06-15T10:30:00Z",
    "is_balanced": true,
    "can_be_posted": false,
    "can_be_edited": true,
    "created_by_name": "Juan Pérez",
    "notes": "Compra a crédito"
  }
]
```

#### Códigos de Error
- `400 Bad Request`: Validación fallida en algún asiento
- `403 Forbidden`: Usuario sin permisos
- `422 Unprocessable Entity`: Error en la validación de algún asiento

---

### 🔢 GET /journal-entries/by-number/{entry_number}

Obtiene un asiento contable por su número.

#### Parámetros de Path
- `entry_number` (string): Número del asiento contable (ej. "JE-2025-000001")

#### Response Exitosa (200)
Igual que GET /journal-entries/{id} pero con búsqueda por número.

#### Códigos de Error
- `404 Not Found`: Asiento no encontrado

---

## 🔄 Flujos de Trabajo Comunes

### Ciclo Completo de un Asiento

1. **Creación**:
   - `POST /journal-entries/` para crear el asiento en borrador

2. **Revisión y Aprobación**:
   - `PUT /journal-entries/{id}` para ajustes si es necesario
   - `POST /journal-entries/{id}/approve` para aprobar el asiento

3. **Contabilización**:
   - `POST /journal-entries/{id}/post` para contabilizar el asiento

4. **En caso de error**:
   - `POST /journal-entries/{id}/cancel` para cancelar el asiento
   - `POST /journal-entries/{id}/reverse` para crear una reversión

### Importación Masiva

1. **Carga Inicial**:
   - `POST /journal-entries/bulk-create` con múltiples asientos

2. **Procesamiento por Lotes**:
   - Aprobación y contabilización individual o usar scripts de backend

## 🔐 Seguridad y Permisos

Los endpoints de asientos contables requieren diferentes niveles de permiso:

- **Lectura/Consulta**: Todos los usuarios con acceso al módulo contable
- **Creación/Edición**: Usuarios con permiso `can_create_entries`
- **Cancelación/Reversión**: Usuarios con permiso `can_create_entries` (generalmente restringido a administradores)

## 🛠️ Consideraciones Técnicas

- Todas las operaciones son transaccionales para mantener integridad de datos
- Las respuestas incluyen campos calculados como `is_balanced`, `can_be_posted`, etc.
- El sistema mantiene registro detallado de auditoría en cada operación
- Se aplican validaciones estrictas para garantizar la integridad contable

## 🔄 Integración con Otros Módulos

- Los asientos contables están vinculados con **cuentas contables** y afectan sus saldos
- Las operaciones de contabilización actualizan los **movimientos de cuentas**
- Los **reportes financieros** consultan la información de asientos contabilizados
- El sistema de **usuarios** valida permisos y registra la auditoría
