# API de Productos - Documentación Completa

## Descripción General

La API de productos proporciona endpoints RESTful para la gestión completa de productos en el sistema contable. Incluye operaciones CRUD, gestión de inventario, búsquedas avanzadas y operaciones masivas.

## Base URL

```
/api/v1/products
```

## Autenticación

Todos los endpoints requieren autenticación JWT. Incluir el token en el header:

```
Authorization: Bearer <jwt_token>
```

## Endpoints Disponibles

### 1. Crear Producto

**POST** `/products`

Crea un nuevo producto en el sistema.

#### Request Body

```json
{
  "code": "PROD001",
  "name": "Producto de Ejemplo",
  "description": "Descripción detallada del producto",
  "product_type": "product",
  "status": "active",
  "current_stock": 100.00,
  "min_stock": 10.00,
  "max_stock": 1000.00,
  "cost_price": 50.00,
  "sale_price": 75.00,
  "tax_rate": 21.00,
  "tax_category": "standard",
  "income_account_id": "123e4567-e89b-12d3-a456-426614174000",
  "expense_account_id": "123e4567-e89b-12d3-a456-426614174001",
  "inventory_account_id": "123e4567-e89b-12d3-a456-426614174002",
  "measurement_unit": "unit",
  "is_active": true
}
```

#### Response

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "code": "PROD001",
  "name": "Producto de Ejemplo",
  "description": "Descripción detallada del producto",
  "product_type": "product",
  "status": "active",
  "current_stock": 100.00,
  "min_stock": 10.00,
  "max_stock": 1000.00,
  "cost_price": 50.00,
  "sale_price": 75.00,
  "profit_margin": 50.00,
  "tax_rate": 21.00,
  "tax_category": "standard",
  "income_account_id": "123e4567-e89b-12d3-a456-426614174000",
  "expense_account_id": "123e4567-e89b-12d3-a456-426614174001",
  "inventory_account_id": "123e4567-e89b-12d3-a456-426614174002",
  "measurement_unit": "unit",
  "is_active": true,
  "stock_status": "normal",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "created_by": "123e4567-e89b-12d3-a456-426614174004",
  "updated_by": "123e4567-e89b-12d3-a456-426614174004"
}
```

#### Códigos de Estado

- `201 Created`: Producto creado exitosamente
- `400 Bad Request`: Datos de entrada inválidos
- `409 Conflict`: Código de producto ya existe
- `422 Unprocessable Entity`: Error de validación

### 2. Listar Productos

**GET** `/products`

Obtiene una lista paginada de productos con filtros opcionales.

#### Query Parameters

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `skip` | int | Número de registros a omitir | `skip=0` |
| `limit` | int | Número máximo de registros | `limit=50` |
| `product_type` | string | Filtrar por tipo de producto | `product_type=product` |
| `status` | string | Filtrar por estado | `status=active` |
| `is_active` | boolean | Filtrar por productos activos | `is_active=true` |
| `low_stock` | boolean | Solo productos con stock bajo | `low_stock=true` |
| `category` | string | Filtrar por categoría fiscal | `category=standard` |
| `min_price` | decimal | Precio mínimo | `min_price=10.00` |
| `max_price` | decimal | Precio máximo | `max_price=100.00` |
| `sort_by` | string | Campo para ordenar | `sort_by=name` |
| `sort_order` | string | Orden ascendente/descendente | `sort_order=asc` |

#### Response

```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "code": "PROD001",
      "name": "Producto de Ejemplo",
      "product_type": "product",
      "status": "active",
      "current_stock": 100.00,
      "sale_price": 75.00,
      "stock_status": "normal",
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50,
  "pages": 1
}
```

### 3. Buscar Productos

**GET** `/products/search`

Realiza búsqueda por texto en código, nombre y descripción.

#### Query Parameters

| Parámetro | Tipo | Descripción | Requerido |
|-----------|------|-------------|-----------|
| `q` | string | Término de búsqueda | Sí |
| `limit` | int | Límite de resultados | No (default: 20) |

#### Response

```json
{
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "code": "PROD001",
      "name": "Producto de Ejemplo",
      "description": "Descripción detallada del producto",
      "sale_price": 75.00,
      "current_stock": 100.00,
      "status": "active"
    }
  ],
  "total_found": 1,
  "search_term": "ejemplo"
}
```

### 4. Obtener Producto por ID

**GET** `/products/{product_id}`

Obtiene los detalles completos de un producto específico.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Response

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "code": "PROD001",
  "name": "Producto de Ejemplo",
  "description": "Descripción detallada del producto",
  "product_type": "product",
  "status": "active",
  "current_stock": 100.00,
  "min_stock": 10.00,
  "max_stock": 1000.00,
  "cost_price": 50.00,
  "sale_price": 75.00,
  "profit_margin": 50.00,
  "tax_rate": 21.00,
  "tax_category": "standard",
  "income_account": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "4001",
    "name": "Ventas de Productos"
  },
  "expense_account": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "code": "5001",
    "name": "Costo de Ventas"
  },
  "inventory_account": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "code": "1301",
    "name": "Inventario de Productos"
  },
  "measurement_unit": "unit",
  "is_active": true,
  "stock_status": "normal",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "created_by": "123e4567-e89b-12d3-a456-426614174004",
  "updated_by": "123e4567-e89b-12d3-a456-426614174004"
}
```

