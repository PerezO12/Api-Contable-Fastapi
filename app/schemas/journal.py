from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field, validator, field_validator, ConfigDict

from app.models.journal import JournalType
from app.models.bank_journal_config import PaymentDirection, PaymentMode


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
    
    # Configuración de cuentas específicas para pagos
    default_debit_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta débito por defecto"
    )
    default_credit_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta crédito por defecto"
    )
    customer_receivable_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta por cobrar clientes específica"
    )
    supplier_payable_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta por pagar proveedores específica"
    )
    cash_difference_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta para diferencias de caja"
    )
    bank_charges_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta para gastos bancarios"
    )
    currency_exchange_account_id: Optional[uuid.UUID] = Field(
        None,
        description="ID de la cuenta para diferencias de cambio"
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
            'created_by_id': journal.created_by_id,
            # Include related objects if available
            'default_account': getattr(journal, 'default_account', None),
            'created_by': getattr(journal, 'created_by', None),
            'bank_config': getattr(journal, 'bank_config', None)
        }
        return cls(**data)


class JournalDetail(JournalRead):
    """Esquema detallado para diarios incluyendo relaciones"""
    default_account: Optional[AccountRead] = None
    created_by: Optional[UserRead] = None
    bank_config: Optional["BankJournalConfigRead"] = None
    
    @classmethod
    def from_journal_with_count(cls, journal, count: int = 0):
        """Crear instancia desde Journal con conteo manual y relaciones"""
        try:
            # Convertir relaciones si existen
            default_account = None
            if journal.default_account:
                default_account = AccountRead(
                    id=str(journal.default_account.id),
                    code=journal.default_account.code,
                    name=journal.default_account.name,
                    account_type=journal.default_account.account_type
                )
            
            created_by = None
            if journal.created_by:
                created_by = UserRead(
                    id=str(journal.created_by.id),
                    full_name=journal.created_by.full_name,
                    email=journal.created_by.email
                )
            
            # Convertir bank_config si existe
            bank_config = None
            if journal.bank_config:
                from app.schemas.journal import BankJournalConfigRead
                # Convertir manualmente para evitar problemas de UUID y greenlet
                bank_config_data = {
                    'journal_id': str(journal.bank_config.journal_id),
                    'bank_account_number': journal.bank_config.bank_account_number,
                    'bank_account_id': str(journal.bank_config.bank_account_id) if journal.bank_config.bank_account_id else None,
                    'transit_account_id': str(journal.bank_config.transit_account_id) if journal.bank_config.transit_account_id else None,
                    'profit_account_id': str(journal.bank_config.profit_account_id) if journal.bank_config.profit_account_id else None,
                    'loss_account_id': str(journal.bank_config.loss_account_id) if journal.bank_config.loss_account_id else None,
                    'dedicated_payment_sequence': journal.bank_config.dedicated_payment_sequence,
                    'allow_inbound_payments': journal.bank_config.allow_inbound_payments,
                    'inbound_payment_mode': journal.bank_config.inbound_payment_mode,
                    'inbound_receipt_account_id': str(journal.bank_config.inbound_receipt_account_id) if journal.bank_config.inbound_receipt_account_id else None,
                    'allow_outbound_payments': journal.bank_config.allow_outbound_payments,
                    'outbound_payment_mode': journal.bank_config.outbound_payment_mode,
                    'outbound_payment_method': journal.bank_config.outbound_payment_method,
                    'outbound_payment_name': journal.bank_config.outbound_payment_name,
                    'outbound_pending_account_id': str(journal.bank_config.outbound_pending_account_id) if journal.bank_config.outbound_pending_account_id else None,
                    'currency_code': journal.bank_config.currency_code,
                    'allow_currency_exchange': journal.bank_config.allow_currency_exchange,
                    'auto_reconcile': journal.bank_config.auto_reconcile,
                    'description': journal.bank_config.description,
                    # Set related accounts to None since we don't load them here
                    'bank_account': None,
                    'transit_account': None,
                    'profit_account': None,
                    'loss_account': None,
                    'inbound_receipt_account': None,
                    'outbound_pending_account': None,
                }
                bank_config = BankJournalConfigRead(**bank_config_data)
            
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
                'default_account': default_account,
                'created_by': created_by,
                'bank_config': bank_config
            }
            return cls(**data)
        except Exception as e:
            print(f"❌ Error en from_journal_with_count: {e}")
            print(f"❌ Journal: {journal}")
            print(f"❌ Journal.default_account: {journal.default_account}")
            print(f"❌ Journal.created_by: {journal.created_by}")
            raise


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


