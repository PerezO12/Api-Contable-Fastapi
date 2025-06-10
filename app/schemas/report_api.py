"""
Schemas para la API de reportes financieros
Implementa la especificación exacta del endpoint /reports
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator


class ReportType(str, Enum):
    """Tipos de reportes disponibles"""
    BALANCE_GENERAL = "balance_general"
    FLUJO_EFECTIVO = "flujo_efectivo"
    P_G = "p_g"  # Pérdidas y Ganancias


class DetailLevel(str, Enum):
    """Niveles de detalle del reporte"""
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


class DateRange(BaseModel):
    """Rango de fechas para el reporte"""
    from_date: date = Field(..., alias="from", description="Fecha de inicio")
    to_date: date = Field(..., alias="to", description="Fecha de fin")
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        if 'from_date' in values and v < values['from_date']:
            raise ValueError('La fecha de fin debe ser mayor o igual a la fecha de inicio')
        return v


class ReportFilters(BaseModel):
    """Filtros adicionales para el reporte"""
    cost_center: Optional[List[str]] = Field(None, description="Centros de costo a incluir")
    tags: Optional[List[str]] = Field(None, description="Etiquetas a incluir")


class ReportRequest(BaseModel):
    """Request para generar reportes financieros"""
    project_context: str = Field(..., min_length=1, description="Contexto o nombre del proyecto")
    report_type: ReportType = Field(..., description="Tipo de reporte a generar")
    date_range: DateRange = Field(..., description="Rango de fechas")
    detail_level: DetailLevel = Field(DetailLevel.MEDIO, description="Nivel de detalle")
    include_subaccounts: bool = Field(False, description="Incluir subcuentas en el detalle")
    filters: Optional[ReportFilters] = Field(None, description="Filtros adicionales")


class AccountReportItem(BaseModel):
    """Item de cuenta en el reporte"""
    account_group: str = Field(..., description="Grupo de cuenta")
    account_code: Optional[str] = Field(None, description="Código de cuenta")
    account_name: str = Field(..., description="Nombre de cuenta")
    opening_balance: Decimal = Field(..., description="Saldo de apertura")
    movements: Decimal = Field(..., description="Movimientos del período")
    closing_balance: Decimal = Field(..., description="Saldo de cierre")
    subaccounts: Optional[List["AccountReportItem"]] = Field(None, description="Subcuentas si aplica")
    level: int = Field(1, description="Nivel en la jerarquía")


class ReportTable(BaseModel):
    """Tabla principal del reporte"""
    sections: List[Dict[str, Any]] = Field(..., description="Secciones del reporte")
    totals: Dict[str, Decimal] = Field(..., description="Totales principales")
    summary: Dict[str, Any] = Field(..., description="Resumen del reporte")


class ReportNarrative(BaseModel):
    """Narrativa del reporte con análisis y recomendaciones"""
    executive_summary: str = Field(..., description="Resumen ejecutivo")
    key_variations: List[str] = Field(..., description="Variaciones clave identificadas")
    recommendations: List[str] = Field(..., description="Recomendaciones")
    financial_highlights: List[str] = Field(..., description="Puntos destacados financieros")


class ReportResponse(BaseModel):
    """Respuesta completa del reporte"""
    success: bool = Field(True, description="Indica si el reporte se generó exitosamente")
    report_type: ReportType = Field(..., description="Tipo de reporte generado")
    generated_at: date = Field(..., description="Fecha de generación")
    period: DateRange = Field(..., description="Período del reporte")
    project_context: str = Field(..., description="Contexto del proyecto")
    table: ReportTable = Field(..., description="Datos tabulares del reporte")
    narrative: ReportNarrative = Field(..., description="Análisis narrativo")


class ReportError(BaseModel):
    """Error en la generación del reporte"""
    success: bool = Field(False, description="Indica que hubo un error")
    error_code: str = Field(..., description="Código del error")
    error_message: str = Field(..., description="Mensaje descriptivo del error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")


# Permitir referencias circulares para subaccounts
AccountReportItem.model_rebuild()
