"""
Payment Flow Service - Implementa el flujo completo de pagos.

Flujo implementado:
1. Emisión y contabilización de la factura (YA IMPLEMENTADO en InvoiceService)
2. Importación de pagos en borrador
3. Confirmación del pago  
4. Resultado en los informes
5. Estados y dependencias

Basado en el workflow de sistemas ERP modernos.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func

from app.models.invoice import Invoice, InvoiceStatus, InvoiceType
from app.models.payment import Payment, PaymentInvoice, PaymentStatus, PaymentType, PaymentMethod
from app.models.bank_extract import BankExtract, BankExtractLine, BankExtractStatus, BankExtractLineType
from app.models.third_party import ThirdParty
from app.models.account import Account, AccountType
from app.models.journal import Journal, JournalType
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType, TransactionOrigin

from app.schemas.bank_extract import BankExtractImport, BankExtractImportResult
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentAutoMatchResult

from app.services.bank_extract_service import BankExtractService
from app.services.payment_service import PaymentService
from app.services.journal_entry_service import JournalEntryService
from app.services.account_determination_service import AccountDeterminationService

from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger
from app.utils.codes import generate_code

logger = get_logger(__name__)


class PaymentFlowService:
    """
    Servicio principal para el flujo completo de pagos
    Coordina la importación, vinculación automática y confirmación de pagos
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.bank_extract_service = BankExtractService(db)
        self.payment_service = PaymentService(db)
        # self.journal_entry_service = JournalEntryService(db)  # Comentado hasta resolver asyncio
        self.account_determination = AccountDeterminationService(db)

    # =============================================
    # PASO 2: IMPORTACIÓN DE PAGOS EN BORRADOR
    # =============================================

    def import_payments_with_auto_matching(
        self,
        extract_data: BankExtractImport,
        created_by_id: uuid.UUID,
        file_content: Optional[bytes] = None,
        auto_match: bool = True
    ) -> Dict[str, Any]:
        """
        Paso 2: Importación de extracto bancario con auto-vinculación
        
        Flujo:
        1. Importa el extracto bancario (BankExtract y BankExtractLines)
        2. Para cada línea de pago, busca facturas coincidentes
        3. Crea Payment en estado DRAFT vinculado a la línea y factura (si encuentra coincidencia)
        
        Returns:
            Dict con resultado de importación y auto-matching
        """
        try:
            logger.info(f"Starting payment import with auto-matching for extract: {extract_data.name}")
            
            # 1. Importar extracto bancario
            import_result = self.bank_extract_service.import_bank_extract(
                extract_data, created_by_id, file_content
            )
            
            # Obtener el extracto creado
            extract = self.db.query(BankExtract).filter(
                BankExtract.id == import_result.extract_id
            ).first()
            
            if not extract:
                raise BusinessRuleError("Failed to retrieve imported extract")
            
            auto_match_results = []
            
            if auto_match:
                # 2. Auto-matching para cada línea
                for line in extract.extract_lines:
                    match_result = self._auto_match_extract_line(line, created_by_id)
                    auto_match_results.append(match_result)
            
            self.db.commit()
            
            # 3. Estadísticas del resultado
            total_lines = len(extract.extract_lines)
            matched_lines = sum(1 for result in auto_match_results if result["matched"])
            payments_created = sum(1 for result in auto_match_results if result["payment_created"])
            
            logger.info(f"Import completed: {matched_lines}/{total_lines} lines matched, {payments_created} payments created")
            
            return {
                "extract_id": extract.id,
                "extract_name": extract.name,
                "total_lines": total_lines,
                "matched_lines": matched_lines,
                "payments_created": payments_created,
                "auto_match_results": auto_match_results,
                "import_result": import_result
            }
            
        except Exception as e:
            logger.error(f"Error importing payments with auto-matching: {str(e)}")
            self.db.rollback()
            raise

    def _auto_match_extract_line(self, line: BankExtractLine, created_by_id: uuid.UUID) -> Dict[str, Any]:
        """
        Auto-matching de una línea de extracto con facturas pendientes
        
        Reglas de matching:
        1. Solo líneas de crédito (ingresos) se consideran para pagos de cliente
        2. Solo líneas de débito (salidas) se consideran para pagos a proveedor  
        3. Busca facturas con:
           - Partner que coincida (por nombre o referencia)
           - Monto pendiente que coincida exactamente
           - Estado POSTED
        """
        try:
            logger.debug(f"Auto-matching line: {line.description}, amount: {line.amount}")
            
            result = {
                "line_id": line.id,
                "line_description": line.description,
                "line_amount": line.amount,
                "matched": False,
                "payment_created": False,
                "invoice_id": None,
                "payment_id": None,
                "match_reason": "",
                "errors": []
            }
            
            # Solo procesar líneas con monto significativo
            if abs(line.amount) < Decimal('0.01'):
                result["match_reason"] = "Amount too small"
                return result
            
            # Determinar tipo de pago basado en el signo del monto
            if line.is_credit:  # Entrada de dinero = pago de cliente
                payment_type = PaymentType.CUSTOMER_PAYMENT
                invoice_type = InvoiceType.CUSTOMER_INVOICE
                search_amount = line.credit_amount
            elif line.is_debit:  # Salida de dinero = pago a proveedor
                payment_type = PaymentType.SUPPLIER_PAYMENT
                invoice_type = InvoiceType.SUPPLIER_INVOICE
                search_amount = line.debit_amount
            else:
                result["match_reason"] = "Invalid line amount"
                return result
            
            # Buscar facturas coincidentes
            matching_invoices = self._find_matching_invoices(
                line, invoice_type, search_amount
            )
            
            if not matching_invoices:
                result["match_reason"] = "No matching invoices found"
                return result
            
            # Tomar la primera coincidencia exacta
            matched_invoice = matching_invoices[0]
            result["matched"] = True
            result["invoice_id"] = matched_invoice.id
            result["match_reason"] = f"Exact match with invoice {matched_invoice.number}"
            
            # Crear payment en borrador
            payment = self._create_draft_payment_from_line(
                line, matched_invoice, payment_type, created_by_id
            )
            
            if payment:
                result["payment_created"] = True
                result["payment_id"] = payment.id
                
                # Vincular la línea con el pago
                line.payment_id = payment.id
            
            return result
            
        except Exception as e:
            logger.error(f"Error in auto-matching line {line.id}: {str(e)}")
            return {
                "line_id": line.id,
                "line_description": line.description,
                "line_amount": line.amount,
                "matched": False,
                "payment_created": False,
                "invoice_id": None,
                "payment_id": None,
                "match_reason": f"Error: {str(e)}",
                "errors": [str(e)]
            }

    def _find_matching_invoices(
        self, 
        line: BankExtractLine, 
        invoice_type: InvoiceType, 
        amount: Decimal
    ) -> List[Invoice]:
        """
        Busca facturas que coincidan con la línea del extracto
        
        Criterios de búsqueda:
        1. Tipo de factura correcto
        2. Estado POSTED 
        3. Monto pendiente coincide exactamente
        4. Partner coincide (por nombre aproximado o referencia)
        """
        
        # Buscar por monto exacto primero
        base_query = self.db.query(Invoice).filter(
            and_(
                Invoice.invoice_type == invoice_type,
                Invoice.status == InvoiceStatus.POSTED,
                Invoice.outstanding_amount == amount
            )
        ).join(ThirdParty)
        
        # Si hay información del partner en la línea, filtrar por nombre
        if line.partner_name:
            partner_name = line.partner_name.strip().upper()
            base_query = base_query.filter(
                or_(
                    func.upper(ThirdParty.name).like(f"%{partner_name}%"),
                    func.upper(ThirdParty.commercial_name).like(f"%{partner_name}%"),
                    func.upper(ThirdParty.tax_id).like(f"%{partner_name}%")
                )
            )
        
        # Ordenar por fecha de vencimiento (más urgentes primero)
        invoices = base_query.order_by(Invoice.due_date).limit(5).all()
        
        return invoices

    def _create_draft_payment_from_line(
        self,
        line: BankExtractLine,
        invoice: Invoice,
        payment_type: PaymentType,
        created_by_id: uuid.UUID
    ) -> Optional[Payment]:
        """
        Crea un Payment en estado DRAFT vinculado a la línea del extracto y la factura
        """
        try:
            # Generar número de pago
            payment_number = self._generate_payment_number(payment_type)
            
            # Determinar monto del pago
            payment_amount = line.credit_amount if line.is_credit else line.debit_amount
            
            # Crear el pago
            payment = Payment(
                number=payment_number,
                reference=line.reference or line.bank_reference,
                external_reference=line.bank_reference,
                payment_type=payment_type,
                payment_method=PaymentMethod.BANK_TRANSFER,  # Asumimos transferencia bancaria
                status=PaymentStatus.DRAFT,
                third_party_id=invoice.third_party_id,
                payment_date=line.transaction_date,
                value_date=line.value_date or line.transaction_date,
                amount=payment_amount,
                allocated_amount=Decimal('0'),
                unallocated_amount=payment_amount,
                currency_code=line.bank_extract.currency_code,
                exchange_rate=Decimal('1'),
                account_id=line.bank_extract.account_id,
                description=f"Auto-generated from bank extract: {line.description}",
                notes=f"Matched with invoice {invoice.number}",
                created_by_id=created_by_id
            )
            
            self.db.add(payment)
            self.db.flush()
            
            # Crear la relación payment-invoice
            payment_invoice = PaymentInvoice(
                payment_id=payment.id,
                invoice_id=invoice.id,
                amount=min(payment_amount, invoice.outstanding_amount),
                allocation_date=line.transaction_date,
                description=f"Auto-allocation from extract line",
                created_by_id=created_by_id
            )
            
            self.db.add(payment_invoice)
            
            # Actualizar montos del pago
            payment.update_allocation_amounts()
            
            logger.info(f"Created draft payment {payment.number} for invoice {invoice.number}")
            return payment
            
        except Exception as e:
            logger.error(f"Error creating draft payment: {str(e)}")
            return None

    # =============================================
    # PASO 3: CONFIRMACIÓN DEL PAGO
    # =============================================

    def confirm_payment(self, payment_id: uuid.UUID, confirmed_by_id: uuid.UUID) -> PaymentResponse:
        """
        Paso 3: Confirmar pago (DRAFT → POSTED)
        
        Flujo:
        1. Valida el pago en borrador
        2. Determina cuentas contables
        3. Genera Journal Entry en diario de Banco
        4. Actualiza estado del pago a POSTED
        5. Realiza conciliación automática con facturas
        6. Actualiza estado de facturas (PAID/PARTIALLY_PAID)
        """
        try:
            logger.info(f"Confirming payment {payment_id}")
            
            # 1. Obtener y validar el pago
            payment = self.db.query(Payment).options(
                joinedload(Payment.payment_invoices).joinedload(PaymentInvoice.invoice),
                joinedload(Payment.third_party),
                joinedload(Payment.account)
            ).filter(Payment.id == payment_id).first()
            
            if not payment:
                raise NotFoundError(f"Payment with id {payment_id} not found")
            
            if payment.status != PaymentStatus.DRAFT:
                raise BusinessRuleError(f"Payment cannot be confirmed in current status: {payment.status}")
            
            # 2. Validar completitud del pago
            validation_errors = self._validate_payment_for_confirmation(payment)
            if validation_errors:
                raise BusinessRuleError(f"Validation errors: {'; '.join(validation_errors)}")
            
            # 3. Crear asiento contable del pago
            journal_entry = self._create_journal_entry_for_payment(payment, confirmed_by_id)
            
            # 4. Actualizar estado del pago
            payment.status = PaymentStatus.POSTED
            payment.posted_by_id = confirmed_by_id
            payment.posted_at = datetime.utcnow()
            payment.journal_entry_id = journal_entry.id
            payment.updated_at = datetime.utcnow()
            
            # 5. Conciliar automáticamente con facturas
            reconciliation_results = self._auto_reconcile_payment_invoices(payment)
            
            # 6. Actualizar estados de facturas
            self._update_invoice_payment_status(payment)
            
            # 7. Marcar línea de extracto como conciliada
            if payment.bank_extract_lines:
                for line in payment.bank_extract_lines:
                    line.is_reconciled = True
                    line.reconciled_amount = payment.amount
                    line.pending_amount = Decimal('0')
                    line.reconciled_by_id = confirmed_by_id
                    line.reconciled_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Payment {payment.number} confirmed successfully with journal entry {journal_entry.number}")
            return PaymentResponse.from_orm(payment)
            
        except Exception as e:
            logger.error(f"Error confirming payment {payment_id}: {str(e)}")
            self.db.rollback()
            raise

    def _validate_payment_for_confirmation(self, payment: Payment) -> List[str]:
        """Valida que el pago puede ser confirmado"""
        errors = []
        
        if not payment.amount or payment.amount <= 0:
            errors.append("Payment must have a positive amount")
        
        if not payment.third_party_id:
            errors.append("Payment must have a third party")
        
        if not payment.account_id:
            errors.append("Payment must have a bank/cash account")
        
        if not payment.payment_date:
            errors.append("Payment must have a payment date")
        
        # Validar que las facturas asignadas existen y están en estado correcto
        for pi in payment.payment_invoices:
            if pi.invoice.status != InvoiceStatus.POSTED:
                errors.append(f"Invoice {pi.invoice.number} is not in POSTED status")
        
        return errors

    def _create_journal_entry_for_payment(self, payment: Payment, posted_by_id: uuid.UUID) -> JournalEntry:
        """
        Crea el asiento contable del pago
        
        Estructura del asiento:
        - DEBE: Cuenta de Banco/Caja (entrada de fondos para cobros)
        - HABER: Cuenta del Partner (reducción de saldo por cobrar/pagar)
        """
        
        # Determinar el diario (banco o caja según la cuenta)
        bank_journal = self._get_bank_journal_for_account(payment.account_id)
        
        # Determinar cuenta del partner (buscar cuenta por defecto)
        if payment.is_customer_payment:
            # Buscar cuenta de clientes por cobrar
            partner_account = self.db.query(Account).filter(
                and_(
                    Account.account_type == AccountType.ACTIVO,
                    Account.code.like('11%')  # Cuentas de activo corriente
                )
            ).first()
        else:
            # Buscar cuenta de proveedores por pagar  
            partner_account = self.db.query(Account).filter(
                and_(
                    Account.account_type == AccountType.PASIVO,
                    Account.code.like('22%')  # Cuentas de pasivo corriente
                )
            ).first()
        
        if not partner_account:
            raise BusinessRuleError("No partner account found for payment posting")
        
        # Crear el asiento
        journal_entry = JournalEntry(
            number=f"JE-PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            journal_id=bank_journal.id,
            entry_date=payment.payment_date,
            entry_type=JournalEntryType.PAYMENT,
            reference=payment.number,
            description=f"Payment {payment.number} - {payment.third_party.name}",
            notes=payment.description,
            origin=TransactionOrigin.PAYMENT,
            origin_id=str(payment.id),
            status=JournalEntryStatus.POSTED,
            created_by_id=posted_by_id,
            posted_by_id=posted_by_id,
            posted_at=datetime.utcnow()
        )
        
        self.db.add(journal_entry)
        self.db.flush()
        
        # Crear líneas del asiento
        if payment.is_customer_payment:
            # Pago de cliente: DEBE Banco, HABER Cuenta por Cobrar
            lines = [
                JournalEntryLine(
                    journal_entry_id=journal_entry.id,
                    sequence=1,
                    account_id=payment.account_id,  # Banco
                    third_party_id=payment.third_party_id,
                    description=f"Payment received from {payment.third_party.name}",
                    debit_amount=payment.amount,
                    credit_amount=Decimal('0'),
                    currency_code=payment.currency_code,
                    exchange_rate=payment.exchange_rate
                ),
                JournalEntryLine(
                    journal_entry_id=journal_entry.id,
                    sequence=2,
                    account_id=partner_account.id,  # Cuenta por Cobrar
                    third_party_id=payment.third_party_id,
                    description=f"Payment from {payment.third_party.name}",
                    debit_amount=Decimal('0'),
                    credit_amount=payment.amount,
                    currency_code=payment.currency_code,
                    exchange_rate=payment.exchange_rate
                )
            ]
        else:
            # Pago a proveedor: DEBE Cuenta por Pagar, HABER Banco
            lines = [
                JournalEntryLine(
                    journal_entry_id=journal_entry.id,
                    sequence=1,
                    account_id=partner_account.id,  # Cuenta por Pagar
                    third_party_id=payment.third_party_id,
                    description=f"Payment to {payment.third_party.name}",
                    debit_amount=payment.amount,
                    credit_amount=Decimal('0'),
                    currency_code=payment.currency_code,
                    exchange_rate=payment.exchange_rate
                ),
                JournalEntryLine(
                    journal_entry_id=journal_entry.id,
                    sequence=2,
                    account_id=payment.account_id,  # Banco
                    third_party_id=payment.third_party_id,
                    description=f"Payment to {payment.third_party.name}",
                    debit_amount=Decimal('0'),
                    credit_amount=payment.amount,
                    currency_code=payment.currency_code,
                    exchange_rate=payment.exchange_rate
                )
            ]
        
        # Agregar líneas al asiento
        for line in lines:
            self.db.add(line)
        
        # Actualizar totales del asiento
        journal_entry.calculate_totals()
        
        return journal_entry

    def _get_bank_journal_for_account(self, account_id: uuid.UUID) -> Journal:
        """Obtiene el diario de banco asociado a la cuenta"""
        
        # Buscar diario de banco que corresponda a la cuenta
        journal = self.db.query(Journal).filter(
            and_(
                Journal.default_account_id == account_id,
                Journal.type == JournalType.BANK
            )
        ).first()
        
        if not journal:
            # Si no hay diario específico, buscar el primer diario de banco
            journal = self.db.query(Journal).filter(
                Journal.type == JournalType.BANK
            ).first()
        
        if not journal:
            raise BusinessRuleError("No bank journal found for payment posting")
        
        return journal

    def _auto_reconcile_payment_invoices(self, payment: Payment) -> List[Dict[str, Any]]:
        """
        Concilia automáticamente el pago con las facturas asignadas
        Implementa el concepto de reconciliación interna
        """
        reconciliation_results = []
        
        for payment_invoice in payment.payment_invoices:
            try:
                # Obtener las líneas del asiento de la factura (cuenta por cobrar/pagar)
                invoice_lines = self.db.query(JournalEntryLine).join(JournalEntry).filter(
                    and_(
                        JournalEntry.id == payment_invoice.invoice.journal_entry_id,
                        JournalEntryLine.third_party_id == payment.third_party_id,
                        JournalEntryLine.debit_amount > 0 if payment.is_customer_payment else JournalEntryLine.credit_amount > 0
                    )
                ).all()
                
                # Obtener las líneas del asiento del pago (cuenta por cobrar/pagar)
                payment_lines = self.db.query(JournalEntryLine).join(JournalEntry).filter(
                    and_(
                        JournalEntry.id == payment.journal_entry_id,
                        JournalEntryLine.third_party_id == payment.third_party_id,
                        JournalEntryLine.credit_amount > 0 if payment.is_customer_payment else JournalEntryLine.debit_amount > 0
                    )
                ).all()
                
                # Marcar líneas como conciliadas (esto sería parte de un sistema de conciliación más complejo)
                result = {
                    "invoice_id": payment_invoice.invoice.id,
                    "invoice_number": payment_invoice.invoice.number,
                    "allocated_amount": payment_invoice.amount,
                    "reconciled": True,
                    "invoice_lines_count": len(invoice_lines),
                    "payment_lines_count": len(payment_lines)
                }
                
                reconciliation_results.append(result)
                
            except Exception as e:
                logger.error(f"Error reconciling payment with invoice {payment_invoice.invoice.number}: {str(e)}")
                result = {
                    "invoice_id": payment_invoice.invoice.id,
                    "invoice_number": payment_invoice.invoice.number,
                    "allocated_amount": payment_invoice.amount,
                    "reconciled": False,
                    "error": str(e)
                }
                reconciliation_results.append(result)
        
        return reconciliation_results

    def _update_invoice_payment_status(self, payment: Payment):
        """
        Actualiza el estado de las facturas basado en los pagos recibidos
        """
        for payment_invoice in payment.payment_invoices:
            invoice = payment_invoice.invoice
            
            # Recalcular montos pagados de la factura
            total_paid = self.db.query(func.sum(PaymentInvoice.amount)).join(Payment).filter(
                and_(
                    PaymentInvoice.invoice_id == invoice.id,
                    Payment.status == PaymentStatus.POSTED
                )
            ).scalar() or Decimal('0')
            
            # Actualizar montos en la factura
            invoice.paid_amount = total_paid
            invoice.outstanding_amount = invoice.total_amount - total_paid
            
            # Actualizar estado
            if invoice.outstanding_amount <= Decimal('0.01'):  # Tolerancia para redondeo
                invoice.status = InvoiceStatus.PAID
            elif invoice.paid_amount > Decimal('0'):
                invoice.status = InvoiceStatus.PARTIALLY_PAID
            
            logger.info(f"Updated invoice {invoice.number}: paid={invoice.paid_amount}, outstanding={invoice.outstanding_amount}, status={invoice.status}")

    # =============================================
    # UTILIDADES
    # =============================================

    def _generate_payment_number(self, payment_type: PaymentType) -> str:
        """Genera número de pago según el tipo"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        if payment_type == PaymentType.CUSTOMER_PAYMENT:
            return f"PAY-IN-{timestamp}"
        elif payment_type == PaymentType.SUPPLIER_PAYMENT:
            return f"PAY-OUT-{timestamp}"
        else:
            return f"PAY-{timestamp}"

    def get_payment_flow_status(self, extract_id: uuid.UUID) -> Dict[str, Any]:
        """
        Obtiene el estado del flujo de pagos para un extracto
        Útil para monitoreo y reportes
        """
        extract = self.db.query(BankExtract).options(
            joinedload(BankExtract.extract_lines).joinedload(BankExtractLine.payment)
        ).filter(BankExtract.id == extract_id).first()
        
        if not extract:
            raise NotFoundError(f"Bank extract with id {extract_id} not found")
        
        total_lines = len(extract.extract_lines)
        matched_lines = sum(1 for line in extract.extract_lines if line.payment_id)
        posted_payments = sum(
            1 for line in extract.extract_lines 
            if line.payment and line.payment.status == PaymentStatus.POSTED
        )
        draft_payments = sum(
            1 for line in extract.extract_lines 
            if line.payment and line.payment.status == PaymentStatus.DRAFT
        )
        
        return {
            "extract_id": extract.id,
            "extract_name": extract.name,
            "extract_status": extract.status,
            "total_lines": total_lines,
            "matched_lines": matched_lines,
            "draft_payments": draft_payments,
            "posted_payments": posted_payments,
            "unmatched_lines": total_lines - matched_lines,
            "completion_percentage": (posted_payments / total_lines * 100) if total_lines > 0 else 0
        }
