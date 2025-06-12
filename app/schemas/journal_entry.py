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

    @model_validator(mode='after')
    def validate_amounts(self):
        """Valida que solo uno de los montos sea mayor que cero"""
        debit = self.debit_amount or Decimal('0')
        credit = self.credit_amount or Decimal('0')
        
        if (debit > 0 and credit > 0) or (debit == 0 and credit == 0):
            raise ValueError("Una línea debe tener monto en débito O crédito, no ambos o ninguno")
        
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


class JournalEntryLineRead(JournalEntryLineBase):
    """Schema para leer líneas de asiento"""
    id: uuid.UUID
    journal_entry_id: uuid.UUID
    line_number: int
    created_at: datetime
    updated_at: datetime
    
    # Campos relacionados
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    third_party_code: Optional[str] = None
    third_party_name: Optional[str] = None
    cost_center_code: Optional[str] = None
    cost_center_name: Optional[str] = None
    amount: Decimal = Decimal('0')  # Monto absoluto
    movement_type: str = "debit"    # "debit" o "credit"
    
    model_config = ConfigDict(from_attributes=True)


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
    """Schema para cancelar asiento"""
    reason: str = Field(..., min_length=1, max_length=500, description="Razón para cancelar")


# Esquemas para listados
class JournalEntrySummary(BaseModel):
    """Schema resumido para listados"""
    id: uuid.UUID
    number: str
    entry_date: date
    description: str
    status: JournalEntryStatus
    entry_type: JournalEntryType
    total_debit: Decimal
    created_by_name: Optional[str] = None
    created_at: datetime
    
    @field_validator('entry_date', mode='before')
    @classmethod
    def convert_datetime_to_date(cls, v):
        """Convertir datetime a date si es necesario para compatibilidad con SQLAlchemy"""
        if isinstance(v, datetime):
            return v.date()
        return v
    
    model_config = ConfigDict(from_attributes=True)


class JournalEntryList(BaseModel):
    """Schema para listado paginado de asientos"""
    entries: List[JournalEntrySummary]
    total: int
    page: int
    size: int
    pages: int


# Esquemas para filtros
class JournalEntryFilter(BaseModel):
    """Schema para filtrar asientos"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[JournalEntryStatus] = None
    entry_type: Optional[JournalEntryType] = None
    account_id: Optional[uuid.UUID] = None
    created_by_id: Optional[uuid.UUID] = None
    search: Optional[str] = None  # Búsqueda en descripción/referencia


# Esquemas para importación
class JournalEntryImportLine(BaseModel):
    """Schema para importar líneas de asiento"""
    account_code: str
    description: str
    debit_amount: Optional[Decimal] = None
    credit_amount: Optional[Decimal] = None
    third_party: Optional[str] = None
    cost_center: Optional[str] = None
    reference: Optional[str] = None


class JournalEntryImport(BaseModel):
    """Schema para importar asientos"""
    entry_date: date
    reference: Optional[str] = None
    description: str
    lines: List[JournalEntryImportLine]


class BulkJournalEntryImport(BaseModel):
    """Schema para importación masiva"""
    entries: List[JournalEntryImport]
    validate_only: bool = False  # Solo validar sin guardar


# Esquemas para reportes
class JournalEntryStats(BaseModel):
    """Schema para estadísticas de asientos"""
    total_entries: int
    posted_entries: int
    draft_entries: int
    cancelled_entries: int
    entries_by_type: dict[str, int]
    total_amount_posted: Decimal
    entries_by_month: dict[str, int]


class AccountMovementSummary(BaseModel):
    """Schema para resumen de movimientos por cuenta"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    total_debits: Decimal
    total_credits: Decimal
    net_movement: Decimal
    movement_count: int


class JournalReport(BaseModel):
    """Schema para reporte de libro diario"""
    period_start: date
    period_end: date
    entries: List[JournalEntryDetail]
    total_entries: int
    total_amount: Decimal


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
