"""
Bank extract schemas for request/response serialization and validation.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from app.models.bank_extract import BankExtractStatus, BankExtractLineType


# Base schemas
class BankExtractBase(BaseModel):
    """Schema base para extractos bancarios"""
    name: str = Field(max_length=100, description="Nombre del extracto")
    reference: Optional[str] = Field(None, max_length=100, description="Referencia del extracto")
    statement_date: date = Field(description="Fecha del estado de cuenta")
    start_date: date = Field(description="Fecha de inicio del período")
    end_date: date = Field(description="Fecha de fin del período")
    starting_balance: Decimal = Field(description="Saldo inicial")
    ending_balance: Decimal = Field(description="Saldo final")
    currency_code: str = Field(default="USD", max_length=3, description="Código de moneda")
    description: Optional[str] = Field(None, description="Descripción del extracto")
    notes: Optional[str] = Field(None, description="Notas adicionales")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validar que la fecha de fin sea posterior a la de inicio"""
        start_date = values.get('start_date')
        if start_date and v < start_date:
            raise ValueError('End date must be after start date')
        return v

    @validator('statement_date')
    def validate_statement_date(cls, v, values):
        """Validar que la fecha del estado esté en el rango del período"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        if start_date and v < start_date:
            raise ValueError('Statement date must be within the period range')
        if end_date and v > end_date:
            raise ValueError('Statement date must be within the period range')
        return v


class BankExtractCreate(BankExtractBase):
    """Schema para crear extractos bancarios"""
    account_id: uuid.UUID = Field(description="ID de la cuenta bancaria")
    file_name: Optional[str] = Field(None, max_length=255, description="Nombre del archivo")


class BankExtractUpdate(BaseModel):
    """Schema para actualizar extractos bancarios"""
    name: Optional[str] = Field(None, max_length=100)
    reference: Optional[str] = Field(None, max_length=100)
    ending_balance: Optional[Decimal] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class BankExtractResponse(BankExtractBase):
    """Schema de respuesta para extractos bancarios"""
    id: uuid.UUID
    account_id: uuid.UUID
    status: BankExtractStatus
    file_name: Optional[str]
    file_hash: Optional[str]
    total_lines: int
    reconciled_lines: int
    pending_lines: int
    is_fully_reconciled: bool
    created_by_id: uuid.UUID
    imported_at: datetime
    reconciled_by_id: Optional[uuid.UUID]
    reconciled_at: Optional[datetime]

    class Config:
        from_attributes = True


# Bank extract line schemas
class BankExtractLineBase(BaseModel):
    """Schema base para líneas de extracto"""
    sequence: int = Field(ge=1, description="Secuencia de la línea")
    transaction_date: date = Field(description="Fecha de la transacción")
    value_date: Optional[date] = Field(None, description="Fecha valor")
    reference: Optional[str] = Field(None, max_length=100, description="Referencia")
    bank_reference: Optional[str] = Field(None, max_length=100, description="Referencia bancaria")
    check_number: Optional[str] = Field(None, max_length=50, description="Número de cheque")
    description: str = Field(description="Descripción del movimiento")
    additional_info: Optional[str] = Field(None, description="Información adicional")
    line_type: BankExtractLineType = Field(description="Tipo de línea")
    debit_amount: Decimal = Field(ge=0, description="Monto débito")
    credit_amount: Decimal = Field(ge=0, description="Monto crédito")
    balance: Optional[Decimal] = Field(None, description="Saldo después del movimiento")
    partner_name: Optional[str] = Field(None, max_length=255, description="Nombre del tercero")
    partner_account: Optional[str] = Field(None, max_length=50, description="Cuenta del tercero")

    @validator('debit_amount')
    def validate_debit_amount(cls, v, values):
        """Validar que solo uno de los montos esté presente"""
        credit_amount = values.get('credit_amount', 0)
        
        if v > 0 and credit_amount > 0:
            raise ValueError('Only one of debit_amount or credit_amount should be greater than zero')
        if v == 0 and credit_amount == 0:
            raise ValueError('Either debit_amount or credit_amount must be greater than zero')
        
        return v

    @validator('credit_amount')
    def validate_credit_amount(cls, v, values):
        """Validar que solo uno de los montos esté presente"""
        debit_amount = values.get('debit_amount', 0)
        
        if v > 0 and debit_amount > 0:
            raise ValueError('Only one of debit_amount or credit_amount should be greater than zero')
        
        return v


class BankExtractLineCreate(BankExtractLineBase):
    """Schema para crear líneas de extracto"""
    pass


class BankExtractLineUpdate(BaseModel):
    """Schema para actualizar líneas de extracto"""
    description: Optional[str] = None
    additional_info: Optional[str] = None
    partner_name: Optional[str] = Field(None, max_length=255)
    partner_account: Optional[str] = Field(None, max_length=50)


class BankExtractLineResponse(BankExtractLineBase):
    """Schema de respuesta para líneas de extracto"""
    id: uuid.UUID
    bank_extract_id: uuid.UUID
    amount: Decimal
    is_debit: bool
    is_credit: bool
    is_reconciled: bool
    reconciled_amount: Decimal
    pending_amount: Decimal
    is_fully_reconciled: bool
    created_by_id: uuid.UUID
    reconciled_by_id: Optional[uuid.UUID]
    reconciled_at: Optional[datetime]

    class Config:
        from_attributes = True


class BankExtractWithLines(BankExtractResponse):
    """Schema de extracto con líneas"""
    lines: List[BankExtractLineResponse] = Field(default_factory=list)


# Bulk import schemas
class BankExtractImport(BankExtractCreate):
    """Schema para importar extracto con líneas"""
    lines: List[BankExtractLineCreate] = Field(description="Líneas del extracto")

    @validator('lines')
    def validate_lines(cls, v):
        """Validar que hay al menos una línea"""
        if not v:
            raise ValueError('At least one extract line is required')
        return v


class BankExtractImportResult(BaseModel):
    """Schema para resultado de importación"""
    extract_id: uuid.UUID
    total_lines: int
    imported_lines: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# Summary schemas
class BankExtractSummary(BaseModel):
    """Schema para resumen de extractos"""
    total_extracts: int = Field(description="Total de extractos")
    total_lines: int = Field(description="Total de líneas")
    reconciled_lines: int = Field(description="Líneas conciliadas")
    pending_lines: int = Field(description="Líneas pendientes")
    total_debits: Decimal = Field(description="Total débitos")
    total_credits: Decimal = Field(description="Total créditos")
    by_status: dict = Field(description="Distribución por estado")
    by_account: dict = Field(description="Distribución por cuenta")


class BankExtractListResponse(BaseModel):
    """Schema para lista de extractos"""
    extracts: List[BankExtractResponse]
    total: int
    page: int
    size: int
    pages: int


# Status update schemas
class BankExtractStatusUpdate(BaseModel):
    """Schema para actualizar estado de extracto"""
    status: BankExtractStatus = Field(description="Nuevo estado")
    notes: Optional[str] = Field(None, description="Notas del cambio de estado")


# Reconciliation validation
class BankExtractValidation(BaseModel):
    """Schema para validación de extracto"""
    is_valid: bool = Field(description="Si el extracto es válido")
    balance_difference: Decimal = Field(description="Diferencia de saldo")
    total_debits: Decimal = Field(description="Total débitos")
    total_credits: Decimal = Field(description="Total créditos")
    calculated_ending_balance: Decimal = Field(description="Saldo final calculado")
    errors: List[str] = Field(default_factory=list, description="Errores encontrados")
    warnings: List[str] = Field(default_factory=list, description="Advertencias")
