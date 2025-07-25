import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, ForeignKey, Numeric, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.user import User
    from app.models.journal_entry import JournalEntry
    from app.models.bank_journal_config import BankJournalConfig


class JournalType(str, Enum):
    """Tipos de diario contable"""
    SALE = "sale"           # Diario de ventas - Para facturas de venta
    PURCHASE = "purchase"   # Diario de compras - Para facturas de proveedores
    CASH = "cash"          # Diario de efectivo - Para operaciones en efectivo
    BANK = "bank"          # Diario de banco - Para operaciones bancarias
    MISCELLANEOUS = "miscellaneous"  # Diario varios - Para asientos diversos


class Journal(Base):
    """
    Modelo para diarios contables
    Cada diario agrupa asientos contables de un tipo específico
    """
    __tablename__ = "journals"

    # Información básica del diario
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Nombre descriptivo del diario"
    )
    
    # Código único del diario (para mostrar en interfaces)
    code: Mapped[str] = mapped_column(
        String(10), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Código único del diario"
    )
    
    # Tipo de diario
    type: Mapped[JournalType] = mapped_column(
        nullable=False,
        index=True,
        comment="Tipo de diario (sale, purchase, cash, bank, miscellaneous)"
    )
    
    # Prefijo para la secuencia de numeración
    sequence_prefix: Mapped[str] = mapped_column(
        String(10), 
        unique=True, 
        nullable=False,
        comment="Prefijo único para la secuencia de numeración"
    )
    
    # Cuenta contable por defecto
    default_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta contable por defecto para asientos de este diario"
    )
    
    # === CONFIGURACIÓN DE CUENTAS ESPECÍFICAS PARA PAGOS ===
    # Cuentas específicas para diferentes tipos de operaciones
    default_debit_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta débito por defecto para asientos automáticos"
    )
    
    default_credit_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta crédito por defecto para asientos automáticos"
    )
    
    customer_receivable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta por cobrar clientes específica para este diario"
    )
    
    supplier_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta por pagar proveedores específica para este diario"
    )
    
    cash_difference_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta para diferencias de caja/efectivo"
    )
    
    bank_charges_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta para gastos y comisiones bancarias"
    )
    
    currency_exchange_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta para diferencias de cambio de moneda"
    )
    
    # Configuración de secuencia
    current_sequence_number: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Número actual de la secuencia"
    )
    
    sequence_padding: Mapped[int] = mapped_column(
        default=4,
        nullable=False,
        comment="Número de dígitos para rellenar con ceros (ej: 0001)"
    )
    
    # Si incluye año en la secuencia
    include_year_in_sequence: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Si incluir el año en la secuencia (ej: VEN/2025/0001)"
    )
    
    # Si resetear la secuencia cada año
    reset_sequence_yearly: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Si resetear la secuencia cada año"
    )
    
    # Control de acceso y validación
    requires_validation: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Si los asientos en este diario requieren validación"
    )
    
    allow_manual_entries: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Si permite asientos manuales en este diario"
    )
    
    # Estado del diario
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Si el diario está activo"
    )
    
    # Descripción opcional
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descripción del propósito del diario"
    )
    
    # Último año de reseteo de secuencia
    last_sequence_reset_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Último año en que se reseteó la secuencia"
    )
    
    # Metadatos de auditoría
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )

    # Relationships
    default_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[default_account_id],
        back_populates="journals_as_default"
    )
    
    # Relaciones con cuentas específicas para pagos
    default_debit_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[default_debit_account_id],
        back_populates="journals_as_default_debit"
    )
    
    default_credit_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[default_credit_account_id],
        back_populates="journals_as_default_credit"
    )
    
    customer_receivable_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[customer_receivable_account_id],
        back_populates="journals_as_customer_receivable"
    )
    
    supplier_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[supplier_payable_account_id],
        back_populates="journals_as_supplier_payable"
    )
    
    cash_difference_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[cash_difference_account_id],
        back_populates="journals_as_cash_difference"
    )
    
    bank_charges_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[bank_charges_account_id],
        back_populates="journals_as_bank_charges"
    )
    
    currency_exchange_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[currency_exchange_account_id],
        back_populates="journals_as_currency_exchange"
    )
    
    created_by: Mapped[Optional["User"]] = relationship(
        "User"
    )
    
    journal_entries: Mapped[List["JournalEntry"]] = relationship(
        "JournalEntry",
        back_populates="journal",
        cascade="all, delete-orphan"
    )

    # Configuración bancaria (solo para diarios tipo BANK)
    bank_config: Mapped[Optional["BankJournalConfig"]] = relationship(
        "BankJournalConfig",
        back_populates="journal",
        cascade="all, delete-orphan",
        uselist=False
    )

    # Restricciones de base de datos
    __table_args__ = (
        UniqueConstraint('sequence_prefix', name='uq_journal_sequence_prefix'),
        UniqueConstraint('code', name='uq_journal_code'),
    )

    def __repr__(self) -> str:
        return f"<Journal(code='{self.code}', name='{self.name}', type='{self.type}')>"

    def get_next_sequence_number(self, year: Optional[int] = None) -> str:
        """
        Genera el siguiente número de secuencia para este diario
        
        Args:
            year: Año para incluir en la secuencia. Si es None, usa el año actual
            
        Returns:
            Número de secuencia completo (ej: "VEN/2025/0001")
        """
        if year is None:
            year = datetime.now(timezone.utc).year
        
        # Verificar si necesita resetear la secuencia
        if (self.reset_sequence_yearly and 
            self.last_sequence_reset_year != year):
            self.current_sequence_number = 0
            self.last_sequence_reset_year = year
        
        # Incrementar número de secuencia
        self.current_sequence_number += 1
        
        # Formatear número con padding
        number_str = str(self.current_sequence_number).zfill(self.sequence_padding)
        
        # Construir secuencia completa
        if self.include_year_in_sequence:
            return f"{self.sequence_prefix}/{year}/{number_str}"
        else:
            return f"{self.sequence_prefix}/{number_str}"    # NOTA: Comentado temporalmente para evitar lazy loading en serialización
    # El conteo se maneja ahora directamente en los servicios y esquemas
    # @hybrid_property
    # def total_journal_entries(self) -> int:
    #     """Total de asientos contables en este diario"""
    #     return len(self.journal_entries)

    def can_create_entry(self, manual: bool = False) -> bool:
        """
        Verifica si se puede crear un asiento en este diario
        
        Args:
            manual: Si el asiento es manual
            
        Returns:
            True si se puede crear, False caso contrario
        """
        if not self.is_active:
            return False
            
        if manual and not self.allow_manual_entries:
            return False
            
        return True

    def get_suggested_accounts(self) -> List["Account"]:
        """
        Obtiene las cuentas sugeridas para este tipo de diario
        Basado en el tipo de diario y cuentas frecuentemente usadas
        """
        # Esta funcionalidad se puede expandir según las reglas de negocio
        suggested = []
        
        if self.default_account:
            suggested.append(self.default_account)
            
        return suggested

    def is_bank_journal(self) -> bool:
        """
        Verifica si este diario es de tipo bancario
        
        Returns:
            True si es diario bancario
        """
        return self.type == JournalType.BANK

    def get_bank_config(self) -> Optional["BankJournalConfig"]:
        """
        Obtiene la configuración bancaria si existe
        
        Returns:
            BankJournalConfig o None si no es diario bancario
        """
        return self.bank_config if self.is_bank_journal() else None

    def ensure_bank_config(self) -> "BankJournalConfig":
        """
        Asegura que exista configuración bancaria para diarios tipo BANK
        Crea la configuración si no existe
        
        Returns:
            BankJournalConfig existente o recién creada
            
        Raises:
            ValueError: Si no es diario bancario
        """
        if not self.is_bank_journal():
            raise ValueError("Solo los diarios tipo BANK pueden tener configuración bancaria")
        
        if not self.bank_config:
            from app.models.bank_journal_config import BankJournalConfig
            self.bank_config = BankJournalConfig(journal_id=self.id)
        
        return self.bank_config

    def validate_for_payments(self) -> list[str]:
        """
        Valida si el diario está configurado correctamente para pagos
        
        Returns:
            Lista de errores de validación (vacía si es válido)
        """
        errors = []

        if not self.is_active:
            errors.append("El diario debe estar activo")

        if self.is_bank_journal():
            bank_config = self.get_bank_config()
            if not bank_config:
                errors.append("Los diarios bancarios requieren configuración bancaria")
            else:
                errors.extend(bank_config.validate_configuration())

        return errors
