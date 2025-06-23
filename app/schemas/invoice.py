"""
Invoice schemas for request/response serialization and validation.
Following Odoo pattern from IMPLEMENTAR.md
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from app.models.invoice import InvoiceStatus, InvoiceType


# ================================
# LINE SCHEMAS (siguiendo IMPLEMENTAR.md)
# ================================

class InvoiceLineBase(BaseModel):
    """Schema base para líneas de factura siguiendo patrón Odoo"""
    sequence: Optional[int] = Field(None, description="Orden de la línea (auto-asignado si no se especifica)")
    product_id: Optional[uuid.UUID] = Field(None, description="ID del producto (opcional)")
    description: str = Field(description="Descripción de la línea")
    quantity: Decimal = Field(default=Decimal('1'), gt=0, description="Cantidad")
    unit_price: Decimal = Field(ge=0, description="Precio unitario")
    discount_percentage: Optional[Decimal] = Field(default=Decimal('0'), ge=0, le=100, description="Porcentaje de descuento")
    
    # Overrides de cuentas contables (opcionales - patrón Odoo)
    account_id: Optional[uuid.UUID] = Field(None, description="Override cuenta ingreso/gasto")
    cost_center_id: Optional[uuid.UUID] = Field(None, description="Centro de costo")
    
    # Impuestos (siguiendo patrón Odoo)
    tax_ids: Optional[List[uuid.UUID]] = Field(default_factory=list, description="IDs de impuestos aplicables")


class InvoiceLineCreate(InvoiceLineBase):
    """Schema para crear líneas de factura"""
    pass


class InvoiceLineUpdate(BaseModel):
    """Schema para actualizar líneas de factura"""
    sequence: Optional[int] = None
    product_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    account_id: Optional[uuid.UUID] = None
    cost_center_id: Optional[uuid.UUID] = None
    tax_ids: Optional[List[uuid.UUID]] = None


class InvoiceLineResponse(BaseModel):
    """Schema de respuesta para líneas de factura (no hereda para evitar conflicto de tipos)"""
    id: uuid.UUID
    invoice_id: uuid.UUID
    sequence: int = Field(description="Orden de la línea")
    product_id: Optional[uuid.UUID] = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal
    account_id: Optional[uuid.UUID] = None
    cost_center_id: Optional[uuid.UUID] = None
    tax_ids: List[uuid.UUID] = Field(default_factory=list)
    
    # Montos calculados
    subtotal: Decimal = Field(description="quantity * unit_price")
    discount_amount: Decimal = Field(description="subtotal * discount_percentage / 100")
    tax_amount: Decimal = Field(description="Impuestos calculados")
    total_amount: Decimal = Field(description="subtotal - discount + tax")
    
    # Auditoría
    created_at: datetime
    updated_at: datetime
    created_by_id: uuid.UUID
    updated_by_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


# ================================
# INVOICE SCHEMAS (siguiendo IMPLEMENTAR.md)
# ================================

class InvoiceBase(BaseModel):
    """Schema base para facturas siguiendo patrón Odoo"""
    invoice_date: date = Field(description="Fecha de la factura")
    due_date: Optional[date] = Field(None, description="Fecha de vencimiento (opcional si hay payment_terms)")
    invoice_type: InvoiceType = Field(description="Tipo de factura: CUSTOMER_INVOICE, SUPPLIER_INVOICE, CREDIT_NOTE o DEBIT_NOTE")
    currency_code: str = Field(default="USD", max_length=3, description="Código de moneda")
    exchange_rate: Optional[Decimal] = Field(default=Decimal('1'), gt=0, description="Tasa de cambio")
    description: Optional[str] = Field(None, description="Descripción de la factura")
    notes: Optional[str] = Field(None, description="Notas adicionales")

    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Validar que la fecha de vencimiento sea posterior a la fecha de factura"""
        if v:
            invoice_date = values.get('invoice_date')
            if invoice_date and v < invoice_date:
                raise ValueError('Due date must be after invoice date')
        return v

    @validator('exchange_rate')
    def validate_exchange_rate(cls, v, values):
        """Validar tasa de cambio si la moneda no es la base"""
        currency_code = values.get('currency_code', 'USD')
        if currency_code != 'USD' and (v is None or v == 0):
            raise ValueError('Exchange rate is required for non-USD currencies')
        return v or Decimal('1')


