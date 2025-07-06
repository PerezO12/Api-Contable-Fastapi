"""
API endpoints for company settings management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from app.api.deps import get_db, get_current_user
from app.schemas.company_settings import (
    CompanySettingsCreate, CompanySettingsUpdate, CompanySettingsResponse,
    DefaultAccountsInfo, AccountSuggestion
)
from app.services.company_settings_service import CompanySettingsService
from app.utils.exceptions import NotFoundError, BusinessRuleError
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=CompanySettingsResponse)
async def get_company_settings(db: AsyncSession = Depends(get_db)):
    """
    Obtener la configuración actual de la empresa
    """
    try:
        service = CompanySettingsService(db)
        settings = await service.get_company_settings()
        
        if settings:
            return settings
            
        # Si no existe configuración, devolver una respuesta básica vacía
        # En lugar de crear automáticamente, que puede causar errores
        logger.info("No company settings found, returning empty configuration")
        
        return CompanySettingsResponse(
            id=uuid4(),  # UUID temporal
            company_name="Empresa sin configurar",
            tax_id="",
            currency_code="USD",
            
            # Basic account IDs - all None
            default_customer_receivable_account_id=None,
            default_supplier_payable_account_id=None,
            default_sales_income_account_id=None,
            default_purchase_expense_account_id=None,
            default_sales_tax_payable_account_id=None,
            default_purchase_tax_deductible_account_id=None,
            default_tax_account_id=None,
            
            # Brazilian tax accounts IDs - all None
            default_icms_payable_account_id=None,
            default_icms_deductible_account_id=None,
            default_pis_payable_account_id=None,
            default_pis_deductible_account_id=None,
            default_cofins_payable_account_id=None,
            default_cofins_deductible_account_id=None,
            default_ipi_payable_account_id=None,
            default_ipi_deductible_account_id=None,
            default_iss_payable_account_id=None,
            default_csll_payable_account_id=None,
            default_irpj_payable_account_id=None,
            
            # Other account IDs - all None
            default_cash_account_id=None,
            default_bank_account_id=None,
            bank_suspense_account_id=None,
            internal_transfer_account_id=None,
            deferred_expense_account_id=None,
            deferred_expense_journal_id=None,
            deferred_expense_months=12,
            deferred_revenue_account_id=None,
            deferred_revenue_journal_id=None,
            deferred_revenue_months=12,
            invoice_line_discount_same_account=True,
            early_payment_discount_gain_account_id=None,
            early_payment_discount_loss_account_id=None,
            validate_invoice_on_posting=True,
            deferred_generation_method="on_invoice_validation",
            notes="",
            is_active=True,
            
            # All account names - None
            default_customer_receivable_account_name=None,
            default_supplier_payable_account_name=None,
            default_sales_income_account_name=None,
            default_purchase_expense_account_name=None,
            default_sales_tax_payable_account_name=None,
            default_purchase_tax_deductible_account_name=None,
            default_tax_account_name=None,
            
            # Brazilian tax accounts names - all None
            default_icms_payable_account_name=None,
            default_icms_deductible_account_name=None,
            default_pis_payable_account_name=None,
            default_pis_deductible_account_name=None,
            default_cofins_payable_account_name=None,
            default_cofins_deductible_account_name=None,
            default_ipi_payable_account_name=None,
            default_ipi_deductible_account_name=None,
            default_iss_payable_account_name=None,
            default_csll_payable_account_name=None,
            default_irpj_payable_account_name=None,
            
            # Other account names - all None
            default_cash_account_name=None,
            default_bank_account_name=None,
            bank_suspense_account_name=None,
            internal_transfer_account_name=None,
            deferred_expense_account_name=None,
            deferred_revenue_account_name=None,
            early_payment_discount_gain_account_name=None,
            early_payment_discount_loss_account_name=None,
            
            # All configuration flags - False
            has_customer_receivable_configured=False,
            has_supplier_payable_configured=False,
            has_sales_income_configured=False,
            has_purchase_expense_configured=False,
            has_deferred_accounts_configured=False,
            has_tax_accounts_configured=False,
            has_brazilian_tax_accounts_configured=False
        )
        
    except Exception as e:
        logger.error(f"Error getting company settings: {e}")
        logger.exception("Full traceback:")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving company settings: {str(e)}"
        )


@router.post("/", response_model=CompanySettingsResponse)
async def create_company_settings(
    settings_data: CompanySettingsCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Crear nueva configuración de empresa
    """
    try:
        service = CompanySettingsService(db)
        settings = await service.create_company_settings(settings_data, current_user.id)
        return settings
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating company settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating company settings"
        )


