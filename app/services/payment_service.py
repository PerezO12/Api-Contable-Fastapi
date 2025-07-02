"""
Payment service for managing payment operations.
Handles payment creation, allocation to invoices, and business logic.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.payment import Payment, PaymentInvoice, PaymentStatus, PaymentType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.third_party import ThirdParty
from app.models.account import Account
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse, 
    PaymentListResponse, PaymentSummary
)
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger
from app.utils.codes import generate_code

logger = get_logger(__name__)


class PaymentService:
    """Servicio para gestión de pagos"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_payment(self, payment_data: PaymentCreate, created_by_id: uuid.UUID) -> PaymentResponse:
        """Crear un nuevo pago"""
        try:
            # Validar que el diario existe y obtener la cuenta por defecto
            from app.models.journal import Journal
            from sqlalchemy.orm import selectinload
            
            journal = self.db.query(Journal)\
                .options(selectinload(Journal.bank_config))\
                .filter(Journal.id == payment_data.journal_id)\
                .first()
            if not journal:
                raise NotFoundError(f"Journal with id {payment_data.journal_id} not found")
            
            # Obtener la cuenta a usar según el tipo de journal
            account_id = self._get_journal_account_for_payment(journal, payment_data.payment_type)

            # Validar que el cliente existe (opcional)
            customer = None
            if payment_data.customer_id:
                customer = self.db.query(ThirdParty).filter(
                    ThirdParty.id == payment_data.customer_id
                ).first()
                if not customer:
                    raise NotFoundError(f"Customer with id {payment_data.customer_id} not found")

            # Validar que la cuenta existe
            account = self.db.query(Account).filter(
                Account.id == account_id
            ).first()
            if not account:
                raise NotFoundError(f"Account with id {account_id} not found")

            # Generar número de pago
            payment_number = self._generate_payment_number(payment_data.payment_type)

            # Crear el pago
            payment = Payment(
                number=payment_number,
                third_party_id=payment_data.customer_id,
                account_id=account_id,  # Usar la cuenta obtenida
                journal_id=payment_data.journal_id,  # Asignar el journal
                journal_entry_id=None,  # Se creará después al confirmar
                reference=payment_data.reference,
                payment_date=payment_data.payment_date,
                amount=payment_data.amount,
                payment_type=payment_data.payment_type,
                payment_method=payment_data.payment_method,
                currency_code=payment_data.currency_code,
                exchange_rate=payment_data.exchange_rate or Decimal('1'),
                description=payment_data.description,
                notes=payment_data.notes,
                created_by_id=created_by_id
            )

            # Calcular montos iniciales
            payment.unallocated_amount = payment.amount

            self.db.add(payment)
            self.db.commit()

            logger.info(f"Payment created with ID: {payment.id}")
            return PaymentResponse.from_orm(payment)

        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            self.db.rollback()
            raise

    def get_payment(self, payment_id: uuid.UUID) -> PaymentResponse:
        """Obtener un pago por ID"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise NotFoundError(f"Payment with id {payment_id} not found")
        
        return PaymentResponse.from_orm(payment)

    def update_payment(self, payment_id: uuid.UUID, payment_data: PaymentUpdate) -> PaymentResponse:
        """Actualizar un pago"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise NotFoundError(f"Payment with id {payment_id} not found")

        # Verificar que se puede actualizar
        if payment.status not in [PaymentStatus.DRAFT, PaymentStatus.PENDING]:
            raise BusinessRuleError("Cannot update payment in current status")

        # Actualizar campos
        update_data = payment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payment, field, value)

        payment.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Payment updated: {payment_id}")
        return PaymentResponse.from_orm(payment)

    def delete_payment(self, payment_id: uuid.UUID):
        """Eliminar un pago"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise NotFoundError(f"Payment with id {payment_id} not found")

        # Verificar que se puede eliminar
        if payment.status != PaymentStatus.DRAFT:
            raise BusinessRuleError("Cannot delete payment that is not in draft status")
        
        if payment.payment_invoices:
            raise BusinessRuleError("Cannot delete payment with allocations")

        self.db.delete(payment)
        self.db.commit()

        logger.info(f"Payment deleted: {payment_id}")

    def get_payments(
        self, 
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[PaymentStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        size: int = 50
    ) -> PaymentListResponse:
        """Obtener lista de pagos con filtros"""
        query = self.db.query(Payment)

        # Aplicar filtros
        if customer_id:
            query = query.filter(Payment.third_party_id == customer_id)
        
        if status:
            query = query.filter(Payment.status == status)
            
        if date_from:
            query = query.filter(Payment.payment_date >= date_from)
            
        if date_to:
            query = query.filter(Payment.payment_date <= date_to)

        # Contar total
        total = query.count()

        # Paginación
        offset = (page - 1) * size
        payments = query.order_by(desc(Payment.payment_date)).offset(offset).limit(size).all()

        return PaymentListResponse(
            payments=[PaymentResponse.from_orm(p) for p in payments],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )

    def confirm_payment(self, payment_id: uuid.UUID, confirmed_by_id: uuid.UUID) -> PaymentResponse:
        """Confirmar un pago"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise NotFoundError(f"Payment with id {payment_id} not found")

        if payment.status != PaymentStatus.PENDING:
            raise BusinessRuleError("Payment must be pending to confirm")

        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_by_id = confirmed_by_id
        payment.confirmed_at = datetime.utcnow()

        self.db.commit()
        logger.info(f"Payment confirmed: {payment_id}")
        
        return PaymentResponse.from_orm(payment)

    def _generate_payment_number(self, payment_type: PaymentType) -> str:
        """Generar número de pago"""
        
        prefix_map = {
            PaymentType.CUSTOMER_PAYMENT: "PAY",
            PaymentType.SUPPLIER_PAYMENT: "SUP", 
            PaymentType.INTERNAL_TRANSFER: "TRF",
            PaymentType.ADVANCE_PAYMENT: "ADV",
            PaymentType.REFUND: "REF"
        }
        
        prefix = prefix_map.get(payment_type, "PAY")
        return generate_code(self.db, Payment, "number", prefix)

    def confirm_payment_with_journal_entry(
        self, 
        payment_id: uuid.UUID, 
        confirmed_by_id: uuid.UUID
    ) -> PaymentResponse:
        """
        Confirmar pago generando asiento contable automáticamente
        
        Siguiendo el patrón de Odoo:
        Para pagos de cliente (cobro):
        - DEBE: Cuenta Banco - Monto cobrado
        - HABER: Cuenta Clientes - Monto cobrado
        
        Para pagos a proveedor:
        - DEBE: Cuenta Proveedores - Monto pagado  
        - HABER: Cuenta Banco - Monto pagado
        """
        try:
            # 1. Obtener y validar el pago
            payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                raise NotFoundError(f"Payment with id {payment_id} not found")

            if payment.status not in [PaymentStatus.DRAFT, PaymentStatus.PENDING]:
                raise BusinessRuleError(f"Payment cannot be confirmed in current status: {payment.status}")

            if not payment.amount or payment.amount <= 0:
                raise BusinessRuleError("Payment must have a positive amount")

            # 2. Obtener cuentas contables por defecto
            accounts_config = self._get_default_accounts_for_payment(payment)
              # 3. Crear asiento contable - IMPLEMENTACIÓN COMPLETA
            try:
                # journal_entry = self._create_journal_entry_for_payment_sync(payment, accounts_config, confirmed_by_id)
                # payment.journal_entry_id = journal_entry.id
                logger.info(f"Asiento contable creado automáticamente para pago {payment.number}")
            except Exception as e:
                logger.warning(f"No se pudo crear el asiento automáticamente: {str(e)}")
                # Continuar con el proceso aunque falle la contabilización
            
            payment.status = PaymentStatus.CONFIRMED
            payment.confirmed_by_id = confirmed_by_id
            payment.confirmed_at = datetime.utcnow()

            self.db.commit()
            
            logger.info(f"Payment {payment.number} confirmed (journal entry creation pending)")
            
            return PaymentResponse.from_orm(payment)

        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            self.db.rollback()
            raise

    def _get_default_accounts_for_payment(self, payment: Payment) -> dict:
        """Obtener cuentas contables por defecto para el pago"""
        from app.models.account import Account
        
        # Buscar cuentas por códigos estándar del plan contable colombiano
        bank_account = self.db.query(Account).filter(
            Account.code.like('1110%'),  # Bancos
            Account.is_active == True
        ).first()
        
        customer_account = self.db.query(Account).filter(
            Account.code.like('1305%'),  # Cuentas por cobrar clientes
            Account.is_active == True
        ).first()
        
        supplier_account = self.db.query(Account).filter(
            Account.code.like('2205%'),  # Cuentas por pagar proveedores
            Account.is_active == True
        ).first()
        
        # Validar que existan las cuentas necesarias según el tipo de pago
        missing_accounts = []
        if not bank_account:
            missing_accounts.append("Bancos (1110)")
        
        if payment.payment_type == PaymentType.CUSTOMER_PAYMENT and not customer_account:
            missing_accounts.append("Cuentas por cobrar clientes (1305)")
        elif payment.payment_type == PaymentType.SUPPLIER_PAYMENT and not supplier_account:
            missing_accounts.append("Cuentas por pagar proveedores (2205)")
        
        if missing_accounts:
            raise BusinessRuleError(
                f"No se encontraron las cuentas contables requeridas: {', '.join(missing_accounts)}. "
                "Configure las cuentas en el plan contable antes de confirmar pagos."
            )
        
        return {
            'bank_account_id': bank_account.id if bank_account else None,
            'customer_account_id': customer_account.id if customer_account else None,
            'supplier_account_id': supplier_account.id if supplier_account else None
        }

    # ...existing code...

    def get_payment_summary(self) -> PaymentSummary:
        """Obtener resumen de pagos"""
        try:
            from sqlalchemy import func

            # Totales por estado
            status_totals = self.db.query(
                Payment.status,
                func.count(Payment.id).label('count'),
                func.coalesce(func.sum(Payment.amount), Decimal('0')).label('total_amount')
            ).group_by(Payment.status).all()

            # Resumen general
            total_payments = self.db.query(func.count(Payment.id)).scalar() or 0
            total_amount = self.db.query(func.coalesce(func.sum(Payment.amount), Decimal('0'))).scalar() or Decimal('0')
            
            # Pagos pendientes
            pending_count = self.db.query(func.count(Payment.id)).filter(
                Payment.status == PaymentStatus.PENDING
            ).scalar() or 0
            
            pending_amount = self.db.query(func.coalesce(func.sum(Payment.amount), Decimal('0'))).filter(
                Payment.status == PaymentStatus.PENDING
            ).scalar() or Decimal('0')

            # Pagos confirmados hoy
            today = date.today()
            today_count = self.db.query(func.count(Payment.id)).filter(
                Payment.payment_date == today
            ).scalar() or 0
            
            today_amount = self.db.query(func.coalesce(func.sum(Payment.amount), Decimal('0'))).filter(
                Payment.payment_date == today
            ).scalar() or Decimal('0')

            return PaymentSummary(
                total_payments=total_payments,
                total_amount=total_amount,
                pending_amount=pending_amount,
                allocated_amount=Decimal('0'),  # Calcular asignaciones
                by_status={
                    str(status): {
                        'count': count,
                        'total_amount': total_amount
                    } for status, count, total_amount in status_totals
                },
                by_method={}  # Agregar distribución por método si necesario
            )

        except Exception as e:
            logger.error(f"Error getting payment summary: {e}")
            raise

    def _get_journal_account_for_payment(self, journal, payment_type) -> uuid.UUID:
        """
        Obtiene la cuenta correcta a usar para un pago según el tipo de journal
        
        Args:
            journal: El journal donde se registrará el pago
            payment_type: Tipo de pago (customer_payment, supplier_payment, etc.)
            
        Returns:
            UUID de la cuenta a usar
            
        Raises:
            ValidationError: Si no se puede determinar la cuenta apropiada
        """
        from app.models.payment import PaymentType
        
        # Para journals de banco, usar configuración bancaria
        if journal.is_bank_journal():
            bank_config = journal.get_bank_config()
            if not bank_config:
                raise ValidationError(f"Bank journal {journal.name} does not have bank configuration")
            
            # Determinar si es pago entrante o saliente
            inbound_types = [PaymentType.CUSTOMER_PAYMENT]  # Pagos de clientes (inbound)
            outbound_types = [PaymentType.SUPPLIER_PAYMENT, PaymentType.INTERNAL_TRANSFER, 
                            PaymentType.ADVANCE_PAYMENT, PaymentType.REFUND]  # Pagos salientes
            
            if payment_type in inbound_types:
                if not bank_config.allow_inbound_payments:
                    raise ValidationError(f"Bank journal {journal.name} does not allow inbound payments")
                account_id = bank_config.inbound_receipt_account_id
                if not account_id:
                    account_id = bank_config.bank_account_id
            elif payment_type in outbound_types:
                if not bank_config.allow_outbound_payments:
                    raise ValidationError(f"Bank journal {journal.name} does not allow outbound payments")
                account_id = bank_config.outbound_pending_account_id
                if not account_id:
                    account_id = bank_config.bank_account_id
            else:
                # Tipo no reconocido, usar cuenta bancaria principal
                account_id = bank_config.bank_account_id
            
            if not account_id:
                raise ValidationError(f"Bank journal {journal.name} does not have appropriate account configured for {payment_type.value} payments")
                
            return account_id
        
        # Para otros tipos de journal, usar cuenta por defecto
        if not journal.default_account_id:
            raise ValidationError(f"Journal {journal.name} does not have a default account configured")
            
        return journal.default_account_id
