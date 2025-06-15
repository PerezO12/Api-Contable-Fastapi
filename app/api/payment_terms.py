import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.utils.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.services.payment_terms_service import PaymentTermsService
from app.schemas.payment_terms import (
    PaymentTermsCreate, PaymentTermsUpdate, PaymentTermsRead, PaymentTermsDetail,
    PaymentTermsSummary, PaymentTermsFilter, PaymentCalculationRequest,
    PaymentCalculationResponse
)


router = APIRouter(prefix="/payment-terms", tags=["Condiciones de Pago"])


@router.post(
    "/",
    response_model=PaymentTermsDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Crear condiciones de pago",
    description="Crea nuevas condiciones de pago con su cronograma de pagos"
)
async def create_payment_terms(
    payment_terms_data: PaymentTermsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaymentTermsDetail:
    """Crear nuevas condiciones de pago"""
    try:
        service = PaymentTermsService(db)
        payment_terms = await service.create_payment_terms(payment_terms_data)
        return PaymentTermsDetail.model_validate(payment_terms)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[PaymentTermsSummary],
    summary="Listar condiciones de pago",
    description="Obtiene una lista paginada de condiciones de pago con filtros opcionales"
)
async def list_payment_terms(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    search_text: Optional[str] = Query(None, description="Buscar en código, nombre o descripción"),
    min_days: Optional[int] = Query(None, ge=0, description="Días mínimos del primer pago"),
    max_days: Optional[int] = Query(None, ge=0, description="Días máximos del último pago"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[PaymentTermsSummary]:
    """Listar condiciones de pago con filtros"""
    try:
        filters = PaymentTermsFilter(
            is_active=is_active,
            search_text=search_text,
            min_days=min_days,
            max_days=max_days
        )
        
        service = PaymentTermsService(db)
        payment_terms, total = await service.list_payment_terms(filters, skip, limit)
        return [PaymentTermsSummary.model_validate(pt) for pt in payment_terms]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/active",
    response_model=List[PaymentTermsRead],
    summary="Obtener condiciones de pago activas",
    description="Obtiene todas las condiciones de pago activas para uso en formularios"
)
async def get_active_payment_terms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[PaymentTermsRead]:
    """Obtener condiciones de pago activas"""
    try:
        service = PaymentTermsService(db)
        payment_terms = await service.get_active_payment_terms()
        return [PaymentTermsRead.model_validate(pt) for pt in payment_terms]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/{payment_terms_id}",
    response_model=PaymentTermsDetail,
    summary="Obtener condiciones de pago por ID",
    description="Obtiene los detalles completos de las condiciones de pago incluyendo su cronograma"
)
async def get_payment_terms_by_id(
    payment_terms_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaymentTermsDetail:
    """Obtener condiciones de pago por ID"""
    try:
        service = PaymentTermsService(db)
        payment_terms = await service.get_payment_terms_by_id(payment_terms_id)
        return PaymentTermsDetail.model_validate(payment_terms)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/code/{code}",
    response_model=PaymentTermsDetail,
    summary="Obtener condiciones de pago por código",
    description="Obtiene las condiciones de pago usando su código único"
)
async def get_payment_terms_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaymentTermsDetail:
    """Obtener condiciones de pago por código"""
    try:
        service = PaymentTermsService(db)
        payment_terms = await service.get_payment_terms_by_code(code)
        return PaymentTermsDetail.model_validate(payment_terms)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.put(
    "/{payment_terms_id}",
    response_model=PaymentTermsDetail,
    summary="Actualizar condiciones de pago",
    description="Actualiza las condiciones de pago y opcionalmente su cronograma"
)
async def update_payment_terms(
    payment_terms_id: uuid.UUID,
    payment_terms_data: PaymentTermsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaymentTermsDetail:
    """Actualizar condiciones de pago"""
    try:
        service = PaymentTermsService(db)
        payment_terms = await service.update_payment_terms(payment_terms_id, payment_terms_data)
        return PaymentTermsDetail.model_validate(payment_terms)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.patch(
    "/{payment_terms_id}/toggle-active",
    response_model=PaymentTermsRead,
    summary="Alternar estado activo",
    description="Alterna el estado activo/inactivo de las condiciones de pago"
)
async def toggle_payment_terms_active(
    payment_terms_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaymentTermsRead:
    """Alternar estado activo de condiciones de pago"""
    try:
        service = PaymentTermsService(db)
        payment_terms = await service.toggle_active_status(payment_terms_id)
        return PaymentTermsRead.model_validate(payment_terms)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.delete(
    "/{payment_terms_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar condiciones de pago",
    description="Elimina las condiciones de pago si no están en uso"
)
async def delete_payment_terms(
    payment_terms_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Eliminar condiciones de pago"""
    try:
        service = PaymentTermsService(db)
        await service.delete_payment_terms(payment_terms_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post(
    "/calculate",
    response_model=PaymentCalculationResponse,
    summary="Calcular cronograma de pagos",
    description="Calcula fechas y montos de pago basados en condiciones de pago específicas"
)
async def calculate_payment_schedule(
    request: PaymentCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaymentCalculationResponse:
    """Calcular cronograma de pagos"""
    try:
        service = PaymentTermsService(db)
        calculation = await service.calculate_payment_dates(request)
        return calculation
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/{payment_terms_id}/validate",
    response_model=Dict[str, Any],
    summary="Validar condiciones de pago",
    description="Valida las condiciones de pago y retorna detalles de la validación"
)
async def validate_payment_terms(
    payment_terms_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validar condiciones de pago"""
    try:
        service = PaymentTermsService(db)
        validation_result = await service.validate_payment_terms(payment_terms_id)
        return validation_result
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