@router.put("/", response_model=CompanySettingsResponse)
async def update_company_settings(
    settings_data: CompanySettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Actualizar configuración de empresa existente
    """
    try:
        service = CompanySettingsService(db)
        settings = await service.update_company_settings(settings_data, current_user.id)
        return settings
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating company settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company settings"
        )


@router.get("/accounts", response_model=DefaultAccountsInfo)
async def get_default_accounts_info(db: AsyncSession = Depends(get_db)):
    """
    Obtener información de cuentas disponibles para configurar como defecto
    """
    try:
        service = CompanySettingsService(db)
        return await service.get_default_accounts_info()
    except Exception as e:
        logger.error(f"Error getting default accounts info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving default accounts information"
        )


@router.get("/default-accounts", response_model=DefaultAccountsInfo)
async def get_default_accounts_info_alt(db: AsyncSession = Depends(get_db)):
    """
    Obtener información de cuentas disponibles para configurar como defecto (endpoint alternativo)
    """
    try:
        service = CompanySettingsService(db)
        return await service.get_default_accounts_info()
    except Exception as e:
        logger.error(f"Error getting default accounts info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving default accounts information"
        )


@router.get("/validate", response_model=dict)
async def validate_company_settings(db: AsyncSession = Depends(get_db)):
    """
    Validar la configuración actual de la empresa
    """
    try:
        service = CompanySettingsService(db)
        settings = await service.get_company_settings()
        
        if not settings:
            return {
                "is_valid": False,
                "issues": ["No hay configuración de empresa"],
                "recommendations": ["Crear configuración básica de empresa"]
            }
        
        issues = []
        recommendations = []
        
        # Validar configuraciones críticas
        if not settings.default_customer_receivable_account_id:
            issues.append("Falta cuenta por cobrar por defecto para clientes")
            recommendations.append("Configurar una cuenta de activo como cuenta por cobrar por defecto")
        
        if not settings.default_supplier_payable_account_id:
            issues.append("Falta cuenta por pagar por defecto para proveedores")
            recommendations.append("Configurar una cuenta de pasivo como cuenta por pagar por defecto")
        
        if not settings.bank_suspense_account_id:
            issues.append("Falta cuenta transitoria bancaria")
            recommendations.append("Configurar una cuenta bancaria como cuenta transitoria")
        
        if not settings.company_name or settings.company_name.strip() == "":
            issues.append("Nombre de empresa vacío")
            recommendations.append("Establecer un nombre válido para la empresa")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "settings": settings
        }
        
    except Exception as e:
        logger.error(f"Error validating company settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating company settings"
        )


@router.get("/account-suggestions", response_model=List[AccountSuggestion])
async def get_account_suggestions(
    account_type: Optional[str] = Query(None, description="Filtrar por tipo de cuenta"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener sugerencias de cuentas para configuración
    """
    try:
        service = CompanySettingsService(db)
        return await service.get_account_suggestions(account_type)
    except Exception as e:
        logger.error(f"Error getting account suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving account suggestions"
        )


@router.post("/initialize", response_model=dict)
async def initialize_company_settings(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Inicializar configuración básica de empresa con valores por defecto
    """
    try:
        service = CompanySettingsService(db)
        
        # Verificar si ya existe configuración
        existing_settings = await service.get_company_settings()
        if existing_settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe configuración de empresa"
            )
        
        # Crear configuración por defecto
        default_settings = await service.get_or_create_default_settings()
        
        return {
            "message": "Configuración de empresa inicializada exitosamente",
            "settings_id": str(default_settings.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing company settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error initializing company settings"
        )


class TaxAccountsUpdate(BaseModel):
    """Schema para actualizar cuentas de impuestos"""
    default_sales_tax_payable_account_id: Optional[UUID] = Field(
        None, 
        description="Cuenta por defecto para impuestos por pagar sobre ventas"
    )
    default_purchase_tax_deductible_account_id: Optional[UUID] = Field(
        None, 
        description="Cuenta por defecto para impuestos deducibles sobre compras"
    )
    default_tax_account_id: Optional[UUID] = Field(
        None, 
        description="Cuenta genérica para impuestos (fallback)"
    )
    
    # Brazilian tax accounts
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

class TaxAccountsResponse(BaseModel):
    """Response con información de cuentas de impuestos"""
    default_sales_tax_payable_account_id: Optional[UUID]
    default_sales_tax_payable_account_name: Optional[str]
    default_purchase_tax_deductible_account_id: Optional[UUID]
    default_purchase_tax_deductible_account_name: Optional[str]
    default_tax_account_id: Optional[UUID]
    default_tax_account_name: Optional[str]
    
    # Brazilian tax accounts
    default_icms_payable_account_id: Optional[UUID]
    default_icms_payable_account_name: Optional[str]
    default_icms_deductible_account_id: Optional[UUID]
    default_icms_deductible_account_name: Optional[str]
    default_pis_payable_account_id: Optional[UUID]
    default_pis_payable_account_name: Optional[str]
    default_pis_deductible_account_id: Optional[UUID]
    default_pis_deductible_account_name: Optional[str]
    default_cofins_payable_account_id: Optional[UUID]
    default_cofins_payable_account_name: Optional[str]
    default_cofins_deductible_account_id: Optional[UUID]
    default_cofins_deductible_account_name: Optional[str]
    default_ipi_payable_account_id: Optional[UUID]
    default_ipi_payable_account_name: Optional[str]
    default_ipi_deductible_account_id: Optional[UUID]
    default_ipi_deductible_account_name: Optional[str]
    default_iss_payable_account_id: Optional[UUID]
    default_iss_payable_account_name: Optional[str]
    default_csll_payable_account_id: Optional[UUID]
    default_csll_payable_account_name: Optional[str]
    default_irpj_payable_account_id: Optional[UUID]
    default_irpj_payable_account_name: Optional[str]
    
    is_configured: bool = Field(description="Indica si al menos una cuenta está configurada")


@router.get("/tax-accounts", response_model=TaxAccountsResponse)
async def get_tax_accounts_configuration(db: AsyncSession = Depends(get_db)):
    """
    Obtener configuración actual de las cuentas de impuestos
    """
    try:
        service = CompanySettingsService(db)
        return await service.get_tax_accounts_configuration()
        
    except Exception as e:
        logger.error(f"Error getting tax accounts configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving tax accounts configuration"
        )


@router.put("/tax-accounts", response_model=TaxAccountsResponse)
async def update_tax_accounts_configuration(
    tax_accounts_data: TaxAccountsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Actualizar configuración de cuentas de impuestos
    """
    try:
        service = CompanySettingsService(db)
        return await service.update_tax_accounts_configuration(tax_accounts_data)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating tax accounts configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating tax accounts configuration"
        )


@router.get("/tax-accounts/suggestions")
async def get_tax_account_suggestions(
    db: AsyncSession = Depends(get_db),
    account_type: Optional[str] = Query(None, description="Tipo de cuenta: 'LIABILITY' para impuestos por pagar, 'ASSET' para impuestos deducibles")
):
    """
    Obtener sugerencias de cuentas para configurar como cuentas de impuestos
    """
    try:
        from sqlalchemy import text
        
        # Construir query según el tipo de cuenta
        if account_type == "LIABILITY":
            query = text("""
                SELECT id, code, name, description, account_type
                FROM accounts
                WHERE account_type = 'LIABILITY' 
                  AND is_active = true 
                  AND allows_movements = true
                  AND (name ILIKE '%impuesto%' OR name ILIKE '%tax%' OR code LIKE '24%' OR code LIKE '21%')
                ORDER BY code
                LIMIT 10
            """)
        elif account_type == "ASSET":
            query = text("""
                SELECT id, code, name, description, account_type
                FROM accounts
                WHERE account_type = 'ASSET' 
                  AND is_active = true 
                  AND allows_movements = true
                  AND (name ILIKE '%impuesto%' OR name ILIKE '%tax%' OR code LIKE '13%' OR code LIKE '1365%')
                ORDER BY code
                LIMIT 10
            """)
        else:
            query = text("""
                SELECT id, code, name, description, account_type
                FROM accounts
                WHERE is_active = true 
                  AND allows_movements = true
                  AND (name ILIKE '%impuesto%' OR name ILIKE '%tax%')
                ORDER BY account_type, code
                LIMIT 20
            """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        suggestions = []
        for row in rows:
            suggestions.append({
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "description": row.description or "",
                "account_type": row.account_type
            })
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error getting tax account suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving tax account suggestions"
        )


@router.post("/tax-accounts/auto-configure")
async def auto_configure_tax_accounts(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Configurar automáticamente las cuentas de impuestos usando el algoritmo de búsqueda inteligente
    """
    try:
        from sqlalchemy import text
        
        # Buscar cuenta para impuestos por pagar (ventas)
        sales_tax_query = text("""
            SELECT id, code, name
            FROM accounts
            WHERE account_type = 'LIABILITY' 
              AND is_active = true 
              AND allows_movements = true
              AND (name ILIKE '%impuesto%' OR name ILIKE '%tax%')
            ORDER BY 
                CASE 
                    WHEN code LIKE '2408%' THEN 1
                    WHEN code LIKE '2405%' THEN 2
                    WHEN code LIKE '24%' THEN 3
                    WHEN code LIKE '21%' THEN 4
                    ELSE 5
                END,
                code
            LIMIT 1
        """)
        
        # Buscar cuenta para impuestos deducibles (compras)
        purchase_tax_query = text("""
            SELECT id, code, name
            FROM accounts
            WHERE account_type = 'ASSET' 
              AND is_active = true 
              AND allows_movements = true
              AND (name ILIKE '%impuesto%' OR name ILIKE '%tax%')
            ORDER BY 
                CASE 
                    WHEN code LIKE '1365%' THEN 1
                    WHEN code LIKE '1360%' THEN 2
                    WHEN code LIKE '13%' THEN 3
                    ELSE 4
                END,
                code
            LIMIT 1
        """)
        
        sales_result = await db.execute(sales_tax_query)
        sales_account = sales_result.fetchone()
        
        purchase_result = await db.execute(purchase_tax_query)
        purchase_account = purchase_result.fetchone()
        
        # Usar la cuenta de ventas como genérica si no hay de compras
        generic_account = sales_account if sales_account else purchase_account
        
        if not sales_account and not purchase_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se encontraron cuentas de impuestos apropiadas en el plan contable"
            )
        
        # Actualizar configuración
        update_query = text("""
            UPDATE company_settings 
            SET 
                default_sales_tax_payable_account_id = :sales_tax_id,
                default_purchase_tax_deductible_account_id = :purchase_tax_id,
                default_tax_account_id = :generic_tax_id,
                updated_at = CURRENT_TIMESTAMP
            WHERE is_active = true
        """)
        
        await db.execute(update_query, {
            "sales_tax_id": sales_account.id if sales_account else None,
            "purchase_tax_id": purchase_account.id if purchase_account else None,
            "generic_tax_id": generic_account.id if generic_account else None
        })
        
        await db.commit()
        
        configured_accounts = {}
        if sales_account:
            configured_accounts["sales_tax"] = f"{sales_account.code} - {sales_account.name}"
        if purchase_account:
            configured_accounts["purchase_tax"] = f"{purchase_account.code} - {purchase_account.name}"
        if generic_account:
            configured_accounts["generic_tax"] = f"{generic_account.code} - {generic_account.name}"
        
        return {
            "success": True,
            "message": "Cuentas de impuestos configuradas automáticamente",
            "configured_accounts": configured_accounts
        }
        
    except Exception as e:
        logger.error(f"Error auto-configuring tax accounts: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error auto-configuring tax accounts"
        )
