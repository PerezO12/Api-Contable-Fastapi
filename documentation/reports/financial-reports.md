# Endpoints de Reportes Financieros - ACTUALIZADO

## Descripción General

Los endpoints de reportes financieros proporcionan acceso a los reportes contables fundamentales del sistema, incluyendo Balance General, Estado de Resultados, Balance de Comprobación, Libro Mayor y Análisis Financiero. Todos los reportes siguen principios contables estándar y proporcionan información detallada y analítica.

## Base URL

```
Base URL: /api/v1/reports/legacy
```

## Autenticación

Todos los endpoints requieren autenticación mediante Bearer Token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints Disponibles

### 📊 GET /balance-sheet
Generar Balance General a una fecha específica siguiendo principios contables.

#### Parámetros de Query
- `as_of_date`: Optional[date] - Fecha de corte del balance (default: hoy)
- `include_zero_balances`: bool = false - Incluir cuentas con saldo cero
- `company_name`: Optional[str] - Nombre de la empresa para el reporte

#### Request
```http
GET /api/v1/reports/legacy/balance-sheet?as_of_date=2024-06-30&include_zero_balances=false&company_name=Mi%20Empresa%20S.A.
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "report_type": "balance_sheet",
  "company_name": "Mi Empresa S.A.",
  "as_of_date": "2024-06-30",
  "generated_at": "2024-06-15T10:30:00Z",
  "currency": "CLP",
  "assets": {
    "current_assets": {
      "total": 15000000.00,
      "accounts": [
        {
          "account_code": "1101001",
          "account_name": "Caja General",
          "balance": 2500000.00
        },
        {
          "account_code": "1102001",
          "account_name": "Banco Estado",
          "balance": 8500000.00
        },
        {
          "account_code": "1201001",
          "account_name": "Clientes",
          "balance": 4000000.00
        }
      ]
    },
    "non_current_assets": {
      "total": 25000000.00,
      "accounts": [
        {
          "account_code": "1501001",
          "account_name": "Muebles y Enseres",
          "balance": 15000000.00
        },
        {
          "account_code": "1502001",
          "account_name": "Equipos de Computación",
          "balance": 10000000.00
        }
      ]
    },
    "total_assets": 40000000.00
  },
  "liabilities": {
    "current_liabilities": {
      "total": 8000000.00,
      "accounts": [
        {
          "account_code": "2101001",
          "account_name": "Proveedores",
          "balance": 5000000.00
        },
        {
          "account_code": "2102001",
          "account_name": "IVA por Pagar",
          "balance": 3000000.00
        }
      ]
    },
    "non_current_liabilities": {
      "total": 12000000.00,
      "accounts": [
        {
          "account_code": "2201001",
          "account_name": "Préstamo Bancario LP",
          "balance": 12000000.00
        }
      ]
    },
    "total_liabilities": 20000000.00
  },
  "equity": {
    "total": 20000000.00,
    "accounts": [
      {
        "account_code": "3101001",
        "account_name": "Capital",
        "balance": 15000000.00
      },
      {
        "account_code": "3201001",
        "account_name": "Utilidades Retenidas",
        "balance": 5000000.00
      }
    ]
  },
  "validation": {
    "assets_equals_liabilities_plus_equity": true,
    "total_balance": 0.00,
    "is_balanced": true
  },
  "summary": {
    "total_accounts_included": 8,
    "accounts_with_zero_balance": 2,
    "last_transaction_date": "2024-06-29T16:45:00Z"
  }
}
```

---

### 📈 GET /income-statement
Generar Estado de Resultados para un período específico.

#### Parámetros de Query
- `start_date`: date (requerido) - Fecha de inicio del período
- `end_date`: date (requerido) - Fecha de fin del período
- `include_zero_balances`: bool = false - Incluir cuentas con saldo cero
- `company_name`: Optional[str] - Nombre de la empresa para el reporte

