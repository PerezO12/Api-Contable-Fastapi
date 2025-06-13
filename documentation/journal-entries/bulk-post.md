# Operaciones de Contabilización Masiva de Asientos Contables

## Descripción General

La funcionalidad de contabilización masiva permite contabilizar múltiples asientos contables aprobados simultáneamente, afectando los saldos de las cuentas contables en el sistema. Esta es una operación crítica que marca el punto de no retorno en el ciclo de vida de los asientos contables.

## Casos de Uso

### ¿Cuándo usar esta funcionalidad?

1. **Cierre contable**: Contabilización final de todos los asientos del período
2. **Procesamiento de lotes**: Contabilización eficiente de múltiples transacciones aprobadas
3. **Automatización**: Contabilización programada de asientos automáticos
4. **Flujo de trabajo**: Paso final después de la aprobación en procesos controlados

### ¿Cuándo NO usar esta funcionalidad?

- **Asientos no aprobados**: Solo se pueden contabilizar asientos en estado APPROVED
- **Asientos ya contabilizados**: No se pueden re-contabilizar asientos POSTED
- **Período cerrado**: El período contable debe estar abierto
- **Cuentas bloqueadas**: Las cuentas deben permitir movimientos

## Estados Permitidos

```
APPROVED ─────→ POSTED

DRAFT ────────X (Debe estar aprobado primero)
PENDING ──────X (Debe estar aprobado primero)
POSTED ───────X (Ya está contabilizado)
CANCELLED ────X (No se puede contabilizar)
```

## Validaciones Implementadas

### Validaciones de Negocio

1. **Estado válido**: Solo se pueden contabilizar asientos en estado APPROVED
2. **Balance perfecto**: Los asientos deben estar perfectamente balanceados
3. **Cuentas activas**: Todas las cuentas deben estar activas y permitir movimientos
4. **Período abierto**: El período contable debe estar abierto para contabilización
5. **Secuencia numérica**: Validación de secuencia de números de asiento
6. **Límites de fecha**: Las fechas deben estar dentro del período permitido

### Validaciones de Integridad

1. **Existencia de cuentas**: Todas las cuentas contables deben existir
2. **Estructura de datos**: Validación de integridad referencial
3. **Montos válidos**: Los montos deben ser positivos y válidos
4. **Referencias únicas**: Validación de referencias duplicadas

### Validaciones de Seguridad

1. **Permisos de usuario**: Solo usuarios con rol de contabilizador pueden ejecutar
2. **Auditoría obligatoria**: Registro detallado de la operación
3. **Razón requerida**: Se debe proporcionar una razón para la contabilización
4. **Confirmación explícita**: Requiere confirmación explícita debido al impacto

## API Endpoints

### 1. Validación Previa de Contabilización Masiva

```http
POST /api/v1/journal-entries/bulk/post/validate
```

**Request Body:**
```json
{
  "entry_ids": ["uuid1", "uuid2", "uuid3"],
  "posted_by_id": "user-uuid",
  "force_post": false,
  "reason": "Contabilización masiva del cierre mensual"
}
```

**Response:**
```json
{
  "can_post_all": false,
  "total_entries": 3,
  "valid_entries": 2,
  "invalid_entries": 1,
  "validations": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "JE-2024-001",
      "journal_entry_description": "Ventas del día",
      "current_status": "approved",
      "can_post": true,
      "errors": [],
      "warnings": [],
      "impact_summary": {
        "affected_accounts": 4,
        "total_debit": "5000.00",
        "total_credit": "5000.00"
      }
    },
    {
      "journal_entry_id": "uuid2",
      "journal_entry_number": "JE-2024-002",
      "journal_entry_description": "Compras del día",
      "current_status": "approved",
      "can_post": true,
      "errors": [],
      "warnings": ["Contabilización con monto significativo: 25000.00"],
      "impact_summary": {
        "affected_accounts": 6,
        "total_debit": "25000.00",
        "total_credit": "25000.00"
      }
    },
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003",
      "journal_entry_description": "Asiento no aprobado",
      "current_status": "draft",
      "can_post": false,
      "errors": ["El asiento debe estar aprobado para poder contabilizarse"],
      "warnings": []
    }
  ],
  "global_impact": {
    "total_affected_accounts": 10,
    "total_amount": "30000.00",
    "period": "2024-01"
  },
  "global_errors": [],
  "global_warnings": ["Operación afectará saldos de 10 cuentas contables"]
}
```

