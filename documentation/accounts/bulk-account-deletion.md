# Eliminación Múltiple de Cuentas

## Descripción General

El sistema de eliminación múltiple de cuentas proporciona capacidades avanzadas para la gestión masiva de cuentas contables, implementando validaciones exhaustivas y controles de seguridad para mantener la integridad del plan contable.

## Endpoints Disponibles

### 1. Validación Previa
**POST** `/api/v1/accounts/validate-deletion`

### 2. Eliminación Múltiple  
**POST** `/api/v1/accounts/bulk-delete`

## Características Principales

### Validaciones Exhaustivas

El sistema implementa múltiples niveles de validación:

#### Validaciones Críticas (Bloquean eliminación)
- **Movimientos contables**: La cuenta tiene asientos o transacciones asociadas
- **Cuentas hijas**: La cuenta tiene subcuentas dependientes en la jerarquía
- **Cuenta de sistema**: Cuentas principales del plan contable (códigos 1-6)
- **Cuenta inexistente**: El ID de cuenta no existe en el sistema

#### Advertencias (No bloquean eliminación)
- **Saldo pendiente**: La cuenta tiene un saldo diferente de cero
- **Cuenta inactiva**: La cuenta ya está marcada como inactiva

### Parámetros de Control

#### force_delete
- `false` (default): Solo elimina cuentas que pasan todas las validaciones
- `true`: Permite eliminación de cuentas con advertencias, respetando validaciones críticas

#### delete_reason
- Campo opcional para documentar la razón de la eliminación
- Recomendado para auditoría y trazabilidad

## Schemas de Datos

### BulkAccountDelete
```python
class BulkAccountDelete(BaseModel):
    account_ids: List[uuid.UUID] = Field(min_length=1, max_length=100)
    force_delete: bool = Field(default=False)
    delete_reason: Optional[str] = Field(default=None, max_length=500)
```

### BulkAccountDeleteResult
```python
class BulkAccountDeleteResult(BaseModel):
    total_requested: int
    successfully_deleted: List[uuid.UUID]
    failed_to_delete: List[dict]
    validation_errors: List[dict]
    warnings: List[str]
    
    # Propiedades calculadas
    success_count: int
    failure_count: int
    success_rate: float
```

### AccountDeleteValidation
```python
class AccountDeleteValidation(BaseModel):
    account_id: uuid.UUID
    can_delete: bool
    blocking_reasons: List[str]
    warnings: List[str]
    dependencies: dict
```

## Flujo de Trabajo Recomendado

### 1. Identificación de Cuentas
Identificar las cuentas que se desean eliminar usando consultas del sistema:

```http
GET /api/v1/accounts/?is_active=false&search=obsoleta
```

### 2. Validación Previa
Validar qué cuentas pueden eliminarse:

```http
POST /api/v1/accounts/validate-deletion
Content-Type: application/json

[
  "87654321-4321-4321-4321-987654321098",
  "12345678-5678-5678-5678-123456789012",
  "98765432-8765-8765-8765-987654321987"
]
```

### 3. Análisis de Resultados
Revisar el resultado de la validación:

```json
[
  {
    "account_id": "87654321-4321-4321-4321-987654321098",
    "can_delete": true,
    "blocking_reasons": [],
    "warnings": ["La cuenta tiene un saldo pendiente de 150.00"],
    "dependencies": {"balance": "150.00"}
  },
  {
    "account_id": "12345678-5678-5678-5678-123456789012",
    "can_delete": false,
    "blocking_reasons": ["La cuenta tiene 45 movimientos contables"],
    "warnings": [],
    "dependencies": {"movements_count": 45}
  }
]
```

### 4. Eliminación Controlada
Proceder con la eliminación basada en la validación:

```http
POST /api/v1/accounts/bulk-delete
Content-Type: application/json

{
  "account_ids": [
    "87654321-4321-4321-4321-987654321098"
  ],
  "force_delete": false,
  "delete_reason": "Limpieza de cuentas obsoletas del ejercicio 2024"
}
```

### 5. Procesamiento de Resultados
Analizar el resultado de la eliminación:

```json
{
  "total_requested": 1,
  "successfully_deleted": ["87654321-4321-4321-4321-987654321098"],
  "failed_to_delete": [],
  "validation_errors": [],
  "warnings": [
    "Cuenta 87654321-4321-4321-4321-987654321098: La cuenta tiene un saldo pendiente de 150.00",
    "Razón de eliminación: Limpieza de cuentas obsoletas del ejercicio 2024"
  ],
  "success_count": 1,
  "failure_count": 0,
  "success_rate": 100.0
}
```

## Casos de Uso

### Limpieza de Final de Ejercicio

**Objetivo**: Eliminar cuentas temporales o auxiliares del ejercicio anterior

```json
{
  "account_ids": ["uuid1", "uuid2", "uuid3"],
  "force_delete": false,
  "delete_reason": "Limpieza de cuentas auxiliares del ejercicio 2024"
}
```

**Validaciones especiales**:
- Verificar que no tengan saldos de arrastre
- Confirmar que no hay movimientos pendientes de procesamiento

### Migración de Plan de Cuentas

