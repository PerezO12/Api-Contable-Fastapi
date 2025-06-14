# Resumen Técnico - Operaciones Masivas de Asientos Contables

## Visión General

Se han implementado cinco operaciones masivas principales para asientos contables, cada una con sus propios endpoints de validación y ejecución. Estas operaciones permiten gestionar eficientemente grandes volúmenes de asientos contables mientras mantienen la integridad y trazabilidad del sistema.

## Operaciones Implementadas

### 1. Aprobación Masiva (Bulk Approve)
- **Estados origen**: DRAFT, PENDING
- **Estado destino**: APPROVED
- **Endpoint validación**: `POST /api/v1/journal-entries/bulk-approve/validate`
- **Endpoint ejecución**: `POST /api/v1/journal-entries/bulk-approve`
- **Impacto**: Cambio de estado, sin afectar saldos

### 2. Contabilización Masiva (Bulk Post)
- **Estados origen**: APPROVED
- **Estado destino**: POSTED
- **Endpoint validación**: `POST /api/v1/journal-entries/bulk-post/validate`
- **Endpoint ejecución**: `POST /api/v1/journal-entries/bulk-post`
- **Impacto**: Cambio de estado + actualización de saldos de cuentas

### 3. Cancelación Masiva (Bulk Cancel)
- **Estados origen**: DRAFT, PENDING, APPROVED
- **Estado destino**: CANCELLED
- **Endpoint validación**: `POST /api/v1/journal-entries/bulk-cancel/validate`
- **Endpoint ejecución**: `POST /api/v1/journal-entries/bulk-cancel`
- **Impacto**: Cambio de estado, sin afectar saldos

### 4. Reversión Masiva (Bulk Reverse)
- **Estados origen**: POSTED
- **Estado destino**: POSTED (original) + nuevos asientos de reversión
- **Endpoint validación**: `POST /api/v1/journal-entries/bulk/reverse/validate`
- **Endpoint ejecución**: `POST /api/v1/journal-entries/bulk/reverse`
- **Impacto**: Marcado como revertido + creación de asientos de reversión + actualización de saldos

### 5. Restablecimiento Masivo (Bulk Reset to Draft)
- **Estados origen**: APPROVED, PENDING
- **Estado destino**: DRAFT
- **Endpoint validación**: `POST /api/v1/journal-entries/bulk/reset-to-draft/validate`
- **Endpoint ejecución**: `POST /api/v1/journal-entries/bulk/reset-to-draft`
- **Impacto**: Cambio de estado, sin afectar saldos

## Arquitectura Común

### Patrón de Diseño
Todas las operaciones siguen el mismo patrón arquitectónico:

```python
# 1. Endpoint de validación
@router.post("/bulk/{operation}/validate")
async def validate_bulk_operation(
    request: BulkOperationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BulkOperationValidationResult

# 2. Endpoint de ejecución
@router.post("/bulk/{operation}")
async def execute_bulk_operation(
    request: BulkOperationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BulkOperationResult
```

### Flujo de Procesamiento

1. **Validación de entrada**: Verificación de parámetros y permisos
2. **Carga de asientos**: Recuperación eficiente con `selectinload`
3. **Validación individual**: Validación por cada asiento
4. **Procesamiento por lotes**: Ejecución de la operación
5. **Auditoría**: Registro de resultados y cambios
6. **Respuesta estructurada**: Reporte detallado de resultados

### Estructura de Respuesta Estándar

```json
{
  "operation_id": "uuid",
  "total_requested": 10,
  "total_processed": 8,
  "total_failed": 2,
  "execution_time_ms": 1500,
  "processed_entries": [...],
  "failed_entries": [...],
  "operation_summary": {
    "reason": "...",
    "executed_by": "...",
    "executed_at": "..."
  }
}
```

## Esquemas de Datos

### Esquemas Base

```python
# Validación individual
class JournalEntry{Operation}Validation(BaseModel):
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    journal_entry_description: str
    current_status: JournalEntryStatus
    can_{operation}: bool
    errors: List[str]
    warnings: List[str]

# Request masivo
class BulkJournalEntry{Operation}(BaseModel):
    journal_entry_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=100)
    {operation}_by_id: Optional[uuid.UUID] = None
    reason: str = Field(..., min_length=10, max_length=500)
    force_{operation}: bool = False

# Response masivo
class BulkJournalEntry{Operation}Result(BaseModel):
    operation_id: uuid.UUID
    total_requested: int
    total_{operation}d: int
    total_failed: int
    execution_time_ms: int
    {operation}d_entries: List[...]
    failed_entries: List[...]
    operation_summary: dict
```