### 2. Contabilización Masiva

```http
POST /api/v1/journal-entries/bulk/post
```

**Request Body:**
```json
{
  "entry_ids": ["uuid1", "uuid2", "uuid3"],
  "posted_by_id": "user-uuid",
  "force_post": false,
  "reason": "Contabilización masiva del cierre mensual",
  "confirm_impact": true
}
```

**Response:**
```json
{
  "operation_id": "bulk-post-uuid",
  "total_requested": 3,
  "total_posted": 2,
  "total_failed": 1,
  "execution_time_ms": 2150,
  "posted_entries": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "JE-2024-001",
      "previous_status": "approved",
      "new_status": "posted",
      "posted_at": "2024-01-15T15:45:00Z",
      "posted_by": "María García",
      "impact_summary": {
        "affected_accounts": 4,
        "total_debit": "5000.00",
        "total_credit": "5000.00",
        "balance_changes": [
          {
            "account_code": "1110",
            "account_name": "Caja General",
            "previous_balance": "10000.00",
            "new_balance": "15000.00",
            "change": "5000.00"
          }
        ]
      }
    },
    {
      "journal_entry_id": "uuid2",
      "journal_entry_number": "JE-2024-002",
      "previous_status": "approved",
      "new_status": "posted",
      "posted_at": "2024-01-15T15:45:01Z",
      "posted_by": "María García",
      "impact_summary": {
        "affected_accounts": 6,
        "total_debit": "25000.00",
        "total_credit": "25000.00"
      }
    }
  ],
  "failed_entries": [
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003",
      "current_status": "draft",
      "errors": ["El asiento debe estar aprobado para poder contabilizarse"],
      "error_code": "INVALID_STATUS_FOR_POSTING"
    }
  ],
  "operation_summary": {
    "reason": "Contabilización masiva del cierre mensual",
    "executed_by": "María García",
    "executed_at": "2024-01-15T15:45:00Z",
    "total_impact": {
      "affected_accounts": 10,
      "total_amount": "30000.00",
      "period": "2024-01"
    }
  }
}
```

## Parámetros de Configuración

### Parámetros Opcionales

- **force_post**: Si es `true`, omite algunas validaciones no críticas
- **posted_by_id**: ID del usuario contabilizador (si no se especifica, usa el usuario autenticado)
- **reason**: Razón de la contabilización masiva (requerido)
- **confirm_impact**: Confirmación explícita del impacto en las cuentas

### Límites del Sistema

- **Máximo de asientos por operación**: 50 (más restrictivo que otras operaciones)
- **Timeout de operación**: 60 segundos (mayor debido al impacto)
- **Validación de integridad**: Completa antes y después de la operación

## Códigos de Error

### Errores por Asiento

- **INVALID_STATUS_FOR_POSTING**: El asiento no está en estado APPROVED
- **UNBALANCED_ENTRY**: El asiento no está balanceado
- **INACTIVE_ACCOUNTS**: Una o más cuentas están inactivas
- **CLOSED_PERIOD**: El período contable está cerrado
- **ACCOUNT_LOCKED**: Cuenta bloqueada para movimientos
- **SEQUENCE_ERROR**: Error en secuencia numérica

### Errores Globales

- **BULK_POST_LIMIT_EXCEEDED**: Se excedió el límite de asientos por operación
- **PERIOD_LOCKED**: El período está bloqueado para contabilización
- **INSUFFICIENT_PERMISSIONS**: Usuario sin permisos de contabilización
- **IMPACT_NOT_CONFIRMED**: No se confirmó el impacto de la operación
- **DATABASE_TRANSACTION_ERROR**: Error en transacción de base de datos

## Impacto en el Sistema

### Cambios en Saldos

La contabilización masiva actualiza automáticamente:

1. **Saldos de cuentas**: Actualización de todos los saldos afectados
2. **Histórico de movimientos**: Registro detallado de cada movimiento
3. **Balances de prueba**: Actualización de balances consolidados
4. **Reportes financieros**: Impacto inmediato en estados financieros

