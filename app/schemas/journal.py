from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field, validator, ConfigDict

from app.models.journal import JournalType


class AccountRead(BaseModel):
    """Esquema simplificado para cuentas en journals"""
    id: str
    code: str
    name: str
    account_type: str
    
    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    """Esquema simplificado para usuarios en journals"""
    id: str
    full_name: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)


class JournalBase(BaseModel):
    """Esquema base para diarios"""
    name: str = Field(
        ..., 
        max_length=100,
        description="Nombre descriptivo del diario"
    )
    code: str = Field(
        ..., 
        max_length=10,
        description="Código único del diario"
    )
    type: JournalType = Field(
        ...,
        description="Tipo de diario (sale, purchase, cash, bank, miscellaneous)"
    )
    sequence_prefix: str = Field(
        ..., 
        max_length=10,
        description="Prefijo único para la secuencia de numeración"
    )
    default_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta contable por defecto"
    )
    sequence_padding: int = Field(
        4,
        ge=1,
        le=10,
        description="Número de dígitos para rellenar con ceros (ej: 0001)"
    )
    include_year_in_sequence: bool = Field(
        True,
        description="Si incluir el año en la secuencia (ej: VEN/2025/0001)"
    )
    reset_sequence_yearly: bool = Field(
        True,
        description="Si resetear la secuencia cada año"
    )
    requires_validation: bool = Field(
        False,
        description="Si los asientos en este diario requieren validación"
    )
    allow_manual_entries: bool = Field(
        True,
        description="Si permite asientos manuales en este diario"
    )
    is_active: bool = Field(
        True,
        description="Si el diario está activo"
    )
    description: Optional[str] = Field(
        None,
        description="Descripción del propósito del diario"
    )

    @validator('sequence_prefix')
    def validate_sequence_prefix(cls, v):
        if not v or not v.strip():
            raise ValueError('El prefijo de secuencia es obligatorio')
        if len(v.strip()) < 2:
            raise ValueError('El prefijo de secuencia debe tener al menos 2 caracteres')
        return v.strip().upper()

    @validator('code')
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError('El código es obligatorio')
        return v.strip().upper()

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre es obligatorio')
        return v.strip()


class JournalCreate(JournalBase):
    """Esquema para crear diarios"""
    pass


class JournalUpdate(BaseModel):
    """Esquema para actualizar diarios"""
    name: Optional[str] = Field(
        None, 
        max_length=100,
        description="Nombre descriptivo del diario"
    )
    default_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta contable por defecto"
    )
    sequence_padding: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Número de dígitos para rellenar con ceros"
    )
    include_year_in_sequence: Optional[bool] = Field(
        None,
        description="Si incluir el año en la secuencia"
    )
    reset_sequence_yearly: Optional[bool] = Field(
        None,
        description="Si resetear la secuencia cada año"
    )
    requires_validation: Optional[bool] = Field(
        None,
        description="Si los asientos requieren validación"
    )
    allow_manual_entries: Optional[bool] = Field(
        None,
        description="Si permite asientos manuales"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Si el diario está activo"
    )
    description: Optional[str] = Field(
        None,
        description="Descripción del diario"
    )

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('El nombre no puede estar vacío')
            return v.strip()
        return v


class JournalRead(JournalBase):
    """Esquema para leer diarios"""
    id: uuid.UUID
    current_sequence_number: int
    last_sequence_reset_year: Optional[int]
    total_journal_entries: int = Field(
        default=0,
        description="Total de asientos contables en este diario"
    )
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_journal_with_count(cls, journal, count: int = 0):
        """Crear instancia desde Journal con conteo manual"""
        data = {
            'id': journal.id,
            'name': journal.name,
            'code': journal.code,
            'type': journal.type,
            'sequence_prefix': journal.sequence_prefix,
            'default_account_id': journal.default_account_id,
            'sequence_padding': journal.sequence_padding,
            'include_year_in_sequence': journal.include_year_in_sequence,
            'reset_sequence_yearly': journal.reset_sequence_yearly,
            'requires_validation': journal.requires_validation,
            'allow_manual_entries': journal.allow_manual_entries,
            'is_active': journal.is_active,
            'description': journal.description,
            'current_sequence_number': journal.current_sequence_number,
            'last_sequence_reset_year': journal.last_sequence_reset_year,
            'total_journal_entries': count,
            'created_at': journal.created_at,
            'updated_at': journal.updated_at,
            'created_by_id': journal.created_by_id
        }
        return cls(**data)


