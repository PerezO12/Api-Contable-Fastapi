"""
Script para verificar tablas existentes en la base de datos
"""
import asyncio
from app.database import SessionLocal
from sqlalchemy import text

def check_tables():
    """Verificar tablas existentes en la base de datos"""
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        print('Tablas existentes:')
        for table in tables:
            print(f'  - {table}')
        
        # Verificar específicamente las tablas del sistema de pagos
        payment_tables = ['payments', 'payment_invoices', 'invoices', 'invoice_lines', 
                         'bank_extracts', 'bank_extract_lines', 'bank_reconciliations']
        
        print('\nTablas del sistema de pagos:')
        for table in payment_tables:
            exists = table in tables
            status = "✅" if exists else "❌"
            print(f'  {status} {table}')

if __name__ == "__main__":
    check_tables()
