# 📐 Esquemas y Modelos de Reportes

## Descripción General

Esta sección documenta todos los esquemas de datos, modelos y estructuras utilizadas por el sistema de reportes financieros. Los esquemas están diseñados para proporcionar flexibilidad, consistencia y compatibilidad con estándares contables internacionales.

## Arquitectura de Esquemas

```
📁 Esquemas de Reportes
├── 📊 Reportes Clásicos (reports.py)
│   ├── BalanceSheet
│   ├── IncomeStatement
│   ├── TrialBalance
│   └── GeneralLedger
├── 🔄 API Unificada (report_api.py)
│   ├── ReportResponse
│   ├── ReportTable
│   ├── ReportNarrative
│   └── ReportFilters
└── 🧮 Modelos Base
    ├── AccountBalance
    ├── FinancialRatio
    └── ReportError
```

## Esquemas de Reportes Clásicos

### BalanceSheet

Schema completo para el Balance General tradicional.

```python
class BalanceSheet(BaseModel):
    """Schema para balance general completo"""
    report_date: date
    company_name: str
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    total_assets: Decimal
    total_liabilities_equity: Decimal
    is_balanced: bool
```

**Ejemplo JSON:**
```json
{
  "report_date": "2025-06-10",
  "company_name": "Mi Empresa S.A.",
  "assets": {
    "section_name": "ACTIVOS",
    "account_type": "ACTIVO",
    "items": [
      {
        "account_id": "uuid",
        "account_code": "1001",
        "account_name": "Caja",
        "balance": "50000.00",
        "level": 1,
        "children": []
      }
    ],
    "total": "170000.00"
  },
  "liabilities": { /* ... */ },
  "equity": { /* ... */ },
  "total_assets": "170000.00",
  "total_liabilities_equity": "170000.00",
  "is_balanced": true
}
```

### BalanceSheetSection

```python
class BalanceSheetSection(BaseModel):
    """Schema para secciones del balance general"""
    section_name: str
    account_type: AccountType
    items: List[BalanceSheetItem]
    total: Decimal
```

### BalanceSheetItem

```python
class BalanceSheetItem(BaseModel):
    """Schema para items del balance general"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    balance: Decimal
    level: int
    children: List['BalanceSheetItem'] = []
    
    model_config = ConfigDict(from_attributes=True)
```

**Propiedades:**
- `account_id`: Identificador único de la cuenta
- `account_code`: Código contable de la cuenta
- `account_name`: Nombre descriptivo de la cuenta
- `balance`: Saldo actual de la cuenta
- `level`: Nivel jerárquico (1=principal, 2=subcuenta, etc.)
- `children`: Subcuentas anidadas (estructura recursiva)

---

### IncomeStatement

Schema para Estado de Resultados con análisis de rentabilidad.

```python
class IncomeStatement(BaseModel):
    """Schema para estado de resultados"""
    start_date: date
    end_date: date
    company_name: str
    revenues: IncomeStatementSection
    expenses: IncomeStatementSection
    gross_profit: Decimal
    operating_profit: Decimal
    net_profit: Decimal
```

**Ejemplo JSON:**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-06-10",
  "company_name": "Mi Empresa S.A.",
  "revenues": {
    "section_name": "INGRESOS",
    "items": [
      {
        "account_id": "uuid",
        "account_code": "4001",
        "account_name": "Ventas",
        "amount": "250000.00",
        "level": 1
      }
    ],
    "total": "325000.00"
  },
  "expenses": { /* ... */ },
  "gross_profit": "325000.00",
  "operating_profit": "250000.00",
  "net_profit": "250000.00"
}
```

### IncomeStatementSection

```python
class IncomeStatementSection(BaseModel):
    """Schema para secciones del estado de resultados"""
    section_name: str
    items: List[IncomeStatementItem]
    total: Decimal
