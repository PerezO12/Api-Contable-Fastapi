"""
Bank reconciliation schemas for request/response serialization and validation.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from app.models.bank_reconciliation import ReconciliationType


# Base schemas
class BankReconciliationBase(BaseModel):
    """Schema base para conciliación bancaria"""
    amount: Decimal = Field(gt=0, description="Monto conciliado")
    reconciliation_type: ReconciliationType = Field(description="Tipo de conciliación")
    reconciliation_date: date = Field(description="Fecha de conciliación")
    description: Optional[str] = Field(None, description="Descripción de la conciliación")
    notes: Optional[str] = Field(None, description="Notas adicionales")


class BankReconciliationCreate(BankReconciliationBase):
    """Schema para crear conciliación bancaria"""
    extract_line_id: uuid.UUID = Field(description="ID de la línea de extracto")
    payment_id: Optional[uuid.UUID] = Field(None, description="ID del pago")
    invoice_id: Optional[uuid.UUID] = Field(None, description="ID de la factura")

    @validator('payment_id')
    def validate_payment_or_invoice(cls, v, values):
        """Validar que se proporcione payment_id o invoice_id"""
        invoice_id = values.get('invoice_id')
        if not v and not invoice_id:
            raise ValueError('Either payment_id or invoice_id must be provided')
        if v and invoice_id:
            raise ValueError('Cannot provide both payment_id and invoice_id')
        return v


class BankReconciliationUpdate(BaseModel):
    """Schema para actualizar conciliación bancaria"""
    amount: Optional[Decimal] = Field(None, gt=0)
    reconciliation_date: Optional[date] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    is_confirmed: Optional[bool] = None


class BankReconciliationResponse(BankReconciliationBase):
    """Schema de respuesta para conciliación bancaria"""
    id: uuid.UUID
    extract_line_id: uuid.UUID
    payment_id: Optional[uuid.UUID]
    invoice_id: Optional[uuid.UUID]
    is_confirmed: bool
    created_by_id: uuid.UUID
    confirmed_by_id: Optional[uuid.UUID]
    confirmed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Bulk reconciliation schemas
class BulkReconciliationCreate(BaseModel):
    """Schema para conciliación masiva"""
    reconciliations: List[BankReconciliationCreate] = Field(description="Lista de conciliaciones")

    @validator('reconciliations')
    def validate_reconciliations(cls, v):
        """Validar que hay al menos una conciliación"""
        if not v:
            raise ValueError('At least one reconciliation is required')
        return v


class BulkReconciliationResult(BaseModel):
    """Schema para resultado de conciliación masiva"""
    created_reconciliations: List[uuid.UUID] = Field(description="IDs de conciliaciones creadas")
    total_created: int = Field(description="Total de conciliaciones creadas")
    errors: List[str] = Field(default_factory=list, description="Errores encontrados")


# Automatic reconciliation schemas
class AutoReconciliationRequest(BaseModel):
    """Schema para solicitud de conciliación automática"""
    extract_line_ids: Optional[List[uuid.UUID]] = Field(None, description="IDs de líneas específicas")
    date_range_start: Optional[date] = Field(None, description="Fecha de inicio del rango")
    date_range_end: Optional[date] = Field(None, description="Fecha de fin del rango")
    tolerance_amount: Optional[Decimal] = Field(None, ge=0, description="Tolerancia en el monto")
    tolerance_days: Optional[int] = Field(None, ge=0, description="Tolerancia en días")


class AutoReconciliationResult(BaseModel):
    """Schema para resultado de conciliación automática"""
    processed_lines: int = Field(description="Líneas procesadas")
    reconciled_lines: int = Field(description="Líneas conciliadas")
    suggested_reconciliations: List[BankReconciliationResponse] = Field(
        default_factory=list, 
        description="Conciliaciones sugeridas"
    )
    errors: List[str] = Field(default_factory=list, description="Errores encontrados")


# Reconciliation validation schemas
class ReconciliationValidation(BaseModel):
    """Schema para validación de conciliación"""
    is_valid: bool = Field(description="Si la conciliación es válida")
    extract_line_amount: Decimal = Field(description="Monto de la línea de extracto")
    reconciled_amount: Decimal = Field(description="Monto total conciliado")
    remaining_amount: Decimal = Field(description="Monto restante")
    errors: List[str] = Field(default_factory=list, description="Errores encontrados")
    warnings: List[str] = Field(default_factory=list, description="Advertencias")


# Summary schemas
class ReconciliationSummary(BaseModel):
    """Schema para resumen de conciliaciones"""
    total_reconciliations: int = Field(description="Total de conciliaciones")
    confirmed_reconciliations: int = Field(description="Conciliaciones confirmadas")
    pending_reconciliations: int = Field(description="Conciliaciones pendientes")
    total_amount: Decimal = Field(description="Monto total conciliado")
    by_type: dict = Field(description="Distribución por tipo")
    by_status: dict = Field(description="Distribución por estado")


class BankReconciliationListResponse(BaseModel):
    """Schema para lista de conciliaciones"""
    reconciliations: List[BankReconciliationResponse]
    total: int
    page: int
    size: int
    pages: int


# Enhanced response schemas with related data
class BankReconciliationWithDetails(BankReconciliationResponse):
    """Schema de conciliación con detalles relacionados"""
    extract_line: Optional[dict] = Field(None, description="Datos de la línea de extracto")
    payment: Optional[dict] = Field(None, description="Datos del pago")
    invoice: Optional[dict] = Field(None, description="Datos de la factura")


# Confirmation schemas
class ReconciliationConfirmation(BaseModel):
    """Schema para confirmar conciliaciones"""
    reconciliation_ids: List[uuid.UUID] = Field(description="IDs de conciliaciones a confirmar")
    notes: Optional[str] = Field(None, description="Notas de confirmación")

    @validator('reconciliation_ids')
    def validate_reconciliation_ids(cls, v):
        """Validar que hay al menos un ID"""
        if not v:
            raise ValueError('At least one reconciliation ID is required')
        return v


class ReconciliationCancellation(BaseModel):
    """Schema para cancelar conciliaciones"""
    reconciliation_ids: List[uuid.UUID] = Field(description="IDs de conciliaciones a cancelar")
    reason: Optional[str] = Field(None, description="Razón de la cancelación")

    @validator('reconciliation_ids')
    def validate_reconciliation_ids(cls, v):
        """Validar que hay al menos un ID"""
        if not v:
            raise ValueError('At least one reconciliation ID is required')
        return v


# Auto reconciliation schemas
class BankReconciliationAutoRequest(BaseModel):
    """Schema para solicitud de conciliación automática"""
    extract_id: uuid.UUID = Field(description="ID del extracto bancario")
    account_id: Optional[uuid.UUID] = Field(None, description="ID de la cuenta (opcional)")
    tolerance_amount: Optional[Decimal] = Field(Decimal('0.01'), description="Tolerancia de monto")
    tolerance_days: Optional[int] = Field(7, description="Tolerancia de días")
    

class BankReconciliationAutoResponse(BaseModel):
    """Schema para respuesta de conciliación automática"""
    processed_lines: int = Field(description="Líneas procesadas")
    reconciled_lines: int = Field(description="Líneas conciliadas")
    reconciled_amount: Decimal = Field(description="Monto total conciliado")
    unreconciled_lines: int = Field(description="Líneas no conciliadas")
    reconciliations: List[BankReconciliationResponse] = Field(description="Conciliaciones creadas")
