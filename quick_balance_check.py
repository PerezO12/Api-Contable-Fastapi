#!/usr/bin/env python3
"""
Script simple para verificar si las cuentas están actualizando saldos correctamente.
Versión simplificada que no requiere importar toda la configuración de la app.
"""

import os
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuración directa de base de datos (ajustar según sea necesario)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:password@localhost/database_name")

def quick_balance_check():
    """
    Verificación rápida de saldos sin importar modelos de la app
    """
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("🔍 Verificación rápida de saldos de cuentas...")
        print("=" * 50)
        
        # Consulta directa para obtener discrepancias
        query = text("""
        SELECT 
            a.code,
            a.name,
            a.debit_balance as stored_debit,
            a.credit_balance as stored_credit,
            COALESCE(real_balances.real_debit, 0) as real_debit,
            COALESCE(real_balances.real_credit, 0) as real_credit,
            ABS(COALESCE(a.debit_balance, 0) - COALESCE(real_balances.real_debit, 0)) as debit_diff,
            ABS(COALESCE(a.credit_balance, 0) - COALESCE(real_balances.real_credit, 0)) as credit_diff
        FROM accounts a
        LEFT JOIN (
            SELECT 
                jel.account_id,
                SUM(jel.debit_amount) as real_debit,
                SUM(jel.credit_amount) as real_credit
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            WHERE je.status = 'POSTED'
            GROUP BY jel.account_id
        ) real_balances ON a.id = real_balances.account_id
        WHERE a.allows_movements = true 
        AND a.is_active = true
        AND (
            ABS(COALESCE(a.debit_balance, 0) - COALESCE(real_balances.real_debit, 0)) > 0.01
            OR ABS(COALESCE(a.credit_balance, 0) - COALESCE(real_balances.real_credit, 0)) > 0.01
        )
        ORDER BY debit_diff + credit_diff DESC
        LIMIT 20
        """)
        
        result = db.execute(query).fetchall()
        
        if result:
            print(f"❌ Encontradas {len(result)} cuentas con discrepancias:")
            print("-" * 80)
            
            for row in result:
                print(f"Cuenta: {row.code} - {row.name}")
                print(f"  Débitos  -> Real: {float(row.real_debit):>12.2f} | Almacenado: {float(row.stored_debit or 0):>12.2f} | Diff: {float(row.debit_diff):>8.2f}")
                print(f"  Créditos -> Real: {float(row.real_credit):>12.2f} | Almacenado: {float(row.stored_credit or 0):>12.2f} | Diff: {float(row.credit_diff):>8.2f}")
                print()
        else:
            print("✅ No se encontraron discrepancias significativas")
        
        # Estadísticas generales
        stats_query = text("""
        SELECT 
            COUNT(*) as total_accounts,
            COUNT(CASE WHEN real_balances.account_id IS NOT NULL THEN 1 END) as accounts_with_movements,
            (SELECT COUNT(*) FROM journal_entries WHERE status = 'POSTED') as posted_entries,
            (SELECT COUNT(*) FROM journal_entry_lines jel 
             JOIN journal_entries je ON jel.journal_entry_id = je.id 
             WHERE je.status = 'POSTED') as posted_lines
        FROM accounts a
        LEFT JOIN (
            SELECT DISTINCT jel.account_id
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            WHERE je.status = 'POSTED'
        ) real_balances ON a.id = real_balances.account_id        WHERE a.allows_movements = true AND a.is_active = true
        """)
        
        stats = db.execute(stats_query).fetchone()
        
        if stats:
            print(f"📊 Estadísticas:")
            print(f"   - Cuentas activas que permiten movimientos: {stats.total_accounts}")
            print(f"   - Cuentas con movimientos contabilizados: {stats.accounts_with_movements}")
            print(f"   - Journal entries contabilizados: {stats.posted_entries}")
            print(f"   - Líneas contables contabilizadas: {stats.posted_lines}")
        else:
            print("📊 No se pudieron obtener estadísticas")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Revisa la configuración de DATABASE_URL")

if __name__ == "__main__":
    print("🏦 Verificación Rápida de Saldos")
    print(f"Database URL: {DATABASE_URL}")
    print()
    
    quick_balance_check()
    
    print("\n🎉 Verificación completada.")
