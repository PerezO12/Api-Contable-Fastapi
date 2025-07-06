"""
Account Determination API endpoints
Provides endpoints for account determination preview and modification
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.account import Account
from app.services.account_determination_service import AccountDeterminationService
from app.schemas.account_determination_schemas import (
    PaymentAccountDeterminationRequest,
    PaymentAccountDeterminationResponse,
    InvoiceAccountDeterminationRequest,
    InvoiceAccountDeterminationResponse,
    PaymentAccountSuggestions,
    InvoiceAccountSuggestions,
    PaymentJournalEntryPreview,
    InvoiceJournalEntryPreview,
    AccountSuggestion,
    InvoiceLineSuggestion,
    TaxAccountSuggestion,
    BrazilianTaxAccountSuggestion,
    JournalEntryLinePreview,
    PaymentAccountDeterminationSummary,
    InvoiceAccountDeterminationSummary
)
from app.utils.exceptions import BusinessRuleError, NotFoundError

router = APIRouter()


@router.post(
    "/payments/{payment_id}/account-suggestions",
    response_model=PaymentAccountDeterminationResponse,
    summary="Obtener sugerencias de cuentas para pago",
    description="Determina las cuentas contables sugeridas para un pago usando la jerarquía Journal → Company Settings → Defaults"
)
async def get_payment_account_suggestions(
    payment_id: str,
    request: PaymentAccountDeterminationRequest,
    db: Session = Depends(get_db)
):
    """
    Obtiene sugerencias de cuentas para un pago específico
    """
    try:
        # Buscar el pago
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with ID {payment_id} not found"
            )
        
        # Inicializar servicio de determinación
        service = AccountDeterminationService(db)
        
        # Determinar cuentas
        accounts = service.determine_accounts_for_payment(payment)
        
        # Convertir a esquemas de respuesta
        suggestions = _convert_payment_accounts_to_suggestions(accounts)
        
        # Generar preview del asiento contable
        journal_entry_lines = service.get_payment_journal_entry_preview(payment)
        journal_entry_preview = _convert_payment_journal_entry_preview(payment, journal_entry_lines)
        
        return PaymentAccountDeterminationResponse(
            success=True,
            message="Sugerencias de cuentas generadas exitosamente",
            warnings=[],
            suggestions=suggestions,
            journal_entry_preview=journal_entry_preview
        )
        
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post(
    "/invoices/{invoice_id}/account-suggestions",
    response_model=InvoiceAccountDeterminationResponse,
    summary="Obtener sugerencias de cuentas para factura",
    description="Determina las cuentas contables sugeridas para una factura usando la jerarquía Journal → Company Settings → Defaults"
)
async def get_invoice_account_suggestions(
    invoice_id: str,
    request: InvoiceAccountDeterminationRequest,
    db: Session = Depends(get_db)
):
    """
    Obtiene sugerencias de cuentas para una factura específica
    """
    try:
        # Buscar la factura
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found"
            )
        
        # Inicializar servicio de determinación
        service = AccountDeterminationService(db)
        
        # Determinar cuentas
        accounts = service.determine_accounts_for_invoice(invoice)
        
        # Convertir a esquemas de respuesta
        suggestions = _convert_invoice_accounts_to_suggestions(accounts)
        
        # Generar preview del asiento contable
        journal_entry_lines = service.get_invoice_journal_entry_preview(invoice)
        journal_entry_preview = _convert_invoice_journal_entry_preview(invoice, journal_entry_lines)
        
        return InvoiceAccountDeterminationResponse(
            success=True,
            message="Sugerencias de cuentas generadas exitosamente",
            warnings=[],
            suggestions=suggestions,
            journal_entry_preview=journal_entry_preview
        )
        
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/payments/{payment_id}/account-summary",
    response_model=PaymentAccountDeterminationSummary,
    summary="Obtener resumen de determinación de cuentas para pago",
    description="Proporciona un resumen estadístico de cómo se determinaron las cuentas para un pago"
)
async def get_payment_account_summary(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene un resumen de la determinación de cuentas para un pago
    """
    try:
        # Buscar el pago
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with ID {payment_id} not found"
            )
        
        # Inicializar servicio de determinación
        service = AccountDeterminationService(db)
        
        # Determinar cuentas
        accounts = service.determine_accounts_for_payment(payment)
        
        # Generar resumen
        summary = _generate_payment_account_summary(payment, accounts)
        
        return summary
        
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/invoices/{invoice_id}/account-summary",
    response_model=InvoiceAccountDeterminationSummary,
    summary="Obtener resumen de determinación de cuentas para factura",
    description="Proporciona un resumen estadístico de cómo se determinaron las cuentas para una factura"
)
async def get_invoice_account_summary(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene un resumen de la determinación de cuentas para una factura
    """
    try:
        # Buscar la factura
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found"
            )
        
        # Inicializar servicio de determinación
        service = AccountDeterminationService(db)
        
        # Determinar cuentas
        accounts = service.determine_accounts_for_invoice(invoice)
        
        # Generar resumen
        summary = _generate_invoice_account_summary(invoice, accounts)
        
        return summary
        
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


# ===============================
# FUNCIONES AUXILIARES
# ===============================

def _convert_payment_accounts_to_suggestions(accounts: Dict) -> PaymentAccountSuggestions:
    """Convierte las cuentas determinadas a esquemas de sugerencias"""
    
    # Convertir cuenta de banco/efectivo
    bank_cash_account = None
    if accounts.get('bank_cash_account'):
        bank_cash_account = AccountSuggestion(
            account_id=accounts['bank_cash_account']['account_id'],
            account_code=accounts['bank_cash_account']['account_code'],
            account_name=accounts['bank_cash_account']['account_name'],
            source=accounts['bank_cash_account']['source']
        )
    
    # Convertir cuenta de tercero
    third_party_account = None
    if accounts.get('third_party_account'):
        third_party_account = AccountSuggestion(
            account_id=accounts['third_party_account']['account_id'],
            account_code=accounts['third_party_account']['account_code'],
            account_name=accounts['third_party_account']['account_name'],
            source=accounts['third_party_account']['source']
        )
    
    # Convertir cuentas de comisiones
    fee_accounts = []
    for fee_account in accounts.get('fee_accounts', []):
        fee_accounts.append(AccountSuggestion(
            account_id=fee_account['account_id'],
            account_code=fee_account['account_code'],
            account_name=fee_account['account_name'],
            source=fee_account['source']
        ))
    
    # Convertir cuentas de diferencias de cambio
    exchange_accounts = []
    for exchange_account in accounts.get('exchange_accounts', []):
        exchange_accounts.append(AccountSuggestion(
            account_id=exchange_account['account_id'],
            account_code=exchange_account['account_code'],
            account_name=exchange_account['account_name'],
            source=exchange_account['source']
        ))
    
    # Convertir cuentas de impuestos
    tax_accounts = []
    for tax_account in accounts.get('tax_accounts', []):
        tax_accounts.append(AccountSuggestion(
            account_id=tax_account['account_id'],
            account_code=tax_account['account_code'],
            account_name=tax_account['account_name'],
            source=tax_account['source']
        ))
    
    return PaymentAccountSuggestions(
        bank_cash_account=bank_cash_account,
        third_party_account=third_party_account,
        fee_accounts=fee_accounts,
        exchange_accounts=exchange_accounts,
        tax_accounts=tax_accounts
    )


def _convert_invoice_accounts_to_suggestions(accounts: Dict) -> InvoiceAccountSuggestions:
    """Convierte las cuentas determinadas a esquemas de sugerencias"""
    
    # Convertir cuenta de tercero
    third_party_account = None
    if accounts.get('third_party_account'):
        third_party_account = AccountSuggestion(
            account_id=accounts['third_party_account']['account_id'],
            account_code=accounts['third_party_account']['account_code'],
            account_name=accounts['third_party_account']['account_name'],
            source=accounts['third_party_account']['source']
        )
    
    # Convertir cuentas de líneas
    line_accounts = []
    for line_account in accounts.get('line_accounts', []):
        line_accounts.append(InvoiceLineSuggestion(
            line_id=line_account['line_id'],
            line_sequence=line_account['line_sequence'],
            line_description=line_account['line_description'],
            account_suggestion=AccountSuggestion(
                account_id=line_account['account_id'],
                account_code=line_account['account_code'],
                account_name=line_account['account_name'],
                source=line_account['source']
            )
        ))
    
    # Convertir cuentas de impuestos
    tax_accounts = []
    for tax_account in accounts.get('tax_accounts', []):
        tax_accounts.append(TaxAccountSuggestion(
            tax_amount=tax_account['tax_amount'],
            account_suggestion=AccountSuggestion(
                account_id=tax_account['account_id'],
                account_code=tax_account['account_code'],
                account_name=tax_account['account_name'],
                source=tax_account['source']
            )
        ))
    
    # Convertir cuentas de impuestos brasileños
    brazilian_tax_accounts = []
    for brazilian_tax_account in accounts.get('brazilian_tax_accounts', []):
        brazilian_tax_accounts.append(BrazilianTaxAccountSuggestion(
            tax_name=brazilian_tax_account['tax_name'],
            tax_amount=brazilian_tax_account['tax_amount'],
            account_suggestion=AccountSuggestion(
                account_id=brazilian_tax_account['account_id'],
                account_code=brazilian_tax_account['account_code'],
                account_name=brazilian_tax_account['account_name'],
                source=brazilian_tax_account['source']
            )
        ))
    
    return InvoiceAccountSuggestions(
        third_party_account=third_party_account,
        line_accounts=line_accounts,
        tax_accounts=tax_accounts,
        brazilian_tax_accounts=brazilian_tax_accounts
    )


def _convert_payment_journal_entry_preview(payment: Payment, lines: List[Dict]) -> PaymentJournalEntryPreview:
    """Convierte las líneas del asiento contable a esquema de preview"""
    
    journal_entry_lines = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    
    for line in lines:
        journal_entry_line = JournalEntryLinePreview(
            account_id=line['account_id'],
            account_code=line['account_code'],
            account_name=line['account_name'],
            description=line['description'],
            debit_amount=line['debit_amount'],
            credit_amount=line['credit_amount'],
            third_party_id=line.get('third_party_id'),
            product_id=line.get('product_id'),
            cost_center_id=line.get('cost_center_id'),
            source=line['source']
        )
        
        journal_entry_lines.append(journal_entry_line)
        total_debit += line['debit_amount']
        total_credit += line['credit_amount']
    
    return PaymentJournalEntryPreview(
        payment_id=payment.id,
        payment_number=payment.number,
        lines=journal_entry_lines,
        total_debit=total_debit,
        total_credit=total_credit
    )


def _convert_invoice_journal_entry_preview(invoice: Invoice, lines: List[Dict]) -> InvoiceJournalEntryPreview:
    """Convierte las líneas del asiento contable a esquema de preview"""
    
    journal_entry_lines = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    
    for line in lines:
        journal_entry_line = JournalEntryLinePreview(
            account_id=line['account_id'],
            account_code=line['account_code'],
            account_name=line['account_name'],
            description=line['description'],
            debit_amount=line['debit_amount'],
            credit_amount=line['credit_amount'],
            third_party_id=line.get('third_party_id'),
            product_id=line.get('product_id'),
            cost_center_id=line.get('cost_center_id'),
            source=line['source']
        )
        
        journal_entry_lines.append(journal_entry_line)
        total_debit += line['debit_amount']
        total_credit += line['credit_amount']
    
    return InvoiceJournalEntryPreview(
        invoice_id=invoice.id,
        invoice_number=invoice.number,
        lines=journal_entry_lines,
        total_debit=total_debit,
        total_credit=total_credit
    )


def _generate_payment_account_summary(payment: Payment, accounts: Dict) -> PaymentAccountDeterminationSummary:
    """Genera un resumen estadístico de la determinación de cuentas para un pago"""
    
    total_accounts = 0
    accounts_from_journal = 0
    accounts_from_company_settings = 0
    accounts_from_defaults = 0
    missing_accounts = 0
    
    # Contar cuentas por fuente
    all_accounts = []
    
    if accounts.get('bank_cash_account'):
        all_accounts.append(accounts['bank_cash_account'])
    
    if accounts.get('third_party_account'):
        all_accounts.append(accounts['third_party_account'])
    
    all_accounts.extend(accounts.get('fee_accounts', []))
    all_accounts.extend(accounts.get('exchange_accounts', []))
    all_accounts.extend(accounts.get('tax_accounts', []))
    
    for account in all_accounts:
        total_accounts += 1
        source = account.get('source', '')
        
        if 'journal' in source:
            accounts_from_journal += 1
        elif 'company_settings' in source:
            accounts_from_company_settings += 1
        elif 'default' in source:
            accounts_from_defaults += 1
    
    return PaymentAccountDeterminationSummary(
        total_accounts_determined=total_accounts,
        accounts_from_journal=accounts_from_journal,
        accounts_from_company_settings=accounts_from_company_settings,
        accounts_from_defaults=accounts_from_defaults,
        missing_accounts=missing_accounts,
        payment_id=payment.id,
        payment_number=payment.number
    )


def _generate_invoice_account_summary(invoice: Invoice, accounts: Dict) -> InvoiceAccountDeterminationSummary:
    """Genera un resumen estadístico de la determinación de cuentas para una factura"""
    
    total_accounts = 0
    accounts_from_journal = 0
    accounts_from_company_settings = 0
    accounts_from_defaults = 0
    missing_accounts = 0
    
    # Contar cuentas por fuente
    all_accounts = []
    
    if accounts.get('third_party_account'):
        all_accounts.append(accounts['third_party_account'])
    
    all_accounts.extend(accounts.get('line_accounts', []))
    all_accounts.extend(accounts.get('tax_accounts', []))
    all_accounts.extend(accounts.get('brazilian_tax_accounts', []))
    
    for account in all_accounts:
        total_accounts += 1
        source = account.get('source', '')
        
        if 'journal' in source:
            accounts_from_journal += 1
        elif 'company_settings' in source:
            accounts_from_company_settings += 1
        elif 'default' in source:
            accounts_from_defaults += 1
    
    return InvoiceAccountDeterminationSummary(
        total_accounts_determined=total_accounts,
        accounts_from_journal=accounts_from_journal,
        accounts_from_company_settings=accounts_from_company_settings,
        accounts_from_defaults=accounts_from_defaults,
        missing_accounts=missing_accounts,
        invoice_id=invoice.id,
        invoice_number=invoice.number
    )
