#!/usr/bin/env python3
"""
Script para verificar la configuración actual de la compañía.
"""
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.company_settings import CompanySettings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def show_current_company_settings():
    """Mostrar la configuración actual de la compañía"""
    
    async with AsyncSessionLocal() as session:
        session: AsyncSession
        
        try:
            # Buscar configuración existente
            stmt = select(CompanySettings).limit(1)
            result = await session.execute(stmt)
            settings = result.scalar_one_or_none()
            
            if not settings:
                print("❌ No se encontró configuración de compañía")
                return
            
            print("🏢 CONFIGURACIÓN ACTUAL DE LA COMPAÑÍA:")
            print("=" * 60)
            print(f"ID: {settings.id}")
            print(f"Nombre: {settings.company_name}")
            print(f"RUT/Tax ID: {settings.tax_id}")
            print(f"Moneda: {settings.currency_code}")
            print(f"Activa: {settings.is_active}")
            print()
            
            print("📊 CUENTAS CONFIGURADAS:")
            print(f"  • Por cobrar (clientes): {settings.default_customer_receivable_account_id}")
            print(f"  • Por pagar (proveedores): {settings.default_supplier_payable_account_id}")
            print(f"  • Suspensión bancaria: {settings.bank_suspense_account_id}")
            print(f"  • Transferencias internas: {settings.internal_transfer_account_id}")
            print(f"  • Gastos diferidos: {settings.deferred_expense_account_id}")
            print(f"  • Ingresos diferidos: {settings.deferred_revenue_account_id}")
            print(f"  • Descuento ganancia pago anticipado: {settings.early_payment_discount_gain_account_id}")
            print(f"  • Descuento pérdida pago anticipado: {settings.early_payment_discount_loss_account_id}")
            print()
            
            print("📋 JOURNALS CONFIGURADOS:")
            print(f"  • Gastos diferidos: {settings.deferred_expense_journal_id}")
            print(f"  • Ingresos diferidos: {settings.deferred_revenue_journal_id}")
            print()
            
            print("⚙️ CONFIGURACIÓN ADICIONAL:")
            print(f"  • Validar facturas en contabilización: {settings.validate_invoice_on_posting}")
            print(f"  • Descuentos en misma cuenta: {settings.invoice_line_discount_same_account}")
            print(f"  • Meses gastos diferidos: {settings.deferred_expense_months}")
            print(f"  • Meses ingresos diferidos: {settings.deferred_revenue_months}")
            print(f"  • Método generación diferidos: {settings.deferred_generation_method}")
            
        except Exception as e:
            logger.error(f"❌ Error al obtener configuración: {str(e)}")
            raise

async def main():
    """Función principal"""
    await show_current_company_settings()

if __name__ == "__main__":
    asyncio.run(main())
