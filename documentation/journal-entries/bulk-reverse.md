# Operaciones de Reversión Masiva de Asientos Contables

## Descripción General

La funcionalidad de reversión masiva permite revertir múltiples asientos contables contabilizados simultáneamente. Esta operación crea asientos de reversión que anulan el efecto contable de los asientos originales, restaurando los saldos de las cuentas al estado previo a la contabilización original.

## Casos de Uso

### ¿Cuándo usar esta funcionalidad?

1. **Corrección de errores contabilizados**: Reversión de asientos con errores detectados después de la contabilización
2. **Ajustes de cierre**: Reversión de asientos de cierre para realizar ajustes adicionales
3. **Correcciones de período**: Reversión de asientos contabilizados en período incorrecto
4. **Auditoría y compliance**: Reversión requerida por auditores o reguladores
5. **Cambios de política contable**: Reversión por cambios en criterios contables

### ¿Cuándo NO usar esta funcionalidad?

- **Asientos no contabilizados**: Para asientos DRAFT, PENDING o APPROVED usar cancelación
- **Asientos ya revertidos**: No se pueden revertir asientos que ya han sido revertidos
- **Período cerrado**: No se puede revertir si el período está cerrado para modificaciones
- **Dependencias posteriores**: Cuando existen asientos posteriores que dependen del asiento a revertir

## Estados Permitidos

```
POSTED ───────→ POSTED (original) + POSTED (reversión)

DRAFT ─────────X (Usar cancelación)
PENDING ───────X (Usar cancelación)
APPROVED ──────X (Usar cancelación)
CANCELLED ─────X (No se puede revertir)
REVERSED ──────X (Ya está revertido)
```

## Validaciones Implementadas

### Validaciones de Negocio

1. **Estado válido**: Solo se pueden revertir asientos en estado POSTED
2. **No revertidos previamente**: Los asientos no deben estar ya marcados como REVERSED
3. **Período permitido**: El período de reversión debe estar abierto para contabilización
4. **Fecha de reversión válida**: La fecha de reversión debe ser válida según políticas contables
5. **Cuentas activas**: Las cuentas involucradas deben estar activas
6. **Razón obligatoria**: Se debe proporcionar una razón detallada para la reversión

### Validaciones de Integridad

1. **Existencia de cuentas**: Todas las cuentas del asiento original deben existir
2. **Consistencia de datos**: Validación de integridad referencial
3. **Secuencia numérica**: Validación de secuencia para asientos de reversión
4. **Dependencias**: Verificación de asientos posteriores que puedan verse afectados

### Validaciones de Seguridad

1. **Permisos de usuario**: Solo usuarios con permisos de reversión pueden ejecutar
2. **Auditoría obligatoria**: Registro detallado de la operación de reversión
3. **Confirmación de impacto**: Confirmación explícita del impacto en saldos
4. **Límites de tiempo**: Validación de límites de tiempo para reversiones

## API Endpoints

### 1. Validación Previa de Reversión Masiva

```http
POST /api/v1/journal-entries/bulk/reverse/validate
```

**Request Body:**
```json
{
  "entry_ids": ["uuid1", "uuid2", "uuid3"],
  "reversed_by_id": "user-uuid",
  "reversal_date": "2024-01-31",
  "reason": "Reversión por corrección contable solicitada por auditoría"
}
```