```

### IncomeStatementItem

```python
class IncomeStatementItem(BaseModel):
    """Schema para items del estado de resultados"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    amount: Decimal
    level: int
```

---

### TrialBalance

Schema para Balance de Comprobación.

```python
class TrialBalance(BaseModel):
    """Schema para balance de comprobación"""
    report_date: date
    company_name: str
    accounts: List[TrialBalanceItem]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool
```

### TrialBalanceItem

```python
class TrialBalanceItem(BaseModel):
    """Schema para items del balance de comprobación"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    opening_balance: Decimal
    debit_movements: Decimal
    credit_movements: Decimal
    closing_balance: Decimal
    normal_balance_side: str
```

**Campos Explicados:**
- `opening_balance`: Saldo inicial del período
- `debit_movements`: Suma de todos los débitos del período
- `credit_movements`: Suma de todos los créditos del período
- `closing_balance`: Saldo final calculado
- `normal_balance_side`: "debit" o "credit" según tipo de cuenta

---

### GeneralLedger

Schema para Libro Mayor con movimientos detallados.

```python
class GeneralLedger(BaseModel):
    """Schema para libro mayor"""
    start_date: date
    end_date: date
    company_name: str
    accounts: List[LedgerAccount]
```

### LedgerAccount

```python
class LedgerAccount(BaseModel):
    """Schema para cuenta en libro mayor"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    opening_balance: Decimal
    movements: List[LedgerMovement]
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
```

### LedgerMovement

```python
class LedgerMovement(BaseModel):
    """Schema para movimientos del libro mayor"""
    date: date
    journal_entry_number: str
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal
    reference: Optional[str] = None
```

## Esquemas de API Unificada

### ReportResponse

Schema principal para respuestas de la API unificada.

```python
class ReportResponse(BaseModel):
    """Schema principal para respuestas de reportes"""
    success: bool
    report_type: ReportType
    generated_at: date
    period: DateRange
    project_context: str
    table: ReportTable
    narrative: ReportNarrative
```

### ReportType

```python
class ReportType(str, Enum):
    """Tipos de reportes disponibles"""
    BALANCE_GENERAL = "balance_general"
    FLUJO_EFECTIVO = "flujo_efectivo"
    P_G = "p_g"  # Pérdidas y Ganancias
```

### DetailLevel

```python
class DetailLevel(str, Enum):
    """Niveles de detalle del reporte"""
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
```

### DateRange

```python
class DateRange(BaseModel):
    """Rango de fechas para el reporte"""
    from_date: date = Field(..., alias="from", description="Fecha de inicio")
    to_date: date = Field(..., alias="to", description="Fecha de fin")
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        if 'from_date' in values and v < values['from_date']:
            raise ValueError('La fecha de fin debe ser mayor o igual a la fecha de inicio')
        return v
```

### ReportTable

```python
class ReportTable(BaseModel):
    """Tabla principal del reporte"""
    sections: List[ReportSection]
    totals: Dict[str, Decimal]
    summary: Dict[str, Any]
```

### ReportSection

```python
class ReportSection(BaseModel):
    """Sección de la tabla de reporte"""
    section_name: str
    items: List[AccountReportItem]
    total: Decimal
```

### AccountReportItem

```python
class AccountReportItem(BaseModel):
    """Item de cuenta en el reporte"""
    account_group: str
    account_code: str
    account_name: str
    opening_balance: Decimal
    movements: Decimal
    closing_balance: Decimal
    level: int
```

### ReportNarrative

```python
class ReportNarrative(BaseModel):
    """Narrativa del reporte con análisis y recomendaciones"""
    executive_summary: str
    key_insights: List[str]
    recommendations: List[str]
    financial_highlights: Dict[str, Any]
```

### ReportFilters

```python
class ReportFilters(BaseModel):
    """Filtros adicionales para el reporte"""
    cost_center: Optional[List[str]] = Field(None, description="Centros de costo a incluir")
    tags: Optional[List[str]] = Field(None, description="Etiquetas a incluir")
```

### ReportRequest

```python
class ReportRequest(BaseModel):
    """Request para generar reportes financieros"""
    project_context: str = Field(..., min_length=1, description="Contexto o nombre del proyecto")
    report_type: ReportType = Field(..., description="Tipo de reporte a generar")
    date_range: DateRange = Field(..., description="Rango de fechas")
    detail_level: DetailLevel = Field(DetailLevel.MEDIO, description="Nivel de detalle")
    include_subaccounts: bool = Field(False, description="Incluir subcuentas en el detalle")
```

## Esquemas de Análisis Financiero

### FinancialAnalysis

```python
class FinancialAnalysis(BaseModel):
    """Schema para análisis financiero completo"""
    report_date: date
    company_name: str
    balance_sheet: BalanceSheet
    income_statement: Optional[IncomeStatement]
    liquidity_ratios: List[FinancialRatio]
    profitability_ratios: List[FinancialRatio]
    leverage_ratios: List[FinancialRatio]
    efficiency_ratios: List[FinancialRatio]
    overall_assessment: str
```

### FinancialRatio

```python
class FinancialRatio(BaseModel):
    """Schema para ratio financiero"""
    name: str
    value: Decimal
    description: str
    interpretation: str
```

**Ejemplos de Ratios:**
```json
{
  "name": "Liquidez Corriente",
  "value": "2.45",
  "description": "Activos Corrientes / Pasivos Corrientes",
  "interpretation": "Excelente capacidad de pago a corto plazo"
}
```

## Esquemas de Exportación

### ReportExportRequest

```python
class ReportExportRequest(BaseModel):
    """Request para exportación de reportes"""
    report_type: str
    format: str  # pdf, excel, csv
    parameters: Dict[str, Any]
    template: str = "standard"
```

### ReportExportResponse

```python
class ReportExportResponse(BaseModel):
    """Response de exportación de reportes"""
    file_url: str
    file_name: str
    file_size: int
    format: str
    generated_at: datetime
    expires_at: date
```

## Esquemas de Error

### ReportError

```python
class ReportError(BaseModel):
    """Schema para errores de reportes"""
    error_code: str
    error_message: str
    error_type: str
    severity: str
    suggestions: Optional[List[str]] = None
```

### ReportGenerationError

Excepción específica para errores de generación de reportes.

```python
class ReportGenerationError(Exception):
    """Excepción para errores en generación de reportes"""
    def __init__(self, report_type: str, reason: str):
        self.report_type = report_type
        self.reason = reason
        super().__init__(f"Error generando {report_type}: {reason}")
```

## Modelos Base del Servicio

### AccountBalance

```python
class AccountBalance:
    """Clase auxiliar para manejar balances de cuentas"""
    def __init__(self, account: Account, debit_total: Decimal, credit_total: Decimal):
        self.account = account
        self.debit_total = debit_total
        self.credit_total = credit_total
    
    @property
    def balance(self) -> Decimal:
        """Calcular balance según naturaleza de la cuenta"""
        if self.account.normal_balance_side == "debit":
            return self.debit_total - self.credit_total
        else:
            return self.credit_total - self.debit_total
```

## Validaciones y Constraints

### Validaciones de Fecha

```python
@validator('end_date')
def validate_date_range(cls, v, values):
    if 'start_date' in values and v < values['start_date']:
        raise ValueError('End date must be after start date')
    return v
```

### Validaciones de Balance

```python
@validator('is_balanced')
def validate_balance_equation(cls, v, values):
    if 'total_assets' in values and 'total_liabilities_equity' in values:
        assets = values['total_assets']
        liab_equity = values['total_liabilities_equity']
        return abs(assets - liab_equity) < Decimal('0.01')
    return v
```

### Validaciones de Decimales

```python
class DecimalField(BaseModel):
    value: Decimal = Field(..., decimal_places=2, max_digits=15)
    
    @validator('value')
    def validate_decimal_precision(cls, v):
        if v.as_tuple().exponent < -2:
            raise ValueError('Maximum 2 decimal places allowed')
        return v
```

## Configuración de Modelos

### ConfigDict Estándar

```python
model_config = ConfigDict(
    from_attributes=True,
    validate_assignment=True,
    arbitrary_types_allowed=False,
    use_enum_values=True
)
```

### Configuración JSON

```python
class Config:
    json_encoders = {
        Decimal: lambda v: str(v),
        date: lambda v: v.isoformat(),
        datetime: lambda v: v.isoformat()
    }
```

## Evolución de Esquemas

### Versionado

Los esquemas incluyen versionado para mantener compatibilidad:

```python
class ReportResponseV1(BaseModel):
    """Versión 1 del schema de respuesta"""
    version: Literal["1.0"] = "1.0"
    # ... campos específicos
```

### Migración de Datos

Para cambios en esquemas, se implementan adaptadores:

```python
def migrate_v1_to_v2(v1_data: ReportResponseV1) -> ReportResponseV2:
    """Migrar datos de v1 a v2"""
    return ReportResponseV2(
        version="2.0",
        # ... mapeo de campos
    )
```

## Ejemplos de Uso Completos

### Balance Sheet Completo

```json
{
  "report_date": "2025-06-10",
  "company_name": "Empresa Ejemplo S.A.",
  "assets": {
    "section_name": "ACTIVOS",
    "account_type": "ACTIVO",
    "items": [
      {
        "account_id": "11111111-1111-1111-1111-111111111111",
        "account_code": "1",
        "account_name": "ACTIVOS",
        "balance": "300000.00",
        "level": 0,
        "children": [
          {
            "account_id": "12345678-1234-1234-1234-123456789012",
            "account_code": "1.1",
            "account_name": "ACTIVO CORRIENTE",
            "balance": "170000.00",
            "level": 1,
            "children": [
              {
                "account_id": "12345678-1234-1234-1234-123456789013",
                "account_code": "1.1.01",
                "account_name": "Efectivo y Equivalentes",
                "balance": "170000.00",
                "level": 2,
                "children": [
                  {
                    "account_id": "12345678-1234-1234-1234-123456789014",
                    "account_code": "1.1.01.01",
                    "account_name": "Caja",
                    "balance": "50000.00",
                    "level": 3,
                    "children": []
                  },
                  {
                    "account_id": "12345678-1234-1234-1234-123456789015",
                    "account_code": "1.1.01.02",
                    "account_name": "Bancos",
                    "balance": "120000.00",
                    "level": 3,
                    "children": []
                  }
                ]
              }
            ]
          }
        ]
      }
    ],
    "total": "300000.00"
  },
  "liabilities": {
    "section_name": "PASIVOS",
    "account_type": "PASIVO",
    "items": [
      {
        "account_id": "21111111-1111-1111-1111-111111111111",
        "account_code": "2",
        "account_name": "PASIVOS",
        "balance": "75000.00",
        "level": 0,
        "children": [
          {
            "account_id": "22345678-1234-1234-1234-123456789012",
            "account_code": "2.1",
            "account_name": "PASIVO CORRIENTE",
            "balance": "75000.00",
            "level": 1,
            "children": [
              {
                "account_id": "22345678-1234-1234-1234-123456789013",
                "account_code": "2.1.01",
                "account_name": "Proveedores",
                "balance": "45000.00",
                "level": 2,
                "children": []
              },
              {
                "account_id": "22345678-1234-1234-1234-123456789014",
                "account_code": "2.1.02",
                "account_name": "Cuentas por Pagar",
                "balance": "30000.00",
                "level": 2,
                "children": []
              }
            ]
          }
        ]
      }
    ],
    "total": "75000.00"
  },
  "equity": {
    "section_name": "PATRIMONIO",
    "account_type": "PATRIMONIO",
    "items": [
      {
        "account_id": "31111111-1111-1111-1111-111111111111",
        "account_code": "3",
        "account_name": "PATRIMONIO",
        "balance": "225000.00",
        "level": 0,
        "children": [
          {
            "account_id": "32345678-1234-1234-1234-123456789012",
            "account_code": "3.1",
            "account_name": "Capital",
            "balance": "200000.00",
            "level": 1,
            "children": []
          },
          {
            "account_id": "32345678-1234-1234-1234-123456789013",
            "account_code": "3.2",
            "account_name": "Utilidades Retenidas",
            "balance": "25000.00",
            "level": 1,
            "children": []
          }
        ]
      }
    ],
    "total": "225000.00"
  },
  "total_assets": "300000.00",
  "total_liabilities_equity": "300000.00",
  "is_balanced": true
}
```

Este sistema de esquemas proporciona la base sólida y flexible necesaria para manejar todos los aspectos de los reportes financieros, desde la generación básica hasta el análisis avanzado y la integración con sistemas externos.
