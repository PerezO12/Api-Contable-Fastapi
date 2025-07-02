#!/usr/bin/env python3
"""
Script para verificar los pagos en la base de datos
"""

import asyncio
from app.database import AsyncSessionLocal
from app.models.payment import Payment
from sqlalchemy.future import select

async def main():
    """Función principal"""
    async with AsyncSessionLocal() as db:
        try:
            # Buscar todos los pagos
            result = await db.execute(select(Payment))
            payments = result.scalars().all()
            
            print(f'Total de pagos encontrados: {len(payments)}')
            
            for payment in payments:
                print(f'- ID: {payment.id}')
                print(f'  Número: {payment.number}')
                print(f'  Monto: {payment.amount}')
                print(f'  Estado: {payment.status}')
                print(f'  Fecha: {payment.payment_date}')
                print(f'  Tercero ID: {payment.third_party_id}')
                print(f'  Journal ID: {payment.journal_id}')
                print('---')
                    
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
