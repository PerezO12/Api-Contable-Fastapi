# Endpoints de Centros de Costo

Este documento describe todos los endpoints disponibles para la gestión de centros de costo, incluyendo operaciones CRUD, consultas especializadas y reportes avanzados.

## Base URL
```
/api/v1/cost-centers
/api/v1/cost-center-reports
```

## Autenticación
Todos los endpoints requieren autenticación JWT válida:
```http
Authorization: Bearer <jwt_token>
```

---

## Endpoints CRUD

### **GET** `/api/v1/cost-centers`
Listar centros de costo con filtros y paginación.

#### Parámetros de Query
```typescript
interface CostCenterFilters {
  code?: string;           // Filtrar por código (búsqueda parcial)
  name?: string;           // Filtrar por nombre (búsqueda parcial)
  parent_id?: UUID;        // Filtrar por centro padre
  is_active?: boolean;     // Filtrar por estado activo
  level?: number;          // Filtrar por nivel jerárquico
  has_children?: boolean;  // Filtrar si tiene centros hijos
  
  // Filtros de fecha
  created_after?: date;    // Creados después de fecha
  created_before?: date;   // Creados antes de fecha
  
  // Ordenamiento
  order_by?: 'code' | 'name' | 'created_at' | 'level';
  order_desc?: boolean;
  
  // Paginación
  skip?: number;           // Elementos a omitir (default: 0)
  limit?: number;          // Elementos por página (default: 100, max: 1000)
}
```

#### Ejemplo de Solicitud
```http
GET /api/v1/cost-centers?is_active=true&order_by=code&limit=50
```

#### Respuesta Exitosa
```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "code": "CC001",
      "name": "Ventas Nacional",
      "description": "Centro de costo para ventas nacionales",
      "parent_id": null,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "level": 0,
      "full_code": "CC001",
      "is_leaf": false,
      "parent_name": null,
      "children_count": 3,
      "movements_count": 156
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 50
}
```

### **POST** `/api/v1/cost-centers`
Crear nuevo centro de costo.

#### Cuerpo de la Solicitud
```json
{
  "code": "CC001",
  "name": "Ventas Nacional",
  "description": "Centro de costo para ventas nacionales",
  "parent_id": null,
  "is_active": true
}
```

#### Respuesta Exitosa (201)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "CC001",
  "name": "Ventas Nacional",
  "description": "Centro de costo para ventas nacionales",
  "parent_id": null,
  "is_active": true,
  "created_at": "2024-12-11T10:30:00Z",
  "updated_at": "2024-12-11T10:30:00Z",
  "level": 0,
  "full_code": "CC001",
  "is_leaf": true,
  "parent_name": null,
  "children_count": 0,
  "movements_count": 0
}
```

### **GET** `/api/v1/cost-centers/{id}`
Obtener centro de costo específico por ID.

#### Parámetros de Ruta
- `id`: UUID del centro de costo

#### Respuesta Exitosa
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "CC001",
  "name": "Ventas Nacional",
  "description": "Centro de costo para ventas nacionales",
  "parent_id": null,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "level": 0,
  "full_code": "CC001",
  "is_leaf": false,
  "parent_name": null,
  "children_count": 3,
  "movements_count": 156
}
```

### **PUT** `/api/v1/cost-centers/{id}`
Actualizar centro de costo existente.

#### Cuerpo de la Solicitud
```json
{
  "name": "Ventas Nacional Actualizado",
  "description": "Descripción actualizada",
  "parent_id": "456e7890-e89b-12d3-a456-426614174000",
  "is_active": true
}
```

