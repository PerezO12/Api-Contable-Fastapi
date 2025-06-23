"""
Invoice API endpoints for managing invoices.
Implements complete invoice workflow following Odoo pattern.
"""
import uuid
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
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
    InvoiceCreateLegacy,  # Para compatibilidad con el endpoint actual
    InvoiceCancelRequest, InvoiceResetToDraftRequest, InvoicePostRequest,
    # Bulk operation schemas
    BulkInvoicePostRequest, BulkInvoiceCancelRequest, 
    BulkInvoiceResetToDraftRequest, BulkInvoiceDeleteRequest,
    BulkOperationResult
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
    # Parámetros de paginación
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=200, description="Page size"),
    
    # Filtros básicos
    third_party_id: Optional[uuid.UUID] = Query(None, description="Filter by third party ID"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by invoice status"),
    invoice_type: Optional[InvoiceType] = Query(None, description="Filter by invoice type"),
    currency_code: Optional[str] = Query(None, description="Filter by currency code"),
    created_by_id: Optional[uuid.UUID] = Query(None, description="Filter by user who created the invoice"),
    
    # Filtros de fecha
    date_from: Optional[date] = Query(None, description="Filter invoices from this date (inclusive)"),
    date_to: Optional[date] = Query(None, description="Filter invoices to this date (inclusive)"),
    
    # Filtros de búsqueda de texto
    invoice_number: Optional[str] = Query(None, description="Search by invoice number (partial match)"),
    third_party_name: Optional[str] = Query(None, description="Search by third party name (partial match)"),
    description: Optional[str] = Query(None, description="Search by description (partial match)"),
    reference: Optional[str] = Query(None, description="Search by internal or external reference (partial match)"),
    
    # Filtros de monto
    amount_from: Optional[Decimal] = Query(None, description="Minimum total amount (inclusive)"),
    amount_to: Optional[Decimal] = Query(None, description="Maximum total amount (inclusive)"),
    
    # Ordenamiento
    sort_by: Optional[str] = Query("invoice_date", description="Field to sort by (invoice_date, number, total_amount, status, created_at, due_date)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
    
    # Parámetro legacy para compatibilidad
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID (legacy, use third_party_id)"),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de facturas con filtros avanzados
    
    Endpoint mejorado para búsqueda flexible de facturas con múltiples criterios:
    
    **Filtros Básicos:**
    - third_party_id: Tercero específico
    - status: Estado de la factura (DRAFT, POSTED, CANCELLED, etc.)
    - invoice_type: Tipo de factura (CUSTOMER_INVOICE, SUPPLIER_INVOICE, etc.)
    - currency_code: Código de moneda (COP, USD, EUR)
    - created_by_id: Usuario que creó la factura
    
    **Filtros de Fecha:**
    - date_from: Desde fecha (inclusive) - permite filtrar solo desde una fecha
    - date_to: Hasta fecha (inclusive) - permite filtrar solo hasta una fecha
    - Ambos pueden usarse juntos para un rango específico
    
    **Búsquedas de Texto:**
    - invoice_number: Número de factura (búsqueda parcial)
    - third_party_name: Nombre del tercero (búsqueda parcial)
    - description: Descripción de la factura (búsqueda parcial)
    - reference: Referencia interna o externa (búsqueda parcial)
    
    **Filtros de Monto:**
    - amount_from: Monto mínimo (inclusive)
    - amount_to: Monto máximo (inclusive)
    
    **Ordenamiento:**
    - sort_by: Campo de ordenamiento (por defecto: invoice_date)
    - sort_order: Dirección (asc/desc, por defecto: desc)
    
    **Ejemplos de uso:**
    - `/invoices?invoice_number=FAC-001` - Buscar facturas que contengan "FAC-001"
    - `/invoices?date_from=2024-01-01&date_to=2024-12-31` - Facturas del año 2024
    - `/invoices?date_from=2024-01-01` - Facturas desde enero 2024
    - `/invoices?third_party_name=CLIENTE` - Facturas de terceros que contengan "CLIENTE"
    - `/invoices?amount_from=1000000&sort_by=total_amount&sort_order=desc` - Facturas mayores a $1M ordenadas por monto
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
            date_to=date_to,
            invoice_number=invoice_number,
            third_party_name=third_party_name,
            description=description,
            reference=reference,
            amount_from=amount_from,
            amount_to=amount_to,
            currency_code=currency_code,
            created_by_id=created_by_id,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ================================
# BULK OPERATIONS ENDPOINTS
# ================================

@router.post("/bulk/validate", response_model=dict)
def validate_bulk_operation(
    operation: str = Query(..., description="Operation to validate: post, cancel, reset, delete"),
    invoice_ids: List[uuid.UUID] = Query(..., description="List of invoice IDs to validate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validar si las facturas pueden ser procesadas en una operación bulk específica
    
    No realiza cambios, solo valida las precondiciones.
    Útil para mostrar advertencias en el frontend antes de ejecutar la operación.
    """
    try:
        if len(invoice_ids) > 100:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, 
                              detail="Maximum 100 invoices per validation")
        
        service = InvoiceService(db)
        return service.validate_bulk_operation(invoice_ids, operation)
        
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/bulk/post", response_model=BulkOperationResult)
def bulk_post_invoices(
    request_data: BulkInvoicePostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Contabilizar múltiples facturas en lote: DRAFT → POSTED
    
    Flujo Odoo IMPLEMENTADO en masa:
    1. Validar que todas estén en DRAFT
    2. Para cada factura válida:
       - Cambiar estado a POSTED
       - Generar asiento contable automáticamente
       - Actualizar fecha de contabilización
    3. Retornar resumen detallado del procesamiento
    
    Características:
    - Máximo 100 facturas por operación
    - Procesamiento individual con control de errores
    - Opción de continuar o parar en el primer error
    - Transacción por factura para mayor consistencia
    """
    try:
        service = InvoiceService(db)
        result = service.bulk_post_invoices(
            invoice_ids=request_data.invoice_ids,
            posted_by_id=current_user.id,
            posting_date=request_data.posting_date,
            notes=request_data.notes,
            force_post=request_data.force_post or False,
            stop_on_error=request_data.stop_on_error or False
        )
        
        return BulkOperationResult(**result)
        
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/bulk/cancel", response_model=BulkOperationResult)
def bulk_cancel_invoices(
    request_data: BulkInvoiceCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancelar múltiples facturas en lote: POSTED → CANCELLED
    
    Flujo Odoo IMPLEMENTADO en masa:
    1. Validar que todas estén en POSTED
    2. Validar que no tengan pagos aplicados
    3. Para cada factura válida:
       - Cambiar estado a CANCELLED
       - Crear asiento contable de reversión
       - Actualizar fecha de cancelación
    4. Retornar resumen detallado del procesamiento
    
    Características:
    - Máximo 100 facturas por operación
    - Validación estricta de pagos (no cancela si tiene pagos)
    - Control de errores individual
    - Generación automática de asientos de reversión
    """
    try:
        service = InvoiceService(db)
        result = service.bulk_cancel_invoices(
            invoice_ids=request_data.invoice_ids,
            cancelled_by_id=current_user.id,
            reason=request_data.reason,
            stop_on_error=request_data.stop_on_error or False
        )
        
        return BulkOperationResult(**result)
        
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/bulk/reset-to-draft", response_model=BulkOperationResult)
def bulk_reset_invoices_to_draft(
    request_data: BulkInvoiceResetToDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restablecer múltiples facturas a borrador en lote: POSTED/CANCELLED → DRAFT
    
    Flujo Odoo IMPLEMENTADO en masa:
    1. Validar que todas estén en POSTED o CANCELLED
    2. Validar que no tengan pagos aplicados (excepto con force_reset)
    3. Para cada factura válida:
       - POSTED: Eliminar asiento contable asociado
       - CANCELLED: Eliminar asiento de reversión asociado
       - Cambiar estado a DRAFT
       - Limpiar fechas de contabilización y cancelación
    4. Retornar resumen detallado del procesamiento
    
    Características:
    - Máximo 100 facturas por operación
    - Opción force_reset para facturas con pagos (peligroso)
    - Eliminación segura de asientos contables y de reversión
    - Las facturas vuelven a ser editables
    """
    try:
        service = InvoiceService(db)
        result = service.bulk_reset_to_draft_invoices(
            invoice_ids=request_data.invoice_ids,
            reset_by_id=current_user.id,
            reason=request_data.reason,
            force_reset=request_data.force_reset or False,
            stop_on_error=request_data.stop_on_error or False
        )
        
        return BulkOperationResult(**result)
        
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/bulk/delete", response_model=BulkOperationResult)
def bulk_delete_invoices(
    request_data: BulkInvoiceDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar múltiples facturas en lote (solo DRAFT)
    
    Operación DESTRUCTIVA:
    1. Validar que todas estén en DRAFT
    2. Validar que no tengan asientos contables
    3. Para cada factura válida:
       - Eliminar líneas de factura
       - Eliminar factura
    4. Retornar resumen detallado del procesamiento
    
    Características:
    - Máximo 50 facturas por operación (por seguridad)
    - Solo facturas en estado DRAFT
    - Eliminación cascada de líneas
    - Confirmación obligatoria
    - Operación irreversible
    """
    try:
        service = InvoiceService(db)
        result = service.bulk_delete_invoices(
            invoice_ids=request_data.invoice_ids,
            deleted_by_id=current_user.id,
            reason=request_data.reason
        )
        
        return BulkOperationResult(**result)
        
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ================================
# INDIVIDUAL INVOICE ENDPOINTS
# ================================


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
    request_data: Optional[InvoicePostRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Contabilizar factura: DRAFT → POSTED
    
    Flujo Odoo IMPLEMENTADO:
    1. Cambiar estado a POSTED
    2. Generar asiento contable automáticamente
    3. La factura queda lista para recibir pagos
    
    Body opcional:
    - posting_date: fecha de contabilización
    - notes: notas adicionales
    - force_post: forzar contabilización
    """
    try:
        service = InvoiceService(db)
        
        # Usar el método que implementa la lógica completa de Odoo
        return service.post_invoice(invoice_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: uuid.UUID,
    request_data: Optional[InvoiceCancelRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancelar factura: POSTED → CANCELLED
    
    Flujo Odoo IMPLEMENTADO:
    1. Cambiar estado a CANCELLED
    2. Crear asiento contable de reversión si existe asiento original
    3. La factura queda en estado final (cancelada)
    
    Body opcional:
    - reason: razón de la cancelación
    """
    try:
        service = InvoiceService(db)
        reason = None
        
        if request_data:
            reason = request_data.reason
        
        return service.cancel_invoice(invoice_id, current_user.id, reason)
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{invoice_id}/reset-to-draft", response_model=InvoiceResponse)
def reset_invoice_to_draft(
    invoice_id: uuid.UUID,    request_data: Optional[InvoiceResetToDraftRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restablecer factura a borrador: POSTED/CANCELLED → DRAFT
    
    Flujo Odoo IMPLEMENTADO:
    1. Validar que no hay pagos aplicados
    2. Eliminar asiento contable o de reversión asociado
    3. Cambiar estado a DRAFT
    4. La factura vuelve a ser editable
    
    Estados soportados:
    - POSTED → DRAFT: Elimina el asiento contable original
    - CANCELLED → DRAFT: Elimina el asiento de reversión
    
    Body opcional:
    - reason: razón del restablecimiento
    """
    
    try:
        service = InvoiceService(db)
        reason = None
        
        if request_data:
            reason = request_data.reason
        
        return service.reset_to_draft(invoice_id, current_user.id, reason)
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{invoice_id}/workflow-status", response_model=dict)
def get_invoice_workflow_status(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener el estado actual del workflow de una factura y las transiciones válidas
    
    Retorna:
    - current_status: estado actual
    - valid_transitions: lista de transiciones válidas desde el estado actual
    - can_edit: si la factura puede editarse
    - can_delete: si la factura puede eliminarse
    """
    try:
        service = InvoiceService(db)
        invoice = service.get_invoice(invoice_id)
        
        # Definir transiciones válidas según el estado actual
        valid_transitions = []
        can_edit = False
        can_delete = False
        
        if invoice.status == InvoiceStatus.DRAFT:
            valid_transitions = ["post", "cancel"]
            can_edit = True
            can_delete = True
        elif invoice.status == InvoiceStatus.POSTED:
            valid_transitions = ["cancel", "reset-to-draft"]
            can_edit = False
            can_delete = False
        elif invoice.status == InvoiceStatus.CANCELLED:
            valid_transitions = []  # Estado final
            can_edit = False
            can_delete = False
        
        return {
            "invoice_id": str(invoice.id),
            "current_status": invoice.status,
            "valid_transitions": valid_transitions,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "has_journal_entry": invoice.journal_entry_id is not None,
            "posted_at": invoice.posted_at.isoformat() if invoice.posted_at else None,
            "cancelled_at": invoice.cancelled_at.isoformat() if invoice.cancelled_at else None
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


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


@router.get("/{invoice_id}/payment-schedule-preview", response_model=List[dict])
def get_payment_schedule_preview(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener vista previa de cómo se dividirán los pagos según las condiciones de pago
    
    Retorna información de cada vencimiento:
    - sequence: número de secuencia del vencimiento
    - amount: monto de este vencimiento
    - percentage: porcentaje del total
    - due_date: fecha de vencimiento
    - description: descripción del vencimiento
    """
    try:
        service = InvoiceService(db)
        return service.get_payment_schedule_preview(invoice_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/payment-terms/{payment_terms_id}/validate", response_model=dict)
def validate_payment_terms(
    payment_terms_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validar condiciones de pago para uso en facturas    
    Retorna:
    - is_valid: boolean indicando si es válido
    - errors: lista de errores encontrados
    """
    try:
        service = InvoiceService(db)
        is_valid, errors = service.validate_payment_terms(payment_terms_id)
        return {
            "is_valid": is_valid,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



