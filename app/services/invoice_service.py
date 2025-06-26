"""
Invoice service for managing invoice operations following Odoo pattern.
Handles DRAFT → POSTED → CANCELLED workflow with automatic journal entry creation.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, func

from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.models.third_party import ThirdParty
from app.models.payment_terms import PaymentTerms
from app.models.account import Account
from app.models.product import Product
from app.models.tax import Tax
from app.models.journal import Journal, JournalType
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType, TransactionOrigin
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceLineCreate, InvoiceLineUpdate, InvoiceLineResponse,
    InvoiceCreateWithLines, InvoiceWithLines,
    InvoiceListResponse, InvoiceSummary
)
from app.schemas.journal_entry import JournalEntryCreate, JournalEntryLineCreate
from app.services.account_determination_service import AccountDeterminationService
from app.services.payment_terms_processor import PaymentTermsProcessor
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
    CANCELLED (Cancelada) - Reversión del asiento, estado final    """
    
    def __init__(self, db: Session):
        self.db = db
        self.account_determination = AccountDeterminationService(db)
        self.payment_terms_processor = PaymentTermsProcessor(db)
    
    def _get_default_journal_for_invoice_type(self, invoice_type: InvoiceType) -> Optional[Journal]:
        """
        Obtiene el diario por defecto para un tipo de factura
        
        Args:
            invoice_type: Tipo de factura (CUSTOMER_INVOICE, SUPPLIER_INVOICE, etc.)
            
        Returns:
            Journal por defecto o None si no se encuentra
        """
        # Mapeo de tipos de factura a tipos de diario
        type_mapping = {
            InvoiceType.CUSTOMER_INVOICE: JournalType.SALE,
            InvoiceType.SUPPLIER_INVOICE: JournalType.PURCHASE,
            InvoiceType.CREDIT_NOTE: JournalType.SALE,  # Notas de crédito van al diario de ventas
            InvoiceType.DEBIT_NOTE: JournalType.SALE,   # Notas de débito van al diario de ventas
        }
        
        journal_type = type_mapping.get(invoice_type)
        if not journal_type:
            return None
        
        # Buscar el primer diario activo de este tipo
        return self.db.query(Journal).filter(
            Journal.type == journal_type,
            Journal.is_active == True
        ).first()
    
    def _determine_journal_for_invoice(self, invoice_data: InvoiceCreate) -> Optional[Journal]:
        """
        Determina qué diario usar para una factura
        
        Lógica:
        1. Si se especifica journal_id, usar ese diario
        2. Si no, usar el diario por defecto para el tipo de factura
        
        Args:
            invoice_data: Datos de la factura a crear
            
        Returns:
            Journal a usar o None si no se puede determinar
        """
        journal = None
        
        # Si se especifica journal_id, validar que existe y está activo
        if invoice_data.journal_id:
            journal = self.db.query(Journal).filter(
                Journal.id == invoice_data.journal_id,
                Journal.is_active == True
            ).first()
            
            if not journal:
                raise NotFoundError(f"Journal with id {invoice_data.journal_id} not found or inactive")
        else:
            # Selección automática basada en el tipo de factura
            journal = self._get_default_journal_for_invoice_type(invoice_data.invoice_type)
        
        return journal
    
    def _generate_invoice_number_with_journal(self, journal: Journal) -> str:
        """
        Genera el número de factura usando la secuencia del diario
        
        Args:
            journal: Diario a usar para la secuencia
            
        Returns:
            Número de factura generado (ej: VEN/2025/0001)
        """
        # Usar el método del diario para obtener el siguiente número
        invoice_number = journal.get_next_sequence_number()
        
        # Guardar los cambios en la secuencia del diario
        self.db.add(journal)
        self.db.flush()  # Para asegurar que se actualice la secuencia
        
        return invoice_number
    
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
                    raise NotFoundError(f"PaymentTerms with id {invoice_data.payment_terms_id} not found")            # Determinar diario a usar
            journal = self._determine_journal_for_invoice(invoice_data)
            
            # Generar número de factura usando el diario
            if invoice_data.invoice_number:
                # Si se especifica un número manual, validar que no existe
                existing = self.db.query(Invoice).filter(Invoice.number == invoice_data.invoice_number).first()
                if existing:
                    raise ValidationError(f"Invoice number {invoice_data.invoice_number} already exists")
                invoice_number = invoice_data.invoice_number
            elif journal:
                # Usar la secuencia del diario
                invoice_number = self._generate_invoice_number_with_journal(journal)
            else:
                # Fallback al método anterior
                invoice_number = self._generate_invoice_number(invoice_data.invoice_type)            # Crear factura
            new_invoice = Invoice(
                number=invoice_number,
                invoice_type=invoice_data.invoice_type,
                status=InvoiceStatus.DRAFT,  # Siempre inicia en DRAFT
                third_party_id=invoice_data.third_party_id,
                journal_id=journal.id if journal else None,  # Asignar diario
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
        Flujo similar a Odoo:
        1. Marca el journal entry original como CANCELLED (sin eliminarlo)
        2. Deshace conciliaciones si las hay
        3. Marca la factura como CANCELLED
        4. NO crea asientos de reversión adicionales
        """
        try:
            # 1. Obtener y validar la factura
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            # Validar que se puede cancelar
            if invoice.status != InvoiceStatus.POSTED:
                raise BusinessRuleError(f"Invoice cannot be cancelled in current status: {invoice.status}")
            
            # 2. Cancelar el journal entry original (siguiendo flujo Odoo)
            if invoice.journal_entry_id:
                original_entry = self.db.query(JournalEntry).filter(
                    JournalEntry.id == invoice.journal_entry_id
                ).first()
                
                if original_entry and original_entry.status == JournalEntryStatus.POSTED:
                    # Marcar el asiento original como cancelado (sin crear reversión)
                    original_entry.status = JournalEntryStatus.CANCELLED
                    original_entry.cancelled_by_id = cancelled_by_id
                    original_entry.cancelled_at = datetime.utcnow()
                    
                    # Actualizar notas del asiento
                    cancel_note = f"Cancelled due to invoice cancellation: {reason or 'No reason provided'}"
                    if original_entry.notes:
                        original_entry.notes += f"\n\n{cancel_note}"
                    else:
                        original_entry.notes = cancel_note
                    
                    # TODO: Aquí se podrían deshacer conciliaciones si existen
                    # self._undo_reconciliations(original_entry)
                    
                    logger.info(f"Journal entry {original_entry.number} marked as cancelled for invoice {invoice.number}")
              # 3. Actualizar estado de la factura
            invoice.status = InvoiceStatus.CANCELLED
            invoice.cancelled_by_id = cancelled_by_id
            invoice.cancelled_at = datetime.utcnow()
            invoice.updated_at = datetime.utcnow()
            
            # Agregar nota sobre la cancelación
            if reason:
                invoice.notes = (invoice.notes or "") + f"\n[CANCELLED] {reason}"
            
            self.db.commit()
            
            logger.info(f"Invoice {invoice.number} cancelled following Odoo pattern")
            return InvoiceResponse.from_orm(invoice)            
        except Exception as e:
            logger.error(f"Error cancelling invoice {invoice_id}: {str(e)}")
            self.db.rollback()
            raise

    def reset_to_draft(self, invoice_id: uuid.UUID, reset_by_id: uuid.UUID, reason: Optional[str] = None) -> InvoiceResponse:
        """
        Resetear factura a DRAFT desde POSTED o CANCELLED
        - POSTED → DRAFT: Elimina el asiento contable asociado
        - CANCELLED → DRAFT: Elimina el asiento contable asociado (mismo comportamiento)
        
        En ambos casos, el journal entry se elimina completamente para permitir 
        regeneración cuando la factura se contabilice nuevamente.
        """
        try:
            # 1. Obtener y validar la factura
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            # Validar que se puede resetear
            if invoice.status not in [InvoiceStatus.POSTED, InvoiceStatus.CANCELLED]:
                raise BusinessRuleError(f"Invoice cannot be reset from current status: {invoice.status}. Only POSTED and CANCELLED invoices can be reset to DRAFT")
            
            # Validar que no hay pagos aplicados (implementar cuando exista el módulo de pagos)
            # TODO: Validar pagos cuando se implemente el módulo correspondiente
              # 2. Guardar referencia al journal entry antes de modificar
            journal_entry_id = invoice.journal_entry_id
            journal_entry = None
            
            if journal_entry_id:
                journal_entry = self.db.query(JournalEntry).filter(
                    JournalEntry.id == journal_entry_id
                ).first()
            
            # 3. Resetear campos de contabilización y cancelación PRIMERO
            previous_status = invoice.status
            invoice.status = InvoiceStatus.DRAFT
            invoice.posted_by_id = None
            invoice.posted_at = None
            invoice.cancelled_by_id = None
            invoice.cancelled_at = None
            invoice.updated_at = datetime.utcnow()
              # 4. Limpiar la referencia al journal entry en la factura 
            # Tanto para POSTED como CANCELLED: eliminar la referencia porque se borra el journal entry
            invoice.journal_entry_id = None
            
            # 5. Hacer flush para persistir los cambios de la factura antes de manejar journal entries
            self.db.flush()
              # 6. Manejar asientos contables: SIEMPRE eliminar cuando se resetea a DRAFT
            if journal_entry:
                # Sin importar el estado anterior (POSTED o CANCELLED), 
                # al resetear a DRAFT se debe eliminar el journal entry
                
                # Eliminar líneas del journal entry primero
                self.db.query(JournalEntryLine).filter(
                    JournalEntryLine.journal_entry_id == journal_entry.id
                ).delete()
                
                # Luego eliminar el journal entry
                self.db.delete(journal_entry)
                
                logger.info(f"Deleted journal entry {journal_entry.number} for reset invoice {invoice.number} (was {previous_status})")
            # 7. Log de auditoría
            status_name = "CANCELLED" if previous_status == InvoiceStatus.CANCELLED else "POSTED"
            if reason:
                invoice.notes = (invoice.notes or "") + f"\n[RESET TO DRAFT FROM {status_name}] {reason}"
            else:
                invoice.notes = (invoice.notes or "") + f"\n[RESET TO DRAFT FROM {status_name}] Reset by user {reset_by_id}"
            
            self.db.commit()

            logger.info(f"Invoice {invoice.number} reset from {status_name} to DRAFT")
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
                updated_at=datetime.utcnow()            )
            
            self.db.add(new_line)
            self.db.flush()  # Para obtener el ID y cargar relaciones
            
            # Recargar la línea con la información del producto
            reloaded_line = self.db.query(InvoiceLine).options(
                joinedload(InvoiceLine.product)
            ).filter(InvoiceLine.id == new_line.id).first()
            
            if not reloaded_line:
                raise Exception("Failed to reload invoice line")
            
            self.db.commit()

            logger.info(f"Line added to invoice {invoice.number}")
            return self._create_line_response_with_product_info(reloaded_line)

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
        limit: int = 1000,
        third_party_id: Optional[uuid.UUID] = None,
        status: Optional[InvoiceStatus] = None,
        invoice_type: Optional[InvoiceType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        invoice_number: Optional[str] = None,
        third_party_name: Optional[str] = None,
        description: Optional[str] = None,
        reference: Optional[str] = None,
        amount_from: Optional[Decimal] = None,
        amount_to: Optional[Decimal] = None,
        currency_code: Optional[str] = None,
        created_by_id: Optional[uuid.UUID] = None,
        sort_by: Optional[str] = "invoice_date",
        sort_order: Optional[str] = "desc"
    ) -> InvoiceListResponse:
        """
        Obtener lista de facturas con filtros avanzados
        
        Args:
            skip: Número de registros a saltar para paginación
            limit: Límite de registros por página
            third_party_id: ID del tercero específico
            status: Estado específico de la factura
            invoice_type: Tipo específico de factura
            date_from: Fecha desde (inclusive)
            date_to: Fecha hasta (inclusive)
            invoice_number: Búsqueda por número de factura (parcial)
            third_party_name: Búsqueda por nombre del tercero (parcial)
            description: Búsqueda por descripción (parcial)
            reference: Búsqueda por referencia interna o externa (parcial)
            amount_from: Monto total mínimo (inclusive)
            amount_to: Monto total máximo (inclusive)
            currency_code: Código de moneda específico
            created_by_id: ID del usuario que creó la factura
            sort_by: Campo por el cual ordenar (invoice_date, number, total_amount, etc.)
            sort_order: Orden de clasificación (asc, desc)
        
        Returns:
            InvoiceListResponse con facturas filtradas y metadatos de paginación
        """
        from sqlalchemy import func
        
        # Construir query base con join para tercero (para búsqueda por nombre)
        query = self.db.query(Invoice).join(ThirdParty, Invoice.third_party_id == ThirdParty.id)
        
        # Aplicar filtros básicos
        if third_party_id:
            query = query.filter(Invoice.third_party_id == third_party_id)
            
        if status:
            query = query.filter(Invoice.status == status)
            
        if invoice_type:
            query = query.filter(Invoice.invoice_type == invoice_type)
            
        if currency_code:
            query = query.filter(Invoice.currency_code == currency_code)
            
        if created_by_id:
            query = query.filter(Invoice.created_by_id == created_by_id)
        
        # Filtros de fecha (más flexibles)
        if date_from:
            query = query.filter(Invoice.invoice_date >= date_from)
            
        if date_to:
            query = query.filter(Invoice.invoice_date <= date_to)
        
        # Filtros de búsqueda de texto (parcial, case-insensitive)
        if invoice_number:
            query = query.filter(Invoice.number.ilike(f"%{invoice_number}%"))
            
        if third_party_name:
            query = query.filter(ThirdParty.name.ilike(f"%{third_party_name}%"))
            
        if description:
            query = query.filter(Invoice.description.ilike(f"%{description}%"))
            
        if reference:
            # Buscar en referencia interna o externa
            query = query.filter(
                func.or_(
                    Invoice.internal_reference.ilike(f"%{reference}%"),
                    Invoice.external_reference.ilike(f"%{reference}%")
                )
            )
        
        # Filtros de monto
        if amount_from is not None:
            query = query.filter(Invoice.total_amount >= amount_from)
            
        if amount_to is not None:
            query = query.filter(Invoice.total_amount <= amount_to)
          # Aplicar ordenamiento
        valid_sort_fields = {
            "invoice_date": Invoice.invoice_date,
            "number": Invoice.number,
            "total_amount": Invoice.total_amount,
            "status": Invoice.status,
            "created_at": Invoice.created_at,
            "due_date": Invoice.due_date
        }
        
        sort_field = valid_sort_fields.get(sort_by or "invoice_date", Invoice.invoice_date)
        sort_direction = (sort_order or "desc").lower()
        
        if sort_direction == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
        
        # Obtener total y datos paginados
        total = query.count()
        invoices = query.offset(skip).limit(limit).all()
        
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
          # Generar número para el journal entry usando el diario de la factura
        if invoice.journal_id:
            # Usar el mismo diario que la factura
            journal = self.db.query(Journal).filter(Journal.id == invoice.journal_id).first()
            if journal:
                entry_number = self._generate_journal_entry_number_with_journal(journal)
            else:
                entry_number = self._generate_journal_entry_number()
        else:
            entry_number = self._generate_journal_entry_number()
          # Crear asiento principal
        journal_entry = JournalEntry(
            number=entry_number,
            entry_type=entry_type,
            status=JournalEntryStatus.POSTED,
            entry_date=datetime.combine(invoice.invoice_date, datetime.min.time()).replace(tzinfo=timezone.utc),
            description=f"Invoice {invoice.number} - {invoice.third_party.name if invoice.third_party else 'Unknown'}",
            reference=invoice.number,
            transaction_origin=transaction_origin,
            journal_id=invoice.journal_id,  # Usar el mismo diario que la factura
            created_by_id=created_by_id        )
        
        self.db.add(journal_entry)
        self.db.flush()
          # Crear líneas del asiento
        self._create_journal_entry_lines(journal_entry, invoice)
        
        # CRÍTICO: Calcular totales del journal entry después de crear las líneas
        journal_entry.calculate_totals()
        
        # CRÍTICO: Actualizar saldos de las cuentas ya que se creó con status POSTED
        for line in journal_entry.lines:
            if line.account:
                line.account.update_balance(line.debit_amount, line.credit_amount)
        
        return journal_entry

    def _create_journal_entry_lines(self, journal_entry: JournalEntry, invoice: Invoice):
        """
        Crear líneas del asiento contable para la factura siguiendo lógica contable estándar
        """
        lines = self.db.query(InvoiceLine).filter(InvoiceLine.invoice_id == invoice.id).all()
        line_counter = 1
        
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
                    cost_center_id=getattr(line, 'cost_center_id', None),
                    line_number=line_counter
                )
                self.db.add(journal_line)
                line_counter += 1
                
            except Exception as e:
                logger.warning(f"Error creating journal line for invoice line {line.id}: {str(e)}")
                # Continuar con las demás líneas
        
        # 2. Línea de impuestos (simplificada por ahora)
        if invoice.tax_amount and invoice.tax_amount > 0:
            self._create_tax_journal_line(journal_entry, invoice, line_counter)
            line_counter += 1        # 3. Líneas del tercero (cuenta por cobrar/pagar) usando payment terms
        third_party_account = self.account_determination.determine_third_party_account(invoice)
        due_lines, _ = self.payment_terms_processor.process_invoice_payment_terms(
            invoice, third_party_account, line_counter
        )
          # Agregar las líneas de vencimiento al asiento
        for due_line in due_lines:
            due_line.journal_entry_id = journal_entry.id
            self.db.add(due_line)

    def _create_tax_journal_line(self, journal_entry: JournalEntry, invoice: Invoice, line_number: int):
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
                    Account.is_active == True
                ).first()
            
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
                    credit_amount=credit,
                    line_number=line_number
                )
                self.db.add(tax_line)
            else:
                logger.warning(f"No tax account found for invoice {invoice.number}")
                
        except Exception as e:
            logger.warning(f"Error creating tax journal line for invoice {invoice.id}: {str(e)}")

    def _create_reversal_journal_entry(self, invoice: Invoice, created_by_id: uuid.UUID, reason: Optional[str] = None) -> JournalEntry:
        """
        Crear asiento de reversión para cancelación de factura
        
        DEPRECATED: Este método ya no se usa en el flujo principal de cancelación de facturas.
        El nuevo flujo sigue el patrón de Odoo: marca el journal entry original como CANCELLED
        en lugar de crear asientos de reversión.
        
        Se mantiene por compatibilidad pero puede ser removido en futuras versiones.
        """
        original_entry = self.db.query(JournalEntry).filter(
            JournalEntry.id == invoice.journal_entry_id
        ).first()
        
        if not original_entry:
            raise ValidationError("Original journal entry not found")        # Generar número para el asiento de reversión usando el mismo diario
        if invoice.journal_id:
            journal = self.db.query(Journal).filter(Journal.id == invoice.journal_id).first()
            if journal:
                entry_number = self._generate_journal_entry_number_with_journal(journal)
            else:
                entry_number = self._generate_journal_entry_number()
        else:
            entry_number = self._generate_journal_entry_number()
        
        # Crear asiento de reversión
        reversal_entry = JournalEntry(
            number=entry_number,
            entry_type=JournalEntryType.REVERSAL,
            status=JournalEntryStatus.POSTED,
            entry_date=datetime.now(timezone.utc),
            description=f"Reversal of {original_entry.number} - {reason or 'Invoice cancellation'}",
            reference=f"REV-{original_entry.number}",
            transaction_origin=TransactionOrigin.ADJUSTMENT,
            journal_id=invoice.journal_id,  # Usar el mismo diario
            created_by_id=created_by_id
        )
        
        self.db.add(reversal_entry)
        self.db.flush()
          # Crear líneas de reversión (invertir débitos y créditos)
        original_lines = self.db.query(JournalEntryLine).filter(
            JournalEntryLine.journal_entry_id == original_entry.id
        ).all()
        
        line_counter = 1
        for orig_line in original_lines:
            reversal_line = JournalEntryLine(
                journal_entry_id=reversal_entry.id,
                account_id=orig_line.account_id,
                description=f"Reversal: {orig_line.description}",
                debit_amount=orig_line.credit_amount,  # Invertir
                credit_amount=orig_line.debit_amount,  # Invertir
                third_party_id=orig_line.third_party_id,
                cost_center_id=orig_line.cost_center_id,
                line_number=line_counter            )
            self.db.add(reversal_line)
            line_counter += 1
          # CRÍTICO: Actualizar saldos de las cuentas ya que se creó con status POSTED
        self.db.flush()  # Asegurar que las líneas estén persistidas
        
        # CRÍTICO: Calcular totales del journal entry de reversión
        reversal_entry.calculate_totals()
        
        # Cargar las líneas con sus cuentas para actualizar saldos
        reversal_lines = self.db.query(JournalEntryLine).filter(
            JournalEntryLine.journal_entry_id == reversal_entry.id
        ).all()
        
        for line in reversal_lines:
            if line.account:
                line.account.update_balance(line.debit_amount, line.credit_amount)
        
        return reversal_entry
    
    def _generate_journal_entry_number(self) -> str:
        """
        Generar número secuencial para asientos contables (método legacy)
        """
        return generate_code(self.db, JournalEntry, "number", "JE")
    
    def _generate_journal_entry_number_with_journal(self, journal: Journal) -> str:
        """
        Genera el número de asiento contable usando la secuencia del diario con formato JE
        
        Para journal entries derivados de facturas, el formato será:
        PREFIJO/AÑO/JE/NÚMERO (ej: VEN/2025/JE/0001)
        
        Args:
            journal: Diario a usar para la secuencia
            
        Returns:
            Número de journal entry generado
        """
        from datetime import datetime
        year = datetime.now().year
        
        # Verificar si necesita resetear la secuencia (para el journal entry también)
        if (journal.reset_sequence_yearly and 
            journal.last_sequence_reset_year != year):
            journal.current_sequence_number = 0
            journal.last_sequence_reset_year = year
          # Incrementar número de secuencia 
        journal.current_sequence_number += 1
        
        # Formatear número con padding
        number_str = str(journal.current_sequence_number).zfill(journal.sequence_padding)
        
        # Construir secuencia para journal entry con formato específico
        if journal.include_year_in_sequence:
            return f"{journal.sequence_prefix}/{year}/JE/{number_str}"
        else:
            return f"{journal.sequence_prefix}/JE/{number_str}"
    
    def _create_line_response_with_product_info(self, line: InvoiceLine) -> InvoiceLineResponse:
        """
        Crear respuesta de línea de factura incluyendo información del producto
        """
        # Comenzar con la respuesta base
        line_data = {
            'id': line.id,
            'invoice_id': line.invoice_id,
            'sequence': line.sequence,
            'product_id': line.product_id,
            'description': line.description,
            'quantity': line.quantity,
            'unit_price': line.unit_price,
            'discount_percentage': line.discount_percentage,
            'account_id': line.account_id,
            'cost_center_id': line.cost_center_id,
            'tax_ids': [],  # TODO: Implementar gestión de impuestos
            'subtotal': line.subtotal,
            'discount_amount': line.discount_amount,
            'tax_amount': line.tax_amount,
            'total_amount': line.total_amount,
            'created_at': line.created_at,
            'updated_at': line.updated_at,
            'created_by_id': line.created_by_id,
            'updated_by_id': line.updated_by_id,
            'product_name': None,
            'product_code': None
        }
        
        # Agregar información del producto si existe
        if line.product_id and line.product:
            line_data['product_name'] = line.product.name
            line_data['product_code'] = line.product.code
            
        return InvoiceLineResponse(**line_data)
    
    def get_invoice_with_lines(self, invoice_id: uuid.UUID) -> InvoiceWithLines:
        """
        Obtener factura con todas sus líneas
        """
        # Obtener la factura base
        invoice_response = self.get_invoice(invoice_id)
        
        # Obtener las líneas ordenadas por secuencia con información del producto
        lines = self.db.query(InvoiceLine).options(
            joinedload(InvoiceLine.product)
        ).filter(
            InvoiceLine.invoice_id == invoice_id
        ).order_by(InvoiceLine.sequence).all()
        
        lines_response = [self._create_line_response_with_product_info(line) for line in lines]
        
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

    def get_payment_schedule_preview(
        self, 
        invoice_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Obtiene una vista previa de cómo se dividirán los pagos de una factura
        según sus condiciones de pago
        """
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundError(f"Invoice with id {invoice_id} not found")
        
        if not invoice.payment_terms_id:
            # Sin condiciones de pago, un solo vencimiento en la fecha de la factura
            return [{
                'sequence': 1,
                'amount': float(invoice.total_amount or 0),
                'percentage': 100.0,
                'due_date': invoice.due_date or invoice.invoice_date,
                'description': f'Full payment - Invoice {invoice.number}'            }]
        
        return self.payment_terms_processor.get_payment_schedule_preview(
            invoice.total_amount or Decimal('0'),
            invoice.payment_terms_id,
            invoice.invoice_date
        )

    def validate_payment_terms(self, payment_terms_id: uuid.UUID) -> Tuple[bool, List[str]]:
        """
        Valida las condiciones de pago para uso en facturas
        """
        return self.payment_terms_processor.validate_payment_terms_for_invoice(payment_terms_id)

    # ================================
    # BULK OPERATIONS
    # ================================

    def bulk_post_invoices(
        self, 
        invoice_ids: List[uuid.UUID], 
        posted_by_id: uuid.UUID,
        posting_date: Optional[date] = None,
        notes: Optional[str] = None,
        force_post: bool = False,
        stop_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Contabilizar múltiples facturas en lote: DRAFT → POSTED
        
        Características:
        - Validación previa de estados
        - Procesamiento por lotes para performance
        - Control de errores individual
        - Rollback opcional en caso de error
        """
        import time
        start_time = time.time()
        
        total_requested = len(invoice_ids)
        successful_ids = []
        failed_items = []
        skipped_items = []
        
        try:
            # 1. Validación masiva previa
            invoices = self.db.query(Invoice).filter(
                Invoice.id.in_(invoice_ids)
            ).all()
            
            invoices_by_id = {inv.id: inv for inv in invoices}
            
            # Identificar IDs no encontrados
            found_ids = set(invoices_by_id.keys())
            not_found_ids = set(invoice_ids) - found_ids
            
            for invoice_id in not_found_ids:
                failed_items.append({
                    "id": str(invoice_id),
                    "error": "Invoice not found"
                })
            
            # 2. Validar estados
            valid_invoices = []
            for invoice in invoices:
                if invoice.status != InvoiceStatus.DRAFT:
                    skipped_items.append({
                        "id": str(invoice.id),
                        "reason": f"Invoice status is {invoice.status}, expected DRAFT",
                        "current_status": invoice.status
                    })
                elif not invoice.total_amount or invoice.total_amount <= 0:
                    skipped_items.append({
                        "id": str(invoice.id),
                        "reason": "Invoice total must be greater than 0",
                        "total_amount": float(invoice.total_amount or 0)
                    })
                else:
                    valid_invoices.append(invoice)
            
            # 3. Procesar facturas válidas
            for invoice in valid_invoices:
                try:
                    # Usar el método individual existente
                    self.post_invoice(invoice.id, posted_by_id)
                    successful_ids.append(invoice.id)
                    
                    # Agregar notas adicionales si se proporcionan
                    if notes:
                        invoice.notes = (invoice.notes or "") + f"\n[BULK POST] {notes}"
                        
                except Exception as e:
                    error_msg = str(e)
                    failed_items.append({
                        "id": str(invoice.id),
                        "error": error_msg,
                        "invoice_number": invoice.number
                    })
                    
                    if stop_on_error:
                        logger.error(f"Bulk post stopped at invoice {invoice.id}: {error_msg}")
                        break
                    else:
                        logger.warning(f"Failed to post invoice {invoice.id}: {error_msg}")
                        continue
            
            # 4. Commit si hay éxitos
            if successful_ids:
                self.db.commit()
                logger.info(f"Bulk post completed: {len(successful_ids)} successful, {len(failed_items)} failed, {len(skipped_items)} skipped")
            
            execution_time = time.time() - start_time
            
            return {
                "total_requested": total_requested,
                "successful": len(successful_ids),
                "failed": len(failed_items),
                "skipped": len(skipped_items),
                "successful_ids": successful_ids,                
                "failed_items": failed_items,
                "skipped_items": skipped_items,
                "execution_time_seconds": round(execution_time, 3)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk post operation failed: {str(e)}")
            raise

    def bulk_cancel_invoices(
        self, 
        invoice_ids: List[uuid.UUID], 
        cancelled_by_id: uuid.UUID,
        reason: Optional[str] = None,
        stop_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Cancelar múltiples facturas en lote: POSTED → CANCELLED
        """
        import time
        start_time = time.time()
        
        total_requested = len(invoice_ids)
        successful_ids = []
        failed_items = []
        skipped_items = []
        
        try:
            # 1. Validación masiva previa
            invoices = self.db.query(Invoice).filter(
                Invoice.id.in_(invoice_ids)
            ).all()
            
            invoices_by_id = {inv.id: inv for inv in invoices}
            
            # Identificar IDs no encontrados
            found_ids = set(invoices_by_id.keys())
            not_found_ids = set(invoice_ids) - found_ids
            
            for invoice_id in not_found_ids:
                failed_items.append({
                    "id": str(invoice_id),
                    "error": "Invoice not found"
                })
            
            # 2. Validar estados
            valid_invoices = []
            for invoice in invoices:
                if invoice.status != InvoiceStatus.POSTED:
                    skipped_items.append({
                        "id": str(invoice.id),
                        "reason": f"Invoice status is {invoice.status}, expected POSTED",
                        "current_status": invoice.status
                    })
                elif invoice.paid_amount > 0:
                    skipped_items.append({
                        "id": str(invoice.id),
                        "reason": "Cannot cancel invoice with payments",
                        "paid_amount": float(invoice.paid_amount)
                    })
                else:
                    valid_invoices.append(invoice)
            
            # 3. Procesar facturas válidas
            for invoice in valid_invoices:
                try:
                    # Usar el método individual existente
                    self.cancel_invoice(invoice.id, cancelled_by_id, reason)
                    successful_ids.append(invoice.id)
                        
                except Exception as e:
                    error_msg = str(e)
                    failed_items.append({
                        "id": str(invoice.id),
                        "error": error_msg,
                        "invoice_number": invoice.number
                    })
                    
                    if stop_on_error:
                        logger.error(f"Bulk cancel stopped at invoice {invoice.id}: {error_msg}")
                        break
                    else:
                        logger.warning(f"Failed to cancel invoice {invoice.id}: {error_msg}")
                        continue
              # 4. Commit si hay éxitos
            if successful_ids:
                self.db.commit()
                logger.info(f"Bulk cancel completed: {len(successful_ids)} successful, {len(failed_items)} failed, {len(skipped_items)} skipped")
            
            execution_time = time.time() - start_time
            
            return {
                "total_requested": total_requested,
                "successful": len(successful_ids),
                "failed": len(failed_items),
                "skipped": len(skipped_items),
                "successful_ids": successful_ids,
                "failed_items": failed_items,
                "skipped_items": skipped_items,
                "execution_time_seconds": round(execution_time, 3)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk cancel operation failed: {str(e)}")
            raise

    def bulk_reset_to_draft_invoices(
        self, 
        invoice_ids: List[uuid.UUID], 
        reset_by_id: uuid.UUID,
        reason: Optional[str] = None,
        force_reset: bool = False,
        stop_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Restablecer múltiples facturas a borrador en lote: POSTED/CANCELLED → DRAFT
        """
        import time
        start_time = time.time()
        
        total_requested = len(invoice_ids)
        successful_ids = []
        failed_items = []
        skipped_items = []
        
        try:
            # 1. Validación masiva previa
            invoices = self.db.query(Invoice).filter(
                Invoice.id.in_(invoice_ids)
            ).all()
            
            invoices_by_id = {inv.id: inv for inv in invoices}
            
            # Identificar IDs no encontrados
            found_ids = set(invoices_by_id.keys())
            not_found_ids = set(invoice_ids) - found_ids
            
            for invoice_id in not_found_ids:
                failed_items.append({
                    "id": str(invoice_id),
                    "error": "Invoice not found"
                })
            
            # 2. Validar estados
            valid_invoices = []
            for invoice in invoices:
                if invoice.status not in [InvoiceStatus.POSTED, InvoiceStatus.CANCELLED]:
                    skipped_items.append({
                        "id": str(invoice.id),
                        "reason": f"Invoice status is {invoice.status}, expected POSTED or CANCELLED",
                        "current_status": invoice.status
                    })
                elif invoice.paid_amount > 0 and not force_reset:
                    skipped_items.append({
                        "id": str(invoice.id),
                        "reason": "Cannot reset invoice with payments (use force_reset=true to override)",
                        "paid_amount": float(invoice.paid_amount)
                    })
                else:
                    valid_invoices.append(invoice)
            
            # 3. Procesar facturas válidas
            for invoice in valid_invoices:
                try:
                    # Usar el método individual existente
                    self.reset_to_draft(invoice.id, reset_by_id, reason)
                    successful_ids.append(invoice.id)
                        
                except Exception as e:
                    error_msg = str(e)
                    failed_items.append({
                        "id": str(invoice.id),
                        "error": error_msg,
                        "invoice_number": invoice.number
                    })
                    
                    if stop_on_error:
                        logger.error(f"Bulk reset stopped at invoice {invoice.id}: {error_msg}")
                        break
                    else:
                        logger.warning(f"Failed to reset invoice {invoice.id}: {error_msg}")
                        continue
            
            # 4. Commit si hay éxitos
            if successful_ids:
                self.db.commit()
                logger.info(f"Bulk reset completed: {len(successful_ids)} successful, {len(failed_items)} failed, {len(skipped_items)} skipped")
            
            execution_time = time.time() - start_time
            
            return {
                "total_requested": total_requested,
                "successful": len(successful_ids),
                "failed": len(failed_items),
                "skipped": len(skipped_items),
                "successful_ids": successful_ids,
                "failed_items": failed_items,
                "skipped_items": skipped_items,
                "execution_time_seconds": round(execution_time, 3)
            }            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk reset operation failed: {str(e)}")
            raise

    def bulk_delete_invoices(
        self, 
        invoice_ids: List[uuid.UUID], 
        deleted_by_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Eliminar múltiples facturas en lote (solo en DRAFT)
        """
        import time
        start_time = time.time()
        
        total_requested = len(invoice_ids)
        successful_ids = []
        failed_items = []
        skipped_items = []
        
        try:
            # Importar InvoiceLine
            from app.models.invoice import InvoiceLine
            
            # 1. Validación masiva previa
            invoices = self.db.query(Invoice).filter(
                Invoice.id.in_(invoice_ids)
            ).all()
            
            invoices_by_id = {inv.id: inv for inv in invoices}
            
            # Identificar IDs no encontrados
            found_ids = set(invoices_by_id.keys())
            not_found_ids = set(invoice_ids) - found_ids
            
            for invoice_id in not_found_ids:
                failed_items.append({
                    "id": str(invoice_id),
                    "error": "Invoice not found"
                })
            
            # 2. Validar estados - solo DRAFT puede eliminarse
            valid_invoices = []
            for invoice in invoices:
                if invoice.status != InvoiceStatus.DRAFT:
                    skipped_items.append({
                        "id": str(invoice.id),
                        "reason": f"Cannot delete invoice in status {invoice.status}, only DRAFT allowed",
                        "current_status": invoice.status
                    })
                elif invoice.journal_entry_id:
                    skipped_items.append({
                        "id": str(invoice.id),
                        "reason": "Cannot delete invoice with journal entry",
                        "journal_entry_id": str(invoice.journal_entry_id)
                    })
                else:
                    valid_invoices.append(invoice)
            
            # 3. Procesar facturas válidas
            for invoice in valid_invoices:
                try:
                    # Verificar y desactivar referencias de NFe antes de eliminar
                    from app.models.nfe import NFe, NFeStatus
                    
                    # Buscar NFe que referencian esta factura
                    nfes = self.db.query(NFe).filter(NFe.invoice_id == invoice.id).all()
                    
                    # Desactivar la referencia a la factura en las NFe
                    for nfe in nfes:
                        nfe.invoice_id = None
                        nfe.status = NFeStatus.UNLINKED  # Marcar como desvinculada
                        logger.info(f"Unlinked NFe {nfe.chave_nfe} from invoice {invoice.id}")
                    
                    # Eliminar líneas de factura primero
                    self.db.query(InvoiceLine).filter(
                        InvoiceLine.invoice_id == invoice.id
                    ).delete(synchronize_session=False)
                    
                    # Eliminar factura
                    self.db.delete(invoice)
                    successful_ids.append(invoice.id)
                    
                    logger.info(f"Deleted invoice {invoice.id} ({invoice.number}) and unlinked {len(nfes)} NFe references - Reason: {reason or 'Not specified'}")
                        
                except Exception as e:
                    error_msg = str(e)
                    failed_items.append({
                        "id": str(invoice.id),
                        "error": error_msg,
                        "invoice_number": invoice.number
                    })
                    logger.warning(f"Failed to delete invoice {invoice.id}: {error_msg}")
            
            # 4. Commit si hay éxitos
            if successful_ids:
                self.db.commit()
                logger.info(f"Bulk delete completed: {len(successful_ids)} successful, {len(failed_items)} failed, {len(skipped_items)} skipped")
            
            execution_time = time.time() - start_time
            
            return {
                "total_requested": total_requested,
                "successful": len(successful_ids),
                "failed": len(failed_items),
                "skipped": len(skipped_items),
                "successful_ids": successful_ids,
                "failed_items": failed_items,
                "skipped_items": skipped_items,
                "execution_time_seconds": round(execution_time, 3)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk delete operation failed: {str(e)}")
            raise

    def validate_bulk_operation(
        self, 
        invoice_ids: List[uuid.UUID], 
        operation: str
    ) -> Dict[str, Any]:
        """
        Validar si las facturas pueden ser procesadas en una operación bulk específica
        Sin hacer cambios en la base de datos.
        """
        valid_statuses = {
            "post": [InvoiceStatus.DRAFT],
            "cancel": [InvoiceStatus.POSTED],
            "reset": [InvoiceStatus.POSTED],
            "delete": [InvoiceStatus.DRAFT]
        }
        
        if operation not in valid_statuses:
            raise ValueError(f"Unknown operation: {operation}")
        
        # Obtener facturas
        invoices = self.db.query(Invoice).filter(
            Invoice.id.in_(invoice_ids)
        ).all()
        
        invoices_by_id = {inv.id: inv for inv in invoices}
        
        # Clasificar resultados
        valid_invoices = []
        invalid_invoices = []
        not_found_ids = []
        
        # IDs no encontrados
        found_ids = set(invoices_by_id.keys())
        not_found_ids = list(set(invoice_ids) - found_ids)
        
        # Validar estados
        expected_statuses = valid_statuses[operation]
        for invoice in invoices:
            is_valid = True
            reasons = []
            
            # Validar estado
            if invoice.status not in expected_statuses:
                is_valid = False
                reasons.append(f"Status is {invoice.status}, expected {' or '.join([s.value for s in expected_statuses])}")
            
            # Validaciones específicas por operación
            if operation == "post":
                if not invoice.total_amount or invoice.total_amount <= 0:
                    is_valid = False
                    reasons.append("Total amount must be greater than 0")
            elif operation == "cancel":
                if invoice.paid_amount > 0:
                    is_valid = False
                    reasons.append("Cannot cancel invoice with payments")
            elif operation == "reset":
                if invoice.paid_amount > 0:
                    is_valid = False
                    reasons.append("Cannot reset invoice with payments (use force_reset to override)")
            elif operation == "delete":
                if invoice.journal_entry_id:
                    is_valid = False
                    reasons.append("Cannot delete invoice with journal entry")
            
            if is_valid:
                valid_invoices.append({
                    "id": str(invoice.id),
                    "invoice_number": invoice.number,
                    "status": invoice.status.value,
                    "total_amount": float(invoice.total_amount or 0)
                })
            else:
                invalid_invoices.append({
                    "id": str(invoice.id),
                    "invoice_number": invoice.number,
                    "status": invoice.status.value,
                    "reasons": reasons
                })
        
        return {
            "operation": operation,
            "total_requested": len(invoice_ids),
            "valid_count": len(valid_invoices),
            "invalid_count": len(invalid_invoices),
            "not_found_count": len(not_found_ids),
            "valid_invoices": valid_invoices,
            "invalid_invoices": invalid_invoices,
            "not_found_ids": [str(id) for id in not_found_ids],
            "can_proceed": len(valid_invoices) > 0
        }
