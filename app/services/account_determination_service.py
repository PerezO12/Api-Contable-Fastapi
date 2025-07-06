"""
Account Determination Service for Invoice Processing
Implements Odoo-style automatic account determination for invoices.
"""
import uuid
from typing import Dict, List, Optional, Union
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.invoice import Invoice, InvoiceLine, InvoiceType
from app.models.third_party import ThirdParty
from app.models.product import Product
from app.models.account import Account, AccountType
from app.models.tax import Tax, TaxType
from app.models.company_settings import CompanySettings
from app.utils.exceptions import BusinessRuleError, NotFoundError

# Import para type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.payment import Payment


class AccountDeterminationService:
    """
    Servicio para determinación automática de cuentas contables en facturas
    Utiliza las configuraciones de empresa por defecto del sistema
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._company_settings = None
    
    def get_company_settings(self) -> Optional[CompanySettings]:
        """Obtiene la configuración activa de la empresa (cache)"""
        if self._company_settings is None:
            self._company_settings = self.db.query(CompanySettings).filter(
                CompanySettings.is_active == True
            ).first()
        return self._company_settings
    
    def determine_accounts_for_invoice(self, invoice: Invoice) -> Dict[str, Dict]:
        """
        Determina todas las cuentas contables necesarias para una factura
        
        Returns:
            Dict con estructura:
            {
                'third_party_account': {...},
                'line_accounts': [{...}],
                'tax_accounts': [{...}]
            }
        """
        result = {
            'third_party_account': self._get_third_party_account(invoice),
            'line_accounts': self._get_line_accounts(invoice),
            'tax_accounts': self._get_tax_accounts(invoice)
        }
        
        # Validar que todas las cuentas requeridas fueron encontradas
        self._validate_account_completeness(invoice, result)
        
        return result
    
    def _get_third_party_account(self, invoice: Invoice) -> Dict[str, Union[str, uuid.UUID]]:
        """
        Obtener cuenta del cliente/proveedor
        Jerarquía:
        1. Si se especifica cuenta override en la factura, usar esa
        2. Si no, usar cuenta por defecto del tercero
        3. Si no tiene, usar cuenta por defecto del tipo
        """
        # 1. Verificar override en la factura
        if invoice.third_party_account_id:
            account = self.db.query(Account).filter(Account.id == invoice.third_party_account_id).first()
            if account:
                self._validate_third_party_account(account, invoice.invoice_type)
                return {
                    'account_id': account.id,
                    'account_code': account.code,
                    'account_name': account.name,
                    'source': 'invoice_override'
                }
        
        # 2. Cuenta por defecto del tercero
        third_party = invoice.third_party
        if third_party:
            # Por ahora, buscar cuenta por defecto del tipo (paso 3)
            # TODO: Implementar cuentas por defecto en terceros si es necesario
            pass
          # 3. Cuenta por defecto del tipo
        if invoice.invoice_type in [InvoiceType.CUSTOMER_INVOICE, InvoiceType.CREDIT_NOTE, InvoiceType.DEBIT_NOTE]:
            # Buscar cuenta de clientes (1105, 1140 - Clientes por cobrar)
            account = self._get_default_account_by_pattern(['1105', '1140', '1300'], AccountType.ASSET)
            account_description = "Cuenta de clientes por cobrar"
        else:  # SUPPLIER_INVOICE
            # Buscar cuenta de proveedores (2205 - Proveedores por pagar)
            account = self._get_default_account_by_pattern(['2205', '2200'], AccountType.LIABILITY)
            account_description = "Cuenta de proveedores por pagar"
        
        if not account:
            raise BusinessRuleError(
                f"No se encontró cuenta contable para {account_description}. "
                f"Configure una cuenta adecuada en el plan contable."
            )
        
        return {
            'account_id': account.id,
            'account_code': account.code,
            'account_name': account.name,
            'source': 'default_by_type'
        }
    
    def _get_line_accounts(self, invoice: Invoice) -> List[Dict[str, Union[str, uuid.UUID]]]:
        """
        Obtener cuentas de ingresos/gastos por línea
        Jerarquía para cada línea:
        1. Si línea especifica cuenta override, usar esa
        2. Si tiene producto, usar cuenta del producto según tipo de factura
        3. Si producto no tiene cuenta, usar cuenta de categoría del producto
        4. Si no, usar cuenta por defecto del tipo de factura
        """
        line_accounts = []
        
        for line in invoice.lines:
            account_info = self._determine_line_account(line, invoice.invoice_type)
            line_accounts.append({
                **account_info,
                'line_id': line.id,
                'line_sequence': line.sequence,
                'line_description': line.description
            })
        
        return line_accounts
    
    def _determine_line_account(self, line: InvoiceLine, invoice_type: InvoiceType) -> Dict[str, Union[str, uuid.UUID]]:
        """Determina la cuenta contable para una línea específica"""
        
        # 1. Override en la línea
        if line.account_id:
            account = self.db.query(Account).filter(Account.id == line.account_id).first()
            if account:
                self._validate_line_account(account, invoice_type)
                return {
                    'account_id': account.id,
                    'account_code': account.code,
                    'account_name': account.name,
                    'source': 'line_override'
                }
          # 2. Cuenta del producto
        if line.product_id:
            product = self.db.query(Product).filter(Product.id == line.product_id).first()
            if product:
                account_id = None
                if invoice_type in [InvoiceType.CUSTOMER_INVOICE, InvoiceType.CREDIT_NOTE, InvoiceType.DEBIT_NOTE]:
                    account_id = product.sales_account_id
                else:  # SUPPLIER_INVOICE
                    account_id = product.purchase_account_id
                
                if account_id:
                    account = self.db.query(Account).filter(Account.id == account_id).first()
                    if account:
                        return {
                            'account_id': account.id,
                            'account_code': account.code,
                            'account_name': account.name,
                            'source': 'product_account'
                        }
        
        # 3. Cuenta de categoría del producto (TODO: implementar si es necesario)
          # 4. Cuenta por defecto del tipo - usar configuraciones del sistema
        if invoice_type in [InvoiceType.CUSTOMER_INVOICE, InvoiceType.CREDIT_NOTE, InvoiceType.DEBIT_NOTE]:
            # Buscar cuenta de ingresos por defecto configurada en el sistema
            account = self._get_default_sales_income_account()
            account_description = "ingresos por ventas"
        else:  # SUPPLIER_INVOICE
            # Buscar cuenta de gastos por defecto configurada en el sistema
            account = self._get_default_purchase_expense_account()
            account_description = "gastos por compras"
        
        if not account:
            raise BusinessRuleError(
                f"No se encontró cuenta contable por defecto para {account_description}. "
                f"Configure una cuenta adecuada en el plan contable."
            )
        
        return {
            'account_id': account.id,
            'account_code': account.code,
            'account_name': account.name,
            'source': 'default_by_type'
        }
    
    def _get_tax_accounts(self, invoice: Invoice) -> List[Dict[str, Union[str, uuid.UUID, Decimal]]]:
        """
        Obtener cuentas de impuestos
        Para facturas de venta: usar cuentas de pasivo (impuestos por pagar)
        Para facturas de compra: usar cuentas de activo (impuestos por cobrar) o pasivo (impuestos por pagar)
        """
        tax_accounts = []
        
        if invoice.tax_amount and invoice.tax_amount > 0:
            # Determinar patrón de cuenta según tipo de factura
            if invoice.invoice_type in [InvoiceType.CUSTOMER_INVOICE, InvoiceType.CREDIT_NOTE, InvoiceType.DEBIT_NOTE]:
                # Impuestos sobre ventas: cuentas de pasivo (impuestos por pagar)
                # Patrones más generales para impuestos por pagar
                patterns = ['2408', '2405', '2400', '24', '2105', '2100', '21']
                account_type = AccountType.LIABILITY
                description = "impuestos por pagar"
            else:  # SUPPLIER_INVOICE
                # Impuestos sobre compras: cuentas de activo (impuestos por cobrar/deducibles)
                # Patrones para impuestos deducibles
                patterns = ['1365', '1360', '1300', '13', '2408', '2405', '2400', '24']
                account_type = None  # Permitir cualquier tipo
                description = "impuestos deducibles"
            
            # Buscar cuenta usando patrones generales
            account = self._get_default_account_by_pattern(patterns, account_type)
            
            if not account:
                # Si no encuentra cuenta específica, usar cuenta de IVA general
                iva_patterns = ['IVA', 'IVA_POR_PAGAR', 'IVA_DEDUCIBLE', 'IMPUESTO']
                for pattern in iva_patterns:
                    account = self.db.query(Account).filter(
                        Account.name.ilike(f"%{pattern}%"),
                        Account.is_active == True,
                        Account.allows_movements == True
                    ).first()
                    if account:
                        break
            
            if not account:
                # Como último recurso, usar una cuenta de pasivo genérica
                account = self.db.query(Account).filter(
                    Account.account_type == AccountType.LIABILITY,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).order_by(Account.code).first()
            
            if account:
                tax_accounts.append({
                    'account_id': account.id,
                    'account_code': account.code,
                    'account_name': account.name,
                    'tax_amount': invoice.tax_amount,
                    'source': 'default_tax_account'
                })
            else:
                raise BusinessRuleError(
                    f"No se encontró cuenta contable para {description}. "
                    f"Configure una cuenta apropiada en el plan contable."
                )
        
        return tax_accounts
    
    # Methods specifically needed by InvoiceService
    
    def determine_third_party_account(self, invoice: Invoice) -> Account:
        """
        Determinar cuenta del tercero para el InvoiceService
        Retorna directamente el objeto Account
        """
        account_data = self._get_third_party_account(invoice)
        account = self.db.query(Account).filter(Account.id == account_data['account_id']).first()
        if not account:
            raise BusinessRuleError(f"Account not found: {account_data['account_id']}")
        return account
    
    def determine_line_account(self, line: "InvoiceLine") -> Account:
        """
        Determinar cuenta contable para una línea de factura
        Retorna directamente el objeto Account
        """
        # Obtener la factura para conocer el tipo
        invoice = line.invoice
        if not invoice:
            raise BusinessRuleError("Invoice line must have an associated invoice")
        
        account_data = self._determine_line_account(line, invoice.invoice_type)
        account = self.db.query(Account).filter(Account.id == account_data['account_id']).first()
        if not account:
            raise BusinessRuleError(f"Account not found: {account_data['account_id']}")
        return account
    
    def determine_tax_account(self, tax: "Tax", invoice_type: InvoiceType) -> Account:
        """
        Determinar cuenta contable para un impuesto específico
        Retorna directamente el objeto Account
        """
        # Usar la cuenta contable directamente del impuesto
        if hasattr(tax, 'account_id') and tax.account_id:
            account = self.db.query(Account).filter(Account.id == tax.account_id).first()
            if account:
                return account
        
        # Fallback: buscar cuenta por defecto según el tipo de factura
        if invoice_type == InvoiceType.CUSTOMER_INVOICE:
            # IVA por pagar
            account = self._get_default_account_by_pattern(['2408', '2400'], AccountType.LIABILITY)
        else:  # PURCHASE
            # IVA deducible
            account = self._get_default_account_by_pattern(['1365', '2408'], None)
        
        if not account:
            raise BusinessRuleError(f"No tax account found for invoice type {invoice_type}")
        
        return account
    
    def get_tax_account_by_type(self, tax_type: str, invoice_type: InvoiceType) -> Optional[Account]:
        """
        Obtiene la cuenta específica para un tipo de impuesto según la configuración de empresa
        
        Args:
            tax_type: Tipo de impuesto ('ICMS', 'PIS', 'COFINS', 'IPI', 'ISS', 'CSLL', 'IRPJ')
            invoice_type: Tipo de factura para determinar si es por pagar o deducible
            
        Returns:
            Account específica para el tipo de impuesto o None si no se encuentra
        """
        settings = self.get_company_settings()
        if not settings:
            return None
        
        # Determinar si es impuesto por pagar (ventas) o deducible (compras)
        is_payable = invoice_type in [InvoiceType.CUSTOMER_INVOICE, InvoiceType.CREDIT_NOTE, InvoiceType.DEBIT_NOTE]
        
        # Mapear tipo de impuesto a campo de configuración
        account_field_mapping = {
            'ICMS': 'default_icms_payable_account_id' if is_payable else 'default_icms_deductible_account_id',
            'PIS': 'default_pis_payable_account_id' if is_payable else 'default_pis_deductible_account_id',
            'COFINS': 'default_cofins_payable_account_id' if is_payable else 'default_cofins_deductible_account_id',
            'IPI': 'default_ipi_payable_account_id' if is_payable else 'default_ipi_deductible_account_id',
            'ISS': 'default_iss_payable_account_id' if is_payable else None,  # ISS solo por pagar
            'CSLL': 'default_csll_payable_account_id' if is_payable else None,  # CSLL solo por pagar
            'IRPJ': 'default_irpj_payable_account_id' if is_payable else None,  # IRPJ solo por pagar
        }
        
        # Obtener el campo correspondiente
        account_field = account_field_mapping.get(tax_type.upper())
        if not account_field:
            return None
        
        # Obtener el ID de la cuenta desde la configuración
        account_id = getattr(settings, account_field, None)
        if not account_id:
            return None
        
        # Buscar y validar la cuenta
        account = self.db.query(Account).filter(
            Account.id == account_id,
            Account.is_active == True,
            Account.allows_movements == True
        ).first()
        
        return account

    def determine_accounts_for_payment(self, payment: "Payment") -> Dict[str, Dict]:
        """
        Determina todas las cuentas contables necesarias para un pago
        
        Args:
            payment: El pago para el cual determinar las cuentas
            
        Returns:
            Dict con estructura:
            {
                'bank_cash_account': {...},
                'third_party_account': {...},
                'fee_accounts': [{...}],
                'exchange_accounts': [{...}],
                'tax_accounts': [{...}]
            }
        """
        from app.models.payment import PaymentType
        
        result = {
            'bank_cash_account': None,
            'third_party_account': None,
            'fee_accounts': [],
            'exchange_accounts': [],
            'tax_accounts': []
        }
        
        # Determinar cuenta bancaria/efectivo
        if payment.payment_method in ['BANK_TRANSFER', 'CHECK', 'DEBIT_CARD']:
            bank_account = self._get_default_bank_account()
            if bank_account:
                result['bank_cash_account'] = {
                    'account_id': bank_account.id,
                    'account_code': bank_account.code,
                    'account_name': bank_account.name,
                    'source': 'default_bank_account'
                }
        else:  # CASH, CREDIT_CARD, etc.
            cash_account = self._get_default_cash_account()
            if cash_account:
                result['bank_cash_account'] = {
                    'account_id': cash_account.id,
                    'account_code': cash_account.code,
                    'account_name': cash_account.name,
                    'source': 'default_cash_account'
                }
        
        # Determinar cuenta de tercero
        if payment.payment_type == PaymentType.CUSTOMER_PAYMENT:
            # Cuenta de clientes por cobrar
            account = self._get_default_customer_receivable_account()
        else:  # SUPPLIER_PAYMENT
            # Cuenta de proveedores por pagar
            account = self._get_default_supplier_payable_account()
        
        if account:
            result['third_party_account'] = {
                'account_id': account.id,
                'account_code': account.code,
                'account_name': account.name,
                'source': 'default_by_payment_type'
            }
        
        # Validar que se encontraron las cuentas básicas
        if not result['bank_cash_account']:
            raise BusinessRuleError("No se pudo determinar cuenta bancaria/efectivo para el pago")
        
        if not result['third_party_account']:
            raise BusinessRuleError("No se pudo determinar cuenta de tercero para el pago")
        
        return result

    def get_payment_journal_entry_preview(self, payment: "Payment") -> List[Dict[str, Union[str, uuid.UUID, Decimal]]]:
        """
        Genera preview de las líneas del asiento contable que se creará para un pago
        
        Args:
            payment: El pago para el cual generar el preview
            
        Returns:
            Lista de diccionarios con las líneas del asiento
        """
        from app.models.payment import PaymentType
        
        accounts = self.determine_accounts_for_payment(payment)
        lines = []
        
        bank_cash_account = accounts['bank_cash_account']
        third_party_account = accounts['third_party_account']
        
        if payment.payment_type == PaymentType.CUSTOMER_PAYMENT:
            # Pago de cliente: DEBE: Banco/Efectivo, HABER: Cliente
            lines.append({
                'account_id': bank_cash_account['account_id'],
                'account_code': bank_cash_account['account_code'],
                'account_name': bank_cash_account['account_name'],
                'description': f"Pago {payment.number} - {payment.third_party.name if payment.third_party else 'Desconocido'}",
                'debit_amount': payment.amount,
                'credit_amount': Decimal('0'),
                'third_party_id': None,
                'product_id': None,
                'cost_center_id': None,
                'source': bank_cash_account['source']
            })
            
            lines.append({
                'account_id': third_party_account['account_id'],
                'account_code': third_party_account['account_code'],
                'account_name': third_party_account['account_name'],
                'description': f"Pago {payment.number} - {payment.third_party.name if payment.third_party else 'Desconocido'}",
                'debit_amount': Decimal('0'),
                'credit_amount': payment.amount,
                'third_party_id': payment.third_party_id,
                'product_id': None,
                'cost_center_id': None,
                'source': third_party_account['source']
            })
            
        else:  # SUPPLIER_PAYMENT
            # Pago a proveedor: DEBE: Proveedor, HABER: Banco/Efectivo
            lines.append({
                'account_id': third_party_account['account_id'],
                'account_code': third_party_account['account_code'],
                'account_name': third_party_account['account_name'],
                'description': f"Pago {payment.number} - {payment.third_party.name if payment.third_party else 'Desconocido'}",
                'debit_amount': payment.amount,
                'credit_amount': Decimal('0'),
                'third_party_id': payment.third_party_id,
                'product_id': None,
                'cost_center_id': None,
                'source': third_party_account['source']
            })
            
            lines.append({
                'account_id': bank_cash_account['account_id'],
                'account_code': bank_cash_account['account_code'],
                'account_name': bank_cash_account['account_name'],
                'description': f"Pago {payment.number} - {payment.third_party.name if payment.third_party else 'Desconocido'}",
                'debit_amount': Decimal('0'),
                'credit_amount': payment.amount,
                'third_party_id': None,
                'product_id': None,
                'cost_center_id': None,
                'source': bank_cash_account['source']
            })
        
        return lines

    def get_invoice_journal_entry_preview(self, invoice: "Invoice") -> List[Dict[str, Union[str, uuid.UUID, Decimal]]]:
        """
        Genera preview de las líneas del asiento contable que se creará para una factura
        (usa el método existente pero lo renombra para consistencia con la API)
        
        Args:
            invoice: La factura para la cual generar el preview
            
        Returns:
            Lista de diccionarios con las líneas del asiento
        """
        return self.get_journal_entry_lines_preview(invoice)

    def _get_default_bank_account(self) -> Optional[Account]:
        """Obtiene la cuenta bancaria por defecto"""
        settings = self.get_company_settings()
        if settings and settings.default_bank_account_id:
            account = self.db.query(Account).filter(
                Account.id == settings.default_bank_account_id,
                Account.is_active == True,
                Account.allows_movements == True
            ).first()
            if account:
                return account
        
        # Fallback: buscar primera cuenta bancaria activa
        account = self.db.query(Account).filter(
            Account.code.like('11%'),  # Cuentas de activo corriente
            Account.name.ilike('%banco%'),
            Account.is_active == True,
            Account.allows_movements == True
        ).first()
        
        return account

    def _get_default_cash_account(self) -> Optional[Account]:
        """Obtiene la cuenta de efectivo por defecto"""
        settings = self.get_company_settings()
        if settings and settings.default_cash_account_id:
            account = self.db.query(Account).filter(
                Account.id == settings.default_cash_account_id,
                Account.is_active == True,
                Account.allows_movements == True
            ).first()
            if account:
                return account
        
        # Fallback: buscar primera cuenta de efectivo activa
        account = self.db.query(Account).filter(
            Account.code.like('11%'),  # Cuentas de activo corriente
            Account.name.ilike('%efectivo%'),
            Account.is_active == True,
            Account.allows_movements == True
        ).first()
        
        return account

    def _get_default_sales_income_account(self) -> Optional[Account]:
        """Obtiene la cuenta por defecto para ingresos por ventas del sistema"""
        # 1. Primero intentar obtener de la configuración de empresa
        settings = self.get_company_settings()
        if settings and settings.default_sales_income_account_id:
            account = self.db.query(Account).filter(
                Account.id == settings.default_sales_income_account_id,
                Account.is_active == True,
                Account.allows_movements == True
            ).first()
            
            if account:
                return account
        
        # 2. Si no está configurado, buscar usando patrones comunes
        # Patrones típicos para ingresos por ventas en diferentes países
        patterns = ['411', '4100', '4110', '4111', '4135', '41100', '41110']
        
        account = self._get_default_account_by_pattern(patterns, AccountType.INCOME)
        if account:
            return account
        
        # 3. Como último recurso, buscar la primera cuenta de ingresos activa
        account = self.db.query(Account).filter(
            Account.account_type == AccountType.INCOME,
            Account.is_active == True,
            Account.allows_movements == True
        ).order_by(Account.code).first()
        
        return account
    
    def _get_default_purchase_expense_account(self) -> Optional[Account]:
        """Obtiene la cuenta por defecto para gastos por compras del sistema"""
        # 1. Primero intentar obtener de la configuración de empresa
        settings = self.get_company_settings()
        if settings and settings.default_purchase_expense_account_id:
            account = self.db.query(Account).filter(
                Account.id == settings.default_purchase_expense_account_id,
                Account.is_active == True,
                Account.allows_movements == True
            ).first()
            
            if account:
                return account
        
        # 2. Si no está configurado, buscar usando patrones comunes
        # Patrones típicos para gastos por compras en diferentes países
        patterns = ['511', '5100', '5110', '5111', '51100', '51110']
        
        account = self._get_default_account_by_pattern(patterns, AccountType.EXPENSE)
        if account:
            return account
        
        # 3. Como último recurso, buscar la primera cuenta de gastos activa
        account = self.db.query(Account).filter(
            Account.account_type == AccountType.EXPENSE,
            Account.is_active == True,
            Account.allows_movements == True
        ).order_by(Account.code).first()
        
        return account
    
    def _get_default_customer_receivable_account(self) -> Optional[Account]:
        """Obtiene la cuenta por defecto para clientes por cobrar"""
        settings = self.get_company_settings()
        if settings and settings.default_customer_receivable_account_id:
            account = self.db.query(Account).filter(
                Account.id == settings.default_customer_receivable_account_id,
                Account.is_active == True
            ).first()
            if account:
                return account
        
        # Fallback: buscar primera cuenta de activo corriente para clientes
        account = self.db.query(Account).filter(
            Account.account_type == AccountType.ASSET,
            Account.is_active == True,
            Account.allows_movements == True
        ).order_by(Account.code).first()
        
        return account

    def _get_default_supplier_payable_account(self) -> Optional[Account]:
        """Obtiene la cuenta por defecto para proveedores por pagar"""
        settings = self.get_company_settings()
        if settings and settings.default_supplier_payable_account_id:
            account = self.db.query(Account).filter(
                Account.id == settings.default_supplier_payable_account_id,
                Account.is_active == True
            ).first()
            if account:
                return account
        
        # Fallback: buscar primera cuenta de pasivo corriente para proveedores
        account = self.db.query(Account).filter(
            Account.account_type == AccountType.LIABILITY,
            Account.is_active == True,
            Account.allows_movements == True
        ).order_by(Account.code).first()
        
        return account

    def _get_default_tax_account_for_invoice_type(self, invoice_type: InvoiceType) -> Optional[Account]:
        """
        Obtiene la cuenta por defecto para impuestos según el tipo de factura
        usando la configuración de empresa
        """
        settings = self.get_company_settings()
        if not settings:
            return None
        
        # 1. Usar cuenta específica según tipo de factura
        if invoice_type in [InvoiceType.CUSTOMER_INVOICE, InvoiceType.CREDIT_NOTE, InvoiceType.DEBIT_NOTE]:
            # Impuestos sobre ventas: usar cuenta de impuestos por pagar
            if settings.default_sales_tax_payable_account_id:
                account = self.db.query(Account).filter(
                    Account.id == settings.default_sales_tax_payable_account_id,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).first()
                if account:
                    return account
        else:  # SUPPLIER_INVOICE
            # Impuestos sobre compras: usar cuenta de impuestos deducibles
            if settings.default_purchase_tax_deductible_account_id:
                account = self.db.query(Account).filter(
                    Account.id == settings.default_purchase_tax_deductible_account_id,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).first()
                if account:
                    return account
        
        # 2. Usar cuenta genérica de impuestos como fallback
        if settings.default_tax_account_id:
            account = self.db.query(Account).filter(
                Account.id == settings.default_tax_account_id,
                Account.is_active == True,
                Account.allows_movements == True
            ).first()
            if account:
                return account
        
        return None
    
    def _get_default_account_by_pattern(self, code_patterns: List[str], account_type: Optional[AccountType]) -> Optional[Account]:
        """
        Busca una cuenta por patrones de código y tipo con lógica mejorada
        """
        query = self.db.query(Account).filter(
            Account.is_active == True, 
            Account.allows_movements == True
        )
        
        if account_type:
            query = query.filter(Account.account_type == account_type)
        
        # Buscar por patrones de código en orden de prioridad
        for pattern in code_patterns:
            # Primero buscar coincidencia exacta
            account = query.filter(Account.code == pattern).first()
            if account:
                return account
            
            # Luego buscar que comience con el patrón
            account = query.filter(Account.code.like(f"{pattern}%")).first()
            if account:
                return account
        
        # Si no encuentra nada con patrones específicos, buscar la primera cuenta del tipo
        if account_type:
            account = query.filter(Account.account_type == account_type).order_by(Account.code).first()
            if account:
                return account
        
        return None
    
    def _validate_third_party_account(self, account: Account, invoice_type: InvoiceType) -> None:
        """Valida que la cuenta de tercero sea compatible con el tipo de factura"""
        if invoice_type == InvoiceType.CUSTOMER_INVOICE:
            # Para ventas: cuentas de activo (clientes por cobrar)
            allowed_types = [AccountType.ASSET]
        else:  # PURCHASE
            # Para compras: cuentas de pasivo (proveedores por pagar)
            allowed_types = [AccountType.LIABILITY]
        
        if account.account_type not in allowed_types:
            raise BusinessRuleError(
                f"La cuenta {account.code} - {account.name} no es válida para facturas de tipo "
                f"{'venta' if invoice_type == InvoiceType.CUSTOMER_INVOICE else 'compra'}. "
                f"Debe ser una cuenta de tipo {', '.join([t.value for t in allowed_types])}."
            )
    
    def _validate_line_account(self, account: Account, invoice_type: InvoiceType) -> None:
        """Valida que la cuenta de línea sea compatible con el tipo de factura"""
        if invoice_type == InvoiceType.CUSTOMER_INVOICE:
            # Para ventas: cuentas de ingresos
            allowed_types = [AccountType.INCOME]
        else:  # PURCHASE
            # Para compras: cuentas de gastos o activos
            allowed_types = [AccountType.EXPENSE, AccountType.ASSET]
        
        if account.account_type not in allowed_types:
            raise BusinessRuleError(
                f"La cuenta {account.code} - {account.name} no es válida para líneas de facturas de tipo "
                f"{'venta' if invoice_type == InvoiceType.CUSTOMER_INVOICE else 'compra'}. "
                f"Debe ser una cuenta de tipo {', '.join([t.value for t in allowed_types])}."
            )
    
    def _validate_account_completeness(self, invoice: Invoice, accounts: Dict) -> None:
        """Valida que se hayan encontrado todas las cuentas necesarias"""
        errors = []
        
        # Validar cuenta de tercero
        if not accounts['third_party_account']:
            errors.append("No se encontró cuenta para el cliente/proveedor")
        
        # Validar cuentas de líneas
        if len(accounts['line_accounts']) != len(invoice.lines):
            errors.append("No se pudieron determinar todas las cuentas de líneas")
        
        # Validar cuentas de impuestos si hay impuestos
        if invoice.tax_amount > 0 and not accounts['tax_accounts']:
            errors.append("No se encontraron cuentas para los impuestos")
        
        if errors:
            raise BusinessRuleError(
                f"Error en determinación de cuentas: {'; '.join(errors)}"
            )
    
    def get_journal_entry_lines_preview(self, invoice: Invoice) -> List[Dict]:
        """
        Genera preview de las líneas del asiento contable que se creará
        """
        accounts = self.determine_accounts_for_invoice(invoice)
        lines = []
        
        # Línea del tercero (cliente/proveedor)
        third_party_account = accounts['third_party_account']
        
        if invoice.invoice_type == InvoiceType.CUSTOMER_INVOICE:
            # DÉBITO: Cliente por el total
            lines.append({
                'account_id': third_party_account['account_id'],
                'account_code': third_party_account['account_code'],
                'account_name': third_party_account['account_name'],
                'description': f"Factura {invoice.number} - {invoice.third_party.name}",
                'debit_amount': invoice.total_amount,
                'credit_amount': Decimal('0'),
                'third_party_id': invoice.third_party_id
            })
        else:  # PURCHASE
            # CRÉDITO: Proveedor por el total
            lines.append({
                'account_id': third_party_account['account_id'],
                'account_code': third_party_account['account_code'],
                'account_name': third_party_account['account_name'],
                'description': f"Factura {invoice.number} - {invoice.third_party.name}",
                'debit_amount': Decimal('0'),
                'credit_amount': invoice.total_amount,
                'third_party_id': invoice.third_party_id
            })
        
        # Líneas de productos/servicios
        for i, (line, line_account) in enumerate(zip(invoice.lines, accounts['line_accounts'])):
            line_total = line.subtotal - line.discount_amount  # Sin impuestos
            
            if invoice.invoice_type == InvoiceType.CUSTOMER_INVOICE:
                # CRÉDITO: Ingresos
                lines.append({
                    'account_id': line_account['account_id'],
                    'account_code': line_account['account_code'],
                    'account_name': line_account['account_name'],
                    'description': line.description,
                    'debit_amount': Decimal('0'),
                    'credit_amount': line_total,
                    'product_id': line.product_id,
                    'cost_center_id': line.cost_center_id
                })
            else:  # PURCHASE
                # DÉBITO: Gastos
                lines.append({
                    'account_id': line_account['account_id'],
                    'account_code': line_account['account_code'],
                    'account_name': line_account['account_name'],
                    'description': line.description,
                    'debit_amount': line_total,
                    'credit_amount': Decimal('0'),
                    'product_id': line.product_id,
                    'cost_center_id': line.cost_center_id
                })
        
        # Líneas de impuestos
        for tax_account in accounts['tax_accounts']:
            if invoice.invoice_type == InvoiceType.CUSTOMER_INVOICE:
                # CRÉDITO: IVA por pagar
                lines.append({
                    'account_id': tax_account['account_id'],
                    'account_code': tax_account['account_code'],
                    'account_name': tax_account['account_name'],
                    'description': f"IVA Factura {invoice.number}",
                    'debit_amount': Decimal('0'),
                    'credit_amount': tax_account['tax_amount']
                })
            else:  # PURCHASE
                # DÉBITO: IVA deducible
                lines.append({
                    'account_id': tax_account['account_id'],
                    'account_code': tax_account['account_code'],
                    'account_name': tax_account['account_name'],
                    'description': f"IVA Factura {invoice.number}",
                    'debit_amount': tax_account['tax_amount'],
                    'credit_amount': Decimal('0')
                })
        
        return lines
