import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.journal_entry import JournalEntryStatus, JournalEntryType


# Esquemas para líneas de asiento
class JournalEntryLineBase(BaseModel):
    """Schema base para líneas de asiento contable"""
    account_id: uuid.UUID = Field(..., description="ID de la cuenta contable")
    description: str = Field(..., min_length=1, max_length=500, description="Descripción del movimiento")
    debit_amount: Decimal = Field(Decimal('0'), ge=0, description="Monto débito")
    credit_amount: Decimal = Field(Decimal('0'), ge=0, description="Monto crédito")
    third_party_id: Optional[uuid.UUID] = Field(None, description="ID del tercero")
    cost_center_id: Optional[uuid.UUID] = Field(None, description="ID del centro de costo")
    reference: Optional[str] = Field(None, max_length=100, description="Referencia adicional")
    
    # Nuevos campos para fechas y condiciones de pago
    invoice_date: Optional[date] = Field(None, description="Fecha de la factura (si es diferente a la fecha del asiento)")
    due_date: Optional[date] = Field(None, description="Fecha de vencimiento manual")
    payment_terms_id: Optional[uuid.UUID] = Field(None, description="ID de las condiciones de pago")

    @model_validator(mode='after')
    def validate_amounts(self):
        """Valida que solo uno de los montos sea mayor que cero"""
        debit = self.debit_amount or Decimal('0')
        credit = self.credit_amount or Decimal('0')
        
        if (debit > 0 and credit > 0) or (debit == 0 and credit == 0):
            raise ValueError("Una línea debe tener monto en débito O crédito, no ambos o ninguno")
        
        return self

    @model_validator(mode='after')
    def validate_payment_terms_and_due_date(self):
        """Valida que no se especifiquen tanto condiciones de pago como fecha de vencimiento manual"""
        if self.payment_terms_id and self.due_date:
            raise ValueError("No se puede especificar tanto condiciones de pago como fecha de vencimiento manual")
        
        return self


class JournalEntryLineCreate(JournalEntryLineBase):
    """Schema para crear líneas de asiento"""
    pass


class JournalEntryLineUpdate(BaseModel):
    """Schema para actualizar líneas de asiento"""
    account_id: Optional[uuid.UUID] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    debit_amount: Optional[Decimal] = Field(None, ge=0)
    credit_amount: Optional[Decimal] = Field(None, ge=0)
    third_party_id: Optional[uuid.UUID] = Field(None, description="ID del tercero")
    cost_center_id: Optional[uuid.UUID] = Field(None, description="ID del centro de costo")
    reference: Optional[str] = Field(None, max_length=100)
    invoice_date: Optional[date] = Field(None, description="Fecha de la factura")
    due_date: Optional[date] = Field(None, description="Fecha de vencimiento manual")
    payment_terms_id: Optional[uuid.UUID] = Field(None, description="ID de las condiciones de pago")


class JournalEntryLineRead(JournalEntryLineBase):
    """Schema para leer líneas de asiento"""
    id: uuid.UUID
    journal_entry_id: uuid.UUID
    line_number: int
    created_at: datetime
    updated_at: datetime
    
    # Campos relacionados - Cuenta
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    
    # Campos relacionados - Tercero (información completa)
    third_party_code: Optional[str] = None
    third_party_name: Optional[str] = None
    third_party_document_type: Optional[str] = None
    third_party_document_number: Optional[str] = None
    third_party_tax_id: Optional[str] = None
    third_party_email: Optional[str] = None
    third_party_phone: Optional[str] = None
    third_party_address: Optional[str] = None
    third_party_city: Optional[str] = None
    third_party_type: Optional[str] = None
    
    # Campos relacionados - Centro de Costo
    cost_center_code: Optional[str] = None
    cost_center_name: Optional[str] = None
    
    # Campos relacionados - Términos de Pago (información completa)
    payment_terms_code: Optional[str] = None
    payment_terms_name: Optional[str] = None
    payment_terms_description: Optional[str] = None
    
    # Campos calculados
    amount: Decimal = Decimal('0')  # Monto absoluto
    movement_type: str = "debit"    # "debit" o "credit"
    effective_invoice_date: Optional[date] = None  # Fecha de factura efectiva
    effective_due_date: Optional[date] = None      # Fecha de vencimiento efectiva
    
    model_config = ConfigDict(from_attributes=True)


