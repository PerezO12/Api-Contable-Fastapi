# Endpoints de Flujo de Pagos - ACTUALIZADO con Operaciones Bulk

## Descripción General

Los endpoints de flujo de pagos implementan el proceso completo de gestión de pagos siguiendo las mejores prácticas contables modernas. Incluye confirmación individual y operaciones masivas (bulk).

## Flujo Principal de Pagos

### 1. Estado: DRAFT (Borrador)
- Pagos importados o creados manualmente
- Pueden ser editados, eliminados o confirmados
- Se pueden validar antes de confirmar

### 2. Estado: POSTED (Confirmado/Contabilizado)
- Se genera automáticamente el asiento contable
- Se concilian con facturas automáticamente
- Ya no se pueden editar (solo cancelar)

### 3. Estado: RECONCILED (Conciliado)
- Totalmente procesado y reconciliado
- Estado final del proceso

### 4. Estado: CANCELLED (Cancelado)
- Pago anulado
- Se revierten los asientos contables

---

## Endpoints Disponibles

### 📥 POST /payment-flow/import
Importar extracto bancario con auto-matching.

#### Request
```json
{
  "extract_name": "Extracto Banco Nacional - Enero 2025",
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "statement_date": "2025-01-30",
  "currency_code": "COP",
  "opening_balance": 1500000.00,
  "closing_balance": 1750000.00,
  "lines": [
    {
      "transaction_date": "2025-01-15",
      "value_date": "2025-01-15",
      "description": "PAGO FACTURA FV-001",
      "partner_name": "CLIENTE ABC S.A.S",
      "reference": "TRF-12345",
      "bank_reference": "REF-BANCO-67890",
      "debit_amount": 0.00,
      "credit_amount": 250000.00,
      "currency_code": "COP",
      "transaction_type": "CREDIT"
    }
  ]
}
```

#### Response (200 OK)
```json
{
  "extract_id": "456e7890-e89b-12d3-a456-426614174000",
  "extract_name": "Extracto Banco Nacional - Enero 2025",
  "total_lines": 10,
  "matched_lines": 8,
  "payments_created": 8,
  "auto_match_results": [
    {
      "line_id": "789e0123-e89b-12d3-a456-426614174000",
      "line_description": "PAGO FACTURA FV-001",
      "line_amount": 250000.00,
      "matched": true,
      "payment_created": true,
      "invoice_id": "abc1234-e89b-12d3-a456-426614174000",
      "payment_id": "def5678-e89b-12d3-a456-426614174000",
      "match_reason": "Exact amount and partner match",
      "errors": []
    }
  ]
}
```

---

### ✅ POST /payment-flow/validate-confirmation
Validar si múltiples pagos pueden ser confirmados.

#### Request
```json
{
  "payment_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ]
}
```

#### Response (200 OK)
```json
{
  "total_payments": 2,
  "can_confirm_count": 1,
  "blocked_count": 1,
  "warnings_count": 1,
  "validation_results": [
    {
      "payment_id": "123e4567-e89b-12d3-a456-426614174000",
      "payment_number": "PAY-2025-001",
      "can_confirm": true,
      "blocking_reasons": [],
      "warnings": ["Payment has no partner assigned"],
      "requires_confirmation": true
    },
    {
      "payment_id": "456e7890-e89b-12d3-a456-426614174000",
      "payment_number": "PAY-2025-002",
      "can_confirm": false,
      "blocking_reasons": ["Payment must have a positive amount"],
      "warnings": [],
      "requires_confirmation": true
    }
  ]
}
```

---

### 🚀 POST /payment-flow/bulk-confirm
Confirmar múltiples pagos en lote (DRAFT → POSTED).

#### Request
```json
{
  "payment_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ],
  "confirmation_notes": "Confirmación masiva de pagos enero 2025"
}
```

#### Query Parameters
- `force` (boolean, opcional): Si es `true`, ignora advertencias y procesa pagos con warnings

