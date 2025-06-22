# Endpoints de Reportes de Centros de Costo

## Descripción General

Los endpoints de reportes de centros de costo proporcionan análisis avanzado de rentabilidad, KPIs y métricas de rendimiento para facilitar la toma de decisiones gerenciales. Todos los reportes se generan en tiempo real utilizando los datos de asientos contables asociados a cada centro de costo.

## Base URL

```
/api/v1/cost-center-reports
```

## Autenticación

Todos los endpoints requieren autenticación JWT:

```
Authorization: Bearer <jwt_token>
```

## Endpoints Disponibles

### 1. Análisis de Rentabilidad

**GET** `/cost-center-reports/{cost_center_id}/profitability`

Genera análisis detallado de rentabilidad para un centro de costo específico.

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `cost_center_id` | UUID | ID único del centro de costo |

#### Query Parameters

| Parámetro | Tipo | Requerido | Descripción | Ejemplo |
|-----------|------|-----------|-------------|---------|
| `start_date` | date | Sí | Fecha inicio del análisis | "2024-01-01" |
| `end_date` | date | Sí | Fecha fin del análisis | "2024-12-31" |
| `include_indirect_costs` | boolean | No | Incluir costos indirectos asignados | true |
| `comparison_period` | boolean | No | Incluir comparación con período anterior | false |

#### Ejemplo de Request

```http
GET /api/v1/cost-center-reports/123e4567-e89b-12d3-a456-426614174000/profitability?start_date=2024-01-01&end_date=2024-12-31&include_indirect_costs=true&comparison_period=true
```

#### Ejemplo de Response

```json
{
  "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
  "cost_center_name": "Centro de Ventas Norte",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "profitability": {
    "total_revenue": "500000.00",
    "direct_costs": "300000.00",
    "indirect_costs": "50000.00",
    "total_costs": "350000.00",
    "gross_profit": "200000.00",
    "net_profit": "150000.00",
    "gross_margin": 40.0,
    "net_margin": 30.0,
    "roi": 42.86
  },
  "cost_breakdown": [
    {
      "category": "Salarios",
      "amount": "200000.00",
      "percentage": 57.14
    },
    {
      "category": "Materiales",
      "amount": "100000.00",
      "percentage": 28.57
    },
    {
      "category": "Gastos Generales",
      "amount": "50000.00",
      "percentage": 14.29
    }
  ],
  "comparison": {
    "previous_period": {
      "net_profit": "130000.00",
      "net_margin": 26.0
    },
    "variance": {
      "profit_change": "20000.00",
      "margin_change": 4.0,
      "percentage_change": 15.38
    }
  }
}
```

### 2. KPIs de Centro de Costo

**GET** `/cost-center-reports/{cost_center_id}/kpis`

Obtiene métricas clave de rendimiento (KPIs) para un centro de costo.

#### Query Parameters

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `start_date` | date | Sí | Fecha inicio del período |
| `end_date` | date | Sí | Fecha fin del período |
| `include_trends` | boolean | No | Incluir análisis de tendencias |
| `benchmark_comparison` | boolean | No | Comparar con promedio de otros centros |

#### Ejemplo de Response

```json
{
  "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "kpis": {
    "financial_kpis": {
      "revenue_per_employee": "50000.00",
      "profit_per_employee": "15000.00",
      "cost_efficiency_ratio": 0.70,
      "revenue_growth_rate": 15.5,
      "profit_growth_rate": 12.3
    },
    "operational_kpis": {
      "productivity_index": 1.25,
      "efficiency_ratio": 0.85,
      "utilization_rate": 92.5,
      "cost_variance": -5.2
    },
    "quality_kpis": {
      "customer_satisfaction": 4.2,
      "defect_rate": 0.03,
      "return_rate": 0.05
    }
  },
  "trends": {
    "quarterly_performance": [
      {
        "quarter": "Q1",
        "revenue": "120000.00",
        "profit": "36000.00",
        "margin": 30.0
      },
      {
        "quarter": "Q2",
        "revenue": "125000.00",
        "profit": "37500.00",
        "margin": 30.0
      }
    ]
  },
  "benchmarks": {
    "industry_average": {
      "profit_margin": 25.0,
      "revenue_growth": 10.0
    },
    "company_average": {
      "profit_margin": 28.0,
      "revenue_growth": 12.0
    },
    "performance_vs_company": {
      "margin_difference": 2.0,
      "growth_difference": 3.5,
      "ranking": 2
    }
  }
}
```