class JournalEntryLineDetail(JournalEntryLineRead):
    """Schema para detalles completos de línea con cronograma de pagos"""
    payment_schedule: List[dict] = []  # Cronograma de pagos calculado


# Esquemas para asientos contables
class JournalEntryBase(BaseModel):
    """Schema base para asientos contables"""
    entry_date: date = Field(..., description="Fecha del asiento")
    reference: Optional[str] = Field(None, max_length=100, description="Referencia externa")
    description: str = Field(..., min_length=1, max_length=1000, description="Descripción del asiento")
    entry_type: JournalEntryType = Field(JournalEntryType.MANUAL, description="Tipo de asiento")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas adicionales")
    
    @field_validator('entry_date', mode='before')
    @classmethod
    def convert_datetime_to_date(cls, v):
        """Convertir datetime a date si es necesario para compatibilidad con SQLAlchemy"""
        if isinstance(v, datetime):
            return v.date()
        return v


class JournalEntryCreate(JournalEntryBase):
    """Schema para crear asientos contables"""
    lines: List[JournalEntryLineCreate] = Field(..., min_length=2, description="Líneas del asiento (mínimo 2)")
    
    @field_validator('lines')
    @classmethod
    def validate_lines_balance(cls, v):
        """Valida que el asiento esté balanceado"""
        if len(v) < 2:
            raise ValueError("Un asiento debe tener al menos 2 líneas")
        
        total_debit = sum(line.debit_amount or Decimal('0') for line in v)
        total_credit = sum(line.credit_amount or Decimal('0') for line in v)
        
        if total_debit != total_credit:
            raise ValueError(f"El asiento no está balanceado: Débitos={total_debit}, Créditos={total_credit}")
        
        if total_debit == 0:
            raise ValueError("El asiento debe tener movimientos con montos mayores a cero")
        
        return v


class JournalEntryUpdate(BaseModel):
    """Schema para actualizar asientos contables (solo borradores)"""
    entry_date: Optional[date] = None
    reference: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)


class JournalEntryRead(JournalEntryBase):
    """Schema para leer asientos contables"""
    id: uuid.UUID
    number: str
    status: JournalEntryStatus
    total_debit: Decimal
    total_credit: Decimal
    created_by_id: uuid.UUID
    posted_by_id: Optional[uuid.UUID] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Propiedades calculadas
    is_balanced: bool = True
    can_be_posted: bool = False
    can_be_edited: bool = True
    
    # Información del usuario
    created_by_name: Optional[str] = None
    posted_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class JournalEntryDetail(JournalEntryRead):
    """Schema para detalles completos del asiento con líneas"""
    lines: List[JournalEntryLineRead] = []


# Esquemas para operaciones
class JournalEntryPost(BaseModel):
    """Schema para contabilizar asiento"""
    reason: Optional[str] = Field(None, max_length=500, description="Razón para contabilizar")


class JournalEntryCancel(BaseModel):
    """Schema para anulación de asiento contable"""
    reason: str = Field(..., min_length=1, max_length=500, description="Razón de la anulación")


class JournalEntryFilter(BaseModel):
    """Schema para filtros de búsqueda de asientos contables"""
    start_date: Optional[date] = Field(None, description="Fecha inicial")
    end_date: Optional[date] = Field(None, description="Fecha final")
    status: Optional[List[JournalEntryStatus]] = Field(None, description="Estados a filtrar")
    entry_type: Optional[List[JournalEntryType]] = Field(None, description="Tipos de asiento")
    created_by_id: Optional[uuid.UUID] = Field(None, description="ID del usuario creador")
    account_id: Optional[uuid.UUID] = Field(None, description="ID de cuenta específica")
    min_amount: Optional[Decimal] = Field(None, description="Monto mínimo")
    max_amount: Optional[Decimal] = Field(None, description="Monto máximo")
    search_text: Optional[str] = Field(None, description="Texto a buscar en descripción o referencia")


