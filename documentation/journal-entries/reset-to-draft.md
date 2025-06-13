# Funcionalidad de Restablecimiento a Borrador de Asientos Contables

## Descripción General

Se ha implementado una nueva funcionalidad que permite restablecer asientos contables desde estados "Aprobado" o "Pendiente" de vuelta al estado "Borrador". Esta operación es crítica en sistemas contables y requiere validaciones estrictas para mantener la integridad de los datos.

## Casos de Uso

### ¿Cuándo usar esta funcionalidad?

1. **Corrección de errores**: Cuando se detecta un error en un asiento ya aprobado pero aún no contabilizado
2. **Cambios de última hora**: Modificaciones necesarias antes de la contabilización final
3. **Revisión adicional**: Cuando se requiere una revisión más detallada
4. **Proceso de aprobación**: Devolución a borrador para correcciones en el flujo de aprobación

### ¿Cuándo NO usar esta funcionalidad?

- **Asientos contabilizados**: No se pueden restablecer asientos ya contabilizados (POSTED)
- **Asientos cancelados**: No se pueden restablecer asientos cancelados
- **Asientos ya en borrador**: No tiene sentido restablecer lo que ya está en borrador

## Estados Permitidos

```
PENDING ─────┐
             ├─→ DRAFT
APPROVED ────┘

POSTED ──────X (No permitido)
CANCELLED ───X (No permitido)
DRAFT ───────X (Ya está en borrador)
```

## Validaciones Implementadas

### Validaciones de Negocio

1. **Estado válido**: Solo se pueden restablecer asientos en estado APPROVED o PENDING
2. **Integridad referencial**: Verificar que no hay dependencias que impidan el restablecimiento
3. **Permisos de usuario**: Solo usuarios con permisos de creación pueden restablecer
4. **Tipos especiales**: Advertencias para asientos de apertura, cierre o automáticos

### Validaciones de Seguridad

1. **Auditoría completa**: Registro de quién y cuándo restablece cada asiento
2. **Razón obligatoria**: Se debe proporcionar una razón para el restablecimiento
3. **Límites de tiempo**: Advertencias para asientos aprobados recientemente
4. **Montos significativos**: Advertencias para asientos con montos altos

## API Endpoints

### 1. Restablecimiento Individual

```http
POST /api/v1/journal-entries/{entry_id}/reset-to-draft
```

**Request Body:**
```json
{
  "reason": "Corrección de cuenta contable en línea 2"
}
```

**Response:**
```json
{
  "id": "uuid",
  "number": "JE-2024-001",
  "status": "draft",
  "description": "Descripción del asiento",
  // ... resto de campos del asiento
}
```

### 2. Validación Previa Masiva

```http
POST /api/v1/journal-entries/validate-reset-to-draft
```

**Request Body:**
```json
["entry_id_1", "entry_id_2", "entry_id_3"]
```

**Response:**
```json
[
  {
    "journal_entry_id": "uuid",
    "journal_entry_number": "JE-2024-001",
    "journal_entry_description": "Descripción",
    "current_status": "approved",
    "can_reset": true,
    "errors": [],
    "warnings": ["Asiento con monto significativo: 50000.00"]
  }
]
```

### 3. Restablecimiento Masivo

```http
POST /api/v1/journal-entries/bulk-reset-to-draft
```

**Request Body:**
```json
{
  "journal_entry_ids": ["entry_id_1", "entry_id_2", "entry_id_3"],
  "force_reset": false,
  "reason": "Corrección masiva de asientos del período"
}
```

**Response:**
```json
{
  "operation_id": "bulk-reset-uuid",
  "total_requested": 3,
  "total_reset": 2,
  "total_failed": 1,
  "execution_time_ms": 850,
  "reset_entries": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "JE-2024-001",
      "previous_status": "approved",
      "new_status": "draft",
      "reset_at": "2024-01-15T16:20:00Z",
      "reset_by": "Usuario Contador"
    }
  ],
  "failed_entries": [
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003",
      "current_status": "posted",
      "errors": ["No se puede restablecer un asiento contabilizado"],
      "error_code": "CANNOT_RESET_POSTED_ENTRY"
    }
  ],
  "operation_summary": {
    "reason": "Corrección masiva de asientos del período",
    "executed_by": "Usuario Contador",
    "executed_at": "2024-01-15T16:20:00Z"
  }
}
```

### 3. Restablecimiento Masivo

```http
POST /api/v1/journal-entries/bulk-reset-to-draft
```

**Request Body:**
```json
{
  "journal_entry_ids": ["id1", "id2", "id3"],
  "force_reset": false,
  "reason": "Corrección masiva de centro de costos"
}
```

**Response:**
```json
{
  "total_requested": 3,
  "total_reset": 2,
  "total_failed": 1,
  "reset_entries": [...],
  "failed_entries": [...],
  "errors": [],
  "warnings": []
}
```