#### Códigos de Estado

- `200 OK`: Producto encontrado
- `404 Not Found`: Producto no encontrado

### 5. Actualizar Producto

**PUT** `/products/{product_id}`

Actualiza los datos de un producto existente.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Request Body

```json
{
  "name": "Producto Actualizado",
  "description": "Nueva descripción",
  "sale_price": 80.00,
  "cost_price": 55.00,
  "max_stock": 1500.00,
  "tax_rate": 19.00
}
```

#### Response

Retorna el producto actualizado con la misma estructura que GET `/products/{product_id}`.

#### Códigos de Estado

- `200 OK`: Producto actualizado exitosamente
- `400 Bad Request`: Datos inválidos
- `404 Not Found`: Producto no encontrado
- `409 Conflict`: Conflicto con código existente

### 6. Eliminar Producto

**DELETE** `/products/{product_id}`

Realiza soft delete del producto (marca como inactivo).

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Response

```json
{
  "message": "Producto eliminado exitosamente",
  "product_id": "123e4567-e89b-12d3-a456-426614174003"
}
```

#### Códigos de Estado

- `200 OK`: Producto eliminado exitosamente
- `404 Not Found`: Producto no encontrado
- `409 Conflict`: Producto tiene movimientos asociados

### 7. Obtener Movimientos de Producto

**GET** `/products/{product_id}/movements`

Obtiene el historial de movimientos de inventario del producto.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Query Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `skip` | int | Registros a omitir |
| `limit` | int | Límite de registros |
| `start_date` | date | Fecha inicio (YYYY-MM-DD) |
| `end_date` | date | Fecha fin (YYYY-MM-DD) |
| `movement_type` | string | Tipo de movimiento |

#### Response

```json
{
  "movements": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174005",
      "product_id": "123e4567-e89b-12d3-a456-426614174003",
      "movement_type": "sale",
      "quantity": 5.00,
      "unit_price": 75.00,
      "total_amount": 375.00,
      "reference_type": "journal_entry",
      "reference_id": "123e4567-e89b-12d3-a456-426614174006",
      "previous_stock": 100.00,
      "new_stock": 95.00,
      "notes": "Venta a cliente ABC",
      "created_at": "2024-01-15T14:30:00Z",
      "created_by": "123e4567-e89b-12d3-a456-426614174004"
    }
  ],
  "total": 1,
  "current_stock": 95.00
}
```

### 8. Obtener Estadísticas de Producto

**GET** `/products/{product_id}/stats`

Obtiene estadísticas detalladas del producto.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Query Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `period` | string | Período (month, quarter, year) |
| `start_date` | date | Fecha inicio |
| `end_date` | date | Fecha fin |

#### Response

```json
{
  "product_id": "123e4567-e89b-12d3-a456-426614174003",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "sales": {
    "total_quantity": 50.00,
    "total_amount": 3750.00,
    "average_price": 75.00,
    "transactions_count": 10
  },
  "purchases": {
    "total_quantity": 200.00,
    "total_amount": 10000.00,
    "average_price": 50.00,
    "transactions_count": 4
  },
  "inventory": {
    "current_stock": 95.00,
    "stock_value": 4750.00,
    "turnover_ratio": 0.53,
    "days_of_inventory": 68.5
  },
  "profitability": {
    "gross_profit": 1250.00,
    "profit_margin": 33.33,
    "roi": 12.5
  }
}
```

