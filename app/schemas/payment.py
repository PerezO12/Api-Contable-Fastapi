"""
Payment schemas for request/response serialization and validation.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from app.models.payment import PaymentStatus, PaymentType, PaymentMethod


# Base schemas
class PaymentBase(BaseModel):
    """Schema base para pagos"""
    reference: Optional[str] = Field(None, max_length=100, description="Referencia del pago")
    payment_date: date = Field(description="Fecha del pago")
    amount: Decimal = Field(gt=0, description="Monto del pago")
    payment_type: PaymentType = Field(description="Tipo de pago")
    payment_method: PaymentMethod = Field(description="Método de pago")
    currency_code: str = Field(default="USD", max_length=3, description="Código de moneda")
    exchange_rate: Optional[Decimal] = Field(None, gt=0, description="Tasa de cambio")
    description: Optional[str] = Field(None, description="Descripción del pago")
    notes: Optional[str] = Field(None, description="Notas adicionales")

    @validator('exchange_rate')
    def validate_exchange_rate(cls, v, values):
        """Validar tasa de cambio si la moneda no es la base"""
        currency_code = values.get('currency_code', 'USD')
        if currency_code != 'USD' and v is None:
            raise ValueError('Exchange rate is required for non-USD currencies')
        return v


class PaymentCreate(PaymentBase):
    """Schema para crear pagos"""
    customer_id: uuid.UUID = Field(description="ID del cliente")
    account_id: uuid.UUID = Field(description="ID de la cuenta")
    journal_id: Optional[uuid.UUID] = Field(None, description="ID del diario contable")


class PaymentUpdate(BaseModel):
    """Schema para actualizar pagos"""
    reference: Optional[str] = Field(None, max_length=100)
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    exchange_rate: Optional[Decimal] = Field(None, gt=0)


class PaymentResponse(PaymentBase):
    """Schema de respuesta para pagos"""
    id: uuid.UUID
    payment_number: str
    customer_id: uuid.UUID
    account_id: uuid.UUID
    journal_id: Optional[uuid.UUID]
    status: PaymentStatus
    total_allocated: Decimal
    remaining_amount: Decimal
    is_fully_allocated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for payment-invoice relationship
class PaymentInvoiceBase(BaseModel):
    """Schema base para relación pago-factura"""
    allocated_amount: Decimal = Field(gt=0, description="Monto asignado")
    allocation_date: Optional[date] = Field(None, description="Fecha de asignación")
    notes: Optional[str] = Field(None, description="Notas de la asignación")


class PaymentInvoiceCreate(PaymentInvoiceBase):
    """Schema para crear asignación pago-factura"""
    invoice_id: uuid.UUID = Field(description="ID de la factura")


class PaymentInvoiceResponse(PaymentInvoiceBase):
    """Schema de respuesta para asignación pago-factura"""
    id: uuid.UUID
    payment_id: uuid.UUID
    invoice_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentWithAllocations(PaymentResponse):
    """Schema de pago con asignaciones"""
    allocations: List[PaymentInvoiceResponse] = Field(default_factory=list)


# Schemas for allocation operations
class AllocatePaymentRequest(BaseModel):
    """Schema para asignar pago a facturas"""
    allocations: List[PaymentInvoiceCreate] = Field(description="Lista de asignaciones")

    @validator('allocations')
    def validate_allocations(cls, v):
        """Validar que hay al menos una asignación"""
        if not v:
            raise ValueError('At least one allocation is required')
        return v


class DeallocatePaymentRequest(BaseModel):
    """Schema para desasignar pago de facturas"""
    allocation_ids: List[uuid.UUID] = Field(description="IDs de asignaciones a eliminar")

    @validator('allocation_ids')
    def validate_allocation_ids(cls, v):
        """Validar que hay al menos un ID"""
        if not v:
            raise ValueError('At least one allocation ID is required')
        return v


# Summary schemas
class PaymentSummary(BaseModel):
    """Schema para resumen de pagos"""
    total_payments: int = Field(description="Total de pagos")
    total_amount: Decimal = Field(description="Monto total")
    pending_amount: Decimal = Field(description="Monto pendiente")
    allocated_amount: Decimal = Field(description="Monto asignado")
    by_status: dict = Field(description="Distribución por estado")
    by_method: dict = Field(description="Distribución por método")


class PaymentListResponse(BaseModel):
    """Schema para lista de pagos"""
    payments: List[PaymentResponse]
    total: int
    page: int
    size: int
    pages: int