**Response:**
```json
{
  "can_reverse_all": false,
  "total_entries": 3,
  "valid_entries": 2,
  "invalid_entries": 1,
  "validations": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "JE-2024-001",
      "journal_entry_description": "Ventas del día",
      "current_status": "posted",
      "posted_date": "2024-01-15",
      "can_reverse": true,
      "errors": [],
      "warnings": [],
      "reversal_impact": {
        "affected_accounts": 4,
        "total_amount": "5000.00",
        "proposed_reversal_number": "JE-REV-2024-001"
      }
    },
    {
      "journal_entry_id": "uuid2",
      "journal_entry_number": "JE-2024-002",
      "journal_entry_description": "Compras del día",
      "current_status": "posted",
      "posted_date": "2024-01-15",
      "can_reverse": true,
      "errors": [],
      "warnings": ["Asiento con monto significativo: 25000.00"],
      "reversal_impact": {
        "affected_accounts": 6,
        "total_amount": "25000.00",
        "proposed_reversal_number": "JE-REV-2024-002"
      }
    },
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003",
      "journal_entry_description": "Asiento no contabilizado",
      "current_status": "approved",
      "can_reverse": false,
      "errors": ["Solo se pueden revertir asientos contabilizados (POSTED)"],
      "warnings": []
    }
  ],
  "global_impact": {
    "total_affected_accounts": 10,
    "total_reversal_amount": "30000.00",
    "reversal_period": "2024-01",
    "impact_on_balances": [
      {
        "account_code": "1110",
        "account_name": "Caja General",
        "current_balance": "15000.00",
        "balance_after_reversal": "10000.00",
        "impact": "-5000.00"
      }
    ]
  },
  "global_errors": [],
  "global_warnings": ["La reversión afectará saldos de 10 cuentas contables"]
}
```

### 2. Reversión Masiva

```http
POST /api/v1/journal-entries/bulk/reverse
```

**Request Body:**
```json
{
  "entry_ids": ["uuid1", "uuid2", "uuid3"],
  "reversed_by_id": "user-uuid",
  "reversal_date": "2024-01-31",
  "reason": "Reversión por corrección contable solicitada por auditoría",
  "confirm_impact": true
}
```

**Response:**
```json
{
  "operation_id": "bulk-reverse-uuid",
  "total_requested": 3,
  "total_reversed": 2,
  "total_failed": 1,
  "execution_time_ms": 3250,
  "reversed_entries": [
    {
      "original_entry": {
        "journal_entry_id": "uuid1",
        "journal_entry_number": "JE-2024-001",
        "previous_status": "posted",
        "new_status": "posted",
        "marked_as_reversed": true,
        "reversed_at": "2024-01-31T17:30:00Z",
        "reversed_by": "Ana López"
      },
      "reversal_entry": {
        "journal_entry_id": "new-uuid1",
        "journal_entry_number": "JE-REV-2024-001",
        "status": "posted",
        "description": "Reversión de JE-2024-001: Ventas del día",
        "posted_at": "2024-01-31T17:30:00Z",
        "reversal_of": "uuid1",
        "lines": [
          {
            "account_id": "acc1",
            "description": "REV: Ventas del día",
            "debit_amount": "0.00",
            "credit_amount": "5000.00"
          },
          {
            "account_id": "acc2",
            "description": "REV: Ventas del día",
            "debit_amount": "5000.00",
            "credit_amount": "0.00"
          }
        ]
      },
      "balance_impact": {
        "affected_accounts": 4,
        "total_amount": "5000.00",
        "balance_changes": [
          {
            "account_code": "1110",
            "account_name": "Caja General",
            "balance_before": "15000.00",
            "balance_after": "10000.00",
            "change": "-5000.00"
          }
        ]
      }
    },
    {
      "original_entry": {
        "journal_entry_id": "uuid2",
        "journal_entry_number": "JE-2024-002",
        "previous_status": "posted",
        "new_status": "posted",
        "marked_as_reversed": true,
        "reversed_at": "2024-01-31T17:30:01Z",
        "reversed_by": "Ana López"
      },
      "reversal_entry": {
        "journal_entry_id": "new-uuid2",
        "journal_entry_number": "JE-REV-2024-002",
        "status": "posted",
        "description": "Reversión de JE-2024-002: Compras del día",
        "posted_at": "2024-01-31T17:30:01Z",
        "reversal_of": "uuid2"
      },
      "balance_impact": {
        "affected_accounts": 6,
        "total_amount": "25000.00"
      }
    }
  ],
  "failed_entries": [
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "JE-2024-003",
      "current_status": "approved",
      "errors": ["Solo se pueden revertir asientos contabilizados (POSTED)"],
      "error_code": "INVALID_STATUS_FOR_REVERSAL"
    }
  ],
  "operation_summary": {
    "reason": "Reversión por corrección contable solicitada por auditoría",
    "executed_by": "Ana López",
    "executed_at": "2024-01-31T17:30:00Z",
    "reversal_date": "2024-01-31",
    "total_impact": {
      "affected_accounts": 10,
      "total_reversal_amount": "30000.00",
      "created_reversal_entries": 2
    }
  }
}
```

