import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional, List

from sqlalchemy import Boolean, String, Text, ForeignKey, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.base import Base
from app.models.user import User


class AccountType(str, Enum):
    """Tipos de cuentas contables según la naturaleza contable"""
    ACTIVO = "activo"
    PASIVO = "pasivo"
    PATRIMONIO = "patrimonio"
    INGRESO = "ingreso"
    GASTO = "gasto"
    COSTOS = "costos"


class AccountCategory(str, Enum):
    """Categorías principales para clasificación de cuentas"""
    # Activos
    ACTIVO_CORRIENTE = "activo_corriente"
    ACTIVO_NO_CORRIENTE = "activo_no_corriente"
    
    # Pasivos
    PASIVO_CORRIENTE = "pasivo_corriente"
    PASIVO_NO_CORRIENTE = "pasivo_no_corriente"
    
    # Patrimonio
    CAPITAL = "capital"
    RESERVAS = "reservas"
    RESULTADOS = "resultados"
    
    # Ingresos
    INGRESOS_OPERACIONALES = "ingresos_operacionales"
    INGRESOS_NO_OPERACIONALES = "ingresos_no_operacionales"
    
    # Gastos
    GASTOS_OPERACIONALES = "gastos_operacionales"
    GASTOS_NO_OPERACIONALES = "gastos_no_operacionales"
    
    # Costos
    COSTO_VENTAS = "costo_ventas"
    COSTOS_PRODUCCION = "costos_produccion"


class Account(Base):
    """
    Modelo de cuentas contables con estructura jerárquica
    """
    __tablename__ = "accounts"

    # Información básica de la cuenta
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Clasificación contable
    account_type: Mapped[AccountType] = mapped_column(nullable=False)
    category: Mapped[Optional[AccountCategory]] = mapped_column(nullable=True)
    
    # Jerarquía de cuentas
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Nivel en la jerarquía
    
    # Control de cuenta
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allows_movements: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Solo cuentas hoja
    
    # Configuración de la cuenta
    requires_third_party: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Requiere terceros
    requires_cost_center: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Requiere centro de costo
    
    # Saldos (se calculan dinámicamente pero se pueden cachear)
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    debit_balance: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    credit_balance: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
      # Metadatos
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Auditoría
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )
    
    # Relationships    
    parent: Mapped[Optional["Account"]] = relationship(
        "Account", 
        remote_side="Account.id",
        back_populates="children"
    )    
    children: Mapped[List["Account"]] = relationship(
        "Account",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    # Relación con el usuario que creó la cuenta
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
      # Relación con movimientos contables (forward reference)
    # journal_entry_lines: Mapped[List["JournalEntryLine"]] = relationship(
    #     "JournalEntryLine", 
    #     back_populates="account"
    # )

    def __repr__(self) -> str:
        return f"<Account(code='{self.code}', name='{self.name}', type='{self.account_type}')>"

    @hybrid_property
    def full_code(self) -> str:
        """Retorna el código completo incluyendo jerarquía"""
        if self.parent:
            return f"{self.parent.full_code}.{self.code}"
        return self.code

    @hybrid_property
    def full_name(self) -> str:
        """Retorna el nombre completo incluyendo jerarquía"""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name

    @property
    def is_parent_account(self) -> bool:
        """Verifica si es una cuenta padre (tiene hijos)"""
        # Verificar si children está cargado para evitar lazy loading en contexto async
        if 'children' in self.__dict__:
            return len(self.children) > 0
        else:
            # Si no está cargado, usar allows_movements como indicador
            # Las cuentas padre normalmente no permiten movimientos
            return not self.allows_movements

    @property
    def is_leaf_account(self) -> bool:
        """Verifica si es una cuenta hoja (no tiene hijos)"""
        # Verificar si children está cargado para evitar lazy loading en contexto async
        if 'children' in self.__dict__:
            return len(self.children) == 0
        else:
            # Si no está cargado, usar allows_movements como indicador
            # Las cuentas hoja normalmente permiten movimientos
            return self.allows_movements

    @property
    def can_receive_movements(self) -> bool:
        """Verifica si la cuenta puede recibir movimientos contables"""
        # Verificaciones básicas que no requieren lazy loading
        if not (self.is_active and self.allows_movements):
            return False
        
        # Para la verificación de cuenta hoja, usar una lógica segura
        # Si children está cargado, usar esa información
        if 'children' in self.__dict__:
            return len(self.children) == 0
        else:
            # Si no está cargado, confiar en allows_movements
            # Una cuenta que allows_movements=True debería ser hoja
            return True

    @property
    def normal_balance_side(self) -> str:
        """Retorna el lado normal del balance para esta cuenta"""
        if self.account_type in [AccountType.ACTIVO, AccountType.GASTO, AccountType.COSTOS]:
            return "debit"
        else:  # PASIVO, PATRIMONIO, INGRESO
            return "credit"

    @property
    def increases_with(self) -> str:
        """Retorna con qué lado aumenta el saldo de la cuenta"""
        return self.normal_balance_side    
    @property
    def decreases_with(self) -> str:
        """Retorna con qué lado disminuye el saldo de la cuenta"""
        return "credit" if self.normal_balance_side == "debit" else "debit"

    def get_balance_display(self) -> Decimal:
        """
        Retorna el balance con el signo correcto según la naturaleza de la cuenta
        """
        if self.normal_balance_side == "debit":
            return self.debit_balance - self.credit_balance
        else:
            return self.credit_balance - self.debit_balance

    def update_balance(self, debit_amount: Decimal = Decimal('0'), credit_amount: Decimal = Decimal('0')) -> None:
        """
        Actualiza los saldos de la cuenta
        """
        self.debit_balance += Decimal(str(debit_amount))
        self.credit_balance += Decimal(str(credit_amount))
        self.balance = self.get_balance_display()

    def validate_movement_allowed(self) -> bool:
        """
        Valida si se pueden crear movimientos en esta cuenta
        """
        if not self.is_active:
            raise ValueError(f"La cuenta {self.code} - {self.name} está inactiva")
        
        if not self.allows_movements:
            raise ValueError(f"La cuenta {self.code} - {self.name} no permite movimientos")
        
        if not self.is_leaf_account:
            raise ValueError(f"La cuenta {self.code} - {self.name} es una cuenta padre y no puede recibir movimientos")
        
        return True

    def get_children_recursive(self) -> List["Account"]:
        """
        Obtiene todos los hijos de forma recursiva
        """
        all_children = []
        for child in self.children:
            all_children.append(child)
            all_children.extend(child.get_children_recursive())
        return all_children

    def calculate_total_balance(self) -> Decimal:
        """
        Calcula el balance total incluyendo todas las cuentas hijas
        """
        total = Decimal(str(self.balance))
        for child in self.children:
            total += child.calculate_total_balance()
        return total