### 9. Ajustar Stock

**POST** `/products/{product_id}/stock`

Realiza ajuste manual del stock del producto.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Request Body

```json
{
  "adjustment_type": "increase",
  "quantity": 50.00,
  "reason": "Reconteo de inventario",
  "unit_cost": 52.00,
  "reference_document": "ADJ-2024-001"
}
```

#### Tipos de Ajuste

- `increase`: Incrementar stock
- `decrease`: Decrementar stock
- `set`: Establecer stock absoluto

#### Response

```json
{
  "message": "Stock ajustado exitosamente",
  "product_id": "123e4567-e89b-12d3-a456-426614174003",
  "previous_stock": 95.00,
  "new_stock": 145.00,
  "adjustment_quantity": 50.00,
  "movement_id": "123e4567-e89b-12d3-a456-426614174007"
}
```

### 10. Operaciones Masivas

**POST** `/products/bulk`

Realiza operaciones masivas sobre múltiples productos.

#### Request Body

```json
{
  "operation": "update_prices",
  "products": [
    {
      "product_id": "123e4567-e89b-12d3-a456-426614174003",
      "data": {
        "sale_price": 80.00,
        "cost_price": 55.00
      }
    },
    {
      "product_id": "123e4567-e89b-12d3-a456-426614174008",
      "data": {
        "sale_price": 120.00,
        "cost_price": 85.00
      }
    }
  ]
}
```

#### Operaciones Disponibles

- `update_prices`: Actualizar precios
- `update_stock`: Actualizar stocks
- `change_status`: Cambiar estados
- `update_taxes`: Actualizar información fiscal

#### Response

```json
{
  "operation": "update_prices",
  "total_products": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "product_id": "123e4567-e89b-12d3-a456-426614174003",
      "status": "success",
      "message": "Precios actualizados"
    },
    {
      "product_id": "123e4567-e89b-12d3-a456-426614174008",
      "status": "success",
      "message": "Precios actualizados"
    }
  ]
}
```

### 11. Obtener Productos Activos

**GET** `/products/active`

Obtiene una lista de todos los productos activos en el sistema.

#### Response

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "code": "PROD001",
    "name": "Producto de Ejemplo",
    "product_type": "product",
    "current_stock": 100.00,
    "sale_price": 75.00
  }
]
```

### 12. Obtener Productos con Stock Bajo

**GET** `/products/low-stock`

Obtiene productos cuyo stock actual está por debajo del stock mínimo.

#### Response

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "code": "PROD001",
    "name": "Producto de Ejemplo",
    "current_stock": 5.00,
    "min_stock": 10.00,
    "stock_difference": -5.00,
    "urgency_level": "medium"
  }
]
```

### 13. Obtener Productos que Necesitan Reorden

**GET** `/products/need-reorder`

Obtiene productos que necesitan ser reordenados basado en stock mínimo y patrones de consumo.

