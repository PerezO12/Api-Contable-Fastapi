"""
Servicio especializado para generar Estados de Flujo de Efectivo correctos
según estándares contables internacionales
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict
from enum import Enum

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account, AccountType, CashFlowCategory
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus
from app.schemas.reports import (
    CashFlowStatement, CashFlowItem, OperatingCashFlow
)
from app.utils.exceptions import ReportGenerationError


class CashFlowMethod(str, Enum):
    """Métodos de cálculo del flujo de efectivo"""
    DIRECT = "direct"      # Método directo: cobros y pagos
    INDIRECT = "indirect"  # Método indirecto: utilidad neta + ajustes


class CashFlowService:
    """Servicio especializado para generar Estados de Flujo de Efectivo correctos"""
    
    def __init__(self, db: AsyncSession, company_name: str = "Empresa"):
        self.db = db
        self.company_name = company_name

    async def generate_cash_flow_statement(
        self,
        start_date: date,
        end_date: date,
        method: CashFlowMethod = CashFlowMethod.INDIRECT,
        company_name: Optional[str] = None
    ) -> CashFlowStatement:
        """
        Generar Estado de Flujo de Efectivo según estándares contables
        
        Args:
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período  
            method: Método de cálculo (directo o indirecto)
            company_name: Nombre de la empresa
            
        Returns:
            CashFlowStatement: Estado de flujo de efectivo completo
        """
        try:
            # 1. Calcular efectivo inicial y final
            cash_beginning = await self._get_cash_balance_at_date(start_date - timedelta(days=1))
            cash_ending = await self._get_cash_balance_at_date(end_date)
            
            # 2. Calcular flujos por actividad
            operating_flow = await self._calculate_operating_cash_flow(
                start_date, end_date, method
            )
            
            investing_activities = await self._calculate_investing_cash_flow(
                start_date, end_date
            )
            
            financing_activities = await self._calculate_financing_cash_flow(
                start_date, end_date
            )
              # 3. Calcular totales netos
            net_cash_from_operating = operating_flow.net_operating_cash_flow
            net_cash_from_investing = sum((item.amount for item in investing_activities), Decimal('0'))
            net_cash_from_financing = sum((item.amount for item in financing_activities), Decimal('0'))
            
            # 4. Verificar cuadre
            net_change_in_cash = (
                net_cash_from_operating + 
                net_cash_from_investing + 
                net_cash_from_financing
            )
            
            calculated_ending_cash = cash_beginning + net_change_in_cash
            is_balanced = abs(calculated_ending_cash - cash_ending) < Decimal('0.01')
            
            return CashFlowStatement(
                report_date=end_date,
                start_date=start_date,
                end_date=end_date,
                company_name=company_name or self.company_name,
                method=method.value,
                
                # Efectivo inicial
                cash_beginning_period=cash_beginning,
                
                # Actividades de Operación
                operating_activities=operating_flow,
                net_cash_from_operating=net_cash_from_operating,
                
                # Actividades de Inversión
                investing_activities=investing_activities,
                net_cash_from_investing=net_cash_from_investing,
                
                # Actividades de Financiamiento
                financing_activities=financing_activities,
                net_cash_from_financing=net_cash_from_financing,
                
                # Efectivo final
                net_change_in_cash=net_change_in_cash,
                cash_ending_period=cash_ending,
                
                # Validación
                is_balanced=is_balanced
            )
            
        except Exception as e:
            raise ReportGenerationError(
                report_type="cash_flow_statement",
                reason=f"Error generando flujo de efectivo: {str(e)}"
            )

    async def _get_cash_balance_at_date(self, as_of_date: date) -> Decimal:
        """Obtener balance de efectivo y equivalentes a una fecha específica"""
        query = (
            select(Account)
            .where(
                and_(
                    Account.cash_flow_category == CashFlowCategory.CASH_EQUIVALENTS,
                    Account.is_active == True
                )
            )
        )
        
        result = await self.db.execute(query)
        cash_accounts = result.scalars().all()
        
        total_cash = Decimal('0')
        
        for account in cash_accounts:
            # Obtener movimientos hasta la fecha
            movements_query = (
                select(JournalEntryLine, JournalEntry)
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    and_(
                        JournalEntryLine.account_id == account.id,
                        JournalEntry.entry_date <= as_of_date,
                        JournalEntry.status == JournalEntryStatus.POSTED
                    )
                )
            )
            
            movements_result = await self.db.execute(movements_query)
            movements = movements_result.all()
            
            # Calcular balance acumulado
            account_balance = Decimal('0')
            for line, entry in movements:
                if account.normal_balance_side == "debit":
                    account_balance += line.debit_amount - line.credit_amount
                else:
                    account_balance += line.credit_amount - line.debit_amount
            
            total_cash += account_balance
        
        return total_cash

    async def _calculate_operating_cash_flow(
        self, 
        start_date: date, 
        end_date: date, 
        method: CashFlowMethod
    ) -> OperatingCashFlow:
        """Calcular flujos de actividades de operación"""
        
        if method == CashFlowMethod.INDIRECT:
            return await self._calculate_operating_indirect(start_date, end_date)
        else:
            return await self._calculate_operating_direct(start_date, end_date)

    async def _calculate_operating_indirect(
        self, 
        start_date: date, 
        end_date: date
    ) -> OperatingCashFlow:
        """Método Indirecto: Utilidad Neta + Ajustes"""
        
        # 1. Obtener utilidad neta del período
        net_income = await self._get_net_income(start_date, end_date)
        
        # 2. Obtener ajustes para partidas que no son efectivo
        adjustments = await self._get_operating_adjustments(start_date, end_date)
        
        # 3. Cambios en capital de trabajo
        working_capital_changes = await self._get_working_capital_changes(
            start_date, end_date
        )
        
        items = [
            CashFlowItem(
                description="Utilidad (Pérdida) Neta",
                amount=net_income,
                account_code="",
                account_name="Estado de Resultados"
            )
        ]
        
        # Agregar ajustes
        items.extend(adjustments)
          # Agregar cambios en capital de trabajo
        items.extend(working_capital_changes)
        
        net_operating_cash_flow = sum((item.amount for item in items), Decimal('0'))
        
        return OperatingCashFlow(
            method="indirect",
            net_income=net_income,
            adjustments=adjustments,
            working_capital_changes=working_capital_changes,
            items=items,
            net_operating_cash_flow=net_operating_cash_flow
        )

    async def _calculate_operating_direct(
        self, 
        start_date: date, 
        end_date: date
    ) -> OperatingCashFlow:
        """Método Directo: Cobros - Pagos operativos"""
        
        # Obtener movimientos de cuentas operativas
        operating_flows = await self._get_direct_operating_flows(start_date, end_date)
        
        items = []
        for flow in operating_flows:        items.append(CashFlowItem(
                description=flow['description'],
                amount=flow['amount'],
                account_code=flow['account_code'],
                account_name=flow['account_name']
            ))
        
        net_operating_cash_flow = sum((item.amount for item in items), Decimal('0'))
        
        return OperatingCashFlow(
            method="direct",
            net_income=Decimal('0'),  # No aplica en método directo
            adjustments=[],
            working_capital_changes=[],
            items=items,
            net_operating_cash_flow=net_operating_cash_flow
        )

    async def _calculate_investing_cash_flow(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[CashFlowItem]:
        """Calcular flujos de actividades de inversión"""
        
        investing_accounts = await self._get_accounts_by_cash_flow_category(
            CashFlowCategory.INVESTING
        )
        
        items = []
        for account in investing_accounts:
            net_movement = await self._calculate_account_net_movement(
                account, start_date, end_date
            )
            
            if net_movement != 0:
                # Para actividades de inversión, las compras son salidas (-)
                # y las ventas son entradas (+)
                cash_flow_amount = -net_movement if account.account_type == AccountType.ACTIVO else net_movement
                
                items.append(CashFlowItem(
                    description=f"{'Adquisición' if cash_flow_amount < 0 else 'Venta'} de {account.name}",
                    amount=cash_flow_amount,
                    account_code=account.code,
                    account_name=account.name
                ))
        
        return items

    async def _calculate_financing_cash_flow(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[CashFlowItem]:
        """Calcular flujos de actividades de financiamiento"""
        
        financing_accounts = await self._get_accounts_by_cash_flow_category(
            CashFlowCategory.FINANCING
        )
        
        items = []
        for account in financing_accounts:
            net_movement = await self._calculate_account_net_movement(
                account, start_date, end_date
            )
            
            if net_movement != 0:
                # Para financiamiento, aumentos de deuda/capital son entradas (+)
                # y pagos de deuda/dividendos son salidas (-)
                cash_flow_amount = net_movement
                
                description = self._get_financing_description(account, cash_flow_amount)
                
                items.append(CashFlowItem(
                    description=description,
                    amount=cash_flow_amount,
                    account_code=account.code,
                    account_name=account.name
                ))
        
        return items

    async def _get_net_income(self, start_date: date, end_date: date) -> Decimal:
        """Obtener utilidad neta del período"""
        
        # Obtener ingresos
        revenues_query = (
            select(JournalEntryLine, JournalEntry, Account)
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(Account, JournalEntryLine.account_id == Account.id)
            .where(
                and_(
                    Account.account_type == AccountType.INGRESO,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                    JournalEntry.status == JournalEntryStatus.POSTED
                )
            )
        )
        
        revenues_result = await self.db.execute(revenues_query)
        revenues_movements = revenues_result.all()
        
        total_revenues = Decimal('0')
        for line, entry, account in revenues_movements:
            total_revenues += line.credit_amount - line.debit_amount
        
        # Obtener gastos
        expenses_query = (
            select(JournalEntryLine, JournalEntry, Account)
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(Account, JournalEntryLine.account_id == Account.id)
            .where(
                and_(
                    Account.account_type.in_([AccountType.GASTO, AccountType.COSTOS]),                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                    JournalEntry.status == JournalEntryStatus.POSTED
                )
            )
        )
        
        expenses_result = await self.db.execute(expenses_query)
        expenses_movements = expenses_result.all()
        
        total_expenses = Decimal('0')
        for line, entry, account in expenses_movements:
            total_expenses += line.debit_amount - line.credit_amount
        
        return total_revenues - total_expenses

    async def _get_operating_adjustments(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[CashFlowItem]:
        """Obtener ajustes operativos para flujo de caja método indirecto"""
        # TODO: Implementar ajustes específicos como:
        # - Depreciación y amortización
        # - Provisiones
        # - Pérdidas/ganancias en venta de activos
        # - Otros ajustes por partidas no monetarias
        
        # Por ahora, retornar lista vacía
        return []

    async def _get_working_capital_changes(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[CashFlowItem]:
        """Calcular cambios en capital de trabajo"""
        # TODO: Implementar cambios en capital de trabajo:
        # - Cambios en cuentas por cobrar
        # - Cambios en inventarios  
        # - Cambios en cuentas por pagar        # - Otros cambios en activos y pasivos operativos
        
        # Por ahora, retornar lista vacía
        return []

    async def _get_direct_operating_flows(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Dict]:
        """Obtener flujos operativos directos (cobros y pagos)"""        
        flows = []
        
        # Obtener movimientos de cuentas operativas
        # TODO: Implementar flujos directos específicos
        
        return flows

    async def _get_accounts_by_cash_flow_category(
        self, 
        category: CashFlowCategory
    ) -> List[Account]:
        """Obtener cuentas por categoría de flujo de efectivo"""
        
        query = (
            select(Account)
            .where(
                and_(
                    Account.cash_flow_category == category,
                    Account.is_active == True
                )
            )
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _calculate_account_net_movement(
        self, 
        account: Account, 
        start_date: date, 
        end_date: date
    ) -> Decimal:
        """Calcular movimiento neto de una cuenta en un período"""
        
        query = (
            select(JournalEntryLine, JournalEntry)
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(
                and_(
                    JournalEntryLine.account_id == account.id,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                    JournalEntry.status == JournalEntryStatus.POSTED
                )
            )
        )
        
        result = await self.db.execute(query)
        movements = result.all()
        
        net_movement = Decimal('0')
        for line, entry in movements:
            net_movement += line.debit_amount - line.credit_amount
        
        return net_movement

    def _get_financing_description(self, account: Account, amount: Decimal) -> str:
        """Generar descripción apropiada para actividades de financiamiento"""
        
        if account.account_type == AccountType.PASIVO:
            if amount > 0:
                return f"Obtención de {account.name}"
            else:
                return f"Pago de {account.name}"
        elif account.account_type == AccountType.PATRIMONIO:
            if amount > 0:
                return f"Aporte por {account.name}"
            else:
                return f"Distribución por {account.name}"
        else:
            return f"Movimiento en {account.name}"