#### Response (200 OK)
```json
{
  "operation": "bulk_confirm",
  "total_payments": 2,
  "successful": 1,
  "failed": 1,
  "results": [
    {
      "payment_id": "123e4567-e89b-12d3-a456-426614174000",
      "payment_number": "PAY-2025-001",
      "success": true,
      "message": "Payment confirmed successfully",
      "error": null
    },
    {
      "payment_id": "456e7890-e89b-12d3-a456-426614174000",
      "payment_number": "PAY-2025-002",
      "success": false,
      "message": "Validation failed",
      "error": "Payment must have a positive amount"
    }
  ],
  "summary": "Confirmed 1 payments successfully, 1 payments failed"
}
```

---

### ✅ POST /payment-flow/confirm/{payment_id}
Confirmar pago individual (DRAFT → POSTED).

#### Path Parameters
- `payment_id` (UUID): ID del pago a confirmar

#### Request
```json
{
  "payment_id": "123e4567-e89b-12d3-a456-426614174000",
  "confirmation_notes": "Confirmación manual del pago"
}
```

#### Response (200 OK)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "number": "PAY-2025-001",
  "reference": "TRF-12345",
  "payment_type": "customer_payment",
  "payment_method": "bank_transfer",
  "status": "posted",
  "third_party_id": "789e0123-e89b-12d3-a456-426614174000",
  "payment_date": "2025-01-15",
  "amount": 250000.00,
  "allocated_amount": 250000.00,
  "unallocated_amount": 0.00,
  "currency_code": "COP",
  "exchange_rate": 1.0,
  "account_id": "abc1234-e89b-12d3-a456-426614174000",
  "description": "Auto-generated from bank extract: PAGO FACTURA FV-001",
  "is_fully_allocated": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T14:45:00Z"
}
```

---

### ❌ POST /payment-flow/bulk-cancel
Cancelar múltiples pagos en lote.

#### Request
```json
{
  "payment_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ],
  "cancellation_reason": "Pagos duplicados identificados"
}
```

#### Response (200 OK)
```json
{
  "operation": "bulk_cancel",
  "total_payments": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "payment_id": "123e4567-e89b-12d3-a456-426614174000",
      "payment_number": "PAY-2025-001",
      "success": true,
      "message": "Payment cancelled successfully",
      "error": null
    },
    {
      "payment_id": "456e7890-e89b-12d3-a456-426614174000",
      "payment_number": "PAY-2025-002",
      "success": true,
      "message": "Payment cancelled successfully",
      "error": null
    }
  ],
  "summary": "Cancelled 2 payments successfully"
}
```

---

### 🗑️ POST /payment-flow/bulk-delete
Eliminar múltiples pagos en lote (solo DRAFT).

#### Request
```json
{
  "payment_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ]
}
```

#### Query Parameters
- `force` (boolean, opcional): Si es `true`, permite eliminar pagos que no están en DRAFT

#### Response (200 OK)
```json
{
  "operation": "bulk_delete",
  "total_payments": 2,
  "successful": 1,
  "failed": 1,
  "results": [
    {
      "payment_id": "123e4567-e89b-12d3-a456-426614174000",
      "payment_number": "PAY-2025-001",
      "success": true,
      "message": "Payment deleted successfully",
      "error": null
    },
    {
      "payment_id": "456e7890-e89b-12d3-a456-426614174000",
      "payment_number": "PAY-2025-002",
      "success": false,
      "message": "Cannot delete non-draft payment",
      "error": "Payment in status posted cannot be deleted. Use force=true to override."
    }
  ],
  "summary": "Deleted 1 payments successfully, 1 payments failed"
}
```

---

### 📊 GET /payment-flow/status/{extract_id}
Obtener estado del flujo de pagos para un extracto.

#### Path Parameters
- `extract_id` (UUID): ID del extracto bancario

#### Response (200 OK)
```json
{
  "extract_id": "456e7890-e89b-12d3-a456-426614174000",
  "extract_name": "Extracto Banco Nacional - Enero 2025",
  "extract_status": "imported",
  "total_lines": 10,
  "matched_lines": 8,
  "draft_payments": 3,
  "posted_payments": 5,
  "unmatched_lines": 2,
  "completion_percentage": 80.0
}
```

---

### 📝 GET /payment-flow/drafts
Obtener pagos en borrador pendientes de confirmación.

#### Query Parameters
- `limit` (int, opcional): Límite de resultados (default: 50)
- `offset` (int, opcional): Offset para paginación (default: 0)
- `third_party_id` (UUID, opcional): Filtrar por tercero

#### Response (200 OK)
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "number": "PAY-2025-003",
    "reference": "TRF-98765",
    "payment_type": "customer_payment",
    "status": "draft",
    "payment_date": "2025-01-16",
    "amount": 150000.00,
    "currency_code": "COP",
    "third_party_id": "789e0123-e89b-12d3-a456-426614174000",
    "created_at": "2025-01-16T09:15:00Z"
  }
]
```

