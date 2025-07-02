"""
API v1 router configuration.
"""
from fastapi import APIRouter

from app.api.v1 import (
    accounts, auth, users, journal_entries, reports, report_api, 
    export_templates, export, cost_centers, third_parties, cost_center_reports,
    products, journals, generic_import, import_templates
)
from app.api import payment_terms, payments, invoices, bank_extracts, bank_reconciliation, nfe, payment_flow

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Account management routes
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])

# Journal entry routes
api_router.include_router(journal_entries.router, prefix="/journal-entries", tags=["journal-entries"])

# Journal routes
api_router.include_router(journals.router, prefix="/journals", tags=["journals"])

# Cost center routes
api_router.include_router(cost_centers.router, prefix="/cost-centers", tags=["cost-centers"])

# Third party routes
api_router.include_router(third_parties.router, prefix="/third-parties", tags=["third-parties"])

# Product routes
api_router.include_router(products.router, prefix="/products", tags=["products"])

# Payment terms routes
api_router.include_router(payment_terms.router, tags=["payment-terms"])

# Payment routes - Odoo-like payment workflow
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])

# Payment flow routes - Complete payment workflow (import, match, confirm)
api_router.include_router(payment_flow.router, prefix="/payment-flow", tags=["payment-flow"])

# Invoice routes - Customer and supplier invoices
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])

# Bank extract routes - Bank statement import and management
api_router.include_router(bank_extracts.router, prefix="/bank-extracts", tags=["bank-extracts"])

# Bank reconciliation routes - Bank reconciliation workflow
api_router.include_router(bank_reconciliation.router, prefix="/bank-reconciliation", tags=["bank-reconciliation"])

# NFe routes - Brazilian electronic invoice bulk import
api_router.include_router(nfe.router, prefix="/nfe", tags=["nfe"])

# Cost center reports routes
api_router.include_router(cost_center_reports.router, prefix="/cost-center-reports", tags=["cost-center-reports"])

# Export templates routes
api_router.include_router(export_templates.router, prefix="/templates", tags=["export-templates"])

# Data export routes - Generic export system for any table
api_router.include_router(export.router, prefix="/export", tags=["export"])

# Report routes - Now enabled and fully functional
api_router.include_router(reports.router, prefix="/reports/legacy", tags=["reports-legacy"])

# New unified report API - Especificación exacta del endpoint /reports
api_router.include_router(report_api.router, prefix="/reports", tags=["report-api"])

# Generic import system - Metadata-driven import assistant
api_router.include_router(generic_import.router, prefix="/generic-import", tags=["generic-import"])

# Import templates system - CSV template downloads
api_router.include_router(import_templates.router, prefix="/import", tags=["import-templates"])