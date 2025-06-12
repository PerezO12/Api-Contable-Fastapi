"""
Cost Center Reporting Service for advanced analytics and reporting.
Provides profitability analysis, budget tracking, KPIs and comparative reports.
"""
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from calendar import monthrange

from sqlalchemy import select, func, and_, or_, desc, asc, case, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.cost_center import CostCenter
from app.models.journal_entry import JournalEntryLine, JournalEntry, JournalEntryStatus
from app.models.account import Account, AccountType, AccountCategory
from app.schemas.cost_center import (
    CostCenterRead, CostCenterProfitability, CostCenterProfitabilityMetrics,
    CostCenterComparison, CostCenterComparisonItem, CostCenterBudgetTracking,
    BudgetVariance, CostCenterKPIs, CostCenterKPIValue, CostCenterRanking,
    CostCenterRankingItem, CostCenterAlert
)
from app.utils.exceptions import NotFoundError, ValidationError


class CostCenterReportingService:
    """Servicio para reportes avanzados de centros de costo"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cost_center_profitability(
        self,
        cost_center_id: uuid.UUID,
        start_date: date,
        end_date: date,
        include_indirect_costs: bool = True,
        comparison_period: bool = False
    ) -> CostCenterProfitability:
        """Generar análisis de rentabilidad para un centro de costo"""
        
        # Obtener centro de costo
        cost_center = await self._get_cost_center_or_404(cost_center_id)
        
        # Calcular métricas principales
        metrics = await self._calculate_profitability_metrics(
            cost_center_id, start_date, end_date, include_indirect_costs
        )
        
        # Calcular métricas de comparación si se solicita
        comparison_metrics = None
        if comparison_period:
            # Período anterior de igual duración
            period_days = (end_date - start_date).days
            comparison_start = start_date - timedelta(days=period_days + 1)
            comparison_end = start_date - timedelta(days=1)
            
            comparison_metrics = await self._calculate_profitability_metrics(
                cost_center_id, comparison_start, comparison_end, include_indirect_costs
            )
        
        # Obtener desglose de ingresos y costos
        revenue_breakdown = await self._get_revenue_breakdown(
            cost_center_id, start_date, end_date
        )
        cost_breakdown = await self._get_cost_breakdown(
            cost_center_id, start_date, end_date, include_indirect_costs
        )
        
        # Generar insights y recomendaciones
        insights = self._generate_profitability_insights(metrics, comparison_metrics)
        recommendations = self._generate_profitability_recommendations(metrics)
        
        return CostCenterProfitability(
            cost_center=CostCenterRead.model_validate(cost_center),
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            metrics=metrics,
            comparison_metrics=comparison_metrics,
            revenue_breakdown=revenue_breakdown,
            cost_breakdown=cost_breakdown,
            insights=insights,
            recommendations=recommendations
        )

    async def compare_cost_centers(
        self,
        cost_center_ids: List[uuid.UUID],
        start_date: date,
        end_date: date,
        metrics: List[str]
    ) -> CostCenterComparison:
        """Comparar rendimiento entre múltiples centros de costo"""
        
        comparison_items = []
        
        # Calcular métricas para cada centro de costo
        for cost_center_id in cost_center_ids:
            cost_center = await self._get_cost_center_or_404(cost_center_id)
            profitability_metrics = await self._calculate_profitability_metrics(
                cost_center_id, start_date, end_date, True
            )
            
            comparison_items.append({
                'cost_center': cost_center,
                'metrics': profitability_metrics
            })
        
        # Ordenar por rentabilidad
        comparison_items.sort(
            key=lambda x: x['metrics'].net_margin, 
            reverse=True
        )
        
        # Asignar rankings y calcular variaciones
        ranked_items = []
        best_margin = comparison_items[0]['metrics'].net_margin if comparison_items else Decimal('0')
        
        for i, item in enumerate(comparison_items):
            variance = item['metrics'].net_margin - best_margin
            ranked_items.append(
                CostCenterComparisonItem(
                    cost_center=CostCenterRead.model_validate(item['cost_center']),
                    metrics=item['metrics'],
                    ranking=i + 1,
                    variance_from_best=variance
                )
            )
        
        # Calcular estadísticas resumen
        summary_stats = self._calculate_comparison_statistics(ranked_items)
        insights = self._generate_comparison_insights(ranked_items)
        
        return CostCenterComparison(
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            comparison_metrics=metrics,
            cost_centers=ranked_items,
            summary_statistics=summary_stats,
            insights=insights,
            best_performer=ranked_items[0].cost_center if ranked_items else None,
            worst_performer=ranked_items[-1].cost_center if ranked_items else None
        )

    async def get_budget_tracking(
        self,
        cost_center_id: uuid.UUID,
        budget_year: int,
        month: Optional[int] = None,
        include_forecast: bool = True
    ) -> CostCenterBudgetTracking:
        """Seguimiento presupuestario de centro de costo"""
        
        cost_center = await self._get_cost_center_or_404(cost_center_id)
        
        # Determinar período de análisis
        if month:
            start_date = date(budget_year, month, 1)
            end_date = date(budget_year, month, monthrange(budget_year, month)[1])
        else:
            start_date = date(budget_year, 1, 1)
            end_date = date(budget_year, 12, 31)
        
        # Obtener datos reales
        actual_metrics = await self._calculate_profitability_metrics(
            cost_center_id, start_date, end_date, True
        )
        
        # Simular datos presupuestarios (en implementación real vendría de tabla de presupuestos)
        budget_revenue = actual_metrics.revenue * Decimal('1.1')  # Presupuesto 10% mayor
        budget_costs = actual_metrics.total_costs * Decimal('0.95')  # Presupuesto 5% menor
        budget_profit = budget_revenue - budget_costs
        
        # Calcular variaciones
        revenue_variance = BudgetVariance(
            budget_amount=budget_revenue,
            actual_amount=actual_metrics.revenue,
            variance_amount=actual_metrics.revenue - budget_revenue,
            variance_percentage=((actual_metrics.revenue - budget_revenue) / budget_revenue * 100) if budget_revenue > 0 else Decimal('0'),
            status="favorable" if actual_metrics.revenue >= budget_revenue else "unfavorable"
        )
        
        cost_variance = BudgetVariance(
            budget_amount=budget_costs,
            actual_amount=actual_metrics.total_costs,
            variance_amount=actual_metrics.total_costs - budget_costs,
            variance_percentage=((actual_metrics.total_costs - budget_costs) / budget_costs * 100) if budget_costs > 0 else Decimal('0'),
            status="favorable" if actual_metrics.total_costs <= budget_costs else "unfavorable"
        )
        
        profit_variance = BudgetVariance(
            budget_amount=budget_profit,
            actual_amount=actual_metrics.net_profit,
            variance_amount=actual_metrics.net_profit - budget_profit,
            variance_percentage=((actual_metrics.net_profit - budget_profit) / budget_profit * 100) if budget_profit > 0 else Decimal('0'),
            status="favorable" if actual_metrics.net_profit >= budget_profit else "unfavorable"
        )
        
        # Generar alertas y recomendaciones
        alerts = self._generate_budget_alerts(revenue_variance, cost_variance, profit_variance)
        recommendations = self._generate_budget_recommendations(revenue_variance, cost_variance, profit_variance)
        
        return CostCenterBudgetTracking(
            cost_center=CostCenterRead.model_validate(cost_center),
            budget_year=budget_year,
            month=month,
            revenue_variance=revenue_variance,
            cost_variance=cost_variance,
            profit_variance=profit_variance,
            alerts=alerts,
            recommendations=recommendations
        )

    async def get_cost_center_kpis(
        self,
        cost_center_id: uuid.UUID,
        start_date: date,
        end_date: date,
        include_trends: bool = True,
        benchmark_period: Optional[int] = None
    ) -> CostCenterKPIs:
        """Obtener KPIs de centro de costo"""
        
        cost_center = await self._get_cost_center_or_404(cost_center_id)
        
        # Calcular métricas base
        metrics = await self._calculate_profitability_metrics(
            cost_center_id, start_date, end_date, True
        )
        
        # Calcular KPIs
        profitability_ratio = CostCenterKPIValue(
            value=metrics.net_margin,
            unit="%",
            status=self._classify_performance(metrics.net_margin, [5, 10, 15, 20]),
            trend="stable"  # Se calcularía con datos históricos
        )
        
        cost_efficiency = CostCenterKPIValue(
            value=metrics.cost_efficiency,
            unit="ratio",
            status=self._classify_performance(metrics.cost_efficiency, [0.7, 0.8, 0.9, 0.95]),
            trend="stable"
        )
        
        revenue_growth = CostCenterKPIValue(
            value=Decimal('0'),  # Se calcularía con período anterior
            unit="%",
            status="average",
            trend="stable"
        )
        
        # Calcular puntuación general
        overall_score = self._calculate_overall_score([
            profitability_ratio.value,
            cost_efficiency.value * 100,
            revenue_growth.value
        ])
        
        performance_level = self._classify_overall_performance(overall_score)
        
        return CostCenterKPIs(
            cost_center=CostCenterRead.model_validate(cost_center),
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            profitability_ratio=profitability_ratio,
            cost_efficiency=cost_efficiency,
            revenue_growth=revenue_growth,
            overall_score=overall_score,
            performance_level=performance_level
        )

    async def get_cost_center_ranking(
        self,
        ranking_metric: str,
        start_date: date,
        end_date: date,
        limit: int = 10,
        include_inactive: bool = False
    ) -> CostCenterRanking:
        """Obtener ranking de centros de costo"""
        
        # Obtener todos los centros de costo activos
        query = select(CostCenter)
        if not include_inactive:
            query = query.where(CostCenter.is_active == True)
        
        result = await self.db.execute(query)
        cost_centers = result.scalars().all()
        
        # Calcular métricas para cada centro de costo
        ranking_items = []
        for cost_center in cost_centers:
            metrics = await self._calculate_profitability_metrics(
                cost_center.id, start_date, end_date, True
            )
            
            # Seleccionar métrica para ranking
            metric_value = self._get_ranking_metric_value(metrics, ranking_metric)
            
            ranking_items.append({
                'cost_center': cost_center,
                'metric_value': metric_value,
                'metrics': metrics
            })
        
        # Ordenar por métrica
        ranking_items.sort(key=lambda x: x['metric_value'], reverse=True)
        
        # Crear items de ranking
        ranked_list = []
        for i, item in enumerate(ranking_items[:limit]):
            ranked_list.append(
                CostCenterRankingItem(
                    position=i + 1,
                    cost_center=CostCenterRead.model_validate(item['cost_center']),
                    metric_value=item['metric_value'],
                    metric_description=self._get_metric_description(ranking_metric),
                    performance_score=self._calculate_performance_score(item['metrics']),
                    trend="stable"  # Se calcularía con datos históricos
                )
            )
        
        # Estadísticas de la métrica
        metric_values = [item['metric_value'] for item in ranking_items]
        metric_stats = {
            'average': sum(metric_values) / len(metric_values) if metric_values else Decimal('0'),
            'median': sorted(metric_values)[len(metric_values)//2] if metric_values else Decimal('0'),
            'max': max(metric_values) if metric_values else Decimal('0'),
            'min': min(metric_values) if metric_values else Decimal('0')
        }
        
        insights = self._generate_ranking_insights(ranked_list, ranking_metric)
        
        return CostCenterRanking(
            ranking_metric=ranking_metric,
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            rankings=ranked_list,
            metric_statistics=metric_stats,
            insights=insights
        )

    async def get_hierarchy_analysis(
        self,
        start_date: date,
        end_date: date,
        root_cost_center_id: Optional[uuid.UUID] = None,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """Análisis de jerarquía de centros de costo"""
        
        # Obtener jerarquía
        hierarchy_query = select(CostCenter).options(
            selectinload(CostCenter.children),
            selectinload(CostCenter.parent)
        )
        
        if root_cost_center_id:
            hierarchy_query = hierarchy_query.where(
                or_(
                    CostCenter.id == root_cost_center_id,
                    CostCenter.parent_id == root_cost_center_id
                )
            )
        
        result = await self.db.execute(hierarchy_query)
        cost_centers = result.scalars().all()
        
        # Calcular métricas para cada nivel
        hierarchy_data = []
        for cost_center in cost_centers:
            metrics = await self._calculate_profitability_metrics(
                cost_center.id, start_date, end_date, True
            )
            
            hierarchy_data.append({
                'cost_center': CostCenterRead.model_validate(cost_center),
                'level': cost_center.level,
                'metrics': metrics,
                'contribution_to_parent': self._calculate_contribution_percentage(cost_center, metrics)
            })
        
        return {
            'period_start': start_date,
            'period_end': end_date,
            'hierarchy_data': hierarchy_data,
            'summary': self._generate_hierarchy_summary(hierarchy_data),
            'insights': self._generate_hierarchy_insights(hierarchy_data)
        }

    async def get_executive_dashboard(
        self,
        period: str = "current_month",
        top_performers_count: int = 5,
        include_alerts: bool = True
    ) -> Dict[str, Any]:
        """Dashboard ejecutivo de centros de costo"""
        
        # Determinar fechas según período
        start_date, end_date = self._get_period_dates(period)
        
        # Obtener métricas consolidadas
        total_metrics = await self._calculate_consolidated_metrics(start_date, end_date)
        
        # Obtener top performers
        ranking = await self.get_cost_center_ranking(
            "profit", start_date, end_date, top_performers_count
        )
        
        # Generar alertas si se solicita
        alerts = []
        if include_alerts:
            alerts = await self._generate_executive_alerts(start_date, end_date)
        
        return {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'consolidated_metrics': total_metrics,
            'top_performers': ranking.rankings,
            'alerts': alerts,
            'summary_insights': self._generate_executive_insights(total_metrics, ranking.rankings),
            'generated_at': datetime.now()
        }

    # Métodos auxiliares

    async def _get_cost_center_or_404(self, cost_center_id: uuid.UUID) -> CostCenter:
        """Obtener centro de costo o lanzar error 404"""
        result = await self.db.execute(
            select(CostCenter).where(CostCenter.id == cost_center_id)
        )
        cost_center = result.scalar_one_or_none()
        
        if not cost_center:
            raise NotFoundError("Centro de costo no encontrado")
        
        return cost_center

    async def _calculate_profitability_metrics(
        self,
        cost_center_id: uuid.UUID,
        start_date: date,
        end_date: date,
        include_indirect_costs: bool
    ) -> CostCenterProfitabilityMetrics:
        """Calcular métricas de rentabilidad"""
        
        # Consulta para obtener movimientos del centro de costo
        movements_query = (
            select(
                Account.account_type,
                func.sum(JournalEntryLine.debit_amount).label('total_debits'),
                func.sum(JournalEntryLine.credit_amount).label('total_credits')
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(Account, JournalEntryLine.account_id == Account.id)
            .where(
                and_(
                    JournalEntryLine.cost_center_id == cost_center_id,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                    JournalEntry.status == JournalEntryStatus.POSTED
                )
            )
            .group_by(Account.account_type)
        )
        
        result = await self.db.execute(movements_query)
        movements = result.all()
        
        # Calcular totales por tipo de cuenta
        revenue = Decimal('0')
        direct_costs = Decimal('0')
        
        for account_type, debits, credits in movements:
            if account_type == AccountType.INGRESO:
                revenue += (credits or Decimal('0')) - (debits or Decimal('0'))
            elif account_type in [AccountType.GASTO, AccountType.COSTOS]:
                direct_costs += (debits or Decimal('0')) - (credits or Decimal('0'))
        
        # Costos indirectos (simplificado - en implementación real se asignarían según reglas)
        indirect_costs = direct_costs * Decimal('0.15') if include_indirect_costs else Decimal('0')
        
        total_costs = direct_costs + indirect_costs
        gross_profit = revenue - direct_costs
        net_profit = revenue - total_costs
        
        # Calcular márgenes
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else Decimal('0')
        net_margin = (net_profit / revenue * 100) if revenue > 0 else Decimal('0')
        
        # Eficiencia de costos
        cost_efficiency = (revenue / total_costs) if total_costs > 0 else Decimal('0')
        
        return CostCenterProfitabilityMetrics(
            revenue=revenue,
            direct_costs=direct_costs,
            indirect_costs=indirect_costs,
            total_costs=total_costs,
            gross_profit=gross_profit,
            net_profit=net_profit,
            gross_margin=gross_margin,
            net_margin=net_margin,
            cost_efficiency=cost_efficiency
        )

    async def _get_revenue_breakdown(
        self, cost_center_id: uuid.UUID, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Obtener desglose de ingresos por cuenta"""
        
        query = (
            select(
                Account.code,
                Account.name,
                func.sum(JournalEntryLine.credit_amount - JournalEntryLine.debit_amount).label('amount')
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(Account, JournalEntryLine.account_id == Account.id)
            .where(
                and_(
                    JournalEntryLine.cost_center_id == cost_center_id,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                    JournalEntry.status == JournalEntryStatus.POSTED,
                    Account.account_type == AccountType.INGRESO
                )
            )
            .group_by(Account.code, Account.name)
            .order_by(desc('amount'))
        )
        
        result = await self.db.execute(query)
        breakdown = []
        
        for code, name, amount in result.all():
            breakdown.append({
                'account_code': code,
                'account_name': name,
                'amount': amount or Decimal('0'),
                'percentage': 0  # Se calcularía con el total de ingresos
            })
        
        return breakdown

    async def _get_cost_breakdown(
        self, cost_center_id: uuid.UUID, start_date: date, end_date: date, include_indirect: bool
    ) -> List[Dict[str, Any]]:
        """Obtener desglose de costos por cuenta"""
        
        query = (
            select(
                Account.code,
                Account.name,
                func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount).label('amount')
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(Account, JournalEntryLine.account_id == Account.id)
            .where(
                and_(
                    JournalEntryLine.cost_center_id == cost_center_id,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                    JournalEntry.status == JournalEntryStatus.POSTED,
                    Account.account_type.in_([AccountType.GASTO, AccountType.COSTOS])
                )
            )
            .group_by(Account.code, Account.name)
            .order_by(desc('amount'))
        )
        
        result = await self.db.execute(query)
        breakdown = []
        
        for code, name, amount in result.all():            breakdown.append({
                'account_code': code,
                'account_name': name,
                'amount': amount or Decimal('0'),
                'type': 'direct'
            })
        
        return breakdown

    def _generate_profitability_insights(
        self, metrics: CostCenterProfitabilityMetrics, comparison: Optional[CostCenterProfitabilityMetrics]
    ) -> List[str]:
        """Generar insights de rentabilidad"""
        insights = []
        
        if metrics.net_margin > 20:
            insights.append("Excelente margen de rentabilidad, superior al 20%")
        elif metrics.net_margin < 5:
            insights.append("Margen de rentabilidad bajo, requiere atención")
        
        if metrics.cost_efficiency > 1.5:
            insights.append("Alta eficiencia en el uso de recursos")
        elif metrics.cost_efficiency < 1.1:
            insights.append("Eficiencia de costos por debajo del promedio")
        
        if comparison:
            margin_change = metrics.net_margin - comparison.net_margin
            if margin_change > 2:
                insights.append(f"Mejora significativa en rentabilidad: +{margin_change:.1f}%")
            elif margin_change < -2:
                insights.append(f"Deterioro en rentabilidad: {margin_change:.1f}%")
        
        return insights

    def _generate_profitability_recommendations(self, metrics: CostCenterProfitabilityMetrics) -> List[str]:
        """Generar recomendaciones de rentabilidad"""
        recommendations = []
        
        if metrics.net_margin < 10:
            recommendations.append("Revisar estructura de costos para mejorar rentabilidad")
        
        if metrics.cost_efficiency < 1.2:
            recommendations.append("Implementar medidas de eficiencia operativa")
        
        if metrics.indirect_costs > metrics.direct_costs * Decimal('0.3'):
            recommendations.append("Analizar y optimizar asignación de costos indirectos")
        
        return recommendations

    def _classify_performance(self, value: Decimal, thresholds: List[float]) -> str:
        """Clasificar rendimiento según umbrales"""
        if value >= thresholds[3]:
            return "excellent"
        elif value >= thresholds[2]:
            return "good"
        elif value >= thresholds[1]:
            return "average"
        else:
            return "poor"

    def _calculate_overall_score(self, values: List[Decimal]) -> Decimal:
        """Calcular puntuación general"""
        if not values:
            return Decimal('0')
        
        # Promedio ponderado simple
        total = sum(abs(val) for val in values)
        average = Decimal(str(total)) / Decimal(str(len(values)))
        return min(average, Decimal('100'))

    def _classify_overall_performance(self, score: Decimal) -> str:
        """Clasificar rendimiento general"""
        if score >= 90:
            return "outstanding"
        elif score >= 80:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 60:
            return "average"
        else:
            return "poor"

    def _get_ranking_metric_value(self, metrics: CostCenterProfitabilityMetrics, metric: str) -> Decimal:
        """Obtener valor de métrica para ranking"""
        metric_map = {
            'profit': metrics.net_profit,
            'margin': metrics.net_margin,            'efficiency': metrics.cost_efficiency,
            'revenue': metrics.revenue,
            'cost_per_unit': metrics.total_costs  # Simplificado
        }
        return metric_map.get(metric, Decimal('0'))

    def _get_metric_description(self, metric: str) -> str:
        """Obtener descripción de métrica"""
        descriptions = {
            'profit': 'Utilidad neta',
            'margin': 'Margen de rentabilidad (%)',
            'efficiency': 'Eficiencia de costos',
            'revenue': 'Ingresos totales',
            'cost_per_unit': 'Costo por unidad'
        }
        return descriptions.get(metric, 'Métrica desconocida')

    def _calculate_performance_score(self, metrics: CostCenterProfitabilityMetrics) -> Decimal:
        """Calcular puntuación de rendimiento"""
        # Fórmula simplificada
        margin_score = min(metrics.net_margin * 2, Decimal('40'))
        efficiency_score = min(metrics.cost_efficiency * 30, Decimal('30'))
        revenue_score = min(metrics.revenue / 10000, Decimal('30'))
        
        return margin_score + efficiency_score + revenue_score

    def _generate_ranking_insights(self, rankings: List[CostCenterRankingItem], metric: str) -> List[str]:
        """Generar insights de ranking"""
        insights = []
        
        if rankings:
            top_performer = rankings[0]
            insights.append(f"Mejor rendimiento: {top_performer.cost_center.name} con {top_performer.metric_value}")
        
        if len(rankings) > 1:
            performance_gap = rankings[0].metric_value - rankings[-1].metric_value
            insights.append(f"Brecha de rendimiento: {performance_gap}")
        
        return insights

    def _calculate_comparison_statistics(self, items: List[CostCenterComparisonItem]) -> Dict[str, Decimal]:
        """Calcular estadísticas de comparación"""
        if not items:
            return {}
        
        margins = [item.metrics.net_margin for item in items]
        revenues = [item.metrics.revenue for item in items]
        
        return {
            'avg_margin': Decimal(str(sum(margins))) / Decimal(str(len(margins))),
            'avg_revenue': Decimal(str(sum(revenues))) / Decimal(str(len(revenues))),
            'margin_std': Decimal('0'),  # Se calcularía la desviación estándar
            'revenue_std': Decimal('0')
        }

    def _generate_comparison_insights(self, items: List[CostCenterComparisonItem]) -> List[str]:
        """Generar insights de comparación"""
        insights = []
        
        if items:
            best = items[0]
            worst = items[-1]
            
            gap = best.metrics.net_margin - worst.metrics.net_margin
            insights.append(f"Brecha de rentabilidad: {gap:.1f}% entre mejor y peor centro")
        
        return insights

    def _generate_budget_alerts(
        self, revenue_var: BudgetVariance, cost_var: BudgetVariance, profit_var: BudgetVariance
    ) -> List[str]:
        """Generar alertas presupuestarias"""
        alerts = []
        
        if abs(revenue_var.variance_percentage) > 10:
            alerts.append(f"Variación significativa en ingresos: {revenue_var.variance_percentage:.1f}%")
        
        if abs(cost_var.variance_percentage) > 15:
            alerts.append(f"Desviación importante en costos: {cost_var.variance_percentage:.1f}%")
        
        if profit_var.status == "unfavorable" and abs(profit_var.variance_percentage) > 20:
            alerts.append("Alerta crítica: utilidad muy por debajo del presupuesto")
        
        return alerts

    def _generate_budget_recommendations(
        self, revenue_var: BudgetVariance, cost_var: BudgetVariance, profit_var: BudgetVariance
    ) -> List[str]:
        """Generar recomendaciones presupuestarias"""
        recommendations = []
        
        if revenue_var.status == "unfavorable":
            recommendations.append("Revisar estrategias de generación de ingresos")
        
        if cost_var.status == "unfavorable":
            recommendations.append("Implementar medidas de control de costos")
        
        if profit_var.status == "unfavorable":
            recommendations.append("Ajustar presupuesto o mejorar eficiencia operativa")
        
        return recommendations

    def _get_period_dates(self, period: str) -> tuple[date, date]:
        """Obtener fechas según período"""
        today = date.today()
        
        if period == "current_month":
            start_date = date(today.year, today.month, 1)
            end_date = today
        elif period == "current_quarter":
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = date(today.year, quarter_start_month, 1)
            end_date = today
        elif period == "current_year":
            start_date = date(today.year, 1, 1)
            end_date = today
        else:
            # Default to current month
            start_date = date(today.year, today.month, 1)
            end_date = today
        
        return start_date, end_date

    async def _calculate_consolidated_metrics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calcular métricas consolidadas"""
        # Obtener todos los centros de costo activos
        query = select(CostCenter).where(CostCenter.is_active == True)
        result = await self.db.execute(query)
        cost_centers = result.scalars().all()
        
        total_revenue = Decimal('0')
        total_costs = Decimal('0')
        total_profit = Decimal('0')
        
        for cost_center in cost_centers:
            metrics = await self._calculate_profitability_metrics(
                cost_center.id, start_date, end_date, True
            )
            total_revenue += metrics.revenue
            total_costs += metrics.total_costs
            total_profit += metrics.net_profit
        
        total_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        return {
            'total_revenue': total_revenue,
            'total_costs': total_costs,
            'total_profit': total_profit,
            'total_margin': total_margin,
            'active_cost_centers': len(cost_centers)
        }

    async def _generate_executive_alerts(self, start_date: date, end_date: date) -> List[CostCenterAlert]:
        """Generar alertas ejecutivas"""
        # Implementación simplificada
        return []

    def _generate_executive_insights(
        self, metrics: Dict[str, Any], top_performers: List[CostCenterRankingItem]
    ) -> List[str]:
        """Generar insights ejecutivos"""
        insights = []
        
        if metrics.get('total_margin', 0) > 15:
            insights.append("Rentabilidad consolidada excelente")
        elif metrics.get('total_margin', 0) < 5:
            insights.append("Rentabilidad consolidada requiere atención")
        
        if top_performers:
            insights.append(f"Mejor centro de costo: {top_performers[0].cost_center.name}")
        
        return insights

    def _calculate_contribution_percentage(self, cost_center: CostCenter, metrics: CostCenterProfitabilityMetrics) -> Decimal:
        """Calcular porcentaje de contribución al padre"""
        # Implementación simplificada
        return Decimal('0')

    def _generate_hierarchy_summary(self, hierarchy_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar resumen de jerarquía"""
        return {
            'total_centers': len(hierarchy_data),
            'total_revenue': sum(item['metrics'].revenue for item in hierarchy_data),
            'total_profit': sum(item['metrics'].net_profit for item in hierarchy_data)
        }

    def _generate_hierarchy_insights(self, hierarchy_data: List[Dict[str, Any]]) -> List[str]:
        """Generar insights de jerarquía"""
        return ["Análisis de jerarquía completado"]