#### Request
```http
GET /api/v1/reports/legacy/income-statement?start_date=2024-01-01&end_date=2024-06-30&include_zero_balances=false&company_name=Mi%20Empresa%20S.A.
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "report_type": "income_statement",
  "company_name": "Mi Empresa S.A.",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-06-30"
  },
  "generated_at": "2024-06-15T10:30:00Z",
  "currency": "CLP",
  "revenues": {
    "total": 45000000.00,
    "accounts": [
      {
        "account_code": "4101001",
        "account_name": "Ventas de Productos",
        "balance": 40000000.00
      },
      {
        "account_code": "4102001",
        "account_name": "Servicios",
        "balance": 5000000.00
      }
    ]
  },
  "cost_of_goods_sold": {
    "total": 27000000.00,
    "accounts": [
      {
        "account_code": "5101001",
        "account_name": "Costo de Ventas",
        "balance": 27000000.00
      }
    ]
  },
  "gross_profit": 18000000.00,
  "operating_expenses": {
    "total": 12000000.00,
    "accounts": [
      {
        "account_code": "5201001",
        "account_name": "Sueldos y Salarios",
        "balance": 8000000.00
      },
      {
        "account_code": "5202001",
        "account_name": "Arriendo",
        "balance": 2400000.00
      },
      {
        "account_code": "5203001",
        "account_name": "Servicios Básicos",
        "balance": 1600000.00
      }
    ]
  },
  "operating_income": 6000000.00,
  "other_income": {
    "total": 500000.00,
    "accounts": [
      {
        "account_code": "4201001",
        "account_name": "Ingresos Financieros",
        "balance": 500000.00
      }
    ]
  },
  "other_expenses": {
    "total": 300000.00,
    "accounts": [
      {
        "account_code": "5301001",
        "account_name": "Gastos Financieros",
        "balance": 300000.00
      }
    ]
  },
  "net_income_before_taxes": 6200000.00,
  "taxes": {
    "total": 1550000.00,
    "accounts": [
      {
        "account_code": "5401001",
        "account_name": "Impuesto a la Renta",
        "balance": 1550000.00
      }
    ]
  },
  "net_income": 4650000.00,
  "margins": {
    "gross_margin_percentage": 40.0,
    "operating_margin_percentage": 13.33,
    "net_margin_percentage": 10.33
  },
  "summary": {
    "total_revenue_accounts": 2,
    "total_expense_accounts": 6,
    "period_days": 181,
    "average_daily_revenue": 248618.78,
    "average_daily_expenses": 214364.64
  }
}
```

---

### ⚖️ GET /trial-balance
Generar Balance de Comprobación para verificar que débitos igualen créditos.

#### Parámetros de Query
- `as_of_date`: Optional[date] - Fecha de corte (default: hoy)
- `include_zero_balances`: bool = false - Incluir cuentas con saldo cero
- `company_name`: Optional[str] - Nombre de la empresa para el reporte

#### Request
```http
GET /api/v1/reports/legacy/trial-balance?as_of_date=2024-06-30&include_zero_balances=false
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "report_type": "trial_balance",
  "company_name": "Mi Empresa S.A.",
  "as_of_date": "2024-06-30",
  "generated_at": "2024-06-15T10:30:00Z",
  "currency": "CLP",
  "accounts": [
    {
      "account_code": "1101001",
      "account_name": "Caja General",
      "account_type": "ACTIVO",
      "debit_balance": 2500000.00,
      "credit_balance": 0.00,
      "net_balance": 2500000.00
    },
    {
      "account_code": "2101001",
      "account_name": "Proveedores",
      "account_type": "PASIVO",
      "debit_balance": 0.00,
      "credit_balance": 5000000.00,
      "net_balance": -5000000.00
    },
    {
      "account_code": "4101001",
      "account_name": "Ventas de Productos",
      "account_type": "INGRESOS",
      "debit_balance": 0.00,
      "credit_balance": 40000000.00,
      "net_balance": -40000000.00
    },
    {
      "account_code": "5101001",
      "account_name": "Costo de Ventas",
      "account_type": "GASTOS",
      "debit_balance": 27000000.00,
      "credit_balance": 0.00,
      "net_balance": 27000000.00
    }
  ],
  "totals": {
    "total_debits": 150000000.00,
    "total_credits": 150000000.00,
    "difference": 0.00,
    "is_balanced": true
  },
  "summary": {
    "total_accounts": 25,
    "accounts_with_debit_balance": 12,
    "accounts_with_credit_balance": 13,
    "accounts_with_zero_balance": 8,
    "largest_debit_account": {
      "account_code": "5101001",
      "account_name": "Costo de Ventas",
      "balance": 27000000.00
    },
    "largest_credit_account": {
      "account_code": "4101001",
      "account_name": "Ventas de Productos",
      "balance": 40000000.00
    }
  },
  "validation": {
    "debits_equal_credits": true,
    "all_accounts_classified": true,
    "no_duplicate_accounts": true,
    "validation_passed": true
  }
}
```

