"""
API endpoints para reportes financieros
Implementa endpoints individuales por tipo de reporte usando        )
        
        table_data = self._convert_cash_flow_to_table(cash_ledger, detail_level)
        narrative_data = self._generate_cash_flow_narrative(cash_ledger, from_date, to_date, original_to_date)
        
        date_range = DateRange(**{"from": from_date, "to": to_date})
        return ReportResponse(
            success=True,
            report_type=ReportType.FLUJO_EFECTIVO,
            generated_at=date.today(),
            period=date_range,
            project_context=resolved_context,
            table=table_data,
            narrative=narrative_data
        )rs
"""
from datetime import date
from decimal import Decimal
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.account import AccountType
from app.services.report_service import ReportService
from app.services.company_service import CompanyService
from app.services.cash_flow_service import CashFlowService, CashFlowMethod
from app.schemas.report_api import (
    ReportResponse, ReportError, ReportType, DetailLevel,
    ReportTable, ReportNarrative, AccountReportItem, DateRange
)
from app.schemas.reports import CashFlowStatement, CashFlowItem
from app.utils.exceptions import ReportGenerationError

router = APIRouter()


class ReportAPIService:    
    """Servicio adaptador para la API de reportes"""
    def __init__(self, db: AsyncSession):
        self.db = db
        self.report_service = ReportService(db)
        self.company_service = CompanyService(db)
    
    async def _get_project_context(self, project_context: Optional[str]) -> str:
        """Obtener el contexto del proyecto, usando el nombre de empresa como default"""
        if project_context:
            return project_context
        return await self.company_service.get_company_name()
    
    async def generate_balance_general(
        self,
        project_context: Optional[str],
        from_date: date,
        to_date: date,
        detail_level: DetailLevel = DetailLevel.MEDIO,
        include_subaccounts: bool = False
    ) -> ReportResponse:
        """Generar Balance General"""
        
        # Validar y corregir fechas futuras automáticamente
        today = date.today()
        original_to_date = to_date
        
        # Si to_date es superior a la fecha actual, corregir automáticamente
        if to_date > today:
            to_date = today
            
        # Si from_date también es superior a la fecha actual, corregir automáticamente
        if from_date > today:
            from_date = today
            
        # Si después de las correcciones from_date > to_date, ajustar from_date
        if from_date > to_date:
            from_date = to_date
        
        # Obtener contexto del proyecto con valor por defecto
        resolved_context = await self._get_project_context(project_context)
          # Usar el servicio existente
        balance_sheet = await self.report_service.generate_balance_sheet(
            as_of_date=to_date,
            include_zero_balances=(detail_level == DetailLevel.ALTO),
            company_name=resolved_context
        )
        
        # Convertir a formato de la API
        table_data = self._convert_balance_sheet_to_table(balance_sheet, detail_level)
        narrative_data = self._generate_balance_narrative(balance_sheet, from_date, to_date, original_to_date)
        
        date_range = DateRange(**{"from": from_date, "to": to_date})
        
        return ReportResponse(
            success=True,
            report_type=ReportType.BALANCE_GENERAL,
            generated_at=date.today(),
            period=date_range,
            project_context=resolved_context,
            table=table_data,
            narrative=narrative_data
        )
    
    async def generate_flujo_efectivo(
        self,
        project_context: Optional[str],
        from_date: date,
        to_date: date,
        detail_level: DetailLevel = DetailLevel.MEDIO,
        include_subaccounts: bool = False
    ) -> ReportResponse:
        """Generar Estado de Flujo de Efectivo"""
        
        # Validar y corregir fechas futuras automáticamente
        today = date.today()
        original_to_date = to_date
        
        # Si to_date es superior a la fecha actual, corregir automáticamente
        if to_date > today:
            to_date = today
            
        # Si from_date también es superior a la fecha actual, corregir automáticamente
        if from_date > today:
            from_date = today
            
        # Si después de las correcciones from_date > to_date, ajustar from_date
        if from_date > to_date:
            from_date = to_date        # Obtener contexto del proyecto con valor por defecto
        resolved_context = await self._get_project_context(project_context)
        
        # Usar el nuevo CashFlowService para generar el estado
        cash_flow_service = CashFlowService(self.db, resolved_context)
        
        # Determinar método basado en el nivel de detalle
        method = CashFlowMethod.DIRECT if detail_level == DetailLevel.ALTO else CashFlowMethod.INDIRECT
        
        # Generar el estado de flujo de efectivo
        cash_flow_statement = await cash_flow_service.generate_cash_flow_statement(
            start_date=from_date,
            end_date=to_date,
            method=method,
            company_name=resolved_context
        )
        
        # Convertir a formato de la API
        table_data = self._convert_cash_flow_statement_to_table(cash_flow_statement, detail_level)
        narrative_data = self._generate_cash_flow_statement_narrative(
            cash_flow_statement, from_date, to_date, original_to_date
        )
        
        date_range = DateRange(**{"from": from_date, "to": to_date})
        return ReportResponse(
            success=True,
            report_type=ReportType.FLUJO_EFECTIVO,
            generated_at=date.today(),
            period=date_range,
            project_context=resolved_context,
            table=table_data,
            narrative=narrative_data
        )

    async def generate_perdidas_ganancias(
        self,
        project_context: Optional[str],
        from_date: date,
        to_date: date,
        detail_level: DetailLevel = DetailLevel.MEDIO,
        include_subaccounts: bool = False
    ) -> ReportResponse:
        """Generar Estado de Pérdidas y Ganancias"""
        
        # Validar y corregir fechas si son superiores a la fecha actual
        today = date.today()
        original_to_date = to_date
        
        # Corregir fecha final si es futura
        if to_date > today:
            to_date = today
            
        # Corregir fecha inicial si es futura
        if from_date > today:
            from_date = today
            
        # Asegurar que from_date no sea mayor que to_date después de las correcciones
        if from_date > to_date:
            from_date = to_date
        
        # Obtener contexto del proyecto con valor por defecto
        resolved_context = await self._get_project_context(project_context)
        
        income_statement = await self.report_service.generate_income_statement(
            start_date=from_date,
            end_date=to_date,
            include_zero_balances=(detail_level == DetailLevel.ALTO),
            company_name=resolved_context
        )
        
        table_data = self._convert_income_statement_to_table(income_statement, detail_level)
        narrative_data = self._generate_income_narrative(income_statement, from_date, to_date, original_to_date)
        
        date_range = DateRange(**{"from": from_date, "to": to_date})
        return ReportResponse(
            success=True,
            report_type=ReportType.P_G,
            generated_at=date.today(),
            period=date_range,
            project_context=resolved_context,
            table=table_data,
            narrative=narrative_data
        )
    
    def _convert_balance_sheet_to_table(self, balance_sheet, detail_level: DetailLevel) -> ReportTable:
        """Convertir Balance General al formato de tabla de la API"""
        
        sections = []
        
        # Sección de Activos
        activos_items = []
        for item in balance_sheet.assets.items:
            activos_items.append({
                "account_group": "ACTIVOS",
                "account_code": item.account_code,
                "account_name": item.account_name,
                "opening_balance": Decimal('0'),  # Simplificado
                "movements": item.balance,
                "closing_balance": item.balance,
                "level": item.level
            })
        
        sections.append({
            "section_name": "ACTIVOS",
            "items": activos_items,
            "total": balance_sheet.assets.total
        })
        
        # Sección de Pasivos
        pasivos_items = []
        for item in balance_sheet.liabilities.items:
            pasivos_items.append({
                "account_group": "PASIVOS",
                "account_code": item.account_code,
                "account_name": item.account_name,
                "opening_balance": Decimal('0'),
                "movements": item.balance,
                "closing_balance": item.balance,
                "level": item.level
            })
        
        sections.append({
            "section_name": "PASIVOS",
            "items": pasivos_items,
            "total": balance_sheet.liabilities.total
        })
        
        # Sección de Patrimonio
        patrimonio_items = []
        for item in balance_sheet.equity.items:
            patrimonio_items.append({
                "account_group": "PATRIMONIO",
                "account_code": item.account_code,
                "account_name": item.account_name,
                "opening_balance": Decimal('0'),
                "movements": item.balance,
                "closing_balance": item.balance,
                "level": item.level
            })
        
        sections.append({
            "section_name": "PATRIMONIO",
            "items": patrimonio_items,
            "total": balance_sheet.equity.total
        })
        
        return ReportTable(
            sections=sections,
            totals={
                "total_activos": balance_sheet.total_assets,
                "total_pasivos": balance_sheet.liabilities.total,
                "total_patrimonio": balance_sheet.equity.total,
                "total_pasivos_patrimonio": balance_sheet.total_liabilities_equity
            },
            summary={
                "is_balanced": balance_sheet.is_balanced,
                "report_date": balance_sheet.report_date,
                "company_name": balance_sheet.company_name
            }
        )
    def _convert_cash_flow_to_table(self, cash_ledger, detail_level: DetailLevel) -> ReportTable:
        """Convertir flujo de efectivo al formato de tabla"""
        
        sections = []
        total_cash_flow = Decimal('0')
        
        # Agrupar por actividades (simplificado)
        actividades_operacion = []
        
        for account in cash_ledger.accounts:
            if "caja" in account.account_name.lower() or "banco" in account.account_name.lower():
                net_movement = account.total_debits - account.total_credits
                total_cash_flow += net_movement
                
                actividades_operacion.append({
                    "account_group": "ACTIVIDADES DE OPERACIÓN",
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "opening_balance": account.opening_balance,
                    "movements": net_movement,
                    "closing_balance": account.closing_balance,
                    "level": 1
                })
        
        sections.append({
            "section_name": "ACTIVIDADES DE OPERACIÓN",
            "items": actividades_operacion,
            "total": sum(item["movements"] for item in actividades_operacion)
        })
        
        return ReportTable(
            sections=sections,
            totals={
                "flujo_neto_efectivo": total_cash_flow,
                "efectivo_inicial": Decimal('0'),  # Simplificado
                "efectivo_final": total_cash_flow
            },
            summary={
                "start_date": cash_ledger.start_date,
                "end_date": cash_ledger.end_date,
                "company_name": cash_ledger.company_name
            }
        )
    
    def _convert_income_statement_to_table(self, income_statement, detail_level: DetailLevel) -> ReportTable:
        """Convertir Estado de Resultados al formato de tabla"""
        
        sections = []
        
        # Sección de Ingresos
        ingresos_items = []
        for item in income_statement.revenues.items:
            ingresos_items.append({
                "account_group": "INGRESOS",
                "account_code": item.account_code,
                "account_name": item.account_name,
                "opening_balance": Decimal('0'),
                "movements": item.amount,
                "closing_balance": item.amount,
                "level": item.level
            })
        
        sections.append({
            "section_name": "INGRESOS",
            "items": ingresos_items,
            "total": income_statement.revenues.total
        })
        
        # Sección de Gastos
        gastos_items = []
        for item in income_statement.expenses.items:
            gastos_items.append({
                "account_group": "GASTOS",
                "account_code": item.account_code,
                "account_name": item.account_name,
                "opening_balance": Decimal('0'),
                "movements": item.amount,
                "closing_balance": item.amount,
                "level": item.level
            })
        
        sections.append({
            "section_name": "GASTOS",
            "items": gastos_items,
            "total": income_statement.expenses.total
        })
        
        return ReportTable(
            sections=sections,
            totals={
                "total_ingresos": income_statement.revenues.total,
                "total_gastos": income_statement.expenses.total,
                "utilidad_bruta": income_statement.gross_profit,
                "utilidad_operacional": income_statement.operating_profit,
                "utilidad_neta": income_statement.net_profit
            },
            summary={
                "start_date": income_statement.start_date,
                "end_date": income_statement.end_date,
                "company_name": income_statement.company_name            }
        )
    
    def _generate_balance_narrative(self, balance_sheet, from_date: date, to_date: date, original_to_date: Optional[date] = None) -> ReportNarrative:
        """Generar narrativa para Balance General"""
        
        # Calcular ratios básicos
        total_assets = balance_sheet.total_assets
        total_liabilities = balance_sheet.liabilities.total
        total_equity = balance_sheet.equity.total
        
        debt_ratio = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
        equity_ratio = (total_equity / total_assets * 100) if total_assets > 0 else 0
        
        executive_summary = f"""
        El Balance General al {to_date} muestra activos totales por ${total_assets:,.2f}.
        La estructura financiera presenta un {debt_ratio:.1f}% de financiamiento con pasivos y un {equity_ratio:.1f}% con patrimonio.
        La ecuación contable se encuentra {'balanceada' if balance_sheet.is_balanced else 'desbalanceada'}.
        """
        key_variations = [
            f"Activos totales: ${total_assets:,.2f}",
            f"Pasivos totales: ${total_liabilities:,.2f}",
            f"Patrimonio total: ${total_equity:,.2f}",
            f"Ratio de endeudamiento: {debt_ratio:.1f}%"
        ]
        
        recommendations = []
        if debt_ratio > 70:
            recommendations.append("Considerar reducir el nivel de endeudamiento para mejorar la solvencia")
        if debt_ratio < 30:
            recommendations.append("Posibilidad de apalancamiento para financiar crecimiento")
        if balance_sheet.is_balanced:
            recommendations.append("Mantener el equilibrio contable verificando periódicamente")
        
        # Agregar nota si las fechas fueron corregidas automáticamente
        if original_to_date and original_to_date > to_date:
            key_variations.insert(0, f"⚠️ Fecha corregida automáticamente: La fecha solicitada ({original_to_date}) era superior a la actual, se ajustó a {to_date}")
            recommendations.insert(0, "Verificar que las fechas del reporte sean válidas para evitar correcciones automáticas")
        
        financial_highlights = [
            f"Estructura de capital: {equity_ratio:.1f}% patrimonio, {debt_ratio:.1f}% deuda",
            f"Estado del balance: {'Balanceado' if balance_sheet.is_balanced else 'Requiere ajustes'}",
            f"Total de cuentas con saldo: {len(balance_sheet.assets.items + balance_sheet.liabilities.items + balance_sheet.equity.items)}"
        ]
        
        return ReportNarrative(
            executive_summary=executive_summary.strip(),
            key_variations=key_variations,
            recommendations=recommendations,
            financial_highlights=financial_highlights
        )
    
    def _generate_cash_flow_narrative(self, cash_ledger, from_date: date, to_date: date, original_to_date: Optional[date] = None) -> ReportNarrative:
        """Generar narrativa para Flujo de Efectivo"""
        
        total_movements = sum(
            abs(account.total_debits - account.total_credits) 
            for account in cash_ledger.accounts
        )
        
        executive_summary = f"""
        El Estado de Flujo de Efectivo del período {from_date} al {to_date}
        muestra movimientos netos por ${total_movements:,.2f} en cuentas de efectivo y equivalentes.
        """
        
        # Agregar nota si las fechas fueron corregidas automáticamente
        key_variations = [f"Movimientos totales de efectivo: ${total_movements:,.2f}"]
        recommendations = ["Monitorear el flujo de efectivo regularmente"]
        
        if original_to_date and original_to_date > to_date:
            key_variations.insert(0, f"⚠️ Fecha corregida automáticamente: La fecha final solicitada ({original_to_date}) era superior a la actual, se ajustó a {to_date}")
            recommendations.insert(0, "Verificar que las fechas del reporte sean válidas para evitar correcciones automáticas")
        
        return ReportNarrative(
            executive_summary=executive_summary.strip(),
            key_variations=key_variations,
            recommendations=recommendations,            financial_highlights=["Análisis de liquidez basado en movimientos de efectivo"]
        )

    def _generate_income_narrative(self, income_statement, from_date: date, to_date: date, original_to_date: Optional[date] = None) -> ReportNarrative:
        """Generar narrativa para Estado de Resultados"""
        
        total_revenues = income_statement.revenues.total
        total_expenses = income_statement.expenses.total
        net_profit = income_statement.net_profit
        
        margin = (net_profit / total_revenues * 100) if total_revenues > 0 else 0
        
        executive_summary = f"""
        El Estado de Resultados del período {from_date} al {to_date}
        registra ingresos por ${total_revenues:,.2f} y gastos por ${total_expenses:,.2f},
        resultando en una utilidad neta de ${net_profit:,.2f} (margen {margin:.1f}%).
        """
        
        key_variations = [
            f"Ingresos totales: ${total_revenues:,.2f}",
            f"Gastos totales: ${total_expenses:,.2f}",
            f"Utilidad neta: ${net_profit:,.2f}",
            f"Margen de utilidad: {margin:.1f}%"
        ]
        
        recommendations = []
        if margin < 5:
            recommendations.append("Revisar estructura de costos para mejorar rentabilidad")
        elif margin > 20:
            recommendations.append("Excelente margen de rentabilidad, mantener eficiencia")
        
        if net_profit < 0:
            recommendations.append("Analizar causas de pérdidas y implementar medidas correctivas")
          # Agregar nota si las fechas fueron corregidas automáticamente
        if original_to_date and original_to_date > to_date:
            key_variations.insert(0, f"⚠️ Fecha corregida automáticamente: La fecha final solicitada ({original_to_date}) era superior a la actual, se ajustó a {to_date}")
            recommendations.insert(0, "Verificar que las fechas del reporte sean válidas para evitar correcciones automáticas")
        
        financial_highlights = [
            f"Rentabilidad: {'Positiva' if net_profit > 0 else 'Negativa'}",
            f"Eficiencia operativa: {margin:.1f}% de margen",
            f"Relación ingresos/gastos: {(total_revenues/total_expenses):.2f}" if total_expenses > 0 else "N/A"
        ]
        
        return ReportNarrative(
            executive_summary=executive_summary.strip(),
            key_variations=key_variations,
            recommendations=recommendations,
            financial_highlights=financial_highlights
        )

    def _convert_cash_flow_statement_to_table(self, cash_flow_statement: CashFlowStatement, detail_level: DetailLevel) -> ReportTable:
        """Convertir CashFlowStatement al formato de tabla de la API"""
        
        sections = []
        
        # Sección de Actividades de Operación
        operating_items = []
        
        # Agregar utilidad neta si es método indirecto
        if cash_flow_statement.method == "indirect" and cash_flow_statement.operating_activities.net_income != 0:
            operating_items.append({
                "account_group": "ACTIVIDADES DE OPERACIÓN",
                "account_code": "",
                "account_name": "Utilidad (Pérdida) Neta",
                "opening_balance": Decimal('0'),
                "movements": cash_flow_statement.operating_activities.net_income,
                "closing_balance": cash_flow_statement.operating_activities.net_income,
                "level": 1
            })
        
        # Agregar ajustes
        for adjustment in cash_flow_statement.operating_activities.adjustments:
            operating_items.append({
                "account_group": "ACTIVIDADES DE OPERACIÓN",
                "account_code": adjustment.account_code,
                "account_name": f"Ajuste: {adjustment.description}",
                "opening_balance": Decimal('0'),
                "movements": adjustment.amount,
                "closing_balance": adjustment.amount,
                "level": 2
            })
        
        # Agregar cambios en capital de trabajo
        for wc_change in cash_flow_statement.operating_activities.working_capital_changes:
            operating_items.append({
                "account_group": "ACTIVIDADES DE OPERACIÓN",
                "account_code": wc_change.account_code,
                "account_name": f"Capital de trabajo: {wc_change.description}",
                "opening_balance": Decimal('0'),
                "movements": wc_change.amount,
                "closing_balance": wc_change.amount,
                "level": 2
            })
        
        # Agregar otros items operativos (método directo)
        for item in cash_flow_statement.operating_activities.items:
            operating_items.append({
                "account_group": "ACTIVIDADES DE OPERACIÓN",
                "account_code": item.account_code,
                "account_name": item.description,
                "opening_balance": Decimal('0'),
                "movements": item.amount,
                "closing_balance": item.amount,
                "level": 1
            })
        
        sections.append({
            "section_name": "ACTIVIDADES DE OPERACIÓN",
            "items": operating_items,
            "total": cash_flow_statement.net_cash_from_operating
        })
        
        # Sección de Actividades de Inversión
        investing_items = []
        for item in cash_flow_statement.investing_activities:
            investing_items.append({
                "account_group": "ACTIVIDADES DE INVERSIÓN",
                "account_code": item.account_code,
                "account_name": item.description,
                "opening_balance": Decimal('0'),
                "movements": item.amount,
                "closing_balance": item.amount,
                "level": 1
            })
        
        sections.append({
            "section_name": "ACTIVIDADES DE INVERSIÓN",
            "items": investing_items,
            "total": cash_flow_statement.net_cash_from_investing
        })
        
        # Sección de Actividades de Financiamiento
        financing_items = []
        for item in cash_flow_statement.financing_activities:
            financing_items.append({
                "account_group": "ACTIVIDADES DE FINANCIAMIENTO",
                "account_code": item.account_code,
                "account_name": item.description,
                "opening_balance": Decimal('0'),
                "movements": item.amount,
                "closing_balance": item.amount,
                "level": 1
            })
        
        sections.append({
            "section_name": "ACTIVIDADES DE FINANCIAMIENTO",
            "items": financing_items,
            "total": cash_flow_statement.net_cash_from_financing
        })
        
        return ReportTable(
            sections=sections,
            totals={
                "flujo_operativo": cash_flow_statement.net_cash_from_operating,
                "flujo_inversion": cash_flow_statement.net_cash_from_investing,
                "flujo_financiamiento": cash_flow_statement.net_cash_from_financing,
                "flujo_neto": cash_flow_statement.net_change_in_cash,
                "efectivo_inicial": cash_flow_statement.cash_beginning_period,
                "efectivo_final": cash_flow_statement.cash_ending_period
            },
            summary={
                "method": cash_flow_statement.method,
                "start_date": cash_flow_statement.start_date,
                "end_date": cash_flow_statement.end_date,
                "company_name": cash_flow_statement.company_name,
                "is_balanced": cash_flow_statement.is_balanced
            }
        )

    def _generate_cash_flow_statement_narrative(self, cash_flow_statement: CashFlowStatement, from_date: date, to_date: date, original_to_date: Optional[date] = None) -> ReportNarrative:
        """Generar narrativa para CashFlowStatement"""
        
        operating_flow = cash_flow_statement.net_cash_from_operating
        investing_flow = cash_flow_statement.net_cash_from_investing
        financing_flow = cash_flow_statement.net_cash_from_financing
        net_change = cash_flow_statement.net_change_in_cash
        
        executive_summary = f"""
        El Estado de Flujo de Efectivo del período {from_date} al {to_date} (método {cash_flow_statement.method})
        muestra flujo operativo de ${operating_flow:,.2f}, flujo de inversión de ${investing_flow:,.2f},
        y flujo de financiamiento de ${financing_flow:,.2f}, resultando en un cambio neto de ${net_change:,.2f}.
        El efectivo pasó de ${cash_flow_statement.cash_beginning_period:,.2f} a ${cash_flow_statement.cash_ending_period:,.2f}.
        """
        
        key_variations = [
            f"Flujo de actividades operativas: ${operating_flow:,.2f}",
            f"Flujo de actividades de inversión: ${investing_flow:,.2f}",
            f"Flujo de actividades de financiamiento: ${financing_flow:,.2f}",
            f"Cambio neto en efectivo: ${net_change:,.2f}",
            f"Método utilizado: {cash_flow_statement.method.title()}"
        ]
        
        recommendations = []
        if operating_flow < 0:
            recommendations.append("Revisar flujos operativos negativos - posible problema de liquidez")
        elif operating_flow > 0:
            recommendations.append("Excelente generación de efectivo operativo - continuar tendencia")
        
        if abs(investing_flow) > abs(operating_flow):
            recommendations.append("Alto nivel de actividad de inversión - evaluar retornos esperados")
        
        if net_change < 0:
            recommendations.append("Disminución neta de efectivo requiere monitoreo de liquidez")
        
        if not cash_flow_statement.is_balanced:
            recommendations.append("⚠️ Revisar cálculos - el flujo no cuadra correctamente")
          # Agregar nota si las fechas fueron corregidas automáticamente
        if original_to_date and original_to_date > to_date:
            key_variations.insert(0, f"⚠️ Fecha corregida automáticamente: La fecha final solicitada ({original_to_date}) era superior a la actual, se ajustó a {to_date}")
            recommendations.insert(0, "Verificar que las fechas del reporte sean válidas para evitar correcciones automáticas")
        
        financial_highlights = [
            f"Generación operativa: {'Positiva' if operating_flow > 0 else 'Negativa'}",
            f"Posición de liquidez: {'Fortaleciéndose' if net_change > 0 else 'Debilitándose'}",
            f"Estado del flujo: {'Balanceado' if cash_flow_statement.is_balanced else 'Requiere revisión'}",
            f"Efectivo inicial vs final: {((cash_flow_statement.cash_ending_period / cash_flow_statement.cash_beginning_period - 1) * 100):.1f}% cambio" if cash_flow_statement.cash_beginning_period > 0 else "N/A"
        ]
        
        return ReportNarrative(
            executive_summary=executive_summary.strip(),
            key_variations=key_variations,
            recommendations=recommendations,
            financial_highlights=financial_highlights
        )


