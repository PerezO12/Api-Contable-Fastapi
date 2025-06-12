"""
API endpoints for cost center reporting and analytics.
Provides cost center profitability analysis, budget tracking and performance reports.
"""
import uuid
from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.cost_center import (
    CostCenterReport, CostCenterProfitability, CostCenterComparison,
    CostCenterBudgetTracking, CostCenterKPIs, CostCenterRanking
)
from app.services.cost_center_reporting_service import CostCenterReportingService
from app.utils.exceptions import (
    raise_validation_error, raise_not_found, raise_insufficient_permissions
)

router = APIRouter()


@router.get(
    "/{cost_center_id}/profitability",
    response_model=CostCenterProfitability,
    summary="Get cost center profitability analysis",
    description="Generate detailed profitability analysis for a specific cost center"
)
async def get_cost_center_profitability(
    cost_center_id: uuid.UUID,
    start_date: date = Query(..., description="Analysis start date"),
    end_date: date = Query(..., description="Analysis end date"),
    include_indirect_costs: bool = Query(True, description="Include allocated indirect costs"),
    comparison_period: bool = Query(False, description="Include comparison with previous period"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterProfitability:
    """Get profitability analysis for a cost center."""
    
    service = CostCenterReportingService(db)
    
    try:
        profitability = await service.get_cost_center_profitability(
            cost_center_id=cost_center_id,
            start_date=start_date,
            end_date=end_date,
            include_indirect_costs=include_indirect_costs,
            comparison_period=comparison_period
        )
        return profitability
    except Exception as e:
        raise_validation_error(f"Error generating profitability analysis: {str(e)}")


@router.get(
    "/comparison",
    response_model=CostCenterComparison,
    summary="Compare multiple cost centers",
    description="Compare performance metrics across multiple cost centers"
)
async def compare_cost_centers(
    cost_center_ids: List[uuid.UUID] = Query(..., description="List of cost center IDs to compare"),
    start_date: date = Query(..., description="Comparison start date"),
    end_date: date = Query(..., description="Comparison end date"),
    metrics: List[str] = Query(
        default=["revenue", "costs", "profit", "margin"], 
        description="Metrics to compare (revenue, costs, profit, margin, efficiency)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterComparison:
    """Compare performance across multiple cost centers."""
    
    if len(cost_center_ids) > 10:
        raise_validation_error("Cannot compare more than 10 cost centers at once")
    
    service = CostCenterReportingService(db)
    
    try:
        comparison = await service.compare_cost_centers(
            cost_center_ids=cost_center_ids,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics
        )
        return comparison
    except Exception as e:
        raise_validation_error(f"Error generating comparison: {str(e)}")


@router.get(
    "/{cost_center_id}/budget-tracking",
    response_model=CostCenterBudgetTracking,
    summary="Track budget vs actual performance",
    description="Monitor budget performance and variance analysis"
)
async def get_budget_tracking(
    cost_center_id: uuid.UUID,
    budget_year: int = Query(..., description="Budget year"),
    month: Optional[int] = Query(None, description="Specific month (1-12) or None for full year"),
    include_forecast: bool = Query(True, description="Include forecast projections"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterBudgetTracking:
    """Track budget vs actual performance for a cost center."""
    
    service = CostCenterReportingService(db)
    
    try:
        tracking = await service.get_budget_tracking(
            cost_center_id=cost_center_id,
            budget_year=budget_year,
            month=month,
            include_forecast=include_forecast
        )
        return tracking
    except Exception as e:
        raise_validation_error(f"Error generating budget tracking: {str(e)}")


@router.get(
    "/ranking",
    response_model=CostCenterRanking,
    summary="Rank cost centers by performance",
    description="Rank cost centers by various performance metrics"
)
async def get_cost_center_ranking(
    ranking_metric: str = Query(
        default="profit", 
        description="Ranking metric: profit, margin, efficiency, revenue, cost_per_unit"
    ),
    start_date: date = Query(..., description="Ranking period start date"),
    end_date: date = Query(..., description="Ranking period end date"),
    limit: int = Query(10, ge=1, le=50, description="Number of top cost centers to return"),
    include_inactive: bool = Query(False, description="Include inactive cost centers"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterRanking:
    """Get cost center ranking by performance metrics."""
    
    service = CostCenterReportingService(db)
    
    try:
        ranking = await service.get_cost_center_ranking(
            ranking_metric=ranking_metric,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            include_inactive=include_inactive
        )
        return ranking
    except Exception as e:
        raise_validation_error(f"Error generating ranking: {str(e)}")


@router.get(
    "/{cost_center_id}/kpis",
    response_model=CostCenterKPIs,
    summary="Get cost center KPIs",
    description="Get key performance indicators for a cost center"
)
async def get_cost_center_kpis(
    cost_center_id: uuid.UUID,
    start_date: date = Query(..., description="KPI calculation start date"),
    end_date: date = Query(..., description="KPI calculation end date"),
    include_trends: bool = Query(True, description="Include trend analysis"),
    benchmark_period: Optional[int] = Query(
        None, 
        description="Number of months back for benchmark comparison"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterKPIs:
    """Get key performance indicators for a cost center."""
    
    service = CostCenterReportingService(db)
    
    try:
        kpis = await service.get_cost_center_kpis(
            cost_center_id=cost_center_id,
            start_date=start_date,
            end_date=end_date,
            include_trends=include_trends,
            benchmark_period=benchmark_period
        )
        return kpis
    except Exception as e:
        raise_validation_error(f"Error generating KPIs: {str(e)}")


@router.get(
    "/hierarchy-analysis",
    summary="Analyze cost center hierarchy",
    description="Analyze performance across the entire cost center hierarchy"
)
async def get_hierarchy_analysis(
    start_date: date = Query(..., description="Analysis start date"),
    end_date: date = Query(..., description="Analysis end date"),
    root_cost_center_id: Optional[uuid.UUID] = Query(
        None, 
        description="Root cost center ID (None for full hierarchy)"
    ),
    max_depth: int = Query(3, ge=1, le=5, description="Maximum hierarchy depth to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze performance across cost center hierarchy."""
    
    service = CostCenterReportingService(db)
    
    try:
        analysis = await service.get_hierarchy_analysis(
            start_date=start_date,
            end_date=end_date,
            root_cost_center_id=root_cost_center_id,
            max_depth=max_depth
        )
        return analysis
    except Exception as e:
        raise_validation_error(f"Error generating hierarchy analysis: {str(e)}")


@router.get(
    "/executive-dashboard",
    summary="Executive cost center dashboard",
    description="High-level dashboard with key cost center metrics"
)
async def get_executive_dashboard(
    period: str = Query(
        default="current_month", 
        description="Period: current_month, current_quarter, current_year, last_month, last_quarter, last_year"
    ),
    top_performers_count: int = Query(5, ge=3, le=10, description="Number of top performers to show"),
    include_alerts: bool = Query(True, description="Include performance alerts"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get executive dashboard with cost center overview."""
    
    service = CostCenterReportingService(db)
    
    try:
        dashboard = await service.get_executive_dashboard(
            period=period,
            top_performers_count=top_performers_count,
            include_alerts=include_alerts
        )
        return dashboard
    except Exception as e:
        raise_validation_error(f"Error generating executive dashboard: {str(e)}")
