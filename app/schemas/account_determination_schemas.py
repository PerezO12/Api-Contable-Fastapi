"""
Schemas for account determination preview and modification
"""
from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field
import uuid


class AccountSuggestion(BaseModel):
    """Esquema para una sugerencia de cuenta"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    source: str = Field(description="Fuente de la sugerencia: journal_configuration, company_settings, default_by_type, etc.")
    editable: bool = True
    
    class Config:
        from_attributes = True


class PaymentAccountSuggestions(BaseModel):
    """Esquema para sugerencias de cuentas de pago"""
    bank_cash_account: Optional[AccountSuggestion] = None
    third_party_account: Optional[AccountSuggestion] = None
    fee_accounts: List[AccountSuggestion] = []
    exchange_accounts: List[AccountSuggestion] = []
    tax_accounts: List[AccountSuggestion] = []
    
    class Config:
        from_attributes = True


class InvoiceLineSuggestion(BaseModel):
    """Esquema para sugerencia de cuenta de línea de factura"""
    line_id: uuid.UUID
    line_sequence: int
    line_description: str
    account_suggestion: AccountSuggestion
    
    class Config:
        from_attributes = True


class BrazilianTaxAccountSuggestion(BaseModel):
    """Esquema para sugerencia de cuenta de impuesto brasileño"""
    tax_name: str = Field(description="Nombre del impuesto: ICMS, PIS, COFINS, etc.")
    tax_amount: Decimal = Field(default=Decimal('0'))
    account_suggestion: AccountSuggestion
    
    class Config:
        from_attributes = True


class TaxAccountSuggestion(BaseModel):
    """Esquema para sugerencia de cuenta de impuesto"""
    tax_amount: Decimal
    account_suggestion: AccountSuggestion
    
    class Config:
        from_attributes = True


class InvoiceAccountSuggestions(BaseModel):
    """Esquema para sugerencias de cuentas de factura"""
    third_party_account: Optional[AccountSuggestion] = None
    line_accounts: List[InvoiceLineSuggestion] = []
    tax_accounts: List[TaxAccountSuggestion] = []
    brazilian_tax_accounts: List[BrazilianTaxAccountSuggestion] = []
    
    class Config:
        from_attributes = True


class JournalEntryLinePreview(BaseModel):
    """Esquema para preview de línea de asiento contable"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    third_party_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    cost_center_id: Optional[uuid.UUID] = None
    source: str = Field(description="Fuente de la cuenta")
    
    class Config:
        from_attributes = True


class PaymentJournalEntryPreview(BaseModel):
    """Esquema para preview de asiento contable de pago"""
    payment_id: uuid.UUID
    payment_number: str
    lines: List[JournalEntryLinePreview]
    total_debit: Decimal
    total_credit: Decimal
    
    class Config:
        from_attributes = True


class InvoiceJournalEntryPreview(BaseModel):
    """Esquema para preview de asiento contable de factura"""
    invoice_id: uuid.UUID
    invoice_number: str
    lines: List[JournalEntryLinePreview]
    total_debit: Decimal
    total_credit: Decimal
    
    class Config:
        from_attributes = True


class AccountModification(BaseModel):
    """Esquema para modificación de cuenta"""
    account_id: uuid.UUID
    reason: Optional[str] = Field(None, description="Razón de la modificación")
    
    class Config:
        from_attributes = True


class PaymentAccountModifications(BaseModel):
    """Esquema para modificaciones de cuentas de pago"""
    bank_cash_account_id: Optional[uuid.UUID] = None
    third_party_account_id: Optional[uuid.UUID] = None
    fee_account_modifications: List[AccountModification] = []
    exchange_account_modifications: List[AccountModification] = []
    tax_account_modifications: List[AccountModification] = []
    
    class Config:
        from_attributes = True


class InvoiceLineAccountModification(BaseModel):
    """Esquema para modificación de cuenta de línea de factura"""
    line_id: uuid.UUID
    account_id: uuid.UUID
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class InvoiceAccountModifications(BaseModel):
    """Esquema para modificaciones de cuentas de factura"""
    third_party_account_id: Optional[uuid.UUID] = None
    line_account_modifications: List[InvoiceLineAccountModification] = []
    tax_account_modifications: List[AccountModification] = []
    brazilian_tax_account_modifications: List[AccountModification] = []
    
    class Config:
        from_attributes = True


class AccountDeterminationRequest(BaseModel):
    """Esquema base para solicitud de determinación de cuentas"""
    journal_id: Optional[uuid.UUID] = None
    preview_only: bool = Field(default=True, description="Solo preview, no aplicar cambios")
    
    class Config:
        from_attributes = True


class PaymentAccountDeterminationRequest(AccountDeterminationRequest):
    """Esquema para solicitud de determinación de cuentas de pago"""
    payment_id: uuid.UUID
    modifications: Optional[PaymentAccountModifications] = None


class InvoiceAccountDeterminationRequest(AccountDeterminationRequest):
    """Esquema para solicitud de determinación de cuentas de factura"""
    invoice_id: uuid.UUID
    modifications: Optional[InvoiceAccountModifications] = None


class AccountDeterminationResponse(BaseModel):
    """Esquema base para respuesta de determinación de cuentas"""
    success: bool
    message: str
    warnings: List[str] = []
    
    class Config:
        from_attributes = True


class PaymentAccountDeterminationResponse(AccountDeterminationResponse):
    """Esquema para respuesta de determinación de cuentas de pago"""
    suggestions: PaymentAccountSuggestions
    journal_entry_preview: PaymentJournalEntryPreview


class InvoiceAccountDeterminationResponse(AccountDeterminationResponse):
    """Esquema para respuesta de determinación de cuentas de factura"""
    suggestions: InvoiceAccountSuggestions
    journal_entry_preview: InvoiceJournalEntryPreview


class AccountDeterminationSummary(BaseModel):
    """Esquema para resumen de determinación de cuentas"""
    total_accounts_determined: int
    accounts_from_journal: int
    accounts_from_company_settings: int
    accounts_from_defaults: int
    missing_accounts: int
    
    class Config:
        from_attributes = True


class PaymentAccountDeterminationSummary(AccountDeterminationSummary):
    """Esquema para resumen de determinación de cuentas de pago"""
    payment_id: uuid.UUID
    payment_number: str


class InvoiceAccountDeterminationSummary(AccountDeterminationSummary):
    """Esquema para resumen de determinación de cuentas de factura"""
    invoice_id: uuid.UUID
    invoice_number: str
