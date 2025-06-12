# Bulk Deletion Endpoints - Journal Entries

## 🔍 POST /journal-entries/validate-deletion

Valida múltiples asientos contables para eliminación sin realizar la eliminación real.

### Permisos Requeridos
- El usuario debe tener el permiso `can_delete_entries`

### Request
```json
{
  "entry_ids": [
    "12345678-1234-1234-1234-123456789012",
    "87654321-4321-4321-4321-210987654321"
  ]
}
```

### Response
```json
[
  {
    "journal_entry_id": "12345678-1234-1234-1234-123456789012",
    "journal_entry_number": "JE-2025-001",
    "can_delete": true,
    "errors": [],
    "warnings": []
  },
  {
    "journal_entry_id": "87654321-4321-4321-4321-210987654321",
    "journal_entry_number": "JE-2025-002",
    "can_delete": false,
    "errors": ["Solo se pueden eliminar asientos en estado BORRADOR"],
    "warnings": []
  }
]
```

### Validaciones
- Los asientos deben existir
- Solo se pueden eliminar asientos en estado `DRAFT`
- Se generan advertencias para:
  - Asientos de apertura o cierre
  - Asientos con montos altos (>50,000)
  - Asientos antiguos (>30 días)

---

## 🗑️ POST /journal-entries/bulk-delete

Elimina múltiples asientos contables en una sola operación.

### Permisos Requeridos
- El usuario debe tener el permiso `can_delete_entries`

### Request
```json
{
  "entry_ids": [
    "12345678-1234-1234-1234-123456789012",
    "87654321-4321-4321-4321-210987654321"
  ],
  "force_delete": false,
  "reason": "Corrección de asientos erróneos del periodo anterior"
}
```

### Parámetros
- `entry_ids`: Array de UUIDs de asientos a eliminar (requerido, mínimo 1)
- `force_delete`: Booleano para forzar eliminación a pesar de advertencias (opcional, default: false)
- `reason`: Motivo de la eliminación para auditoría (opcional)

### Response
```json
{
  "total_requested": 2,
  "total_deleted": 1,
  "total_failed": 1,
  "deleted_entries": [
    {
      "journal_entry_id": "12345678-1234-1234-1234-123456789012",
      "journal_entry_number": "JE-2025-001",
      "can_delete": true,
      "errors": [],
      "warnings": []
    }
  ],
  "failed_entries": [
    {
      "journal_entry_id": "87654321-4321-4321-4321-210987654321",
      "journal_entry_number": "JE-2025-002",
      "can_delete": false,
      "errors": ["Solo se pueden eliminar asientos en estado BORRADOR"],
      "warnings": []
    }
  ],
  "errors": [],
  "warnings": [
    "Asiento JE-2025-001 eliminado: Corrección de asientos erróneos del periodo anterior"
  ]
}
```

### Características
- **Transaccional**: Si hay errores en el proceso, se hace rollback
- **Validación previa**: Valida cada asiento antes de eliminarlo
- **Auditoría**: Registra todas las eliminaciones con motivo
- **Manejo de errores**: Continúa con otros asientos si uno falla

---

## 🔧 POST /journal-entries/bulk-operation

Endpoint unificado para operaciones masivas en asientos contables.

### Permisos Requeridos
- Según la operación:
  - `delete`: Requiere `can_delete_entries`
  - `approve`: Requiere `can_approve_entries`
  - `cancel`: Requiere `can_cancel_entries`

### Request para Eliminación
```json
{
  "operation": "delete",
  "entry_ids": [
    "12345678-1234-1234-1234-123456789012",
    "87654321-4321-4321-4321-210987654321"
  ],
  "operation_data": {
    "force_delete": true,
    "reason": "Eliminación masiva por corrección contable"
  }
}
```

### Request para Aprobación
```json
{
  "operation": "approve",
  "entry_ids": [
    "12345678-1234-1234-1234-123456789012"
  ],
  "operation_data": {
    "approved_by_id": "user-uuid-here"
  }
}
```

### Request para Cancelación
```json
{
  "operation": "cancel",
  "entry_ids": [
    "12345678-1234-1234-1234-123456789012"
  ],
  "operation_data": {
    "cancelled_by_id": "user-uuid-here",
    "reason": "Cancelación por solicitud del cliente"
  }
}
```

### Response para Eliminación
```json
{
  "operation": "delete",
  "result": {
    "total_requested": 2,
    "total_deleted": 2,
    "total_failed": 0,
    "deleted_entries": [...],
    "failed_entries": [],
    "errors": [],
    "warnings": []
  }
}
```

### Response para Aprobación/Cancelación
```json
{
  "operation": "approve",
  "approved_count": 5,
  "failed_count": 1,
  "errors": [
    "Error aprobando 87654321-4321-4321-4321-210987654321: Asiento ya está aprobado"
  ]
}
```

### Operaciones Soportadas
- `delete`: Eliminación masiva
- `approve`: Aprobación masiva (futuro)
- `cancel`: Cancelación masiva (futuro)

---

## 🔒 Seguridad y Validaciones

### Validaciones de Eliminación

Los asientos solo pueden eliminarse si cumplen estas condiciones:

1. **Estado**: Debe estar en estado `DRAFT` (Borrador)
2. **Existencia**: El asiento debe existir en la base de datos
3. **Permisos**: El usuario debe tener permisos de eliminación

### Advertencias de Eliminación

Se generan advertencias (que pueden ser ignoradas con `force_delete: true`) para:

- **Asientos de apertura/cierre**: Detectados por palabras clave en la descripción
- **Montos altos**: Asientos con totales > 50,000
- **Asientos antiguos**: Creados hace más de 30 días

### Auditoría

Todas las eliminaciones se registran con:
- ID del usuario que realizó la acción
- Timestamp de la operación
- Motivo de la eliminación
- Detalles de los asientos eliminados

## 📊 Códigos de Respuesta

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 400 | Error de validación o datos inválidos |
| 401 | No autenticado |
| 403 | Sin permisos suficientes |
| 404 | Asiento no encontrado |
| 422 | Error de validación de esquema |
| 500 | Error interno del servidor |

## 📝 Ejemplos de Uso

### Flujo Completo de Eliminación Masiva

```bash
# 1. Validar asientos antes de eliminar
curl -X POST "http://api.ejemplo.com/api/v1/journal-entries/validate-deletion" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_ids": ["uuid1", "uuid2", "uuid3"]
  }'

# 2. Eliminar solo los asientos válidos
curl -X POST "http://api.ejemplo.com/api/v1/journal-entries/bulk-delete" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_ids": ["uuid1", "uuid3"],
    "force_delete": false,
    "reason": "Corrección de errores detectados en revisión"
  }'
```

### Eliminación Forzada con Advertencias

```bash
curl -X POST "http://api.ejemplo.com/api/v1/journal-entries/bulk-delete" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_ids": ["uuid-with-warnings"],
    "force_delete": true,
    "reason": "Aprobado por supervisor - eliminación de asiento de cierre erróneo"
  }'
```

### Operación Masiva Unificada

```bash
curl -X POST "http://api.ejemplo.com/api/v1/journal-entries/bulk-operation" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "delete",
    "entry_ids": ["uuid1", "uuid2"],
    "operation_data": {
      "force_delete": true,
      "reason": "Operación masiva autorizada"
    }
  }'
```
