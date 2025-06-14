# Operaciones de Aprobación Masiva de Asientos Contables

## Descripción General

La funcionalidad de aprobación masiva permite aprobar múltiples asientos contables simultáneamente, mejorando la eficiencia en procesos como cierres mensuales, aprobaciones de lotes de transacciones, y flujos de trabajo contables.

## Casos de Uso

### ¿Cuándo usar esta funcionalidad?

1. **Cierre mensual**: Aprobación de todos los asientos del período antes del cierre
2. **Aprobación de lotes**: Procesamiento eficiente de múltiples transacciones
3. **Flujo de supervisión**: Aprobación masiva por parte de supervisores
4. **Procesamiento automático**: Aprobación de asientos generados automáticamente

### ¿Cuándo NO usar esta funcionalidad?

- **Asientos ya aprobados**: No se pueden aprobar asientos en estado APPROVED o POSTED
- **Asientos cancelados**: No se pueden aprobar asientos cancelados
- **Asientos desbalanceados**: Los asientos deben estar correctamente balanceados
- **Sin permisos**: El usuario debe tener permisos de aprobación

## Estados Permitidos

```
DRAFT ────────┐
              ├─→ APPROVED
PENDING ──────┘

APPROVED ─────X (Ya está aprobado)
POSTED ───────X (No se puede cambiar)
CANCELLED ────X (No se puede aprobar)
```

## Validaciones Implementadas

### Validaciones de Negocio

1. **Estado válido**: Solo se pueden aprobar asientos en estado DRAFT o PENDING
2. **Balance correcto**: Los asientos deben estar perfectamente balanceados (débitos = créditos)
3. **Cuentas válidas**: Todas las cuentas deben existir y estar activas
4. **Período abierto**: El período contable debe estar abierto para modificaciones
5. **Estructura válida**: Cada asiento debe tener al menos dos líneas contables

### Validaciones de Seguridad

1. **Permisos de usuario**: Solo usuarios con rol de aprobador pueden ejecutar esta operación
2. **Auditoría completa**: Registro de quién y cuándo aprueba cada asiento
3. **Razón obligatoria**: Se debe proporcionar una razón para la aprobación masiva
4. **Límites de cantidad**: Máximo de asientos por operación según configuración

## API Endpoints

### 1. Validación Previa de Aprobación Masiva

```http
POST /api/v1/journal-entries/bulk-approve/validate
```

**Request Body:**
```json
{
  "journal_entry_ids": ["uuid1", "uuid2", "uuid3"],
  "approved_by_id": "user-uuid",
  "force_approve": false,
  "reason": "Aprobación masiva del cierre mensual de enero"
}
```

**Response:**
```json
{
  "can_approve_all": false,
  "total_entries": 3,
  "valid_entries": 2,
  "invalid_entries": 1,
  "validations": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "JE-2024-001",
      "journal_entry_description": "Ventas del día",
      "current_status": "draft",
      "can_approve": true,
      "errors": [],
      "warnings": []
    },
    {
      "journal_entry_id": "uuid2", 
      "journal_entry_number": "JE-2024-002",
      "journal_entry_description": "Compras del día",
      "current_status": "draft",
      "can_approve": true,
      "errors": [],
      "warnings": ["Asiento con monto significativo: 15000.00"]
    },
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003", 
      "journal_entry_description": "Asiento desbalanceado",
      "current_status": "draft",
      "can_approve": false,
      "errors": ["El asiento no está balanceado: débitos 1000.00, créditos 800.00"],
      "warnings": []
    }
  ],
  "global_errors": [],
  "global_warnings": ["Se aprobará 1 asiento con montos significativos"]
}
```

### 2. Aprobación Masiva

```http
POST /api/v1/journal-entries/bulk-approve
```

**Request Body:**
```json
{
  "journal_entry_ids": ["uuid1", "uuid2", "uuid3"],
  "approved_by_id": "user-uuid",
  "force_approve": false,
  "reason": "Aprobación masiva del cierre mensual de enero"
}
```

**Response:**
```json
{
  "operation_id": "bulk-approve-uuid",
  "total_requested": 3,
  "total_approved": 2,
  "total_failed": 1,
  "execution_time_ms": 1250,
  "approved_entries": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "JE-2024-001",
      "previous_status": "draft",
      "new_status": "approved",
      "approved_at": "2024-01-15T14:30:00Z",
      "approved_by": "Juan Pérez"
    },
    {
      "journal_entry_id": "uuid2",
      "journal_entry_number": "JE-2024-002", 
      "previous_status": "draft",
      "new_status": "approved",
      "approved_at": "2024-01-15T14:30:01Z",
      "approved_by": "Juan Pérez"
    }
  ],
  "failed_entries": [
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003",
      "current_status": "draft",
      "errors": ["El asiento no está balanceado: débitos 1000.00, créditos 800.00"],
      "error_code": "UNBALANCED_ENTRY"
    }
  ],
  "operation_summary": {
    "reason": "Aprobación masiva del cierre mensual de enero",
    "executed_by": "Juan Pérez",
    "executed_at": "2024-01-15T14:30:00Z"
  }
}
```