---

### 📈 GET /payment-flow/pending-reconciliation
Resumen de pagos pendientes de conciliación.

#### Response (200 OK)
```json
{
  "draft_payments": 15,
  "unmatched_extract_lines": 8,
  "draft_matches": 12,
  "total_pending": 23
}
```

---

## Flujo de Trabajo Recomendado

### 1. Importación de Extracto
```http
POST /payment-flow/import
```
- Importa extracto bancario
- Auto-matching automático con facturas
- Crea pagos en estado DRAFT

### 2. Revisión y Validación
```http
POST /payment-flow/validate-confirmation
```
- Valida que los pagos pueden ser confirmados
- Identifica problemas antes de procesar

### 3. Confirmación Masiva
```http
POST /payment-flow/bulk-confirm
```
- Confirma múltiples pagos simultaneamente
- Genera asientos contables automáticamente
- Concilia con facturas

### 4. Monitoreo del Estado
```http
GET /payment-flow/status/{extract_id}
```
- Supervisa el progreso del proceso
- Identifica pagos pendientes

## Estados de Pago y Transiciones

```
DRAFT ──────→ POSTED ──────→ RECONCILED
  │              │
  │              ↓
  └──────→ CANCELLED
```

### Operaciones Permitidas por Estado

| Estado | Editar | Confirmar | Cancelar | Eliminar |
|--------|--------|-----------|----------|----------|
| DRAFT | ✅ | ✅ | ✅ | ✅ |
| POSTED | ❌ | ❌ | ✅ | ❌* |
| RECONCILED | ❌ | ❌ | ❌ | ❌ |
| CANCELLED | ❌ | ❌ | ❌ | ❌* |

*Solo con `force=true`

## Códigos de Error

### 400 Bad Request
- Datos de validación incorrectos
- Estados incompatibles para la operación
- Límites de operaciones bulk excedidos

### 404 Not Found
- Pago no encontrado
- Extracto no encontrado

### 500 Internal Server Error
- Errores de base de datos
- Fallos en generación de asientos contables

## Consideraciones de Rendimiento

- **Operaciones Bulk**: Máximo 100 pagos por operación
- **Timeout**: Operaciones grandes pueden tardar varios minutos
- **Transacciones**: Cada operación bulk se ejecuta en una transacción
- **Rollback**: Si una operación falla, se revierten todos los cambios

## Seguridad y Permisos

- **Crear/Importar**: Rol CONTADOR o superior
- **Confirmar**: Rol CONTADOR o superior  
- **Cancelar**: Rol ADMIN o superior
- **Eliminar**: Rol ADMIN únicamente

## Integración con Otros Módulos

### Con Facturas
- Auto-matching por monto y tercero
- Actualización automática de estados de factura
- Conciliación automática de cuentas por cobrar/pagar

### Con Contabilidad
- Generación automática de asientos contables
- Uso de diarios de banco configurados
- Respeto de plan de cuentas establecido

### Con Terceros
- Búsqueda automática por nombre comercial
- Validación de cuentas contables de terceros
- Actualización de balances de cuentas
