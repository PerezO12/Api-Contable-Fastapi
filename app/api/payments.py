"""
Payment API endpoints for managing payments.
Implements complete payment workflow following Odoo pattern.
"""
import uuid
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.payment import PaymentStatus, PaymentType
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse,
    PaymentListResponse, PaymentSummary
)
from app.services.payment_service import PaymentService
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=PaymentResponse, status_code=http_status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear un nuevo pago
    
    Flujo Odoo:
    1. Cliente creado previamente
    2. Crear pago en estado DRAFT
    3. Confirmar pago para generar asiento contable
    4. Asignar a facturas específicas
    """
    try:
        service = PaymentService(db)
        return service.create_payment(payment_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=PaymentListResponse)
def get_payments(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    date_from: Optional[date] = Query(None, description="Filter payments from this date"),
    date_to: Optional[date] = Query(None, description="Filter payments to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de pagos con filtros
    
    Permite filtrar por cliente, estado, rango de fechas, etc.
    Similar a la vista de pagos en Odoo.
    """
    try:
        service = PaymentService(db)
        return service.get_payments(
            customer_id=customer_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener pago por ID"""
    try:
        service = PaymentService(db)
        return service.get_payment(payment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: uuid.UUID,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar pago
    
    Solo se puede actualizar si está en estado DRAFT o PENDING
    """
    try:
        service = PaymentService(db)
        return service.update_payment(payment_id, payment_data)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{payment_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar pago
    
    Solo se puede eliminar si está en estado DRAFT
    """
    try:
        service = PaymentService(db)
        service.delete_payment(payment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirmar pago
    
    Flujo Odoo:
    1. Cambiar estado a CONFIRMED
    2. Generar asiento contable automáticamente
    3. El pago queda listo para ser asignado a facturas
    
    ✅ IMPLEMENTADO: Generación automática de asiento contable
    """
    try:
        service = PaymentService(db)
        
        # ✅ IMPLEMENTADO: Generación automática de asiento contable
        # Siguiendo el patrón de Odoo:
        # Para pagos de cliente (cobro):
        #   - DEBE: Cuenta de banco/caja
        #   - HABER: Cuenta de clientes
        # Para pagos a proveedor:
        #   - DEBE: Cuenta de proveedores 
        #   - HABER: Cuenta de banco/caja
        
        # Usar el nuevo método que incluye creación automática de asiento
        return service.confirm_payment_with_journal_entry(payment_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/summary/statistics", response_model=PaymentSummary)
def get_payment_summary(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID"),
    date_from: Optional[date] = Query(None, description="Filter payments from this date"),
    date_to: Optional[date] = Query(None, description="Filter payments to this date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener resumen estadístico de pagos
    
    Útil para dashboards y reportes ejecutivos    """
    try:
        service = PaymentService(db)
        return service.get_payment_summary()
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Endpoints adicionales para workflow completo

@router.get("/types/", response_model=List[dict])
def get_payment_types():
    """Obtener tipos de pago disponibles"""
    return [{"value": t.value, "label": t.value.replace("_", " ").title()} for t in PaymentType]


@router.get("/statuses/", response_model=List[dict])
def get_payment_statuses():
    """Obtener estados de pago disponibles"""
    return [{"value": s.value, "label": s.value.replace("_", " ").title()} for s in PaymentStatus]