## Parámetros de Configuración

### Parámetros Requeridos

- **entry_ids**: Lista de IDs de asientos a revertir
- **reversal_date**: Fecha para los asientos de reversión
- **reason**: Razón detallada para la reversión

### Parámetros Opcionales

- **reversed_by_id**: ID del usuario que realiza la reversión
- **confirm_impact**: Confirmación explícita del impacto en saldos
- **auto_post_reversals**: Si los asientos de reversión se contabilizan automáticamente

### Límites del Sistema

- **Máximo de asientos por operación**: 25 (más restrictivo debido al impacto)
- **Timeout de operación**: 90 segundos (mayor debido a la complejidad)
- **Validación de integridad**: Completa antes y después de la operación

## Códigos de Error

### Errores por Asiento

- **INVALID_STATUS_FOR_REVERSAL**: Solo se pueden revertir asientos POSTED
- **ALREADY_REVERSED**: El asiento ya ha sido revertido
- **CLOSED_PERIOD**: El período para la fecha de reversión está cerrado
- **INACTIVE_ACCOUNTS**: Una o más cuentas están inactivas
- **INSUFFICIENT_PERMISSIONS**: Usuario sin permisos de reversión
- **DEPENDENT_ENTRIES**: Existen asientos posteriores que dependen de este asiento

### Errores Globales

- **BULK_REVERSE_LIMIT_EXCEEDED**: Se excedió el límite de asientos por operación
- **INVALID_REVERSAL_DATE**: Fecha de reversión no válida
- **IMPACT_NOT_CONFIRMED**: No se confirmó el impacto de la reversión
- **SEQUENCE_ERROR**: Error en secuencia numérica para reversiones
- **DATABASE_TRANSACTION_ERROR**: Error en transacción de base de datos

## Efectos de la Reversión

### En el Asiento Original

1. **Estado se mantiene**: El estado permanece como POSTED
2. **Marcado como revertido**: Se agrega flag de "reversed" = true
3. **Metadatos de reversión**: Se agregan fecha, usuario y razón de reversión
4. **Referencia al asiento de reversión**: Link al asiento que lo revierte

### En el Asiento de Reversión

1. **Nuevo asiento**: Se crea un nuevo asiento contable
2. **Numeración especial**: Numeración con prefijo "REV" o similar
3. **Líneas invertidas**: Todas las líneas con débitos y créditos invertidos
4. **Referencia al original**: Link al asiento que está revirtiendo
5. **Estado POSTED**: Se contabiliza automáticamente

### En los Saldos de Cuentas

1. **Restauración de saldos**: Los saldos vuelven al estado previo
2. **Historial preservado**: Se mantiene el historial completo de movimientos
3. **Trazabilidad completa**: Registro detallado de la operación de reversión

## Mejores Prácticas

### Para Usuarios

1. **Validar impacto**: Siempre revisar el impacto en saldos antes de revertir
2. **Fecha apropiada**: Usar fecha de reversión apropiada según políticas contables
3. **Razones detalladas**: Proporcionar razones específicas y documentadas
4. **Comunicación**: Informar a todos los interesados sobre reversiones importantes

### Para Desarrolladores

1. **Transacciones atómicas**: Asegurar atomicidad completa de la operación
2. **Validaciones exhaustivas**: Implementar todas las validaciones necesarias
3. **Logging completo**: Registrar cada paso de la reversión
4. **Integridad referencial**: Mantener consistencia de referencias

