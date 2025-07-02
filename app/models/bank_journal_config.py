"""
Extensiones para diarios bancarios
Agrega funcionalidades específicas para manejo de operaciones bancarias
"""
import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.journal import Journal
    from app.models.account import Account


class PaymentDirection(str, Enum):
    """Dirección del pago"""
    INBOUND = "inbound"   # Pagos entrantes (cobros)
    OUTBOUND = "outbound" # Pagos salientes (pagos)


class PaymentMode(str, Enum):
    """Modo de procesamiento del pago"""
    MANUAL = "manual"     # Procesamiento manual individual
    BATCH = "batch"       # Procesamiento por lotes


class BankJournalConfig(Base):
    """
    Configuración específica para diarios bancarios
    Extiende la funcionalidad básica de Journal para operaciones bancarias
    """
    __tablename__ = "bank_journal_configs"

    # Relación uno a uno con Journal
    journal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("journals.id", ondelete="CASCADE"),
        primary_key=True,
        comment="ID del diario bancario"
    )

    # Configuración bancaria básica
    bank_account_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Número de cuenta bancaria asociada"
    )

    # Cuentas contables asociadas
    bank_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta bancaria principal (activo)"
    )

    transit_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta transitoria para operaciones en proceso"
    )

    profit_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta de ganancias (intereses, diferencias positivas)"
    )

    loss_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta de pérdidas (comisiones, diferencias negativas)"
    )

    # Configuración de secuencias
    dedicated_payment_sequence: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Si usar secuencia dedicada para pagos (separada de transacciones)"
    )

    # Configuración de pagos entrantes
    allow_inbound_payments: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Si permite pagos entrantes (cobros)"
    )

    inbound_payment_mode: Mapped[PaymentMode] = mapped_column(
        SQLEnum(PaymentMode),
        default=PaymentMode.MANUAL,
        nullable=False,
        comment="Modo de procesamiento de pagos entrantes"
    )

    inbound_receipt_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta de recibo para pagos entrantes"
    )

    # Configuración de pagos salientes
    allow_outbound_payments: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Si permite pagos salientes"
    )

    outbound_payment_mode: Mapped[PaymentMode] = mapped_column(
        SQLEnum(PaymentMode),
        default=PaymentMode.MANUAL,
        nullable=False,
        comment="Modo de procesamiento de pagos salientes"
    )

    outbound_payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Método de pago por defecto para salientes"
    )

    outbound_payment_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Nombre descriptivo para pagos salientes"
    )

    outbound_pending_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=True,
        comment="Cuenta de pagos pendientes para salientes"
    )

    # Configuración adicional
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default="COP",
        nullable=False,
        comment="Moneda principal del diario bancario"
    )

    allow_currency_exchange: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Si permite operaciones con múltiples monedas"
    )

    auto_reconcile: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Si intenta conciliación automática"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descripción de la configuración bancaria"
    )

    # Relationships
    journal: Mapped["Journal"] = relationship(
        "Journal",
        back_populates="bank_config"
    )

    bank_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[bank_account_id]
    )

    transit_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[transit_account_id]
    )

    profit_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[profit_account_id]
    )

    loss_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[loss_account_id]
    )

    inbound_receipt_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[inbound_receipt_account_id]
    )

    outbound_pending_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[outbound_pending_account_id]
    )

    def __repr__(self) -> str:
        return f"<BankJournalConfig(journal_id='{self.journal_id}', bank_account='{self.bank_account_number}')>"

    def get_account_for_operation(self, operation_type: str, direction: PaymentDirection) -> Optional["Account"]:
        """
        Obtiene la cuenta apropiada según el tipo de operación y dirección
        
        Args:
            operation_type: 'main', 'transit', 'profit', 'loss', 'receipt', 'pending'
            direction: PaymentDirection.INBOUND o PaymentDirection.OUTBOUND
            
        Returns:
            Account correspondiente o None
        """
        if operation_type == "main":
            return self.bank_account
        elif operation_type == "transit":
            return self.transit_account
        elif operation_type == "profit":
            return self.profit_account
        elif operation_type == "loss":
            return self.loss_account
        elif operation_type == "receipt" and direction == PaymentDirection.INBOUND:
            return self.inbound_receipt_account
        elif operation_type == "pending" and direction == PaymentDirection.OUTBOUND:
            return self.outbound_pending_account
        
        return None

    def validate_configuration(self) -> list[str]:
        """
        Valida la configuración bancaria y retorna lista de errores
        
        Returns:
            Lista de mensajes de error (vacía si es válida)
        """
        errors = []

        # Validar que tenga al menos cuenta bancaria principal
        if not self.bank_account_id:
            errors.append("La cuenta bancaria principal es obligatoria")

        # Validar configuración de pagos entrantes
        if self.allow_inbound_payments and not self.inbound_receipt_account_id:
            errors.append("La cuenta de recibo es obligatoria para pagos entrantes")

        # Validar configuración de pagos salientes  
        if self.allow_outbound_payments and not self.outbound_pending_account_id:
            errors.append("La cuenta de pagos pendientes es obligatoria para pagos salientes")

        # Validar moneda
        if len(self.currency_code) != 3:
            errors.append("El código de moneda debe tener 3 caracteres")

        return errors

    def is_valid_for_payments(self) -> bool:
        """
        Verifica si la configuración es válida para procesamiento de pagos
        
        Returns:
            True si está configurada correctamente
        """
        return len(self.validate_configuration()) == 0
