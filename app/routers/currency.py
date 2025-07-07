"""
API endpoints for currency and exchange rate management
"""
import uuid
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.currency import (
    CurrencyCreate, CurrencyUpdate, CurrencyRead, CurrencyList, CurrencySummary, CurrencyFilter,
    ExchangeRateCreate, ExchangeRateUpdate, ExchangeRateRead, ExchangeRateList, ExchangeRateFilter,
    CurrencyConversionRequest, CurrencyConversionResponse,
    ExchangeRateImportRequest, ExchangeRateImportResult
)
from app.services.currency_service import CurrencyService, ExchangeRateService, CurrencyConversionService
from app.utils.exceptions import NotFoundError, BusinessRuleError, ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Currencies"])


# === EXCHANGE RATE MANAGEMENT (GENERAL) ===
# Note: These routes MUST come first to avoid conflicts with currency-specific routes

exchange_rate_router = APIRouter(tags=["Exchange Rates"])


@exchange_rate_router.get("/exchange-rates", response_model=ExchangeRateList)
async def get_exchange_rates(
    currency_code: Optional[str] = Query(None, description="Filtrar por código de moneda"),
    date_from: Optional[date] = Query(None, description="Fecha desde"),
    date_to: Optional[date] = Query(None, description="Fecha hasta"),
    source: Optional[str] = Query(None, description="Filtrar por origen"),
    provider: Optional[str] = Query(None, description="Filtrar por proveedor"),
    include_inactive_currencies: bool = Query(False, description="Incluir monedas inactivas"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=1000, description="Tamaño de página"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de tipos de cambio con filtros
    """
    try:
        service = ExchangeRateService(db)
        
        filters = ExchangeRateFilter(
            currency_code=currency_code,
            date_from=date_from,
            date_to=date_to,
            source=source,
            provider=provider
        )
        
        skip = (page - 1) * size
        exchange_rates, total = await service.get_exchange_rates(
            filters=filters,
            skip=skip,
            limit=size,
            include_inactive_currencies=include_inactive_currencies
        )
        
        pages = (total + size - 1) // size
        
        return ExchangeRateList(
            exchange_rates=[ExchangeRateRead.model_validate(er) for er in exchange_rates],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo tipos de cambio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@exchange_rate_router.post("/exchange-rates", response_model=ExchangeRateRead, status_code=status.HTTP_201_CREATED)
async def create_exchange_rate(
    exchange_rate_data: ExchangeRateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear nuevo tipo de cambio
    """
    try:
        service = ExchangeRateService(db)
        exchange_rate = await service.create_exchange_rate(exchange_rate_data)
        return ExchangeRateRead.model_validate(exchange_rate)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando tipo de cambio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@exchange_rate_router.get("/exchange-rates/{exchange_rate_id}", response_model=ExchangeRateRead)
async def get_exchange_rate(
    exchange_rate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener tipo de cambio por ID
    """
    try:
        service = ExchangeRateService(db)
        exchange_rate = await service.get_exchange_rate_by_id(exchange_rate_id)
        return ExchangeRateRead.model_validate(exchange_rate)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo tipo de cambio {exchange_rate_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@exchange_rate_router.put("/exchange-rates/{exchange_rate_id}", response_model=ExchangeRateRead)
async def update_exchange_rate(
    exchange_rate_id: uuid.UUID,
    exchange_rate_data: ExchangeRateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar tipo de cambio
    """
    try:
        service = ExchangeRateService(db)
        exchange_rate = await service.update_exchange_rate(exchange_rate_id, exchange_rate_data)
        return ExchangeRateRead.model_validate(exchange_rate)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error actualizando tipo de cambio {exchange_rate_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@exchange_rate_router.delete("/exchange-rates/{exchange_rate_id}")
async def delete_exchange_rate(
    exchange_rate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar tipo de cambio
    """
    try:
        service = ExchangeRateService(db)
        await service.delete_exchange_rate(exchange_rate_id)
        return {"message": "Tipo de cambio eliminado exitosamente"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error eliminando tipo de cambio {exchange_rate_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# Include exchange rate router FIRST to avoid path conflicts
router.include_router(exchange_rate_router)


# === CURRENCY ENDPOINTS ===

@router.get("/", response_model=CurrencyList)
async def get_currencies(
    code: Optional[str] = Query(None, description="Filtrar por código de moneda"),
    name: Optional[str] = Query(None, description="Filtrar por nombre de moneda"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    country_code: Optional[str] = Query(None, description="Filtrar por código de país"),
    include_inactive: bool = Query(False, description="Incluir monedas inactivas"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=1000, description="Tamaño de página"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de monedas con filtros y paginación
    """
    try:
        service = CurrencyService(db)
        
        filters = CurrencyFilter(
            code=code,
            name=name,
            is_active=is_active,
            country_code=country_code
        )
        
        skip = (page - 1) * size
        currencies, total = await service.get_currencies(
            filters=filters,
            skip=skip,
            limit=size,
            include_inactive=include_inactive
        )
        
        pages = (total + size - 1) // size
        
        return CurrencyList(
            currencies=[CurrencyRead.model_validate(c) for c in currencies],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo monedas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/summary", response_model=List[CurrencySummary])
async def get_currencies_summary(
    active_only: bool = Query(True, description="Solo monedas activas"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista resumida de monedas para dropdowns
    """
    try:
        service = CurrencyService(db)
        currencies, _ = await service.get_currencies(
            include_inactive=not active_only,
            limit=1000  # Límite alto para obtener todas
        )
        
        return [CurrencySummary.model_validate(c) for c in currencies]
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de monedas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/base", response_model=Optional[CurrencyRead])
async def get_base_currency(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener la moneda base del sistema
    """
    try:
        service = CurrencyService(db)
        base_currency = await service.get_base_currency()
        
        if base_currency:
            return CurrencyRead.model_validate(base_currency)
        return None
        
    except Exception as e:
        logger.error(f"Error obteniendo moneda base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/base/{currency_code}")
async def set_base_currency(
    currency_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Establecer la moneda base del sistema
    """
    try:
        service = CurrencyService(db)
        currency = await service.set_base_currency(currency_code.upper())
        
        return {
            "message": f"Moneda base establecida: {currency.code}",
            "currency": CurrencyRead.model_validate(currency)
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error estableciendo moneda base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{currency_id}", response_model=CurrencyRead)
async def get_currency(
    currency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener moneda por ID
    """
    try:
        service = CurrencyService(db)
        currency = await service.get_currency_by_id(currency_id)
        return CurrencyRead.model_validate(currency)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo moneda {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/", response_model=CurrencyRead, status_code=status.HTTP_201_CREATED)
async def create_currency(
    currency_data: CurrencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear nueva moneda
    """
    try:
        service = CurrencyService(db)
        currency = await service.create_currency(currency_data)
        return CurrencyRead.model_validate(currency)
        
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando moneda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{currency_id}", response_model=CurrencyRead)
async def update_currency(
    currency_id: uuid.UUID,
    currency_data: CurrencyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar moneda
    """
    try:
        service = CurrencyService(db)
        currency = await service.update_currency(currency_id, currency_data)
        return CurrencyRead.model_validate(currency)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error actualizando moneda {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{currency_id}")
async def delete_currency(
    currency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar moneda (soft delete)
    """
    try:
        service = CurrencyService(db)
        await service.delete_currency(currency_id)
        return {"message": "Moneda eliminada exitosamente"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error eliminando moneda {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# === CURRENCY-SPECIFIC EXCHANGE RATE ENDPOINTS ===

@router.get("/{currency_id}/exchange-rates", response_model=ExchangeRateList)
async def get_exchange_rates_for_currency(
    currency_id: uuid.UUID,
    date_from: Optional[date] = Query(None, description="Fecha desde"),
    date_to: Optional[date] = Query(None, description="Fecha hasta"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=1000, description="Tamaño de página"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener tipos de cambio para una moneda específica
    """
    try:
        # Verificar que la moneda existe
        currency_service = CurrencyService(db)
        currency = await currency_service.get_currency_by_id(currency_id)
        
        service = ExchangeRateService(db)
        
        filters = ExchangeRateFilter(
            currency_code=currency.code,
            date_from=date_from,
            date_to=date_to
        )
        
        skip = (page - 1) * size
        exchange_rates, total = await service.get_exchange_rates(
            filters=filters,
            skip=skip,
            limit=size
        )
        
        pages = (total + size - 1) // size
        
        return ExchangeRateList(
            exchange_rates=[ExchangeRateRead.model_validate(er) for er in exchange_rates],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo tipos de cambio para moneda {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{currency_id}/exchange-rates/latest", response_model=Optional[ExchangeRateRead])
async def get_latest_exchange_rate(
    currency_id: uuid.UUID,
    reference_date: Optional[date] = Query(None, description="Fecha de referencia (por defecto hoy)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener el tipo de cambio más reciente para una moneda
    """
    try:
        # Verificar que la moneda existe
        currency_service = CurrencyService(db)
        currency = await currency_service.get_currency_by_id(currency_id)
        
        service = ExchangeRateService(db)
        exchange_rate = await service.get_latest_exchange_rate(
            currency.code, 
            reference_date or date.today()
        )
        
        if exchange_rate:
            return ExchangeRateRead.model_validate(exchange_rate)
        return None
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo último tipo de cambio para moneda {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# === CONVERSION ENDPOINTS ===

conversion_router = APIRouter(prefix="/convert", tags=["Currency Conversion"])


@conversion_router.post("/", response_model=CurrencyConversionResponse)
async def convert_currency(
    conversion_request: CurrencyConversionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Convertir importe entre monedas
    """
    try:
        service = CurrencyConversionService(db)
        result = await service.convert_currency(conversion_request)
        return result
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error convirtiendo moneda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# Include conversion router in main router
router.include_router(conversion_router)
