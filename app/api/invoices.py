"""
Invoice API endpoints for managing invoices.
Implements complete invoice workflow following Odoo pattern.
"""
import uuid
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.invoice import Invoice, InvoiceStatus, InvoiceType
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceCreateWithLines, InvoiceWithLines,
    InvoiceLineCreate, InvoiceLineResponse,
    InvoiceListResponse, InvoiceSummary,
    InvoiceCreateLegacy  # Para compatibilidad con el endpoint actual
)
from app.services.invoice_service import InvoiceService
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=InvoiceWithLines, status_code=http_status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreateWithLines,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🆕 Crear factura con líneas siguiendo patrón Odoo de IMPLEMENTAR.md
    
    Este es el endpoint principal que sigue IMPLEMENTAR.md:
    - Crea factura completa con líneas en una operación
    - Usa 'third_party_id' en lugar de 'customer_id'
    - Usa 'payment_terms_id' en lugar de 'payment_term_id'
    - Líneas con impuestos por línea (tax_ids)
    - Soporte para overrides de cuentas contables
    - Facturas inician en estado DRAFT (sin journal entry)
    
    Para crear solo header: POST /header-only
    """
    try:
        service = InvoiceService(db)
        return service.create_invoice_with_lines(invoice_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/legacy", response_model=InvoiceResponse, status_code=http_status.HTTP_201_CREATED)
def create_invoice_legacy(
    invoice_data: InvoiceCreateLegacy,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ⚠️ LEGACY: Crear factura con schema anterior (para compatibilidad)
    
    Usa el schema anterior con:
    - 'customer_id' en lugar de 'third_party_id'
    - 'payment_term_id' en lugar de 'payment_terms_id'
    - discount_percentage y tax_percentage globales
    
    RECOMENDADO: Usar POST / o POST /with-lines con el nuevo schema
    """
    try:        # Convertir schema legacy al nuevo
        new_data_dict = {
            "invoice_date": invoice_data.invoice_date,
            "due_date": invoice_data.due_date,
            "invoice_type": invoice_data.invoice_type,
            "currency_code": invoice_data.currency_code,
            "exchange_rate": invoice_data.exchange_rate,
            "description": invoice_data.description,
            "notes": invoice_data.notes,
            "third_party_id": invoice_data.customer_id,  # Mapeo legacy
            "payment_terms_id": invoice_data.payment_term_id  # Mapeo legacy
        }
        new_data = InvoiceCreate(**new_data_dict)
        
        service = InvoiceService(db)
        return service.create_invoice(new_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/header-only", response_model=InvoiceResponse, status_code=http_status.HTTP_201_CREATED)
def create_invoice_header_only(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear solo encabezado de factura (sin líneas) - Para casos especiales
    
    Crea factura en estado DRAFT sin líneas.
    Las líneas se pueden agregar después con POST /invoices/{id}/lines
    
    Usar POST / (endpoint principal) es recomendado para el flujo normal.
    """
    try:
        service = InvoiceService(db)
        return service.create_invoice(invoice_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/with-lines-alt", response_model=InvoiceWithLines, status_code=http_status.HTTP_201_CREATED)
def create_invoice_with_lines(
    invoice_data: InvoiceCreateWithLines,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear factura con líneas en una sola operación
    
    Más eficiente para facturas con múltiples productos/servicios
    """
    try:
        service = InvoiceService(db)
        return service.create_invoice_with_lines(invoice_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=InvoiceListResponse)
def get_invoices(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID (legacy, use third_party_id)"),
    third_party_id: Optional[uuid.UUID] = Query(None, description="Filter by third party ID"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by invoice status"),
    invoice_type: Optional[InvoiceType] = Query(None, description="Filter by invoice type"),
    date_from: Optional[date] = Query(None, description="Filter invoices from this date"),
    date_to: Optional[date] = Query(None, description="Filter invoices to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de facturas con filtros
    
    Permite filtrar por cliente/tercero, estado, tipo, rango de fechas, etc.
    Similar a la vista de facturas en Odoo.
    
    Parámetros de filtro:
    - third_party_id: ID del tercero (nuevo parámetro siguiendo IMPLEMENTAR.md)
    - customer_id: ID del tercero (parámetro legacy para compatibilidad)
    """
    try:
        service = InvoiceService(db)
        skip = (page - 1) * size  # Convert page/size to skip/limit
        
        # Usar third_party_id si se proporciona, sino customer_id (legacy)
        filter_third_party_id = third_party_id or customer_id
        
        return service.get_invoices(
            skip=skip,
            limit=size,
            third_party_id=filter_third_party_id,
            status=status,
            invoice_type=invoice_type,
            date_from=date_from,
            date_to=date_to
        )
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener factura por ID"""
    try:
        service = InvoiceService(db)
        return service.get_invoice(invoice_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{invoice_id}/with-lines", response_model=InvoiceWithLines)
def get_invoice_with_lines(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener factura con todas sus líneas
    
    Útil para mostrar el detalle completo de la factura
    """
    try:
        service = InvoiceService(db)
        return service.get_invoice_with_lines(invoice_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: uuid.UUID,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar factura
    
    Solo se puede actualizar si está en estado DRAFT o PENDING
    """
    try:
        service = InvoiceService(db)
        return service.update_invoice(invoice_id, invoice_data)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{invoice_id}/lines", response_model=InvoiceLineResponse, status_code=http_status.HTTP_201_CREATED)
def add_invoice_line(
    invoice_id: uuid.UUID,
    line_data: InvoiceLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Agregar línea a factura existente
    
    Permite agregar productos/servicios adicionales a una factura
    """
    try:
        service = InvoiceService(db)
        return service.add_invoice_line(invoice_id, line_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{invoice_id}/calculate-totals", response_model=InvoiceResponse)
def calculate_invoice_totals(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recalcular totales de factura
    
    Útil después de agregar/modificar líneas
    """
    try:
        service = InvoiceService(db)
        return service.calculate_invoice_totals(invoice_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{invoice_id}/post", response_model=InvoiceResponse)
def post_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Contabilizar factura (emitir)
    
    Flujo Odoo IMPLEMENTADO:
    1. Cambiar estado a POSTED
    2. Generar asiento contable automáticamente
    3. La factura queda lista para recibir pagos
    """
    try:
        service = InvoiceService(db)
        
        # Usar el método que implementa la lógica completa de Odoo
        return service.post_invoice(invoice_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/summary/statistics", response_model=InvoiceSummary)
def get_invoice_summary(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID (legacy, use third_party_id)"),
    third_party_id: Optional[uuid.UUID] = Query(None, description="Filter by third party ID"),
    invoice_type: Optional[InvoiceType] = Query(None, description="Filter by invoice type"),
    date_from: Optional[date] = Query(None, description="Filter invoices from this date"),
    date_to: Optional[date] = Query(None, description="Filter invoices to this date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener resumen estadístico de facturas
    
    Útil para dashboards y reportes ejecutivos.
    Soporta filtros por tercero (third_party_id o customer_id legacy).
    """
    try:
        # Por ahora retornamos un resumen básico
        # En el futuro esto se implementaría en el servicio
        from app.models.invoice import Invoice
        from decimal import Decimal
        
        query = db.query(Invoice)
        
        # Usar third_party_id si se proporciona, sino customer_id (legacy)
        filter_third_party_id = third_party_id or customer_id
        
        if filter_third_party_id:
            query = query.filter(Invoice.third_party_id == filter_third_party_id)
        if invoice_type:
            query = query.filter(Invoice.invoice_type == invoice_type)
        if date_from:
            query = query.filter(Invoice.invoice_date >= date_from)
        if date_to:
            query = query.filter(Invoice.invoice_date <= date_to)
            
        invoices = query.all()
        
        total_amount = Decimal(str(sum(i.total_amount or 0 for i in invoices)))
        paid_amount = Decimal(str(sum(i.paid_amount or 0 for i in invoices)))
        pending_amount = total_amount - paid_amount
          # Calcular vencidas (solo facturas contabilizadas no pagadas completamente)
        from datetime import date
        overdue_amount = Decimal(str(sum(
            i.outstanding_amount or 0 for i in invoices 
            if i.due_date and i.due_date < date.today() and i.status == InvoiceStatus.POSTED and (i.outstanding_amount or 0) > 0
        )))
        
        by_status = {}
        by_type = {}
        
        for status in InvoiceStatus:
            count = len([i for i in invoices if i.status == status])
            if count > 0:
                by_status[status.value] = count
                
        for inv_type in InvoiceType:
            count = len([i for i in invoices if i.invoice_type == inv_type])
            if count > 0:
                by_type[inv_type.value] = count
        
        return InvoiceSummary(
            total_invoices=len(invoices),
            total_amount=total_amount,
            paid_amount=paid_amount,
            pending_amount=pending_amount,
            overdue_amount=overdue_amount,
            by_status=by_status,
            by_type=by_type
        )
        
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Endpoints auxiliares

@router.get("/types/", response_model=List[dict])
def get_invoice_types():
    """Obtener tipos de factura disponibles"""
    return [{"value": t.value, "label": t.value.replace("_", " ").title()} for t in InvoiceType]


@router.get("/statuses/", response_model=List[dict])
def get_invoice_statuses():
    """Obtener estados de factura disponibles"""
    return [{"value": s.value, "label": s.value.replace("_", " ").title()} for s in InvoiceStatus]
