"""
Invoice models for managing customer and supplier invoices.
Implements invoice header-detail pattern with integration to journal entries.
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
    from app.models.payment_terms import PaymentTerms
    from app.models.product import Product
    from app.models.account import Account
    from app.models.journal_entry import JournalEntry
    from app.models.payment import PaymentInvoice
    from app.models.cost_center import CostCenter
    from app.models.bank_reconciliation import BankReconciliation


class InvoiceType(str, Enum):
    """Tipos de factura"""
    CUSTOMER_INVOICE = "customer_invoice"  # Factura de cliente (ventas)
    SUPPLIER_INVOICE = "supplier_invoice"  # Factura de proveedor (compras)
    CREDIT_NOTE = "credit_note"  # Nota de crédito
    DEBIT_NOTE = "debit_note"    # Nota de débito


class InvoiceStatus(str, Enum):
    """Estados de la factura"""
    DRAFT = "draft"              # Borrador
    PENDING = "pending"          # Pendiente de aprobación
    APPROVED = "approved"        # Aprobada
    POSTED = "posted"           # Contabilizada
    PAID = "paid"               # Pagada
    PARTIALLY_PAID = "partially_paid"  # Parcialmente pagada
    OVERDUE = "overdue"         # Vencida
    CANCELLED = "cancelled"     # Anulada


class Invoice(Base):
    """
    Modelo de facturas (encabezado)
    Maneja tanto facturas de cliente como de proveedor
    """
    __tablename__ = "invoices"

    # Información básica
    number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    internal_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, 
    comment="Referencia externa (número de factura del proveedor)")
    
    # Tipo y estado
    invoice_type: Mapped[InvoiceType] = mapped_column(SQLEnum(InvoiceType), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    
    # Tercero (cliente o proveedor)
    third_party_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("third_parties.id"), nullable=False, index=True)
    
    # Fechas
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Términos de pago
    payment_terms_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("payment_terms.id"), nullable=True)
    
    # Montos
    subtotal: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Control de pagos
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Moneda
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=4), default=1, nullable=False)
    
    # Información adicional
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Centro de costo
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cost_centers.id"), nullable=True)
    
    # Asiento contable relacionado
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    posted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    cancelled_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Fechas de auditoría
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    third_party: Mapped["ThirdParty"] = relationship("ThirdParty", back_populates="invoices")
    payment_terms: Mapped[Optional["PaymentTerms"]] = relationship("PaymentTerms")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry")
    
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan"    )
    
    payment_invoices: Mapped[List["PaymentInvoice"]] = relationship(
        "PaymentInvoice",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    bank_reconciliations: Mapped[List["BankReconciliation"]] = relationship(
        "BankReconciliation",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

    # Propiedades calculadas
    @hybrid_property
    def is_customer_invoice(self) -> bool:
        """Indica si es factura de cliente"""
        return self.invoice_type in [InvoiceType.CUSTOMER_INVOICE]
    
    @hybrid_property
    def is_supplier_invoice(self) -> bool:
        """Indica si es factura de proveedor"""
        return self.invoice_type in [InvoiceType.SUPPLIER_INVOICE]
    
    @hybrid_property
    def is_paid(self) -> bool:
        """Indica si la factura está completamente pagada"""
        return self.outstanding_amount <= 0
    
    @hybrid_property
    def is_overdue(self) -> bool:
        """Indica si la factura está vencida"""
        from datetime import date
        return self.due_date < date.today() and self.outstanding_amount > 0

    def __repr__(self) -> str:
        return f"<Invoice(number='{self.number}', type='{self.invoice_type}', total={self.total_amount})>"


class InvoiceLine(Base):
    """
    Modelo de líneas de factura (detalle)
    Detalla los productos/servicios facturados
    """
    __tablename__ = "invoice_lines"

    # Relación con factura
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    
    # Línea
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Producto/Servicio
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Cantidad y precios
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), nullable=False)
    discount_percentage: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Impuestos
    tax_percentage: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Totales
    subtotal: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    
    # Cuenta contable
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    
    # Centro de costo específico de la línea
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cost_centers.id"), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship("Product")
    account: Mapped[Optional["Account"]] = relationship("Account")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")

    def __repr__(self) -> str:
        return f"<InvoiceLine(invoice_id='{self.invoice_id}', line={self.line_number}, total={self.total_amount})>"
