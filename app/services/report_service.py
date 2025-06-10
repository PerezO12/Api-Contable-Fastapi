"""
Servicio de Reportes Financieros - Versión Corregida
Siguiendo principios contables y mejores prácticas de FastAPI/SQLAlchemy async
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Tuple

from sqlalchemy import select, func, and_, desc, case, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account, AccountType, AccountCategory
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus
from app.schemas.reports import (
    BalanceSheet, BalanceSheetSection, BalanceSheetItem,
    IncomeStatement, IncomeStatementSection, IncomeStatementItem,
    TrialBalance, TrialBalanceItem,
    GeneralLedger, LedgerAccount, LedgerMovement,
    FinancialAnalysis, FinancialRatio
)
from app.utils.exceptions import ReportGenerationError, raise_validation_error


class AccountBalance:
    """Clase auxiliar para manejar balances de cuentas"""
    def __init__(
        self,
        account: Account,
        debit_total: Decimal = Decimal('0'),
        credit_total: Decimal = Decimal('0')
    ):
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


class ReportService:
    """
    Servicio para generar reportes financieros siguiendo principios contables
    Implementa los 3 reportes fundamentales: Balance General, Estado de Resultados, Balance de Comprobación
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.company_name = "Sistema Contable"  # Debería venir de configuración

    async def generate_balance_sheet(
        self, 
        as_of_date: date, 
        include_zero_balances: bool = False,
        company_name: Optional[str] = None
    ) -> BalanceSheet:
        """
        Generar Balance General a una fecha específica
        Ecuación contable: Activos = Pasivos + Patrimonio
        """
        try:
            # Obtener saldos de cuentas acumulados hasta la fecha
            account_balances = await self._get_account_balances_as_of_date(as_of_date)
            
            # Filtrar saldos cero si se requiere
            if not include_zero_balances:
                account_balances = [ab for ab in account_balances if ab.balance != 0]
            
            # Crear secciones del balance
            assets_section = self._create_balance_sheet_section(
                "ACTIVOS", 
                AccountType.ACTIVO, 
                account_balances
            )
            
            liabilities_section = self._create_balance_sheet_section(
                "PASIVOS", 
                AccountType.PASIVO, 
                account_balances
            )
            
            equity_section = self._create_balance_sheet_section(
                "PATRIMONIO", 
                AccountType.PATRIMONIO, 
                account_balances
            )
              # Verificar ecuación contable
            is_balanced = (assets_section.total == 
                          liabilities_section.total + equity_section.total)
            
            return BalanceSheet(
                report_date=as_of_date,
                company_name=company_name or self.company_name,
                assets=assets_section,
                liabilities=liabilities_section,
                equity=equity_section,
                total_assets=assets_section.total,
                total_liabilities_equity=liabilities_section.total + equity_section.total,
                is_balanced=is_balanced
            )
            
        except Exception as e:
            raise ReportGenerationError(
                report_type="balance_general",
                reason=f"Error generando Balance General: {str(e)}"
            )

    async def generate_income_statement(
        self,
        start_date: date,
        end_date: date,
        include_zero_balances: bool = False,
        company_name: Optional[str] = None
    ) -> IncomeStatement:
        """
        Generar Estado de Resultados para un período
        Fórmula: Utilidad Neta = Ingresos - Gastos
        """
        try:
            # Obtener movimientos del período
            account_balances = await self._get_account_balances_for_period(
                start_date, end_date
            )
            
            # Filtrar saldos cero si se requiere
            if not include_zero_balances:
                account_balances = [ab for ab in account_balances if ab.balance != 0]
            
            # Crear secciones del estado de resultados
            revenues_section = self._create_income_statement_section(
                "INGRESOS",
                AccountType.INGRESO,
                account_balances
            )
            
            expenses_section = self._create_income_statement_section(
                "GASTOS",
                AccountType.GASTO,
                account_balances
            )
            
            # Calcular utilidades
            gross_profit = revenues_section.total
            operating_profit = gross_profit - expenses_section.total
            net_profit = operating_profit  # Simplificado por ahora
            return IncomeStatement(
                start_date=start_date,
                end_date=end_date,
                company_name=company_name or self.company_name,
                revenues=revenues_section,
                expenses=expenses_section,
                gross_profit=gross_profit,
                operating_profit=operating_profit,
                net_profit=net_profit
            )
            
        except Exception as e:
            raise ReportGenerationError(
                report_type="income_statement",
                reason=f"Error generando Estado de Resultados: {str(e)}"
            )

    async def generate_trial_balance(
        self,
        as_of_date: date,
        include_zero_balances: bool = False,
        company_name: Optional[str] = None
    ) -> TrialBalance:
        """
        Generar Balance de Comprobación
        Verifica que Σ Débitos = Σ Créditos
        """
        try:
            account_balances = await self._get_account_balances_as_of_date(as_of_date)
            
            trial_balance_items = []
            total_debits = Decimal('0')
            total_credits = Decimal('0')
            
            for account_balance in account_balances:
                # Calcular balance de apertura (simplificado, debería venir de período anterior)
                opening_balance = Decimal('0')
                
                # Los movimientos son los totales de débitos y créditos
                debit_movements = account_balance.debit_total
                credit_movements = account_balance.credit_total
                
                # Balance de cierre
                closing_balance = account_balance.balance
                
                # Solo incluir si hay movimientos o balance no es cero
                if (include_zero_balances or 
                    debit_movements != 0 or credit_movements != 0 or closing_balance != 0):
                    
                    trial_balance_items.append(
                        TrialBalanceItem(
                            account_id=account_balance.account.id,
                            account_code=account_balance.account.code,
                            account_name=account_balance.account.name,
                            opening_balance=opening_balance,
                            debit_movements=debit_movements,
                            credit_movements=credit_movements,
                            closing_balance=closing_balance,
                            normal_balance_side=account_balance.account.normal_balance_side
                        )
                    )
                    total_debits += debit_movements
                    total_credits += credit_movements
            
            return TrialBalance(
                report_date=as_of_date,
                company_name=company_name or self.company_name,
                accounts=trial_balance_items,
                total_debits=total_debits,
                total_credits=total_credits,
                is_balanced=(total_debits == total_credits)
            )
            
        except Exception as e:
            raise ReportGenerationError(
                report_type="trial_balance",
                reason=f"Error generando Balance de Comprobación: {str(e)}"
            )

    async def generate_general_ledger(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[uuid.UUID] = None,
        account_type: Optional[AccountType] = None,
        company_name: Optional[str] = None
    ) -> GeneralLedger:
        """
        Generar Libro Mayor General
        Muestra todos los movimientos por cuenta en orden cronológico
        """
        try:
            # Query base para obtener movimientos
            query = (
                select(JournalEntryLine, JournalEntry, Account)
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .join(Account, JournalEntryLine.account_id == Account.id)
                .where(
                    and_(
                        JournalEntry.entry_date >= start_date,
                        JournalEntry.entry_date <= end_date,
                        JournalEntry.status == JournalEntryStatus.POSTED
                    )
                )
                .order_by(Account.code, JournalEntry.entry_date, JournalEntryLine.line_number)
            )
            
            # Aplicar filtros adicionales
            if account_id:
                query = query.where(Account.id == account_id)
            
            if account_type:
                query = query.where(Account.account_type == account_type)
            
            result = await self.db.execute(query)
            movements = result.all()
            
            # Agrupar por cuenta
            accounts_dict: Dict[uuid.UUID, Dict] = {}
            
            for line, entry, account in movements:
                if account.id not in accounts_dict:
                    accounts_dict[account.id] = {
                        'account': account,
                        'movements': [],
                        'total_debits': Decimal('0'),
                        'total_credits': Decimal('0')
                    }
                
                # Crear movimiento
                movement = LedgerMovement(
                    date=entry.entry_date,
                    journal_entry_number=entry.number,
                    description=line.description or entry.description,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    running_balance=Decimal('0'),  # Se calculará después
                    reference=entry.reference
                )
                
                accounts_dict[account.id]['movements'].append(movement)
                accounts_dict[account.id]['total_debits'] += line.debit_amount
                accounts_dict[account.id]['total_credits'] += line.credit_amount
            
            # Calcular balances corridos y crear objetos LedgerAccount
            ledger_accounts = []
            
            for account_data in accounts_dict.values():
                account = account_data['account']
                movements = account_data['movements']
                
                # Calcular balance de apertura (simplificado)
                opening_balance = Decimal('0')
                running_balance = opening_balance
                
                # Calcular balances corridos
                for movement in movements:
                    if account.normal_balance_side == "debit":
                        running_balance += movement.debit_amount - movement.credit_amount
                    else:
                        running_balance += movement.credit_amount - movement.debit_amount
                    
                    movement.running_balance = running_balance
                
                ledger_account = LedgerAccount(
                    account_id=account.id,
                    account_code=account.code,
                    account_name=account.name,
                    opening_balance=opening_balance,
                    movements=movements,
                    closing_balance=running_balance,
                    total_debits=account_data['total_debits'],
                    total_credits=account_data['total_credits']
                )
                
                ledger_accounts.append(ledger_account)
            return GeneralLedger(
                start_date=start_date,
                end_date=end_date,
                company_name=company_name or self.company_name,
                accounts=ledger_accounts
            )
            
        except Exception as e:
            raise ReportGenerationError(
                report_type="general_ledger",
                reason=f"Error generando Libro Mayor: {str(e)}"
            )

    async def generate_financial_analysis(
        self,
        as_of_date: date,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> FinancialAnalysis:
        """
        Generar análisis financiero con ratios principales
        """
        try:
            # Balance General
            balance_sheet = await self.generate_balance_sheet(as_of_date)
            
            # Estado de Resultados (si se proporcionan fechas)
            income_statement = None
            if start_date and end_date:
                income_statement = await self.generate_income_statement(start_date, end_date)
            
            # Calcular ratios
            liquidity_ratios = self._calculate_liquidity_ratios(balance_sheet)
            profitability_ratios = self._calculate_profitability_ratios(
                balance_sheet, income_statement
            )
            leverage_ratios = self._calculate_leverage_ratios(balance_sheet)
            efficiency_ratios = self._calculate_efficiency_ratios(
                balance_sheet, income_statement
            )
            return FinancialAnalysis(
                report_date=as_of_date,
                liquidity_ratios=liquidity_ratios,
                profitability_ratios=profitability_ratios,
                leverage_ratios=leverage_ratios,
                efficiency_ratios=efficiency_ratios
            )
            
        except Exception as e:
            raise ReportGenerationError(
                report_type="financial_analysis",
                reason=f"Error generando análisis financiero: {str(e)}"
            )

    # Métodos auxiliares privados
    
    async def _get_account_balances_as_of_date(
        self, 
        as_of_date: date
    ) -> List[AccountBalance]:
        """Obtener saldos acumulados de todas las cuentas hasta una fecha"""
        
        # Subquery para totales de movimientos
        movements_subquery = (
            select(
                JournalEntryLine.account_id,
                func.coalesce(func.sum(JournalEntryLine.debit_amount), 0).label('total_debits'),
                func.coalesce(func.sum(JournalEntryLine.credit_amount), 0).label('total_credits')
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(
                and_(
                    JournalEntry.entry_date <= as_of_date,
                    JournalEntry.status == JournalEntryStatus.POSTED
                )
            )
            .group_by(JournalEntryLine.account_id)
            .subquery()
        )
        
        # Query principal con todas las cuentas
        query = (
            select(Account, movements_subquery.c.total_debits, movements_subquery.c.total_credits)
            .outerjoin(movements_subquery, Account.id == movements_subquery.c.account_id)
            .order_by(Account.code)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        account_balances = []
        for account, total_debits, total_credits in rows:
            debit_total = Decimal(str(total_debits or 0))
            credit_total = Decimal(str(total_credits or 0))
            
            account_balances.append(
                AccountBalance(account, debit_total, credit_total)
            )
        
        return account_balances

    async def _get_account_balances_for_period(
        self,
        start_date: date,
        end_date: date
    ) -> List[AccountBalance]:
        """Obtener movimientos de cuentas en un período específico"""
        
        # Similar al método anterior pero para un período
        movements_subquery = (
            select(
                JournalEntryLine.account_id,
                func.coalesce(func.sum(JournalEntryLine.debit_amount), 0).label('total_debits'),
                func.coalesce(func.sum(JournalEntryLine.credit_amount), 0).label('total_credits')
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(
                and_(
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                    JournalEntry.status == JournalEntryStatus.POSTED
                )
            )
            .group_by(JournalEntryLine.account_id)
            .subquery()
        )
        
        query = (
            select(Account, movements_subquery.c.total_debits, movements_subquery.c.total_credits)
            .join(movements_subquery, Account.id == movements_subquery.c.account_id)
            .order_by(Account.code)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        account_balances = []
        for account, total_debits, total_credits in rows:
            debit_total = Decimal(str(total_debits or 0))
            credit_total = Decimal(str(total_credits or 0))
            
            account_balances.append(
                AccountBalance(account, debit_total, credit_total)
            )
        
        return account_balances

    def _create_balance_sheet_section(
        self,
        section_name: str,
        account_type: AccountType,
        account_balances: List[AccountBalance]
    ) -> BalanceSheetSection:
        """Crear una sección del balance general"""
        
        filtered_balances = [
            ab for ab in account_balances 
            if ab.account.account_type == account_type
        ]
        
        items = []
        total = Decimal('0')
        
        for account_balance in filtered_balances:
            item = BalanceSheetItem(
                account_id=account_balance.account.id,
                account_code=account_balance.account.code,
                account_name=account_balance.account.name,
                balance=abs(account_balance.balance),  # Mostrar valores positivos
                level=account_balance.account.level or 1,
                children=[]  # TODO: Implementar jerarquía
            )
            items.append(item)
            total += abs(account_balance.balance)
        
        return BalanceSheetSection(
            section_name=section_name,
            account_type=account_type,
            items=items,
            total=total
        )

    def _create_income_statement_section(
        self,
        section_name: str,
        account_type: AccountType,
        account_balances: List[AccountBalance]
    ) -> IncomeStatementSection:
        """Crear una sección del estado de resultados"""
        
        filtered_balances = [
            ab for ab in account_balances 
            if ab.account.account_type == account_type
        ]
        
        items = []
        total = Decimal('0')
        
        for account_balance in filtered_balances:
            # Para ingresos, mostrar el valor absoluto del balance (que será negativo)
            # Para gastos, mostrar el valor absoluto
            amount = abs(account_balance.balance)
            
            item = IncomeStatementItem(
                account_id=account_balance.account.id,
                account_code=account_balance.account.code,
                account_name=account_balance.account.name,
                amount=amount,
                level=account_balance.account.level or 1
            )
            items.append(item)
            total += amount
        
        return IncomeStatementSection(
            section_name=section_name,
            items=items,
            total=total
        )

    def _calculate_liquidity_ratios(self, balance_sheet: BalanceSheet) -> List[FinancialRatio]:
        """Calcular ratios de liquidez"""
        ratios = []
        
        # Obtener activos y pasivos corrientes
        current_assets = sum(
            item.balance for item in balance_sheet.assets.items
            # TODO: Filtrar por categoría CORRIENTE cuando esté implementada
        )
        
        current_liabilities = sum(
            item.balance for item in balance_sheet.liabilities.items
            # TODO: Filtrar por categoría CORRIENTE cuando esté implementada
        )
          # Ratio corriente
        if current_liabilities > 0:
            current_ratio = Decimal(str(current_assets / current_liabilities))
            ratios.append(FinancialRatio(
                name="Razón Corriente",
                value=current_ratio,
                description="Activos Corrientes / Pasivos Corrientes",
                interpretation=self._interpret_current_ratio(current_ratio)
            ))
        
        return ratios

    def _calculate_profitability_ratios(
        self, 
        balance_sheet: BalanceSheet, 
        income_statement: Optional[IncomeStatement]
    ) -> List[FinancialRatio]:
        """Calcular ratios de rentabilidad"""
        ratios = []
        
        if income_statement is None:
            return ratios
        
        # Margen de utilidad neta
        if income_statement.revenues.total > 0:
            net_margin = (income_statement.net_profit / income_statement.revenues.total) * 100
            ratios.append(FinancialRatio(
                name="Margen de Utilidad Neta",
                value=net_margin,
                description="(Utilidad Neta / Ingresos Totales) × 100",
                interpretation=self._interpret_net_margin(net_margin)
            ))
        
        return ratios

    def _calculate_leverage_ratios(self, balance_sheet: BalanceSheet) -> List[FinancialRatio]:
        """Calcular ratios de apalancamiento"""
        ratios = []
        
        # Ratio de endeudamiento
        if balance_sheet.total_assets > 0:
            debt_ratio = (balance_sheet.liabilities.total / balance_sheet.total_assets) * 100
            ratios.append(FinancialRatio(
                name="Ratio de Endeudamiento",
                value=debt_ratio,
                description="(Total Pasivos / Total Activos) × 100",
                interpretation=self._interpret_debt_ratio(debt_ratio)
            ))
        
        return ratios

    def _calculate_efficiency_ratios(
        self, 
        balance_sheet: BalanceSheet, 
        income_statement: Optional[IncomeStatement]
    ) -> List[FinancialRatio]:
        """Calcular ratios de eficiencia"""
        ratios = []
        
        if income_statement is None:
            return ratios
        
        # ROA - Return on Assets
        if balance_sheet.total_assets > 0:
            roa = (income_statement.net_profit / balance_sheet.total_assets) * 100
            ratios.append(FinancialRatio(
                name="Rentabilidad sobre Activos (ROA)",
                value=roa,
                description="(Utilidad Neta / Total Activos) × 100",
                interpretation=self._interpret_roa(roa)
            ))
        
        return ratios

    # Métodos de interpretación de ratios
    
    def _interpret_current_ratio(self, ratio: Decimal) -> str:
        """Interpretar ratio corriente"""
        if ratio >= 2:
            return "Excelente liquidez"
        elif ratio >= 1.5:
            return "Buena liquidez"
        elif ratio >= 1:
            return "Liquidez aceptable"
        else:
            return "Problemas de liquidez"

    def _interpret_net_margin(self, margin: Decimal) -> str:
        """Interpretar margen de utilidad neta"""
        if margin >= 20:
            return "Excelente rentabilidad"
        elif margin >= 10:
            return "Buena rentabilidad"
        elif margin >= 5:
            return "Rentabilidad aceptable"
        elif margin >= 0:
            return "Rentabilidad baja"
        else:
            return "Pérdidas"

    def _interpret_debt_ratio(self, ratio: Decimal) -> str:
        """Interpretar ratio de endeudamiento"""
        if ratio <= 30:
            return "Bajo endeudamiento"
        elif ratio <= 50:
            return "Endeudamiento moderado"
        elif ratio <= 70:
            return "Endeudamiento alto"
        else:
            return "Endeudamiento muy alto"

    def _interpret_roa(self, roa: Decimal) -> str:
        """Interpretar ROA"""
        if roa >= 15:
            return "Excelente eficiencia"
        elif roa >= 10:
            return "Buena eficiencia"
        elif roa >= 5:
            return "Eficiencia aceptable"
        elif roa >= 0:
            return "Baja eficiencia"
        else:
            return "Ineficiencia"
