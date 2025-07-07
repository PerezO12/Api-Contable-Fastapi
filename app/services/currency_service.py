"""
Currency service for managing currencies and exchange rates
"""
import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.currency import Currency, ExchangeRate
from app.models.company_settings import CompanySettings
from app.schemas.currency import (
    CurrencyCreate, CurrencyUpdate, CurrencyFilter,
    ExchangeRateCreate, ExchangeRateUpdate, ExchangeRateFilter,
    CurrencyConversionRequest, CurrencyConversionResponse,
    ExchangeRateImportRequest, ExchangeRateImportResult
)
from app.utils.exceptions import NotFoundError, BusinessRuleError, ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CurrencyService:
    """
    Servicio para gestión de monedas
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_currencies(
        self,
        filters: Optional[CurrencyFilter] = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> Tuple[List[Currency], int]:
        """
        Obtener lista de monedas con filtros y paginación
        """
        query = select(Currency)
        
        # Filtros base
        if not include_inactive:
            query = query.where(Currency.is_active == True)
        
        # Aplicar filtros
        if filters:
            if filters.code:
                query = query.where(Currency.code.ilike(f"%{filters.code}%"))
            if filters.name:
                query = query.where(Currency.name.ilike(f"%{filters.name}%"))
            if filters.is_active is not None:
                query = query.where(Currency.is_active == filters.is_active)
            if filters.country_code:
                query = query.where(Currency.country_code == filters.country_code)
        
        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.scalar(count_query)
        total = total_result if total_result is not None else 0
        
        # Aplicar paginación y ordenamiento
        query = query.order_by(Currency.code).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        currencies = result.scalars().all()
        
        return list(currencies), total
    
    async def get_currency_by_id(self, currency_id: uuid.UUID) -> Currency:
        """
        Obtener moneda por ID
        """
        query = select(Currency).where(Currency.id == currency_id)
        result = await self.db.execute(query)
        currency = result.scalar_one_or_none()
        
        if not currency:
            raise NotFoundError(f"Moneda con ID {currency_id} no encontrada")
        
        return currency
    
    async def get_currency_by_code(self, code: str) -> Currency:
        """
        Obtener moneda por código
        """
        query = select(Currency).where(Currency.code == code.upper())
        result = await self.db.execute(query)
        currency = result.scalar_one_or_none()
        
        if not currency:
            raise NotFoundError(f"Moneda con código {code} no encontrada")
        
        return currency
    
    async def create_currency(self, currency_data: CurrencyCreate) -> Currency:
        """
        Crear nueva moneda
        """
        # Verificar que no exista el código
        existing = await self.db.execute(
            select(Currency).where(Currency.code == currency_data.code.upper())
        )
        if existing.scalar_one_or_none():
            raise BusinessRuleError(f"Ya existe una moneda con código {currency_data.code}")
        
        currency = Currency(**currency_data.model_dump())
        self.db.add(currency)
        await self.db.commit()
        await self.db.refresh(currency)
        
        # Crear exchange rate automático con valor 1.0
        await self._create_default_exchange_rate(currency)
        
        logger.info(f"Moneda creada: {currency.code} - {currency.name}")
        return currency
    
    async def _create_default_exchange_rate(self, currency: Currency) -> None:
        """
        Crear exchange rate por defecto para una nueva moneda
        """
        from app.schemas.currency import ExchangeRateCreate
        
        # Solo crear si no es la moneda base del sistema
        base_currency = await self.get_base_currency()
        if base_currency and currency.code == base_currency.code:
            return  # No crear exchange rate para la moneda base
        
        # Crear exchange rate con valor 1.0 para la fecha actual
        exchange_rate_data = ExchangeRateCreate(
            currency_id=currency.id,
            rate=Decimal('1.0'),
            rate_date=date.today(),
            source="system",
            provider="default",
            notes=f"Tipo de cambio inicial para {currency.code}"
        )
        
        exchange_rate = ExchangeRate(**exchange_rate_data.model_dump())
        self.db.add(exchange_rate)
        await self.db.commit()
        
        logger.info(f"Exchange rate inicial creado para {currency.code}: 1.0")
    
    async def update_currency(self, currency_id: uuid.UUID, currency_data: CurrencyUpdate) -> Currency:
        """
        Actualizar moneda
        """
        currency = await self.get_currency_by_id(currency_id)
        
        # Actualizar campos
        update_data = currency_data.model_dump(exclude_unset=True)
        old_is_active = currency.is_active
        
        for field, value in update_data.items():
            setattr(currency, field, value)
        
        await self.db.commit()
        await self.db.refresh(currency)
        
        # Si el estado de activo cambió, verificar si necesitamos crear exchange rate
        if 'is_active' in update_data:
            new_is_active = update_data['is_active']
            if not old_is_active and new_is_active:
                # Se activó la moneda, verificar si tiene exchange rate
                await self._ensure_exchange_rate_exists(currency)
        
        logger.info(f"Moneda actualizada: {currency.code}")
        return currency
    
    async def _ensure_exchange_rate_exists(self, currency: Currency) -> None:
        """
        Asegurar que existe al menos un exchange rate para la moneda
        """
        # Verificar si ya tiene exchange rates
        existing_count = await self.db.scalar(
            select(func.count()).where(ExchangeRate.currency_id == currency.id)
        )
        
        if existing_count == 0:
            # No tiene exchange rates, crear uno por defecto
            await self._create_default_exchange_rate(currency)
    
    async def delete_currency(self, currency_id: uuid.UUID) -> bool:
        """
        Eliminar moneda (soft delete)
        """
        currency = await self.get_currency_by_id(currency_id)
        
        # Verificar que no sea la moneda base
        base_currency = await self.get_base_currency()
        if base_currency and currency.id == base_currency.id:
            raise BusinessRuleError("No se puede eliminar la moneda base del sistema")
        
        # Verificar que no tenga tipos de cambio asociados
        exchange_rates_count_result = await self.db.scalar(
            select(func.count()).where(ExchangeRate.currency_id == currency_id)
        )
        exchange_rates_count = exchange_rates_count_result if exchange_rates_count_result is not None else 0
        
        if exchange_rates_count > 0:
            raise BusinessRuleError("No se puede eliminar una moneda que tiene tipos de cambio asociados")
        
        currency.is_active = False
        await self.db.commit()
        
        logger.info(f"Moneda desactivada: {currency.code}")
        return True
    
    async def get_base_currency(self) -> Optional[Currency]:
        """
        Obtener la moneda base del sistema
        """
        # Buscar en configuración de empresa
        settings_query = select(CompanySettings).options(
            joinedload(CompanySettings.base_currency)
        ).where(CompanySettings.is_active == True)
        
        result = await self.db.execute(settings_query)
        settings = result.scalar_one_or_none()
        
        if settings and settings.base_currency:
            return settings.base_currency
        
        # Fallback: buscar por currency_code
        if settings and settings.currency_code:
            try:
                return await self.get_currency_by_code(settings.currency_code)
            except NotFoundError:
                pass
        
        # Último fallback: USD si existe
        try:
            return await self.get_currency_by_code("USD")
        except NotFoundError:
            return None
    
    async def set_base_currency(self, currency_code: str) -> Currency:
        """
        Establecer la moneda base del sistema
        """
        currency = await self.get_currency_by_code(currency_code)
        
        # Buscar o crear configuración de empresa
        settings_query = select(CompanySettings).where(CompanySettings.is_active == True)
        result = await self.db.execute(settings_query)
        settings = result.scalar_one_or_none()
        
        if not settings:
            raise BusinessRuleError("No existe configuración de empresa activa")
        
        settings.base_currency_id = currency.id
        settings.currency_code = currency.code  # Mantener compatibilidad
        
        await self.db.commit()
        
        logger.info(f"Moneda base establecida: {currency.code}")
        return currency


class ExchangeRateService:
    """
    Servicio para gestión de tipos de cambio
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_exchange_rates(
        self,
        filters: Optional[ExchangeRateFilter] = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive_currencies: bool = False
    ) -> Tuple[List[ExchangeRate], int]:
        """
        Obtener lista de tipos de cambio con filtros
        """
        # Always join with Currency table since we need it for ordering
        query = select(ExchangeRate).options(
            joinedload(ExchangeRate.currency)
        ).join(Currency)
        
        # Por defecto, solo mostrar exchange rates de monedas activas
        if not include_inactive_currencies:
            query = query.where(Currency.is_active == True)
        
        # Aplicar filtros
        if filters:
            if filters.currency_code:
                query = query.where(
                    Currency.code.ilike(f"%{filters.currency_code}%")
                )
            if filters.date_from:
                query = query.where(ExchangeRate.rate_date >= filters.date_from)
            if filters.date_to:
                query = query.where(ExchangeRate.rate_date <= filters.date_to)
            if filters.source:
                query = query.where(ExchangeRate.source.ilike(f"%{filters.source}%"))
            if filters.provider:
                query = query.where(ExchangeRate.provider.ilike(f"%{filters.provider}%"))
        
        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.scalar(count_query)
        total = total_result if total_result is not None else 0
        
        # Aplicar paginación y ordenamiento
        query = query.order_by(desc(ExchangeRate.rate_date), Currency.code).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        exchange_rates = result.scalars().all()
        
        return list(exchange_rates), total
    
    async def get_exchange_rate_by_id(self, exchange_rate_id: uuid.UUID) -> ExchangeRate:
        """
        Obtener tipo de cambio por ID
        """
        query = select(ExchangeRate).options(
            joinedload(ExchangeRate.currency)
        ).where(ExchangeRate.id == exchange_rate_id)
        
        result = await self.db.execute(query)
        exchange_rate = result.scalar_one_or_none()
        
        if not exchange_rate:
            raise NotFoundError(f"Tipo de cambio con ID {exchange_rate_id} no encontrado")
        
        return exchange_rate
    
    async def get_latest_exchange_rate(
        self, 
        currency_code: str, 
        reference_date: Optional[date] = None
    ) -> Optional[ExchangeRate]:
        """
        Obtener el tipo de cambio más reciente para una moneda
        """
        if reference_date is None:
            reference_date = date.today()
        
        query = select(ExchangeRate).options(
            joinedload(ExchangeRate.currency)
        ).join(Currency).where(
            and_(
                Currency.code == currency_code.upper(),
                ExchangeRate.rate_date <= reference_date
            )
        ).order_by(desc(ExchangeRate.rate_date)).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_exchange_rate(self, exchange_rate_data: ExchangeRateCreate) -> ExchangeRate:
        """
        Crear nuevo tipo de cambio
        """
        # Verificar que la moneda existe
        currency_query = select(Currency).where(Currency.id == exchange_rate_data.currency_id)
        currency = await self.db.scalar(currency_query)
        if not currency:
            raise NotFoundError(f"Moneda con ID {exchange_rate_data.currency_id} no encontrada")
        
        # Verificar que no exista tipo de cambio para esa fecha
        existing_query = select(ExchangeRate).where(
            and_(
                ExchangeRate.currency_id == exchange_rate_data.currency_id,
                ExchangeRate.rate_date == exchange_rate_data.rate_date
            )
        )
        existing = await self.db.scalar(existing_query)
        if existing:
            raise BusinessRuleError(
                f"Ya existe un tipo de cambio para {currency.code} en la fecha {exchange_rate_data.rate_date}"
            )
        
        exchange_rate = ExchangeRate(**exchange_rate_data.model_dump())
        self.db.add(exchange_rate)
        await self.db.commit()
        await self.db.refresh(exchange_rate, ["currency"])
        
        logger.info(f"Tipo de cambio creado: {currency.code} = {exchange_rate.rate} ({exchange_rate.rate_date})")
        return exchange_rate
    
    async def update_exchange_rate(
        self, 
        exchange_rate_id: uuid.UUID, 
        exchange_rate_data: ExchangeRateUpdate
    ) -> ExchangeRate:
        """
        Actualizar tipo de cambio
        """
        exchange_rate = await self.get_exchange_rate_by_id(exchange_rate_id)
        
        # Actualizar campos
        update_data = exchange_rate_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(exchange_rate, field, value)
        
        await self.db.commit()
        await self.db.refresh(exchange_rate, ["currency"])
        
        logger.info(f"Tipo de cambio actualizado: {exchange_rate.currency.code}")
        return exchange_rate
    
    async def delete_exchange_rate(self, exchange_rate_id: uuid.UUID) -> bool:
        """
        Eliminar tipo de cambio
        """
        exchange_rate = await self.get_exchange_rate_by_id(exchange_rate_id)
        
        # Verificar que no esté siendo usado en transacciones
        # TODO: Implementar verificación cuando se agreguen las transacciones
        
        await self.db.delete(exchange_rate)
        await self.db.commit()
        
        logger.info(f"Tipo de cambio eliminado: {exchange_rate.currency.code} ({exchange_rate.rate_date})")
        return True


