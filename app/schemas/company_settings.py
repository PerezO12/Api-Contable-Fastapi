"""
Schemas for company settings and default account configurations
"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class CompanySettingsBase(BaseModel):
    """Schema base para configuración de empresa"""
    company_name: str = Field(..., description="Nombre de la empresa")
    tax_id: Optional[str] = Field(None, description="NIT/RUT de la empresa")
    currency_code: str = Field(default="COP", description="Código de moneda (ISO 4217)")
    
    # Cuentas por defecto para terceros
    default_customer_receivable_account_id: Optional[UUID] = Field(None, description="Cuenta por cobrar por defecto para clientes")
    default_supplier_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por pagar por defecto para proveedores")
    
    # Cuentas por defecto para ingresos y gastos
    default_sales_income_account_id: Optional[UUID] = Field(None, description="Cuenta de ingresos por ventas por defecto")
    default_purchase_expense_account_id: Optional[UUID] = Field(None, description="Cuenta de gastos por compras por defecto")
    
    # Cuentas de impuestos
    default_sales_tax_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para impuestos por pagar sobre ventas")
    default_purchase_tax_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para impuestos deducibles sobre compras")
    default_tax_account_id: Optional[UUID] = Field(None, description="Cuenta genérica para impuestos (fallback)")
    
    # Impuestos brasileños específicos
    default_icms_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para ICMS por pagar")
    default_icms_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para ICMS deducible")
    default_pis_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para PIS por pagar")
    default_pis_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para PIS deducible")
    default_cofins_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para COFINS por pagar")
    default_cofins_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para COFINS deducible")
    default_ipi_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para IPI por pagar")
    default_ipi_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para IPI deducible")
    default_iss_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para ISS por pagar")
    default_csll_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para CSLL por pagar")
    default_irpj_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para IRPJ por pagar")
    
    # Cuentas básicas de tesorería
    default_cash_account_id: Optional[UUID] = Field(None, description="Cuenta de efectivo por defecto")
    default_bank_account_id: Optional[UUID] = Field(None, description="Cuenta bancaria por defecto")
    
    # Transacciones bancarias
    bank_suspense_account_id: Optional[UUID] = Field(None, description="Cuenta transitoria bancaria")
    internal_transfer_account_id: Optional[UUID] = Field(None, description="Cuenta para transferencias internas")
    
    # Diferidos
    deferred_expense_account_id: Optional[UUID] = Field(None, description="Cuenta para gastos diferidos")
    deferred_expense_journal_id: Optional[UUID] = Field(None, description="Diario para gastos diferidos")
    deferred_expense_months: Optional[int] = Field(default=12, description="Meses para amortización de gastos diferidos")
    
    deferred_revenue_account_id: Optional[UUID] = Field(None, description="Cuenta para ingresos diferidos")
    deferred_revenue_journal_id: Optional[UUID] = Field(None, description="Diario para ingresos diferidos")
    deferred_revenue_months: Optional[int] = Field(default=12, description="Meses para amortización de ingresos diferidos")
    
    # Descuentos
    invoice_line_discount_same_account: bool = Field(default=True, description="Usar misma cuenta del producto para descuentos por línea")
    early_payment_discount_gain_account_id: Optional[UUID] = Field(None, description="Cuenta para ganancia por descuento por pago anticipado")
    early_payment_discount_loss_account_id: Optional[UUID] = Field(None, description="Cuenta para pérdida por descuento por pago anticipado")
    
    # Configuración adicional
    validate_invoice_on_posting: bool = Field(default=True, description="Validar facturas al contabilizar")
    deferred_generation_method: str = Field(default="on_invoice_validation", description="Método de generación de diferidos")
    is_active: bool = Field(default=True, description="Configuración activa")
    notes: Optional[str] = Field(None, description="Notas adicionales")


class CompanySettingsCreate(CompanySettingsBase):
    """Schema para crear configuración de empresa"""
    pass


class CompanySettingsUpdate(BaseModel):
    """Schema para actualizar configuración de empresa"""
    company_name: Optional[str] = Field(None, description="Nombre de la empresa")
    tax_id: Optional[str] = Field(None, description="NIT/RUT de la empresa")
    currency_code: Optional[str] = Field(None, description="Código de moneda (ISO 4217)")
    
    # Cuentas por defecto para terceros
    default_customer_receivable_account_id: Optional[UUID] = Field(None, description="Cuenta por cobrar por defecto para clientes")
    default_supplier_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por pagar por defecto para proveedores")
    
    # Cuentas por defecto para ingresos y gastos
    default_sales_income_account_id: Optional[UUID] = Field(None, description="Cuenta de ingresos por ventas por defecto")
    default_purchase_expense_account_id: Optional[UUID] = Field(None, description="Cuenta de gastos por compras por defecto")
    
    # Cuentas de impuestos
    default_sales_tax_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para impuestos por pagar sobre ventas")
    default_purchase_tax_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para impuestos deducibles sobre compras")
    default_tax_account_id: Optional[UUID] = Field(None, description="Cuenta genérica para impuestos (fallback)")
    
    # Impuestos brasileños específicos
    default_icms_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para ICMS por pagar")
    default_icms_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para ICMS deducible")
    default_pis_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para PIS por pagar")
    default_pis_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para PIS deducible")
    default_cofins_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para COFINS por pagar")
    default_cofins_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para COFINS deducible")
    default_ipi_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para IPI por pagar")
    default_ipi_deductible_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para IPI deducible")
    default_iss_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para ISS por pagar")
    default_csll_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para CSLL por pagar")
    default_irpj_payable_account_id: Optional[UUID] = Field(None, description="Cuenta por defecto para IRPJ por pagar")
    
    # Cuentas básicas de tesorería
    default_cash_account_id: Optional[UUID] = Field(None, description="Cuenta de efectivo por defecto")
    default_bank_account_id: Optional[UUID] = Field(None, description="Cuenta bancaria por defecto")
    
    # Transacciones bancarias
    bank_suspense_account_id: Optional[UUID] = Field(None, description="Cuenta transitoria bancaria")
    internal_transfer_account_id: Optional[UUID] = Field(None, description="Cuenta para transferencias internas")
    
    # Diferidos
    deferred_expense_account_id: Optional[UUID] = Field(None, description="Cuenta para gastos diferidos")
    deferred_expense_journal_id: Optional[UUID] = Field(None, description="Diario para gastos diferidos")
    deferred_expense_months: Optional[int] = Field(None, description="Meses para amortización de gastos diferidos")
    
    deferred_revenue_account_id: Optional[UUID] = Field(None, description="Cuenta para ingresos diferidos")
    deferred_revenue_journal_id: Optional[UUID] = Field(None, description="Diario para ingresos diferidos")
    deferred_revenue_months: Optional[int] = Field(None, description="Meses para amortización de ingresos diferidos")
    
    # Descuentos
    invoice_line_discount_same_account: Optional[bool] = Field(None, description="Usar misma cuenta del producto para descuentos por línea")
    early_payment_discount_gain_account_id: Optional[UUID] = Field(None, description="Cuenta para ganancia por descuento por pago anticipado")
    early_payment_discount_loss_account_id: Optional[UUID] = Field(None, description="Cuenta para pérdida por descuento por pago anticipado")
    
    # Configuración adicional
    validate_invoice_on_posting: Optional[bool] = Field(None, description="Validar facturas al contabilizar")
    deferred_generation_method: Optional[str] = Field(None, description="Método de generación de diferidos")
    is_active: Optional[bool] = Field(None, description="Configuración activa")
    notes: Optional[str] = Field(None, description="Notas adicionales")


class CompanySettingsResponse(CompanySettingsBase):
    """Schema para respuesta de configuración de empresa"""
    id: UUID = Field(..., description="ID único de la configuración")
    
    # Información de relaciones (nombres de cuentas para mostrar)
    default_customer_receivable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta por cobrar por defecto")
    default_supplier_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta por pagar por defecto")
    
    # Nombres de cuentas de ingresos y gastos
    default_sales_income_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de ingresos por ventas por defecto")
    default_purchase_expense_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de gastos por compras por defecto")
    
    # Nombres de cuentas de tesorería
    default_cash_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de efectivo por defecto")
    default_bank_account_name: Optional[str] = Field(None, description="Nombre de la cuenta bancaria por defecto")
    
    # Nombres de cuentas bancarias
    bank_suspense_account_name: Optional[str] = Field(None, description="Nombre de la cuenta transitoria bancaria")
    internal_transfer_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de transferencias internas")
    
    # Nombres de cuentas diferidas
    deferred_expense_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de gastos diferidos")
    deferred_revenue_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de ingresos diferidos")
    
    # Nombres de cuentas de descuentos
    early_payment_discount_gain_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de ganancia por descuento")
    early_payment_discount_loss_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de pérdida por descuento")
    
    # Nombres de cuentas de impuestos
    default_sales_tax_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de impuestos por pagar sobre ventas")
    default_purchase_tax_deductible_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de impuestos deducibles sobre compras")
    default_tax_account_name: Optional[str] = Field(None, description="Nombre de la cuenta genérica de impuestos")
    
    # Nombres de cuentas de impuestos brasileños específicos
    default_icms_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de ICMS por pagar")
    default_icms_deductible_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de ICMS deducible")
    default_pis_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de PIS por pagar")
    default_pis_deductible_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de PIS deducible")
    default_cofins_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de COFINS por pagar")
    default_cofins_deductible_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de COFINS deducible")
    default_ipi_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de IPI por pagar")
    default_ipi_deductible_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de IPI deducible")
    default_iss_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de ISS por pagar")
    default_csll_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de CSLL por pagar")
    default_irpj_payable_account_name: Optional[str] = Field(None, description="Nombre de la cuenta de IRPJ por pagar")
    
    # Flags de configuración
    has_customer_receivable_configured: bool = Field(..., description="Tiene cuenta por cobrar configurada")
    has_supplier_payable_configured: bool = Field(..., description="Tiene cuenta por pagar configurada")
    has_sales_income_configured: bool = Field(..., description="Tiene cuenta de ingresos por ventas configurada")
    has_purchase_expense_configured: bool = Field(..., description="Tiene cuenta de gastos por compras configurada")
    has_deferred_accounts_configured: bool = Field(..., description="Tiene cuentas diferidas configuradas")
    has_tax_accounts_configured: bool = Field(..., description="Tiene cuentas de impuestos configuradas")
    has_brazilian_tax_accounts_configured: bool = Field(..., description="Tiene cuentas de impuestos brasileños configuradas")
    
    class Config:
        from_attributes = True


class ThirdPartyAccountUpdate(BaseModel):
    """Schema para actualizar cuentas contables de un tercero"""
    receivable_account_id: Optional[UUID] = Field(None, description="Cuenta por cobrar específica")
    payable_account_id: Optional[UUID] = Field(None, description="Cuenta por pagar específica")


class DefaultAccountsInfo(BaseModel):
    """Schema para información de cuentas por defecto"""
    # Información de cuentas disponibles
    available_receivable_accounts: list = Field(default_factory=list, description="Cuentas disponibles para clientes")
    available_payable_accounts: list = Field(default_factory=list, description="Cuentas disponibles para proveedores")
    available_bank_accounts: list = Field(default_factory=list, description="Cuentas bancarias disponibles")
    available_expense_accounts: list = Field(default_factory=list, description="Cuentas de gastos disponibles")
    available_revenue_accounts: list = Field(default_factory=list, description="Cuentas de ingresos disponibles")
    
    # Configuración actual
    current_settings: Optional[CompanySettingsResponse] = Field(None, description="Configuración actual de la empresa")
    
    # Información de estado para compatibilidad con frontend
    has_receivable_account: bool = Field(default=False, description="Tiene cuenta por cobrar configurada")
    has_payable_account: bool = Field(default=False, description="Tiene cuenta por pagar configurada")
    has_bank_suspense_account: bool = Field(default=False, description="Tiene cuenta bancaria transitoria configurada")
    has_internal_transfer_account: bool = Field(default=False, description="Tiene cuenta de transferencias internas configurada")
    has_deferred_expense_account: bool = Field(default=False, description="Tiene cuenta de gastos diferidos configurada")
    has_deferred_revenue_account: bool = Field(default=False, description="Tiene cuenta de ingresos diferidos configurada")
    has_early_payment_accounts: bool = Field(default=False, description="Tiene cuentas de descuentos configuradas")
    missing_accounts: list = Field(default_factory=list, description="Lista de cuentas faltantes")
    recommendations: list = Field(default_factory=list, description="Recomendaciones para la configuración")


class AccountSuggestion(BaseModel):
    """Schema para sugerencias de cuentas por defecto"""
    account_id: UUID = Field(..., description="ID de la cuenta")
    account_code: str = Field(..., description="Código de la cuenta")
    account_name: str = Field(..., description="Nombre de la cuenta")
    account_type: str = Field(..., description="Tipo de cuenta")
    suggested_for: str = Field(..., description="Para qué se sugiere esta cuenta")
    confidence: float = Field(..., description="Nivel de confianza (0-1)")
    reason: str = Field(..., description="Razón de la sugerencia")