**Objetivo**: Eliminar cuentas del plan anterior durante migración

```json
{
  "account_ids": ["uuid1", "uuid2"],
  "force_delete": true,
  "delete_reason": "Migración a nuevo plan de cuentas según NIIF"
}
```

**Consideraciones**:
- Usar `force_delete: true` para cuentas con saldos que se migrarán
- Documentar mapping de cuentas eliminadas a nuevas cuentas

### Corrección de Errores

**Objetivo**: Eliminar cuentas creadas por error

```json
{
  "account_ids": ["uuid1"],
  "force_delete": false,
  "delete_reason": "Cuenta creada por error durante configuración inicial"
}
```

**Requisitos**:
- Solo eliminar si no tienen movimientos
- Preferir inactivación para cuentas con historial

## Consideraciones de Seguridad

### Permisos Requeridos
- Solo usuarios con rol **ADMIN** pueden ejecutar eliminaciones múltiples
- Los endpoints requieren autenticación JWT válida

### Límites Operacionales
- Máximo 100 cuentas por operación
- Validación de IDs únicos (no duplicados)
- Timeout de 30 segundos para operaciones grandes

### Auditoría
- Todas las eliminaciones se registran en logs del sistema
- El campo `delete_reason` es altamente recomendado
- Se mantiene historial de operaciones para auditoría

## Mejores Prácticas

### 1. Planificación
- Realizar respaldo completo antes de eliminaciones masivas
- Identificar y documentar impactos en reportes existentes
- Coordinar con usuarios finales sobre cambios en el plan

### 2. Validación
- Siempre ejecutar validación previa con `/validate-deletion`
- Revisar cuidadosamente los `blocking_reasons`
- Analizar dependencias reportadas en cada cuenta

### 3. Ejecución
- Procesar en lotes pequeños (10-50 cuentas)
- Usar `force_delete` solo cuando sea necesario
- Incluir siempre `delete_reason` descriptiva

### 4. Verificación
- Verificar resultados de cada operación
- Procesar cuentas fallidas individualmente si es necesario
- Validar integridad del plan de cuentas post-eliminación

### 5. Documentación
- Mantener registro de todas las operaciones masivas
- Documentar razones de negocio para eliminaciones
- Actualizar documentación del plan de cuentas

## Manejo de Errores

### Errores Comunes

#### Cuenta con Movimientos
```json
{
  "account_id": "uuid",
  "reason": "La cuenta tiene 45 movimientos contables",
  "details": {"movements_count": 45}
}
```
**Solución**: Transferir o consolidar movimientos antes de eliminar

#### Cuenta con Hijas
```json
{
  "account_id": "uuid", 
  "reason": "La cuenta tiene 3 cuentas hijas",
  "details": {"children_count": 3}
}
```
**Solución**: Eliminar primero las cuentas hijas o reasignar jerarquía

#### Cuenta de Sistema
```json
{
  "account_id": "uuid",
  "reason": "No se puede eliminar una cuenta de sistema"
}
```
**Solución**: Las cuentas principales (1-6) no pueden eliminarse

### Recuperación de Errores

En caso de errores durante la eliminación:

1. **Verificar estado**: Consultar qué cuentas se eliminaron exitosamente
2. **Reintento selectivo**: Procesar solo las cuentas fallidas
3. **Análisis de causa**: Revisar razones específicas de fallo
4. **Estrategia alternativa**: Considerar inactivación en lugar de eliminación

## Monitoreo y Logging

### Métricas Importantes
- Número de operaciones de eliminación múltiple por día
- Tasa de éxito promedio de las operaciones
- Cuentas más frecuentemente eliminadas por error

### Logs del Sistema
```
[2025-06-12 14:30:00] BULK_DELETE_START: user=admin, accounts=5, reason="Cleanup 2024"
[2025-06-12 14:30:02] BULK_DELETE_SUCCESS: account=uuid1, reason="Cleanup 2024"
[2025-06-12 14:30:02] BULK_DELETE_FAILED: account=uuid2, reason="Has movements"
[2025-06-12 14:30:02] BULK_DELETE_COMPLETE: success=3, failed=2, rate=60%
```

## Integración con Otros Módulos

### Impacto en Reportes
- Verificar que reportes no referencien cuentas eliminadas
- Actualizar filtros y consultas predefinidas
- Regenerar cache de estructuras contables

### Relación con Asientos
- Los asientos existentes no se ven afectados por eliminación de cuentas
- Nuevos asientos no podrán usar cuentas eliminadas
- Considerar migración de saldos antes de eliminación

### Sincronización con Sistemas Externos
- Notificar a sistemas integrados sobre cuentas eliminadas
- Actualizar mappings de cuentas en interfaces
- Verificar impacto en exportaciones automáticas

## Versionado y Compatibilidad

### Versión Actual: v1.0
- Implementación inicial de eliminación múltiple
- Validaciones exhaustivas
- Soporte para hasta 100 cuentas por operación

### Mejoras Futuras Planificadas
- Eliminación asíncrona para lotes muy grandes
- Papelera de reciclaje para restauración
- Plantillas de eliminación para casos comunes
- Dashboard de monitoreo en tiempo real