class CurrencyConversionService:
    """
    Servicio para conversión de monedas
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.currency_service = CurrencyService(db)
        self.exchange_rate_service = ExchangeRateService(db)
    
    async def convert_currency(self, conversion_request: CurrencyConversionRequest) -> CurrencyConversionResponse:
        """
        Convertir entre monedas
        """
        from_code = conversion_request.from_currency_code.upper()
        to_code = conversion_request.to_currency_code.upper()
        conversion_date = conversion_request.conversion_date or date.today()
        
        # Si es la misma moneda, no hay conversión
        if from_code == to_code:
            return CurrencyConversionResponse(
                original_amount=conversion_request.amount,
                converted_amount=conversion_request.amount,
                from_currency_code=from_code,
                to_currency_code=to_code,
                exchange_rate=Decimal('1.0'),
                conversion_date=conversion_date,
                rate_source="same_currency"
            )
        
        # Obtener moneda base
        base_currency = await self.currency_service.get_base_currency()
        if not base_currency:
            raise BusinessRuleError("No hay moneda base configurada en el sistema")
        
        base_code = base_currency.code
        
        # Caso 1: Conversión desde moneda base a otra moneda
        if from_code == base_code and to_code != base_code:
            rate = await self.exchange_rate_service.get_latest_exchange_rate(to_code, conversion_date)
            if not rate:
                raise NotFoundError(f"No se encontró tipo de cambio para {to_code} en {conversion_date}")
            
            converted_amount = rate.convert_from_base(conversion_request.amount)
            exchange_rate_value = rate.rate
            
        # Caso 2: Conversión desde otra moneda a moneda base
        elif from_code != base_code and to_code == base_code:
            rate = await self.exchange_rate_service.get_latest_exchange_rate(from_code, conversion_date)
            if not rate:
                raise NotFoundError(f"No se encontró tipo de cambio para {from_code} en {conversion_date}")
            
            converted_amount = rate.convert_to_base(conversion_request.amount)
            exchange_rate_value = rate.rate
            
        # Caso 3: Conversión entre dos monedas extranjeras (vía moneda base)
        else:
            from_rate = await self.exchange_rate_service.get_latest_exchange_rate(from_code, conversion_date)
            to_rate = await self.exchange_rate_service.get_latest_exchange_rate(to_code, conversion_date)
            
            if not from_rate:
                raise NotFoundError(f"No se encontró tipo de cambio para {from_code} en {conversion_date}")
            if not to_rate:
                raise NotFoundError(f"No se encontró tipo de cambio para {to_code} en {conversion_date}")
            
            # Convertir a moneda base y luego a moneda destino
            base_amount = from_rate.convert_to_base(conversion_request.amount)
            converted_amount = to_rate.convert_from_base(base_amount)
            exchange_rate_value = from_rate.rate / to_rate.rate
        
        return CurrencyConversionResponse(
            original_amount=conversion_request.amount,
            converted_amount=converted_amount,
            from_currency_code=from_code,
            to_currency_code=to_code,
            exchange_rate=exchange_rate_value,
            conversion_date=conversion_date,
            rate_source="database"
        )
    
    async def validate_exchange_rate_exists(
        self, 
        currency_code: str, 
        transaction_date: date
    ) -> bool:
        """
        Validar que existe tipo de cambio para una moneda en una fecha
        """
        try:
            rate = await self.exchange_rate_service.get_latest_exchange_rate(currency_code, transaction_date)
            return rate is not None
        except Exception:
            return False
    
    async def get_exchange_rate_for_transaction(
        self, 
        currency_code: str, 
        transaction_date: date
    ) -> ExchangeRate:
        """
        Obtener tipo de cambio para una transacción específica
        """
        rate = await self.exchange_rate_service.get_latest_exchange_rate(currency_code, transaction_date)
        if not rate:
            raise NotFoundError(
                f"No se encontró tipo de cambio para {currency_code} en {transaction_date} "
                f"o fechas anteriores. Debe cargar el tipo de cambio antes de procesar la transacción."
            )
        return rate
