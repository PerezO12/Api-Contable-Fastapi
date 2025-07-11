import uuid
from decimal import Decimal
from datetime import date
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.account import AccountType
from app.schemas.account import AccountSummary


# Esquemas para Balance General
class BalanceSheetItem(BaseModel):
    """Schema para items del balance general"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    balance: Decimal
    level: int
    children: List['BalanceSheetItem'] = []
    
    model_config = ConfigDict(from_attributes=True)


class BalanceSheetSection(BaseModel):
    """Schema para secciones del balance general"""
    section_name: str
    account_type: AccountType
    items: List[BalanceSheetItem]
    total: Decimal


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


# Esquemas para Estado de Resultados
class IncomeStatementItem(BaseModel):
    """Schema para items del estado de resultados"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    amount: Decimal
    level: int


class IncomeStatementSection(BaseModel):
    """Schema para secciones del estado de resultados"""
    section_name: str
    items: List[IncomeStatementItem]
    total: Decimal


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


# Esquemas para Balance de Comprobación
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


class TrialBalance(BaseModel):
    """Schema para balance de comprobación"""
    report_date: date
    company_name: str
    accounts: List[TrialBalanceItem]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


# Esquemas para Libro Mayor
class LedgerMovement(BaseModel):
    """Schema para movimientos del libro mayor"""
    date: date
    journal_entry_number: str
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal
    reference: Optional[str] = None


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


class GeneralLedger(BaseModel):
    """Schema para libro mayor general"""
    start_date: date
    end_date: date
    company_name: str
    accounts: List[LedgerAccount]


# Esquemas para análisis financiero
class FinancialRatio(BaseModel):
    """Schema para ratios financieros"""
    name: str
    value: Decimal
    description: str
    interpretation: str


class FinancialAnalysis(BaseModel):
    """Schema para análisis financiero"""
    report_date: date
    liquidity_ratios: List[FinancialRatio]
    profitability_ratios: List[FinancialRatio]
    leverage_ratios: List[FinancialRatio]
    efficiency_ratios: List[FinancialRatio]


# Esquemas para reportes personalizados
class ReportColumn(BaseModel):
    """Schema para columnas de reporte"""
    name: str
    field: str
    data_type: str  # "decimal", "string", "date", "integer"
    format: Optional[str] = None  # Para formateo específico


class CustomReportFilter(BaseModel):
    """Schema para filtros de reportes personalizados"""
    field: str
    operator: str  # "eq", "gt", "lt", "contains", "between"
    value: Any
    value2: Optional[Any] = None  # Para operador "between"


class CustomReportDefinition(BaseModel):
    """Schema para definición de reporte personalizado"""
    name: str
    description: Optional[str] = None
    table: str  # "accounts", "journal_entries", "journal_entry_lines"
    columns: List[ReportColumn]
    filters: List[CustomReportFilter] = []
    group_by: Optional[str] = None
    order_by: Optional[str] = None
    limit: Optional[int] = None


class CustomReportResult(BaseModel):
    """Schema para resultado de reporte personalizado"""
    definition: CustomReportDefinition
    data: List[Dict[str, Any]]
    total_rows: int
    generated_at: date


# Esquemas para Estado de Flujo de Efectivo
class CashFlowItem(BaseModel):
    """Schema para items del flujo de efectivo"""
    description: str = Field(..., description="Descripción del movimiento")
    amount: Decimal = Field(..., description="Monto del movimiento (positivo=entrada, negativo=salida)")
    account_code: str = Field(..., description="Código de cuenta relacionada")
    account_name: str = Field(..., description="Nombre de cuenta relacionada")


class OperatingCashFlow(BaseModel):
    """Schema para flujos de actividades de operación"""
    method: str = Field(..., description="Método utilizado: 'direct' o 'indirect'")
    net_income: Decimal = Field(Decimal('0'), description="Utilidad neta (solo método indirecto)")
    adjustments: List[CashFlowItem] = Field(default_factory=list, description="Ajustes por partidas no efectivo")
    working_capital_changes: List[CashFlowItem] = Field(default_factory=list, description="Cambios en capital de trabajo")
    items: List[CashFlowItem] = Field(..., description="Items del flujo operativo")
    net_operating_cash_flow: Decimal = Field(..., description="Flujo neto de actividades de operación")


class CashFlowStatement(BaseModel):
    """Schema para estado de flujo de efectivo completo"""
    report_date: date = Field(..., description="Fecha del reporte")
    start_date: date = Field(..., description="Fecha de inicio del período")
    end_date: date = Field(..., description="Fecha de fin del período")
    company_name: str = Field(..., description="Nombre de la empresa")
    method: str = Field(..., description="Método utilizado: 'direct' o 'indirect'")
    
    # Efectivo inicial
    cash_beginning_period: Decimal = Field(..., description="Efectivo y equivalentes al inicio")
    
    # Actividades de Operación
    operating_activities: OperatingCashFlow = Field(..., description="Flujos de actividades de operación")
    net_cash_from_operating: Decimal = Field(..., description="Flujo neto de actividades de operación")
    
    # Actividades de Inversión
    investing_activities: List[CashFlowItem] = Field(..., description="Flujos de actividades de inversión")
    net_cash_from_investing: Decimal = Field(..., description="Flujo neto de actividades de inversión")
    
    # Actividades de Financiamiento
    financing_activities: List[CashFlowItem] = Field(..., description="Flujos de actividades de financiamiento")
    net_cash_from_financing: Decimal = Field(..., description="Flujo neto de actividades de financiamiento")
    
    # Efectivo final
    net_change_in_cash: Decimal = Field(..., description="Cambio neto en efectivo")
    cash_ending_period: Decimal = Field(..., description="Efectivo y equivalentes al final")
    
    # Validación
    is_balanced: bool = Field(..., description="Si el estado cuadra correctamente")

    model_config = ConfigDict(from_attributes=True)


# Esquemas para exportación
class ReportExportRequest(BaseModel):
    """Schema para solicitar exportación de reporte"""
    report_type: str  # "balance_sheet", "income_statement", "trial_balance", "ledger"
    format: str  # "pdf", "excel", "csv"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_ids: Optional[List[uuid.UUID]] = None
    include_details: bool = True


class ReportExportResponse(BaseModel):
    """Schema para respuesta de exportación"""
    file_url: str
    file_name: str
    file_size: int
    expires_at: date