---

### 📚 GET /general-ledger
Generar Libro Mayor mostrando todas las transacciones por cuenta.

#### Parámetros de Query
- `start_date`: date (requerido) - Fecha de inicio del período
- `end_date`: date (requerido) - Fecha de fin del período
- `account_id`: Optional[UUID] - Filtrar por cuenta específica
- `account_type`: Optional[AccountType] - Filtrar por tipo de cuenta
- `company_name`: Optional[str] - Nombre de la empresa para el reporte

#### Request
```http
GET /api/v1/reports/legacy/general-ledger?start_date=2024-06-01&end_date=2024-06-30&account_type=ACTIVO
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "report_type": "general_ledger",
  "company_name": "Mi Empresa S.A.",
  "period": {
    "start_date": "2024-06-01",
    "end_date": "2024-06-30"
  },
  "generated_at": "2024-06-15T10:30:00Z",
  "filters": {
    "account_id": null,
    "account_type": "ACTIVO"
  },
  "currency": "CLP",
  "accounts": [
    {
      "account_id": "123e4567-e89b-12d3-a456-426614174000",
      "account_code": "1101001",
      "account_name": "Caja General",
      "account_type": "ACTIVO",
      "opening_balance": 1500000.00,
      "closing_balance": 2500000.00,
      "total_debits": 5000000.00,
      "total_credits": 4000000.00,
      "net_change": 1000000.00,
      "transactions": [
        {
          "date": "2024-06-15T10:30:00Z",
          "journal_entry_id": "je-uuid-here",
          "journal_entry_number": "AST-2024-0001",
          "description": "Venta de productos",
          "reference": "FAC-001",
          "debit_amount": 500000.00,
          "credit_amount": 0.00,
          "running_balance": 2000000.00,
          "third_party_name": "Cliente Principal S.A."
        },
        {
          "date": "2024-06-20T14:15:00Z",
          "journal_entry_id": "je-uuid-here2",
          "journal_entry_number": "AST-2024-0002",
          "description": "Pago de proveedor",
          "reference": "PAGO-001",
          "debit_amount": 0.00,
          "credit_amount": 300000.00,
          "running_balance": 1700000.00,
          "third_party_name": "Proveedor ABC Ltda."
        }
      ],
      "transaction_count": 15
    }
  ],
  "summary": {
    "total_accounts": 8,
    "total_transactions": 125,
    "total_debits": 85000000.00,
    "total_credits": 78000000.00,
    "net_change": 7000000.00,
    "most_active_account": {
      "account_code": "1101001",
      "account_name": "Caja General",
      "transaction_count": 25
    }
  }
}
```

---

### 🔍 GET /financial-analysis
Generar análisis financiero integral con ratios y interpretación.

#### Parámetros de Query
- `as_of_date`: Optional[date] - Fecha de análisis (default: hoy)
- `start_date`: Optional[date] - Fecha de inicio para análisis de rentabilidad
- `end_date`: Optional[date] - Fecha de fin para análisis de rentabilidad

