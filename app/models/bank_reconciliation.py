"""
Bank reconciliation models for linking bank extract lines with payments and invoices.
Implements the reconciliation process between bank statements and accounting records.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Boolean, ForeignKey, Numeric, DateTime, Date, 
    Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.bank_extract import BankExtractLine
    from app.models.payment import Payment
    from app.models.invoice import Invoice


class ReconciliationType(str, Enum):
    """Tipos de conciliación"""
    PAYMENT = "payment"          # Conciliación con pago
    INVOICE = "invoice"          # Conciliación directa con factura
    MANUAL = "manual"            # Conciliación manual
    AUTOMATIC = "automatic"      # Conciliación automática


class BankReconciliation(Base):
    """
    Modelo de conciliación bancaria
    Relaciona líneas de extracto con pagos y/o facturas
    """
    __tablename__ = "bank_reconciliations"

    # Línea de extracto bancario
    extract_line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bank_extract_lines.id"), 
                                                       nullable=False, index=True)
    
    # Pago relacionado (opcional)
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("payments.id"), 
                                                            nullable=True, index=True)
    
    # Factura relacionada (opcional, para conciliación directa)
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("invoices.id"), 
                                                           nullable=True, index=True)
    
    # Monto conciliado
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    
    # Tipo de conciliación
    reconciliation_type: Mapped[ReconciliationType] = mapped_column(SQLEnum(ReconciliationType), 
                                                                   nullable=False)
    
    # Fecha de conciliación
    reconciliation_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Información adicional
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Control de estado
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    confirmed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    extract_line: Mapped["BankExtractLine"] = relationship("BankExtractLine", 
                                                          back_populates="bank_reconciliations")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", 
                                                        back_populates="bank_reconciliations")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", 
                                                        back_populates="bank_reconciliations")

    def __repr__(self) -> str:
        return f"<BankReconciliation(extract_line_id='{self.extract_line_id}', amount={self.amount})>"
