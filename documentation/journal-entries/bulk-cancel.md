# Operaciones de Cancelación Masiva de Asientos Contables

## Descripción General

La funcionalidad de cancelación masiva permite cancelar múltiples asientos contables simultáneamente. Esta operación marca los asientos como cancelados sin afectar los saldos de las cuentas, ya que solo se pueden cancelar asientos que aún no han sido contabilizados.

## Casos de Uso

### ¿Cuándo usar esta funcionalidad?

1. **Corrección de errores**: Cancelación de lotes de asientos con errores detectados
2. **Cambios de proceso**: Cancelación masiva cuando cambian políticas contables
3. **Limpieza de datos**: Eliminación lógica de asientos obsoletos o incorrectos
4. **Control de calidad**: Cancelación de asientos que no pasan revisiones de calidad

### ¿Cuándo NO usar esta funcionalidad?

- **Asientos contabilizados**: No se pueden cancelar asientos en estado POSTED
- **Asientos ya cancelados**: No se pueden cancelar asientos que ya están CANCELLED
- **Reversión de contabilizados**: Para asientos POSTED usar reversión en lugar de cancelación

## Estados Permitidos

```
DRAFT ─────────┐
               ├─→ CANCELLED
PENDING ───────┤
               │
APPROVED ──────┘

POSTED ────────X (Usar reversión)
CANCELLED ─────X (Ya está cancelado)
```

## Validaciones Implementadas

### Validaciones de Negocio

1. **Estado válido**: Solo se pueden cancelar asientos en estado DRAFT, PENDING o APPROVED
2. **No contabilizados**: Los asientos no deben estar en estado POSTED
3. **No cancelados previamente**: Los asientos no deben estar ya CANCELLED
4. **Razón obligatoria**: Se debe proporcionar una razón clara para la cancelación
5. **Período permitido**: Validación de período para cancelaciones

### Validaciones de Seguridad

1. **Permisos de usuario**: Solo usuarios con permisos de cancelación pueden ejecutar
2. **Auditoría completa**: Registro detallado de quién y cuándo cancela cada asiento
3. **Confirmación requerida**: Confirmación explícita antes de la cancelación masiva
4. **Límites de cantidad**: Máximo de asientos por operación según configuración

## API Endpoints

### 1. Validación Previa de Cancelación Masiva

```http
POST /api/v1/journal-entries/bulk/cancel/validate
```

**Request Body:**
```json
{
  "entry_ids": ["uuid1", "uuid2", "uuid3"],
  "cancelled_by_id": "user-uuid",
  "reason": "Cancelación por error en proceso de importación"
}
```

**Response:**
```json
{
  "can_cancel_all": false,
  "total_entries": 3,
  "valid_entries": 2,
  "invalid_entries": 1,
  "validations": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "JE-2024-001",
      "journal_entry_description": "Asiento de prueba",
      "current_status": "draft",
      "can_cancel": true,
      "errors": [],
      "warnings": []
    },
    {
      "journal_entry_id": "uuid2",
      "journal_entry_number": "JE-2024-002",
      "journal_entry_description": "Asiento aprobado",
      "current_status": "approved",
      "can_cancel": true,
      "errors": [],
      "warnings": ["Asiento ya aprobado - se perderá la aprobación"]
    },
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003",
      "journal_entry_description": "Asiento contabilizado",
      "current_status": "posted",
      "can_cancel": false,
      "errors": ["No se puede cancelar un asiento contabilizado. Use reversión en su lugar."],
      "warnings": []
    }
  ],
  "global_errors": [],
  "global_warnings": ["Se cancelará 1 asiento ya aprobado"]
}
```

### 2. Cancelación Masiva

```http
POST /api/v1/journal-entries/bulk/cancel
```

**Request Body:**
```json
{
  "entry_ids": ["uuid1", "uuid2", "uuid3"],
  "cancelled_by_id": "user-uuid",
  "reason": "Cancelación por error en proceso de importación",
  "confirm_action": true
}
```

