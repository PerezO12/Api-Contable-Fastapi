"""
Schemas for Cost Center functionality.
Includes CRUD operations, hierarchical structure and validation schemas.
"""
import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Schemas base
class CostCenterBase(BaseModel):
    """Schema base para centros de costo"""
    code: str = Field(..., min_length=1, max_length=20, description="Código único del centro de costo")
    name: str = Field(..., min_length=2, max_length=200, description="Nombre del centro de costo")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción detallada")
    parent_id: Optional[uuid.UUID] = Field(None, description="ID del centro de costo padre")
    is_active: bool = Field(True, description="Si el centro de costo está activo")
    allows_direct_assignment: bool = Field(True, description="Si permite asignación directa de transacciones")
    manager_name: Optional[str] = Field(None, max_length=200, description="Nombre del responsable")
    budget_code: Optional[str] = Field(None, max_length=50, description="Código presupuestario")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas adicionales")

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v):
        """Valida el formato del código"""
        if not v or not v.strip():
            raise ValueError("El código no puede estar vacío")
        
        # Permitir solo caracteres alfanuméricos, puntos y guiones
        allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-_')
        if not all(c in allowed_chars for c in v):
            raise ValueError("El código solo puede contener letras, números, puntos, guiones y guiones bajos")
        
        return v.strip().upper()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Valida y limpia el nombre"""
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class CostCenterCreate(CostCenterBase):
    """Schema para crear centros de costo"""
    pass


class CostCenterUpdate(BaseModel):
    """Schema para actualizar centros de costo"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    parent_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    allows_direct_assignment: Optional[bool] = None
    manager_name: Optional[str] = Field(None, max_length=200)
    budget_code: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Valida y limpia el nombre si está presente"""
        if v is not None:
            if not v.strip():
                raise ValueError("El nombre no puede estar vacío")
            return v.strip()
        return v


class CostCenterRead(BaseModel):
    """Schema para leer centros de costo"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: bool
    allows_direct_assignment: bool
    manager_name: Optional[str] = None
    budget_code: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Propiedades calculadas - se asignan manualmente en el servicio
    full_code: Optional[str] = None
    level: Optional[int] = None
    is_leaf: Optional[bool] = None


class CostCenterHierarchy(CostCenterRead):
    """Schema para centros de costo con jerarquía"""
    parent: Optional["CostCenterRead"] = None
    children: List["CostCenterRead"] = []


class CostCenterSummary(BaseModel):
    """Schema resumido para listados"""
    id: uuid.UUID
    code: str
    name: str
    is_active: bool
    level: Optional[int] = None
    parent_name: Optional[str] = None
    children_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class CostCenterList(BaseModel):
    """Schema para listado paginado"""
    cost_centers: List[CostCenterSummary]
    total: int
    page: int
    size: int
    pages: int


# Schemas para filtros y búsquedas
class CostCenterFilter(BaseModel):
    """Schema para filtrar centros de costo"""
    search: Optional[str] = None  # Búsqueda en código, nombre o descripción
    is_active: Optional[bool] = None
    parent_id: Optional[uuid.UUID] = None
    allows_direct_assignment: Optional[bool] = None
    level: Optional[int] = None


# Schemas para reportes
class CostCenterMovement(BaseModel):
    """Schema para movimientos por centro de costo"""
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    entry_date: datetime
    account_code: str
    account_name: str
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    reference: Optional[str] = None


class CostCenterReport(BaseModel):
    """Schema para reportes de centros de costo"""
    cost_center: CostCenterRead
    period_start: datetime
    period_end: datetime
    movements: List[CostCenterMovement]
    total_debits: Decimal
    total_credits: Decimal
    net_amount: Decimal
    movement_count: int


class CostCenterBudgetSummary(BaseModel):
    """Schema para resumen presupuestario"""
    cost_center_id: uuid.UUID
    cost_center_code: str
    cost_center_name: str
    budgeted_amount: Optional[Decimal] = None
    actual_amount: Decimal
    variance: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None


# Schemas para importación/exportación
class CostCenterImport(BaseModel):
    """Schema para importar centros de costo"""
    code: str
    name: str
    description: Optional[str] = None
    parent_code: Optional[str] = None  # Código del padre en lugar de ID
    manager_name: Optional[str] = None
    budget_code: Optional[str] = None


class CostCenterExport(BaseModel):
    """Schema para exportar centros de costo"""
    code: str
    name: str
    description: Optional[str] = None
    parent_code: Optional[str] = None
    full_code: str
    level: int
    is_active: bool
    allows_direct_assignment: bool
    manager_name: Optional[str] = None
    budget_code: Optional[str] = None
    children_count: int
    created_at: datetime