### Integridad Transaccional

- **Atomicidad por asiento**: Cada asiento se contabiliza completamente o no se contabiliza
- **Consistencia global**: Los saldos se mantienen consistentes durante toda la operación
- **Rollback automático**: En caso de error, se revierten todos los cambios del asiento fallido
- **Verificación post-operación**: Validación de integridad después de la contabilización

## Mejores Prácticas

### Para Usuarios

1. **Validar impacto**: Siempre revisar el impacto antes de contabilizar
2. **Lotes pequeños**: Procesar en grupos de 10-25 asientos para mejor control
3. **Horarios apropiados**: Realizar contabilizaciones en horarios de menor actividad
4. **Backup previo**: Asegurar respaldo antes de operaciones masivas importantes

### Para Desarrolladores

1. **Transacciones robustas**: Implementar manejo robusto de transacciones
2. **Logging exhaustivo**: Registrar cada cambio de saldo y movimiento
3. **Validación previa obligatoria**: Nunca omitir validaciones previas
4. **Monitoreo en tiempo real**: Implementar alertas de rendimiento

### Para Administradores

1. **Horarios controlados**: Establecer ventanas de contabilización
2. **Monitoreo intensivo**: Vigilar rendimiento durante operaciones
3. **Respaldos frecuentes**: Aumentar frecuencia de respaldos
4. **Capacitación especializada**: Entrenamiento específico para contabilizadores

## Recuperación de Errores

### Estrategias de Recuperación

1. **Reversión automática**: Asientos fallidos se revierten automáticamente
2. **Continuación selectiva**: Procesar solo asientos válidos
3. **Re-procesamiento**: Posibilidad de re-procesar asientos fallidos
4. **Auditoría completa**: Registro detallado para investigación

### Procedimientos de Emergencia

1. **Parada de emergencia**: Procedimiento para detener operaciones en curso
2. **Rollback masivo**: Reversión de operaciones completas si es necesario
3. **Verificación de integridad**: Herramientas de verificación post-error
4. **Contacto de soporte**: Escalación automática en errores críticos

## Casos de Uso Avanzados

### Contabilización Programada

```json
{
  "entry_ids": ["uuid1", "uuid2"],
  "posted_by_id": "system-uuid",
  "schedule_for": "2024-01-31T23:55:00Z",
  "reason": "Contabilización automática de cierre",
  "auto_confirm": true
}
```

### Contabilización Condicional

```json
{
  "entry_ids": ["uuid1", "uuid2"],
  "posted_by_id": "supervisor-uuid",
  "conditions": {
    "max_total_amount": 100000,
    "require_supervisor_approval": true,
    "validate_account_limits": true
  },
  "reason": "Contabilización con validaciones adicionales"
}
```

## Integración con Reportes

### Actualización Automática

- **Balance General**: Actualización inmediata de saldos
- **Estado de Resultados**: Inclusión automática de ingresos y gastos
- **Flujo de Efectivo**: Actualización de movimientos de efectivo
- **Balance de Prueba**: Recálculo automático de balances

### Notificaciones

- **Alertas de impacto**: Notificación cuando se afectan montos significativos
- **Reportes de cierre**: Generación automática de reportes post-contabilización
- **Dashboard ejecutivo**: Actualización de métricas en tiempo real
- **Auditoría instantánea**: Disponibilidad inmediata de trazas de auditoría

## Troubleshooting

### Problemas Comunes

1. **Timeouts en lotes grandes**: Reducir tamaño de lote y aumentar timeout
2. **Errores de integridad**: Verificar consistencia de datos antes de contabilizar
3. **Bloqueos de cuenta**: Verificar estado de cuentas antes de la operación
4. **Problemas de rendimiento**: Optimizar consultas y usar índices apropiados

### Herramientas de Diagnóstico

1. **Monitor de transacciones**: Visualización en tiempo real de progreso
2. **Logs de saldos**: Historial detallado de cambios en saldos
3. **Métricas de rendimiento**: Estadísticas de tiempo de ejecución
4. **Verificador de integridad**: Herramienta de verificación post-operación
