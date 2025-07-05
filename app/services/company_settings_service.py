"""
Service for managing company settings and default account configurations
"""
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_

from app.models.company_settings import CompanySettings
from app.models.account import Account, AccountType, AccountCategory
from app.models.third_party import ThirdParty
from app.schemas.company_settings import (
    CompanySettingsCreate, CompanySettingsUpdate, CompanySettingsResponse,
    DefaultAccountsInfo, AccountSuggestion
)
from app.utils.exceptions import NotFoundError, BusinessRuleError
import logging

logger = logging.getLogger(__name__)


class CompanySettingsService:
    """Servicio para gestionar configuración de empresa y cuentas por defecto"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_company_settings(self) -> Optional[CompanySettingsResponse]:
        """Obtiene la configuración activa de la empresa"""
        # Get active settings with relations loaded
        settings_result = await self.db.execute(
            select(CompanySettings).options(
                selectinload(CompanySettings.default_customer_receivable_account),
                selectinload(CompanySettings.default_supplier_payable_account),
                selectinload(CompanySettings.bank_suspense_account),
                selectinload(CompanySettings.internal_transfer_account),
                selectinload(CompanySettings.deferred_expense_account),
                selectinload(CompanySettings.deferred_revenue_account),
                selectinload(CompanySettings.early_payment_discount_gain_account),
                selectinload(CompanySettings.early_payment_discount_loss_account)
            ).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            return None
        
        return self._build_settings_response(settings)
    
    async def create_company_settings(
        self, 
        settings_data: CompanySettingsCreate,
        created_by_id: uuid.UUID
    ) -> CompanySettingsResponse:
        """Crea configuración de empresa"""
        
        # Verificar que no existe configuración activa
        existing_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            raise BusinessRuleError("Ya existe configuración activa de empresa")
        
        # Validar cuentas referenciadas
        await self._validate_account_references(settings_data)
        
        # Crear configuración
        settings = CompanySettings(
            **settings_data.model_dump(exclude_unset=True),
            created_by_id=created_by_id
        )
        
        self.db.add(settings)
        await self.db.flush()
        await self.db.commit()
        
        # Reload with relations
        await self.db.refresh(settings, [
            'default_customer_receivable_account',
            'default_supplier_payable_account',
            'bank_suspense_account',
            'internal_transfer_account',
            'deferred_expense_account',
            'deferred_revenue_account',
            'early_payment_discount_gain_account',
            'early_payment_discount_loss_account'
        ])
        
        logger.info(f"Created company settings: {settings.company_name}")
        return self._build_settings_response(settings)
    
    async def update_company_settings(
        self, 
        settings_data: CompanySettingsUpdate,
        updated_by_id: uuid.UUID
    ) -> CompanySettingsResponse:
        """Actualiza configuración de empresa"""
        
        logger.info("=== SERVICE: Iniciando actualización de configuración ===")
        logger.info(f"Datos recibidos en el servicio: {settings_data.model_dump()}")
        
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            raise NotFoundError("No se encontró configuración de empresa")
        
        logger.info(f"Configuración actual antes de actualizar: {settings.company_name}")
        logger.info(f"ID de configuración: {settings.id}")
        
        # Validar cuentas referenciadas
        await self._validate_account_references(settings_data)
        
        # Actualizar campos
        update_data = settings_data.model_dump(exclude_unset=True)
        logger.info(f"Campos a actualizar: {update_data}")
        
        for field, value in update_data.items():
            if hasattr(settings, field):
                old_value = getattr(settings, field)
                setattr(settings, field, value)
                logger.info(f"Actualizando {field}: {old_value} -> {value}")
        
        self.db.add(settings)
        await self.db.flush()
        logger.info("Datos enviados a la base de datos (flush realizado)")
        
        await self.db.commit()
        logger.info("Commit realizado - cambios persistidos")
        
        # Reload with relations
        await self.db.refresh(settings, [
            'default_customer_receivable_account',
            'default_supplier_payable_account',
            'bank_suspense_account',
            'internal_transfer_account',
            'deferred_expense_account',
            'deferred_revenue_account',
            'early_payment_discount_gain_account',
            'early_payment_discount_loss_account'
        ])
        
        logger.info(f"Configuración después del refresh:")
        logger.info(f"  - default_customer_receivable_account_id: {settings.default_customer_receivable_account_id}")
        logger.info(f"  - default_supplier_payable_account_id: {settings.default_supplier_payable_account_id}")
        logger.info(f"  - bank_suspense_account_id: {settings.bank_suspense_account_id}")
        
        response = self._build_settings_response(settings)
        logger.info("=== SERVICE: Finalizada actualización de configuración ===")
        return response
    
    async def get_or_create_default_settings(self) -> CompanySettings:
        """Obtiene o crea configuración por defecto"""
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            # Create default settings
            settings = CompanySettings(
                company_name="Mi Empresa",
                tax_id="12345678901",
                currency_code="USD",
                is_active=True
            )
            self.db.add(settings)
            await self.db.commit()
            logger.info("Created default company settings")
        
        return settings
    
    async def get_default_accounts_info(self) -> DefaultAccountsInfo:
        """Obtiene información de cuentas disponibles para configurar como defecto"""
        
        # Obtener cuentas disponibles por tipo
        receivable_accounts = await self._get_available_receivable_accounts()
        payable_accounts = await self._get_available_payable_accounts()
        bank_accounts = await self._get_available_bank_accounts()
        expense_accounts = await self._get_available_expense_accounts()
        revenue_accounts = await self._get_available_revenue_accounts()
        
        # Configuración actual
        current_settings = await self.get_company_settings()
        
        # Determinar estado de configuración
        has_receivable = bool(current_settings and current_settings.default_customer_receivable_account_id)
        has_payable = bool(current_settings and current_settings.default_supplier_payable_account_id)
        has_bank_suspense = bool(current_settings and current_settings.bank_suspense_account_id)
        has_internal_transfer = bool(current_settings and current_settings.internal_transfer_account_id)
        has_deferred_expense = bool(current_settings and current_settings.deferred_expense_account_id)
        has_deferred_revenue = bool(current_settings and current_settings.deferred_revenue_account_id)
        has_early_payment = bool(current_settings and (
            current_settings.early_payment_discount_gain_account_id or 
            current_settings.early_payment_discount_loss_account_id
        ))
        
        # Determinar cuentas faltantes y recomendaciones
        missing_accounts = []
        recommendations = []
        
        if not has_receivable:
            missing_accounts.append("Cuenta por cobrar por defecto")
            recommendations.append("Configurar una cuenta de activo (13xx) como cuenta por cobrar por defecto")
        
        if not has_payable:
            missing_accounts.append("Cuenta por pagar por defecto")
            recommendations.append("Configurar una cuenta de pasivo (22xx) como cuenta por pagar por defecto")
        
        if not has_bank_suspense:
            missing_accounts.append("Cuenta transitoria bancaria")
            recommendations.append("Configurar una cuenta bancaria como cuenta transitoria")
        
        return DefaultAccountsInfo(
            available_receivable_accounts=receivable_accounts,
            available_payable_accounts=payable_accounts,
            available_bank_accounts=bank_accounts,
            available_expense_accounts=expense_accounts,
            available_revenue_accounts=revenue_accounts,
            current_settings=current_settings,
            has_receivable_account=has_receivable,
            has_payable_account=has_payable,
            has_bank_suspense_account=has_bank_suspense,
            has_internal_transfer_account=has_internal_transfer,
            has_deferred_expense_account=has_deferred_expense,
            has_deferred_revenue_account=has_deferred_revenue,
            has_early_payment_accounts=has_early_payment,
            missing_accounts=missing_accounts,
            recommendations=recommendations
        )
    
    # ========================
    # MÉTODOS PRIVADOS
    # ========================
    
    def _build_settings_response(self, settings: CompanySettings) -> CompanySettingsResponse:
        """Construye la respuesta con información de las cuentas"""
        return CompanySettingsResponse(
            id=settings.id,
            company_name=settings.company_name,
            tax_id=getattr(settings, 'tax_id', ''),
            currency_code=getattr(settings, 'currency_code', 'COP'),
            
            # IDs de cuentas
            default_customer_receivable_account_id=settings.default_customer_receivable_account_id,
            default_supplier_payable_account_id=settings.default_supplier_payable_account_id,
            bank_suspense_account_id=settings.bank_suspense_account_id,
            internal_transfer_account_id=settings.internal_transfer_account_id,
            deferred_expense_account_id=settings.deferred_expense_account_id,
            deferred_expense_journal_id=getattr(settings, 'deferred_expense_journal_id', None),
            deferred_expense_months=getattr(settings, 'deferred_expense_months', 12),
            deferred_revenue_account_id=settings.deferred_revenue_account_id,
            deferred_revenue_journal_id=getattr(settings, 'deferred_revenue_journal_id', None),
            deferred_revenue_months=getattr(settings, 'deferred_revenue_months', 12),
            invoice_line_discount_same_account=getattr(settings, 'invoice_line_discount_same_account', True),
            early_payment_discount_gain_account_id=settings.early_payment_discount_gain_account_id,
            early_payment_discount_loss_account_id=settings.early_payment_discount_loss_account_id,
            validate_invoice_on_posting=getattr(settings, 'validate_invoice_on_posting', True),
            deferred_generation_method=getattr(settings, 'deferred_generation_method', 'on_invoice_validation'),
            is_active=settings.is_active,
            notes=getattr(settings, 'notes', ''),
            
            # Nombres de cuentas
            default_customer_receivable_account_name=settings.default_customer_receivable_account.name if settings.default_customer_receivable_account else None,
            default_supplier_payable_account_name=settings.default_supplier_payable_account.name if settings.default_supplier_payable_account else None,
            bank_suspense_account_name=settings.bank_suspense_account.name if settings.bank_suspense_account else None,
            internal_transfer_account_name=settings.internal_transfer_account.name if settings.internal_transfer_account else None,
            deferred_expense_account_name=settings.deferred_expense_account.name if settings.deferred_expense_account else None,
            deferred_revenue_account_name=settings.deferred_revenue_account.name if settings.deferred_revenue_account else None,
            early_payment_discount_gain_account_name=settings.early_payment_discount_gain_account.name if settings.early_payment_discount_gain_account else None,
            early_payment_discount_loss_account_name=settings.early_payment_discount_loss_account.name if settings.early_payment_discount_loss_account else None,
            
            # Flags de configuración
            has_customer_receivable_configured=bool(settings.default_customer_receivable_account_id),
            has_supplier_payable_configured=bool(settings.default_supplier_payable_account_id),
            has_deferred_accounts_configured=bool(settings.deferred_expense_account_id or settings.deferred_revenue_account_id)
        )
    
    async def _validate_account_references(self, settings_data) -> None:
        """Valida que las cuentas referenciadas existan y sean activas"""
        account_fields = [
            'default_customer_receivable_account_id',
            'default_supplier_payable_account_id',
            'bank_suspense_account_id',
            'internal_transfer_account_id',
            'deferred_expense_account_id',
            'deferred_revenue_account_id',
            'early_payment_discount_gain_account_id',
            'early_payment_discount_loss_account_id'
        ]
        
        for field in account_fields:
            account_id = getattr(settings_data, field, None)
            if account_id:
                account_result = await self.db.execute(
                    select(Account).where(
                        and_(
                            Account.id == account_id,
                            Account.is_active == True
                        )
                    )
                )
                account = account_result.scalar_one_or_none()
                
                if not account:
                    raise BusinessRuleError(f"Account with ID {account_id} not found or inactive for field {field}")
    
    async def _get_available_receivable_accounts(self) -> List[Dict[str, Any]]:
        """Obtiene cuentas disponibles para usar como cuentas por cobrar"""
        accounts_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.ASSET,
                    or_(
                        Account.code.like('13%'),
                        Account.name.ilike('%cobrar%'),
                        Account.name.ilike('%cliente%')
                    ),
                    Account.is_active == True
                )
            ).order_by(Account.code)
        )
        accounts = accounts_result.scalars().all()
        
        return [
            {
                "id": str(acc.id),
                "code": acc.code,
                "name": acc.name,
                "account_type": acc.account_type.value
            }
            for acc in accounts
        ]
    
    async def _get_available_payable_accounts(self) -> List[Dict[str, Any]]:
        """Obtiene cuentas disponibles para usar como cuentas por pagar"""
        accounts_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.LIABILITY,
                    or_(
                        Account.code.like('22%'),
                        Account.name.ilike('%pagar%'),
                        Account.name.ilike('%proveedor%')
                    ),
                    Account.is_active == True
                )
            ).order_by(Account.code)
        )
        accounts = accounts_result.scalars().all()
        
        return [
            {
                "id": str(acc.id),
                "code": acc.code,
                "name": acc.name,
                "account_type": acc.account_type.value
            }
            for acc in accounts
        ]
    
    async def _get_available_bank_accounts(self) -> List[Dict[str, Any]]:
        """Obtiene cuentas bancarias disponibles"""
        accounts_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.ASSET,
                    or_(
                        Account.code.like('11%'),
                        Account.name.ilike('%banco%'),
                        Account.name.ilike('%caja%')
                    ),
                    Account.is_active == True
                )
            ).order_by(Account.code)
        )
        accounts = accounts_result.scalars().all()
        
        return [
            {
                "id": str(acc.id),
                "code": acc.code,
                "name": acc.name,
                "account_type": acc.account_type.value
            }
            for acc in accounts
        ]
    
    async def _get_available_expense_accounts(self) -> List[Dict[str, Any]]:
        """Obtiene cuentas de gastos disponibles"""
        accounts_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.EXPENSE,
                    Account.is_active == True
                )
            ).order_by(Account.code)
        )
        accounts = accounts_result.scalars().all()
        
        return [
            {
                "id": str(acc.id),
                "code": acc.code,
                "name": acc.name,
                "account_type": acc.account_type.value
            }
            for acc in accounts
        ]
    
    async def _get_available_revenue_accounts(self) -> List[Dict[str, Any]]:
        """Obtiene cuentas de ingresos disponibles"""
        accounts_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.INCOME,
                    Account.is_active == True
                )
            ).order_by(Account.code)
        )
        accounts = accounts_result.scalars().all()
        
        return [
            {
                "id": str(acc.id),
                "code": acc.code,
                "name": acc.name,
                "account_type": acc.account_type.value
            }
            for acc in accounts
        ]
    
    # Additional methods for payment flow integration
    async def get_customer_receivable_account(self, third_party=None) -> Optional[Account]:
        """Get the appropriate receivable account for a customer"""
        # If third party has specific account configured
        if third_party and hasattr(third_party, 'receivable_account_id') and third_party.receivable_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == third_party.receivable_account_id,
                        Account.is_active == True
                    )
                )
            )
            account = account_result.scalar_one_or_none()
            if account:
                return account
        
        # Use company default
        settings = await self.get_company_settings()
        if settings and settings.default_customer_receivable_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == settings.default_customer_receivable_account_id,
                        Account.is_active == True
                    )
                )
            )
            return account_result.scalar_one_or_none()
        
        # Fallback: find any receivable account
        account_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.ASSET,
                    or_(
                        Account.code.like('13%'),
                        Account.name.ilike('%cobrar%'),
                        Account.name.ilike('%cliente%')
                    ),
                    Account.is_active == True
                )
            ).order_by(Account.code).limit(1)
        )
        return account_result.scalar_one_or_none()
    
    async def get_supplier_payable_account(self, third_party=None) -> Optional[Account]:
        """Get the appropriate payable account for a supplier"""
        # If third party has specific account configured
        if third_party and hasattr(third_party, 'payable_account_id') and third_party.payable_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == third_party.payable_account_id,
                        Account.is_active == True
                    )
                )
            )
            account = account_result.scalar_one_or_none()
            if account:
                return account
        
        # Use company default
        settings = await self.get_company_settings()
        if settings and settings.default_supplier_payable_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == settings.default_supplier_payable_account_id,
                        Account.is_active == True
                    )
                )
            )
            return account_result.scalar_one_or_none()
        
        # Fallback: find any payable account
        account_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.LIABILITY,
                    or_(
                        Account.code.like('22%'),
                        Account.name.ilike('%pagar%'),
                        Account.name.ilike('%proveedor%')
                    ),
                    Account.is_active == True
                )
            ).order_by(Account.code).limit(1)
        )
        return account_result.scalar_one_or_none()
    
    async def get_bank_suspense_account(self) -> Optional[Account]:
        """Get the bank suspense account"""
        settings = await self.get_company_settings()
        if settings and settings.bank_suspense_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == settings.bank_suspense_account_id,
                        Account.is_active == True
                    )
                )
            )
            return account_result.scalar_one_or_none()
        
        # Fallback: find any bank account that could serve as suspense
        account_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.ASSET,
                    or_(
                        Account.name.ilike('%banco%'),
                        Account.name.ilike('%suspense%'),
                        Account.name.ilike('%transitoria%')
                    ),
                    Account.is_active == True
                )
            ).order_by(Account.code).limit(1)
        )
        return account_result.scalar_one_or_none()
    
    async def get_account_suggestions(self, account_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene sugerencias de cuentas basadas en el tipo solicitado"""
        from app.models.account import AccountType, AccountCategory
        
        suggestions = []
        
        if not account_type or account_type == "receivable":
            # Sugerencias para cuentas por cobrar
            receivable_accounts = await self._get_available_receivable_accounts()
            for acc in receivable_accounts[:5]:  # Top 5 suggestions
                suggestions.append({
                    "id": acc["id"],
                    "code": acc["code"],
                    "name": acc["name"],
                    "account_type": acc["account_type"],
                    "account_category": "CUENTA_POR_COBRAR",
                    "score": 0.9 if "13" in acc["code"] else 0.7,
                    "reason": "Cuenta de activo apropiada para cuentas por cobrar de clientes"
                })
        
        if not account_type or account_type == "payable":
            # Sugerencias para cuentas por pagar
            payable_accounts = await self._get_available_payable_accounts()
            for acc in payable_accounts[:5]:
                suggestions.append({
                    "id": acc["id"],
                    "code": acc["code"],
                    "name": acc["name"],
                    "account_type": acc["account_type"],
                    "account_category": "CUENTA_POR_PAGAR",
                    "score": 0.9 if "22" in acc["code"] else 0.7,
                    "reason": "Cuenta de pasivo apropiada para cuentas por pagar de proveedores"
                })
        
        if not account_type or account_type == "bank":
            # Sugerencias para cuentas bancarias
            bank_accounts = await self._get_available_bank_accounts()
            for acc in bank_accounts[:5]:
                suggestions.append({
                    "id": acc["id"],
                    "code": acc["code"],
                    "name": acc["name"],
                    "account_type": acc["account_type"],
                    "account_category": "BANCO",
                    "score": 0.9 if "banco" in acc["name"].lower() else 0.7,
                    "reason": "Cuenta bancaria apropiada para transacciones"
                })
        
        return suggestions
    
    # Async compatibility methods for fully async codebases
    async def get_customer_receivable_account_async(self, third_party=None) -> Optional[Account]:
        """Async version for use in async codebases"""
        # Si el tercero tiene cuenta específica configurada
        if third_party and hasattr(third_party, 'receivable_account_id') and third_party.receivable_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == third_party.receivable_account_id,
                        Account.is_active == True
                    )
                )
            )
            account = account_result.scalar_one_or_none()
            if account:
                return account
        
        # Usar cuenta por defecto de la empresa
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if settings and settings.default_customer_receivable_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == settings.default_customer_receivable_account_id,
                        Account.is_active == True
                    )
                )
            )
            account = account_result.scalar_one_or_none()
            if account:
                return account
        
        # Fallback: buscar en plan de cuentas
        account_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.ASSET,
                    Account.is_active == True
                )
            ).order_by(Account.code).limit(1)
        )
        return account_result.scalar_one_or_none()

    async def get_supplier_payable_account_async(self, third_party=None) -> Optional[Account]:
        """Async version for use in async codebases"""
        if third_party and hasattr(third_party, 'payable_account_id') and third_party.payable_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == third_party.payable_account_id,
                        Account.is_active == True
                    )
                )
            )
            account = account_result.scalar_one_or_none()
            if account:
                return account
        
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if settings and settings.default_supplier_payable_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == settings.default_supplier_payable_account_id,
                        Account.is_active == True
                    )
                )
            )
            account = account_result.scalar_one_or_none()
            if account:
                return account
        
        account_result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.account_type == AccountType.LIABILITY,
                    Account.is_active == True
                )
            ).order_by(Account.code).limit(1)
        )
        return account_result.scalar_one_or_none()

    async def get_bank_suspense_account_async(self) -> Optional[Account]:
        """Async version for use in async codebases"""
        settings_result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        settings = settings_result.scalar_one_or_none()
        
        if settings and settings.bank_suspense_account_id:
            account_result = await self.db.execute(
                select(Account).where(
                    and_(
                        Account.id == settings.bank_suspense_account_id,
                        Account.is_active == True
                    )
                )
            )
            return account_result.scalar_one_or_none()
        return None
