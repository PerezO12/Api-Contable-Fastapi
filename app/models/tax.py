"""
Tax models for managing different types of taxes (VAT, Sales Tax, etc.)
Supports Odoo-style tax configuration for invoices.
"""
import uuid
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, ForeignKey, Numeric, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.user import User


class TaxType(str, Enum):
    """Tipos de impuesto"""
    SALE = "sale"           # Impuesto de venta (IVA)
    PURCHASE = "purchase"   # Impuesto de compra


class TaxScope(str, Enum):
    """Alcance del impuesto"""
    INCLUSIVE = "inclusive"  # Precio incluye impuesto
    EXCLUSIVE = "exclusive"  # Precio no incluye impuesto


class Tax(Base):
    """
    Modelo para impuestos (IVA, impuestos de ventas, etc.)
    Sigue el patrón de Odoo para configuración de impuestos
    """
    __tablename__ = "taxes"

    # Identificación
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False,
                                     comment="Código único del impuesto (ej: IVA21)")
    name: Mapped[str] = mapped_column(String(100), nullable=False,
                                     comment="Nombre del impuesto")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True,
                                                      comment="Descripción detallada")
    
    # Configuración del impuesto
    tax_type: Mapped[TaxType] = mapped_column(SQLEnum(TaxType), nullable=False,
                                             comment="Tipo: venta o compra")
    tax_scope: Mapped[TaxScope] = mapped_column(SQLEnum(TaxScope), default=TaxScope.EXCLUSIVE, nullable=False,
                                               comment="Si el precio incluye o excluye el impuesto")
    percentage: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), default=0, nullable=False,
                                               comment="Porcentaje del impuesto")
    
    # Cuenta contable donde se contabiliza el impuesto
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False,
                                                  comment="Cuenta contable del impuesto")
    
    # Estado y configuración
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False,
                                            comment="Si es el impuesto por defecto para su tipo")
    
    # Auditoría
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    account: Mapped["Account"] = relationship("Account", lazy="select")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<Tax(code='{self.code}', name='{self.name}', percentage={self.percentage}%)>"

    def calculate_tax_amount(self, base_amount: Decimal) -> Decimal:
        """
        Calcula el monto de impuesto para un monto base dado
        """
        if not base_amount or self.percentage <= 0:
            return Decimal('0')
        
        return base_amount * (self.percentage / Decimal('100'))

    def get_tax_and_total(self, base_amount: Decimal) -> tuple[Decimal, Decimal]:
        """
        Retorna tupla (monto_impuesto, monto_total)
        """
        tax_amount = self.calculate_tax_amount(base_amount)
        total_amount = base_amount + tax_amount
        return tax_amount, total_amount

    @property
    def display_name(self) -> str:
        """Nombre para mostrar en formularios"""
        return f"{self.name} ({self.percentage}%)"

    @property
    def is_sales_tax(self) -> bool:
        """Indica si es impuesto de venta"""
        return self.tax_type == TaxType.SALE

    @property
    def is_purchase_tax(self) -> bool:
        """Indica si es impuesto de compra"""
        return self.tax_type == TaxType.PURCHASE
