"""
Invoice service for managing invoice operations following Odoo pattern.
Handles DRAFT → POSTED → CANCELLED workflow with automatic journal entry creation.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.models.third_party import ThirdParty
from app.models.payment_terms import PaymentTerms
from app.models.account import Account
from app.models.product import Product
from app.models.tax import Tax
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType, TransactionOrigin
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceLineCreate, InvoiceLineUpdate, InvoiceLineResponse,
    InvoiceCreateWithLines, InvoiceWithLines,
    InvoiceListResponse, InvoiceSummary
)
from app.schemas.journal_entry import JournalEntryCreate, JournalEntryLineCreate
from app.services.account_determination_service import AccountDeterminationService
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger
from app.utils.codes import generate_code

logger = get_logger(__name__)


class InvoiceService:
    """
    Servicio para gestión de facturas siguiendo patrón Odoo
    
    Flujo de estados:
    DRAFT (Borrador) - Completamente editable
        ↓ [Contabilizar]
    POSTED (Contabilizada) - Genera JournalEntry(POSTED), no editable
        ↓ [Cancelar]
    CANCELLED (Cancelada) - Reversión del asiento, estado final
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.account_determination = AccountDeterminationService(db)
    
    def create_invoice(self, invoice_data: InvoiceCreate, created_by_id: uuid.UUID) -> InvoiceResponse:
        """
        Crear una nueva factura en estado DRAFT siguiendo patrón Odoo
        """
        try:
            # Validar que el tercero existe
            third_party = self.db.query(ThirdParty).filter(
                ThirdParty.id == invoice_data.third_party_id
            ).first()
            if not third_party:
                raise NotFoundError(f"ThirdParty with id {invoice_data.third_party_id} not found")

            # Validar términos de pago si se proporcionan
            if invoice_data.payment_terms_id:
                payment_terms = self.db.query(PaymentTerms).filter(
                    PaymentTerms.id == invoice_data.payment_terms_id
                ).first()
                if not payment_terms:
                    raise NotFoundError(f"PaymentTerms with id {invoice_data.payment_terms_id} not found")            # Generar número de factura
            invoice_number = invoice_data.invoice_number or self._generate_invoice_number(invoice_data.invoice_type)

            # Crear factura
            new_invoice = Invoice(
                number=invoice_number,
                invoice_type=invoice_data.invoice_type,
                status=InvoiceStatus.DRAFT,  # Siempre inicia en DRAFT
                third_party_id=invoice_data.third_party_id,
                invoice_date=invoice_data.invoice_date,
                due_date=invoice_data.due_date,
                payment_terms_id=invoice_data.payment_terms_id,
                third_party_account_id=invoice_data.third_party_account_id,  # Override opcional
                currency_code=invoice_data.currency_code,
                exchange_rate=invoice_data.exchange_rate,
                description=invoice_data.description,
                notes=invoice_data.notes,
                created_by_id=created_by_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_invoice)
            self.db.flush()  # Para obtener el ID
            self.db.commit()

            logger.info(f"Invoice {invoice_number} created in DRAFT status")
            return InvoiceResponse.from_orm(new_invoice)

        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            self.db.rollback()
            raise

    def create_invoice_with_lines(self, invoice_data: InvoiceCreateWithLines, created_by_id: uuid.UUID) -> InvoiceWithLines:
        """
        Crear factura con líneas en una sola transacción
        """
        try:
            # Crear la factura principal
            invoice_create = InvoiceCreate(**invoice_data.dict(exclude={'lines'}))
            invoice = self.create_invoice(invoice_create, created_by_id)
            
            # Agregar líneas si existen
            lines = []
            if invoice_data.lines:
                for line_data in invoice_data.lines:
                    line = self.add_invoice_line(
                        invoice_id=invoice.id,
                        line_data=line_data,
                        created_by_id=created_by_id
                    )
                    lines.append(line)
            
            # Recalcular totales
            updated_invoice = self.calculate_invoice_totals(invoice.id)
            
            return InvoiceWithLines(
                **updated_invoice.dict(),
                lines=lines
            )

        except Exception as e:
            logger.error(f"Error creating invoice with lines: {str(e)}")
            self.db.rollback()
            raise

    def post_invoice(self, invoice_id: uuid.UUID, posted_by_id: uuid.UUID) -> InvoiceResponse:
        """
        Contabilizar factura: DRAFT → POSTED
        Genera asiento contable automáticamente y bloquea edición
        """
        try:
            # 1. Obtener y validar la factura
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            # Validar que se puede contabilizar
            if invoice.status != InvoiceStatus.DRAFT:
                raise BusinessRuleError(f"Invoice cannot be posted in current status: {invoice.status}")
            
            # 2. Recalcular totales antes de contabilizar
            self.calculate_invoice_totals(invoice_id)
            self.db.refresh(invoice)
            
            if not invoice.total_amount or invoice.total_amount <= 0:
                raise BusinessRuleError("Invoice must have a positive total amount")
            
            # 3. Validar completitud de la factura
            validation_errors = self._validate_invoice_for_posting(invoice)
            if validation_errors:
                raise BusinessRuleError(f"Validation errors: {'; '.join(validation_errors)}")
            
            # 4. Crear asiento contable automáticamente
            journal_entry = self._create_journal_entry_for_invoice(invoice, posted_by_id)
            
            # 5. Actualizar estado de la factura
            invoice.status = InvoiceStatus.POSTED
            invoice.posted_by_id = posted_by_id
            invoice.posted_at = datetime.utcnow()
            invoice.journal_entry_id = journal_entry.id
            invoice.updated_at = datetime.utcnow()
            
            self.db.commit()

            logger.info(f"Invoice {invoice.number} posted successfully with journal entry {journal_entry.number}")
            return InvoiceResponse.from_orm(invoice)

        except Exception as e:
            logger.error(f"Error posting invoice {invoice_id}: {str(e)}")
            self.db.rollback()
            raise

    def cancel_invoice(self, invoice_id: uuid.UUID, cancelled_by_id: uuid.UUID, reason: Optional[str] = None) -> InvoiceResponse:
        """
        Cancelar factura: POSTED → CANCELLED
        Crea asiento de reversión y marca la factura como cancelada
        """
        try:
            # 1. Obtener y validar la factura
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            # Validar que se puede cancelar
            if invoice.status != InvoiceStatus.POSTED:
                raise BusinessRuleError(f"Invoice cannot be cancelled in current status: {invoice.status}")
            
            # 2. Crear asiento de reversión si existe el asiento original
            reversal_entry = None
            if invoice.journal_entry_id:
                reversal_entry = self._create_reversal_journal_entry(invoice, cancelled_by_id, reason)
            
            # 3. Actualizar estado de la factura
            invoice.status = InvoiceStatus.CANCELLED
            invoice.cancelled_by_id = cancelled_by_id
            invoice.cancelled_at = datetime.utcnow()
            invoice.updated_at = datetime.utcnow()
            
            # Agregar nota sobre la cancelación
            if reason:
                invoice.notes = (invoice.notes or "") + f"\n[CANCELLED] {reason}"
            
            self.db.commit()

            reversal_msg = f" with reversal entry {reversal_entry.number}" if reversal_entry else ""
            logger.info(f"Invoice {invoice.number} cancelled{reversal_msg}")
            return InvoiceResponse.from_orm(invoice)

        except Exception as e:
            logger.error(f"Error cancelling invoice {invoice_id}: {str(e)}")
            self.db.rollback()
            raise

    def reset_to_draft(self, invoice_id: uuid.UUID, reset_by_id: uuid.UUID, reason: Optional[str] = None) -> InvoiceResponse:
        """
        Resetear factura a DRAFT desde POSTED (solo si no hay pagos aplicados)
        Elimina el asiento contable asociado
        """
        try:
            # 1. Obtener y validar la factura
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            # Validar que se puede resetear
            if invoice.status not in [InvoiceStatus.POSTED]:
                raise BusinessRuleError(f"Invoice cannot be reset from current status: {invoice.status}")
            
            # Validar que no hay pagos aplicados (implementar cuando exista el módulo de pagos)
            # TODO: Validar pagos cuando se implemente el módulo correspondiente
            
            # 2. Eliminar el asiento contable asociado
            if invoice.journal_entry_id:
                journal_entry = self.db.query(JournalEntry).filter(
                    JournalEntry.id == invoice.journal_entry_id
                ).first()
                if journal_entry and journal_entry.status == JournalEntryStatus.POSTED:
                    # Eliminar líneas del asiento
                    self.db.query(JournalEntryLine).filter(
                        JournalEntryLine.journal_entry_id == journal_entry.id
                    ).delete()
                    
                    # Eliminar el asiento
                    self.db.delete(journal_entry)
            
            # 3. Resetear campos de contabilización
            invoice.status = InvoiceStatus.DRAFT
            invoice.posted_by_id = None
            invoice.posted_at = None
            invoice.journal_entry_id = None
            invoice.updated_at = datetime.utcnow()
            
            # Log de auditoría
            if reason:
                invoice.notes = (invoice.notes or "") + f"\n[RESET TO DRAFT] {reason}"
            
            self.db.commit()

            logger.info(f"Invoice {invoice.number} reset to DRAFT")
            return InvoiceResponse.from_orm(invoice)

        except Exception as e:
            logger.error(f"Error resetting invoice {invoice_id} to draft: {str(e)}")
            self.db.rollback()
            raise

    def add_invoice_line(
        self, 
        invoice_id: uuid.UUID, 
        line_data: InvoiceLineCreate, 
        created_by_id: uuid.UUID
    ) -> InvoiceLineResponse:
        """
        Agregar línea a factura (solo en estado DRAFT)
        """
        try:
            # Validar que la factura existe y está en DRAFT
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            if invoice.status != InvoiceStatus.DRAFT:
                raise BusinessRuleError("Lines can only be added to invoices in DRAFT status")
            
            # Validar producto si se proporciona
            product = None
            if hasattr(line_data, 'product_id') and line_data.product_id:
                product = self.db.query(Product).filter(Product.id == line_data.product_id).first()
                if not product:
                    raise NotFoundError(f"Product with id {line_data.product_id} not found")
            
            # Determinar siguiente secuencia
            max_sequence = self.db.query(func.max(InvoiceLine.sequence)).filter(
                InvoiceLine.invoice_id == invoice_id
            ).scalar() or 0
            
            # Crear línea
            new_line = InvoiceLine(
                invoice_id=invoice_id,
                sequence=max_sequence + 1,
                product_id=getattr(line_data, 'product_id', None),
                description=line_data.description or (product.name if product else ""),
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percentage=getattr(line_data, 'discount_percentage', Decimal('0')),
                account_id=getattr(line_data, 'account_id', None),
                created_by_id=created_by_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_line)
            self.db.commit()

            logger.info(f"Line added to invoice {invoice.number}")
            return InvoiceLineResponse.from_orm(new_line)

        except Exception as e:
            logger.error(f"Error adding line to invoice {invoice_id}: {str(e)}")
            self.db.rollback()
            raise

    def get_invoice(self, invoice_id: uuid.UUID) -> InvoiceResponse:
        """
        Obtener factura por ID
        """
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundError(f"Invoice with id {invoice_id} not found")
        
        return InvoiceResponse.from_orm(invoice)

    def get_invoices(
        self,
        skip: int = 0,
        limit: int = 100,
        third_party_id: Optional[uuid.UUID] = None,
        status: Optional[InvoiceStatus] = None,
        invoice_type: Optional[InvoiceType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> InvoiceListResponse:
        """
        Obtener lista de facturas con filtros
        """
        query = self.db.query(Invoice)
        
        # Aplicar filtros
        if third_party_id:
            query = query.filter(Invoice.third_party_id == third_party_id)
        if status:
            query = query.filter(Invoice.status == status)
        if invoice_type:
            query = query.filter(Invoice.invoice_type == invoice_type)
        if date_from:
            query = query.filter(Invoice.invoice_date >= date_from)
        if date_to:
            query = query.filter(Invoice.invoice_date <= date_to)
          # Obtener total y datos paginados
        total = query.count()
        invoices = query.order_by(desc(Invoice.invoice_date)).offset(skip).limit(limit).all()
        
        # Convertir a respuestas apropiadas
        invoice_responses = [InvoiceResponse.from_orm(inv) for inv in invoices]
        
        return InvoiceListResponse(
            items=invoice_responses,
            total=total,
            page=skip // limit + 1,
            size=limit,
            total_pages=(total + limit - 1) // limit
        )

    def calculate_invoice_totals(self, invoice_id: uuid.UUID) -> InvoiceResponse:
        """
        Recalcular totales de la factura basado en sus líneas
        """
        try:
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            lines = self.db.query(InvoiceLine).filter(InvoiceLine.invoice_id == invoice_id).all()
            
            subtotal = Decimal('0')
            total_discount = Decimal('0')
            tax_amount = Decimal('0')
            
            for line in lines:
                # Calcular subtotal de línea
                line_subtotal = line.quantity * line.unit_price
                subtotal += line_subtotal
                
                # Calcular descuento usando discount_percentage (field correcto)
                if line.discount_percentage:
                    line_discount = line_subtotal * (line.discount_percentage / 100)
                    total_discount += line_discount
                
                # Usar tax_amount directo de la línea (implementación básica por ahora)
                # TODO: Implementar cálculo de impuestos automático cuando el módulo esté completo
                if hasattr(line, 'tax_amount') and line.tax_amount:
                    tax_amount += line.tax_amount
            
            # Calcular totales finales
            subtotal_after_discount = subtotal - total_discount
            
            # Actualizar totales en la factura usando nombres correctos del modelo
            invoice.subtotal = subtotal_after_discount
            invoice.discount_amount = total_discount
            invoice.tax_amount = tax_amount
            invoice.total_amount = subtotal_after_discount + tax_amount
            invoice.outstanding_amount = invoice.total_amount - invoice.paid_amount
            invoice.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return InvoiceResponse.from_orm(invoice)

        except Exception as e:
            logger.error(f"Error calculating invoice totals for {invoice_id}: {str(e)}")
            self.db.rollback()
            raise

    def _generate_invoice_number(self, invoice_type: InvoiceType) -> str:
        """
        Generar número de factura secuencial
        """
        prefix = "INV" if invoice_type == InvoiceType.CUSTOMER_INVOICE else "BILL"
        return generate_code(self.db, Invoice, "number", prefix)

    def _validate_invoice_for_posting(self, invoice: Invoice) -> List[str]:
        """
        Validar que la factura esté completa para contabilizar
        """
        errors = []
        
        # Validar que tiene líneas
        lines_count = self.db.query(InvoiceLine).filter(
            InvoiceLine.invoice_id == invoice.id
        ).count()
        if lines_count == 0:
            errors.append("Invoice must have at least one line")
        
        # Validar que todas las líneas tienen cuentas contables determinables
        lines = self.db.query(InvoiceLine).filter(InvoiceLine.invoice_id == invoice.id).all()
        for line in lines:
            try:
                self.account_determination.determine_line_account(line)
            except Exception as e:
                errors.append(f"Line {line.sequence}: Cannot determine account - {str(e)}")
        
        # Validar cuenta del tercero
        try:
            self.account_determination.determine_third_party_account(invoice)
        except Exception as e:
            errors.append(f"Cannot determine third party account - {str(e)}")
        
        return errors

    def _create_journal_entry_for_invoice(self, invoice: Invoice, created_by_id: uuid.UUID) -> JournalEntry:
        """
        Crear asiento contable para la factura siguiendo el patrón Odoo
        """
        # Determinar tipo de asiento según el origen
        entry_type = JournalEntryType.AUTOMATIC
          # Determinar origen de transacción
        if invoice.invoice_type == InvoiceType.CUSTOMER_INVOICE:
            transaction_origin = TransactionOrigin.SALE
        else:
            transaction_origin = TransactionOrigin.PURCHASE
        
        # Crear asiento principal
        journal_entry = JournalEntry(
            number=self._generate_journal_entry_number(),
            entry_type=entry_type,
            status=JournalEntryStatus.POSTED,
            transaction_date=invoice.invoice_date,
            description=f"Invoice {invoice.number} - {invoice.third_party.name if invoice.third_party else 'Unknown'}",
            reference_number=invoice.number,
            transaction_origin=transaction_origin,
            source_document_id=invoice.id,
            created_by_id=created_by_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(journal_entry)
        self.db.flush()
        
        # Crear líneas del asiento
        self._create_journal_entry_lines(journal_entry, invoice)
        
        return journal_entry

    def _create_journal_entry_lines(self, journal_entry: JournalEntry, invoice: Invoice):
        """
        Crear líneas del asiento contable para la factura siguiendo lógica contable estándar
        """
        lines = self.db.query(InvoiceLine).filter(InvoiceLine.invoice_id == invoice.id).all()
        
        # 1. Líneas por cada línea de factura (ingresos/gastos)
        for line in lines:
            try:
                account = self.account_determination.determine_line_account(line)
                line_amount = line.quantity * line.unit_price
                  # Aplicar descuentos
                if line.discount_percentage:
                    line_amount *= (1 - line.discount_percentage / 100)
                
                if invoice.invoice_type == InvoiceType.CUSTOMER_INVOICE:
                    # Factura de venta: acreditar ingresos
                    debit = Decimal('0')
                    credit = line_amount
                else:
                    # Factura de compra: debitar gastos/costos
                    debit = line_amount
                    credit = Decimal('0')
                
                journal_line = JournalEntryLine(
                    journal_entry_id=journal_entry.id,
                    account_id=account.id,
                    description=line.description[:255],  # Limitar longitud
                    debit_amount=debit,
                    credit_amount=credit,
                    cost_center_id=getattr(line, 'cost_center_id', None)
                )
                self.db.add(journal_line)
                
            except Exception as e:
                logger.warning(f"Error creating journal line for invoice line {line.id}: {str(e)}")
                # Continuar con las demás líneas
        
        # 2. Línea de impuestos (simplificada por ahora)
        if invoice.tax_amount and invoice.tax_amount > 0:
            self._create_tax_journal_line(journal_entry, invoice)
          # 3. Línea del tercero (cuenta por cobrar/pagar)
        self._create_third_party_journal_line(journal_entry, invoice)

    def _create_tax_journal_line(self, journal_entry: JournalEntry, invoice: Invoice):
        """
        Crear línea de asiento para impuestos (implementación básica)
        """
        try:
            # Buscar cuenta de impuestos por defecto
            if invoice.invoice_type == InvoiceType.CUSTOMER_INVOICE:
                # IVA por pagar
                tax_account = self.db.query(Account).filter(
                    Account.code.like('2408%'),
                    Account.is_active == True
                ).first()
            else:
                # IVA deducible
                tax_account = self.db.query(Account).filter(
                    Account.code.like('1365%'),
                    Account.is_active == True                ).first()
            
            if tax_account:
                if invoice.invoice_type == InvoiceType.CUSTOMER_INVOICE:
                    # IVA por pagar: acreditar
                    debit = Decimal('0')
                    credit = invoice.tax_amount
                else:
                    # IVA deducible: debitar
                    debit = invoice.tax_amount
                    credit = Decimal('0')
                
                tax_line = JournalEntryLine(
                    journal_entry_id=journal_entry.id,
                    account_id=tax_account.id,
                    description=f"Tax - Invoice {invoice.number}",
                    debit_amount=debit,
                    credit_amount=credit
                )
                self.db.add(tax_line)
            else:
                logger.warning(f"No tax account found for invoice {invoice.number}")
                
        except Exception as e:
            logger.warning(f"Error creating tax journal line for invoice {invoice.id}: {str(e)}")

    def _create_third_party_journal_line(self, journal_entry: JournalEntry, invoice: Invoice):
        """
        Crear línea de asiento para el tercero (cuenta por cobrar/pagar)        """
        try:
            third_party_account = self.account_determination.determine_third_party_account(invoice)
            
            if invoice.invoice_type == InvoiceType.CUSTOMER_INVOICE:
                # Cuenta por cobrar: debitar
                debit = invoice.total_amount
                credit = Decimal('0')
            else:
                # Cuenta por pagar: acreditar
                debit = Decimal('0')
                credit = invoice.total_amount
            
            third_party_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                account_id=third_party_account.id,
                description=f"Invoice {invoice.number} - {invoice.third_party.name}",
                debit_amount=debit,
                credit_amount=credit,
                third_party_id=invoice.third_party_id
            )
            self.db.add(third_party_line)
            
        except Exception as e:
            logger.error(f"Error creating third party journal line for invoice {invoice.id}: {str(e)}")
            raise  # Este error es crítico, debe fallar la contabilización

    def _create_reversal_journal_entry(self, invoice: Invoice, created_by_id: uuid.UUID, reason: Optional[str] = None) -> JournalEntry:
        """
        Crear asiento de reversión para cancelación de factura
        """
        original_entry = self.db.query(JournalEntry).filter(
            JournalEntry.id == invoice.journal_entry_id
        ).first()
        
        if not original_entry:
            raise ValidationError("Original journal entry not found")
        
        # Crear asiento de reversión
        reversal_entry = JournalEntry(
            number=self._generate_journal_entry_number(),
            entry_type=JournalEntryType.REVERSAL,
            status=JournalEntryStatus.POSTED,
            transaction_date=datetime.utcnow().date(),
            description=f"Reversal of {original_entry.number} - {reason or 'Invoice cancellation'}",
            reference_number=f"REV-{original_entry.number}",
            transaction_origin=TransactionOrigin.ADJUSTMENT,
            source_document_id=invoice.id,
            created_by_id=created_by_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(reversal_entry)
        self.db.flush()
        
        # Crear líneas de reversión (invertir débitos y créditos)
        original_lines = self.db.query(JournalEntryLine).filter(
            JournalEntryLine.journal_entry_id == original_entry.id
        ).all()
        
        for orig_line in original_lines:
            reversal_line = JournalEntryLine(
                journal_entry_id=reversal_entry.id,
                account_id=orig_line.account_id,
                description=f"Reversal: {orig_line.description}",
                debit_amount=orig_line.credit_amount,  # Invertir
                credit_amount=orig_line.debit_amount,  # Invertir
                third_party_id=orig_line.third_party_id,
                cost_center_id=orig_line.cost_center_id
            )
            self.db.add(reversal_line)
        
        return reversal_entry

    def _generate_journal_entry_number(self) -> str:
        """
        Generar número secuencial para asientos contables
        """
        return generate_code(self.db, JournalEntry, "number", "JE")

    def get_invoice_with_lines(self, invoice_id: uuid.UUID) -> InvoiceWithLines:
        """
        Obtener factura con todas sus líneas
        """
        # Obtener la factura base
        invoice_response = self.get_invoice(invoice_id)
        
        # Obtener las líneas ordenadas por secuencia
        lines = self.db.query(InvoiceLine).filter(
            InvoiceLine.invoice_id == invoice_id
        ).order_by(InvoiceLine.sequence).all()
        
        lines_response = [InvoiceLineResponse.from_orm(line) for line in lines]
        
        # Crear la respuesta - InvoiceWithLines hereda de InvoiceResponse
        invoice_dict = invoice_response.dict()
        invoice_dict['lines'] = lines_response
        
        return InvoiceWithLines(**invoice_dict)

    def update_invoice(self, invoice_id: uuid.UUID, invoice_data: InvoiceUpdate) -> InvoiceResponse:
        """
        Actualizar factura (solo en estado DRAFT)
        """
        try:
            # Obtener y validar la factura
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            # Validar que se puede editar
            if invoice.status != InvoiceStatus.DRAFT:
                raise BusinessRuleError("Invoice can only be updated in DRAFT status")
            
            # Actualizar campos si se proporcionan
            if invoice_data.invoice_number is not None:
                invoice.number = invoice_data.invoice_number
            if invoice_data.invoice_date is not None:
                invoice.invoice_date = invoice_data.invoice_date
            if invoice_data.due_date is not None:
                invoice.due_date = invoice_data.due_date
            if invoice_data.description is not None:
                invoice.description = invoice_data.description
            if invoice_data.notes is not None:
                invoice.notes = invoice_data.notes
            if invoice_data.exchange_rate is not None:
                invoice.exchange_rate = invoice_data.exchange_rate
            
            invoice.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Invoice {invoice.number} updated")
            return InvoiceResponse.from_orm(invoice)

        except Exception as e:
            logger.error(f"Error updating invoice {invoice_id}: {str(e)}")
            self.db.rollback()
            raise