#### Response

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "code": "PROD001",
    "name": "Producto de Ejemplo",
    "current_stock": 8.00,
    "min_stock": 10.00,
    "reorder_point": 15.00,
    "suggested_order_quantity": 50.00,
    "days_until_stockout": 7
  }
]
```

### 14. Obtener Producto por Código

**GET** `/products/code/{code}`

Busca un producto específico por su código único.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `code` | string | Código único del producto |

#### Response

```json
{
  "success": true,
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "code": "PROD001",
    "name": "Producto de Ejemplo",
    "description": "Descripción del producto",
    "product_type": "product",
    "status": "active",
    "current_stock": 100.00,
    "cost_price": 50.00,
    "sale_price": 75.00,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 15. Activar Producto

**POST** `/products/{product_id}/activate`

Activa un producto previamente desactivado.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Response

```json
{
  "success": true,
  "message": "Producto activado exitosamente",
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "status": "active",
    "updated_at": "2024-06-16T14:30:00Z"
  }
}
```

### 16. Desactivar Producto

**POST** `/products/{product_id}/deactivate`

Desactiva un producto sin eliminarlo del sistema.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Response

```json
{
  "success": true,
  "message": "Producto desactivado exitosamente",
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "status": "inactive",
    "updated_at": "2024-06-16T14:30:00Z"
  }
}
```

### 17. Descontinuar Producto

**POST** `/products/{product_id}/discontinue`

Marca un producto como descontinuado, impidiendo nuevas ventas pero manteniendo el historial.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Response

```json
{
  "success": true,
  "message": "Producto descontinuado exitosamente",
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "status": "discontinued",
    "updated_at": "2024-06-16T14:30:00Z"
  }
}
```

### 18. Agregar Stock

**POST** `/products/{product_id}/stock/add`

Incrementa el stock actual del producto.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Request Body

```json
{
  "quantity": 50.00,
  "unit_cost": 52.00,
  "reason": "Compra de mercadería",
  "reference": "OC-2024-001"
}
```

#### Response

```json
{
  "success": true,
  "message": "Stock agregado exitosamente",
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "previous_stock": 100.00,
    "added_quantity": 50.00,
    "new_stock": 150.00,
    "movement_id": "movement-uuid-here"
  }
}
```

### 19. Reducir Stock

**POST** `/products/{product_id}/stock/subtract`

Reduce el stock actual del producto.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `product_id` | UUID | ID único del producto |

#### Request Body

```json
{
  "quantity": 10.00,
  "reason": "Ajuste por inventario",
  "reference": "AJ-2024-001"
}
```

#### Response

```json
{
  "success": true,
  "message": "Stock reducido exitosamente",
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "previous_stock": 150.00,
    "subtracted_quantity": 10.00,
    "new_stock": 140.00,
    "movement_id": "movement-uuid-here"
  }
}
```

### 20. Eliminación Masiva de Productos

**POST** `/products/bulk-delete`

Elimina múltiples productos en una sola operación. Solo se pueden eliminar productos que no tengan dependencias críticas.

#### Request Body

```json
[
  "123e4567-e89b-12d3-a456-426614174003",
  "123e4567-e89b-12d3-a456-426614174004",
  "123e4567-e89b-12d3-a456-426614174005"
]
```

#### Response

```json
{
  "total_requested": 3,
  "total_processed": 2,
  "total_errors": 1,
  "successful_ids": [
    "123e4567-e89b-12d3-a456-426614174003",
    "123e4567-e89b-12d3-a456-426614174004"
  ],
  "errors": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174005",
      "error": "Producto tiene movimientos contables asociados"
    }
  ]
}
```

#### Validaciones de Eliminación

La eliminación está sujeta a las siguientes validaciones:

- **✅ Se puede eliminar si:**
  - El producto existe
  - No tiene movimientos contables asociados
  - No está referenciado en asientos contables
  - No tiene transacciones pendientes

- **❌ No se puede eliminar si:**
  - Tiene historial de movimientos
  - Está referenciado en facturas o documentos
  - Tiene asientos contables asociados

#### Validaciones Detalladas para Operaciones Bulk

### Validaciones para Eliminación Masiva

#### Validaciones Críticas (Bloquean eliminación)

1. **Existencia del Producto**
   ```
   Criterio: El producto debe existir en la base de datos
   Error: "Producto no existe"
   Acción: Ignorar ID del producto
   ```

2. **Movimientos Contables**
   ```
   Criterio: No debe tener asientos contables asociados
   Error: "Producto tiene movimientos contables asociados"
   Consulta: journal_entry_lines.product_id IS NOT NULL
   ```

3. **Facturas Pendientes**
   ```
   Criterio: No debe estar en facturas en estado borrador
   Error: "Producto referenciado en facturas pendientes"
   ```

4. **Órdenes de Compra Activas**
   ```
   Criterio: No debe tener órdenes de compra pendientes
   Error: "Producto tiene órdenes de compra activas"
   ```

#### Validaciones de Advertencia (No bloquean)

1. **Stock Actual**
   ```
   Condición: current_stock > 0
   Warning: "Producto tiene stock actual: {cantidad}"
   Recomendación: Considerar mover stock o ajustar inventario
   ```

2. **Estado Activo**
   ```
   Condición: status = "active"
   Warning: "Producto está activo - considere desactivar primero"
   Recomendación: Desactivar antes de eliminar
   ```

3. **Valor de Inventario**
   ```
   Condición: stock_value > umbral_crítico
   Warning: "Producto representa valor significativo: ${valor}"
   Recomendación: Aprobación adicional requerida
   ```

4. **Productos Recientes**
   ```
   Condición: created_at < 30 días
   Warning: "Producto creado recientemente"
   Recomendación: Verificar necesidad de eliminación
   ```

### Validaciones para Desactivación Masiva

#### Validaciones Críticas

1. **Existencia del Producto**
   ```
   Criterio: El producto debe existir
   Error: "Producto no encontrado"
   ```

2. **Estado Ya Inactivo**
   ```
   Criterio: Si ya está inactivo, omitir (no es error)
   Acción: Marcar como exitoso sin cambios
   ```

#### Validaciones de Advertencia

1. **Órdenes Pendientes**
   ```
   Condición: Tiene órdenes de venta/compra pendientes
   Warning: "Producto tiene órdenes pendientes"
   Recomendación: Completar o cancelar órdenes primero
   ```

2. **Stock Alto**
   ```
   Condición: current_stock > max_stock * 0.8
   Warning: "Producto tiene stock alto"
   Recomendación: Considerar liquidación de inventario
   ```

### Validaciones de Integridad del Sistema

#### Límites de Operación

```json
{
  "max_bulk_size": 100,
  "max_concurrent_operations": 5,
  "timeout_minutes": 10,
  "retry_attempts": 3
}
```

#### Validaciones de Permisos

1. **Permisos de Usuario**
   ```
   - products:delete_bulk (para eliminación masiva)
   - products:deactivate_bulk (para desactivación masiva)
   - products:validate_deletion (para validación previa)
   ```

2. **Validación de Empresa**
   ```
   - Productos deben pertenecer a la empresa del usuario
   - No se permite cross-company bulk operations
   ```

#### Validaciones de Negocio Específicas

1. **Productos Críticos**
   ```
   Condición: Marcados como "critical" o "essential"
   Acción: Requerir confirmación adicional
   Warning: "Producto marcado como crítico para operaciones"
   ```

2. **Productos con Garantía**
   ```
   Condición: Tienen garantías activas
   Warning: "Producto tiene garantías activas"
   Recomendación: Verificar impacto en servicio post-venta
   ```

3. **Productos Estacionales**
   ```
   Condición: Marcados como estacionales
   Warning: "Producto estacional - verificar temporada"
   Recomendación: Considerar desactivación temporal
   ```

### Implementación de Validaciones en el Código

#### Estructura de Respuesta de Validación

```json
{
  "product_id": "uuid",
  "product_code": "string",
  "product_name": "string", 
  "product_status": "active|inactive|discontinued",
  "current_stock": "decimal",
  "can_delete": "boolean",
  "can_deactivate": "boolean",
  "blocking_reasons": ["string"],
  "warnings": ["string"],
  "recommendations": ["string"],
  "estimated_stock_value": "decimal",
  "last_movement_date": "datetime",
  "creation_date": "datetime",
  "risk_level": "low|medium|high|critical"
}
```

#### Algoritmo de Validación

```python
def validate_product_for_deletion(product_id: UUID) -> ValidationResult:
    result = ValidationResult()
    
    # 1. Verificar existencia
    product = get_product(product_id)
    if not product:
        result.can_delete = False
        result.blocking_reasons.append("Producto no existe")
        return result
    
    # 2. Validaciones críticas
    if has_journal_entries(product_id):
        result.can_delete = False
        result.blocking_reasons.append("Tiene movimientos contables")
    
    if has_pending_orders(product_id):
        result.can_delete = False  
        result.blocking_reasons.append("Tiene órdenes pendientes")
    
    # 3. Validaciones de advertencia
    if product.current_stock > 0:
        result.warnings.append(f"Stock actual: {product.current_stock}")
        result.estimated_stock_value = calculate_stock_value(product)
    
    if product.status == "active":
        result.warnings.append("Producto activo - considerar desactivar")
    
    # 4. Evaluación de riesgo
    result.risk_level = calculate_risk_level(product, result)
    
    return result
```

#### Configuración de Límites

```python
BULK_OPERATION_LIMITS = {
    "max_products_per_batch": 100,
    "max_concurrent_operations": 5,
    "operation_timeout_seconds": 600,
    "max_retries": 3,
    "critical_stock_value_threshold": 10000.00,
    "recent_product_days": 30
}
```

---

## Flujo Recomendado para Gestión Masiva

### 1. Análisis Previo
```bash
# Validar qué productos se pueden eliminar
POST /api/v1/products/validate-deletion
```

### 2. Decisión Basada en Validación
- **Si can_delete = true y no hay warnings críticos**: Proceder con eliminación
- **Si can_delete = true pero hay warnings**: Considerar desactivación
- **Si can_delete = false**: Evaluar alternativas

### 3. Ejecución de la Acción
```bash
# Opción A: Eliminación (más restrictiva)
POST /api/v1/products/bulk-delete

# Opción B: Desactivación (más segura)
POST /api/v1/products/bulk-deactivate
```

### 4. Verificación de Resultados
- Revisar `total_processed` vs `total_requested`
- Analizar errores en el array `errors`
- Confirmar que `successful_ids` contiene los productos esperados

---

## Consideraciones de Rendimiento

### Limitaciones por Lote
- **Máximo recomendado**: 100 productos por operación
- **Para lotes grandes**: Dividir en múltiples requests
- **Timeout**: Operaciones pueden tardar según el volumen

### Transacciones
- Cada operación bulk se ejecuta en una transacción separada
- Si una operación falla, no afecta las demás
- Se recomienda validar antes de ejecutar para minimizar fallos

### Monitoreo
- Todas las operaciones se registran en logs de auditoría
- Se mantiene historial de cambios de estado
- Se puede rastrear quién ejecutó cada operación masiva

## Modelos de Datos

### ProductType (Enum)

```json
{
  "PRODUCT": "product",
  "SERVICE": "service", 
  "BOTH": "both"
}
```

### ProductStatus (Enum)

```json
{
  "ACTIVE": "active",
  "INACTIVE": "inactive",
  "DISCONTINUED": "discontinued"
}
```

### MeasurementUnit (Enum)

```json
{
  "UNIT": "unit",
  "KILOGRAM": "kg",
  "GRAM": "g",
  "LITER": "l",
  "MILLILITER": "ml",
  "METER": "m",
  "CENTIMETER": "cm",
  "INCH": "inch",
  "FOOT": "foot",
  "SQUARE_METER": "m2",
  "CUBIC_METER": "m3",
  "HOUR": "hour",
  "MINUTE": "minute",
  "PIECE": "piece",
  "PACKAGE": "package",
  "BOX": "box"
}
```

### StockStatus (Calculado)

```json
{
  "LOW": "low",      // current_stock <= min_stock
  "HIGH": "high",    // current_stock >= max_stock
  "NORMAL": "normal" // min_stock < current_stock < max_stock
}
```

## Códigos de Error

### 400 Bad Request

```json
{
  "detail": "Invalid input data",
  "errors": [
    {
      "field": "sale_price",
      "message": "Sale price must be greater than 0"
    }
  ]
}
```

### 404 Not Found

```json
{
  "detail": "Product not found",
  "product_id": "123e4567-e89b-12d3-a456-426614174003"
}
```

### 409 Conflict

```json
{
  "detail": "Product code already exists",
  "code": "PROD001"
}
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "cost_price"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}
```

### 423 Locked

```json
{
  "detail": "Product is locked for stock operations",
  "product_id": "123e4567-e89b-12d3-a456-426614174003"
}
```

### 406 Not Acceptable

```json
{
  "detail": "Cannot activate discontinued product",
  "product_status": "discontinued"
}
```

## Ejemplos de Uso

### Crear un producto completo

```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "LAPTOP001",
    "name": "Laptop HP ProBook 450",
    "description": "Laptop para oficina con Windows 11",
    "product_type": "product",
    "status": "active",
    "current_stock": 25,
    "min_stock": 5,
    "max_stock": 100,
    "cost_price": 800.00,
    "sale_price": 1200.00,
    "tax_rate": 21.00,
    "tax_category": "electronics",
    "measurement_unit": "unit",
    "income_account_id": "123e4567-e89b-12d3-a456-426614174000",
    "expense_account_id": "123e4567-e89b-12d3-a456-426614174001",
    "inventory_account_id": "123e4567-e89b-12d3-a456-426614174002"
  }'
```

### Buscar productos con filtros

```bash
curl -X GET "http://localhost:8000/api/v1/products?product_type=product&status=active&min_price=100&max_price=1000&sort_by=name&sort_order=asc&limit=20" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Ajustar stock de producto

```bash
curl -X POST "http://localhost:8000/api/v1/products/123e4567-e89b-12d3-a456-426614174003/stock" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "adjustment_type": "increase",
    "quantity": 10,
    "reason": "Compra nueva mercadería",
    "unit_cost": 810.00,
    "reference_document": "COMP-2024-001"
  }'