### Para Administradores

1. **Políticas claras**: Establecer políticas sobre cuándo y cómo revertir
2. **Permisos restrictivos**: Configurar permisos muy específicos para reversión
3. **Monitoreo intensivo**: Vigilar todas las operaciones de reversión
4. **Auditoría regular**: Revisar reversiones periódicamente

## Diferencias con Otras Operaciones

### Reversión vs Cancelación

- **Reversión**: Para asientos POSTED, crea asiento contrario
- **Cancelación**: Para asientos no POSTED, marca como cancelado
- **Impacto en saldos**: Reversión afecta saldos, cancelación no
- **Asientos adicionales**: Reversión crea nuevos asientos, cancelación no

### Reversión vs Eliminación

- **Reversión**: Preserva asiento original y crea reversión
- **Eliminación**: Remueve completamente el asiento
- **Auditoría**: Reversión mantiene trazabilidad completa
- **Impacto contable**: Reversión anula efectos, eliminación puede dejar inconsistencias

## Casos de Uso Avanzados

### Reversión Programada

```json
{
  "entry_ids": ["uuid1", "uuid2"],
  "reversed_by_id": "system-uuid",
  "reversal_date": "2024-01-31",
  "schedule_for": "2024-01-31T23:55:00Z",
  "reason": "Reversión automática de cierre para ajustes"
}
```

### Reversión Condicional

```json
{
  "entry_ids": ["uuid1", "uuid2"],
  "reversed_by_id": "supervisor-uuid",
  "reversal_date": "2024-01-31",
  "conditions": {
    "max_impact_per_account": 50000,
    "require_supervisor_approval": true,
    "validate_dependent_entries": true
  },
  "reason": "Reversión con validaciones adicionales"
}
```

## Integración con Reportes

### Impacto en Estados Financieros

- **Balance General**: Restauración de saldos a estado previo
- **Estado de Resultados**: Anulación de ingresos/gastos del período
- **Flujo de Efectivo**: Reversión de movimientos de efectivo
- **Notas a los Estados**: Registro de reversiones significativas

### Reportes de Reversión

- **Reporte de asientos revertidos**: Lista de todas las reversiones del período
- **Impacto de reversiones**: Análisis del impacto en estados financieros
- **Trazabilidad de reversiones**: Seguimiento completo de operaciones
- **Auditoría de reversiones**: Reporte para auditores externos

## Integración con Auditoría

### Información de Auditoría

1. **Registro completo**: Cada reversión se registra en detalle
2. **Justificación documentada**: Razones y autorización de reversiones
3. **Impacto cuantificado**: Medición exacta del impacto en saldos
4. **Trazabilidad temporal**: Línea de tiempo completa de operaciones

### Reportes para Auditores

1. **Lista de reversiones**: Todas las reversiones del período
2. **Análisis de patrones**: Identificación de reversiones frecuentes
3. **Validación de controles**: Verificación de que se siguieron procedimientos
4. **Impacto material**: Evaluación de materialidad de reversiones

## Troubleshooting

### Problemas Comunes

1. **Errores de secuencia**: Verificar configuración de numeración
2. **Problemas de integridad**: Validar consistencia de datos
3. **Timeouts en lotes grandes**: Reducir tamaño de lote
4. **Conflictos de concurrencia**: Manejar acceso simultáneo a asientos

### Herramientas de Diagnóstico

1. **Monitor de reversiones**: Seguimiento en tiempo real de operaciones
2. **Validador de integridad**: Verificación post-reversión de consistencia
3. **Analizador de impacto**: Herramienta para evaluar efectos de reversión
4. **Logs de auditoría**: Trazabilidad completa para diagnóstico

### Procedimientos de Recuperación

1. **Reversión de reversión**: Crear asiento que revierta la reversión
2. **Corrección manual**: Ajustes manuales cuando sea necesario
3. **Restauración desde backup**: En casos extremos
4. **Consulta a auditores**: Procedimiento para casos complejos
