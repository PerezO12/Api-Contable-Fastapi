import uuid
from decimal import Decimal
from datetime import datetime, timezone, date
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, ForeignKey, Numeric, DateTime, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.account import Account
from app.models.base import Base
from app.models.user import User

if TYPE_CHECKING:
    from app.models.cost_center import CostCenter
    from app.models.third_party import ThirdParty
    from app.models.payment_terms import PaymentTerms
    from app.models.product import Product


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


class TransactionOrigin(str, Enum):
    """Origen de la transacción contable"""
    SALE = "sale"  # Venta
    PURCHASE = "purchase"  # Compra
    ADJUSTMENT = "adjustment"  # Ajuste
    TRANSFER = "transfer"  # Transferencia
    PAYMENT = "payment"  # Pago
    COLLECTION = "collection"  # Cobro
    OPENING = "opening"  # Apertura
    CLOSING = "closing"  # Cierre
    OTHER = "other"  # Otro


class JournalEntry(Base):
    """
    Modelo de asientos contables (encabezado)
    Implementa el patrón Header-Detail para doble partida
    """
    __tablename__ = "journal_entries"    # Información básica del asiento
    number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Descripción del asiento (opcional, se genera automáticamente si no se proporciona)")
      # Tipo de asiento
    entry_type: Mapped[JournalEntryType] = mapped_column(default=JournalEntryType.MANUAL, nullable=False)
    
    # Origen de la transacción
    transaction_origin: Mapped[Optional[TransactionOrigin]] = mapped_column(nullable=True,
                                                                          comment="Origen de la transacción (venta, compra, etc.)")
    
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

    @property
    def earliest_due_date(self) -> Optional[date]:
        """Retorna la fecha de vencimiento más próxima de todas las líneas del asiento"""
        due_dates = []
        
        for line in self.lines:
            effective_due_date = line.effective_due_date
            if effective_due_date:
                due_dates.append(effective_due_date)
        
        if due_dates:
            return min(due_dates)
        return None

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
        if self.status not in [JournalEntryStatus.DRAFT, JournalEntryStatus.PENDING]:
            raise ValueError("Solo se pueden aprobar asientos en estado borrador o pendiente")
        
        # Note: validation is performed in the service layer to avoid async issues
        # errors = self.validate_entry()
        # if errors:
        #     raise ValueError(f"No se puede aprobar el asiento: {'; '.join(errors)}")
        
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

    def reset_to_draft(self, reset_by_user_id: uuid.UUID) -> bool:
        """Restablece el asiento a borrador desde cualquier estado"""
        # COMENTADO: Permitir restablecer desde cualquier estado
        # if self.status not in [JournalEntryStatus.APPROVED, JournalEntryStatus.PENDING]:
        #     raise ValueError("Solo se pueden restablecer asientos desde estado aprobado o pendiente")
        
        # COMENTADO: Verificar que no esté contabilizado
        # if self.status == JournalEntryStatus.POSTED:
        #     raise ValueError("No se puede restablecer a borrador un asiento contabilizado")
        
        # COMENTADO: Verificar que no esté cancelado
        # if self.status == JournalEntryStatus.CANCELLED:
        #     raise ValueError("No se puede restablecer a borrador un asiento cancelado")
        
        # Limpiar campos de aprobación
        self.status = JournalEntryStatus.DRAFT
        self.approved_by_id = None
        self.approved_at = None
        
        # Si estaba contabilizado, limpiar también esos campos
        if hasattr(self, 'posted_by_id'):
            self.posted_by_id = None
        if hasattr(self, 'posted_at'):
            self.posted_at = None
        
        # Agregar nota del restablecimiento
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        reset_note = f"Restablecido a borrador el {timestamp} por usuario {reset_by_user_id}"
        
        if self.notes:
            self.notes += f"\\n\\n{reset_note}"
        else:
            self.notes = reset_note
        
        return True

    @property
    def can_be_reset_to_draft(self) -> bool:
        """Verifica si el asiento puede ser restablecido a borrador"""
        return self.status in [JournalEntryStatus.APPROVED, JournalEntryStatus.PENDING]


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
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # Referencias adicionales
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    third_party_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("third_parties.id"), nullable=True)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cost_centers.id"), nullable=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id"), nullable=True,
                                                           comment="Producto asociado a esta línea")
    
    # Información adicional del producto en la transacción
    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=4), nullable=True,
                                                       comment="Cantidad del producto")
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=4), nullable=True,
                                                         comment="Precio unitario del producto")
    discount_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=5, scale=2), nullable=True,
                                                                  comment="Porcentaje de descuento aplicado")
    discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True,
                                                              comment="Monto de descuento aplicado")
    tax_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=5, scale=2), nullable=True,
                                                             comment="Porcentaje de impuesto aplicado")
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True,
                                                         comment="Monto de impuesto aplicado")
    
    # Fechas de facturación y pago
    invoice_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, 
                                                        comment="Fecha de la factura (diferente a fecha de creación del asiento)")
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, 
                                                    comment="Fecha de vencimiento de la factura")
    
    # Condiciones de pago
    payment_terms_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("payment_terms.id"), nullable=True,
                                                                  comment="Condiciones de pago aplicables a esta línea")
    
    # Orden de la línea en el asiento
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account")
    third_party: Mapped[Optional["ThirdParty"]] = relationship("ThirdParty", lazy="select")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter", lazy="select")
    payment_terms: Mapped[Optional["PaymentTerms"]] = relationship("PaymentTerms", lazy="select")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="journal_entry_lines", lazy="select")
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
    def account_code(self) -> Optional[str]:
        """Retorna el código de la cuenta"""
        return self.account.code if self.account else None

    @property
    def account_name(self) -> Optional[str]:
        """Retorna el nombre de la cuenta"""
        return self.account.name if self.account else None

    @property
    def third_party_code(self) -> Optional[str]:
        """Retorna el código del tercero"""
        return self.third_party.code if self.third_party else None

    @property
    def third_party_name(self) -> Optional[str]:
        """Retorna el nombre del tercero"""
        return self.third_party.name if self.third_party else None

    @property
    def cost_center_code(self) -> Optional[str]:
        """Retorna el código del centro de costo"""
        return self.cost_center.code if self.cost_center else None

    @property
    def cost_center_name(self) -> Optional[str]:
        """Retorna el nombre del centro de costo"""
        return self.cost_center.name if self.cost_center else None

    
    @property
    def payment_terms_code(self) -> Optional[str]:
        """Retorna el código de las condiciones de pago"""
        return self.payment_terms.code if self.payment_terms else None

    
    @property
    def payment_terms_name(self) -> Optional[str]:
        """Retorna el nombre de las condiciones de pago"""
        return self.payment_terms.name if self.payment_terms else None

    
    @property
    def effective_invoice_date(self) -> date:
        """Retorna la fecha de factura efectiva (si no está definida, usa la fecha del asiento)"""
        if self.invoice_date:
            return self.invoice_date
        # Convertir datetime a date si es necesario
        entry_date = self.journal_entry.entry_date
        if isinstance(entry_date, datetime):
            return entry_date.date()
        return entry_date

    @property
    def effective_due_date(self) -> Optional[date]:
        """Retorna la fecha de vencimiento efectiva basada en condiciones de pago o fecha manual"""
        if self.due_date:
            return self.due_date        
        if self.payment_terms and self.payment_terms.payment_schedules:
            # Si tiene condiciones de pago, calcular basado en el último pago
            last_schedule = max(self.payment_terms.payment_schedules, key=lambda x: x.days)
            invoice_datetime = datetime.combine(self.effective_invoice_date, datetime.min.time())
            due_datetime = last_schedule.calculate_payment_date(invoice_datetime)
            return due_datetime.date()
        
        return None

    def calculate_and_set_due_date(self) -> None:
        """
        Calcula y establece automáticamente la fecha de vencimiento basada en payment terms.
        Si hay payment_terms_id pero no due_date, calcula la fecha de vencimiento automáticamente.
        """
        # Solo calcular si hay payment_terms pero no hay due_date manual
        if self.payment_terms_id and not self.due_date and self.payment_terms:
            # Si las condiciones de pago tienen cronograma
            if self.payment_terms.payment_schedules:
                # Obtener el último pago (mayor número de días)
                last_schedule = max(self.payment_terms.payment_schedules, key=lambda x: x.days)
                
                # Usar la fecha de factura efectiva como base
                invoice_datetime = datetime.combine(self.effective_invoice_date, datetime.min.time())
                
                # Calcular la fecha de vencimiento
                due_datetime = last_schedule.calculate_payment_date(invoice_datetime)
                
                # Establecer la fecha de vencimiento en la base de datos
                self.due_date = due_datetime.date()

    def get_payment_schedule(self) -> List[dict]:
        """
        Retorna el cronograma de pagos basado en las condiciones de pago
        
        Returns:
            Lista de diccionarios con información de cada pago programado
        """
        if not self.payment_terms:
            # Si no hay condiciones de pago pero hay fecha de vencimiento
            if self.due_date:
                return [{
                    'sequence': 1,
                    'days': (self.due_date - self.effective_invoice_date).days,
                    'percentage': Decimal('100.00'),
                    'amount': self.amount,
                    'payment_date': self.due_date,
                    'description': 'Pago único'
                }]
            return []
        
        # Calcular pagos basados en condiciones de pago
        invoice_datetime = datetime.combine(self.effective_invoice_date, datetime.min.time())
        payment_schedule = []
        
        for schedule in self.payment_terms.payment_schedules:
            payment_date = schedule.calculate_payment_date(invoice_datetime)
            payment_amount = schedule.calculate_amount(self.amount)
            
            payment_schedule.append({
                'sequence': schedule.sequence,
                'days': schedule.days,
                'percentage': schedule.percentage,
                'amount': payment_amount,
                'payment_date': payment_date.date(),
                'description': schedule.description or f'Pago {schedule.sequence}'
            })
        
        return sorted(payment_schedule, key=lambda x: x['sequence'])

    # Propiedades adicionales para información detallada del tercero
    @property
    def third_party_document_type(self) -> Optional[str]:
        """Retorna el tipo de documento del tercero"""
        return self.third_party.document_type.value if self.third_party and self.third_party.document_type else None

    @property
    def third_party_document_number(self) -> Optional[str]:
        """Retorna el número de documento del tercero"""
        return self.third_party.document_number if self.third_party else None

    @property
    def third_party_tax_id(self) -> Optional[str]:
        """Retorna el ID fiscal del tercero"""
        return self.third_party.tax_id if self.third_party else None

    @property
    def third_party_email(self) -> Optional[str]:
        """Retorna el email del tercero"""
        return self.third_party.email if self.third_party else None

    
    @property
    def third_party_phone(self) -> Optional[str]:
        """Retorna el teléfono del tercero"""
        return self.third_party.phone if self.third_party else None

    @property
    def third_party_address(self) -> Optional[str]:
        """Retorna la dirección del tercero"""
        return self.third_party.address if self.third_party else None

    
    @property
    def third_party_city(self) -> Optional[str]:
        """Retorna la ciudad del tercero"""
        return self.third_party.city if self.third_party else None

    @property
    def third_party_type(self) -> Optional[str]:
        """Retorna el tipo del tercero"""
        return self.third_party.third_party_type.value if self.third_party and self.third_party.third_party_type else None    # Propiedades adicionales para información detallada de términos de pago
    @property
    def payment_terms_description(self) -> Optional[str]:
        """Retorna la descripción de las condiciones de pago"""
        return self.payment_terms.description if self.payment_terms else None

    # Propiedades relacionadas con productos
    @property
    def product_code(self) -> Optional[str]:
        """Retorna el código del producto"""
        return self.product.code if self.product else None

    @property
    def product_name(self) -> Optional[str]:
        """Retorna el nombre del producto"""
        return self.product.name if self.product else None

    @property
    def product_type(self) -> Optional[str]:
        """Retorna el tipo del producto"""
        return self.product.product_type.value if self.product and self.product.product_type else None

    @property
    def product_measurement_unit(self) -> Optional[str]:
        """Retorna la unidad de medida del producto"""
        return self.product.measurement_unit.value if self.product and self.product.measurement_unit else None

    @property
    def subtotal_before_discount(self) -> Optional[Decimal]:
        """Calcula el subtotal antes del descuento (cantidad * precio unitario)"""
        if self.quantity and self.unit_price:
            return self.quantity * self.unit_price
        return None

    @property
    def effective_unit_price(self) -> Optional[Decimal]:
        """Calcula el precio unitario efectivo después del descuento"""
        if not self.unit_price:
            return None
            
        if self.discount_percentage:
            discount_factor = (Decimal('100') - self.discount_percentage) / Decimal('100')
            return self.unit_price * discount_factor
        elif self.discount_amount and self.quantity:
            discount_per_unit = self.discount_amount / self.quantity
            return self.unit_price - discount_per_unit
        
        return self.unit_price

    @property
    def total_discount(self) -> Decimal:
        """Calcula el descuento total aplicado"""
        if self.discount_amount:
            return self.discount_amount
        elif self.discount_percentage and self.subtotal_before_discount:
            return self.subtotal_before_discount * (self.discount_percentage / Decimal('100'))
        return Decimal('0')

    @property
    def subtotal_after_discount(self) -> Optional[Decimal]:
        """Calcula el subtotal después del descuento"""
        if self.subtotal_before_discount:
            return self.subtotal_before_discount - self.total_discount
        return None

    @property
    def net_amount(self) -> Optional[Decimal]:
        """Calcula el monto neto (después de descuentos, antes de impuestos)"""
        return self.subtotal_after_discount

    @property
    def gross_amount(self) -> Optional[Decimal]:
        """Calcula el monto bruto (después de descuentos e impuestos)"""
        if self.net_amount:
            tax = self.tax_amount or Decimal('0')
            return self.net_amount + tax
        return None

    def calculate_tax_amount(self) -> Optional[Decimal]:
        """Calcula el monto de impuesto basado en el porcentaje y el monto neto"""
        if self.tax_percentage and self.net_amount:
            return self.net_amount * (self.tax_percentage / Decimal('100'))
        return self.tax_amount

    def validate_product_info(self) -> List[str]:
        """Valida la información del producto en la línea"""
        errors = []
        
        # Si hay producto, validar coherencia
        if self.product_id:
            if self.quantity and self.quantity <= 0:
                errors.append("La cantidad debe ser mayor a cero")
                
            if self.unit_price and self.unit_price < 0:
                errors.append("El precio unitario no puede ser negativo")
                
            if self.discount_percentage and (self.discount_percentage < 0 or self.discount_percentage > 100):
                errors.append("El porcentaje de descuento debe estar entre 0 y 100")
                
            if self.discount_amount and self.discount_amount < 0:
                errors.append("El monto de descuento no puede ser negativo")
                
            if self.tax_percentage and self.tax_percentage < 0:
                errors.append("El porcentaje de impuesto no puede ser negativo")
                
            if self.tax_amount and self.tax_amount < 0:
                errors.append("El monto de impuesto no puede ser negativo")
                
            # Validar que no se especifiquen ambos tipos de descuento
            if self.discount_percentage and self.discount_amount:
                errors.append("No se puede especificar porcentaje y monto de descuento al mismo tiempo")
                
            # Validar coherencia entre cantidades y montos
            if self.quantity and self.unit_price and self.amount:
                expected_amount = self.gross_amount or self.net_amount or (self.quantity * self.unit_price)
                if expected_amount and abs(self.amount - expected_amount) > Decimal('0.01'):                    errors.append("El monto de la línea no coincide con el cálculo del producto")
        
        return errors

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
        
        # Validar información del producto
        product_errors = self.validate_product_info()
        errors.extend(product_errors)
        
        return errors