```

### Operación masiva de actualización de precios

```bash
curl -X POST "http://localhost:8000/api/v1/products/bulk" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "update_prices",
    "products": [
      {
        "product_id": "123e4567-e89b-12d3-a456-426614174003",
        "data": {
          "sale_price": 1250.00,
          "cost_price": 820.00
        }
      }
    ]
  }'
```

### Obtener todos los productos activos

```bash
curl -X GET "http://localhost:8000/api/v1/products/active" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Obtener productos con stock bajo

```bash
curl -X GET "http://localhost:8000/api/v1/products/low-stock" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Obtener productos que necesitan reorden

```bash
curl -X GET "http://localhost:8000/api/v1/products/need-reorder" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Obtener producto por código

```bash
curl -X GET "http://localhost:8000/api/v1/products/code/PROD001" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Activar un producto

```bash
curl -X POST "http://localhost:8000/api/v1/products/123e4567-e89b-12d3-a456-426614174003/activate" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Desactivar un producto

```bash
curl -X POST "http://localhost:8000/api/v1/products/123e4567-e89b-12d3-a456-426614174003/deactivate" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Descontinuar un producto

```bash
curl -X POST "http://localhost:8000/api/v1/products/123e4567-e89b-12d3-a456-426614174003/discontinue" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Agregar stock a un producto