#### Request
```http
GET /api/v1/reports/legacy/financial-analysis?as_of_date=2024-06-30&start_date=2024-01-01&end_date=2024-06-30
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "report_type": "financial_analysis",
  "company_name": "Mi Empresa S.A.",
  "analysis_date": "2024-06-30",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-06-30"
  },
  "generated_at": "2024-06-15T10:30:00Z",
  "currency": "CLP",
  "liquidity_ratios": {
    "current_ratio": {
      "value": 1.875,
      "formula": "Current Assets / Current Liabilities",
      "calculation": "15,000,000 / 8,000,000",
      "interpretation": "GOOD",
      "benchmark": "> 1.5",
      "description": "La empresa puede cubrir sus obligaciones a corto plazo"
    },
    "quick_ratio": {
      "value": 1.125,
      "formula": "(Current Assets - Inventory) / Current Liabilities",
      "calculation": "12,000,000 / 8,000,000",
      "interpretation": "GOOD",
      "benchmark": "> 1.0",
      "description": "Capacidad de pago inmediato sin depender del inventario"
    },
    "cash_ratio": {
      "value": 1.375,
      "formula": "Cash and Cash Equivalents / Current Liabilities",
      "calculation": "11,000,000 / 8,000,000",
      "interpretation": "EXCELLENT",
      "benchmark": "> 0.2",
      "description": "Excelente posición de efectivo para obligaciones inmediatas"
    }
  },
  "profitability_ratios": {
    "gross_margin": {
      "value": 40.0,
      "formula": "(Revenue - COGS) / Revenue * 100",
      "calculation": "(45,000,000 - 27,000,000) / 45,000,000 * 100",
      "interpretation": "GOOD",
      "benchmark": "> 30%",
      "description": "Margen bruto saludable en las operaciones principales"
    },
    "operating_margin": {
      "value": 13.33,
      "formula": "Operating Income / Revenue * 100",
      "calculation": "6,000,000 / 45,000,000 * 100",
      "interpretation": "GOOD",
      "benchmark": "> 10%",
      "description": "Eficiencia operacional adecuada"
    },
    "net_margin": {
      "value": 10.33,
      "formula": "Net Income / Revenue * 100",
      "calculation": "4,650,000 / 45,000,000 * 100",
      "interpretation": "GOOD",
      "benchmark": "> 5%",
      "description": "Rentabilidad neta satisfactoria"
    },
    "return_on_assets": {
      "value": 11.625,
      "formula": "Net Income / Total Assets * 100",
      "calculation": "4,650,000 / 40,000,000 * 100",
      "interpretation": "GOOD",
      "benchmark": "> 8%",
      "description": "Uso eficiente de los activos para generar ganancias"
    },
    "return_on_equity": {
      "value": 23.25,
      "formula": "Net Income / Total Equity * 100",
      "calculation": "4,650,000 / 20,000,000 * 100",
      "interpretation": "EXCELLENT",
      "benchmark": "> 15%",
      "description": "Excelente retorno para los accionistas"
    }
  },
  "leverage_ratios": {
    "debt_ratio": {
      "value": 50.0,
      "formula": "Total Liabilities / Total Assets * 100",
      "calculation": "20,000,000 / 40,000,000 * 100",
      "interpretation": "MODERATE",
      "benchmark": "< 60%",
      "description": "Nivel de endeudamiento moderado y manejable"
    },
    "debt_to_equity": {
      "value": 1.0,
      "formula": "Total Liabilities / Total Equity",
      "calculation": "20,000,000 / 20,000,000",
      "interpretation": "MODERATE",
      "benchmark": "< 1.5",
      "description": "Equilibrio entre deuda y patrimonio"
    },
    "interest_coverage": {
      "value": 20.67,
      "formula": "Operating Income / Interest Expense",
      "calculation": "6,200,000 / 300,000",
      "interpretation": "EXCELLENT",
      "benchmark": "> 5",
      "description": "Excelente capacidad para cubrir gastos financieros"
    }
  },
  "efficiency_ratios": {
    "asset_turnover": {
      "value": 1.125,
      "formula": "Revenue / Total Assets",
      "calculation": "45,000,000 / 40,000,000",
      "interpretation": "GOOD",
      "benchmark": "> 1.0",
      "description": "Uso eficiente de activos para generar ventas"
    },
    "inventory_turnover": {
      "value": 9.0,
      "formula": "COGS / Average Inventory",
      "calculation": "27,000,000 / 3,000,000",
      "interpretation": "EXCELLENT",
      "benchmark": "> 6",
      "description": "Rotación rápida del inventario"
    },
    "receivables_turnover": {
      "value": 11.25,
      "formula": "Revenue / Average Accounts Receivable",
      "calculation": "45,000,000 / 4,000,000",
      "interpretation": "EXCELLENT",
      "benchmark": "> 8",
      "description": "Cobro eficiente de cuentas por cobrar"
    }
  },
  "trend_analysis": {
    "revenue_growth": {
      "current_period": 45000000.00,
      "previous_period": 38000000.00,
      "growth_rate": 18.42,
      "interpretation": "EXCELLENT"
    },
    "profit_growth": {
      "current_period": 4650000.00,
      "previous_period": 3200000.00,
      "growth_rate": 45.31,
      "interpretation": "EXCELLENT"
    }
  },
  "overall_assessment": {
    "financial_health": "GOOD",
    "risk_level": "LOW",
    "key_strengths": [
      "Excelente liquidez y posición de efectivo",
      "Rentabilidad sólida y creciente",
      "Gestión eficiente de inventario y cuentas por cobrar",
      "Nivel de endeudamiento controlado"
    ],
    "areas_for_improvement": [
      "Continuar monitoreando el crecimiento sostenible",
      "Evaluar oportunidades de inversión con exceso de efectivo"
    ],
    "recommendations": [
      "Mantener políticas de cobro actuales",
      "Considerar inversiones en activos productivos",
      "Monitorear tendencias del mercado para sostener crecimiento"
    ]
  }
}
```

