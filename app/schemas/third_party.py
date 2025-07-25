"""
Schemas for Third Party functionality.
Includes customers, suppliers, employees and other business partners.
"""
import re
import uuid
from decimal import Decimal
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr

from app.models.third_party import ThirdPartyType, DocumentType
from app.utils.enum_validators import create_enum_validator


# Schemas base
class ThirdPartyBase(BaseModel):
    """Schema base para terceros"""
    code: str = Field(..., min_length=1, max_length=20, description="Código único del tercero")
    name: str = Field(..., min_length=2, max_length=200, description="Nombre o razón social")
    commercial_name: Optional[str] = Field(None, max_length=200, description="Nombre comercial")
    third_party_type: ThirdPartyType = Field(..., description="Tipo de tercero")
    document_type: DocumentType = Field(..., description="Tipo de documento")
    document_number: str = Field(..., min_length=1, max_length=50, description="Número de documento")
    tax_id: Optional[str] = Field(None, max_length=50, description="ID fiscal (RUT, NIT, etc.)")
    
    # Información de contacto
    email: Optional[str] = Field(None, max_length=254, description="Correo electrónico")
    phone: Optional[str] = Field(None, max_length=20, description="Teléfono")
    mobile: Optional[str] = Field(None, max_length=20, description="Móvil")
    website: Optional[str] = Field(None, max_length=255, description="Sitio web")
    
    # Dirección
    address: Optional[str] = Field(None, max_length=500, description="Dirección")
    city: Optional[str] = Field(None, max_length=100, description="Ciudad")
    state: Optional[str] = Field(None, max_length=100, description="Estado/Provincia")
    country: Optional[str] = Field(None, max_length=100, description="País")
    postal_code: Optional[str] = Field(None, max_length=20, description="Código postal")
    
    # Información comercial
    credit_limit: Optional[str] = Field(None, max_length=20, description="Límite de crédito")
    payment_terms: Optional[str] = Field(None, max_length=100, description="Términos de pago")
    discount_percentage: Optional[str] = Field(None, max_length=10, description="Porcentaje de descuento")
    
    # Información bancaria
    bank_name: Optional[str] = Field(None, max_length=200, description="Nombre del banco")
    bank_account: Optional[str] = Field(None, max_length=50, description="Número de cuenta bancaria")
    
    # Cuentas contables específicas del tercero
    receivable_account_id: Optional[uuid.UUID] = Field(None, description="Cuenta por cobrar específica para este cliente")
    payable_account_id: Optional[uuid.UUID] = Field(None, description="Cuenta por pagar específica para este proveedor")
    
    # Estado
    is_active: bool = Field(True, description="Si el tercero está activo")
    is_tax_withholding_agent: bool = Field(False, description="Si es agente de retención")
      # Metadata
    notes: Optional[str] = Field(None, max_length=1000, description="Notas adicionales")
    internal_code: Optional[str] = Field(None, max_length=50, description="Código interno adicional")

    @field_validator('third_party_type', mode='before')
    @classmethod
    def validate_third_party_type(cls, v):
        """Valida el tipo de tercero de forma case-insensitive"""
        return create_enum_validator(ThirdPartyType)(v)

    @field_validator('document_type', mode='before')
    @classmethod
    def validate_document_type(cls, v):
        """Valida el tipo de documento de forma case-insensitive"""
        return create_enum_validator(DocumentType)(v)

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v):
        """Valida el formato del código"""
        if not v or not v.strip():
            raise ValueError("El código no puede estar vacío")
        
        # Permitir caracteres alfanuméricos Unicode, puntos, guiones y guiones bajos
        # Excluir solo caracteres de control y espacios en blanco
        if not re.match(r'^[^\s\x00-\x1f\x7f-\x9f]+$', v.strip()):
            raise ValueError("El código no puede contener caracteres de control o espacios")
        
        return v.strip().upper()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Valida y limpia el nombre"""
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

    @field_validator('document_number')
    @classmethod
    def validate_document_number(cls, v):
        """Valida el número de documento"""
        if not v or not v.strip():
            raise ValueError("El número de documento es requerido")
        return v.strip()

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Valida el formato del email si está presente"""
        if v and v.strip():
            if '@' not in v:
                raise ValueError("El formato del email es inválido")
            return v.strip().lower()
        return v


