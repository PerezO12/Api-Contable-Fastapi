import pytest
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cash_flow_service import CashFlowService, CashFlowMethod
from app.models.account import Account, AccountType, CashFlowCategory
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus
from app.schemas.reports import CashFlowStatement, OperatingCashFlow


class TestCashFlowService:
    """
    Test suite para CashFlowService
    Sprint 1 - Corrección del sistema de flujo de efectivo
    """

    async def test_cash_flow_service_initialization(self, db_session: AsyncSession):
        """Test de inicialización del servicio"""
        service = CashFlowService(db_session, "Test Company")
        assert service.db == db_session
        assert service.company_name == "Test Company"

    async def test_generate_cash_flow_statement_indirect_method(self, db_session: AsyncSession):
        """Test de generación de flujo de efectivo método indirecto"""
        # Configurar datos de prueba
        await self._setup_test_accounts_and_entries(db_session)
        
        service = CashFlowService(db_session, "Test Company")
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        
        # Generar estado de flujo de efectivo
        cash_flow = await service.generate_cash_flow_statement(
            start_date=start_date,
            end_date=end_date,
            method=CashFlowMethod.INDIRECT,
            company_name="Test Company"
        )
        
        # Verificar estructura del estado
        assert isinstance(cash_flow, CashFlowStatement)
        assert cash_flow.method == "indirect"
        assert cash_flow.start_date == start_date
        assert cash_flow.end_date == end_date
        assert cash_flow.company_name == "Test Company"
        
        # Verificar que tiene todas las secciones
        assert cash_flow.operating_activities is not None
        assert cash_flow.investing_activities is not None
        assert cash_flow.financing_activities is not None
        
        # Verificar cálculos básicos
        assert isinstance(cash_flow.cash_beginning_period, Decimal)
        assert isinstance(cash_flow.cash_ending_period, Decimal)
        assert isinstance(cash_flow.net_change_in_cash, Decimal)

    async def test_generate_cash_flow_statement_direct_method(self, db_session: AsyncSession):
        """Test de generación de flujo de efectivo método directo"""
        # Configurar datos de prueba
        await self._setup_test_accounts_and_entries(db_session)
        
        service = CashFlowService(db_session, "Test Company")
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        
        # Generar estado de flujo de efectivo
        cash_flow = await service.generate_cash_flow_statement(
            start_date=start_date,
            end_date=end_date,
            method=CashFlowMethod.DIRECT,
            company_name="Test Company"
        )
        
        # Verificar método
        assert cash_flow.method == "direct"
        assert cash_flow.operating_activities.method == "direct"
        assert cash_flow.operating_activities.net_income == Decimal('0')  # No aplica en método directo

    async def test_cash_balance_calculation(self, db_session: AsyncSession):
        """Test de cálculo de balance de efectivo"""        # Crear cuenta de efectivo
        cash_account = Account(
            code="1001",
            name="Caja",
            account_type=AccountType.ACTIVO,
            cash_flow_category=CashFlowCategory.CASH_EQUIVALENTS,
            is_active=True
        )
        db_session.add(cash_account)
        await db_session.flush()
          # Crear movimientos de efectivo
        entry_date = date(2025, 1, 15)
        journal_entry = JournalEntry(
            number="JE-001",
            entry_date=entry_date,
            description="Entrada de efectivo",
            status=JournalEntryStatus.POSTED
        )
        db_session.add(journal_entry)
        await db_session.flush()
        
        # Línea de débito en efectivo
        line = JournalEntryLine(
            journal_entry_id=journal_entry.id,
            account_id=cash_account.id,
            debit_amount=Decimal('1000.00'),
            credit_amount=Decimal('0.00'),
            description="Entrada de efectivo"
        )
        db_session.add(line)
        await db_session.commit()
        
        service = CashFlowService(db_session, "Test Company")
        
        # Probar balance antes del movimiento
        balance_before = await service._get_cash_balance_at_date(entry_date - timedelta(days=1))
        assert balance_before == Decimal('0.00')
        
        # Probar balance después del movimiento
        balance_after = await service._get_cash_balance_at_date(entry_date)
        assert balance_after == Decimal('1000.00')

    async def test_operating_cash_flow_indirect(self, db_session: AsyncSession):
        """Test de flujo operativo método indirecto"""        # Configurar cuentas de ingresos y gastos
        revenue_account = Account(
            code="4001",
            name="Ingresos por ventas",
            account_type=AccountType.INGRESO,
            cash_flow_category=CashFlowCategory.OPERATING,
            is_active=True
        )
        
        expense_account = Account(
            code="5001",
            name="Gastos operativos",
            account_type=AccountType.GASTO,
            cash_flow_category=CashFlowCategory.OPERATING,
            is_active=True
        )
        
        db_session.add_all([revenue_account, expense_account])
        await db_session.flush()
        
        # Crear asientos para generar utilidad neta
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
          # Asiento de ingresos
        revenue_entry = JournalEntry(
            number="JE-002",
            entry_date=date(2025, 1, 15),
            description="Venta de productos",
            status=JournalEntryStatus.POSTED
        )
        db_session.add(revenue_entry)
        await db_session.flush()
        
        revenue_line = JournalEntryLine(
            journal_entry_id=revenue_entry.id,
            account_id=revenue_account.id,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('5000.00'),
            description="Ingresos por ventas"
        )
        db_session.add(revenue_line)
          # Asiento de gastos
        expense_entry = JournalEntry(
            number="JE-003",
            entry_date=date(2025, 1, 20),
            description="Gastos operativos",
            status=JournalEntryStatus.POSTED
        )
        db_session.add(expense_entry)
        await db_session.flush()
        
        expense_line = JournalEntryLine(
            journal_entry_id=expense_entry.id,
            account_id=expense_account.id,
            debit_amount=Decimal('2000.00'),
            credit_amount=Decimal('0.00'),
            description="Gastos del período"
        )
        db_session.add(expense_line)
        await db_session.commit()
        
        service = CashFlowService(db_session, "Test Company")
        
        # Probar cálculo de utilidad neta
        net_income = await service._get_net_income(start_date, end_date)
        assert net_income == Decimal('3000.00')  # 5000 - 2000
        
        # Probar flujo operativo indirecto
        operating_flow = await service._calculate_operating_indirect(start_date, end_date)
        assert operating_flow.method == "indirect"
        assert operating_flow.net_income == Decimal('3000.00')

    async def test_investing_cash_flow(self, db_session: AsyncSession):
        """Test de flujo de actividades de inversión"""        # Crear cuenta de activo fijo
        equipment_account = Account(
            code="1401",
            name="Equipo de oficina",
            account_type=AccountType.ACTIVO,
            cash_flow_category=CashFlowCategory.INVESTING,
            is_active=True
        )
        db_session.add(equipment_account)
        await db_session.flush()
          # Crear movimiento de inversión
        investment_entry = JournalEntry(
            number="JE-004",
            entry_date=date(2025, 1, 10),
            description="Compra de equipo",
            status=JournalEntryStatus.POSTED
        )
        db_session.add(investment_entry)
        await db_session.flush()
        
        investment_line = JournalEntryLine(
            journal_entry_id=investment_entry.id,
            account_id=equipment_account.id,
            debit_amount=Decimal('10000.00'),
            credit_amount=Decimal('0.00'),
            description="Compra de equipo"
        )
        db_session.add(investment_line)
        await db_session.commit()
        
        service = CashFlowService(db_session, "Test Company")
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        
        # Probar flujo de inversión
        investing_flows = await service._calculate_investing_cash_flow(start_date, end_date)
        assert len(investing_flows) == 1
        assert investing_flows[0].amount == Decimal('-10000.00')  # Compra es salida de efectivo
        assert "Adquisición" in investing_flows[0].description

    async def test_financing_cash_flow(self, db_session: AsyncSession):
        """Test de flujo de actividades de financiamiento"""        # Crear cuenta de capital
        capital_account = Account(
            code="3001",
            name="Capital social",
            account_type=AccountType.PATRIMONIO,
            cash_flow_category=CashFlowCategory.FINANCING,
            is_active=True
        )
        db_session.add(capital_account)
        await db_session.flush()
          # Crear movimiento de financiamiento
        capital_entry = JournalEntry(
            number="JE-005",
            entry_date=date(2025, 1, 5),
            description="Aporte de capital",
            status=JournalEntryStatus.POSTED
        )
        db_session.add(capital_entry)
        await db_session.flush()
        
        capital_line = JournalEntryLine(
            journal_entry_id=capital_entry.id,
            account_id=capital_account.id,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('50000.00'),
            description="Aporte de socios"
        )
        db_session.add(capital_line)
        await db_session.commit()
        
        service = CashFlowService(db_session, "Test Company")
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        
        # Probar flujo de financiamiento
        financing_flows = await service._calculate_financing_cash_flow(start_date, end_date)
        assert len(financing_flows) == 1
        assert financing_flows[0].amount == Decimal('-50000.00')  # Crédito en patrimonio
        assert "Aporte" in financing_flows[0].description

    async def test_cash_flow_balance_validation(self, db_session: AsyncSession):
        """Test de validación del balance del flujo de efectivo"""
        await self._setup_test_accounts_and_entries(db_session)
        
        service = CashFlowService(db_session, "Test Company")
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        
        cash_flow = await service.generate_cash_flow_statement(
            start_date=start_date,
            end_date=end_date,
            method=CashFlowMethod.INDIRECT
        )
        
        # Verificar que el cambio neto coincide con la diferencia de efectivo
        expected_change = cash_flow.cash_ending_period - cash_flow.cash_beginning_period
        assert abs(cash_flow.net_change_in_cash - expected_change) < Decimal('0.01')
        
        # Verificar que la suma de flujos coincide con el cambio neto
        total_flows = (
            cash_flow.net_cash_from_operating +
            cash_flow.net_cash_from_investing +
            cash_flow.net_cash_from_financing
        )
        assert abs(total_flows - cash_flow.net_change_in_cash) < Decimal('0.01')

    async def _setup_test_accounts_and_entries(self, db_session: AsyncSession):
        """Configurar cuentas y asientos de prueba para los tests"""        # Cuenta de efectivo
        cash_account = Account(
            code="1001",
            name="Caja",
            account_type=AccountType.ACTIVO,
            cash_flow_category=CashFlowCategory.CASH_EQUIVALENTS,
            is_active=True
        )
        
        # Cuenta de ingresos
        revenue_account = Account(
            code="4001",
            name="Ingresos por ventas",
            account_type=AccountType.INGRESO,
            cash_flow_category=CashFlowCategory.OPERATING,
            is_active=True
        )
        
        # Cuenta de gastos
        expense_account = Account(
            code="5001",
            name="Gastos operativos",
            account_type=AccountType.GASTO,
            cash_flow_category=CashFlowCategory.OPERATING,
            is_active=True
        )
        
        # Cuenta de activo fijo
        equipment_account = Account(
            code="1401",
            name="Equipo de oficina",
            account_type=AccountType.ACTIVO,
            cash_flow_category=CashFlowCategory.INVESTING,
            is_active=True
        )
        
        # Cuenta de capital
        capital_account = Account(
            code="3001",
            name="Capital social",
            account_type=AccountType.PATRIMONIO,
            cash_flow_category=CashFlowCategory.FINANCING,
            is_active=True
        )
        
        db_session.add_all([
            cash_account, revenue_account, expense_account, 
            equipment_account, capital_account
        ])
        await db_session.flush()
        
        # Crear algunos asientos básicos
        start_date = date(2025, 1, 1)
          # Asiento inicial de capital
        capital_entry = JournalEntry(
            number="JE-100",
            entry_date=start_date,
            description="Capital inicial",
            status=JournalEntryStatus.POSTED
        )
        db_session.add(capital_entry)
        await db_session.flush()
        
        # Líneas del asiento de capital
        capital_line_debit = JournalEntryLine(
            journal_entry_id=capital_entry.id,
            account_id=cash_account.id,
            debit_amount=Decimal('100000.00'),
            credit_amount=Decimal('0.00'),
            description="Efectivo inicial"
        )
        
        capital_line_credit = JournalEntryLine(
            journal_entry_id=capital_entry.id,
            account_id=capital_account.id,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('100000.00'),
            description="Capital inicial"
        )
        
        db_session.add_all([capital_line_debit, capital_line_credit])
          # Asiento de venta
        sales_entry = JournalEntry(
            number="JE-101",
            entry_date=date(2025, 1, 15),
            description="Venta de productos",
            status=JournalEntryStatus.POSTED
        )
        db_session.add(sales_entry)
        await db_session.flush()
        
        sales_line_debit = JournalEntryLine(
            journal_entry_id=sales_entry.id,
            account_id=cash_account.id,
            debit_amount=Decimal('15000.00'),
            credit_amount=Decimal('0.00'),
            description="Cobro de ventas"
        )
        
        sales_line_credit = JournalEntryLine(
            journal_entry_id=sales_entry.id,
            account_id=revenue_account.id,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('15000.00'),
            description="Ingresos por ventas"
        )
        
        db_session.add_all([sales_line_debit, sales_line_credit])
          # Asiento de gasto
        expense_entry = JournalEntry(
            number="JE-102",
            entry_date=date(2025, 1, 20),
            description="Gastos operativos",
            status=JournalEntryStatus.POSTED
        )
        db_session.add(expense_entry)
        await db_session.flush()
        
        expense_line_debit = JournalEntryLine(
            journal_entry_id=expense_entry.id,
            account_id=expense_account.id,
            debit_amount=Decimal('5000.00'),
            credit_amount=Decimal('0.00'),
            description="Gastos del período"
        )
        
        expense_line_credit = JournalEntryLine(
            journal_entry_id=expense_entry.id,
            account_id=cash_account.id,
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('5000.00'),
            description="Pago de gastos"
        )
        
        db_session.add_all([expense_line_debit, expense_line_credit])
        
        await db_session.commit()
