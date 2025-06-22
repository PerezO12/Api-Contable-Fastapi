# Implementación de Operaciones Bulk para Productos

## Resumen

Este documento detalla la implementación de las operaciones masivas (bulk) para productos en la API Contable, incluyendo eliminación masiva, desactivación masiva y validación previa de eliminación.

## Endpoints Implementados

### 1. POST /products/bulk-delete
- **Propósito**: Eliminar múltiples productos en una sola operación
- **Restricciones**: Solo productos sin dependencias críticas
- **Validaciones**: Movimientos contables, referencias activas

### 2. POST /products/bulk-deactivate  
- **Propósito**: Desactivar múltiples productos preservando historial
- **Ventajas**: Menos restrictivo, reversible, mantiene integridad
- **Casos de uso**: Productos estacionales, descontinuados temporalmente

### 3. POST /products/validate-deletion
- **Propósito**: Validar pre-eliminación sin ejecutar cambios
- **Información**: Bloqueos, advertencias, recomendaciones
- **Flujo**: Ejecutar antes de bulk-delete para prevenir errores

## Arquitectura de Implementación

### Estructura de Archivos

```
app/
├── api/v1/products.py          # Endpoints bulk implementados
├── schemas/product.py          # Esquemas de request/response
├── services/product_service.py # Lógica de negocio
└── models/product.py          # Modelo de datos
```

### Esquemas de Datos

#### BulkProductOperationResult
```python
class BulkProductOperationResult(BaseModel):
    total_requested: int         # Total de productos solicitados
    total_processed: int         # Total procesados exitosamente  
    total_errors: int           # Total con errores
    successful_ids: List[UUID]  # IDs procesados exitosamente
    errors: List[dict]          # Detalles de errores
```

#### Estructura de Errores
```python
{
    "id": "uuid",
    "error": "descripción del error"
}
```

### Validaciones Implementadas

#### Para Eliminación (bulk-delete)
1. **Existencia del producto**
2. **Sin movimientos contables asociados** 
3. **Sin referencias en asientos activos**
4. **Sin transacciones pendientes**

#### Para Desactivación (bulk-deactivate)
1. **Existencia del producto**
2. **Estado actual (omite si ya inactivo)**

#### Para Validación (validate-deletion)
1. **Todas las validaciones de eliminación**
2. **Advertencias de negocio**
3. **Cálculo de valor de stock**
4. **Evaluación de riesgo**

## Flujo de Operación Recomendado

### Paso 1: Validación Previa
```bash
POST /api/v1/products/validate-deletion
Content-Type: application/json

["uuid1", "uuid2", "uuid3"]
```

### Paso 2: Análisis de Respuesta
```json
[
  {
    "product_id": "uuid1",
    "can_delete": true,
    "warnings": ["Stock actual: 50.0"],
    "blocking_reasons": []
  },
  {
    "product_id": "uuid2", 
    "can_delete": false,
    "blocking_reasons": ["Tiene movimientos contables"]
  }
]
```

### Paso 3: Decisión de Estrategia
- **can_delete = true, sin warnings**: Proceder con eliminación
- **can_delete = true, con warnings**: Considerar desactivación
- **can_delete = false**: Evaluar alternativas o correcciones

### Paso 4: Ejecución
```bash
# Opción A: Eliminación
POST /api/v1/products/bulk-delete

# Opción B: Desactivación  
POST /api/v1/products/bulk-deactivate
```

## Características Técnicas

### Manejo de Errores
- **Transacciones independientes**: Cada producto se procesa individualmente
- **Fallos parciales**: Un error no afecta otros productos
- **Información detallada**: Errores específicos para cada producto

### Rendimiento
- **Límite recomendado**: 100 productos por operación
- **Timeout**: 10 minutos máximo de ejecución
- **Optimización**: Consultas batch para validaciones

### Auditoría
- **Logs detallados**: Todas las operaciones se registran
- **Trazabilidad**: Usuario y timestamp para cada operación
- **Historial**: Cambios de estado se mantienen

## Casos de Uso Específicos