# Endpoints separados por tipo de reporte

@router.get(
    "/balance-general",
    response_model=ReportResponse,
    summary="Generar Balance General",
    description="Generar Balance General con parámetros específicos"
)
async def generate_balance_general(
    project_context: Optional[str] = Query(None, description="Contexto o nombre del proyecto (opcional - usa nombre de empresa si se omite)"),
    from_date: date = Query(..., description="Fecha de inicio del período"),
    to_date: date = Query(..., description="Fecha de fin del período"),
    detail_level: DetailLevel = Query(DetailLevel.MEDIO, description="Nivel de detalle del reporte"),
    include_subaccounts: bool = Query(False, description="Incluir subcuentas en el detalle"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ReportResponse:
    """
    Generar Balance General.
    
    - **project_context**: Nombre de la empresa o proyecto
    - **from_date**: Fecha de inicio (usado para cálculos de variación)
    - **to_date**: Fecha al cierre del balance
    - **detail_level**: Nivel de detalle (bajo, medio, alto)
    - **include_subaccounts**: Incluir cuentas con saldo cero
    """
    
    try:
        service = ReportAPIService(db)
        result = await service.generate_balance_general(
            project_context=project_context,
            from_date=from_date,
            to_date=to_date,
            detail_level=detail_level,
            include_subaccounts=include_subaccounts
        )
        return result
        
    except ReportGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error_code": "REPORT_GENERATION_ERROR",
                "error_message": str(e),
                "details": {"report_type": "balance_general"}
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "error_message": "Error interno del servidor",
                "details": {"original_error": str(e)}
            }
        )