class InvoiceCreate(InvoiceBase):
    """Schema para crear facturas siguiendo patrón Odoo de IMPLEMENTAR.md"""
    # Identificación
    invoice_number: Optional[str] = Field(None, max_length=50, description="Número de factura (auto-generado si no se especifica)")
      # Relaciones principales (siguiendo IMPLEMENTAR.md)
    third_party_id: uuid.UUID = Field(description="ID del cliente o proveedor (third_party)")
    journal_id: Optional[uuid.UUID] = Field(None, description="ID del diario contable para numeración automática")
    payment_terms_id: Optional[uuid.UUID] = Field(None, description="ID de términos de pago")
    
    # Overrides de cuentas contables (opcionales - patrón Odoo)
    third_party_account_id: Optional[uuid.UUID] = Field(None, description="Override cuenta cliente/proveedor")
    
    @validator('due_date', always=True)
    def calculate_due_date(cls, v, values):
        """Si no se especifica due_date y hay payment_terms, calcular automáticamente"""
        if not v and values.get('payment_terms_id'):
            # El servicio calculará la fecha automáticamente
            return None
        return v


class InvoiceCreateWithLines(InvoiceCreate):
    """
    Schema para crear factura con líneas en una operación (patrón Odoo completo)
    
    Este es el esquema principal que sigue IMPLEMENTAR.md:
    POST /invoices/with-lines
    """
    lines: List[InvoiceLineCreate] = Field(description="Líneas de la factura")

    @validator('lines')
    def validate_lines(cls, v):
        """Validar que hay al menos una línea"""
        if not v:
            raise ValueError('Invoice must have at least one line')
        return v


class InvoiceUpdate(BaseModel):
    """Schema para actualizar facturas (solo en estado DRAFT)"""
    invoice_number: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    exchange_rate: Optional[Decimal] = Field(None, gt=0)


class InvoiceResponse(InvoiceBase):
    """Schema de respuesta para facturas siguiendo IMPLEMENTAR.md"""
    id: uuid.UUID
    invoice_number: str = Field(description="Número generado automáticamente")
    status: InvoiceStatus
    
    # Relaciones (usando third_party_id según IMPLEMENTAR.md)
    third_party_id: uuid.UUID = Field(description="ID del cliente o proveedor")
    payment_terms_id: Optional[uuid.UUID] = None
    journal_id: Optional[uuid.UUID] = None
    third_party_account_id: Optional[uuid.UUID] = None
    
    # Montos calculados
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal  # remaining_amount renombrado
    
    # Estados calculados
    is_paid: bool
    is_overdue: bool
    days_overdue: int
    
    # Asiento contable generado (patrón Odoo)
    journal_entry_id: Optional[uuid.UUID] = Field(None, description="ID del asiento contable generado")
    
    # Auditoría completa (siguiendo IMPLEMENTAR.md)
    created_by_id: uuid.UUID
    updated_by_id: Optional[uuid.UUID] = None
    posted_by_id: Optional[uuid.UUID] = None  # Quien contabilizó
    cancelled_by_id: Optional[uuid.UUID] = None  # Quien canceló
    
    created_at: datetime
    updated_at: datetime
    posted_at: Optional[datetime] = None  # Fecha contabilización
    cancelled_at: Optional[datetime] = None  # Fecha cancelación

    class Config:
        from_attributes = True


class InvoiceWithLines(InvoiceResponse):
    """Schema de factura con líneas"""
    lines: List[InvoiceLineResponse] = Field(default_factory=list)


# ================================
# BULK OPERATIONS Y UTILIDADES
# ================================

class InvoiceListResponse(BaseModel):
    """Schema para respuesta de lista de facturas"""
    items: List[InvoiceResponse] = Field(..., description="Lista de facturas")
    total: int = Field(..., description="Total de facturas")
    page: int = Field(..., description="Página actual")
    size: int = Field(..., description="Tamaño de página")
    total_pages: int = Field(..., description="Total de páginas")


class InvoiceSummary(BaseModel):
    """Schema para resumen estadístico de facturas"""
    total_invoices: int
    total_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    overdue_amount: Decimal
    by_status: dict  # {status: count}
    by_type: dict    # {type: count}


# ================================
# LEGACY COMPATIBILITY
# ================================

# Para mantener compatibilidad con endpoints existentes que usan customer_id
class InvoiceCreateLegacy(InvoiceBase):
    """Schema legacy para compatibilidad con endpoints existentes"""
    customer_id: uuid.UUID = Field(description="ID del cliente (legacy, use third_party_id)")
    payment_term_id: Optional[uuid.UUID] = Field(None, description="ID del término de pago (legacy, use payment_terms_id)")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Descuento global (legacy, use por línea)")
    tax_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Impuesto global (legacy, use por línea)")


# ================================
# WORKFLOW OPERATION SCHEMAS
# ================================

class InvoiceCancelRequest(BaseModel):
    """Schema para cancelar una factura"""
    reason: Optional[str] = Field(
        None, 
        max_length=500,
        description="Razón de la cancelación"
    )


class InvoiceResetToDraftRequest(BaseModel):
    """Schema para restablecer una factura a borrador"""
    reason: Optional[str] = Field(
        None, 
        max_length=500,
        description="Razón del restablecimiento a borrador"
    )


