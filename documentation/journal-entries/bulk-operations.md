# Operaciones Masivas de Asientos Contables

## Descripción General

Las operaciones masivas permiten ejecutar acciones sobre múltiples asientos contables de manera eficiente y controlada. El sistema soporta las siguientes operaciones:

- **Aprobación masiva** (Bulk Approve)
- **Contabilización masiva** (Bulk Post)
- **Cancelación masiva** (Bulk Cancel)  
- **Reversión masiva** (Bulk Reverse)
- **Restablecimiento masivo a borrador** (Bulk Reset to Draft)
- **Eliminación masiva** (Bulk Delete)

## Arquitectura de Operaciones Masivas

### Flujo General
1. **Validación previa**: Cada asiento se valida individualmente antes de la operación
2. **Procesamiento**: Se ejecuta la operación sobre los asientos válidos
3. **Reporte de resultados**: Se devuelve un resumen detallado de éxitos y fallos

### Principios de Diseño
- **Atomicidad por asiento**: Cada asiento se procesa independientemente
- **Continuidad en errores**: Un error en un asiento no impide procesar los demás
- **Trazabilidad completa**: Registro detallado de cada operación y resultado
- **Validaciones estrictas**: Respeto de todas las reglas de negocio

## Operaciones Soportadas

### 1. Aprobación Masiva (Bulk Approve)

#### Endpoint
```
POST /api/v1/journal-entries/bulk-approve
POST /api/v1/journal-entries/bulk-approve/validate
```

#### Descripción
Permite aprobar múltiples asientos contables simultáneamente.

#### Validaciones
- El asiento debe estar en estado `DRAFT` o `PENDING`
- El asiento debe estar balanceado
- Todas las cuentas deben existir y estar activas
- Se requiere permisos de aprobación

#### Parámetros de Entrada
```json
{
  "journal_entry_ids": ["uuid1", "uuid2", "uuid3"],
  "approved_by_id": "user-uuid",
  "force_approve": false,
  "reason": "Aprobación masiva del cierre mensual"
}
```

#### Respuesta
```json
{
  "total_requested": 3,
  "total_approved": 2,
  "total_failed": 1,
  "approved_entries": [
    {
      "journal_entry_id": "uuid1",
      "journal_entry_number": "AST-2024-001",
      "journal_entry_description": "Asiento de prueba",
      "current_status": "DRAFT",
      "can_approve": true,
      "errors": [],
      "warnings": []
    }
  ],
  "failed_entries": [
    {
      "journal_entry_id": "uuid3",
      "journal_entry_number": "AST-2024-003",
      "journal_entry_description": "Asiento desbalanceado",
      "current_status": "DRAFT",
      "can_approve": false,
      "errors": ["El asiento no está balanceado"],
      "warnings": []
    }
  ],
  "errors": [],
  "warnings": []
}
```

### 2. Contabilización Masiva (Bulk Post)

#### Endpoint
```
POST /api/v1/journal-entries/bulk-post
POST /api/v1/journal-entries/bulk-post/validate
```

#### Descripción
Permite contabilizar múltiples asientos aprobados, afectando los saldos de las cuentas.

#### Validaciones
- El asiento debe estar en estado `APPROVED`
- El asiento debe estar balanceado
- Las cuentas deben permitir movimientos
- El período contable debe estar abierto

#### Parámetros de Entrada
```json
{
  "journal_entry_ids": ["uuid1", "uuid2"],
  "posted_by_id": "user-uuid",
  "force_post": false,
  "reason": "Contabilización masiva del período"
}
```

### 3. Cancelación Masiva (Bulk Cancel)

#### Endpoint
```
POST /api/v1/journal-entries/bulk-cancel
POST /api/v1/journal-entries/bulk-cancel/validate
```

#### Descripción
Permite cancelar múltiples asientos contables simultáneamente.

#### Validaciones
- El asiento NO debe estar en estado `POSTED`
- El asiento NO debe estar ya `CANCELLED`
- Se requiere razón de cancelación

#### Parámetros de Entrada
```json
{
  "journal_entry_ids": ["uuid1", "uuid2"],
  "cancelled_by_id": "user-uuid",
  "reason": "Cancelación por error en el período"
}
```

### 4. Reversión Masiva (Bulk Reverse)

#### Endpoint
```
POST /api/v1/journal-entries/bulk/reverse
POST /api/v1/journal-entries/bulk/reverse/validate
```

#### Descripción
Permite revertir múltiples asientos contabilizados, creando asientos de reversión.

#### Validaciones
- El asiento debe estar en estado `POSTED`
- El asiento NO debe estar ya revertido
- Se requiere razón de reversión

#### Parámetros de Entrada
```json
{
  "journal_entry_ids": ["uuid1", "uuid2"],
  "reversed_by_id": "user-uuid",
  "reversal_date": "2024-01-15",
  "reason": "Reversión por corrección contable"
}
```

### 5. Restablecimiento Masivo a Borrador (Bulk Reset to Draft)

#### Endpoints
```
POST /api/v1/journal-entries/{id}/reset-to-draft                    # Individual
POST /api/v1/journal-entries/validate-reset-to-draft               # Validación masiva
POST /api/v1/journal-entries/bulk-reset-to-draft                   # Ejecución masiva
```

#### Descripción
Permite restablecer múltiples asientos a estado borrador, tanto individualmente como en operaciones masivas.

#### Validaciones
- El asiento debe estar en estado `APPROVED` o `PENDING`
- El asiento NO debe estar `POSTED` o `CANCELLED`
- Se requiere razón para el restablecimiento

