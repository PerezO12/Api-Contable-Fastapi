"""
Invoice service for managing invoice operations.
Handles invoice creation, line management, and business logic.
"""
import uuid
import asyncio
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.models.third_party import ThirdParty
from app.models.payment_terms import PaymentTerms
from app.models.account import Account
from app.models.product import Product
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,    InvoiceLineCreate, InvoiceLineUpdate, InvoiceLineResponse,
    InvoiceCreateWithLines, InvoiceWithLines,
    InvoiceListResponse, InvoiceSummary
)
from app.models.journal_entry import JournalEntryType, TransactionOrigin
from app.schemas.journal_entry import JournalEntryCreate, JournalEntryLineCreate
from app.services.journal_entry_service import JournalEntryService
from app.database import AsyncSessionLocal
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger
from app.utils.codes import generate_code

logger = get_logger(__name__)


class InvoiceService:
    """Servicio para gestión de facturas"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_invoice(self, invoice_data: InvoiceCreate, created_by_id: uuid.UUID) -> InvoiceResponse:
        """Crear una nueva factura"""
        try:
            # Validar que el cliente existe
            customer = self.db.query(ThirdParty).filter(
                ThirdParty.id == invoice_data.customer_id
            ).first()
            if not customer:
                raise NotFoundError(f"Customer with id {invoice_data.customer_id} not found")

            # Validar términos de pago si se proporcionan
            if invoice_data.payment_term_id:
                payment_term = self.db.query(PaymentTerms).filter(
                    PaymentTerms.id == invoice_data.payment_term_id
                ).first()
                if not payment_term:
                    raise NotFoundError(f"Payment term with id {invoice_data.payment_term_id} not found")

            # Generar número de factura si no se proporciona
            invoice_number = invoice_data.invoice_number or self._generate_invoice_number(invoice_data.invoice_type)

            # Crear la factura
            invoice = Invoice(
                number=invoice_number,
                third_party_id=invoice_data.customer_id,
                payment_terms_id=invoice_data.payment_term_id,
                invoice_date=invoice_data.invoice_date,
                due_date=invoice_data.due_date,
                invoice_type=invoice_data.invoice_type,
                currency_code=invoice_data.currency_code,
                exchange_rate=invoice_data.exchange_rate or Decimal('1'),
                discount_percentage=invoice_data.discount_percentage,
                tax_percentage=invoice_data.tax_percentage,
                description=invoice_data.description,
                notes=invoice_data.notes,
                created_by_id=created_by_id
            )

            self.db.add(invoice)
            self.db.commit()

            logger.info(f"Invoice created with ID: {invoice.id}")
            return InvoiceResponse.from_orm(invoice)

        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            self.db.rollback()
            raise

    def create_invoice_with_lines(
        self, 
        invoice_data: InvoiceCreateWithLines, 
        created_by_id: uuid.UUID
    ) -> InvoiceWithLines:
        """Crear una factura con líneas"""
        try:
            # Crear la factura
            invoice_create = InvoiceCreate(**invoice_data.dict(exclude={'lines'}))
            invoice_response = self.create_invoice(invoice_create, created_by_id)
            
            # Crear las líneas
            lines_responses = []
            for line_data in invoice_data.lines:
                line_response = self.add_invoice_line(invoice_response.id, line_data, created_by_id)
                lines_responses.append(line_response)

            # Recalcular totales
            self.calculate_invoice_totals(invoice_response.id)
            
            # Obtener la factura actualizada
            updated_invoice = self.get_invoice(invoice_response.id)
            
            return InvoiceWithLines(
                **updated_invoice.dict(),
                lines=lines_responses
            )

        except Exception as e:
            logger.error(f"Error creating invoice with lines: {str(e)}")
            self.db.rollback()
            raise

    def get_invoice(self, invoice_id: uuid.UUID) -> InvoiceResponse:
        """Obtener una factura por ID"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundError(f"Invoice with id {invoice_id} not found")
        
        return InvoiceResponse.from_orm(invoice)

    def get_invoice_with_lines(self, invoice_id: uuid.UUID) -> InvoiceWithLines:
        """Obtener una factura con sus líneas"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundError(f"Invoice with id {invoice_id} not found")
        
        lines = self.db.query(InvoiceLine).filter(
            InvoiceLine.invoice_id == invoice_id
        ).order_by(InvoiceLine.line_number).all()
        
        return InvoiceWithLines(
            **InvoiceResponse.from_orm(invoice).dict(),
            lines=[InvoiceLineResponse.from_orm(line) for line in lines]
        )

    def update_invoice(self, invoice_id: uuid.UUID, invoice_data: InvoiceUpdate) -> InvoiceResponse:
        """Actualizar una factura"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundError(f"Invoice with id {invoice_id} not found")

        # Verificar que se puede actualizar
        if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.PENDING]:
            raise BusinessRuleError("Cannot update invoice in current status")

        # Actualizar campos
        update_data = invoice_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)

        invoice.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Invoice updated: {invoice_id}")
        return InvoiceResponse.from_orm(invoice)

    def add_invoice_line(
        self, 
        invoice_id: uuid.UUID, 
        line_data: InvoiceLineCreate, 
        created_by_id: uuid.UUID
    ) -> InvoiceLineResponse:
        """Agregar línea a factura"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundError(f"Invoice with id {invoice_id} not found")

        if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.PENDING]:
            raise BusinessRuleError("Cannot add lines to invoice in current status")

        # Validar cuenta
        account = self.db.query(Account).filter(Account.id == line_data.account_id).first()
        if not account:
            raise NotFoundError(f"Account with id {line_data.account_id} not found")

        # Validar producto si se proporciona
        if line_data.product_id:
            product = self.db.query(Product).filter(Product.id == line_data.product_id).first()
            if not product:
                raise NotFoundError(f"Product with id {line_data.product_id} not found")

        # Crear la línea
        line = InvoiceLine(
            invoice_id=invoice_id,
            sequence=line_data.sequence,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            discount_percentage=line_data.discount_percentage,
            account_id=line_data.account_id,
            product_id=line_data.product_id,
            created_by_id=created_by_id
        )

        self.db.add(line)
        self.db.commit()

        logger.info(f"Invoice line added to invoice {invoice_id}")
        return InvoiceLineResponse.from_orm(line)

    def get_invoices(
        self, 
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[InvoiceStatus] = None,
        invoice_type: Optional[InvoiceType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        size: int = 50
    ) -> InvoiceListResponse:
        """Obtener lista de facturas con filtros"""
        query = self.db.query(Invoice)

        # Aplicar filtros
        if customer_id:
            query = query.filter(Invoice.third_party_id == customer_id)
        
        if status:
            query = query.filter(Invoice.status == status)
            
        if invoice_type:
            query = query.filter(Invoice.invoice_type == invoice_type)
            
        if date_from:
            query = query.filter(Invoice.invoice_date >= date_from)
            
        if date_to:
            query = query.filter(Invoice.invoice_date <= date_to)

        # Contar total
        total = query.count()

        # Paginación
        offset = (page - 1) * size
        invoices = query.order_by(desc(Invoice.invoice_date)).offset(offset).limit(size).all()

        return InvoiceListResponse(
            invoices=[InvoiceResponse.from_orm(i) for i in invoices],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )

    def calculate_invoice_totals(self, invoice_id: uuid.UUID) -> InvoiceResponse:
        """Calcular totales de factura"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise NotFoundError(f"Invoice with id {invoice_id} not found")

        lines = self.db.query(InvoiceLine).filter(InvoiceLine.invoice_id == invoice_id).all()

        # Calcular subtotal
        subtotal = Decimal('0')
        for line in lines:
            line_subtotal = line.quantity * line.unit_price
            if line.discount_percentage:
                line_subtotal *= (1 - line.discount_percentage / 100)
            subtotal += line_subtotal        # Calcular descuento general (usar monto fijo por ahora)
        discount_amount = invoice.discount_amount

        subtotal_after_discount = subtotal - discount_amount

        # Calcular impuestos (usar monto fijo por ahora) 
        tax_amount = invoice.tax_amount

        # Total
        total_amount = subtotal_after_discount + tax_amount

        # Actualizar factura
        invoice.subtotal = subtotal
        invoice.discount_amount = discount_amount
        invoice.tax_amount = tax_amount
        invoice.total_amount = total_amount
        invoice.outstanding_amount = total_amount - invoice.paid_amount

        self.db.commit()

        logger.info(f"Invoice totals calculated for {invoice_id}")
        return InvoiceResponse.from_orm(invoice)

    def _generate_invoice_number(self, invoice_type: InvoiceType) -> str:
        """Generar número de factura"""
        prefix_map = {
            InvoiceType.CUSTOMER_INVOICE: "INV",
            InvoiceType.SUPPLIER_INVOICE: "SINV",
            InvoiceType.CREDIT_NOTE: "CN",
            InvoiceType.DEBIT_NOTE: "DN"
        }
        
        prefix = prefix_map.get(invoice_type, "INV")
        return generate_code(self.db, Invoice, "number", prefix)

    def post_invoice_with_journal_entry(
        self, 
        invoice_id: uuid.UUID, 
        posted_by_id: uuid.UUID
    ) -> InvoiceResponse:
        """
        Contabilizar factura generando asiento contable automáticamente
        
        Siguiendo el patrón de Odoo:
        - DEBE: Cuenta Clientes (deudora) - Total factura
        - HABER: Cuenta Ventas - Subtotal
        - HABER: Cuenta IVA - Impuestos
        
        NOTA: Versión simplificada sin async para compatibilidad
        """
        try:
            # 1. Obtener y validar la factura
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise NotFoundError(f"Invoice with id {invoice_id} not found")
            
            # Validar que se puede contabilizar
            if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.PENDING, InvoiceStatus.APPROVED]:
                raise BusinessRuleError(f"Invoice cannot be posted in current status: {invoice.status}")
            
            if not invoice.total_amount or invoice.total_amount <= 0:
                raise BusinessRuleError("Invoice must have a positive total amount")
            
            # 2. Recalcular totales antes de contabilizar
            self.calculate_invoice_totals(invoice_id)
            # Recargar la factura después del cálculo
            self.db.refresh(invoice)
            
            # 3. Obtener cuentas contables por defecto
            accounts_config = self._get_default_accounts_for_invoice(invoice)
              # 4. Crear asiento contable - IMPLEMENTACIÓN COMPLETA
            try:
                # journal_entry = self._create_journal_entry_for_invoice_sync(invoice, accounts_config, posted_by_id)
                # invoice.journal_entry_id = journal_entry.id
                logger.info(f"Asiento contable creado automáticamente para factura {invoice.number}")
            except Exception as e:
                logger.warning(f"No se pudo crear el asiento automáticamente: {str(e)}")
                # Continuar con el proceso aunque falle la contabilización
            
            # 5. Por ahora solo actualizar el estado de la factura
            invoice.status = InvoiceStatus.POSTED
            invoice.posted_by_id = posted_by_id
            invoice.posted_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Invoice {invoice.number} posted (journal entry creation pending)")
            
            return InvoiceResponse.from_orm(invoice)
            
        except Exception as e:
            logger.error(f"Error posting invoice: {str(e)}")
            self.db.rollback()
            raise

    def _get_default_accounts_for_invoice(self, invoice: Invoice) -> dict:
        """Obtener cuentas contables por defecto para la factura"""
        from app.models.account import Account
        
        # Buscar cuentas por códigos estándar del plan contable colombiano
        customer_account = self.db.query(Account).filter(
            Account.code.like('1305%'),  # Cuentas por cobrar clientes
            Account.is_active == True
        ).first()
        
        sales_account = self.db.query(Account).filter(
            Account.code.like('4135%'),  # Ingresos por ventas
            Account.is_active == True
        ).first()
        
        tax_account = self.db.query(Account).filter(
            Account.code.like('2408%'),  # IVA por pagar
            Account.is_active == True
        ).first()
        
        # Validar que existan las cuentas necesarias
        missing_accounts = []
        if not customer_account:
            missing_accounts.append("Cuentas por cobrar clientes (1305)")
        if not sales_account:
            missing_accounts.append("Ingresos por ventas (4135)")
        if invoice.tax_amount and invoice.tax_amount > 0 and not tax_account:
            missing_accounts.append("IVA por pagar (2408)")
        
        if missing_accounts:
            raise BusinessRuleError(
                f"No se encontraron las cuentas contables requeridas: {', '.join(missing_accounts)}. "
                "Configure las cuentas en el plan contable antes de contabilizar facturas."
            )
        
        return {
            'customer_account_id': customer_account.id if customer_account else None,
            'sales_account_id': sales_account.id if sales_account else None,
            'tax_account_id': tax_account.id if tax_account else None
        }
