import uuid
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from sqlalchemy import Boolean, String, Text, ForeignKey, Numeric, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.account import Account
from app.models.base import Base
from app.models.user import User


class JournalEntryStatus(str, Enum):
    """Estados del asiento contable"""
    DRAFT = "draft"  # Borrador
    PENDING = "pending"  # Pendiente de aprobación
    APPROVED = "approved"  # Aprobado
    POSTED = "posted"  # Contabilizado
    CANCELLED = "cancelled"  # Anulado


class JournalEntryType(str, Enum):
    """Tipos de asiento contable"""
    MANUAL = "manual"  # Asiento manual
    AUTOMATIC = "automatic"  # Asiento automático
    ADJUSTMENT = "adjustment"  # Asiento de ajuste
    OPENING = "opening"  # Asiento de apertura
    CLOSING = "closing"  # Asiento de cierre
    REVERSAL = "reversal"  # Asiento de reversión


class JournalEntry(Base):
    """
    Modelo de asientos contables (encabezado)
    Implementa el patrón Header-Detail para doble partida
    """
    __tablename__ = "journal_entries"    # Información básica del asiento
    number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tipo de asiento
    entry_type: Mapped[JournalEntryType] = mapped_column(default=JournalEntryType.MANUAL, nullable=False)
    
    # Fechas
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    posting_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Estado y control
    status: Mapped[JournalEntryStatus] = mapped_column(default=JournalEntryStatus.DRAFT, nullable=False)
    
    # Totales (para validación de cuadre)
    total_debit: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    total_credit: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
      # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    posted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    cancelled_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Fechas de auditoría
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadatos
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine",
        back_populates="journal_entry",
        cascade="all, delete-orphan"
    )
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])
    posted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[posted_by_id])
    cancelled_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[cancelled_by_id])

    def __repr__(self) -> str:
        return f"<JournalEntry(number='{self.number}', date='{self.entry_date}', status='{self.status}')>"

    @property
    def is_balanced(self) -> bool:
        """Verifica si el asiento está balanceado (suma débitos = suma créditos)"""
        return self.total_debit == self.total_credit

    @property
    def can_be_posted(self) -> bool:
        """Verifica si el asiento puede ser contabilizado"""
        return (
            self.status == JournalEntryStatus.APPROVED and
            self.is_balanced and
            len(self.lines) >= 2 and  # Mínimo 2 líneas para doble partida
            all(line.is_valid for line in self.lines)
        )    
    @property
    def can_be_modified(self) -> bool:
        """Verifica si el asiento puede ser modificado"""
        return self.status in [JournalEntryStatus.DRAFT, JournalEntryStatus.PENDING]

    def calculate_totals(self) -> None:
        """Calcula los totales de débito y crédito"""
        self.total_debit = Decimal(str(sum(line.debit_amount for line in self.lines)))
        self.total_credit = Decimal(str(sum(line.credit_amount for line in self.lines)))

    def validate_entry(self) -> List[str]:
        """
        Valida el asiento contable y retorna lista de errores
        """
        errors = []
        
        # Validar que tenga al menos 2 líneas
        if len(self.lines) < 2:
            errors.append("El asiento debe tener al menos 2 líneas")
        
        # Validar balance
        if not self.is_balanced:
            errors.append(f"El asiento no está balanceado. Débitos: {self.total_debit}, Créditos: {self.total_credit}")
        
        # Validar líneas individuales
        for i, line in enumerate(self.lines, 1):
            line_errors = line.validate_line()
            for error in line_errors:
                errors.append(f"Línea {i}: {error}")
          # Validar que no todas las líneas sean cero
        total_amount = Decimal(str(sum(line.debit_amount + line.credit_amount for line in self.lines)))
        if total_amount == 0:
            errors.append("El asiento no puede tener todas las líneas en cero")
        
        return errors

    def approve(self, approved_by_user_id: uuid.UUID) -> bool:
        """Aprueba el asiento contable"""
        if self.status != JournalEntryStatus.PENDING:
            raise ValueError("Solo se pueden aprobar asientos en estado pendiente")
        
        errors = self.validate_entry()
        if errors:
            raise ValueError(f"No se puede aprobar el asiento: {'; '.join(errors)}")
        
        self.status = JournalEntryStatus.APPROVED
        self.approved_by_id = approved_by_user_id
        self.approved_at = datetime.now(timezone.utc)
        return True

    def post(self, posted_by_user_id: uuid.UUID) -> bool:
        """Contabiliza el asiento (lo hace efectivo en las cuentas)"""
        if not self.can_be_posted:
            raise ValueError("El asiento no puede ser contabilizado en su estado actual")
        
        # Actualizar saldos de las cuentas
        for line in self.lines:
            line.account.update_balance(line.debit_amount, line.credit_amount)
        
        self.status = JournalEntryStatus.POSTED
        self.posted_by_id = posted_by_user_id
        self.posted_at = datetime.now(timezone.utc)
        self.posting_date = datetime.now(timezone.utc)
        return True


class JournalEntryLine(Base):
    """
    Modelo de líneas de asientos contables (detalle)
    Cada línea representa un movimiento en una cuenta
    """
    __tablename__ = "journal_entry_lines"

    # Relación con el asiento
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("journal_entries.id"), nullable=False)
    
    # Relación con la cuenta
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    
    # Importes
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Descripción específica de la línea
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Referencias adicionales
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    third_party_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Para cuentas que requieren terceros
    cost_center_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Para centros de costo
    
    # Orden de la línea en el asiento
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account")

    def __repr__(self) -> str:
        return f"<JournalEntryLine(account='{self.account.code}', debit={self.debit_amount}, credit={self.credit_amount})>"

    @property
    def amount(self) -> Decimal:
        """Retorna el importe de la línea (débito o crédito)"""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount

    @property
    def movement_type(self) -> str:
        """Retorna el tipo de movimiento (debit/credit)"""
        return "debit" if self.debit_amount > 0 else "credit"

    @property
    def is_valid(self) -> bool:
        """Verifica si la línea es válida"""
        return len(self.validate_line()) == 0

    def validate_line(self) -> List[str]:
        """
        Valida la línea del asiento y retorna lista de errores
        """
        errors = []
        
        # Validar que tenga débito O crédito, pero no ambos
        if self.debit_amount > 0 and self.credit_amount > 0:
            errors.append("Una línea no puede tener débito y crédito al mismo tiempo")
        
        # Validar que tenga al menos uno de los dos
        if self.debit_amount == 0 and self.credit_amount == 0:
            errors.append("Una línea debe tener débito o crédito")
        
        # Validar importes positivos
        if self.debit_amount < 0 or self.credit_amount < 0:
            errors.append("Los importes no pueden ser negativos")
        
        # Validar que la cuenta permita movimientos
        if self.account and not self.account.can_receive_movements:
            errors.append(f"La cuenta {self.account.code} - {self.account.name} no puede recibir movimientos")
        
        # Validar terceros si es requerido
        if self.account and self.account.requires_third_party and not self.third_party_id:
            errors.append(f"La cuenta {self.account.code} requiere tercero")
        
        # Validar centro de costo si es requerido
        if self.account and self.account.requires_cost_center and not self.cost_center_id:
            errors.append(f"La cuenta {self.account.code} requiere centro de costo")
        
        return errors