class JournalDetail(JournalRead):
    """Esquema detallado para diarios incluyendo relaciones"""
    default_account: Optional[AccountRead] = None
    created_by: Optional[UserRead] = None
    
    @classmethod
    def from_journal_with_count(cls, journal, count: int = 0):
        """Crear instancia desde Journal con conteo manual y relaciones"""
        data = {
            'id': journal.id,
            'name': journal.name,
            'code': journal.code,
            'type': journal.type,
            'sequence_prefix': journal.sequence_prefix,
            'default_account_id': journal.default_account_id,
            'sequence_padding': journal.sequence_padding,
            'include_year_in_sequence': journal.include_year_in_sequence,
            'reset_sequence_yearly': journal.reset_sequence_yearly,
            'requires_validation': journal.requires_validation,
            'allow_manual_entries': journal.allow_manual_entries,
            'is_active': journal.is_active,
            'description': journal.description,
            'current_sequence_number': journal.current_sequence_number,
            'last_sequence_reset_year': journal.last_sequence_reset_year,
            'total_journal_entries': count,
            'created_at': journal.created_at,
            'updated_at': journal.updated_at,
            'created_by_id': journal.created_by_id,
            'default_account': journal.default_account,
            'created_by': journal.created_by
        }
        return cls(**data)


class JournalListItem(BaseModel):
    """Esquema para listado de diarios"""
    id: uuid.UUID
    name: str
    code: str
    type: JournalType
    sequence_prefix: str
    is_active: bool
    current_sequence_number: int
    total_journal_entries: int = 0
    created_at: datetime
    default_account: Optional[AccountRead] = None

    model_config = ConfigDict(from_attributes=True)


class JournalFilter(BaseModel):
    """Esquema para filtros de búsqueda de diarios"""
    type: Optional[JournalType] = Field(
        None,
        description="Filtrar por tipo de diario"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Filtrar por estado activo"
    )
    search: Optional[str] = Field(
        None,
        max_length=100,
        description="Buscar en nombre, código o descripción"
    )


class JournalSequenceInfo(BaseModel):
    """Información de la secuencia de numeración de un diario"""
    id: uuid.UUID
    name: str
    code: str
    sequence_prefix: str
    current_sequence_number: int
    next_sequence_number: str = Field(
        ...,
        description="Próximo número de secuencia que se generará"
    )
    include_year_in_sequence: bool
    reset_sequence_yearly: bool
    last_sequence_reset_year: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class JournalResetSequence(BaseModel):
    """Esquema para resetear la secuencia de un diario"""
    confirm: bool = Field(
        ...,
        description="Confirmación para resetear la secuencia"
    )
    reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Razón para resetear la secuencia"
    )

    @validator('confirm')
    def validate_confirm(cls, v):
        if not v:
            raise ValueError('Debe confirmar el reseteo de la secuencia')
        return v


class JournalStats(BaseModel):
    """Estadísticas de un diario"""
    id: uuid.UUID
    name: str
    code: str
    type: JournalType
    total_entries: int = Field(
        0,
        description="Total de asientos contables"
    )
    total_entries_current_year: int = Field(
        0,
        description="Total de asientos del año actual"
    )
    total_entries_current_month: int = Field(
        0,
        description="Total de asientos del mes actual"
    )
    last_entry_date: Optional[datetime] = Field(
        None,
        description="Fecha del último asiento"
    )
    avg_entries_per_month: float = Field(
        0.0,
        description="Promedio de asientos por mes"
    )

    model_config = ConfigDict(from_attributes=True)
