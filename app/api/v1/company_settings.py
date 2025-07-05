"""
API endpoints for company settings management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

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
        
        if not settings:
            # Si no existe configuración, crear una por defecto
            default_settings = await service.get_or_create_default_settings()
            # Return minimal response - just the basic fields that exist
            return CompanySettingsResponse(
                id=default_settings.id,
                company_name=default_settings.company_name,
                tax_id="",
                deferred_expense_journal_id=None,
                deferred_revenue_journal_id=None,
                notes="",
                default_customer_receivable_account_id=default_settings.default_customer_receivable_account_id,
                default_supplier_payable_account_id=default_settings.default_supplier_payable_account_id,
                bank_suspense_account_id=default_settings.bank_suspense_account_id,
                internal_transfer_account_id=default_settings.internal_transfer_account_id,
                deferred_expense_account_id=default_settings.deferred_expense_account_id,
                deferred_revenue_account_id=default_settings.deferred_revenue_account_id,
                early_payment_discount_gain_account_id=default_settings.early_payment_discount_gain_account_id,
                early_payment_discount_loss_account_id=default_settings.early_payment_discount_loss_account_id,
                default_customer_receivable_account_name=None,
                default_supplier_payable_account_name=None,
                bank_suspense_account_name=None,
                internal_transfer_account_name=None,
                deferred_expense_account_name=None,
                deferred_revenue_account_name=None,
                early_payment_discount_gain_account_name=None,
                early_payment_discount_loss_account_name=None,
                has_customer_receivable_configured=False,
                has_supplier_payable_configured=False,
                has_deferred_accounts_configured=False,
                is_active=default_settings.is_active
            )
        
        return settings
    except Exception as e:
        logger.error(f"Error getting company settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving company settings"
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