## Parámetros de Configuración

### Parámetros Opcionales

- **force_approve**: Si es `true`, omite algunas validaciones no críticas
- **approved_by_id**: ID del usuario aprobador (si no se especifica, usa el usuario autenticado)
- **reason**: Razón de la aprobación masiva (requerido)

### Límites del Sistema

- **Máximo de asientos por operación**: 100 (configurable)
- **Timeout de operación**: 30 segundos
- **Tamaño máximo de respuesta**: 10MB

## Códigos de Error

### Errores por Asiento

- **INVALID_STATUS**: El asiento no está en un estado que permita aprobación
- **UNBALANCED_ENTRY**: El asiento no está balanceado
- **INACTIVE_ACCOUNTS**: Una o más cuentas están inactivas
- **CLOSED_PERIOD**: El período contable está cerrado
- **INSUFFICIENT_PERMISSIONS**: Usuario sin permisos de aprobación

### Errores Globales

- **BULK_LIMIT_EXCEEDED**: Se excedió el límite de asientos por operación
- **INVALID_USER**: Usuario aprobador no válido
- **MISSING_REASON**: No se proporcionó razón para la operación
- **DATABASE_ERROR**: Error de conexión o transacción

## Mejores Prácticas

### Para Usuarios

1. **Validar primero**: Siempre usar el endpoint de validación antes de aprobar
2. **Lotes pequeños**: Procesar en grupos de 20-50 asientos para mejor rendimiento
3. **Razones descriptivas**: Proporcionar razones claras y específicas
4. **Verificar balances**: Asegurar que todos los asientos estén balanceados

### Para Desarrolladores

1. **Manejo de timeouts**: Implementar timeouts apropiados en el cliente
2. **Procesamiento asíncrono**: Considerar implementación asíncrona para lotes grandes
3. **Logging detallado**: Registrar todas las operaciones para auditoría
4. **Validación de entrada**: Validar IDs de asientos antes de enviar

### Para Administradores

1. **Configurar límites**: Ajustar límites según capacidad del servidor
2. **Monitorear uso**: Vigilar frecuencia y tamaño de operaciones masivas
3. **Auditar regularmente**: Revisar logs de aprobaciones masivas
4. **Capacitar usuarios**: Entrenar en uso correcto de la funcionalidad

## Impacto en el Sistema

### Rendimiento

- **Uso de CPU**: Moderado durante procesamiento de validaciones
- **Uso de memoria**: Proporcional al número de asientos procesados
- **I/O de base de datos**: Optimizado con transacciones por lotes

### Integridad de Datos

- **Transaccionalidad**: Cada asiento se procesa en su propia transacción
- **Consistencia**: Estados se actualizan atómicamente
- **Auditoría**: Registro completo de cambios en tablas de auditoría

## Integración con Otros Módulos

### Notificaciones

- **Email automático**: Notificación a interesados sobre aprobaciones masivas
- **Dashboard**: Actualización de métricas y estadísticas
- **Reportes**: Inclusión en reportes de actividad contable

### Permisos

- **Roles requeridos**: `journal_entry_approver` o superior
- **Permisos específicos**: `journal_entries.bulk_approve`
- **Delegación**: Soporte para aprobación delegada

## Casos de Uso Avanzados

### Aprobación Condicional

```json
{
  "journal_entry_ids": ["uuid1", "uuid2"],
  "approved_by_id": "supervisor-uuid",
  "force_approve": false,
  "conditions": {
    "max_amount_per_entry": 10000,
    "require_two_factor": true
  },
  "reason": "Aprobación con validaciones adicionales"
}
```

### Aprobación Programada

```json
{
  "journal_entry_ids": ["uuid1", "uuid2"],
  "approved_by_id": "system-uuid",
  "schedule_for": "2024-01-31T23:59:59Z",
  "reason": "Aprobación automática de cierre"
}
```

## Troubleshooting

### Problemas Comunes

1. **Timeout en operaciones grandes**: Reducir tamaño de lote
2. **Errores de balance**: Verificar cálculos antes de aprobar
3. **Permisos insuficientes**: Verificar roles y permisos del usuario
4. **Período cerrado**: Verificar estado del período contable

### Diagnóstico

1. **Logs del sistema**: Revisar logs de aplicación para errores detallados
2. **Métricas de base de datos**: Monitorear rendimiento de consultas
3. **Trazas de auditoría**: Verificar secuencia de operaciones
4. **Estado de memoria**: Monitorear uso de memoria durante operaciones