class JournalDeleteValidation(BaseModel):
    """Schema para validación previa al borrado de journals"""
    journal_id: str
    can_delete: bool
    blocking_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    dependencies: dict = Field(default_factory=dict)  # Información sobre dependencias (ej: journal_entries_count, journal_name)

    model_config = ConfigDict(from_attributes=True)


# Esquemas para configuración bancaria

class BankJournalConfigBase(BaseModel):
    """Esquema base para configuración bancaria"""
    bank_account_number: Optional[str] = Field(
        None,
        max_length=50,
        description="Número de cuenta bancaria"
    )
    bank_account_id: Optional[str] = Field(
        None,
        description="ID de la cuenta bancaria principal"
    )
    transit_account_id: Optional[str] = Field(
        None,
        description="ID de la cuenta transitoria"
    )
    profit_account_id: Optional[str] = Field(
        None,
        description="ID de la cuenta de ganancias"
    )
    loss_account_id: Optional[str] = Field(
        None,
        description="ID de la cuenta de pérdidas"
    )
    dedicated_payment_sequence: bool = Field(
        False,
        description="Usar secuencia dedicada para pagos"
    )
    allow_inbound_payments: bool = Field(
        True,
        description="Permitir pagos entrantes"
    )
    inbound_payment_mode: PaymentMode = Field(
        PaymentMode.MANUAL,
        description="Modo de procesamiento de pagos entrantes"
    )
    inbound_receipt_account_id: Optional[str] = Field(
        None,
        description="ID de la cuenta de recibo para pagos entrantes"
    )
    allow_outbound_payments: bool = Field(
        True,
        description="Permitir pagos salientes"
    )
    outbound_payment_mode: PaymentMode = Field(
        PaymentMode.MANUAL,
        description="Modo de procesamiento de pagos salientes"
    )
    outbound_payment_method: Optional[str] = Field(
        None,
        max_length=50,
        description="Método de pago por defecto para salientes"
    )
    outbound_payment_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Nombre descriptivo para pagos salientes"
    )
    outbound_pending_account_id: Optional[str] = Field(
        None,
        description="ID de la cuenta de pagos pendientes"
    )
    currency_code: str = Field(
        "COP",
        min_length=3,
        max_length=3,
        description="Código de moneda (3 caracteres)"
    )
    allow_currency_exchange: bool = Field(
        False,
        description="Permitir operaciones con múltiples monedas"
    )
    auto_reconcile: bool = Field(
        False,
        description="Intentar conciliación automática"
    )
    description: Optional[str] = Field(
        None,
        description="Descripción de la configuración bancaria"
    )


class BankJournalConfigCreate(BankJournalConfigBase):
    """Esquema para crear configuración bancaria"""
    pass


class BankJournalConfigUpdate(BaseModel):
    """Esquema para actualizar configuración bancaria"""
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_account_id: Optional[str] = None
    transit_account_id: Optional[str] = None
    profit_account_id: Optional[str] = None
    loss_account_id: Optional[str] = None
    dedicated_payment_sequence: Optional[bool] = None
    allow_inbound_payments: Optional[bool] = None
    inbound_payment_mode: Optional[PaymentMode] = None
    inbound_receipt_account_id: Optional[str] = None
    allow_outbound_payments: Optional[bool] = None
    outbound_payment_mode: Optional[PaymentMode] = None
    outbound_payment_method: Optional[str] = Field(None, max_length=50)
    outbound_payment_name: Optional[str] = Field(None, max_length=100)
    outbound_pending_account_id: Optional[str] = None
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3)
    allow_currency_exchange: Optional[bool] = None
    auto_reconcile: Optional[bool] = None
    description: Optional[str] = None


class BankJournalConfigRead(BankJournalConfigBase):
    """Esquema para leer configuración bancaria"""
    journal_id: str
    
    # Cuentas relacionadas (información expandida)
    bank_account: Optional[AccountRead] = None
    transit_account: Optional[AccountRead] = None
    profit_account: Optional[AccountRead] = None
    loss_account: Optional[AccountRead] = None
    inbound_receipt_account: Optional[AccountRead] = None
    outbound_pending_account: Optional[AccountRead] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('journal_id', 'bank_account_id', 'transit_account_id', 
                     'profit_account_id', 'loss_account_id', 'inbound_receipt_account_id', 
                     'outbound_pending_account_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convertir UUID a string"""
        if v is None:
            return v
        # Convertir UUID a string
        import uuid
        if isinstance(v, uuid.UUID):
            return str(v)
        if hasattr(v, '__str__'):
            return str(v)
        return v


class BankJournalConfigValidation(BaseModel):
    """Esquema para validación de configuración bancaria"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class JournalWithBankConfig(JournalRead):
    """Esquema para diarios con configuración bancaria incluida"""
    bank_config: Optional["BankJournalConfigRead"] = None
    
    model_config = ConfigDict(from_attributes=True)
