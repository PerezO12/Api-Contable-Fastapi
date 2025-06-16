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