**Response:**
```json
{
  "operation_id": "bulk-cancel-uuid",
  "total_requested": 3,
  "total_cancelled": 2,
  "total_failed": 1,
  "execution_time_ms": 850,
  "cancelled_entries": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "JE-2024-001",
      "previous_status": "draft",
      "new_status": "cancelled",
      "cancelled_at": "2024-01-15T16:20:00Z",
      "cancelled_by": "Carlos Ruiz",
      "previous_data": {
        "total_debit": "1000.00",
        "total_credit": "1000.00",
        "lines_count": 2
      }
    },
    {
      "journal_entry_id": "uuid2",
      "journal_entry_number": "JE-2024-002",
      "previous_status": "approved",
      "new_status": "cancelled",
      "cancelled_at": "2024-01-15T16:20:01Z",
      "cancelled_by": "Carlos Ruiz",
      "previous_data": {
        "total_debit": "5000.00",
        "total_credit": "5000.00",
        "lines_count": 4,
        "approved_by": "Supervisor",
        "approved_at": "2024-01-15T14:30:00Z"
      }
    }
  ],
  "failed_entries": [
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003",
      "current_status": "posted",
      "errors": ["No se puede cancelar un asiento contabilizado. Use reversión en su lugar."],
      "error_code": "CANNOT_CANCEL_POSTED_ENTRY"
    }
  ],
  "operation_summary": {
    "reason": "Cancelación por error en proceso de importación",
    "executed_by": "Carlos Ruiz",
    "executed_at": "2024-01-15T16:20:00Z",
    "impact_summary": {
      "total_amount_cancelled": "6000.00",
      "approved_entries_cancelled": 1,
      "draft_entries_cancelled": 1
    }
  }
}
```

## Parámetros de Configuración

### Parámetros Requeridos

- **entry_ids**: Lista de IDs de asientos a cancelar
- **reason**: Razón obligatoria para la cancelación
- **confirm_action**: Confirmación explícita de la acción

### Parámetros Opcionales

- **cancelled_by_id**: ID del usuario que cancela (si no se especifica, usa el usuario autenticado)
- **preserve_audit**: Si se debe preservar información adicional de auditoría

### Límites del Sistema

- **Máximo de asientos por operación**: 100 (configurable)
- **Timeout de operación**: 30 segundos
- **Longitud máxima de razón**: 500 caracteres

## Códigos de Error

### Errores por Asiento

- **CANNOT_CANCEL_POSTED_ENTRY**: No se puede cancelar un asiento contabilizado
- **ALREADY_CANCELLED**: El asiento ya está cancelado
- **INVALID_STATUS**: Estado no válido para cancelación
- **INSUFFICIENT_PERMISSIONS**: Usuario sin permisos de cancelación
- **PERIOD_LOCKED**: Período bloqueado para modificaciones

### Errores Globales

- **BULK_CANCEL_LIMIT_EXCEEDED**: Se excedió el límite de asientos por operación
- **MISSING_REASON**: No se proporcionó razón para la cancelación
- **ACTION_NOT_CONFIRMED**: No se confirmó la acción de cancelación
- **INVALID_USER**: Usuario cancelador no válido
- **DATABASE_ERROR**: Error de base de datos durante la operación

## Efectos de la Cancelación

### En el Asiento Cancelado

1. **Cambio de estado**: El estado cambia a CANCELLED
2. **Preservación de datos**: Se preservan todos los datos originales
3. **Metadatos de cancelación**: Se agregan fecha, usuario y razón de cancelación
4. **Bloqueo de modificaciones**: No se pueden realizar más cambios al asiento

### En el Sistema

1. **Sin impacto en saldos**: Los saldos de cuentas no se ven afectados
2. **Reportes**: Los asientos cancelados se excluyen de reportes principales
3. **Auditoría**: Se mantiene trazabilidad completa de la cancelación
4. **Numeración**: Los números de asiento se mantienen pero no se reutilizan

## Diferencias con Otras Operaciones

### Cancelación vs Eliminación

- **Cancelación**: Marca como cancelado pero preserva la información
- **Eliminación**: Remueve completamente el asiento del sistema
- **Auditoría**: Cancelación mantiene rastro, eliminación puede no hacerlo
- **Reversibilidad**: Cancelación es reversible, eliminación normalmente no