### 1. Limpieza de Inventario
```python
# Escenario: Eliminar productos obsoletos
products_to_validate = get_obsolete_products()
validation_result = validate_deletion(products_to_validate)

# Filtrar solo los que se pueden eliminar sin riesgo
safe_to_delete = [p for p in validation_result 
                 if p.can_delete and not p.warnings]

# Ejecutar eliminación
delete_result = bulk_delete(safe_to_delete)
```

### 2. Gestión Estacional
```python
# Escenario: Desactivar productos fuera de temporada
seasonal_products = get_products_by_category("seasonal")

# Desactivar (más seguro que eliminar)
deactivate_result = bulk_deactivate(seasonal_products)
```

### 3. Migración de Datos
```python
# Escenario: Consolidar productos duplicados
duplicates = find_duplicate_products()

# Validar antes de eliminar
validation = validate_deletion(duplicates)

# Procesar solo los seguros
safe_duplicates = filter_safe_products(validation)
delete_result = bulk_delete(safe_duplicates)
```

## Mejores Prácticas

### 1. Siempre Validar Primero
```python
# ❌ Incorrecto
result = bulk_delete(product_ids)

# ✅ Correcto  
validation = validate_deletion(product_ids)
if all(p.can_delete for p in validation):
    result = bulk_delete(product_ids)
```

### 2. Manejar Errores Graciosamente
```python
result = bulk_delete(product_ids)

if result.total_errors > 0:
    # Procesar errores
    for error in result.errors:
        log_error(f"Failed to delete {error['id']}: {error['error']}")
    
    # Reintentar solo los que fallaron si es apropiado
    failed_ids = [error['id'] for error in result.errors]
    # ... lógica de reintento
```

### 3. Considerar Desactivación como Alternativa
```python
# Para productos con historial, prefiera desactivación
if has_historical_data(product_ids):
    result = bulk_deactivate(product_ids)  # Más seguro
else:
    result = bulk_delete(product_ids)      # OK para productos nuevos
```

### 4. Operaciones en Lotes
```python
# Para grandes volúmenes, dividir en lotes
def process_large_deletion(product_ids: List[UUID]):
    batch_size = 100
    for i in range(0, len(product_ids), batch_size):
        batch = product_ids[i:i + batch_size]
        result = bulk_delete(batch)
        # Procesar resultado del lote
        time.sleep(1)  # Evitar sobrecarga
```

## Configuración del Sistema

### Variables de Entorno
```bash
BULK_OPERATION_MAX_SIZE=100
BULK_OPERATION_TIMEOUT=600
BULK_OPERATION_MAX_CONCURRENT=5
```

### Permisos Requeridos
```json
{
  "products:bulk_delete": "Permitir eliminación masiva",
  "products:bulk_deactivate": "Permitir desactivación masiva", 
  "products:validate_deletion": "Permitir validación previa"
}
```

## Monitoreo y Métricas

### Métricas Recomendadas
- **Volumen de operaciones bulk por día**
- **Tasa de éxito/error por operación**
- **Tiempo promedio de ejecución**
- **Productos más frecuentemente eliminados**

### Alertas
- **Operaciones bulk frecuentes**: Posible problema de datos
- **Alta tasa de errores**: Revisar validaciones
- **Operaciones de gran volumen**: Verificar autorización

## Futuras Mejoras

### Capacidades Adicionales
1. **Bulk Update**: Actualización masiva de propiedades
2. **Bulk Transfer**: Transferencia masiva entre categorías
3. **Bulk Pricing**: Actualización masiva de precios

### Optimizaciones
1. **Procesamiento asíncrono**: Para volúmenes muy grandes
2. **Cache de validaciones**: Reducir consultas repetitivas
3. **Índices específicos**: Optimizar consultas de validación

### Integraciones
1. **Workflow de aprobación**: Para operaciones críticas
2. **Notificaciones**: Alertar a stakeholders relevantes
3. **Backup automático**: Antes de eliminaciones masivas

## Conclusión

La implementación de operaciones bulk para productos proporciona:
- **Eficiencia**: Procesamiento masivo optimizado
- **Seguridad**: Validaciones exhaustivas
- **Flexibilidad**: Múltiples estrategias (eliminar vs desactivar)
- **Trazabilidad**: Auditoría completa de operaciones

Las validaciones implementadas garantizan la integridad de datos mientras permiten operaciones eficientes de mantenimiento de inventario.
