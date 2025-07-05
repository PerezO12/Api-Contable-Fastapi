"""
Payment service for managing core payment operations.
Handles payment CRUD operations, allocations to invoices, and basic payment business logic.
This service focuses on core payment management - complex workflow orchestration is handled by PaymentFlowService.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc, and_, func

from app.models.payment import Payment, PaymentInvoice, PaymentStatus, PaymentType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.third_party import ThirdParty
from app.models.account import Account
from app.models.journal import Journal
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse, 
    PaymentListResponse, PaymentSummary
)
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger
from app.utils.codes import generate_code

logger = get_logger(__name__)


class PaymentService:
    """
    Core payment service for payment CRUD operations and basic business logic.
    
    Responsibilities:
    - Payment creation, update, deletion
    - Payment-invoice allocation management
    - Payment status transitions (CRUD level)
    - Payment queries and reporting
    - Payment validation (business rules)
    
    Does NOT handle:
    - Complex payment workflows (use PaymentFlowService)
    - Bank extract import/matching (use PaymentFlowService)
    - Journal entry creation (use PaymentFlowService)
    - Payment confirmation/posting workflows (use PaymentFlowService)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(self, payment_data: PaymentCreate, created_by_id: uuid.UUID) -> PaymentResponse:
        """Crear un nuevo pago"""
        try:
            # Validar que el diario existe y obtener la cuenta por defecto
            journal_result = await self.db.execute(
                select(Journal).options(selectinload(Journal.bank_config))
                .where(Journal.id == payment_data.journal_id)
            )
            journal = journal_result.scalar_one_or_none()
            if not journal:
                raise NotFoundError(f"Journal with id {payment_data.journal_id} not found")
            
            # Obtener la cuenta a usar según el tipo de journal
            account_id = await self._get_journal_account_for_payment(journal, payment_data.payment_type)

            # Validar que el cliente existe (opcional)
            if payment_data.customer_id:
                customer_result = await self.db.execute(
                    select(ThirdParty).where(ThirdParty.id == payment_data.customer_id)
                )
                customer = customer_result.scalar_one_or_none()
                if not customer:
                    raise NotFoundError(f"Customer with id {payment_data.customer_id} not found")

            # Validar que la cuenta existe
            account_result = await self.db.execute(
                select(Account).where(Account.id == account_id)
            )
            account = account_result.scalar_one_or_none()
            if not account:
                raise NotFoundError(f"Account with id {account_id} not found")

            # Generar número de pago
            payment_number = await self._generate_payment_number(payment_data.payment_type)

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
            await self.db.commit()

            logger.info(f"Payment created with ID: {payment.id}")
            return PaymentResponse.from_orm(payment)

        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            await self.db.rollback()
            raise

    async def get_payment(self, payment_id: uuid.UUID) -> PaymentResponse:
        """Obtener un pago por ID"""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundError(f"Payment with id {payment_id} not found")
        
        return PaymentResponse.from_orm(payment)

    async def update_payment(self, payment_id: uuid.UUID, payment_data: PaymentUpdate) -> PaymentResponse:
        """Actualizar un pago"""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
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
        await self.db.commit()

        logger.info(f"Payment updated: {payment_id}")
        return PaymentResponse.from_orm(payment)

    async def delete_payment(self, payment_id: uuid.UUID):
        """Eliminar un pago"""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundError(f"Payment with id {payment_id} not found")

        # Verificar que se puede eliminar
        if payment.status != PaymentStatus.DRAFT:
            raise BusinessRuleError("Cannot delete payment that is not in draft status")
        
        if payment.payment_invoices:
            raise BusinessRuleError("Cannot delete payment with allocations")

        await self.db.delete(payment)
        await self.db.commit()

        logger.info(f"Payment deleted: {payment_id}")

    async def get_payments(
        self, 
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[PaymentStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        size: int = 50
    ) -> PaymentListResponse:
        """Obtener lista de pagos con filtros"""
        # Build base query with filters
        conditions = []
        
        if customer_id:
            conditions.append(Payment.third_party_id == customer_id)
        
        if status:
            conditions.append(Payment.status == status)
            
        if date_from:
            conditions.append(Payment.payment_date >= date_from)
            
        if date_to:
            conditions.append(Payment.payment_date <= date_to)

        # Base select with conditions
        base_query = select(Payment)
        if conditions:
            base_query = base_query.where(and_(*conditions))

        # Count total
        count_query = select(func.count(Payment.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * size
        payments_query = base_query.order_by(desc(Payment.payment_date)).offset(offset).limit(size)
        
        payments_result = await self.db.execute(payments_query)
        payments = payments_result.scalars().all()

        return PaymentListResponse(
            data=[PaymentResponse.from_orm(p) for p in payments],
            total=total,
            page=page,
            per_page=size,
            pages=(total + size - 1) // size
        )

    async def confirm_payment(self, payment_id: uuid.UUID, confirmed_by_id: uuid.UUID) -> PaymentResponse:
        """
        Confirmar un pago (transición básica de estado)
        Para workflow completo de confirmación, usar PaymentFlowService.confirm_payment()
        """
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundError(f"Payment with id {payment_id} not found")

        if payment.status != PaymentStatus.PENDING:
            raise BusinessRuleError("Payment must be pending to confirm")

        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_by_id = confirmed_by_id
        payment.confirmed_at = datetime.utcnow()

        await self.db.commit()
        logger.info(f"Payment confirmed: {payment_id}")
        
        return PaymentResponse.from_orm(payment)

    async def _generate_payment_number(self, payment_type: PaymentType) -> str:
        """Generar número de pago"""
        
        prefix_map = {
            PaymentType.CUSTOMER_PAYMENT: "PAY",
            PaymentType.SUPPLIER_PAYMENT: "SUP", 
            PaymentType.INTERNAL_TRANSFER: "TRF",
            PaymentType.ADVANCE_PAYMENT: "ADV",
            PaymentType.REFUND: "REF"
        }
        
        prefix = prefix_map.get(payment_type, "PAY")
        # For now, use a simple sequential number - this should be replaced with proper async generation
        result = await self.db.execute(
            select(func.count(Payment.id)).where(Payment.number.like(f"{prefix}%"))
        )
        count = result.scalar() or 0
        return f"{prefix}{str(count + 1).zfill(6)}"



    async def get_payment_summary(self) -> PaymentSummary:
        """Obtener resumen de pagos"""
        try:
            # Totales por estado
            status_totals_result = await self.db.execute(
                select(
                    Payment.status,
                    func.count(Payment.id).label('count'),
                    func.coalesce(func.sum(Payment.amount), Decimal('0')).label('total_amount')
                ).group_by(Payment.status)
            )
            status_totals = status_totals_result.all()

            # Resumen general
            total_payments_result = await self.db.execute(select(func.count(Payment.id)))
            total_payments = total_payments_result.scalar() or 0
            
            total_amount_result = await self.db.execute(
                select(func.coalesce(func.sum(Payment.amount), Decimal('0')))
            )
            total_amount = total_amount_result.scalar() or Decimal('0')
            
            # Pagos pendientes
            pending_count_result = await self.db.execute(
                select(func.count(Payment.id)).where(Payment.status == PaymentStatus.PENDING)
            )
            pending_count = pending_count_result.scalar() or 0
            
            pending_amount_result = await self.db.execute(
                select(func.coalesce(func.sum(Payment.amount), Decimal('0')))
                .where(Payment.status == PaymentStatus.PENDING)
            )
            pending_amount = pending_amount_result.scalar() or Decimal('0')

            # Pagos confirmados hoy
            today = date.today()
            today_count_result = await self.db.execute(
                select(func.count(Payment.id)).where(Payment.payment_date == today)
            )
            today_count = today_count_result.scalar() or 0
            
            today_amount_result = await self.db.execute(
                select(func.coalesce(func.sum(Payment.amount), Decimal('0')))
                .where(Payment.payment_date == today)
            )
            today_amount = today_amount_result.scalar() or Decimal('0')

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

    async def _get_journal_account_for_payment(self, journal, payment_type) -> uuid.UUID:
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