@router.get(
    "/flujo-efectivo",
    response_model=ReportResponse,
    summary="Generar Estado de Flujo de Efectivo",
    description="Generar Estado de Flujo de Efectivo con parámetros específicos"
)
async def generate_flujo_efectivo(
    project_context: Optional[str] = Query(None, description="Contexto o nombre del proyecto (opcional - usa nombre de empresa si se omite)"),
    from_date: date = Query(..., description="Fecha de inicio del período"),
    to_date: date = Query(..., description="Fecha de fin del período"),
    detail_level: DetailLevel = Query(DetailLevel.MEDIO, description="Nivel de detalle del reporte"),
    include_subaccounts: bool = Query(False, description="Incluir subcuentas en el detalle"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ReportResponse:
    """
    Generar Estado de Flujo de Efectivo.
    
    - **project_context**: Nombre de la empresa o proyecto
    - **from_date**: Fecha de inicio del período
    - **to_date**: Fecha de fin del período
    - **detail_level**: Nivel de detalle (bajo, medio, alto)
    - **include_subaccounts**: Incluir análisis detallado de subcuentas
    """
    
    try:
        service = ReportAPIService(db)
        result = await service.generate_flujo_efectivo(
            project_context=project_context,
            from_date=from_date,
            to_date=to_date,
            detail_level=detail_level,
            include_subaccounts=include_subaccounts
        )
        return result
        
    except ReportGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error_code": "REPORT_GENERATION_ERROR",
                "error_message": str(e),
                "details": {"report_type": "flujo_efectivo"}
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "error_message": "Error interno del servidor",
                "details": {"original_error": str(e)}
            }
        )


