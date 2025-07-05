#!/usr/bin/env python3
"""
Script para asignar las cuentas y journals por defecto a la configuración de la compañía.
Este script busca las cuentas que se crearon anteriormente y las asigna como cuentas por defecto.
"""
import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.account import Account, AccountType, AccountCategory
from app.models.journal import Journal, JournalType
from app.models.company_settings import CompanySettings
from app.models.user import User, UserRole

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def find_default_accounts(session: AsyncSession):
    """Buscar las cuentas que pueden ser usadas como cuentas por defecto"""
    
    # Buscar cuenta de efectivo/caja (tomar la primera)
    cash_stmt = select(Account).where(
        Account.name.like('%Caja%')
    ).order_by(Account.code)
    cash_result = await session.execute(cash_stmt)
    cash_accounts = cash_result.scalars().all()
    cash_account = cash_accounts[0] if cash_accounts else None
    
    # Buscar cuenta de ventas/ingresos (tomar la primera)
    sales_stmt = select(Account).where(
        Account.account_type == AccountType.INCOME.value
    ).order_by(Account.code)
    sales_result = await session.execute(sales_stmt)
    sales_accounts = sales_result.scalars().all()
    sales_account = sales_accounts[0] if sales_accounts else None
    
    # Buscar cuenta de compras/gastos (tomar la primera)
    purchase_stmt = select(Account).where(
        Account.account_type == AccountType.EXPENSE.value
    ).order_by(Account.code)
    purchase_result = await session.execute(purchase_stmt)
    purchase_accounts = purchase_result.scalars().all()
    purchase_account = purchase_accounts[0] if purchase_accounts else None
    
    # Buscar cuenta de inventario (tomar la primera)
    inventory_stmt = select(Account).where(
        Account.name.like('%Inventario%')
    ).order_by(Account.code)
    inventory_result = await session.execute(inventory_stmt)
    inventory_accounts = inventory_result.scalars().all()
    inventory_account = inventory_accounts[0] if inventory_accounts else None
    
    # Buscar cuentas de impuestos (tomar la primera de cada tipo)
    tax_receivable_stmt = select(Account).where(
        Account.name.like('%por Cobrar%'),
        Account.category == AccountCategory.TAXES.value
    ).order_by(Account.code)
    tax_receivable_result = await session.execute(tax_receivable_stmt)
    tax_receivable_accounts = tax_receivable_result.scalars().all()
    tax_receivable_account = tax_receivable_accounts[0] if tax_receivable_accounts else None
    
    tax_payable_stmt = select(Account).where(
        Account.name.like('%por Pagar%'),
        Account.category == AccountCategory.TAXES.value
    ).order_by(Account.code)
    tax_payable_result = await session.execute(tax_payable_stmt)
    tax_payable_accounts = tax_payable_result.scalars().all()
    tax_payable_account = tax_payable_accounts[0] if tax_payable_accounts else None
    
    return {
        'cash': cash_account,
        'sales': sales_account,
        'purchase': purchase_account,
        'inventory': inventory_account,
        'tax_receivable': tax_receivable_account,
        'tax_payable': tax_payable_account
    }

async def find_default_journals(session: AsyncSession):
    """Buscar los journals por defecto"""
    
    # Buscar journal de ventas
    sales_stmt = select(Journal).where(
        Journal.type == JournalType.SALE.value
    ).order_by(Journal.name)
    sales_result = await session.execute(sales_stmt)
    sales_journals = sales_result.scalars().all()
    sales_journal = sales_journals[0] if sales_journals else None
    
    # Buscar journal de compras
    purchase_stmt = select(Journal).where(
        Journal.type == JournalType.PURCHASE.value
    ).order_by(Journal.name)
    purchase_result = await session.execute(purchase_stmt)
    purchase_journals = purchase_result.scalars().all()
    purchase_journal = purchase_journals[0] if purchase_journals else None
    
    # Buscar journal de banco
    bank_stmt = select(Journal).where(
        Journal.type == JournalType.BANK.value
    ).order_by(Journal.name)
    bank_result = await session.execute(bank_stmt)
    bank_journals = bank_result.scalars().all()
    bank_journal = bank_journals[0] if bank_journals else None
    
    # Buscar journal de efectivo
    cash_stmt = select(Journal).where(
        Journal.type == JournalType.CASH.value
    ).order_by(Journal.name)
    cash_result = await session.execute(cash_stmt)
    cash_journals = cash_result.scalars().all()
    cash_journal = cash_journals[0] if cash_journals else None
    
    return {
        'sales': sales_journal,
        'purchase': purchase_journal,
        'bank': bank_journal,
        'cash': cash_journal
    }

async def get_or_create_company_settings(session: AsyncSession):
    """Obtener o crear la configuración de la compañía"""
    
    # Buscar configuración existente
    stmt = select(CompanySettings).limit(1)
    result = await session.execute(stmt)
    settings = result.scalar_one_or_none()
    
    if not settings:
        logger.info("No se encontró configuración de compañía, creando una nueva...")
        settings = CompanySettings(
            id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            company_name="Mi Empresa",
            tax_id="123456789",
            address="Dirección de la empresa",
            phone="555-1234",
            email="info@empresa.com"
        )
        session.add(settings)
        await session.flush()  # Para obtener el ID
        logger.info(f"Configuración de compañía creada con ID: {settings.id}")
    
    return settings

