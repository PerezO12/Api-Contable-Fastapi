import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.account import AccountType, AccountCategory


# Esquemas base
class AccountBase(BaseModel):
    """Schema base para cuentas contables"""
    code: str = Field(..., min_length=1, max_length=20, description="Código único de la cuenta")
    name: str = Field(..., min_length=2, max_length=200, description="Nombre de la cuenta")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción detallada")
    account_type: AccountType = Field(..., description="Tipo de cuenta contable")
    category: Optional[AccountCategory] = Field(None, description="Categoría de la cuenta")
    parent_id: Optional[uuid.UUID] = Field(None, description="ID de la cuenta padre")
    is_active: bool = Field(True, description="Si la cuenta está activa")
    allows_movements: bool = Field(True, description="Si permite movimientos contables")
    requires_third_party: bool = Field(False, description="Si requiere especificar terceros")
    requires_cost_center: bool = Field(False, description="Si requiere centro de costo")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas adicionales")

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v):
        """Valida el formato del código de cuenta"""
        # Solo permitir letras, números, puntos y guiones
        if not v.replace('.', '').replace('-', '').replace('_', '').isalnum():
            raise ValueError("El código solo puede contener letras, números, puntos, guiones y guiones bajos")
        return v.upper()  # Convertir a mayúsculas

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Valida y limpia el nombre de la cuenta"""
        return v.strip().title()


class AccountCreate(AccountBase):
    """Schema para crear cuentas contables"""
    pass


class AccountUpdate(BaseModel):
    """Schema para actualizar cuentas contables"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[AccountCategory] = None
    is_active: Optional[bool] = None
    allows_movements: Optional[bool] = None
    requires_third_party: Optional[bool] = None
    requires_cost_center: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            return v.strip().title()
        return v


class AccountRead(AccountBase):
    """Schema para leer cuentas contables"""
    id: uuid.UUID
    level: int
    balance: Decimal
    debit_balance: Decimal
    credit_balance: Decimal
    created_at: datetime
    updated_at: datetime
    
    # Campos calculados
    full_code: Optional[str] = None
    full_name: Optional[str] = None
    is_parent_account: bool = False
    is_leaf_account: bool = True
    can_receive_movements: bool = True
    normal_balance_side: str = "debit"
    
    model_config = ConfigDict(from_attributes=True)


class AccountTree(BaseModel):
    """Schema para representar la jerarquía de cuentas"""
    id: uuid.UUID
    code: str
    name: str
    account_type: AccountType
    level: int
    balance: Decimal
    is_active: bool
    allows_movements: bool
    children: List['AccountTree'] = []
    
    model_config = ConfigDict(from_attributes=True)


class AccountSummary(BaseModel):
    """Schema resumido para listados"""
    id: uuid.UUID
    code: str
    name: str
    account_type: AccountType
    balance: Decimal
    is_active: bool
    can_receive_movements: bool
    
    model_config = ConfigDict(from_attributes=True)


class AccountBalance(BaseModel):
    """Schema para saldos de cuenta"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    debit_balance: Decimal
    credit_balance: Decimal
    net_balance: Decimal
    normal_balance_side: str


class AccountMovement(BaseModel):
    """Schema para movimientos de cuenta"""
    date: date
    journal_entry_number: str
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    balance: Decimal
    reference: Optional[str] = None


class AccountMovementHistory(BaseModel):
    """Schema para historial de movimientos"""
    account: AccountSummary
    movements: List[AccountMovement]
    period_start: date
    period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal


# Esquemas para importación/exportación
class AccountImport(BaseModel):
    """Schema para importar cuentas desde archivos"""
    code: str
    name: str
    account_type: str
    category: Optional[str] = None
    parent_code: Optional[str] = None
    description: Optional[str] = None


class AccountExport(BaseModel):
    """Schema para exportar cuentas"""
    code: str
    name: str
    full_name: str
    account_type: str
    category: Optional[str]
    parent_code: Optional[str]
    level: int
    balance: Decimal
    is_active: bool
    allows_movements: bool


# Esquemas para reportes
class AccountsByType(BaseModel):
    """Schema para cuentas agrupadas por tipo"""
    account_type: AccountType
    accounts: List[AccountSummary]
    total_balance: Decimal


class ChartOfAccounts(BaseModel):
    """Schema para plan de cuentas completo"""
    by_type: List[AccountsByType]
    total_accounts: int
    active_accounts: int
    leaf_accounts: int


# Esquemas para validaciones
class AccountValidation(BaseModel):
    """Schema para validación de cuentas"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class BulkAccountOperation(BaseModel):
    """Schema para operaciones masivas"""
    account_ids: List[uuid.UUID]
    operation: str  # "activate", "deactivate", "delete"
    reason: Optional[str] = None


class AccountStats(BaseModel):
    """Schema para estadísticas de cuentas"""
    total_accounts: int
    active_accounts: int
    inactive_accounts: int
    by_type: dict[str, int]
    by_category: dict[str, int]
    accounts_with_movements: int
    accounts_without_movements: int