class InvoicePostRequest(BaseModel):
    """Schema para contabilizar una factura"""
    posting_date: Optional[date] = Field(
        None,
        description="Fecha de contabilización (opcional, usa fecha actual si no se especifica)"    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas adicionales para la contabilización"
    )
    force_post: Optional[bool] = Field(
        False,
        description="Forzar contabilización aunque haya advertencias menores"
    )


# ================================
# BULK OPERATION SCHEMAS
# ================================

class BulkOperationResult(BaseModel):
    """Resultado de una operación masiva"""
    total_requested: int = Field(description="Total de elementos solicitados")
    successful: int = Field(description="Elementos procesados exitosamente")
    failed: int = Field(description="Elementos que fallaron")
    skipped: int = Field(description="Elementos omitidos por validaciones")
    
    successful_ids: List[uuid.UUID] = Field(description="IDs procesados exitosamente")
    failed_items: List[dict] = Field(description="Items que fallaron con sus errores")
    skipped_items: List[dict] = Field(description="Items omitidos con razones")
    
    execution_time_seconds: float = Field(description="Tiempo de ejecución en segundos")


class BulkInvoicePostRequest(BaseModel):
    """Schema para contabilizar facturas en lote"""
    invoice_ids: List[uuid.UUID] = Field(
        ..., 
        description="Lista de IDs de facturas a contabilizar"
    )
    posting_date: Optional[date] = Field(
        None,
        description="Fecha de contabilización (opcional, usa fecha actual si no se especifica)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas adicionales para todas las facturas"
    )
    force_post: Optional[bool] = Field(
        False,
        description="Forzar contabilización aunque haya advertencias menores"
    )
    stop_on_error: Optional[bool] = Field(
        False,
        description="Detener procesamiento en el primer error (default: continuar)"
    )
    
    @validator('invoice_ids')
    def validate_invoice_ids(cls, v):
        if len(v) < 1:
            raise ValueError('Debe proporcionar al menos 1 ID de factura')
        if len(v) > 100:
            raise ValueError('Máximo 100 facturas por operación bulk')
        return v


class BulkInvoiceCancelRequest(BaseModel):
    """Schema para cancelar facturas en lote"""
    invoice_ids: List[uuid.UUID] = Field(
        ..., 
        description="Lista de IDs de facturas a cancelar"
    )
    reason: Optional[str] = Field(
        None, 
        max_length=500,
        description="Razón de la cancelación para todas las facturas"
    )
    stop_on_error: Optional[bool] = Field(
        False,
        description="Detener procesamiento en el primer error"
    )
    
    @validator('invoice_ids')
    def validate_invoice_ids(cls, v):
        if len(v) < 1:
            raise ValueError('Debe proporcionar al menos 1 ID de factura')
        if len(v) > 100:
            raise ValueError('Máximo 100 facturas por operación bulk')
        return v


class BulkInvoiceResetToDraftRequest(BaseModel):
    """Schema para restablecer facturas a borrador en lote"""
    invoice_ids: List[uuid.UUID] = Field(
        ..., 
        description="Lista de IDs de facturas a restablecer"
    )
    reason: Optional[str] = Field(
        None, 
        max_length=500,
        description="Razón del restablecimiento para todas las facturas"
    )
    stop_on_error: Optional[bool] = Field(
        False,
        description="Detener procesamiento en el primer error"
    )
    force_reset: Optional[bool] = Field(
        False,
        description="Forzar reset aunque haya pagos aplicados (peligroso)"
    )
    
    @validator('invoice_ids')
    def validate_invoice_ids(cls, v):
        if len(v) < 1:
            raise ValueError('Debe proporcionar al menos 1 ID de factura')
        if len(v) > 100:
            raise ValueError('Máximo 100 facturas por operación bulk')
        return v


class BulkInvoiceDeleteRequest(BaseModel):
    """Schema para eliminar facturas en lote"""
    invoice_ids: List[uuid.UUID] = Field(
        ..., 
        description="Lista de IDs de facturas a eliminar"
    )
    confirmation: str = Field(
        ...,
        description="Confirmación requerida: debe ser 'CONFIRM_DELETE'"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Razón de la eliminación masiva"
    )
    
    @validator('invoice_ids')
    def validate_invoice_ids(cls, v):
        if len(v) < 1:
            raise ValueError('Debe proporcionar al menos 1 ID de factura')
        if len(v) > 50:
            raise ValueError('Máximo 50 facturas por operación de eliminación bulk')
        return v
    
    @validator('confirmation')
    def validate_confirmation(cls, v):
        if v != 'CONFIRM_DELETE':
            raise ValueError('Debe confirmar la eliminación con "CONFIRM_DELETE"')
        return v