# Importar todos los modelos para que SQLAlchemy los reconozca
from app.models.base import Base
from app.models.user import User, UserRole, UserSession
from app.models.account import Account, AccountType, AccountCategory
from app.models.journal import Journal, JournalType
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType, TransactionOrigin
from app.models.cost_center import CostCenter
from app.models.third_party import ThirdParty, ThirdPartyType, DocumentType
from app.models.payment_terms import PaymentTerms, PaymentSchedule
from app.models.product import Product, ProductType, ProductStatus, MeasurementUnit, TaxCategory
from app.models.tax import Tax, TaxType, TaxScope

from app.models.audit import (
    AuditLog, AuditAction, AuditLogLevel, ChangeTracking,
    SystemConfiguration, CompanyInfo, NumberSequence
)
# Importar modelos del sistema de pagos y banca
from app.models.payment import Payment, PaymentInvoice, PaymentStatus, PaymentType
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.models.bank_extract import BankExtract, BankExtractLine, BankExtractStatus
from app.models.bank_reconciliation import BankReconciliation, ReconciliationType

# Importar modelos de NFe
from app.models.nfe import NFe, NFeItem, NFeStatus, NFeType

# Exportar para facilitar importaciones
__all__ = [
    "Base",
    "User", 
    "UserRole",
    "UserSession",
    "Account", 
    "AccountType", 
    "AccountCategory",
    "Journal",
    "JournalType",
    "JournalEntry", 
    "JournalEntryLine", 
    "JournalEntryStatus", 
    "JournalEntryType",
    "TransactionOrigin",
    "CostCenter",
    "ThirdParty",
    "ThirdPartyType",
    "DocumentType",
    "PaymentTerms",
    "PaymentSchedule",
    "Product",
    "ProductType",
    "ProductStatus",
    "MeasurementUnit",   
    "TaxCategory",
    "AuditLog",
    "AuditAction",
    "AuditLogLevel",
    "ChangeTracking",
    "SystemConfiguration",
    "CompanyInfo",
    "NumberSequence",
    # Modelos del sistema de pagos y banca
    "Payment",
    "PaymentInvoice", 
    "PaymentStatus",
    "PaymentType",
    "Invoice",
    "InvoiceLine",
    "InvoiceStatus", 
    "InvoiceType",
    "BankExtract",
    "BankExtractLine",
    "BankExtractStatus",
    "BankReconciliation",
    "ReconciliationType",
    # Modelos de NFe
    "NFe",
    "NFeItem", 
    "NFeStatus",
    "NFeType"
]