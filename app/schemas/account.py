import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.account import AccountType, AccountCategory, CashFlowCategory


# Esquemas base
class AccountBase(BaseModel):
    """Schema base para cuentas contables"""
    code: str = Field(..., min_length=1, max_length=20, description="Código único de la cuenta")
    name: str = Field(..., min_length=2, max_length=200, description="Nombre de la cuenta")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción detallada")
    account_type: AccountType = Field(..., description="Tipo de cuenta contable")
    category: Optional[AccountCategory] = Field(None, description="Categoría de la cuenta")
    cash_flow_category: Optional[CashFlowCategory] = Field(None, description="Categoría de flujo de efectivo")
    is_active: bool = Field(True, description="Si la cuenta está activa")
    allows_movements: bool = Field(True, description="Si permite movimientos contables")
    requires_third_party: bool = Field(False, description="Si requiere especificar terceros")
    requires_cost_center: bool = Field(False, description="Si requiere centro de costo")
    allows_reconciliation: bool = Field(False, description="Si permite conciliación")
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
    parent_id: Optional[uuid.UUID] = Field(None, description="ID de la cuenta padre")


class AccountUpdate(BaseModel):
    """Schema para actualizar cuentas contables"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[AccountCategory] = None
    cash_flow_category: Optional[CashFlowCategory] = None
    is_active: Optional[bool] = None
    allows_movements: Optional[bool] = None
    requires_third_party: Optional[bool] = None
    requires_cost_center: Optional[bool] = None
    allows_reconciliation: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            return v.strip().title()
        return v


class AccountRead(BaseModel):
    """Schema para leer cuentas contables - coincide exactamente con el modelo de BD"""
    model_config = ConfigDict(from_attributes=True)
      # Campos exactos del modelo Account
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str]
    account_type: AccountType
    category: Optional[AccountCategory]
    cash_flow_category: Optional[CashFlowCategory]
    parent_id: Optional[uuid.UUID]
    level: int
    is_active: bool
    allows_movements: bool
    requires_third_party: bool
    requires_cost_center: bool
    allows_reconciliation: bool
    balance: Decimal
    debit_balance: Decimal
    credit_balance: Decimal
    notes: Optional[str]
    created_by_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class AccountReadWithCalculated(AccountRead):
    """Schema extendido con campos calculados - usar solo cuando sea necesario"""
    full_code: Optional[str] = None
    full_name: Optional[str] = None
    is_parent_account: Optional[bool] = None
    is_leaf_account: Optional[bool] = None
    can_receive_movements: Optional[bool] = None
    normal_balance_side: Optional[str] = None


class AccountTree(BaseModel):
    """Schema para representar la jerarquía de cuentas"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    code: str
    name: str
    account_type: AccountType
    level: int
    balance: Decimal
    is_active: bool
    allows_movements: bool
    allows_reconciliation: bool
    children: List['AccountTree'] = Field(default_factory=list)


class AccountSummary(BaseModel):
    """Schema resumido para listados"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    code: str
    name: str
    account_type: AccountType
    balance: Decimal
    is_active: bool
    allows_movements: bool
    allows_reconciliation: bool


class AccountListResponse(BaseModel):
    """Schema para respuesta de lista de cuentas"""
    accounts: List[AccountRead]
    total: int
    page: int
    size: int
    total_pages: int


class AccountBalance(BaseModel):
    """Schema para saldos de cuenta"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    debit_balance: Decimal
    credit_balance: Decimal
    net_balance: Decimal
    normal_balance_side: str
    as_of_date: date


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


class BulkAccountDelete(BaseModel):
    """Schema específico para borrado múltiple de cuentas"""
    account_ids: List[uuid.UUID] = Field(min_length=1, description="Lista de IDs de cuentas a eliminar")
    force_delete: bool = Field(default=False, description="Forzar eliminación (requiere confirmación)")
    delete_reason: Optional[str] = Field(default=None, max_length=500, description="Razón para la eliminación")
    
    @field_validator('account_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        """Validar que no haya IDs duplicados"""
        if len(v) != len(set(v)):
            raise ValueError("No se permiten IDs de cuentas duplicados")
        return v


class BulkAccountDeleteResult(BaseModel):
    """Schema para el resultado del borrado múltiple"""
    total_requested: int = Field(description="Total de cuentas solicitadas para eliminar")
    successfully_deleted: List[uuid.UUID] = Field(default_factory=list, description="Cuentas eliminadas exitosamente")
    failed_to_delete: List[dict] = Field(default_factory=list, description="Cuentas que no pudieron eliminarse")
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


class AccountDeleteValidation(BaseModel):
    """Schema para validación previa al borrado"""
    account_id: uuid.UUID
    can_delete: bool
    blocking_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    dependencies: dict = Field(default_factory=dict)  # Información sobre dependencias


class AccountStats(BaseModel):
    """Schema para estadísticas de cuentas"""
    total_accounts: int
    active_accounts: int
    inactive_accounts: int
    by_type: dict[str, int]
    by_category: dict[str, int]
    accounts_with_movements: int
    accounts_without_movements: int


# Reconstruir modelos que tienen referencias forward
AccountTree.model_rebuild()
