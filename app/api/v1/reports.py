"""
API endpoints for financial reports generation.
Siguiendo principios contables y mejores prácticas
"""
import uuid
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.account import AccountType
from app.schemas.reports import (
    BalanceSheet,
    IncomeStatement,
    TrialBalance,
    GeneralLedger,
    FinancialAnalysis,
    ReportExportRequest,
    ReportExportResponse
)
from app.services.report_service import ReportService
from app.utils.exceptions import (
    ReportGenerationError,
    raise_validation_error,
    raise_insufficient_permissions
)

router = APIRouter()


@router.get(
    "/balance-sheet",
    response_model=BalanceSheet,
    summary="Generate Balance Sheet",
    description="Generate Balance Sheet as of a specific date following accounting principles"
)
async def get_balance_sheet(
    as_of_date: Optional[date] = Query(None, description="Balance sheet as of date (defaults to today)"),
    include_zero_balances: bool = Query(False, description="Include accounts with zero balances"),
    company_name: Optional[str] = Query(None, description="Company name for the report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BalanceSheet:
    """
    Generate Balance Sheet report.
    
    The Balance Sheet follows the fundamental accounting equation:
    Assets = Liabilities + Equity
    """
    try:
        # Usar fecha actual si no se especifica
        report_date = as_of_date or date.today()
        
        service = ReportService(db)
        balance_sheet = await service.generate_balance_sheet(
            as_of_date=report_date,
            include_zero_balances=include_zero_balances,
            company_name=company_name
        )
        return balance_sheet
    except ReportGenerationError as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise_validation_error(f"Error generating balance sheet: {str(e)}")


@router.get(
    "/income-statement",
    response_model=IncomeStatement,
    summary="Generate Income Statement",
    description="Generate Income Statement for a specific period"
)
async def get_income_statement(
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    include_zero_balances: bool = Query(False, description="Include accounts with zero balances"),
    company_name: Optional[str] = Query(None, description="Company name for the report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> IncomeStatement:
    """
    Generate Income Statement report.
    
    Shows financial performance over a period:
    Net Income = Revenues - Expenses
    """
    try:
        # Validar fechas
        if end_date < start_date:
            raise_validation_error("End date must be after start date")
        
        service = ReportService(db)
        income_statement = await service.generate_income_statement(
            start_date=start_date,
            end_date=end_date,
            include_zero_balances=include_zero_balances,
            company_name=company_name
        )
        return income_statement
    except ReportGenerationError as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise_validation_error(f"Error generating income statement: {str(e)}")


@router.get(
    "/trial-balance",
    response_model=TrialBalance,
    summary="Generate Trial Balance",
    description="Generate Trial Balance to verify that debits equal credits"
)
async def get_trial_balance(
    as_of_date: Optional[date] = Query(None, description="Trial balance as of date (defaults to today)"),
    include_zero_balances: bool = Query(False, description="Include accounts with zero balances"),
    company_name: Optional[str] = Query(None, description="Company name for the report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> TrialBalance:
    """
    Generate Trial Balance report.
    
    Verifies the fundamental principle: Total Debits = Total Credits
    """
    try:
        report_date = as_of_date or date.today()
        
        service = ReportService(db)
        trial_balance = await service.generate_trial_balance(
            as_of_date=report_date,
            include_zero_balances=include_zero_balances,
            company_name=company_name
        )
        return trial_balance
    except ReportGenerationError as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise_validation_error(f"Error generating trial balance: {str(e)}")


@router.get(
    "/general-ledger",
    response_model=GeneralLedger,
    summary="Generate General Ledger",
    description="Generate General Ledger showing all transactions by account"
)
async def get_general_ledger(
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by specific account ID"),
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    company_name: Optional[str] = Query(None, description="Company name for the report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> GeneralLedger:
    """
    Generate General Ledger report.
    
    Shows detailed transaction history for accounts with running balances.
    """
    try:
        # Validar fechas
        if end_date < start_date:
            raise_validation_error("End date must be after start date")
        
        service = ReportService(db)
        general_ledger = await service.generate_general_ledger(
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            account_type=account_type,
            company_name=company_name
        )
        return general_ledger
    except ReportGenerationError as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise_validation_error(f"Error generating general ledger: {str(e)}")


@router.get(
    "/financial-analysis",
    response_model=FinancialAnalysis,
    summary="Generate Financial Analysis",
    description="Generate comprehensive financial analysis with ratios and interpretation"
)
async def get_financial_analysis(
    as_of_date: Optional[date] = Query(None, description="Analysis as of date (defaults to today)"),
    start_date: Optional[date] = Query(None, description="Period start date for profitability analysis"),
    end_date: Optional[date] = Query(None, description="Period end date for profitability analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> FinancialAnalysis:
    """
    Generate Financial Analysis report.
    
    Includes key financial ratios:
    - Liquidity ratios (current ratio)
    - Profitability ratios (net margin, ROA)
    - Leverage ratios (debt ratio)
    - Efficiency ratios
    """
    try:
        report_date = as_of_date or date.today()
        
        # Validar fechas si se proporcionan ambas
        if start_date and end_date and end_date < start_date:
            raise_validation_error("End date must be after start date")
        
        service = ReportService(db)
        financial_analysis = await service.generate_financial_analysis(
            as_of_date=report_date,
            start_date=start_date,
            end_date=end_date
        )
        return financial_analysis
    except ReportGenerationError as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise_validation_error(f"Error generating financial analysis: {str(e)}")


# Endpoints para exportación de reportes (implementación básica)

@router.post(
    "/export",
    response_model=ReportExportResponse,
    summary="Export Report",
    description="Export financial reports to various formats (PDF, Excel, CSV)"
)
async def export_report(
    export_request: ReportExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ReportExportResponse:
    """
    Export financial reports to various formats.
    
    Currently returns a mock response. In production, this would:
    1. Generate the requested report
    2. Export to the specified format
    3. Store in temporary location
    4. Return download URL
    """
    try:
        # TODO: Implementar exportación real
        # Por ahora, retornamos una respuesta mock
        
        file_name = f"{export_request.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_request.format}"
        
        return ReportExportResponse(
            file_url=f"/reports/downloads/{file_name}",
            file_name=file_name,
            file_size=1024,  # Mock size
            expires_at=date.today()
        )
    except Exception as e:
        raise_validation_error(f"Error exporting report: {str(e)}")


# Endpoints para reportes específicos por tipo de cuenta

@router.get(
    "/accounts-summary/{account_type}",
    response_model=List[dict],
    summary="Get Accounts Summary by Type",
    description="Get summary of accounts by type with current balances"
)
async def get_accounts_summary_by_type(
    account_type: AccountType,
    as_of_date: Optional[date] = Query(None, description="Summary as of date (defaults to today)"),
    include_zero_balances: bool = Query(False, description="Include accounts with zero balances"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[dict]:
    """
    Get summary of accounts by type.
    
    Useful for detailed analysis of specific account categories.
    """
    try:
        report_date = as_of_date or date.today()
        
        service = ReportService(db)
        
        # Generar libro mayor filtrado por tipo de cuenta
        general_ledger = await service.generate_general_ledger(
            start_date=date(report_date.year, 1, 1),  # Desde inicio del año
            end_date=report_date,
            account_type=account_type
        )
        
        # Convertir a formato de resumen
        summary = []
        for ledger_account in general_ledger.accounts:
            if include_zero_balances or ledger_account.closing_balance != 0:
                summary.append({
                    "account_id": str(ledger_account.account_id),
                    "account_code": ledger_account.account_code,
                    "account_name": ledger_account.account_name,
                    "opening_balance": float(ledger_account.opening_balance),
                    "total_debits": float(ledger_account.total_debits),
                    "total_credits": float(ledger_account.total_credits),
                    "closing_balance": float(ledger_account.closing_balance),
                    "movement_count": len(ledger_account.movements)
                })
        
        return summary
        
    except ReportGenerationError as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise_validation_error(f"Error generating accounts summary: {str(e)}")


# Endpoint para verificar integridad contable

@router.get(
    "/accounting-integrity",
    summary="Check Accounting Integrity",
    description="Verify accounting integrity and balance validation"
)
async def check_accounting_integrity(
    as_of_date: Optional[date] = Query(None, description="Check integrity as of date (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    Check accounting system integrity.
    
    Verifies:
    1. Balance Sheet equation (Assets = Liabilities + Equity)
    2. Trial Balance (Total Debits = Total Credits)
    3. Data consistency
    """
    try:
        report_date = as_of_date or date.today()
        
        service = ReportService(db)
        
        # Generar reportes para verificación
        balance_sheet = await service.generate_balance_sheet(report_date)
        trial_balance = await service.generate_trial_balance(report_date)
        
        # Verificar integridad
        integrity_checks = {
            "as_of_date": report_date.isoformat(),
            "balance_sheet_balanced": balance_sheet.is_balanced,
            "balance_sheet_equation": {
                "assets": float(balance_sheet.total_assets),
                "liabilities_equity": float(balance_sheet.total_liabilities_equity),
                "difference": float(balance_sheet.total_assets - balance_sheet.total_liabilities_equity)
            },
            "trial_balance_balanced": trial_balance.is_balanced,
            "trial_balance_totals": {
                "total_debits": float(trial_balance.total_debits),
                "total_credits": float(trial_balance.total_credits),
                "difference": float(trial_balance.total_debits - trial_balance.total_credits)
            },
            "overall_integrity": balance_sheet.is_balanced and trial_balance.is_balanced,
            "timestamp": datetime.now().isoformat()
        }
        
        return integrity_checks
        
    except ReportGenerationError as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise_validation_error(f"Error checking accounting integrity: {str(e)}")
