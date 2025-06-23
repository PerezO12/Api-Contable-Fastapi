"""
Payment Terms Processor Service
Implementa la lógica de procesamiento de condiciones de pago estilo Odoo
para generar múltiples líneas de vencimiento en journal entries
"""
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment_terms import PaymentTerms, PaymentSchedule
from app.models.journal_entry import JournalEntryLine
from app.models.account import Account
from app.utils.exceptions import BusinessRuleError, ValidationError

import logging
logger = logging.getLogger(__name__)


class PaymentTermsProcessor:
    """
    Procesador de condiciones de pago para facturas
    Maneja la división de importes en múltiples vencimientos según Odoo
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_invoice_payment_terms(
        self, 
        invoice: Invoice, 
        receivable_account: Account,
        line_counter: int
    ) -> Tuple[List[JournalEntryLine], int]:
        """
        Procesa las condiciones de pago de una factura generando múltiples líneas
        de cuentas por cobrar/pagar según los vencimientos
        
        Args:
            invoice: Factura a procesar
            receivable_account: Cuenta por cobrar/pagar a usar
            line_counter: Contador actual de líneas para continuar numeración
            
        Returns:
            Tuple con (lista_de_lineas_generadas, nuevo_contador_lineas)
        """
        logger.info(f"Processing payment terms for invoice {invoice.number}")
        
        # Si no hay condiciones de pago, generar una sola línea
        if not invoice.payment_terms_id:
            return self._create_single_due_line(
                invoice, receivable_account, line_counter
            )
        
        # Obtener las condiciones de pago
        payment_terms = self.db.query(PaymentTerms).filter(
            PaymentTerms.id == invoice.payment_terms_id
        ).first()
        
        if not payment_terms:
            logger.warning(f"Payment terms {invoice.payment_terms_id} not found, creating single line")
            return self._create_single_due_line(
                invoice, receivable_account, line_counter
            )
        
        # Validar que las condiciones de pago están completas
        if not payment_terms.is_valid:
            raise BusinessRuleError(
                f"Payment terms '{payment_terms.name}' are invalid. "
                f"Total percentage: {payment_terms.total_percentage}%"
            )
        
        # Calcular vencimientos basados en las condiciones de pago
        due_lines = self._create_multiple_due_lines(
            invoice, payment_terms, receivable_account, line_counter
        )
        
        # Ajustar diferencias de redondeo en la última línea
        self._adjust_rounding_differences(due_lines, invoice.total_amount)
        
        return due_lines, line_counter + len(due_lines)
    
    def _create_single_due_line(
        self, 
        invoice: Invoice, 
        receivable_account: Account,
        line_counter: int
    ) -> Tuple[List[JournalEntryLine], int]:
        """
        Crea una sola línea de vencimiento cuando no hay condiciones de pago
        """
        # Determinar débito/crédito según tipo de factura
        if invoice.invoice_type.value == "CUSTOMER_INVOICE":
            debit = invoice.total_amount
            credit = Decimal('0')
        else:  # SUPPLIER_INVOICE
            debit = Decimal('0')
            credit = invoice.total_amount
        
        # Usar due_date de la factura o invoice_date si no hay due_date
        due_date = invoice.due_date or invoice.invoice_date
        
        line = JournalEntryLine(
            account_id=receivable_account.id,
            description=f"Invoice {invoice.number} - {invoice.third_party.name}",
            debit_amount=debit,
            credit_amount=credit,
            third_party_id=invoice.third_party_id,
            due_date=due_date,
            invoice_date=invoice.invoice_date,
            line_number=line_counter
        )
        
        logger.info(f"Created single due line for invoice {invoice.number}: {debit + credit}")
        return [line], line_counter + 1
    
    def _create_multiple_due_lines(
        self,
        invoice: Invoice,
        payment_terms: PaymentTerms,
        receivable_account: Account,
        line_counter: int
    ) -> List[JournalEntryLine]:
        """
        Crea múltiples líneas de vencimiento basadas en las condiciones de pago
        """
        due_lines = []
        base_date = invoice.invoice_date
        
        logger.info(f"Creating {len(payment_terms.payment_schedules)} due lines for invoice {invoice.number}")
        
        for schedule in payment_terms.payment_schedules:
            # Calcular monto para este vencimiento
            line_amount = schedule.calculate_amount(invoice.total_amount)
              # Calcular fecha de vencimiento
            # Convertir date a datetime para el método calculate_payment_date
            base_datetime = datetime.combine(base_date, datetime.min.time())
            due_datetime = schedule.calculate_payment_date(base_datetime)
            due_date = due_datetime.date()  # Convertir de vuelta a date
            
            # Determinar débito/crédito según tipo de factura
            if invoice.invoice_type.value == "CUSTOMER_INVOICE":
                debit = line_amount
                credit = Decimal('0')
            else:  # SUPPLIER_INVOICE
                debit = Decimal('0')
                credit = line_amount
            
            # Crear descripción detallada
            description = self._build_line_description(
                invoice, schedule, line_amount, due_date
            )
            
            line = JournalEntryLine(
                account_id=receivable_account.id,
                description=description,
                debit_amount=debit,
                credit_amount=credit,
                third_party_id=invoice.third_party_id,
                due_date=due_date,
                invoice_date=invoice.invoice_date,
                line_number=line_counter,
                # Campos adicionales para identificar el vencimiento
                # TODO: Agregar campos personalizados si es necesario
            )
            
            due_lines.append(line)
            line_counter += 1
            
            logger.debug(f"Created due line {schedule.sequence}: {line_amount} due on {due_date}")
        
        return due_lines
    
    def _build_line_description(
        self,
        invoice: Invoice,
        schedule: PaymentSchedule,
        amount: Decimal,
        due_date: date
    ) -> str:
        """
        Construye la descripción para una línea de vencimiento
        """
        base_desc = f"Invoice {invoice.number} - {invoice.third_party.name}"
        
        if schedule.description:
            return f"{base_desc} - {schedule.description} ({schedule.percentage}%)"
        else:
            return f"{base_desc} - Payment {schedule.sequence} ({schedule.percentage}%, due {due_date.strftime('%Y-%m-%d')})"
    
    def _adjust_rounding_differences(
        self, 
        due_lines: List[JournalEntryLine], 
        total_amount: Decimal
    ) -> None:
        """
        Ajusta diferencias de redondeo en la última línea para que el total cuadre
        """
        if not due_lines:
            return
        
        # Calcular total actual de las líneas
        current_total = sum(
            line.debit_amount + line.credit_amount for line in due_lines
        )
        
        # Calcular diferencia de redondeo
        difference = total_amount - current_total
        
        if difference != Decimal('0'):
            logger.info(f"Adjusting rounding difference of {difference} in last due line")
            
            # Ajustar la última línea
            last_line = due_lines[-1]
            if last_line.debit_amount > 0:
                last_line.debit_amount += difference
            else:
                last_line.credit_amount += difference
    
    def get_payment_schedule_preview(
        self, 
        invoice_amount: Decimal,
        payment_terms_id: uuid.UUID,
        invoice_date: date
    ) -> List[Dict]:
        """
        Obtiene una vista previa de cómo se dividirán los pagos
        sin crear las líneas contables
        
        Args:
            invoice_amount: Monto total de la factura
            payment_terms_id: ID de las condiciones de pago
            invoice_date: Fecha base para calcular vencimientos
              Returns:
            Lista con información de cada vencimiento
        """
        payment_terms = self.db.query(PaymentTerms).filter(
            PaymentTerms.id == payment_terms_id
        ).first()
        
        if not payment_terms:
            raise ValidationError(f"Payment terms {payment_terms_id} not found")
        
        if not payment_terms.is_valid:
            raise ValidationError(f"Payment terms '{payment_terms.name}' are invalid")
        
        preview = []
        total_calculated = Decimal('0')
        
        for schedule in payment_terms.payment_schedules:
            amount = schedule.calculate_amount(invoice_amount)
            # Convertir date a datetime para el método calculate_payment_date
            invoice_datetime = datetime.combine(invoice_date, datetime.min.time())
            due_datetime = schedule.calculate_payment_date(invoice_datetime)
            due_date = due_datetime.date()  # Convertir de vuelta a date
            total_calculated += amount
            
            preview.append({
                'sequence': schedule.sequence,
                'description': schedule.description or f"Payment {schedule.sequence}",
                'percentage': float(schedule.percentage),
                'days': schedule.days,
                'amount': float(amount),
                'due_date': due_date.isoformat(),
                'due_date_formatted': due_date.strftime('%Y-%m-%d')
            })
        
        # Ajustar diferencia de redondeo en el último elemento
        if preview and total_calculated != invoice_amount:
            difference = invoice_amount - total_calculated
            preview[-1]['amount'] = float(Decimal(str(preview[-1]['amount'])) + difference)
        
        return preview
    
    def validate_payment_terms_for_invoice(
        self, 
        payment_terms_id: uuid.UUID
    ) -> Tuple[bool, List[str]]:
        """
        Valida que unas condiciones de pago son apropiadas para usar
        
        Returns:
            Tuple con (es_valido, lista_errores)
        """
        errors = []
        
        payment_terms = self.db.query(PaymentTerms).filter(
            PaymentTerms.id == payment_terms_id,
            PaymentTerms.is_active == True
        ).first()
        
        if not payment_terms:
            errors.append("Payment terms not found or inactive")
            return False, errors
        
        if not payment_terms.payment_schedules:
            errors.append("Payment terms must have at least one payment schedule")
        
        if payment_terms.total_percentage != Decimal('100.00'):
            errors.append(f"Total percentage must be 100%, current: {payment_terms.total_percentage}%")
        
        # Validar que no hay solapamientos o inconsistencias en los cronogramas
        schedules = sorted(payment_terms.payment_schedules, key=lambda x: x.days)
        for i, schedule in enumerate(schedules):
            if not schedule.is_valid:
                errors.append(f"Schedule {schedule.sequence} is invalid")
            
            # Validar secuencias
            if schedule.sequence != i + 1:
                errors.append(f"Schedule sequences should be consecutive starting from 1")
        
        return len(errors) == 0, errors


class PaymentTermsCalculator:
    """
    Calculadora auxiliar para operaciones de condiciones de pago
    """
    
    @staticmethod
    def calculate_due_dates(
        base_date: date,
        payment_schedules: List[PaymentSchedule]
    ) -> List[Tuple[PaymentSchedule, date]]:
        """
        Calcula todas las fechas de vencimiento para una lista de cronogramas
        """
        results = []
        for schedule in payment_schedules:
            due_date = base_date + timedelta(days=schedule.days)
            results.append((schedule, due_date))
        return results
    
    @staticmethod
    def split_amount_by_percentages(
        total_amount: Decimal,
        percentages: List[Decimal]
    ) -> List[Decimal]:
        """
        Divide un monto total según porcentajes, ajustando redondeo
        """
        amounts = []
        total_calculated = Decimal('0')
        
        for percentage in percentages[:-1]:  # Todos excepto el último
            amount = (total_amount * percentage) / Decimal('100')
            amounts.append(amount)
            total_calculated += amount
        
        # El último monto es el residuo para evitar errores de redondeo
        last_amount = total_amount - total_calculated
        amounts.append(last_amount)
        
        return amounts