@router.get(
    "/perdidas-ganancias",
    response_model=ReportResponse,
    summary="Generar Estado de Pérdidas y Ganancias",
    description="Generar Estado de Pérdidas y Ganancias con parámetros específicos"
)
async def generate_perdidas_ganancias(
    project_context: Optional[str] = Query(None, description="Contexto o nombre del proyecto (opcional - usa nombre de empresa si se omite)"),
    from_date: date = Query(..., description="Fecha de inicio del período"),
    to_date: date = Query(..., description="Fecha de fin del período"),
    detail_level: DetailLevel = Query(DetailLevel.MEDIO, description="Nivel de detalle del reporte"),
    include_subaccounts: bool = Query(False, description="Incluir subcuentas en el detalle"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ReportResponse:
    """
    Generar Estado de Pérdidas y Ganancias.
    
    - **project_context**: Nombre de la empresa o proyecto
    - **from_date**: Fecha de inicio del período
    - **to_date**: Fecha de fin del período
    - **detail_level**: Nivel de detalle (bajo, medio, alto)
    - **include_subaccounts**: Incluir desglose por subcuentas
    """
    
    try:
        service = ReportAPIService(db)
        result = await service.generate_perdidas_ganancias(
            project_context=project_context,
            from_date=from_date,
            to_date=to_date,
            detail_level=detail_level,
            include_subaccounts=include_subaccounts
        )
        return result
        
    except ReportGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error_code": "REPORT_GENERATION_ERROR",
                "error_message": str(e),
                "details": {"report_type": "perdidas_ganancias"}
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "error_message": "Error interno del servidor",
                "details": {"original_error": str(e)}
            }
        )


# Endpoint adicional para listar tipos de reportes disponibles
@router.get(
    "/tipos",
    response_model=List[Dict[str, str]],
    summary="Listar tipos de reportes disponibles",
    description="Obtener lista de tipos de reportes financieros disponibles"
)
async def list_report_types(
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, str]]:
    """
    Listar todos los tipos de reportes financieros disponibles.
    """
    
    return [
        {
            "type": "balance_general",
            "name": "Balance General",
            "description": "Estado de la situación financiera a una fecha específica",
            "endpoint": "/reports/balance-general"
        },
        {
            "type": "flujo_efectivo",
            "name": "Estado de Flujo de Efectivo",
            "description": "Movimientos de efectivo en un período específico",
            "endpoint": "/reports/flujo-efectivo"
        },
        {
            "type": "perdidas_ganancias",
            "name": "Estado de Pérdidas y Ganancias",
            "description": "Ingresos y gastos en un período específico",
            "endpoint": "/reports/perdidas-ganancias"
        }
    ]