---

### 📤 POST /export
Exportar reportes financieros a varios formatos (PDF, Excel, CSV).

#### Request
```http
POST /api/v1/reports/legacy/export
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "report_type": "balance_sheet",
  "format": "PDF",
  "parameters": {
    "as_of_date": "2024-06-30",
    "include_zero_balances": false,
    "company_name": "Mi Empresa S.A."
  },
  "options": {
    "include_charts": true,
    "include_analysis": true,
    "template": "standard"
  }
}
```

#### Response Exitosa (200)
```json
{
  "export_id": "export-uuid-here",
  "status": "processing",
  "report_type": "balance_sheet",
  "format": "PDF",
  "estimated_completion": "2024-06-15T10:35:00Z",
  "download_url": null,
  "file_size": null,
  "expires_at": "2024-06-16T10:30:00Z"
}
```

---

### 📈 GET /accounts-summary/{account_type}
Obtener resumen de cuentas por tipo específico con saldos actuales.

#### Parámetros de Query
- `as_of_date`: Optional[date] - Fecha de corte (default: hoy)
- `include_zero_balances`: bool = false - Incluir cuentas con saldo cero

#### Request
```http
GET /api/v1/reports/legacy/accounts-summary/ACTIVO?as_of_date=2024-06-30&include_zero_balances=false
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "account_id": "123e4567-e89b-12d3-a456-426614174000",
    "account_code": "1101001",
    "account_name": "Caja General",
    "account_type": "ACTIVO",
    "category": "CORRIENTE",
    "current_balance": 2500000.00,
    "percentage_of_total": 6.25,
    "last_transaction_date": "2024-06-29T16:45:00Z",
    "transaction_count": 25
  },
  {
    "account_id": "456e7890-e89b-12d3-a456-426614174000",
    "account_code": "1102001",
    "account_name": "Banco Estado",
    "account_type": "ACTIVO",
    "category": "CORRIENTE",
    "current_balance": 8500000.00,
    "percentage_of_total": 21.25,
    "last_transaction_date": "2024-06-30T09:15:00Z",
    "transaction_count": 45
  }
]
```

---

## Flujos de Integración

### Generación de Reportes Secuenciales

