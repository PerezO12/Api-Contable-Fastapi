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
    customer_id: Optional[uuid.UUID] = Field(None, description="ID del cliente (opcional)")
    journal_id: uuid.UUID = Field(description="ID del diario contable (obligatorio)")
    # account_id se toma del diario seleccionado


class PaymentUpdate(BaseModel):
    """Schema para actualizar pagos"""
    reference: Optional[str] = Field(None, max_length=100)
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    exchange_rate: Optional[Decimal] = Field(None, gt=0)


# Schemas específicos para el flujo de pagos
class PaymentAutoMatchResult(BaseModel):
    """Resultado del auto-matching de un pago"""
    line_id: uuid.UUID = Field(description="ID de la línea del extracto")
    line_description: str = Field(description="Descripción de la línea")
    line_amount: Decimal = Field(description="Monto de la línea")
    matched: bool = Field(description="Si se encontró coincidencia")
    payment_created: bool = Field(description="Si se creó un pago")
    invoice_id: Optional[uuid.UUID] = Field(None, description="ID de la factura coincidente")
    payment_id: Optional[uuid.UUID] = Field(None, description="ID del pago creado")
    match_reason: str = Field(description="Razón del resultado del matching")
    errors: List[str] = Field(default=[], description="Errores durante el matching")


class PaymentFlowImportResult(BaseModel):
    """Resultado de la importación con auto-matching"""
    extract_id: uuid.UUID = Field(description="ID del extracto importado")
    extract_name: str = Field(description="Nombre del extracto")
    total_lines: int = Field(description="Total de líneas importadas")
    matched_lines: int = Field(description="Líneas con coincidencias encontradas")
    payments_created: int = Field(description="Pagos creados automáticamente")
    auto_match_results: List[PaymentAutoMatchResult] = Field(description="Resultados detallados del auto-matching")


class PaymentFlowStatus(BaseModel):
    """Estado del flujo de pagos para un extracto"""
    extract_id: uuid.UUID = Field(description="ID del extracto")
    extract_name: str = Field(description="Nombre del extracto")
    extract_status: str = Field(description="Estado del extracto")
    total_lines: int = Field(description="Total de líneas")
    matched_lines: int = Field(description="Líneas con pagos vinculados")
    draft_payments: int = Field(description="Pagos en borrador")
    posted_payments: int = Field(description="Pagos confirmados")
    unmatched_lines: int = Field(description="Líneas sin vincular")
    completion_percentage: float = Field(description="Porcentaje de completitud")


class PaymentConfirmation(BaseModel):
    """Schema para confirmar un pago"""
    payment_id: uuid.UUID = Field(description="ID del pago a confirmar")
    confirmation_notes: Optional[str] = Field(None, description="Notas de confirmación")


class PaymentReconciliationResult(BaseModel):
    """Resultado de la conciliación de un pago"""
    invoice_id: uuid.UUID = Field(description="ID de la factura")
    invoice_number: str = Field(description="Número de factura")
    allocated_amount: Decimal = Field(description="Monto asignado")
    reconciled: bool = Field(description="Si fue conciliado exitosamente")
    error: Optional[str] = Field(None, description="Error si la conciliación falló")


class PaymentResponse(PaymentBase):
    """Schema de respuesta para pagos"""
    id: uuid.UUID
    number: str  # Cambiar de payment_number a number
    third_party_id: Optional[uuid.UUID]  # Cambiar de customer_id a third_party_id
    account_id: uuid.UUID
    journal_id: Optional[uuid.UUID]
    status: PaymentStatus
    allocated_amount: Decimal  # Cambiar de total_allocated a allocated_amount
    unallocated_amount: Decimal  # Cambiar de remaining_amount a unallocated_amount
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