class JournalEntrySummary(BaseModel):
    """Schema para resumen de asientos contables"""
    id: uuid.UUID
    number: str
    description: str
    entry_date: date
    status: JournalEntryStatus
    entry_type: JournalEntryType
    total_debit: Decimal
    total_credit: Decimal
    created_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class JournalEntryResetToDraft(BaseModel):
    """Schema para restablecer asiento a borrador"""
    reason: str = Field(..., min_length=1, max_length=500, description="Razón para restablecer a borrador")


class JournalEntryResetToDraftValidation(BaseModel):
    """Schema para validación de restablecimiento a borrador"""
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    journal_entry_description: str
    current_status: JournalEntryStatus
    can_reset: bool
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryResetToDraft(BaseModel):
    """Schema para restablecimiento masivo a borrador de asientos"""
    journal_entry_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100, description="Lista de IDs de asientos a restablecer")
    force_reset: bool = Field(False, description="Forzar restablecimiento ignorando advertencias")
    reason: str = Field(..., min_length=1, max_length=500, description="Razón para el restablecimiento masivo")
    
    @field_validator('journal_entry_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        """Validar que los IDs sean únicos"""
        if len(v) != len(set(v)):
            raise ValueError("Los IDs de asientos deben ser únicos")
        return v


class BulkJournalEntryResetToDraftResult(BaseModel):
    """Schema para resultado de restablecimiento masivo a borrador"""
    total_requested: int
    total_reset: int
    total_failed: int
    reset_entries: List[JournalEntryResetToDraftValidation] = []
    failed_entries: List[JournalEntryResetToDraftValidation] = []
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryApprove(BaseModel):
    """Schema para aprobación masiva de asientos"""
    journal_entry_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100, description="Lista de IDs de asientos a aprobar")
    force_approve: bool = Field(False, description="Forzar aprobación ignorando advertencias")
    reason: Optional[str] = Field(None, max_length=500, description="Razón para la aprobación masiva")
    
    @field_validator('journal_entry_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        """Validar que los IDs sean únicos"""
        if len(v) != len(set(v)):
            raise ValueError("Los IDs de asientos deben ser únicos")
        return v


class JournalEntryApproveValidation(BaseModel):
    """Schema para validación de aprobación"""
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    journal_entry_description: str
    current_status: JournalEntryStatus
    can_approve: bool
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryApproveResult(BaseModel):
    """Schema para resultado de aprobación masiva"""
    total_requested: int
    total_approved: int
    total_failed: int
    approved_entries: List[JournalEntryApproveValidation] = []
    failed_entries: List[JournalEntryApproveValidation] = []
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryPost(BaseModel):
    """Schema para contabilización masiva de asientos"""
    journal_entry_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100, description="Lista de IDs de asientos a contabilizar")
    force_post: bool = Field(False, description="Forzar contabilización ignorando advertencias")
    reason: Optional[str] = Field(None, max_length=500, description="Razón para la contabilización masiva")
    
    @field_validator('journal_entry_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        """Validar que los IDs sean únicos"""
        if len(v) != len(set(v)):
            raise ValueError("Los IDs de asientos deben ser únicos")
        return v


class JournalEntryPostValidation(BaseModel):
    """Schema para validación de contabilización"""
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    journal_entry_description: str
    current_status: JournalEntryStatus
    can_post: bool
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryPostResult(BaseModel):
    """Schema para resultado de contabilización masiva"""
    total_requested: int
    total_posted: int
    total_failed: int
    posted_entries: List[JournalEntryPostValidation] = []
    failed_entries: List[JournalEntryPostValidation] = []
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryCancel(BaseModel):
    """Schema para cancelación masiva de asientos"""
    journal_entry_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100, description="Lista de IDs de asientos a cancelar")
    force_cancel: bool = Field(False, description="Forzar cancelación ignorando advertencias")
    reason: str = Field(..., min_length=1, max_length=500, description="Razón para la cancelación masiva")
    
    @field_validator('journal_entry_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        """Validar que los IDs sean únicos"""
        if len(v) != len(set(v)):
            raise ValueError("Los IDs de asientos deben ser únicos")
        return v


class JournalEntryCancelValidation(BaseModel):
    """Schema para validación de cancelación"""
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    journal_entry_description: str
    current_status: JournalEntryStatus
    can_cancel: bool
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryCancelResult(BaseModel):
    """Schema para resultado de cancelación masiva"""
    total_requested: int
    total_cancelled: int
    total_failed: int
    cancelled_entries: List[JournalEntryCancelValidation] = []
    failed_entries: List[JournalEntryCancelValidation] = []
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryReverse(BaseModel):
    """Schema para reversión masiva de asientos"""
    journal_entry_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=50, description="Lista de IDs de asientos a revertir (máximo 50)")
    force_reverse: bool = Field(False, description="Forzar reversión ignorando advertencias")
    reason: str = Field(..., min_length=1, max_length=500, description="Razón para la reversión masiva")
    
    @field_validator('journal_entry_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        """Validar que los IDs sean únicos"""
        if len(v) != len(set(v)):
            raise ValueError("Los IDs de asientos deben ser únicos")
        return v


class JournalEntryReverseValidation(BaseModel):
    """Schema para validación de reversión"""
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    journal_entry_description: str
    current_status: JournalEntryStatus
    can_reverse: bool
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryReverseResult(BaseModel):
    """Schema para resultado de reversión masiva"""
    total_requested: int
    total_reversed: int
    total_failed: int
    reversed_entries: List[JournalEntryReverseValidation] = []
    failed_entries: List[JournalEntryReverseValidation] = []
    created_reversal_entries: List[str] = []  # Números de los asientos de reversión creados
    errors: List[str] = []
    warnings: List[str] = []


# Esquemas para validación
class JournalEntryValidation(BaseModel):
    """Schema para validación de asientos"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    balance_check: bool
    line_count: int


# Esquemas para operaciones masivas de eliminación
class JournalEntryDeleteValidation(BaseModel):
    """Schema para validación individual de eliminación de asiento"""
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    journal_entry_description: str
    status: JournalEntryStatus
    can_delete: bool
    errors: List[str] = []
    warnings: List[str] = []


class BulkJournalEntryDelete(BaseModel):
    """Schema para eliminación masiva de asientos"""
    journal_entry_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100, description="Lista de IDs de asientos a eliminar")
    force_delete: bool = Field(False, description="Forzar eliminación ignorando advertencias")
    reason: Optional[str] = Field(None, max_length=500, description="Razón para la eliminación masiva")
    
    @field_validator('journal_entry_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        """Validar que los IDs sean únicos"""
        if len(v) != len(set(v)):
            raise ValueError("Los IDs de asientos deben ser únicos")
        return v


class BulkJournalEntryDeleteResult(BaseModel):
    """Schema para resultado de eliminación masiva de asientos"""
    total_requested: int
    total_deleted: int
    total_failed: int
    deleted_entries: List[JournalEntryDeleteValidation] = []
    failed_entries: List[JournalEntryDeleteValidation] = []
    errors: List[str] = []
    warnings: List[str] = []


# Additional response schemas for API
class JournalEntryResponse(JournalEntryRead):
    """Standard API response for journal entries"""
    pass


class JournalEntryDetailResponse(JournalEntryDetail):
    """Detailed API response for journal entries with lines"""
    pass


class JournalEntryListResponse(BaseModel):
    """Paginated list response for journal entries"""
    items: List[JournalEntryResponse]
    total: int
    skip: int
    limit: int


class JournalEntryStatistics(BaseModel):
    """Statistics response for journal entries"""
    total_entries: int
    draft_entries: int
    approved_entries: int
    posted_entries: int
    cancelled_entries: int
    total_debit_amount: Decimal
    total_credit_amount: Decimal
    entries_this_month: int
    entries_this_year: int
