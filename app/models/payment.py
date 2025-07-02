"""
Payment models for managing customer payments and supplier payments.
Implements payment-invoice relationship with automatic journal entry generation.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Boolean, ForeignKey, Numeric, DateTime, Date, 
    Enum as SQLEnum, Integer
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.third_party import ThirdParty
    from app.models.account import Account
    from app.models.journal_entry import JournalEntry
    from app.models.journal import Journal
    from app.models.invoice import Invoice
    from app.models.bank_reconciliation import BankReconciliation
    from app.models.bank_extract import BankExtractLine


class PaymentType(str, Enum):
    """Tipos de pago"""
    CUSTOMER_PAYMENT = "customer_payment"  # Pago de cliente (cobro)
    SUPPLIER_PAYMENT = "supplier_payment"  # Pago a proveedor
    INTERNAL_TRANSFER = "internal_transfer"  # Transferencia interna
    ADVANCE_PAYMENT = "advance_payment"   # Anticipo
    REFUND = "refund"                    # Devolución


class PaymentMethod(str, Enum):
    """Métodos de pago"""
    CASH = "cash"                # Efectivo
    CHECK = "check"              # Cheque
    BANK_TRANSFER = "bank_transfer"  # Transferencia bancaria
    CREDIT_CARD = "credit_card"  # Tarjeta de crédito
    DEBIT_CARD = "debit_card"    # Tarjeta de débito
    ELECTRONIC = "electronic"    # Pago electrónico
    OTHER = "other"              # Otro


class PaymentStatus(str, Enum):
    """Estados del pago"""
    DRAFT = "draft"              # Borrador
    PENDING = "pending"          # Pendiente
    CONFIRMED = "confirmed"      # Confirmado
    POSTED = "posted"           # Contabilizado
    RECONCILED = "reconciled"    # Conciliado
    CANCELLED = "cancelled"      # Anulado


class Payment(Base):
    """
    Modelo de pagos
    Maneja tanto pagos de clientes como pagos a proveedores
    """
    __tablename__ = "payments"

    # Información básica
    number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True,
                                                              comment="Referencia externa (número de cheque, transacción, etc.)")
    
    # Tipo y método
    payment_type: Mapped[PaymentType] = mapped_column(SQLEnum(PaymentType), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(SQLEnum(PaymentMethod), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), default=PaymentStatus.DRAFT, nullable=False)
    
    # Tercero (cliente o proveedor) - opcional
    third_party_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("third_parties.id"), nullable=True, index=True)
    
    # Fechas
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, 
                                                      comment="Fecha valor (fecha efectiva del pago)")
    
    # Montos
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False,
                                                     comment="Monto asignado a facturas")
    unallocated_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False,
                                                       comment="Monto no asignado")
    
    # Moneda
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=4), default=1, nullable=False)
    
    # Cuenta bancaria/caja
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False,
                                                 comment="Cuenta de efectivo/banco donde se recibió/hizo el pago")
    
    # Información del método de pago
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    check_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Información adicional
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Asiento contable relacionado
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
    
    # Journal donde se registra el pago
    journal_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("journals.id"), nullable=True,
                                                           comment="Journal contable donde se registra el pago")
    
    # Control de conciliación
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    confirmed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    posted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    cancelled_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Fechas de auditoría
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    third_party: Mapped["ThirdParty"] = relationship("ThirdParty", back_populates="payments")
    account: Mapped["Account"] = relationship("Account")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry")
    journal: Mapped[Optional["Journal"]] = relationship("Journal")
    
    payment_invoices: Mapped[List["PaymentInvoice"]] = relationship(
        "PaymentInvoice",
        back_populates="payment",
        cascade="all, delete-orphan"
    )
    
    bank_reconciliations: Mapped[List["BankReconciliation"]] = relationship(
        "BankReconciliation",
        back_populates="payment"
    )
    
    # Líneas de extracto bancario relacionadas (para auto-matching)
    bank_extract_lines: Mapped[List["BankExtractLine"]] = relationship(
        "BankExtractLine",
        back_populates="payment"
    )

    # Propiedades calculadas
    @hybrid_property
    def is_customer_payment(self) -> bool:
        """Indica si es pago de cliente"""
        return self.payment_type in [PaymentType.CUSTOMER_PAYMENT]
    @hybrid_property
    def is_supplier_payment(self) -> bool:
        """Indica si es pago a proveedor"""
        return self.payment_type in [PaymentType.SUPPLIER_PAYMENT]
    
    @hybrid_property
    def is_fully_allocated(self) -> bool:
        """Indica si el pago está completamente asignado"""
        return self.unallocated_amount <= 0

    def update_allocation_amounts(self):
        """Actualiza los montos de asignación basado en las facturas relacionadas"""
        from decimal import Decimal
        total_allocated = Decimal(str(sum(pi.amount for pi in self.payment_invoices)))
        self.allocated_amount = total_allocated
        self.unallocated_amount = self.amount - total_allocated

    def __repr__(self) -> str:
        return f"<Payment(number='{self.number}', type='{self.payment_type}', amount={self.amount})>"


class PaymentInvoice(Base):
    """
    Modelo de relación pago-factura
    Permite asignar un pago a múltiples facturas con montos específicos
    """
    __tablename__ = "payment_invoices"

    # Relaciones
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    
    # Monto asignado de este pago a esta factura
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    
    # Fecha de aplicación
    allocation_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Información adicional
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    payment: Mapped["Payment"] = relationship("Payment", back_populates="payment_invoices")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payment_invoices")

    def __repr__(self) -> str:
        return f"<PaymentInvoice(payment_id='{self.payment_id}', invoice_id='{self.invoice_id}', amount={self.amount})>"
