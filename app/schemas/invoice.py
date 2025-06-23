"""
Invoice schemas for request/response serialization and validation.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from app.models.invoice import InvoiceStatus, InvoiceType


# Base schemas
class InvoiceBase(BaseModel):
    """Schema base para facturas"""
    invoice_number: Optional[str] = Field(None, max_length=50, description="Número de factura")
    invoice_date: date = Field(description="Fecha de la factura")
    due_date: date = Field(description="Fecha de vencimiento")
    invoice_type: InvoiceType = Field(description="Tipo de factura")
    currency_code: str = Field(default="USD", max_length=3, description="Código de moneda")
    exchange_rate: Optional[Decimal] = Field(None, gt=0, description="Tasa de cambio")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Porcentaje de descuento")
    tax_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Porcentaje de impuesto")
    description: Optional[str] = Field(None, description="Descripción de la factura")
    notes: Optional[str] = Field(None, description="Notas adicionales")

    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Validar que la fecha de vencimiento sea posterior a la fecha de factura"""
        invoice_date = values.get('invoice_date')
        if invoice_date and v < invoice_date:
            raise ValueError('Due date must be after invoice date')
        return v

    @validator('exchange_rate')
    def validate_exchange_rate(cls, v, values):
        """Validar tasa de cambio si la moneda no es la base"""
        currency_code = values.get('currency_code', 'USD')
        if currency_code != 'USD' and v is None:
            raise ValueError('Exchange rate is required for non-USD currencies')
        return v


class InvoiceCreate(InvoiceBase):
    """Schema para crear facturas"""
    customer_id: uuid.UUID = Field(description="ID del cliente")
    payment_term_id: Optional[uuid.UUID] = Field(None, description="ID del término de pago")


class InvoiceUpdate(BaseModel):
    """Schema para actualizar facturas"""
    invoice_number: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    exchange_rate: Optional[Decimal] = Field(None, gt=0)


class InvoiceResponse(InvoiceBase):
    """Schema de respuesta para facturas"""
    id: uuid.UUID
    customer_id: uuid.UUID
    payment_term_id: Optional[uuid.UUID]
    status: InvoiceStatus
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    is_paid: bool
    is_overdue: bool
    days_overdue: int
    journal_entry_id: Optional[uuid.UUID] = Field(None, description="ID del asiento contable generado")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Invoice line schemas
class InvoiceLineBase(BaseModel):
    """Schema base para líneas de factura"""
    sequence: int = Field(ge=1, description="Secuencia de la línea")
    description: str = Field(max_length=500, description="Descripción del item")
    quantity: Decimal = Field(gt=0, description="Cantidad")
    unit_price: Decimal = Field(ge=0, description="Precio unitario")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Porcentaje de descuento")
    account_id: uuid.UUID = Field(description="ID de la cuenta contable")
    product_id: Optional[uuid.UUID] = Field(None, description="ID del producto")


class InvoiceLineCreate(InvoiceLineBase):
    """Schema para crear líneas de factura"""
    pass


class InvoiceLineUpdate(BaseModel):
    """Schema para actualizar líneas de factura"""
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    account_id: Optional[uuid.UUID] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema de respuesta para líneas de factura"""
    id: uuid.UUID
    invoice_id: uuid.UUID
    subtotal: Decimal
    discount_amount: Decimal
    line_total: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceWithLines(InvoiceResponse):
    """Schema de factura con líneas"""
    lines: List[InvoiceLineResponse] = Field(default_factory=list)


# Bulk operations
class InvoiceCreateWithLines(InvoiceCreate):
    """Schema para crear factura con líneas"""
    lines: List[InvoiceLineCreate] = Field(description="Líneas de la factura")

    @validator('lines')
    def validate_lines(cls, v):
        """Validar que hay al menos una línea"""
        if not v:
            raise ValueError('At least one invoice line is required')
        return v


# Payment allocation schemas
class InvoicePaymentResponse(BaseModel):
    """Schema para pagos asignados a factura"""
    id: uuid.UUID
    payment_id: uuid.UUID
    payment_number: str
    payment_date: date
    allocated_amount: Decimal
    allocation_date: Optional[date]
    notes: Optional[str]

    class Config:
        from_attributes = True


class InvoiceWithPayments(InvoiceResponse):
    """Schema de factura con pagos"""
    payments: List[InvoicePaymentResponse] = Field(default_factory=list)


# Summary schemas
class InvoiceSummary(BaseModel):
    """Schema para resumen de facturas"""
    total_invoices: int = Field(description="Total de facturas")
    total_amount: Decimal = Field(description="Monto total")
    paid_amount: Decimal = Field(description="Monto pagado")
    pending_amount: Decimal = Field(description="Monto pendiente")
    overdue_amount: Decimal = Field(description="Monto vencido")
    by_status: dict = Field(description="Distribución por estado")
    by_type: dict = Field(description="Distribución por tipo")


class InvoiceListResponse(BaseModel):
    """Schema para lista de facturas"""
    invoices: List[InvoiceResponse]
    total: int
    page: int
    size: int
    pages: int


# Status update schemas
class InvoiceStatusUpdate(BaseModel):
    """Schema para actualizar estado de factura"""
    status: InvoiceStatus = Field(description="Nuevo estado")
    notes: Optional[str] = Field(None, description="Notas del cambio de estado")