# Schemas para validaciones
class CostCenterValidation(BaseModel):
    """Schema para validación de centros de costo"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    hierarchy_valid: bool
    code_unique: bool


# Schemas para operaciones masivas
class BulkCostCenterOperation(BaseModel):
    """Schema para operaciones masivas"""
    cost_center_ids: List[uuid.UUID]
    operation: str  # 'activate', 'deactivate', 'delete'
    reason: Optional[str] = None


class CostCenterStats(BaseModel):
    """Schema para estadísticas de centros de costo"""
    total_cost_centers: int
    active_cost_centers: int
    inactive_cost_centers: int
    root_cost_centers: int  # Sin padre
    leaf_cost_centers: int  # Sin hijos
    max_hierarchy_level: int
    cost_centers_with_movements: int


# API Response schemas
class CostCenterResponse(CostCenterRead):
    """Standard API response for cost centers"""
    pass


class CostCenterDetailResponse(CostCenterHierarchy):
    """Detailed API response with hierarchy"""
    pass


class CostCenterListResponse(BaseModel):
    """Paginated list response"""
    items: List[CostCenterSummary]
    total: int
    skip: int
    limit: int


# Advanced Cost Center Reporting Schemas

class CostCenterProfitabilityMetrics(BaseModel):
    """Métricas de rentabilidad de centro de costo"""
    revenue: Decimal = Field(..., description="Ingresos totales")
    direct_costs: Decimal = Field(..., description="Costos directos")
    indirect_costs: Decimal = Field(..., description="Costos indirectos asignados")
    total_costs: Decimal = Field(..., description="Costos totales")
    gross_profit: Decimal = Field(..., description="Utilidad bruta")
    net_profit: Decimal = Field(..., description="Utilidad neta")
    gross_margin: Decimal = Field(..., description="Margen bruto (%)")
    net_margin: Decimal = Field(..., description="Margen neto (%)")
    cost_efficiency: Decimal = Field(..., description="Eficiencia de costos")


class CostCenterProfitability(BaseModel):
    """Análisis de rentabilidad de centro de costo"""
    cost_center: CostCenterRead
    period_start: datetime
    period_end: datetime
    metrics: CostCenterProfitabilityMetrics
    comparison_metrics: Optional[CostCenterProfitabilityMetrics] = None
    revenue_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    cost_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    trends: Optional[Dict[str, List[Decimal]]] = None
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class CostCenterComparisonItem(BaseModel):
    """Item de comparación entre centros de costo"""
    cost_center: CostCenterRead
    metrics: CostCenterProfitabilityMetrics
    ranking: int = Field(..., description="Posición en el ranking")
    variance_from_best: Decimal = Field(..., description="Variación respecto al mejor")


class CostCenterComparison(BaseModel):
    """Comparación entre centros de costo"""
    period_start: datetime
    period_end: datetime
    comparison_metrics: List[str]
    cost_centers: List[CostCenterComparisonItem]
    summary_statistics: Dict[str, Decimal]
    insights: List[str] = Field(default_factory=list)
    best_performer: Optional[CostCenterRead] = None
    worst_performer: Optional[CostCenterRead] = None


class BudgetVariance(BaseModel):
    """Variación presupuestaria"""
    budget_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    status: str = Field(..., description="favorable, unfavorable, on_target")


class CostCenterBudgetTracking(BaseModel):
    """Seguimiento presupuestario de centro de costo"""
    cost_center: CostCenterRead
    budget_year: int
    month: Optional[int] = None
    revenue_variance: BudgetVariance
    cost_variance: BudgetVariance
    profit_variance: BudgetVariance
    monthly_actuals: List[Dict[str, Decimal]] = Field(default_factory=list)
    monthly_budgets: List[Dict[str, Decimal]] = Field(default_factory=list)
    forecast: Optional[Dict[str, Decimal]] = None
    alerts: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class CostCenterKPIValue(BaseModel):
    """Valor de KPI con contexto"""
    value: Decimal
    unit: str
    status: str = Field(..., description="excellent, good, average, poor")
    trend: str = Field(..., description="improving, stable, declining")
    benchmark_value: Optional[Decimal] = None
    target_value: Optional[Decimal] = None


class CostCenterKPIs(BaseModel):
    """Indicadores clave de rendimiento"""
    cost_center: CostCenterRead
    period_start: datetime
    period_end: datetime
    profitability_ratio: CostCenterKPIValue
    cost_efficiency: CostCenterKPIValue
    revenue_growth: CostCenterKPIValue
    cost_per_unit: Optional[CostCenterKPIValue] = None
    employee_productivity: Optional[CostCenterKPIValue] = None
    quality_score: Optional[CostCenterKPIValue] = None
    customer_satisfaction: Optional[CostCenterKPIValue] = None
    overall_score: Decimal = Field(..., description="Puntuación general (0-100)")
    performance_level: str = Field(..., description="outstanding, excellent, good, average, poor")


class CostCenterRankingItem(BaseModel):
    """Item de ranking de centro de costo"""
    position: int
    cost_center: CostCenterRead
    metric_value: Decimal
    metric_description: str
    performance_score: Decimal
    trend: str = Field(..., description="up, stable, down")


class CostCenterRanking(BaseModel):
    """Ranking de centros de costo"""
    ranking_metric: str
    period_start: datetime
    period_end: datetime
    rankings: List[CostCenterRankingItem]
    metric_statistics: Dict[str, Decimal]
    insights: List[str] = Field(default_factory=list)


class CostCenterAlert(BaseModel):
    """Alerta de centro de costo"""
    alert_type: str = Field(..., description="budget_overrun, low_profitability, efficiency_decline")
    severity: str = Field(..., description="low, medium, high, critical")
    cost_center: CostCenterRead
    message: str
    metric_value: Decimal
    threshold_value: Decimal
    recommended_action: str


# Reconstruir modelos con referencias forward
CostCenterHierarchy.model_rebuild()