### 3. Comparación entre Centros de Costo

**GET** `/cost-center-reports/comparison`

Compara el rendimiento de múltiples centros de costo.

#### Query Parameters

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `cost_center_ids` | array | Sí | Lista de IDs de centros de costo |
| `start_date` | date | Sí | Fecha inicio del período |
| `end_date` | date | Sí | Fecha fin del período |
| `metrics` | array | No | Métricas específicas a comparar |

#### Ejemplo de Request

```http
GET /api/v1/cost-center-reports/comparison?cost_center_ids=123e4567-e89b-12d3-a456-426614174000,123e4567-e89b-12d3-a456-426614174001&start_date=2024-01-01&end_date=2024-12-31&metrics=profit_margin,revenue_growth
```

#### Ejemplo de Response

```json
{
  "comparison_period": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "cost_centers": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Centro de Ventas Norte",
      "metrics": {
        "total_revenue": "500000.00",
        "net_profit": "150000.00",
        "profit_margin": 30.0,
        "revenue_growth": 15.5,
        "roi": 42.86
      }
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "name": "Centro de Ventas Sur",
      "metrics": {
        "total_revenue": "450000.00",
        "net_profit": "120000.00",
        "profit_margin": 26.67,
        "revenue_growth": 12.0,
        "roi": 36.36
      }
    }
  ],
  "rankings": {
    "by_profit_margin": [
      {
        "rank": 1,
        "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
        "value": 30.0
      },
      {
        "rank": 2,
        "cost_center_id": "123e4567-e89b-12d3-a456-426614174001",
        "value": 26.67
      }
    ],
    "by_revenue": [
      {
        "rank": 1,
        "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
        "value": "500000.00"
      }
    ]
  },
  "summary": {
    "best_performer": {
      "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
      "metric": "profit_margin",
      "value": 30.0
    },
    "total_revenue": "950000.00",
    "total_profit": "270000.00",
    "average_margin": 28.34
  }
}
```

### 4. Ranking de Centros de Costo

**GET** `/cost-center-reports/ranking`

Obtiene ranking de centros de costo por diferentes métricas.

#### Query Parameters

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `start_date` | date | Sí | Fecha inicio del período |
| `end_date` | date | Sí | Fecha fin del período |
| `metric` | string | Sí | Métrica para ranking |
| `limit` | int | No | Número máximo de resultados |
| `include_details` | boolean | No | Incluir detalles de cada centro |

#### Métricas Disponibles

- `profit_margin` - Margen de utilidad
- `revenue` - Ingresos totales
- `roi` - Retorno sobre inversión
- `efficiency` - Índice de eficiencia
- `growth_rate` - Tasa de crecimiento

#### Ejemplo de Response

```json
{
  "ranking_metric": "profit_margin",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "ranking": [
    {
      "rank": 1,
      "cost_center": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Centro de Ventas Norte",
        "code": "VN001"
      },
      "value": 30.0,
      "details": {
        "revenue": "500000.00",
        "profit": "150000.00",
        "employees": 10,
        "efficiency_score": 95.5
      }
    },
    {
      "rank": 2,
      "cost_center": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "name": "Centro de Ventas Sur",
        "code": "VS001"
      },
      "value": 26.67,
      "details": {
        "revenue": "450000.00",
        "profit": "120000.00",
        "employees": 8,
        "efficiency_score": 88.2
      }
    }
  ],
  "statistics": {
    "highest_value": 30.0,
    "lowest_value": 15.5,
    "average_value": 23.8,
    "median_value": 25.0,
    "total_centers": 5
  }
}
```

