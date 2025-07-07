"""
Currency and Exchange Rate models for multi-currency support
"""
import uuid
from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Numeric, Boolean, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.journal_entry import JournalEntryLine


class Currency(Base):
    """
    Modelo para monedas del sistema
    """
    __tablename__ = "currencies"
    
    # Información básica de la moneda
    code: Mapped[str] = mapped_column(
        String(3), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="Código ISO 4217 de la moneda (USD, EUR, etc.)"
    )
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Nombre completo de la moneda"
    )
    symbol: Mapped[Optional[str]] = mapped_column(
        String(10), 
        nullable=True,
        comment="Símbolo de la moneda ($, €, etc.)"
    )
    
    # Configuración de decimales
    decimal_places: Mapped[int] = mapped_column(
        default=2,
        nullable=False,
        comment="Número de decimales para esta moneda"
    )
    
    # Estado de la moneda
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Si la moneda está activa para uso"
    )
    
    # Metadatos adicionales
    country_code: Mapped[Optional[str]] = mapped_column(
        String(2), 
        nullable=True,
        comment="Código ISO del país principal (opcional)"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True,
        comment="Notas adicionales sobre la moneda"
    )
    
    # Relationships
    exchange_rates: Mapped[List["ExchangeRate"]] = relationship(
        "ExchangeRate",
        back_populates="currency",
        cascade="all, delete-orphan"
    )
    journal_entry_lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine",
        back_populates="currency"
    )
    
    def __repr__(self) -> str:
        return f"<Currency(code='{self.code}', name='{self.name}')>"
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI"""
        if self.symbol:
            return f"{self.code} ({self.symbol}) - {self.name}"
        return f"{self.code} - {self.name}"


class ExchangeRate(Base):
    """
    Modelo para tipos de cambio históricos
    """
    __tablename__ = "exchange_rates"
    
    # Relación con la moneda
    currency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("currencies.id"),
        nullable=False,
        index=True,
        comment="ID de la moneda"
    )
    
    # Tipo de cambio
    rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=6),
        nullable=False,
        comment="Tasa de cambio: 1 unidad de esta moneda = rate unidades de moneda base"
    )
    
    # Fecha de vigencia
    rate_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Fecha de vigencia del tipo de cambio"
    )
    
    # Origen del tipo de cambio
    source: Mapped[str] = mapped_column(
        String(50),
        default="manual",
        nullable=False,
        comment="Origen del tipo de cambio (manual, api_import, etc.)"
    )
    
    # Metadatos del tipo de cambio
    provider: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Proveedor de la tasa (si es automática)"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Notas adicionales sobre este tipo de cambio"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('currency_id', 'rate_date', name='uq_exchange_rates_currency_date'),
    )
    
    # Relationships
    currency: Mapped["Currency"] = relationship(
        "Currency",
        back_populates="exchange_rates"
    )
    journal_entry_lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine",
        back_populates="exchange_rate"
    )
    
    def __repr__(self) -> str:
        return f"<ExchangeRate(currency='{self.currency.code}', rate={self.rate}, date='{self.rate_date}')>"
    
    @property
    def is_recent(self) -> bool:
        """Verifica si el tipo de cambio es reciente (últimos 7 días)"""
        from datetime import timedelta
        today = date.today()
        return (today - self.rate_date).days <= 7
    
    def convert_to_base(self, amount: Decimal) -> Decimal:
        """Convierte un importe de esta moneda a la moneda base"""
        return amount * self.rate
    
    def convert_from_base(self, amount: Decimal) -> Decimal:
        """Convierte un importe de la moneda base a esta moneda"""
        if self.rate == 0:
            raise ValueError("No se puede convertir con tasa de cambio 0")
        return amount / self.rate