async def update_company_settings_with_defaults():
    """Actualizar la configuración de la compañía con las cuentas y journals por defecto"""
    
    async with AsyncSessionLocal() as session:
        session: AsyncSession
        
        try:
            # Obtener o crear configuración de compañía
            company_settings = await get_or_create_company_settings(session)
            
            # Buscar cuentas por defecto
            logger.info("Buscando cuentas por defecto...")
            default_accounts = await find_default_accounts(session)
            
            # Buscar journals por defecto
            logger.info("Buscando journals por defecto...")
            default_journals = await find_default_journals(session)
            
            # Mostrar cuentas encontradas
            print("\n📊 CUENTAS ENCONTRADAS:")
            for key, account in default_accounts.items():
                if account:
                    print(f"   ✅ {key.upper()}: {account.code} - {account.name} (ID: {account.id})")
                else:
                    print(f"   ❌ {key.upper()}: No encontrada")
            
            # Mostrar journals encontrados
            print("\n📋 JOURNALS ENCONTRADOS:")
            for key, journal in default_journals.items():
                if journal:
                    print(f"   ✅ {key.upper()}: {journal.name} (ID: {journal.id})")
                else:
                    print(f"   ❌ {key.upper()}: No encontrado")
            
            # Actualizar configuración con las cuentas encontradas
            updates_made = False
            
            # Solo actualizamos las cuentas que realmente existen en CompanySettings
            if default_accounts['sales'] and not company_settings.default_customer_receivable_account_id:
                company_settings.default_customer_receivable_account_id = default_accounts['sales'].id
                updates_made = True
                logger.info(f"Asignada cuenta por cobrar (ventas): {default_accounts['sales'].name}")
            
            if default_accounts['purchase'] and not company_settings.default_supplier_payable_account_id:
                company_settings.default_supplier_payable_account_id = default_accounts['purchase'].id
                updates_made = True
                logger.info(f"Asignada cuenta por pagar (compras): {default_accounts['purchase'].name}")
            
            if default_accounts['cash'] and not company_settings.bank_suspense_account_id:
                company_settings.bank_suspense_account_id = default_accounts['cash'].id
                updates_made = True
                logger.info(f"Asignada cuenta transitoria bancaria: {default_accounts['cash'].name}")
            
            if default_accounts['cash'] and not company_settings.internal_transfer_account_id:
                company_settings.internal_transfer_account_id = default_accounts['cash'].id
                updates_made = True
                logger.info(f"Asignada cuenta de transferencias internas: {default_accounts['cash'].name}")
            
            if default_accounts['purchase'] and not company_settings.deferred_expense_account_id:
                company_settings.deferred_expense_account_id = default_accounts['purchase'].id
                updates_made = True
                logger.info(f"Asignada cuenta de gastos diferidos: {default_accounts['purchase'].name}")
            
            if default_accounts['sales'] and not company_settings.deferred_revenue_account_id:
                company_settings.deferred_revenue_account_id = default_accounts['sales'].id
                updates_made = True
                logger.info(f"Asignada cuenta de ingresos diferidos: {default_accounts['sales'].name}")
            
            # Actualizar journals (solo los que existen como ForeignKey en CompanySettings)
            if default_journals['purchase'] and not company_settings.deferred_expense_journal_id:
                company_settings.deferred_expense_journal_id = default_journals['purchase'].id
                updates_made = True
                logger.info(f"Asignado journal de gastos diferidos: {default_journals['purchase'].name}")
            
            if default_journals['sales'] and not company_settings.deferred_revenue_journal_id:
                company_settings.deferred_revenue_journal_id = default_journals['sales'].id
                updates_made = True
                logger.info(f"Asignado journal de ingresos diferidos: {default_journals['sales'].name}")
            
            if updates_made:
                company_settings.updated_at = datetime.now(timezone.utc)
                await session.commit()
                logger.info("✅ Configuración de compañía actualizada exitosamente")
                
                # Verificar que los cambios se guardaron
                await session.refresh(company_settings)
                print(f"\n🔍 VERIFICACIÓN FINAL:")
                print(f"   ID de configuración: {company_settings.id}")
                print(f"   Cuenta por cobrar (clientes): {company_settings.default_customer_receivable_account_id}")
                print(f"   Cuenta por pagar (proveedores): {company_settings.default_supplier_payable_account_id}")
                print(f"   Cuenta transitoria bancaria: {company_settings.bank_suspense_account_id}")
                print(f"   Cuenta transferencias internas: {company_settings.internal_transfer_account_id}")
                print(f"   Journal gastos diferidos: {company_settings.deferred_expense_journal_id}")
                print(f"   Journal ingresos diferidos: {company_settings.deferred_revenue_journal_id}")
                
            else:
                logger.info("ℹ️ No se realizaron actualizaciones (las cuentas ya estaban asignadas)")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error al actualizar configuración: {str(e)}")
            raise

async def main():
    """Función principal"""
    print("=" * 70)
    print("🏢 SISTEMA CONTABLE - CONFIGURACIÓN DE CUENTAS POR DEFECTO")
    print("=" * 70)
    print("\nEste script busca las cuentas y journals creados previamente")
    print("y los asigna como cuentas por defecto en la configuración de la compañía.")
    print()
    
    response = input("¿Deseas continuar con la configuración? (y/N): ")
    if response.lower() == 'y':
        await update_company_settings_with_defaults()
    else:
        print("❌ Operación cancelada")

if __name__ == "__main__":
    asyncio.run(main())