### 5. Tracking de Presupuesto

**GET** `/cost-center-reports/{cost_center_id}/budget-tracking`

Seguimiento del cumplimiento de presupuesto para un centro de costo.

#### Query Parameters

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `budget_period` | string | Sí | Período presupuestario (monthly, quarterly, yearly) |
| `year` | int | Sí | Año del presupuesto |
| `month` | int | No | Mes específico (para períodos mensuales) |
| `quarter` | int | No | Trimestre específico (para períodos trimestrales) |

#### Ejemplo de Response

```json
{
  "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
  "budget_period": "yearly",
  "year": 2024,
  "budget_tracking": {
    "revenue": {
      "budgeted": "480000.00",
      "actual": "500000.00",
      "variance": "20000.00",
      "variance_percentage": 4.17,
      "status": "over_budget"
    },
    "costs": {
      "budgeted": "360000.00",
      "actual": "350000.00",
      "variance": "-10000.00",
      "variance_percentage": -2.78,
      "status": "under_budget"
    },
    "profit": {
      "budgeted": "120000.00",
      "actual": "150000.00",
      "variance": "30000.00",
      "variance_percentage": 25.0,
      "status": "over_budget"
    }
  },
  "monthly_progress": [
    {
      "month": 1,
      "revenue_actual": "42000.00",
      "revenue_budgeted": "40000.00",
      "costs_actual": "28000.00",
      "costs_budgeted": "30000.00",
      "variance": "4000.00"
    }
  ],
  "forecast": {
    "projected_year_end": {
      "revenue": "520000.00",
      "costs": "364000.00",
      "profit": "156000.00"
    },
    "confidence_level": 85.5
  }
}
```

### 6. Dashboard Ejecutivo

**GET** `/cost-center-reports/dashboard`

Dashboard consolidado con métricas clave de todos los centros de costo.

#### Query Parameters

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `start_date` | date | Sí | Fecha inicio del período |
| `end_date` | date | Sí | Fecha fin del período |
| `top_performers_limit` | int | No | Límite de mejores centros |
| `include_trends` | boolean | No | Incluir datos de tendencias |

#### Ejemplo de Response

```json
{
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "overview": {
    "total_revenue": "2500000.00",
    "total_profit": "750000.00",
    "average_margin": 30.0,
    "total_centers": 5,
    "active_centers": 5
  },
  "top_performers": {
    "by_profit": [
      {
        "center_name": "Centro de Ventas Norte",
        "profit": "150000.00",
        "margin": 30.0
      }
    ],
    "by_efficiency": [
      {
        "center_name": "Centro de Producción A",
        "efficiency_score": 95.5,
        "cost_variance": -5.2
      }
    ]
  },
  "alerts": [
    {
      "type": "budget_variance",
      "severity": "warning",
      "cost_center": "Centro de Ventas Sur",
      "message": "Costos exceden presupuesto en 8%"
    }
  ],
  "trends": {
    "quarterly_growth": [
      {
        "quarter": "Q1",
        "revenue_growth": 12.5,
        "profit_growth": 15.2
      }
    ]
  }
}
```

## Códigos de Error

### 400 Bad Request

```json
{
  "detail": "Invalid date range: start_date must be before end_date",
  "start_date": "2024-12-31",
  "end_date": "2024-01-01"
}
```

### 404 Not Found

```json
{
  "detail": "Cost center not found",
  "cost_center_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["query", "cost_center_ids"],
      "msg": "At least one cost center ID is required",
      "type": "value_error"
    }
  ]
}
```

## Notas de Implementación

- Todos los cálculos se realizan en tiempo real basados en asientos contables
- Los costos indirectos se asignan automáticamente según configuración
- Las comparaciones de períodos anteriores requieren datos históricos
- Los rankings se actualizan diariamente
- Las alertas de presupuesto se evalúan en tiempo real
- Todos los montos se devuelven como strings para evitar problemas de precisión decimal
