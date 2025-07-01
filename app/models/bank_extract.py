"""
Bank extract models for managing bank statements and reconciliation.
Implements bank statement import and reconciliation with payments and invoices.
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
    from app.models.account import Account
    from app.models.bank_reconciliation import BankReconciliation


class BankExtractStatus(str, Enum):
    """Estados del extracto bancario"""
    IMPORTED = "imported"        # Importado
    PROCESSING = "processing"    # En proceso de conciliación
    RECONCILED = "reconciled"    # Conciliado
    CLOSED = "closed"           # Cerrado


class BankExtract(Base):
    """
    Modelo de extractos bancarios
    Contiene la información del estado de cuenta bancario
    """
    __tablename__ = "bank_extracts"

    # Información básica
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Cuenta bancaria
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Período del extracto
    statement_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Saldos
    starting_balance: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    ending_balance: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Estado
    status: Mapped[BankExtractStatus] = mapped_column(SQLEnum(BankExtractStatus), 
                                                     default=BankExtractStatus.IMPORTED, nullable=False)
    
    # Información de archivo
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True,
                                                    comment="Hash MD5 del archivo para evitar duplicados")
    
    # Moneda
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Información adicional
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, 
                                                 default=datetime.utcnow)
    reconciled_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    account: Mapped["Account"] = relationship("Account")
    
    extract_lines: Mapped[List["BankExtractLine"]] = relationship(
        "BankExtractLine",
        back_populates="bank_extract",
        cascade="all, delete-orphan"
    )

    # Propiedades calculadas
    @hybrid_property
    def total_lines(self) -> int:
        """Total de líneas en el extracto"""
        return len(self.extract_lines)
    
    @hybrid_property
    def reconciled_lines(self) -> int:
        """Líneas conciliadas"""
        return sum(1 for line in self.extract_lines if line.is_reconciled)
    
    @hybrid_property
    def pending_lines(self) -> int:
        """Líneas pendientes de conciliación"""
        return self.total_lines - self.reconciled_lines
    
    @hybrid_property
    def is_fully_reconciled(self) -> bool:
        """Indica si está completamente conciliado"""
        return self.pending_lines == 0

    def calculate_totals(self):
        """Calcula totales del extracto"""
        total_debits = sum(line.debit_amount for line in self.extract_lines)
        total_credits = sum(line.credit_amount for line in self.extract_lines)
        calculated_balance = self.starting_balance + total_credits - total_debits
        
        return {
            "total_debits": total_debits,
            "total_credits": total_credits,
            "calculated_ending_balance": calculated_balance,
            "difference": self.ending_balance - calculated_balance
        }

    def __repr__(self) -> str:
        return f"<BankExtract(name='{self.name}', date='{self.statement_date}', balance={self.ending_balance})>"


class BankExtractLineType(str, Enum):
    """Tipos de línea de extracto"""
    DEBIT = "debit"              # Débito (salida de dinero)
    CREDIT = "credit"            # Crédito (entrada de dinero)
    TRANSFER = "transfer"        # Transferencia
    CHARGE = "charge"            # Cargo bancario
    INTEREST = "interest"        # Interés
    OTHER = "other"              # Otro


class BankExtractLine(Base):
    """
    Modelo de líneas de extracto bancario
    Detalle de movimientos en el extracto
    """
    __tablename__ = "bank_extract_lines"

    # Relación con extracto
    bank_extract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bank_extracts.id"), 
                                                       nullable=False, index=True)
    
    # Información de la transacción
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Referencias
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    check_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Descripción
    description: Mapped[str] = mapped_column(Text, nullable=False)
    additional_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tipo de movimiento
    line_type: Mapped[BankExtractLineType] = mapped_column(SQLEnum(BankExtractLineType), nullable=False)
    
    # Montos
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True)
    
    # Información del tercero (si está disponible en el extracto)
    partner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    partner_account: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Control de conciliación
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reconciled_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    pending_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Pago vinculado (para auto-matching)
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("payments.id"), nullable=True, index=True)
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    reconciled_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    bank_extract: Mapped["BankExtract"] = relationship("BankExtract", back_populates="extract_lines")
    
    # Pago vinculado
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="bank_extract_lines")
    
    bank_reconciliations: Mapped[List["BankReconciliation"]] = relationship(
        "BankReconciliation",
        back_populates="extract_line",
        cascade="all, delete-orphan"
    )
    
    # Propiedades calculadas
    @hybrid_property
    def amount(self) -> Decimal:
        """Monto de la línea (positivo para crédito, negativo para débito)"""
        return self.credit_amount - self.debit_amount
    
    @hybrid_property
    def is_debit(self) -> bool:
        """Indica si es un débito"""
        return self.debit_amount > 0
    
    @hybrid_property
    def is_credit(self) -> bool:
        """Indica si es un crédito"""
        return self.credit_amount > 0
    
    @hybrid_property
    def is_fully_reconciled(self) -> bool:
        """Indica si está completamente conciliado"""
        return self.pending_amount <= 0
    
    def calculate_pending_amount(self):
        """Calcula el monto pendiente de conciliación"""
        from decimal import Decimal
        line_amount = abs(self.amount)  # self.amount is a property that returns Decimal
        self.reconciled_amount = Decimal(str(sum(rec.amount for rec in self.bank_reconciliations)))
        self.pending_amount = line_amount - self.reconciled_amount
        self.is_reconciled = self.pending_amount <= 0

    def __repr__(self) -> str:
        return f"<BankExtractLine(date='{self.transaction_date}', amount={self.amount}, desc='{self.description[:50]}')>"
