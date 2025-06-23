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
    from app.models.journal import Journal
    from app.models.payment import PaymentInvoice
    from app.models.cost_center import CostCenter
    from app.models.bank_reconciliation import BankReconciliation


class InvoiceType(str, Enum):
    """Tipos de factura siguiendo patrón Odoo"""
    CUSTOMER_INVOICE = "CUSTOMER_INVOICE"     # Factura de venta (customer_invoice)
    SUPPLIER_INVOICE = "SUPPLIER_INVOICE"     # Factura de compra (supplier_invoice)
    CREDIT_NOTE = "CREDIT_NOTE"               # Nota de crédito
    DEBIT_NOTE = "DEBIT_NOTE"                 # Nota de débito


class InvoiceStatus(str, Enum):
    """Estados de la factura siguiendo patrón de la base de datos"""
    DRAFT = "DRAFT"                 # Borrador - completamente editable
    PENDING = "PENDING"             # Pendiente
    APPROVED = "APPROVED"           # Aprobada
    POSTED = "POSTED"               # Contabilizada - genera JournalEntry(POSTED), no editable
    PAID = "PAID"                   # Pagada completamente
    PARTIALLY_PAID = "PARTIALLY_PAID"  # Pagada parcialmente
    OVERDUE = "OVERDUE"             # Vencida
    CANCELLED = "CANCELLED"         # Cancelada - reversión del asiento, estado final


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
    
    # Override de cuentas contables (opcionales)
    third_party_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True,
                                                                        comment="Override cuenta cliente/proveedor")
    
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
      # Diario contable para facturación y asiento contable relacionado
    journal_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("journals.id"), nullable=True,
                                                            comment="Diario contable para la numeración de factura")
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
      # Auditoría siguiendo patrón Odoo
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True,
                                                              comment="Quien modificó por última vez")
    posted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True,
                                                             comment="Quien contabilizó la factura")
    cancelled_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True,
                                                                comment="Quien canceló la factura")
    
    # Fechas de auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                         comment="Fecha de contabilización")
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                            comment="Fecha de cancelación")    # Relationships
    third_party: Mapped["ThirdParty"] = relationship("ThirdParty", back_populates="invoices")
    third_party_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[third_party_account_id])
    payment_terms: Mapped[Optional["PaymentTerms"]] = relationship("PaymentTerms")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")
    journal: Mapped[Optional["Journal"]] = relationship("Journal")
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
        cascade="all, delete-orphan"    )
    
    # Propiedades calculadas
    @hybrid_property
    def is_customer_invoice(self) -> bool:
        """Indica si es factura de cliente"""
        return self.invoice_type == InvoiceType.CUSTOMER_INVOICE
    
    @hybrid_property
    def is_supplier_invoice(self) -> bool:
        """Indica si es factura de proveedor"""
        return self.invoice_type == InvoiceType.SUPPLIER_INVOICE
    
    @hybrid_property
    def is_paid(self) -> bool:
        """Indica si la factura está completamente pagada"""
        return self.outstanding_amount <= 0
    
    @hybrid_property
    def is_overdue(self) -> bool:
        """Indica si la factura está vencida"""
        from datetime import date
        return self.due_date < date.today() and self.outstanding_amount > 0
    
    @hybrid_property
    def invoice_number(self) -> str:
        """Alias para el campo number (compatibilidad con schemas)"""
        return self.number
    
    @hybrid_property
    def days_overdue(self) -> int:
        """Calcula los días de vencimiento"""
        from datetime import date
        if self.due_date < date.today() and self.outstanding_amount > 0:
            return (date.today() - self.due_date).days
        return 0

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
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, comment="Orden de las líneas")
    
    # Producto/Servicio
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="Descripción de la línea")
    
    # Cantidad y precios
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), nullable=False)
    discount_percentage: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), default=0, nullable=False)
    
    # Override de cuentas contables (opcionales)
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True,
                                                           comment="Override cuenta ingreso/gasto")
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cost_centers.id"), nullable=True)
      # Montos calculados
    subtotal: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False,
                                             comment="quantity * unit_price")
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False,
                                                 comment="subtotal - discount + tax")
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Fechas de auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship("Product")
    account: Mapped[Optional["Account"]] = relationship("Account")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")

    def __repr__(self) -> str:
        return f"<InvoiceLine(invoice_id='{self.invoice_id}', sequence={self.sequence}, total={self.total_amount})>"