### 4. Operación Masiva Unificada

```http
POST /api/v1/journal-entries/bulk-operation?operation=reset_to_draft
```

**Query Parameters:**
- `operation`: "reset_to_draft"
- `journal_entry_ids`: Lista de IDs
- `force_operation`: boolean (ignorar advertencias)
- `reason`: string (razón de la operación)

## Esquemas de Datos

### JournalEntryResetToDraft
```python
class JournalEntryResetToDraft(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
```

### BulkJournalEntryResetToDraft
```python
class BulkJournalEntryResetToDraft(BaseModel):
    journal_entry_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100)
    force_reset: bool = Field(False)
    reason: str = Field(..., min_length=1, max_length=500)
```

### JournalEntryResetToDraftValidation
```python
class JournalEntryResetToDraftValidation(BaseModel):
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    journal_entry_description: str
    current_status: JournalEntryStatus
    can_reset: bool
    errors: List[str] = []
    warnings: List[str] = []
```

## Lógica de Negocio

### Proceso de Restablecimiento

1. **Validación inicial**: Verificar que el asiento existe y está en estado válido
2. **Validaciones de negocio**: Aplicar todas las reglas de validación
3. **Limpieza de estado**: Limpiar campos de aprobación (approved_by_id, approved_at)
4. **Cambio de estado**: Cambiar status a DRAFT
5. **Auditoría**: Registrar la operación en las notas del asiento
6. **Persistencia**: Guardar cambios en la base de datos

### Campos Afectados

Al restablecer a borrador se limpian los siguientes campos:
- `status` → `DRAFT`
- `approved_by_id` → `null`
- `approved_at` → `null`
- `notes` → Se agrega información del restablecimiento

Los siguientes campos NO se modifican:
- `created_by_id` (mantiene el creador original)
- `created_at` (mantiene fecha de creación original)
- `posted_by_id` y `posted_at` (siempre son null para asientos no contabilizados)
- Líneas del asiento (se mantienen intactas)

## Consideraciones de Seguridad

### Permisos Requeridos
- El usuario debe tener permisos de creación de asientos (`can_create_entries`)
- Se registra la identidad del usuario que realiza el restablecimiento

### Auditoría
- Cada restablecimiento se registra en las notas del asiento
- Se incluye timestamp, usuario y razón
- Se mantiene trazabilidad completa de cambios de estado

### Límites y Restricciones
- Máximo 100 asientos por operación masiva
- Razón obligatoria (1-500 caracteres)
- IDs únicos en operaciones masivas
- Validación de permisos en cada operación

## Manejo de Errores

### Errores Comunes
- **Asiento no encontrado**: HTTP 404
- **Estado inválido**: HTTP 400 con mensaje específico
- **Permisos insuficientes**: HTTP 403
- **Asiento ya contabilizado**: HTTP 400

### Respuestas de Error
```json
{
  "detail": "El asiento no puede ser restablecido a borrador desde el estado posted"
}
```

## Ejemplos de Uso

### Ejemplo 1: Corrección Simple
```python
# Restablecer un asiento para corregir una cuenta
reset_data = {
    "reason": "Corrección de cuenta contable - cambiar de 1101 a 1102"
}

response = await client.post(
    f"/api/v1/journal-entries/{entry_id}/reset-to-draft",
    json=reset_data
)
```

### Ejemplo 2: Validación Previa
```python
# Validar antes de restablecer
entry_ids = ["id1", "id2", "id3"]
validations = await client.post(
    "/api/v1/journal-entries/validate-reset-to-draft",
    json=entry_ids
)

# Procesar solo los que pueden restablecerse
valid_ids = [v["journal_entry_id"] for v in validations if v["can_reset"]]
```

### Ejemplo 3: Operación Masiva
```python
# Restablecer múltiples asientos
bulk_data = {
    "journal_entry_ids": valid_ids,
    "force_reset": False,  # No ignorar advertencias
    "reason": "Revisión adicional requerida por auditoría"
}

result = await client.post(
    "/api/v1/journal-entries/bulk-reset-to-draft",
    json=bulk_data
)
```

## Testing

Se han implementado tests completos que cubren:
- Casos exitosos individuales y masivos
- Validaciones de permisos
- Validaciones de estado
- Manejo de errores
- Validación de datos de entrada

Los tests están en: `app/tests/test_journal_entry_reset_to_draft_api.py`

## Integración con el Sistema

Esta funcionalidad se integra perfectamente con:
- Sistema de permisos existente
- Auditoría y logging
- Validaciones de integridad
- API patterns establecidos
- Manejo de errores consistente

La implementación sigue todas las mejores prácticas establecidas en el sistema y mantiene consistencia con el resto de operaciones de asientos contables.