#### Respuesta Exitosa
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "CC001",
  "name": "Ventas Nacional Actualizado",
  "description": "Descripción actualizada",
  "parent_id": "456e7890-e89b-12d3-a456-426614174000",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-12-11T14:30:00Z",
  "level": 1,
  "full_code": "PARENT.CC001",
  "is_leaf": false,
  "parent_name": "Centro Padre",
  "children_count": 3,
  "movements_count": 156
}
```

### **DELETE** `/api/v1/cost-centers/{id}`
Desactivar centro de costo (soft delete).

#### Respuesta Exitosa (204)
```
No Content
```

---

## Endpoints de Consulta

### **GET** `/api/v1/cost-centers/hierarchy`
Obtener estructura jerárquica completa.

#### Parámetros de Query
```typescript
interface HierarchyParams {
  root_id?: UUID;          // ID del centro raíz (opcional)
  include_inactive?: boolean; // Incluir centros inactivos
  max_depth?: number;      // Profundidad máxima (default: 10)
  include_metrics?: boolean; // Incluir métricas básicas
}
```

#### Ejemplo de Solicitud
```http
GET /api/v1/cost-centers/hierarchy?include_metrics=true
```

#### Respuesta Exitosa
```json
{
  "hierarchy": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "code": "CC001",
      "name": "Ventas",
      "level": 0,
      "is_active": true,
      "children": [
        {
          "id": "456e7890-e89b-12d3-a456-426614174000",
          "code": "CC001.001",
          "name": "Ventas Norte",
          "level": 1,
          "is_active": true,
          "children": [],
          "total_revenue": 500000.00,
          "total_costs": 350000.00,
          "net_margin": 30.0
        }
      ],
      "total_revenue": 1200000.00,
      "total_costs": 840000.00,
      "net_margin": 30.0
    }
  ],
  "total_centers": 15,
  "max_depth": 3
}
```

### **GET** `/api/v1/cost-centers/search`
Búsqueda avanzada de centros de costo.

#### Parámetros de Query
```typescript
interface SearchParams {
  q: string;               // Término de búsqueda (requerido)
  limit?: number;          // Límite de resultados (default: 10)
  include_inactive?: boolean; // Incluir centros inactivos
  search_fields?: string[]; // Campos a buscar: code, name, description
}
```

#### Ejemplo de Solicitud
```http
GET /api/v1/cost-centers/search?q=ventas&limit=5
```

#### Respuesta Exitosa
```json
{
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "code": "CC001",
      "name": "Ventas Nacional",
      "full_code": "CC001",
      "level": 0,
      "is_active": true,
      "match_score": 0.95
    }
  ],
  "total": 3,
  "search_term": "ventas"
}
```

### **GET** `/api/v1/cost-centers/{id}/children`
Obtener centros de costo hijos.

#### Parámetros de Query
```typescript
interface ChildrenParams {
  include_inactive?: boolean; // Incluir hijos inactivos
  recursive?: boolean;        // Incluir todos los descendientes
}
```

#### Respuesta Exitosa
```json
{
  "children": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174000",
      "code": "CC001.001",
      "name": "Ventas Norte",
      "level": 1,
      "is_active": true,
      "children_count": 2
    }
  ],
  "total": 3
}
```

### **GET** `/api/v1/cost-centers/{id}/movements`
Obtener movimientos contables del centro de costo.

#### Parámetros de Query
```typescript
interface MovementsParams {
  start_date?: date;       // Fecha inicio (default: inicio del mes)
  end_date?: date;         // Fecha fin (default: hoy)
  account_type?: AccountType; // Filtrar por tipo de cuenta
  skip?: number;
  limit?: number;
}
```

#### Respuesta Exitosa
```json
{
  "movements": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174000",
      "journal_entry_id": "abc123def456",
      "date": "2024-12-10",
      "account_code": "4101",
      "account_name": "Ventas",
      "description": "Venta de productos",
      "debit_amount": 0.00,
      "credit_amount": 150000.00,
      "reference": "FAC-001"
    }
  ],
  "summary": {
    "total_debits": 350000.00,
    "total_credits": 500000.00,
    "net_amount": 150000.00,
    "movement_count": 25
  }
}
```

---

## Endpoints de Reportes

### **GET** `/api/v1/cost-center-reports/{id}/profitability`
Análisis de rentabilidad del centro de costo.

#### Parámetros de Query
```typescript
interface ProfitabilityParams {
  start_date: date;        // Fecha inicio (requerido)
  end_date: date;          // Fecha fin (requerido)
  include_indirect_costs?: boolean; // Incluir costos indirectos
  comparison_period?: boolean; // Incluir período de comparación
}
```

#### Ejemplo de Solicitud
```http
GET /api/v1/cost-center-reports/123e4567-e89b-12d3-a456-426614174000/profitability?start_date=2024-01-01&end_date=2024-12-31&comparison_period=true
```

#### Respuesta Exitosa
```json
{
  "cost_center": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "CC001",
    "name": "Ventas Nacional"
  },
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-12-31T23:59:59Z",
  "metrics": {
    "revenue": 1500000.00,
    "direct_costs": 900000.00,
    "indirect_costs": 135000.00,
    "total_costs": 1035000.00,
    "gross_profit": 600000.00,
    "net_profit": 465000.00,
    "gross_margin": 40.0,
    "net_margin": 31.0,
    "cost_efficiency": 1.45
  },
  "comparison_metrics": {
    "revenue": 1200000.00,
    "net_profit": 300000.00,
    "net_margin": 25.0
  },
  "revenue_breakdown": [
    {
      "account_code": "4101",
      "account_name": "Ventas Productos",
      "amount": 1200000.00,
      "percentage": 80.0
    }
  ],
  "cost_breakdown": [
    {
      "account_code": "5101",
      "account_name": "Costo de Ventas",
      "amount": 720000.00,
      "type": "direct"
    }
  ],
  "insights": [
    "Excelente margen de rentabilidad, superior al 30%",
    "Mejora significativa vs período anterior: +6.0%"
  ],
  "recommendations": [
    "Mantener estrategia actual de rentabilidad",
    "Considerar expansión de mercado"
  ]
}
```

### **GET** `/api/v1/cost-center-reports/comparison`
Comparación entre múltiples centros de costo.

#### Parámetros de Query
```typescript
interface ComparisonParams {
  cost_center_ids: UUID[]; // IDs de centros a comparar (requerido)
  start_date: date;        // Fecha inicio (requerido)
  end_date: date;          // Fecha fin (requerido)
  metrics?: string[];      // Métricas a comparar
}
```

#### Ejemplo de Solicitud
```http
GET /api/v1/cost-center-reports/comparison?cost_center_ids=123e4567-e89b-12d3-a456-426614174000,456e7890-e89b-12d3-a456-426614174000&start_date=2024-01-01&end_date=2024-12-31
```

#### Respuesta Exitosa
```json
{
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-12-31T23:59:59Z",
  "comparison_metrics": ["profit", "margin", "efficiency"],
  "cost_centers": [
    {
      "cost_center": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "code": "CC001",
        "name": "Ventas Nacional"
      },
      "metrics": {
        "revenue": 1500000.00,
        "net_profit": 465000.00,
        "net_margin": 31.0,
        "cost_efficiency": 1.45
      },
      "ranking": 1,
      "variance_from_best": 0.0
    }
  ],
  "summary_statistics": {
    "avg_margin": 28.5,
    "avg_revenue": 1200000.00,
    "margin_std": 5.2,
    "revenue_std": 300000.00
  },
  "insights": [
    "Brecha de rentabilidad: 8.5% entre mejor y peor centro"
  ],
  "best_performer": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Ventas Nacional"
  },
  "worst_performer": {
    "id": "456e7890-e89b-12d3-a456-426614174000",
    "name": "Ventas Sur"
  }
}
```

### **GET** `/api/v1/cost-center-reports/{id}/budget-tracking`
Seguimiento presupuestario del centro de costo.

#### Parámetros de Query
```typescript
interface BudgetTrackingParams {
  budget_year: number;     // Año presupuestario (requerido)
  month?: number;          // Mes específico (opcional)
  include_forecast?: boolean; // Incluir proyecciones
}
```

#### Respuesta Exitosa
```json
{
  "cost_center": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "CC001",
    "name": "Ventas Nacional"
  },
  "budget_year": 2024,
  "month": null,
  "revenue_variance": {
    "budget_amount": 1650000.00,
    "actual_amount": 1500000.00,
    "variance_amount": -150000.00,
    "variance_percentage": -9.09,
    "status": "unfavorable"
  },
  "cost_variance": {
    "budget_amount": 1089000.00,
    "actual_amount": 1035000.00,
    "variance_amount": -54000.00,
    "variance_percentage": -4.96,
    "status": "favorable"
  },
  "profit_variance": {
    "budget_amount": 561000.00,
    "actual_amount": 465000.00,
    "variance_amount": -96000.00,
    "variance_percentage": -17.11,
    "status": "unfavorable"
  },
  "alerts": [
    "Variación significativa en ingresos: -9.1%"
  ],
  "recommendations": [
    "Revisar estrategias de generación de ingresos"
  ]
}
```

### **GET** `/api/v1/cost-center-reports/ranking`
Ranking de centros de costo por métricas.

#### Parámetros de Query
```typescript
interface RankingParams {
  ranking_metric: 'profit' | 'margin' | 'efficiency' | 'revenue'; // Métrica para ranking
  start_date: date;        // Fecha inicio
  end_date: date;          // Fecha fin
  limit?: number;          // Límite de resultados (default: 10)
  include_inactive?: boolean; // Incluir centros inactivos
}
```

#### Respuesta Exitosa
```json
{
  "ranking_metric": "profit",
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-12-31T23:59:59Z",
  "rankings": [
    {
      "position": 1,
      "cost_center": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "code": "CC001",
        "name": "Ventas Nacional"
      },
      "metric_value": 465000.00,
      "metric_description": "Utilidad neta",
      "performance_score": 92.5,
      "trend": "stable"
    }
  ],
  "metric_statistics": {
    "average": 285000.00,
    "median": 250000.00,
    "max": 465000.00,
    "min": 85000.00
  },
  "insights": [
    "Mejor rendimiento: Ventas Nacional con 465000.00"
  ]
}
```

### **GET** `/api/v1/cost-center-reports/executive-dashboard`
Dashboard ejecutivo consolidado.

#### Parámetros de Query
```typescript
interface DashboardParams {
  period?: 'current_month' | 'current_quarter' | 'current_year'; // Período de análisis
  top_performers_count?: number; // Número de top performers
  include_alerts?: boolean;     // Incluir alertas
}
```

#### Respuesta Exitosa
```json
{
  "period": "current_month",
  "start_date": "2024-12-01",
  "end_date": "2024-12-11",
  "consolidated_metrics": {
    "total_revenue": 5500000.00,
    "total_costs": 3850000.00,
    "total_profit": 1650000.00,
    "total_margin": 30.0,
    "active_cost_centers": 15
  },
  "top_performers": [
    {
      "position": 1,
      "cost_center": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "code": "CC001",
        "name": "Ventas Nacional"
      },
      "metric_value": 465000.00,
      "performance_score": 92.5
    }
  ],
  "alerts": [],
  "summary_insights": [
    "Rentabilidad consolidada excelente",
    "Mejor centro de costo: Ventas Nacional"
  ],
  "generated_at": "2024-12-11T15:30:00Z"
}
```

---

## Códigos de Error

### Errores Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| 400 | Datos de entrada inválidos | Verificar formato de campos |
| 404 | Centro de costo no encontrado | Verificar ID existe |
| 409 | Código duplicado | Usar código único en nivel |
| 422 | Error de validación | Revisar reglas de negocio |

### Ejemplos de Respuestas de Error

#### Error de Validación (422)
```json
{
  "detail": [
    {
      "loc": ["body", "code"],
      "msg": "Código debe contener solo letras, números, guiones y guiones bajos",
      "type": "value_error"
    }
  ]
}
```

#### Error de Conflicto (409)
```json
{
  "detail": "Ya existe un centro de costo con código 'CC001' en este nivel"
}
```

---

## Ejemplos de Uso

### Flujo Completo de Gestión

```javascript
// 1. Crear centro de costo padre
const parentResponse = await fetch('/api/v1/cost-centers', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    code: 'VEN',
    name: 'Ventas',
    description: 'División de Ventas'
  })
});

// 2. Crear centro hijo
const childResponse = await fetch('/api/v1/cost-centers', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    code: 'VEN001',
    name: 'Ventas Norte',
    parent_id: parentResponse.data.id
  })
});

// 3. Obtener análisis de rentabilidad
const profitabilityResponse = await fetch(
  `/api/v1/cost-center-reports/${childResponse.data.id}/profitability?start_date=2024-01-01&end_date=2024-12-31`,
  {
    headers: { 'Authorization': 'Bearer ' + token }
  }
);
```

---

## Rate Limiting

- **Endpoints de Consulta**: 1000 requests/hour
- **Endpoints de Modificación**: 100 requests/hour
- **Endpoints de Reportes**: 50 requests/hour

---
**Última actualización**: Diciembre 2024  
**Versión API**: 1.0.0