```javascript
// 1. Generar Balance General
const balanceSheet = await fetch('/api/v1/reports/legacy/balance-sheet?as_of_date=2024-06-30', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 2. Generar Estado de Resultados
const incomeStatement = await fetch(
  '/api/v1/reports/legacy/income-statement?start_date=2024-01-01&end_date=2024-06-30',
  { headers: { 'Authorization': `Bearer ${token}` } }
);

// 3. Generar Análisis Financiero
const analysis = await fetch(
  '/api/v1/reports/legacy/financial-analysis?as_of_date=2024-06-30&start_date=2024-01-01&end_date=2024-06-30',
  { headers: { 'Authorization': `Bearer ${token}` } }
);

// 4. Exportar reportes
const exportRequest = await fetch('/api/v1/reports/legacy/export', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    report_type: 'balance_sheet',
    format: 'PDF',
    parameters: { as_of_date: '2024-06-30' }
  })
});
```

### Dashboard Financiero

```javascript
// Obtener datos para dashboard
const dashboardData = await Promise.all([
  fetch('/api/v1/reports/legacy/balance-sheet?as_of_date=' + today),
  fetch('/api/v1/reports/legacy/income-statement?start_date=' + startOfMonth + '&end_date=' + today),
  fetch('/api/v1/reports/legacy/trial-balance?as_of_date=' + today),
  fetch('/api/v1/reports/legacy/financial-analysis?as_of_date=' + today)
].map(req => req.then(res => res.json())));

const [balanceSheet, incomeStatement, trialBalance, analysis] = dashboardData;
```

## Validaciones y Reglas de Negocio

### Principios Contables
- **Balance General**: Activos = Pasivos + Patrimonio
- **Estado de Resultados**: Ingresos Netos = Ingresos - Gastos
- **Balance de Comprobación**: Total Débitos = Total Créditos

### Validaciones de Fechas
- Fecha de fin debe ser posterior a fecha de inicio
- No se permiten fechas futuras más allá de hoy
- Períodos máximos de 5 años para análisis

### Integridad de Datos
- Todos los asientos deben estar contabilizados
- Las cuentas deben tener clasificación correcta
- Los saldos deben cuadrar matemáticamente

## Códigos de Error Comunes

### 400 Bad Request
- Fechas inválidas o período incorrecto
- Parámetros de reporte malformados
- Filtros incompatibles

### 401 Unauthorized
- Token de autenticación inválido
- Token expirado

### 404 Not Found
- Cuenta especificada no encontrada
- Reporte no existe

### 422 Unprocessable Entity
- Error en generación de reporte
- Datos contables inconsistentes
- Período demasiado extenso

### 500 Internal Server Error
- Error en cálculos contables
- Problema con base de datos
- Error en exportación

## Testing de Endpoints

### Casos de Prueba Críticos
1. **Balances**: Verificar ecuación contable fundamental
2. **Períodos**: Probar con diferentes rangos de fechas
3. **Filtros**: Validar filtros por cuenta y tipo
4. **Exportación**: Verificar formatos de salida
5. **Análisis**: Validar cálculos de ratios financieros

### Ejemplo con pytest
```python
@pytest.mark.asyncio
async def test_balance_sheet_equation(client: AsyncClient, user_token: str):
    response = await client.get(
        "/api/v1/reports/legacy/balance-sheet",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assets = data["assets"]["total_assets"]
    liabilities = data["liabilities"]["total_liabilities"]
    equity = data["equity"]["total"]
    
    # Verificar ecuación contable fundamental
    assert abs(assets - (liabilities + equity)) < 0.01
    assert data["validation"]["is_balanced"] == True

@pytest.mark.asyncio
async def test_income_statement_period_validation(client: AsyncClient, user_token: str):
    # Probar con fechas inválidas
    response = await client.get(
        "/api/v1/reports/legacy/income-statement?start_date=2024-06-30&end_date=2024-06-01",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400
```

## Referencias

- [Esquemas de Reportes](../schemas/report-schemas.md)
- [Servicio de Reportes](../services/report-service.md)
- [Cuentas Contables](../accounts/account-endpoints-updated.md)
- [Asientos Contables](../journal-entries/journal-entry-endpoints.md)
