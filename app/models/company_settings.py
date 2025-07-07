"""
Company Settings model for default accounting configurations.
Stores company-wide default accounts for various transactions.
"""
import uuid
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.currency import Currency


class CompanySettings(Base):
    """
    Configuración general de la empresa para cuentas contables por defecto
    Equivalente a la configuración de empresa en Odoo
    """
    __tablename__ = "company_settings"
    
    # Información básica de la empresa
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Moneda base de la empresa
    base_currency_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("currencies.id"), 
        nullable=True,
        comment="Moneda base de la empresa para reportes y saldos"
    )
    # DEPRECATED: Mantener por compatibilidad, será removido en futuras versiones
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # === CUENTAS POR DEFECTO PARA TERCEROS ===
    
    # Cuentas por cobrar (clientes)
    default_customer_receivable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por cobrar por defecto para clientes"
    )
    
    # Cuentas por pagar (proveedores)
    default_supplier_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por pagar por defecto para proveedores"
    )
    
    # === CUENTAS POR DEFECTO PARA INGRESOS Y GASTOS ===
    
    # Cuenta de ingresos por ventas por defecto
    default_sales_income_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta de ingresos por ventas por defecto"
    )
    
    # Cuenta de gastos por compras por defecto
    default_purchase_expense_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta de gastos por compras por defecto"
    )
    
    # === CUENTAS DE IMPUESTOS ===
    
    # Impuestos sobre ventas (por pagar)
    default_sales_tax_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para impuestos por pagar sobre ventas"
    )
    
    # Impuestos sobre compras (deducibles)
    default_purchase_tax_deductible_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para impuestos deducibles sobre compras"
    )
    
    # Cuenta genérica de impuestos (fallback)
    default_tax_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta genérica para impuestos (fallback)"
    )
    
    # === IMPUESTOS BRASILEÑOS ESPECÍFICOS ===
    
    # ICMS (Imposto sobre Circulação de Mercadorias e Serviços)
    default_icms_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para ICMS por pagar"
    )
    
    default_icms_deductible_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para ICMS deducible"
    )
    
    # PIS (Programa de Integração Social)
    default_pis_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para PIS por pagar"
    )
    
    default_pis_deductible_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para PIS deducible"
    )
    
    # COFINS (Contribuição para o Financiamento da Seguridade Social)
    default_cofins_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para COFINS por pagar"
    )
    
    default_cofins_deductible_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para COFINS deducible"
    )
    
    # IPI (Imposto sobre Produtos Industrializados)
    default_ipi_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para IPI por pagar"
    )
    
    default_ipi_deductible_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para IPI deducible"
    )
    
    # ISS (Imposto sobre Serviços)
    default_iss_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para ISS por pagar"
    )
    
    # CSLL (Contribuição Social sobre o Lucro Líquido)
    default_csll_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para CSLL por pagar"
    )
    
    # IRPJ (Imposto de Renda Pessoa Jurídica)
    default_irpj_payable_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta por defecto para IRPJ por pagar"
    )
    
    # === CAMPOS COMPATIBLES CON EL SERVICIO DE DETERMINACIÓN ===
    # Campos adicionales para compatibilidad con AccountDeterminationServiceV2
    # Estos referencian los mismos campos que arriba pero con nombres cortos
    
    @property
    def icms_account_id(self) -> Optional[uuid.UUID]:
        """Alias para default_icms_payable_account_id"""
        return self.default_icms_payable_account_id
    
    @property
    def pis_account_id(self) -> Optional[uuid.UUID]:
        """Alias para default_pis_payable_account_id"""
        return self.default_pis_payable_account_id
    
    @property
    def cofins_account_id(self) -> Optional[uuid.UUID]:
        """Alias para default_cofins_payable_account_id"""
        return self.default_cofins_payable_account_id
    
    @property
    def ipi_account_id(self) -> Optional[uuid.UUID]:
        """Alias para default_ipi_payable_account_id"""
        return self.default_ipi_payable_account_id
    
    @property
    def iss_account_id(self) -> Optional[uuid.UUID]:
        """Alias para default_iss_payable_account_id"""
        return self.default_iss_payable_account_id
    
    @property
    def csll_account_id(self) -> Optional[uuid.UUID]:
        """Alias para default_csll_payable_account_id"""
        return self.default_csll_payable_account_id
    
    @property
    def irpj_account_id(self) -> Optional[uuid.UUID]:
        """Alias para default_irpj_payable_account_id"""
        return self.default_irpj_payable_account_id
    
    # Cuentas básicas de tesorería
    default_cash_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta de efectivo por defecto"
    )
    
    default_bank_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta bancaria por defecto"
    )
    
    # Cuenta para diferencias de cambio
    default_currency_exchange_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta para diferencias de cambio"
    )
    
    # === TRANSACCIONES BANCARIAS Y PAGOS ===
    
    # Suspensión bancaria (cuenta transitoria)
    bank_suspense_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta transitoria para suspensión bancaria"
    )
    
    # Transferencia interna
    internal_transfer_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta para transferencias internas de liquidez"
    )
    
    # === ASIENTOS DE GASTOS E INGRESOS DIFERIDOS ===
    
    # Gastos diferidos
    deferred_expense_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta para gastos diferidos"
    )
    
    deferred_expense_journal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("journals.id"), 
        nullable=True,
        comment="Diario para asientos de gastos diferidos"
    )
    
    deferred_expense_months: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        default=12,
        comment="Meses por defecto para amortización de gastos diferidos"
    )
    
    # Ingresos diferidos
    deferred_revenue_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta para ingresos diferidos"
    )
    
    deferred_revenue_journal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("journals.id"), 
        nullable=True,
        comment="Diario para asientos de ingresos diferidos"
    )
    
    deferred_revenue_months: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        default=12,
        comment="Meses por defecto para amortización de ingresos diferidos"
    )
    
    # === DESCUENTOS ===
    
    # Descuentos por línea de factura
    invoice_line_discount_same_account: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Usar misma cuenta que el producto para descuentos por línea"
    )
    
    # Descuentos por pago anticipado
    early_payment_discount_gain_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta para ganancia por descuento por pago anticipado"
    )
    
    early_payment_discount_loss_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("accounts.id"), 
        nullable=True,
        comment="Cuenta para pérdida por descuento por pago anticipado"
    )
    
    # === CONFIGURACIÓN ADICIONAL ===
    
    # Validación en contabilización de facturas
    validate_invoice_on_posting: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Validar facturas automáticamente al contabilizar"
    )
    
    # Método de generación de asientos diferidos
    deferred_generation_method: Mapped[str] = mapped_column(
        String(50), 
        default="on_invoice_validation", 
        nullable=False,
        comment="Cuándo generar asientos diferidos: on_invoice_validation, manual"
    )
    
    # Configuración activa
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadatos
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # === RELACIONES ===
    
    # Moneda base
    base_currency: Mapped[Optional["Currency"]] = relationship(
        "Currency", 
        foreign_keys=[base_currency_id],
        lazy="select"
    )
    
    # Cuentas por defecto para terceros
    default_customer_receivable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_customer_receivable_account_id],
        lazy="select"
    )
    
    default_supplier_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_supplier_payable_account_id],
        lazy="select"
    )
    
    # Cuentas por defecto para ingresos y gastos
    default_sales_income_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_sales_income_account_id],
        lazy="select"
    )
    
    default_purchase_expense_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_purchase_expense_account_id],
        lazy="select"
    )
    
    # Cuentas de impuestos
    default_sales_tax_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_sales_tax_payable_account_id],
        lazy="select"
    )
    
    default_purchase_tax_deductible_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_purchase_tax_deductible_account_id],
        lazy="select"
    )
    
    default_tax_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_tax_account_id],
        lazy="select"
    )
    
    # Relaciones para impuestos brasileños específicos
    default_icms_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_icms_payable_account_id],
        lazy="select"
    )
    
    default_icms_deductible_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_icms_deductible_account_id],
        lazy="select"
    )
    
    default_pis_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_pis_payable_account_id],
        lazy="select"
    )
    
    default_pis_deductible_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_pis_deductible_account_id],
        lazy="select"
    )
    
    default_cofins_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_cofins_payable_account_id],
        lazy="select"
    )
    
    default_cofins_deductible_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_cofins_deductible_account_id],
        lazy="select"
    )
    
    default_ipi_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_ipi_payable_account_id],
        lazy="select"
    )
    
    default_ipi_deductible_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_ipi_deductible_account_id],
        lazy="select"
    )
    
    default_iss_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_iss_payable_account_id],
        lazy="select"
    )
    
    default_csll_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_csll_payable_account_id],
        lazy="select"
    )
    
    default_irpj_payable_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_irpj_payable_account_id],
        lazy="select"
    )
    
    # Cuentas básicas de tesorería
    default_cash_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_cash_account_id],
        lazy="select"
    )
    
    default_bank_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_bank_account_id],
        lazy="select"
    )
    
    # Cuenta para diferencias de cambio
    default_currency_exchange_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[default_currency_exchange_account_id],
        lazy="select"
    )
    
    # Cuentas para transacciones bancarias
    bank_suspense_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[bank_suspense_account_id],
        lazy="select"
    )
    
    internal_transfer_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[internal_transfer_account_id],
        lazy="select"
    )
    
    # Cuentas para diferidos
    deferred_expense_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[deferred_expense_account_id],
        lazy="select"
    )
    
    deferred_revenue_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[deferred_revenue_account_id],
        lazy="select"
    )
    
    # Cuentas para descuentos
    early_payment_discount_gain_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[early_payment_discount_gain_account_id],
        lazy="select"
    )
    
    early_payment_discount_loss_account: Mapped[Optional["Account"]] = relationship(
        "Account", 
        foreign_keys=[early_payment_discount_loss_account_id],
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<CompanySettings(company='{self.company_name}', currency='{self.currency_code}')>"
    
    @property
    def has_customer_receivable_configured(self) -> bool:
        """Verifica si tiene cuenta por cobrar configurada"""
        return self.default_customer_receivable_account_id is not None
    
    @property
    def has_supplier_payable_configured(self) -> bool:
        """Verifica si tiene cuenta por pagar configurada"""
        return self.default_supplier_payable_account_id is not None
    
    @property
    def has_sales_income_configured(self) -> bool:
        """Verifica si tiene cuenta de ingresos por ventas configurada"""
        return self.default_sales_income_account_id is not None
    
    @property
    def has_purchase_expense_configured(self) -> bool:
        """Verifica si tiene cuenta de gastos por compras configurada"""
        return self.default_purchase_expense_account_id is not None
    
    @property
    def has_tax_accounts_configured(self) -> bool:
        """Verifica si tiene al menos una cuenta de impuestos configurada"""
        return (self.default_sales_tax_payable_account_id is not None or 
                self.default_purchase_tax_deductible_account_id is not None or 
                self.default_tax_account_id is not None)
    
    @property
    def has_sales_tax_configured(self) -> bool:
        """Verifica si tiene cuenta de impuestos por pagar configurada"""
        return self.default_sales_tax_payable_account_id is not None
    
    @property
    def has_purchase_tax_configured(self) -> bool:
        """Verifica si tiene cuenta de impuestos deducibles configurada"""
        return self.default_purchase_tax_deductible_account_id is not None
    
    @property
    def has_deferred_accounts_configured(self) -> bool:
        """Verifica si tiene cuentas diferidas configuradas"""
        return (self.deferred_expense_account_id is not None and 
                self.deferred_revenue_account_id is not None)
    
    def validate_configuration(self) -> List[str]:
        """Valida la configuración y retorna lista de errores"""
        errors = []
        
        if not self.company_name or len(self.company_name.strip()) == 0:
            errors.append("El nombre de la empresa es requerido")
        
        if not self.currency_code or len(self.currency_code) != 3:
            errors.append("El código de moneda debe tener 3 caracteres")
        
        # Validaciones opcionales pero recomendadas
        warnings = []
        
        if not self.has_customer_receivable_configured:
            warnings.append("No se ha configurado cuenta por cobrar por defecto para clientes")
        
        if not self.has_supplier_payable_configured:
            warnings.append("No se ha configurado cuenta por pagar por defecto para proveedores")
        
        if not self.has_sales_income_configured:
            warnings.append("No se ha configurado cuenta de ingresos por ventas por defecto")
        
        if not self.has_purchase_expense_configured:
            warnings.append("No se ha configurado cuenta de gastos por compras por defecto")
        
        if not self.bank_suspense_account_id:
            warnings.append("No se ha configurado cuenta transitoria bancaria")
        
        # Por ahora solo retornamos errores críticos
        return errors
    
    @classmethod
    def get_active_settings(cls, db_session):
        """Obtiene la configuración activa de la empresa"""
        return db_session.query(cls).filter(cls.is_active == True).first()
    
    @classmethod
    def get_or_create_default(cls, db_session):
        """Obtiene o crea configuración por defecto si no existe"""
        settings = cls.get_active_settings(db_session)
        
        if not settings:
            settings = cls(
                company_name="Mi Empresa",
                currency_code="USD",
                is_active=True,
                validate_invoice_on_posting=True,
                deferred_generation_method="on_invoice_validation",
                invoice_line_discount_same_account=True,
                deferred_expense_months=12,
                deferred_revenue_months=12
            )
            db_session.add(settings)
            db_session.flush()
        
        return settings
