"""
Servicio para gestionar cambios de moneda base de la empresa.
Maneja todas las validaciones y procesos necesarios para cambiar
la moneda base sin perder integridad de datos históricos.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_, or_
from sqlalchemy.orm import selectinload

from app.models.company_settings import CompanySettings
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, TransactionOrigin
from app.models.account import Account, AccountType
from app.models.currency import Currency, ExchangeRate
from app.models.journal import Journal
from app.models.payment import Payment
from app.schemas.company_settings import CompanySettingsUpdate
from app.utils.exceptions import BusinessRuleError, NotFoundError
from app.services.journal_entry_service import JournalEntryService
import logging

logger = logging.getLogger(__name__)

class CurrencyChangeValidationResult:
    """Resultado de validación de cambio de moneda"""
    def __init__(self):
        self.can_change = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.impact_summary: Dict[str, Any] = {}
        self.historical_entries_count = 0
        self.entries_with_foreign_currency = 0
        self.accounts_affected = 0

class CurrencyChangeService:
    """Servicio para gestión de cambios de moneda base"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_currency_change(
        self, 
        current_currency: str,
        new_currency: str,
        effective_date: Optional[date] = None
    ) -> CurrencyChangeValidationResult:
        """
        Valida si se puede realizar el cambio de moneda base.
        """
        logger.info(f"Validando cambio de moneda de {current_currency} a {new_currency}")
        
        result = CurrencyChangeValidationResult()
        
        if not effective_date:
            effective_date = date.today()
        
        # 1. Validar que la nueva moneda existe y está activa
        await self._validate_target_currency(new_currency, result)
        
        # 2. Analizar asientos históricos
        await self._analyze_historical_entries(current_currency, result)
        
        # 3. Verificar tasas de cambio disponibles
        await self._validate_exchange_rates(current_currency, new_currency, effective_date, result)
        
        # 4. Verificar cuenta para diferencias de cambio
        await self._validate_exchange_difference_account(result)
        
        # 5. Verificar períodos contables cerrados
        await self._validate_accounting_periods(effective_date, result)
        
        # 6. Generar resumen de impacto
        await self._generate_impact_summary(current_currency, new_currency, result)
        
        return result

    async def _validate_target_currency(self, currency_code: str, result: CurrencyChangeValidationResult):
        """Valida que la moneda objetivo existe y está activa"""
        currency_result = await self.db.execute(
            select(Currency).where(
                and_(
                    Currency.code == currency_code,
                    Currency.is_active == True
                )
            )
        )
        currency = currency_result.scalar_one_or_none()
        
        if not currency:
            result.can_change = False
            result.errors.append(f"La moneda {currency_code} no existe o no está activa")

    async def _analyze_historical_entries(self, current_currency: str, result: CurrencyChangeValidationResult):
        """Analiza asientos contables históricos que serán afectados"""
        
        # Contar asientos contabilizados
        posted_entries_result = await self.db.execute(
            select(JournalEntry).where(
                JournalEntry.status == JournalEntryStatus.POSTED
            )
        )
        posted_entries = posted_entries_result.scalars().all()
        
        result.historical_entries_count = len(posted_entries)
        
        if result.historical_entries_count > 0:
            result.warnings.append(
                f"Existen {result.historical_entries_count} asientos contabilizados. "
                "Sus valores históricos se mantendrán en la moneda original."
            )
        
        # Contar asientos con monedas extranjeras
        foreign_currency_lines_result = await self.db.execute(
            select(JournalEntryLine).where(
                JournalEntryLine.currency_id.isnot(None)
            )
        )
        foreign_currency_lines = foreign_currency_lines_result.scalars().all()
        
        result.entries_with_foreign_currency = len(foreign_currency_lines)
        
        if result.entries_with_foreign_currency > 0:
            result.warnings.append(
                f"Existen {result.entries_with_foreign_currency} líneas de asiento con monedas extranjeras. "
                "Estas líneas requerirán revisión después del cambio."
            )

    async def _validate_exchange_rates(
        self, 
        current_currency: str, 
        new_currency: str, 
        effective_date: date,
        result: CurrencyChangeValidationResult
    ):
        """Valida que existen tasas de cambio necesarias"""
        
        # Buscar moneda objetivo
        new_currency_result = await self.db.execute(
            select(Currency).where(Currency.code == new_currency)
        )
        new_currency_obj = new_currency_result.scalar_one_or_none()
        
        if not new_currency_obj:
            result.errors.append(f"No se encontró la moneda {new_currency}")
            return
        
        # Verificar tasa de cambio reciente para la nueva moneda
        rate_result = await self.db.execute(
            select(ExchangeRate).where(
                and_(
                    ExchangeRate.currency_id == new_currency_obj.id,
                    ExchangeRate.rate_date <= effective_date
                )
            ).order_by(ExchangeRate.rate_date.desc()).limit(1)
        )
        latest_rate = rate_result.scalar_one_or_none()
        
        if not latest_rate:
            result.warnings.append(f"No se encontró tasa de cambio para {new_currency}")
        elif (effective_date - latest_rate.rate_date).days > 30:
            result.warnings.append(f"La tasa de cambio más reciente para {new_currency} tiene {(effective_date - latest_rate.rate_date).days} días de antigüedad")

    async def _validate_exchange_difference_account(self, result: CurrencyChangeValidationResult):
        """Valida que existe cuenta configurada para diferencias de cambio"""
        
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings or not hasattr(settings, 'default_currency_exchange_account_id') or not settings.default_currency_exchange_account_id:
            result.warnings.append(
                "No hay cuenta configurada para diferencias de cambio. "
                "Se recomienda configurar una antes del cambio de moneda."
            )

    async def _validate_accounting_periods(self, effective_date: date, result: CurrencyChangeValidationResult):
        """Valida que los períodos contables permiten el cambio"""
        # Por ahora solo verificamos que la fecha no sea muy antigua
        days_old = (date.today() - effective_date).days
        
        if days_old > 365:
            result.warnings.append(
                f"La fecha efectiva del cambio es de hace {days_old} días. "
                "Esto puede afectar períodos contables cerrados."
            )

    async def _generate_impact_summary(
        self, 
        current_currency: str, 
        new_currency: str, 
        result: CurrencyChangeValidationResult
    ):
        """Genera resumen del impacto del cambio"""
        
        # Contar cuentas que serán afectadas
        accounts_result = await self.db.execute(
            select(Account).where(Account.is_active == True)
        )
        accounts = accounts_result.scalars().all()
        result.accounts_affected = len(accounts)
        
        result.impact_summary = {
            "current_currency": current_currency,
            "new_currency": new_currency,
            "total_accounts": result.accounts_affected,
            "historical_entries": result.historical_entries_count,
            "foreign_currency_lines": result.entries_with_foreign_currency,
            "requires_adjustment_entries": result.historical_entries_count > 0,
            "requires_exchange_rates": True
        }

    async def prepare_currency_change(
        self,
        new_currency: str,
        effective_date: date,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Prepara el cambio de moneda creando asientos de ajuste si es necesario.
        """
        logger.info(f"Preparando cambio de moneda a {new_currency}")
        
        # Obtener configuración actual
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            raise BusinessRuleError("No se encontró configuración de empresa")
        
        current_currency = settings.currency_code
        
        # Validar cambio
        validation = await self.validate_currency_change(current_currency, new_currency, effective_date)
        
        if not validation.can_change:
            raise BusinessRuleError(f"No se puede cambiar la moneda: {'; '.join(validation.errors)}")
        
        preparation_result = {
            "validation": validation,
            "adjustment_entries": [],
            "required_actions": []
        }
        
        # Si hay asientos históricos, crear asientos de revalorización
        if validation.historical_entries_count > 0:
            adjustment_entries = await self._create_revaluation_entries(
                current_currency, 
                new_currency, 
                effective_date, 
                user_id
            )
            preparation_result["adjustment_entries"] = adjustment_entries
        
        # Generar lista de acciones requeridas
        preparation_result["required_actions"] = self._generate_required_actions(validation)
        
        return preparation_result

    async def _create_revaluation_entries(
        self,
        current_currency: str,
        new_currency: str,
        effective_date: date,
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Crea asientos de revalorización para el cambio de moneda"""
        
        logger.info("Creando asientos de revalorización por cambio de moneda")
        
        # Buscar moneda objetivo para obtener tasa de cambio
        new_currency_result = await self.db.execute(
            select(Currency).where(Currency.code == new_currency)
        )
        new_currency_obj = new_currency_result.scalar_one_or_none()
        
        if not new_currency_obj:
            logger.warning(f"No se encontró la moneda {new_currency} para crear asientos de revalorización")
            return []
        
        # Buscar tasa de cambio
        exchange_rate_result = await self.db.execute(
            select(ExchangeRate).where(
                and_(
                    ExchangeRate.currency_id == new_currency_obj.id,
                    ExchangeRate.rate_date <= effective_date
                )
            ).order_by(ExchangeRate.rate_date.desc()).limit(1)
        )
        exchange_rate = exchange_rate_result.scalar_one_or_none()
        
        if not exchange_rate:
            # No crear asientos si no hay tasa de cambio
            return []
        
        # Obtener diario para ajustes
        adjustment_journal = await self._get_or_create_adjustment_journal()
        
        # Obtener cuenta para diferencias de cambio
        exchange_diff_account = await self._get_exchange_difference_account()
        
        if not exchange_diff_account:
            # No crear asientos si no hay cuenta configurada
            return []
        
        # Por ahora, crear un asiento de ejemplo que documente el cambio
        journal_entry_service = JournalEntryService(self.db)
        
        entry_data = {
            "journal_id": adjustment_journal.id,
            "entry_date": datetime.combine(effective_date, datetime.min.time()),
            "description": f"Revalorización por cambio de moneda base de {current_currency} a {new_currency}",
            "entry_type": "adjustment",
            "transaction_origin": TransactionOrigin.ADJUSTMENT,
            "reference": f"CURRENCY-CHANGE-{current_currency}-{new_currency}-{effective_date}",
            "lines": [
                {
                    "account_id": exchange_diff_account.id,
                    "description": f"Diferencia por cambio de moneda base (tasa: {exchange_rate.rate})",
                    "debit_amount": Decimal("0.01"),  # Asiento simbólico
                    "credit_amount": Decimal("0.00")
                },
                {
                    "account_id": exchange_diff_account.id,
                    "description": f"Diferencia por cambio de moneda base (tasa: {exchange_rate.rate})",
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": Decimal("0.01")  # Asiento simbólico
                }
            ]
        }
        
        try:
            from app.schemas.journal_entry import JournalEntryCreate
            schema_data = JournalEntryCreate(**entry_data)
            
            adjustment_entry = await journal_entry_service.create_journal_entry(
                schema_data, 
                user_id
            )
            
            return [{
                "id": str(adjustment_entry.id),
                "number": adjustment_entry.number,
                "description": adjustment_entry.description,
                "entry_date": adjustment_entry.entry_date.isoformat() if adjustment_entry.entry_date else None,
                "status": adjustment_entry.status.value if adjustment_entry.status else None
            }]
            
        except Exception as e:
            logger.warning(f"No se pudo crear asiento de revalorización: {e}")
            return []

    async def _get_or_create_adjustment_journal(self) -> Journal:
        """Obtiene o crea un diario para ajustes de moneda"""
        
        # Buscar diario de ajustes existente
        adjustment_journal_result = await self.db.execute(
            select(Journal).where(
                and_(
                    Journal.code.like('%ADJUST%'),
                    Journal.is_active == True
                )
            ).limit(1)
        )
        adjustment_journal = adjustment_journal_result.scalar_one_or_none()
        
        if adjustment_journal:
            return adjustment_journal
        
        # Si no existe, buscar cualquier diario activo
        any_journal_result = await self.db.execute(
            select(Journal).where(Journal.is_active == True).limit(1)
        )
        any_journal = any_journal_result.scalar_one_or_none()
        
        if not any_journal:
            raise BusinessRuleError("No hay diarios activos disponibles para crear asientos de ajuste")
        
        return any_journal

    async def _get_exchange_difference_account(self) -> Optional[Account]:
        """Obtiene la cuenta configurada para diferencias de cambio"""
        
        # Buscar en configuración de empresa
        settings_result = await self.db.execute(
            select(CompanySettings).options(
                selectinload(CompanySettings.default_currency_exchange_account)
            ).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if settings and hasattr(settings, 'default_currency_exchange_account') and settings.default_currency_exchange_account:
            return settings.default_currency_exchange_account
        
        # Buscar cuenta que pueda servir para diferencias de cambio
        exchange_account_result = await self.db.execute(
            select(Account).where(
                and_(
                    or_(
                        Account.name.ilike('%diferencia%cambio%'),
                        Account.name.ilike('%exchange%difference%'),
                        Account.name.ilike('%diferencia%cambiaria%')
                    ),
                    Account.is_active == True
                )
            ).limit(1)
        )
        return exchange_account_result.scalar_one_or_none()

    def _generate_required_actions(self, validation: CurrencyChangeValidationResult) -> List[str]:
        """Genera lista de acciones requeridas antes del cambio"""
        
        actions = []
        
        if validation.historical_entries_count > 0:
            actions.append(
                "Revisar y validar asientos de revalorización por cambio de moneda"
            )
        
        if validation.entries_with_foreign_currency > 0:
            actions.append(
                "Revisar líneas de asiento con monedas extranjeras después del cambio"
            )
        
        if "No hay cuenta configurada" in str(validation.warnings):
            actions.append(
                "Configurar cuenta para diferencias de cambio en configuración de empresa"
            )
        
        if "No se encontró tasa de cambio" in str(validation.warnings):
            actions.append(
                "Configurar tasas de cambio necesarias en el módulo de monedas"
            )
        
        actions.extend([
            "Generar reportes de balances antes del cambio para referencia",
            "Notificar a usuarios sobre el cambio de moneda base",
            "Verificar configuración de cuentas por defecto en nueva moneda",
            "Revisar configuración de reportes financieros"
        ])
        
        return actions

    async def execute_currency_change(
        self,
        new_currency: str,
        effective_date: date,
        user_id: uuid.UUID,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Ejecuta el cambio de moneda base después de las validaciones.
        """
        logger.info(f"Ejecutando cambio de moneda a {new_currency}")
        
        # Obtener configuración actual
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            raise BusinessRuleError("No se encontró configuración de empresa")
        
        current_currency = settings.currency_code
        
        # Validar cambio si no es forzado
        if not force:
            validation = await self.validate_currency_change(current_currency, new_currency, effective_date)
            if not validation.can_change:
                raise BusinessRuleError(f"No se puede cambiar la moneda: {'; '.join(validation.errors)}")
        
        # Preparar el cambio
        preparation = await self.prepare_currency_change(new_currency, effective_date, user_id)
        
        # Ejecutar el cambio en la configuración
        try:
            # Actualizar la moneda base en la configuración
            settings.currency_code = new_currency
            settings.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Cambio de moneda ejecutado exitosamente: {current_currency} -> {new_currency}")
            
            return {
                "success": True,
                "message": f"Moneda base cambiada de {current_currency} a {new_currency}",
                "previous_currency": current_currency,
                "new_currency": new_currency,
                "effective_date": effective_date.isoformat(),
                "preparation_result": preparation,
                "next_steps": preparation["required_actions"]
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error ejecutando cambio de moneda: {e}")
            raise BusinessRuleError(f"Error ejecutando cambio de moneda: {str(e)}")

    async def get_currency_change_impact(self, new_currency: str) -> Dict[str, Any]:
        """
        Obtiene información sobre el impacto de cambiar a una nueva moneda.
        """
        # Obtener configuración actual
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            raise BusinessRuleError("No se encontró configuración de empresa")
        
        current_currency = settings.currency_code
        
        # Realizar validación para obtener impacto
        validation = await self.validate_currency_change(current_currency, new_currency)
        
        return {
            "current_currency": current_currency,
            "new_currency": new_currency,
            "can_change": validation.can_change,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "impact": validation.impact_summary,
            "recommendations": [
                "Realizar backup completo de la base de datos antes del cambio",
                "Generar reportes financieros en moneda actual para referencia",
                "Configurar tasas de cambio actualizadas",
                "Notificar a todos los usuarios sobre el cambio",
                "Revisar configuración de cuentas por defecto",
                "Planificar revisión de asientos históricos si es necesario"
            ]
        }