class ThirdPartyCreate(ThirdPartyBase):
    """Schema para crear terceros"""
    pass


class ThirdPartyUpdate(BaseModel):
    """Schema para actualizar terceros"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    commercial_name: Optional[str] = Field(None, max_length=200)
    third_party_type: Optional[ThirdPartyType] = None
    document_type: Optional[DocumentType] = None
    document_number: Optional[str] = Field(None, min_length=1, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    
    # Información de contacto
    email: Optional[str] = Field(None, max_length=254)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    
    # Dirección
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Información comercial
    credit_limit: Optional[str] = Field(None, max_length=20)
    payment_terms: Optional[str] = Field(None, max_length=100)
    discount_percentage: Optional[str] = Field(None, max_length=10)
    
    # Información bancaria
    bank_name: Optional[str] = Field(None, max_length=200)
    bank_account: Optional[str] = Field(None, max_length=50)
    
    # Cuentas contables específicas del tercero
    receivable_account_id: Optional[uuid.UUID] = Field(None, description="Cuenta por cobrar específica para este cliente")
    payable_account_id: Optional[uuid.UUID] = Field(None, description="Cuenta por pagar específica para este proveedor")
    
    # Estado
    is_active: Optional[bool] = None
    is_tax_withholding_agent: Optional[bool] = None
      # Metadata
    notes: Optional[str] = Field(None, max_length=1000)
    internal_code: Optional[str] = Field(None, max_length=50)

    @field_validator('third_party_type', mode='before')
    @classmethod
    def validate_third_party_type(cls, v):
        """Valida el tipo de tercero de forma case-insensitive"""
        return create_enum_validator(ThirdPartyType)(v)

    @field_validator('document_type', mode='before')
    @classmethod
    def validate_document_type(cls, v):
        """Valida el tipo de documento de forma case-insensitive"""
        return create_enum_validator(DocumentType)(v)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Valida y limpia el nombre si está presente"""
        if v is not None:
            if not v.strip():
                raise ValueError("El nombre no puede estar vacío")
            return v.strip()
        return v

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Valida el formato del email si está presente"""
        if v and v.strip():
            if '@' not in v:
                raise ValueError("El formato del email es inválido")
            return v.strip().lower()
        return v


class ThirdPartyRead(ThirdPartyBase):
    """Schema para leer terceros"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Información de las cuentas contables (nombres para mostrar)
    receivable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta por cobrar")
    receivable_account_code: Optional[str] = Field(None, description="Código de la cuenta por cobrar")
    payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta por pagar")
    payable_account_code: Optional[str] = Field(None, description="Código de la cuenta por pagar")
    
    # Propiedades calculadas
    display_name: Optional[str] = None
    full_address: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ThirdPartySummary(BaseModel):
    """Schema resumido para listados"""
    id: uuid.UUID
    code: str
    name: str
    commercial_name: Optional[str] = None
    third_party_type: ThirdPartyType
    document_number: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    status: Optional[str] = None  # "active" or "inactive"
    
    model_config = ConfigDict(from_attributes=True)
    
    def model_post_init(self, __context):
        """Set computed status field after initialization"""
        if hasattr(self, 'is_active'):
            self.status = "active" if self.is_active else "inactive"


class ThirdPartyList(BaseModel):
    """Schema para listado paginado"""
    third_parties: List[ThirdPartySummary]
    total: int
    page: int
    size: int
    pages: int


# Schemas para filtros y búsquedas
class ThirdPartyFilter(BaseModel):
    """Schema para filtrar terceros"""
    search: Optional[str] = None  # Búsqueda en código, nombre, documento
    third_party_type: Optional[ThirdPartyType] = None
    document_type: Optional[DocumentType] = None
    is_active: Optional[bool] = None
    city: Optional[str] = None
    country: Optional[str] = None


# Schemas para reportes
class ThirdPartyMovement(BaseModel):
    """Schema para movimientos por tercero"""
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    entry_date: datetime
    account_code: str
    account_name: str
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    balance: Decimal
    reference: Optional[str] = None


class ThirdPartyStatement(BaseModel):
    """Schema para estado de cuenta de terceros"""
    third_party: ThirdPartyRead
    period_start: datetime
    period_end: datetime
    opening_balance: Decimal
    movements: List[ThirdPartyMovement]
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    movement_count: int


