#!/usr/bin/env python3
"""
Script para verificar la configuración bancaria del journal
"""

import asyncio
import uuid
from app.database import AsyncSessionLocal
from app.models.journal import Journal
from app.models.bank_journal_config import BankJournalConfig
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def main():
    """Función principal"""
    async with AsyncSessionLocal() as db:
        try:
            # Buscar el journal de banco con su configuración
            result = await db.execute(
                select(Journal)
                .options(selectinload(Journal.bank_config))
                .where(Journal.name.ilike('%Diario de Banco Principal%'))
            )
            journal = result.scalar_one_or_none()
            
            if not journal:
                print('No se encontró el journal')
                return
            
            print(f'Journal: {journal.name}')
            print(f'Tipo: {journal.type}')
            print(f'Cuenta por defecto: {journal.default_account_id}')
            print(f'¿Es journal bancario?: {journal.is_bank_journal()}')
            
            # Verificar configuración bancaria
            if journal.bank_config:
                config = journal.bank_config
                print(f'\n✅ Configuración bancaria encontrada:')
                print(f'- Número de cuenta: {config.bank_account_number}')
                print(f'- Cuenta bancaria ID: {config.bank_account_id}')
                print(f'- Cuenta tránsito ID: {config.transit_account_id}')
                print(f'- Cuenta ganancia ID: {config.profit_account_id}')
                print(f'- Cuenta pérdida ID: {config.loss_account_id}')
                print(f'- Permite pagos entrantes: {config.allow_inbound_payments}')
                print(f'- Cuenta recibos entrantes ID: {config.inbound_receipt_account_id}')
                print(f'- Permite pagos salientes: {config.allow_outbound_payments}')
                print(f'- Cuenta pendientes salientes ID: {config.outbound_pending_account_id}')
                print(f'- Moneda: {config.currency_code}')
                print(f'- Auto-conciliación: {config.auto_reconcile}')
            else:
                print(f'\n❌ No tiene configuración bancaria')
                print(f'Necesita crear la configuración bancaria para este journal')
                
                # Sugerir crear configuración
                bank_account_id = uuid.UUID('fa14c054-04d8-4ffc-9df3-e500d2041cb1')
                print(f'\nSugerencia de configuración:')
                print(f'- bank_account_id: {bank_account_id}')
                print(f'- transit_account_id: {bank_account_id}')
                print(f'- inbound_receipt_account_id: {bank_account_id}')
                print(f'- outbound_pending_account_id: {bank_account_id}')
                    
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