### Cancelación vs Reversión

- **Cancelación**: Para asientos no contabilizados (DRAFT, PENDING, APPROVED)
- **Reversión**: Para asientos contabilizados (POSTED)
- **Impacto en saldos**: Cancelación no afecta, reversión sí afecta
- **Asientos adicionales**: Cancelación no crea asientos, reversión sí

## Mejores Prácticas

### Para Usuarios

1. **Razones específicas**: Proporcionar razones claras y detalladas
2. **Validación previa**: Siempre validar antes de ejecutar la cancelación
3. **Documentación adicional**: Mantener documentación externa cuando sea necesario
4. **Comunicación**: Informar a los interesados sobre cancelaciones importantes

### Para Desarrolladores

1. **Preservar auditoría**: Mantener toda la información de auditoría
2. **Validaciones exhaustivas**: Implementar todas las validaciones necesarias
3. **Logging detallado**: Registrar todas las operaciones de cancelación
4. **Transacciones atómicas**: Asegurar atomicidad en las cancelaciones

### Para Administradores

1. **Políticas claras**: Establecer políticas sobre cuándo cancelar vs eliminar
2. **Permisos granulares**: Configurar permisos específicos para cancelación
3. **Monitoreo de uso**: Vigilar patrones de cancelación masiva
4. **Capacitación específica**: Entrenar usuarios en uso correcto

## Recuperación de Asientos Cancelados

### Posibilidades de Recuperación

1. **Re-creación manual**: Crear nuevo asiento con los mismos datos
2. **Duplicación**: Funcionalidad para duplicar asiento cancelado
3. **Importación**: Re-importar desde fuente original si está disponible
4. **Recuperación desde backup**: En casos extremos, recuperar desde respaldo

### Proceso Recomendado

1. **Identificar asiento cancelado**: Localizar en reportes de cancelados
2. **Revisar razón de cancelación**: Entender por qué fue cancelado
3. **Verificar necesidad**: Confirmar que se necesita recuperar
4. **Crear nuevo asiento**: Usar datos del cancelado como base
5. **Documentar recuperación**: Registrar la relación con el asiento cancelado

## Reportes y Análisis

### Reportes de Asientos Cancelados

1. **Lista de cancelados**: Reporte de todos los asientos cancelados en un período
2. **Análisis de razones**: Agrupación por razones de cancelación
3. **Impacto de cancelaciones**: Análisis de montos y frecuencias
4. **Auditoría de cancelaciones**: Trazabilidad completa de operaciones

### Métricas de Seguimiento

1. **Tasa de cancelación**: Porcentaje de asientos cancelados vs total
2. **Tiempo promedio**: Tiempo entre creación y cancelación
3. **Usuarios más frecuentes**: Usuarios que más cancelan asientos
4. **Razones comunes**: Análisis de razones más frecuentes

## Integración con Flujos de Trabajo

### Notificaciones Automáticas

- **Email a supervisores**: Notificación de cancelaciones importantes
- **Dashboard de gestión**: Actualización de métricas en tiempo real
- **Alertas por volumen**: Alerta cuando se cancelan muchos asientos
- **Reportes periódicos**: Inclusión en reportes de gestión

### Workflows Relacionados

- **Proceso de aprobación**: Impacto en flujos de aprobación
- **Control de calidad**: Integración con procesos de QA
- **Auditoría interna**: Apoyo a procesos de auditoría
- **Gestión de excepciones**: Manejo de casos especiales

## Troubleshooting

### Problemas Comunes

1. **Cancelaciones accidentales**: Procedimiento de recuperación
2. **Permisos insuficientes**: Verificación y ajuste de permisos
3. **Errores de validación**: Diagnóstico de errores de estado
4. **Problemas de rendimiento**: Optimización para lotes grandes

### Herramientas de Diagnóstico

1. **Log de cancelaciones**: Historial detallado de operaciones
2. **Validador de estados**: Herramienta para verificar estados
3. **Monitor de permisos**: Verificación de permisos en tiempo real
4. **Analizador de impacto**: Herramienta para evaluar efectos de cancelación
