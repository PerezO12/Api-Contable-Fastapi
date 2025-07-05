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

    @validator('payment_type', pre=True)
    def normalize_payment_type(cls, v):
        """Normalizar payment_type: convierte a minúsculas"""
        if isinstance(v, str):
            return v.lower()
        return v

    @validator('payment_method', pre=True)
    def normalize_payment_method(cls, v):
        """Normalizar payment_method: convierte a minúsculas"""
        if isinstance(v, str):
            return v.lower()
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

    @validator('payment_method', pre=True)
    def normalize_payment_method(cls, v):
        """Normalizar payment_method: convierte a minúsculas"""
        if isinstance(v, str):
            return v.lower()
        return v


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





# Schemas for bulk operations
class BulkPaymentConfirmationRequest(BaseModel):
    """Schema para confirmación masiva de pagos"""
    payment_ids: List[uuid.UUID] = Field(description="IDs de pagos a confirmar")
    confirmation_notes: Optional[str] = Field(None, description="Notas de confirmación")
    force: bool = Field(False, description="Forzar confirmación omitiendo validaciones")

    @validator('payment_ids')
    def validate_payment_ids(cls, v):
        """Validar que hay al menos un ID"""
        if not v:
            raise ValueError('At least one payment ID is required')
        if len(v) > 100:  # Límite de seguridad
            raise ValueError('Cannot confirm more than 100 payments at once')
        return v


class BulkPaymentValidationRequest(BaseModel):
    """Schema para validación previa de pagos"""
    payment_ids: List[uuid.UUID] = Field(description="IDs de pagos a validar")

    @validator('payment_ids')
    def validate_payment_ids(cls, v):
        if not v:
            raise ValueError('At least one payment ID is required')
        if len(v) > 100:
            raise ValueError('Cannot validate more than 100 payments at once')
        return v


class BulkPaymentResetRequest(BaseModel):
    """Schema para restablecimiento masivo de pagos a borrador"""
    payment_ids: List[uuid.UUID] = Field(description="IDs de pagos a restablecer")
    reset_reason: Optional[str] = Field(None, description="Razón del restablecimiento")
    batch_size: Optional[int] = Field(30, description="Tamaño del lote de procesamiento")

    @validator('payment_ids')
    def validate_payment_ids(cls, v):
        """Validar que hay al menos un ID"""
        if not v:
            raise ValueError('At least one payment ID is required')
        if len(v) > 500:  # Límite de seguridad para resets
            raise ValueError('Cannot reset more than 500 payments at once for safety')
        return v

    @validator('batch_size')
    def validate_batch_size(cls, v):
        """Validar tamaño del lote"""
        if v is not None and not (1 <= v <= 50):
            return 30  # Default seguro
        return v


class BulkPaymentCancelRequest(BaseModel):
    """Schema para cancelación masiva de pagos"""
    payment_ids: List[uuid.UUID] = Field(description="IDs de pagos a cancelar")
    cancellation_reason: Optional[str] = Field(None, description="Razón de la cancelación")
    batch_size: Optional[int] = Field(30, description="Tamaño del lote de procesamiento")

    @validator('payment_ids')
    def validate_payment_ids(cls, v):
        """Validar que hay al menos un ID"""
        if not v:
            raise ValueError('At least one payment ID is required')
        if len(v) > 1000:
            raise ValueError('Cannot cancel more than 1000 payments at once')
        return v

    @validator('batch_size')
    def validate_batch_size(cls, v):
        """Validar tamaño del lote"""
        if v is not None and not (1 <= v <= 50):
            return 30  # Default seguro
        return v


class BulkPaymentDeleteRequest(BaseModel):
    """Schema para eliminación masiva de pagos"""
    payment_ids: List[uuid.UUID] = Field(description="IDs de pagos a eliminar")
    batch_size: Optional[int] = Field(30, description="Tamaño del lote de procesamiento")

    @validator('payment_ids')
    def validate_payment_ids(cls, v):
        """Validar que hay al menos un ID"""
        if not v:
            raise ValueError('At least one payment ID is required')
        if len(v) > 1000:
            raise ValueError('Cannot delete more than 1000 payments at once')
        return v

    @validator('batch_size')
    def validate_batch_size(cls, v):
        """Validar tamaño del lote"""
        if v is not None and not (1 <= v <= 50):
            return 30  # Default seguro
        return v


class BulkPaymentPostRequest(BaseModel):
    """Schema para contabilización masiva de pagos"""
    payment_ids: List[uuid.UUID] = Field(description="IDs de pagos a contabilizar")
    posting_notes: Optional[str] = Field(None, description="Notas de contabilización")
    batch_size: Optional[int] = Field(30, description="Tamaño del lote de procesamiento")

    @validator('payment_ids')
    def validate_payment_ids(cls, v):
        """Validar que hay al menos un ID"""
        if not v:
            raise ValueError('At least one payment ID is required')
        if len(v) > 1000:
            raise ValueError('Cannot post more than 1000 payments at once')
        return v

    @validator('batch_size')
    def validate_batch_size(cls, v):
        """Validar tamaño del lote"""
        if v is not None and not (1 <= v <= 50):
            return 30  # Default seguro
        return v


class PaymentValidationResult(BaseModel):
    """Resultado de validación de un pago individual"""
    payment_id: uuid.UUID = Field(description="ID del pago")
    payment_number: str = Field(description="Número del pago")
    can_confirm: bool = Field(description="Si puede ser confirmado")
    blocking_reasons: List[str] = Field(default=[], description="Razones que bloquean la confirmación")
    warnings: List[str] = Field(default=[], description="Advertencias")
    requires_confirmation: bool = Field(description="Si requiere confirmación del usuario")


class BulkPaymentValidationResponse(BaseModel):
    """Respuesta de validación masiva de pagos"""
    total_payments: int = Field(description="Total de pagos validados")
    can_confirm_count: int = Field(description="Cantidad que puede confirmarse")
    blocked_count: int = Field(description="Cantidad bloqueada")
    warnings_count: int = Field(description="Cantidad con advertencias")
    validation_results: List[PaymentValidationResult] = Field(description="Resultados individuales")


class PaymentOperationResult(BaseModel):
    """Resultado de operación en un pago individual"""
    payment_id: uuid.UUID = Field(description="ID del pago")
    payment_number: str = Field(description="Número del pago")
    success: bool = Field(description="Si la operación fue exitosa")
    message: str = Field(description="Mensaje del resultado")
    error: Optional[str] = Field(None, description="Error si falló")


class BulkPaymentOperationResponse(BaseModel):
    """Respuesta de operación masiva de pagos"""
    operation: str = Field(description="Tipo de operación realizada")
    total_payments: int = Field(description="Total de pagos procesados")
    successful: int = Field(description="Cantidad exitosa")
    failed: int = Field(description="Cantidad fallida")
    results: List[PaymentOperationResult] = Field(description="Resultados individuales")
    summary: str = Field(description="Resumen de la operación")


class PaymentListResponse(BaseModel):
    """Schema para lista de pagos"""
    data: List[PaymentResponse]  # Cambiar payments por data para consistencia
    total: int
    page: int
    per_page: int  # Cambiar size por per_page para consistencia
    pages: int
