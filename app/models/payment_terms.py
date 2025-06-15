import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PaymentTerms(Base):
    """
    Modelo de condiciones de pago
    Define los términos y plazos de pago para facturas
    """
    __tablename__ = "payment_terms"

    # Información básica
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadatos
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    payment_schedules: Mapped[List["PaymentSchedule"]] = relationship(
        "PaymentSchedule",
        back_populates="payment_terms",
        cascade="all, delete-orphan",
        order_by="PaymentSchedule.sequence"
    )

    def __repr__(self) -> str:
        return f"<PaymentTerms(code='{self.code}', name='{self.name}')>"

    @property
    def total_percentage(self) -> Decimal:
        """Retorna el porcentaje total de todos los pagos"""
        return Decimal(str(sum(schedule.percentage for schedule in self.payment_schedules)))

    @property
    def is_valid(self) -> bool:
        """Verifica si las condiciones de pago son válidas"""
        return (
            len(self.payment_schedules) > 0 and
            self.total_percentage == Decimal('100.00') and
            all(schedule.is_valid for schedule in self.payment_schedules)
        )

    def calculate_payment_dates(self, invoice_date: datetime) -> List[dict]:
        """
        Calcula las fechas de pago basadas en la fecha de factura
        
        Args:
            invoice_date: Fecha de la factura
            
        Returns:
            Lista de diccionarios con información de cada pago
        """
        payment_dates = []
        
        for schedule in self.payment_schedules:
            payment_date = schedule.calculate_payment_date(invoice_date)
            payment_dates.append({
                'sequence': schedule.sequence,
                'days': schedule.days,
                'percentage': schedule.percentage,
                'payment_date': payment_date,
                'description': schedule.description
            })
        
        return payment_dates


class PaymentSchedule(Base):
    """
    Modelo de cronograma de pagos
    Define cada período de pago dentro de las condiciones de pago
    """
    __tablename__ = "payment_schedules"    # Relación con condiciones de pago
    payment_terms_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_terms.id"), nullable=False)
    
    # Información del período
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)  # Orden del pago
    days: Mapped[int] = mapped_column(Integer, nullable=False)  # Días desde la fecha de factura
    percentage: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), nullable=False)  # Porcentaje a pagar
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Relationships
    payment_terms: Mapped["PaymentTerms"] = relationship("PaymentTerms", back_populates="payment_schedules")

    def __repr__(self) -> str:
        return f"<PaymentSchedule(days={self.days}, percentage={self.percentage}%)>"

    @property
    def is_valid(self) -> bool:
        """Verifica si el cronograma de pago es válido"""
        return (
            self.days >= 0 and
            Decimal('0') < self.percentage <= Decimal('100') and
            self.sequence > 0
        )

    def calculate_payment_date(self, invoice_date: datetime) -> datetime:
        """
        Calcula la fecha de pago basada en la fecha de factura
        
        Args:
            invoice_date: Fecha de la factura
            
        Returns:
            Fecha de pago calculada
        """
        from datetime import timedelta
        return invoice_date + timedelta(days=self.days)

    def calculate_amount(self, total_amount: Decimal) -> Decimal:
        """
        Calcula el monto a pagar basado en el porcentaje
        
        Args:
            total_amount: Monto total de la factura
            
        Returns:
            Monto correspondiente a este período
        """
        return (total_amount * self.percentage) / Decimal('100')