class ThirdPartyBalance(BaseModel):
    """Schema para saldos de terceros"""
    third_party_id: uuid.UUID
    third_party_code: str
    third_party_name: str
    third_party_type: ThirdPartyType
    current_balance: Decimal
    overdue_balance: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    available_credit: Optional[Decimal] = None


class ThirdPartyAging(BaseModel):
    """Schema para análisis de antigüedad"""
    third_party: ThirdPartySummary
    current: Decimal  # 0-30 días
    days_31_60: Decimal
    days_61_90: Decimal
    days_91_120: Decimal
    over_120_days: Decimal
    total_balance: Decimal


# Schemas para importación/exportación
class ThirdPartyImport(BaseModel):
    """Schema para importar terceros"""
    code: str
    name: str
    commercial_name: Optional[str] = None
    third_party_type: str  # String para permitir validación más flexible
    document_type: str
    document_number: str
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None


class ThirdPartyExport(BaseModel):
    """Schema para exportar terceros"""
    code: str
    name: str
    commercial_name: Optional[str] = None
    third_party_type: str
    document_type: str
    document_number: str
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    is_active: bool
    created_at: datetime


# Schemas para validaciones
class ThirdPartyValidation(BaseModel):
    """Schema para validación de terceros"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    code_unique: bool
    document_unique: bool


# Schemas para operaciones masivas
class BulkThirdPartyOperation(BaseModel):
    """Schema para operaciones masivas"""
    third_party_ids: List[uuid.UUID]
    operation: str  # 'activate', 'deactivate', 'delete', 'update_type'
    new_type: Optional[ThirdPartyType] = None
    reason: Optional[str] = None


class ThirdPartyStats(BaseModel):
    """Schema para estadísticas de terceros"""
    total_third_parties: int
    active_third_parties: int
    inactive_third_parties: int
    customers: int
    suppliers: int
    employees: int
    others: int
    with_email: int
    with_phone: int
    by_country: dict[str, int]


# API Response schemas
class ThirdPartyResponse(ThirdPartyRead):
    """Standard API response for third parties"""
    pass


class ThirdPartyDetailResponse(ThirdPartyRead):
    """Detailed API response"""
    recent_movements: Optional[List[ThirdPartyMovement]] = None
    current_balance: Optional[Decimal] = None


class ThirdPartyListResponse(BaseModel):
    """Paginated list response"""
    items: List[ThirdPartySummary]
    total: int
    skip: int
    limit: int


# Bulk operations schemas
class BulkThirdPartyDelete(BaseModel):
    """Schema específico para borrado múltiple de terceros"""
    third_party_ids: List[uuid.UUID] = Field(min_length=1, max_length=100, description="Lista de IDs de terceros a eliminar")
    force_delete: bool = Field(default=False, description="Forzar eliminación aunque tengan restricciones")
    delete_reason: Optional[str] = Field(default=None, max_length=500, description="Razón para la eliminación")
    
    @field_validator('third_party_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        """Validar que no haya IDs duplicados"""
        if len(v) != len(set(v)):
            raise ValueError("No se permiten IDs de terceros duplicados")
        return v


class BulkThirdPartyDeleteResult(BaseModel):
    """Schema para el resultado del borrado múltiple"""
    total_requested: int = Field(description="Total de terceros solicitados para eliminar")
    successfully_deleted: List[uuid.UUID] = Field(default_factory=list, description="Terceros eliminados exitosamente")
    failed_to_delete: List[dict] = Field(default_factory=list, description="Terceros que no pudieron eliminarse")
    validation_errors: List[dict] = Field(default_factory=list, description="Errores de validación")
    warnings: List[str] = Field(default_factory=list, description="Advertencias del proceso")
    
    @property
    def success_count(self) -> int:
        return len(self.successfully_deleted)
    
    @property
    def failure_count(self) -> int:
        return len(self.failed_to_delete)
    
    @property
    def success_rate(self) -> float:
        if self.total_requested == 0:
            return 0.0
        return (self.success_count / self.total_requested) * 100


class ThirdPartyDeleteValidation(BaseModel):
    """Schema para validación previa al borrado"""
    third_party_id: uuid.UUID
    can_delete: bool
    blocking_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    dependencies: dict = Field(default_factory=dict)  # Información sobre dependencias