### Validaciones Específicas

Cada operación tiene validaciones específicas implementadas en el servicio:

```python
def validate_{operation}_entries(
    self, 
    entries: List[JournalEntry], 
    user: User, 
    **kwargs
) -> List[JournalEntry{Operation}Validation]:
    validations = []
    for entry in entries:
        validation = self._validate_single_{operation}(entry, user, **kwargs)
        validations.append(validation)
    return validations
```

## Servicios Implementados

### JournalEntryService

Todos los métodos de operaciones masivas están implementados en `app/services/journal_entry_service.py`:

```python
class JournalEntryService:
    # Validaciones
    async def validate_bulk_approve_entries(...)
    async def validate_bulk_post_entries(...)
    async def validate_bulk_cancel_entries(...)
    async def validate_bulk_reverse_entries(...)
    async def validate_bulk_reset_to_draft_entries(...)
    
    # Ejecuciones
    async def bulk_approve_entries(...)
    async def bulk_post_entries(...)
    async def bulk_cancel_entries(...)
    async def bulk_reverse_entries(...)
    async def bulk_reset_to_draft_entries(...)
```

### Métodos de Validación Individual

Cada operación tiene un método privado para validar asientos individuales:

```python
def _validate_single_approve(self, entry: JournalEntry, user: User) -> JournalEntryApproveValidation
def _validate_single_post(self, entry: JournalEntry, user: User) -> JournalEntryPostValidation
def _validate_single_cancel(self, entry: JournalEntry, user: User) -> JournalEntryCancelValidation
def _validate_single_reverse(self, entry: JournalEntry, user: User, reversal_date: date) -> JournalEntryReverseValidation
def _validate_single_reset_to_draft(self, entry: JournalEntry, user: User) -> JournalEntryResetToDraftValidation
```

## API Endpoints

### Estructura de URLs Completa

```
/api/v1/journal-entries/
├── {id}/approve                    # Aprobación individual
├── {id}/post                      # Contabilización individual  
├── {id}/cancel                    # Cancelación individual
├── {id}/reverse                   # Reversión individual
├── {id}/reset-to-draft           # Restablecimiento individual
├── bulk/
│   ├── approve/
│   │   ├── validate              # Validación previa
│   │   └── (execute)             # Ejecución masiva
│   ├── post/
│   │   ├── validate
│   │   └── (execute)
│   ├── cancel/
│   │   ├── validate
│   │   └── (execute)
│   ├── reverse/
│   │   ├── validate
│   │   └── (execute)
│   ├── reset-to-draft/
│   │   ├── validate
│   │   └── (execute)
│   ├── create/                   # Creación masiva
│   └── delete/
│       ├── validate
│       └── (execute)
└── validate-{operation}          # Endpoints de validación
```

### Decoradores y Middleware

Todos los endpoints incluyen:
- Autenticación JWT requerida
- Validación de permisos específicos
- Rate limiting para operaciones masivas
- Logging de auditoría automático
- Manejo de errores estandarizado

## Validaciones de Negocio

### Validaciones Comunes

1. **Estados válidos**: Verificación de estados origen permitidos
2. **Permisos de usuario**: Validación de roles y permisos específicos
3. **Integridad de datos**: Verificación de existencia y consistencia
4. **Límites del sistema**: Validación de límites configurables

### Validaciones Específicas por Operación

#### Approve
- Asiento balanceado (débitos = créditos)
- Cuentas activas
- Período abierto

#### Post
- Asiento aprobado
- Secuencia numérica válida
- Cuentas permiten movimientos

#### Cancel
- Asiento no contabilizado
- Razón de cancelación obligatoria

#### Reverse
- Asiento contabilizado
- Fecha de reversión válida
- No previamente revertido

#### Reset to Draft
- Asiento aprobado o pendiente
- No contabilizado

## Optimizaciones de Rendimiento

### Carga Eficiente de Datos

```python
# Uso de selectinload para evitar N+1 queries
entries = await db.execute(
    select(JournalEntry)
    .options(selectinload(JournalEntry.lines))
    .where(JournalEntry.id.in_(journal_entry_ids))
)
```

### Procesamiento por Lotes

```python
# Procesamiento en lotes para operaciones que afectan saldos
batch_size = 50
for i in range(0, len(entries), batch_size):
    batch = entries[i:i + batch_size]
    await self._process_batch(batch)
```

### Transacciones Optimizadas

```python
# Transacciones por asiento para operaciones críticas
for entry in entries:
    try:
        async with db.begin():
            await self._process_single_entry(entry)
            processed_entries.append(entry)
    except Exception as e:
        failed_entries.append({"entry": entry, "error": str(e)})
```