```bash
curl -X POST "http://localhost:8000/api/v1/products/123e4567-e89b-12d3-a456-426614174003/stock/add" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 20,
    "unit_cost": 55.00,
    "reason": "Compra de insumos",
    "reference": "OC-2024-002"
  }'
```

### Reducir stock de un producto

```bash
curl -X POST "http://localhost:8000/api/v1/products/123e4567-e89b-12d3-a456-426614174003/stock/subtract" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 5,
    "reason": "Venta de productos",
    "reference": "VTA-2024-003"
  }'
```

## Integración con Asientos Contables

Los productos se integran con los asientos contables a través de las líneas de asiento (`JournalEntryLine`). Cada línea puede referenciar un producto y especificar:

- Cantidad del producto
- Precio unitario
- Descuentos aplicados
- Impuestos calculados

### Ejemplo de asiento con productos

```json
{
  "date": "2024-01-15",
  "description": "Venta de laptop a cliente ABC",
  "transaction_origin": "sale",
  "lines": [
    {
      "account_id": "account_caja_id",
      "debit": 1452.00,
      "credit": 0,
      "description": "Cobro en efectivo"
    },
    {
      "account_id": "income_account_id",
      "debit": 0,
      "credit": 1200.00,
      "description": "Venta de laptop",
      "product_id": "123e4567-e89b-12d3-a456-426614174003",
      "quantity": 1,
      "unit_price": 1200.00,
      "tax_percentage": 21.00,
      "tax_amount": 252.00
    },
    {
      "account_id": "tax_account_id",
      "debit": 0,
      "credit": 252.00,
      "description": "IVA venta"
    }
  ]
}
```

Esta integración permite trazabilidad completa desde el producto hasta la contabilidad y control automático de inventarios.

## Cambios en la Documentación

- Se agregaron los endpoints de eliminación masiva, validación previa de eliminación y desactivación masiva de productos.
- Se actualizaron ejemplos y secciones relevantes para reflejar los cambios en la API.