#### Parámetros de Entrada (Individual)
```json
{
  "reason": "Corrección necesaria antes de contabilización"
}
```

#### Parámetros de Entrada (Masivo)
```json
{
  "journal_entry_ids": ["uuid1", "uuid2"],
  "force_reset": false,
  "reason": "Restablecimiento masivo para correcciones"
}
```

### 6. Eliminación Masiva (Bulk Delete)

#### Endpoint
```
POST /api/v1/journal-entries/bulk/delete
POST /api/v1/journal-entries/bulk/delete/validate
```

#### Descripción
Permite eliminar múltiples asientos contables simultáneamente.

#### Validaciones
- El asiento debe estar en estado `DRAFT` o `CANCELLED`
- El asiento NO debe estar `POSTED`

## Consideraciones de Rendimiento

### Optimizaciones Implementadas
- **Procesamiento por lotes**: Se procesan múltiples asientos en una sola transacción
- **Validaciones previas**: Se validan todos los asientos antes del procesamiento
- **Carga eficiente**: Uso de `selectinload` para cargar relaciones
- **Índices optimizados**: Búsquedas eficientes por ID y estado

### Límites Recomendados
- **Máximo por operación**: 100 asientos contables
- **Timeout**: 30 segundos por operación masiva
- **Memoria**: Optimizado para procesar hasta 1000 líneas contables

## Casos de Uso Comunes

### 1. Cierre Mensual
```json
{
  "operation": "bulk_approve",
  "journal_entry_ids": ["uuid1", "uuid2", ...],
  "approved_by_id": "supervisor-uuid",
  "reason": "Aprobación del cierre mensual de enero 2024"
}
```

### 2. Corrección de Errores
```json
{
  "operation": "bulk_reset_to_draft",
  "journal_entry_ids": ["uuid1", "uuid2"],
  "reset_by_id": "accountant-uuid",
  "reason": "Corrección de cuentas contables incorrectas"
}
```

### 3. Reversión de Período
```json
{
  "operation": "bulk_reverse",
  "journal_entry_ids": ["uuid1", "uuid2"],
  "reversed_by_id": "supervisor-uuid",
  "reversal_date": "2024-01-31",
  "reason": "Reversión del cierre por ajustes adicionales"
}
```

## Manejo de Errores

### Errores Comunes
- **JournalEntryError**: Error específico del asiento contable
- **ValidationError**: Error de validación de datos
- **PermissionError**: Error de permisos insuficientes
- **DatabaseError**: Error de base de datos

### Estrategia de Recuperación
1. **Validación previa**: Usar endpoints de validación antes de ejecutar
2. **Procesamiento parcial**: Continuar con asientos válidos aunque algunos fallen
3. **Logs detallados**: Registro completo de errores para auditoría
4. **Rollback granular**: Solo se revierten operaciones fallidas

## Auditoría y Trazabilidad

### Información Registrada
- **Usuario ejecutor**: ID del usuario que ejecuta la operación
- **Timestamp**: Fecha y hora exacta de la operación
- **Razón**: Motivo de la operación masiva
- **Resultados**: Detalle de éxitos y fallos
- **Cambios de estado**: Registro de transiciones de estado

### Reportes de Auditoría
- **Log de operaciones masivas**: Historial completo
- **Cambios por asiento**: Trazabilidad individual
- **Estadísticas de uso**: Métricas de operaciones masivas

## Mejores Prácticas

### Para Desarrolladores
1. **Usar validaciones previas**: Siempre validar antes de ejecutar
2. **Manejar timeouts**: Implementar timeouts apropiados
3. **Procesar en lotes**: No exceder límites recomendados
4. **Registrar errores**: Logging completo para debugging

### Para Usuarios
1. **Validar primero**: Usar endpoints de validación
2. **Lotes pequeños**: Procesar en grupos manejables
3. **Razones claras**: Proporcionar razones descriptivas
4. **Verificar resultados**: Revisar reportes de resultado

### Para Administradores
1. **Monitorear rendimiento**: Vigilar tiempos de respuesta
2. **Configurar límites**: Ajustar límites según capacidad
3. **Auditar regularmente**: Revisar logs de operaciones masivas
4. **Capacitar usuarios**: Entrenar en mejores prácticas

## Integración con Frontend

### Componentes Recomendados
- **Selector masivo**: Para seleccionar múltiples asientos
- **Validador previo**: Mostrar validaciones antes de ejecutar
- **Barra de progreso**: Indicar progreso de operación
- **Reporte de resultados**: Mostrar resumen detallado

### Flujo de Usuario
1. **Selección**: Usuario selecciona asientos objetivo
2. **Validación**: Sistema valida operación solicitada
3. **Confirmación**: Usuario confirma después de ver validaciones
4. **Ejecución**: Sistema ejecuta operación masiva
5. **Resultado**: Usuario recibe reporte detallado

## Seguridad

### Controles Implementados
- **Autenticación requerida**: Token JWT válido
- **Autorización granular**: Permisos específicos por operación
- **Validación de entrada**: Sanitización de parámetros
- **Límites de tasa**: Rate limiting para operaciones masivas

### Permisos Requeridos
- `journal_entries.bulk_approve`: Aprobación masiva
- `journal_entries.bulk_post`: Contabilización masiva
- `journal_entries.bulk_cancel`: Cancelación masiva
- `journal_entries.bulk_reverse`: Reversión masiva
- `journal_entries.bulk_reset`: Restablecimiento masivo
- `journal_entries.bulk_delete`: Eliminación masiva