## Auditoría y Logging

### Registro de Auditoría

Cada operación registra:
- ID de operación único
- Usuario ejecutor
- Timestamp de ejecución
- Asientos afectados
- Razón de la operación
- Resultados detallados

### Logs de Sistema

```python
logger.info(
    f"Bulk {operation} operation started",
    extra={
        "operation_id": operation_id,
        "user_id": user.id,
        "entry_count": len(journal_entry_ids),
        "operation": operation
    }
)
```

## Manejo de Errores

### Estrategia de Continuación

Las operaciones masivas continúan procesando asientos válidos aunque algunos fallen:

```python
for entry in entries:
    try:
        result = await self._process_entry(entry)
        processed_entries.append(result)
    except ValidationError as e:
        failed_entries.append({
            "entry_id": entry.id,
            "error": str(e),
            "error_code": e.code
        })
```

### Códigos de Error Estándar

- `INVALID_STATUS`: Estado no válido para la operación
- `INSUFFICIENT_PERMISSIONS`: Permisos insuficientes
- `VALIDATION_ERROR`: Error de validación de negocio
- `DATABASE_ERROR`: Error de base de datos
- `LIMIT_EXCEEDED`: Límite de operación excedido

## Testing

### Estructura de Tests

```python
class TestBulk{Operation}:
    async def test_validate_bulk_{operation}_success(...)
    async def test_validate_bulk_{operation}_mixed_results(...)
    async def test_bulk_{operation}_success(...)
    async def test_bulk_{operation}_with_failures(...)
    async def test_bulk_{operation}_permissions(...)
    async def test_bulk_{operation}_edge_cases(...)
```

### Cobertura de Tests

- ✅ Validaciones exitosas (individual y masiva)
- ✅ Validaciones con errores (individual y masiva)
- ✅ Ejecución exitosa (individual y masiva)
- ✅ Ejecución con fallos parciales
- ✅ Validación de permisos
- ✅ Casos extremos y límites
- ✅ Operaciones individuales
- ✅ Integración de endpoints completa

## Configuración

### Parámetros Configurables

```python
# En config.py
BULK_OPERATIONS_CONFIG = {
    "max_entries_per_operation": 100,
    "operation_timeout_seconds": 60,
    "batch_size": 50,
    "require_reason_min_length": 10,
    "enable_force_operations": True
}
```

### Variables de Entorno

```env
BULK_OPERATIONS_MAX_ENTRIES=100
BULK_OPERATIONS_TIMEOUT=60
BULK_OPERATIONS_BATCH_SIZE=50
```

## Seguridad

### Permisos Requeridos

```python
REQUIRED_PERMISSIONS = {
    "approve": "journal_entries.bulk_approve",
    "post": "journal_entries.bulk_post", 
    "cancel": "journal_entries.bulk_cancel",
    "reverse": "journal_entries.bulk_reverse",
    "reset_to_draft": "journal_entries.bulk_reset"
}
```

### Rate Limiting

```python
@limiter.limit("10/minute")  # Máximo 10 operaciones bulk por minuto
async def bulk_operation_endpoint(...):
    pass
```

## Métricas y Monitoreo

### Métricas Implementadas

1. **Tiempo de ejecución** por operación
2. **Tasa de éxito/fallo** por operación
3. **Volumen de asientos** procesados
4. **Frecuencia de uso** por usuario
5. **Errores más comunes** por tipo

### Alertas Configuradas

- Operaciones que exceden timeout
- Tasa de fallos superior al 20%
- Volumen inusual de operaciones
- Errores de base de datos

## Roadmap de Mejoras

### Mejoras Planificadas

1. **Operaciones asíncronas**: Para lotes muy grandes
2. **Progress tracking**: Seguimiento de progreso en tiempo real
3. **Programación de operaciones**: Operaciones diferidas
4. **Validaciones personalizadas**: Reglas de negocio configurables
5. **Exportación de resultados**: Reportes en Excel/PDF

### Optimizaciones Futuras

1. **Caché de validaciones**: Para mejorar rendimiento
2. **Procesamiento paralelo**: Para operaciones independientes
3. **Compresión de respuestas**: Para lotes grandes
4. **Streaming de resultados**: Para operaciones muy grandes

## Conclusión

Las operaciones masivas de asientos contables proporcionan una solución robusta, eficiente y bien documentada para la gestión de grandes volúmenes de transacciones contables. La implementación sigue patrones consistentes, mantiene la integridad de datos y proporciona trazabilidad completa para cumplir con requisitos de auditoría y compliance.
