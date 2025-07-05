#!/usr/bin/env python3
"""
🧪 SCRIPT DE PRUEBA: ACTUALIZACIÓN DE CONFIGURACIÓN DE EMPRESA
============================================================

Este script:
1. Obtiene las cuentas disponibles del plan de cuentas
2. Asigna cuentas apropiadas para la configuración de empresa
3. Actualiza la configuración
4. Verifica que se haya guardado correctamente

Esto nos ayudará a identificar dónde está el problema de persistencia.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.account import Account, AccountType
from app.models.journal import Journal
from app.services.company_settings_service import CompanySettingsService
from app.schemas.company_settings import CompanySettingsUpdate

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_sample_accounts(db: AsyncSession):
    """Obtiene cuentas de muestra para cada tipo"""
    accounts = {}
    
    # Cuenta por cobrar (activo)
    receivable_result = await db.execute(
        select(Account).where(
            Account.account_type == AccountType.ASSET,
            Account.name.ilike('%cobrar%')
        ).limit(1)
    )
    receivable = receivable_result.scalar_one_or_none()
    if receivable:
        accounts['receivable'] = receivable
        logger.info(f"✅ Cuenta por cobrar encontrada: {receivable.code} - {receivable.name}")
    
    # Cuenta por pagar (pasivo)
    payable_result = await db.execute(
        select(Account).where(
            Account.account_type == AccountType.LIABILITY,
            Account.name.ilike('%pagar%')
        ).limit(1)
    )
    payable = payable_result.scalar_one_or_none()
    if payable:
        accounts['payable'] = payable
        logger.info(f"✅ Cuenta por pagar encontrada: {payable.code} - {payable.name}")
    
    # Cuenta bancaria
    bank_result = await db.execute(
        select(Account).where(
            Account.account_type == AccountType.ASSET,
            Account.name.ilike('%banco%')
        ).limit(1)
    )
    bank = bank_result.scalar_one_or_none()
    if bank:
        accounts['bank'] = bank
        logger.info(f"✅ Cuenta bancaria encontrada: {bank.code} - {bank.name}")
    
    # Cuenta de gastos
    expense_result = await db.execute(
        select(Account).where(Account.account_type == AccountType.EXPENSE).limit(1)
    )
    expense = expense_result.scalar_one_or_none()
    if expense:
        accounts['expense'] = expense
        logger.info(f"✅ Cuenta de gastos encontrada: {expense.code} - {expense.name}")
    
    # Cuenta de ingresos
    income_result = await db.execute(
        select(Account).where(Account.account_type == AccountType.INCOME).limit(1)
    )
    income = income_result.scalar_one_or_none()
    if income:
        accounts['income'] = income
        logger.info(f"✅ Cuenta de ingresos encontrada: {income.code} - {income.name}")
    
    return accounts

async def get_sample_journals(db: AsyncSession):
    """Obtiene journals de muestra"""
    journals = {}
    
    # Diario general o cualquier diario disponible
    general_result = await db.execute(
        select(Journal).where(Journal.name.ilike('%general%')).limit(1)
    )
    general = general_result.scalar_one_or_none()
    
    if not general:
        # Si no hay diario general, tomar el primero disponible
        any_result = await db.execute(select(Journal).limit(1))
        general = any_result.scalar_one_or_none()
    
    if general:
        journals['general'] = general
        logger.info(f"✅ Diario encontrado: {general.name} (ID: {general.id})")
    
    return journals

async def test_company_settings_update():
    """Prueba la actualización de configuración de empresa"""
    logger.info("🚀 Iniciando prueba de actualización de configuración de empresa")
    
    async with AsyncSessionLocal() as db:
        service = CompanySettingsService(db)
        
        try:
            # 1. Obtener configuración actual
            logger.info("📋 1. Obteniendo configuración actual...")
            current_settings = await service.get_company_settings()
            if current_settings:
                logger.info(f"✅ Configuración actual encontrada: {current_settings.company_name}")
            else:
                logger.info("⚠️ No hay configuración actual")
            
            # 2. Obtener cuentas disponibles
            logger.info("🔍 2. Buscando cuentas disponibles...")
            accounts = await get_sample_accounts(db)
            
            if not accounts:
                logger.error("❌ No se encontraron cuentas. Ejecutar primero setup_complete_company.py")
                return
            
            # 3. Obtener journals disponibles
            logger.info("📖 3. Buscando journals disponibles...")
            journals = await get_sample_journals(db)
            
            # 4. Preparar datos de actualización
            logger.info("📝 4. Preparando datos de actualización...")
            update_data = CompanySettingsUpdate(
                company_name="Empresa de Prueba - Actualizada",
                tax_id="999888777666",
                currency_code="USD",
                default_customer_receivable_account_id=accounts.get('receivable').id if accounts.get('receivable') else None,
                default_supplier_payable_account_id=accounts.get('payable').id if accounts.get('payable') else None,
                bank_suspense_account_id=accounts.get('bank').id if accounts.get('bank') else None,
                internal_transfer_account_id=accounts.get('bank').id if accounts.get('bank') else None,
                deferred_expense_account_id=accounts.get('expense').id if accounts.get('expense') else None,
                deferred_expense_journal_id=journals.get('general').id if journals.get('general') else None,
                deferred_expense_months=12,
                deferred_revenue_account_id=accounts.get('income').id if accounts.get('income') else None,
                deferred_revenue_journal_id=journals.get('general').id if journals.get('general') else None,
                deferred_revenue_months=12,
                early_payment_discount_gain_account_id=accounts.get('income').id if accounts.get('income') else None,
                early_payment_discount_loss_account_id=accounts.get('expense').id if accounts.get('expense') else None,
                invoice_line_discount_same_account=True,
                validate_invoice_on_posting=True,
                deferred_generation_method="on_invoice_validation",
                is_active=True,
                notes="Configuración actualizada por script de prueba"
            )
            
            logger.info("🔄 5. Actualizando configuración...")
            logger.info(f"   📊 Datos a enviar:")
            logger.info(f"   - Cuenta por cobrar: {accounts.get('receivable').code if accounts.get('receivable') else 'N/A'}")
            logger.info(f"   - Cuenta por pagar: {accounts.get('payable').code if accounts.get('payable') else 'N/A'}")
            logger.info(f"   - Cuenta bancaria: {accounts.get('bank').code if accounts.get('bank') else 'N/A'}")
            logger.info(f"   - Journal: {journals.get('general').name if journals.get('general') else 'N/A'}")
            
            # 5. Actualizar configuración
            updated_settings = await service.update_company_settings(update_data, current_settings.id if current_settings else None)
            logger.info("✅ 5. Configuración actualizada exitosamente!")
            logger.info(f"   - ID: {updated_settings.id}")
            logger.info(f"   - Nombre: {updated_settings.company_name}")
            logger.info(f"   - Cuenta por cobrar configurada: {updated_settings.has_customer_receivable_configured}")
            logger.info(f"   - Cuenta por pagar configurada: {updated_settings.has_supplier_payable_configured}")
            
            # 6. Verificar inmediatamente que se guardó
            logger.info("🔍 6. Verificando que se guardó en la sesión actual...")
            verification_settings = await service.get_company_settings()
            if verification_settings:
                logger.info("✅ Verificación en sesión actual:")
                logger.info(f"   - Cuenta por cobrar ID: {verification_settings.default_customer_receivable_account_id}")
                logger.info(f"   - Cuenta por pagar ID: {verification_settings.default_supplier_payable_account_id}")
                logger.info(f"   - Cuenta bancaria ID: {verification_settings.bank_suspense_account_id}")
                logger.info(f"   - Journal gastos diferidos ID: {verification_settings.deferred_expense_journal_id}")
            
            # 7. Hacer commit explícito para asegurar persistencia
            logger.info("💾 7. Haciendo commit explícito...")
            await db.commit()
            logger.info("✅ Commit realizado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error durante la actualización: {e}")
            await db.rollback()
            raise

async def verify_persistence():
    """Verifica en una nueva sesión que los datos se hayan persistido"""
    logger.info("🔍 Verificando persistencia en nueva sesión...")
    
    async with AsyncSessionLocal() as db:
        service = CompanySettingsService(db)
        
        try:
            settings = await service.get_company_settings()
            if settings:
                logger.info("✅ Verificación en nueva sesión:")
                logger.info(f"   - Nombre empresa: {settings.company_name}")
                logger.info(f"   - NIT: {settings.tax_id}")
                logger.info(f"   - Cuenta por cobrar ID: {settings.default_customer_receivable_account_id}")
                logger.info(f"   - Cuenta por cobrar nombre: {settings.default_customer_receivable_account_name}")
                logger.info(f"   - Cuenta por pagar ID: {settings.default_supplier_payable_account_id}")
                logger.info(f"   - Cuenta por pagar nombre: {settings.default_supplier_payable_account_name}")
                logger.info(f"   - Cuenta bancaria ID: {settings.bank_suspense_account_id}")
                logger.info(f"   - Cuenta bancaria nombre: {settings.bank_suspense_account_name}")
                logger.info(f"   - Journal gastos diferidos ID: {settings.deferred_expense_journal_id}")
                logger.info(f"   - Has receivable configured: {settings.has_customer_receivable_configured}")
                logger.info(f"   - Has payable configured: {settings.has_supplier_payable_configured}")
                logger.info(f"   - Notas: {settings.notes}")
                
                if all([
                    settings.default_customer_receivable_account_id,
                    settings.default_supplier_payable_account_id,
                    settings.bank_suspense_account_id
                ]):
                    logger.info("🎉 ¡ÉXITO! Los datos se persistieron correctamente")
                    return True
                else:
                    logger.error("❌ FALLO: Algunos campos están nulos después de la actualización")
                    return False
            else:
                logger.error("❌ FALLO: No se encontró configuración en nueva sesión")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verificando persistencia: {e}")
            return False

async def main():
    """Función principal"""
    logger.info("="*60)
    logger.info("🧪 INICIANDO PRUEBA DE CONFIGURACIÓN DE EMPRESA")
    logger.info("="*60)
    
    try:
        # Paso 1: Actualizar configuración
        await test_company_settings_update()
        
        # Paso 2: Verificar persistencia en nueva sesión
        success = await verify_persistence()
        
        if success:
            logger.info("="*60)
            logger.info("🎉 PRUEBA COMPLETADA EXITOSAMENTE")
            logger.info("✅ La configuración se guarda y persiste correctamente")
            logger.info("="*60)
        else:
            logger.error("="*60)
            logger.error("❌ PRUEBA FALLÓ")
            logger.error("❌ Hay un problema con la persistencia de datos")
            logger.error("="*60)
            
    except Exception as e:
        logger.error("="*60)
        logger.error(f"❌ ERROR CRÍTICO EN LA PRUEBA: {e}")
        logger.error("="*60)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
