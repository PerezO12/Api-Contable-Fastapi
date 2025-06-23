#!/usr/bin/env python3
"""
Script para validar que los saldos de las cuentas contables están correctos
comparando con los journal entries contabilizados.

Este script ayuda a identificar discrepancias entre los saldos de las cuentas
y los movimientos registrados en los journal entries.
"""

import sys
import os
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Agregar el directorio padre al path para importar módulos de la app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    from app.models.account import Account
    from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus
except ImportError as e:
    print(f"❌ Error al importar módulos de la aplicación: {e}")
    print("Asegúrate de ejecutar este script desde el directorio raíz del proyecto API Contable")
    sys.exit(1)

# Configurar conexión a base de datos
database_url = settings.database_url
if not database_url:
    print("❌ ERROR: DATABASE_URL no está configurada en las variables de entorno")
    print("Configura la variable de entorno DATABASE_URL antes de ejecutar este script")
    sys.exit(1)

try:
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    
    # Probar la conexión
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Conexión a base de datos establecida correctamente")
    
except Exception as e:
    print(f"❌ Error al conectar con la base de datos: {e}")
    print(f"URL de conexión: {database_url}")
    sys.exit(1)

def validate_account_balances():
    """
    Valida que los saldos de las cuentas coincidan con los journal entries
    """
    db = SessionLocal()
    
    try:
        print("🔍 Validando saldos de cuentas contables...")
        print("=" * 60)
        
        # Obtener todas las cuentas que permiten movimientos
        accounts = db.query(Account).filter(
            Account.allows_movements == True,
            Account.is_active == True
        ).all()
        
        discrepancies = []
        total_accounts_checked = 0
        accounts_with_movements = 0
        
        for account in accounts:
            total_accounts_checked += 1
            
            # Calcular saldos reales desde journal entries POSTED
            real_debit = db.execute(text("""
                SELECT COALESCE(SUM(jel.debit_amount), 0) as total_debit
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_id = :account_id 
                AND je.status = 'POSTED'
            """), {"account_id": str(account.id)}).scalar()
            
            real_credit = db.execute(text("""
                SELECT COALESCE(SUM(jel.credit_amount), 0) as total_credit
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_id = :account_id 
                AND je.status = 'POSTED'
            """), {"account_id": str(account.id)}).scalar()
            
            real_debit = Decimal(str(real_debit))
            real_credit = Decimal(str(real_credit))
            
            # Si hay movimientos, contar como cuenta con movimientos
            if real_debit > 0 or real_credit > 0:
                accounts_with_movements += 1
            
            # Comparar con saldos almacenados en la cuenta
            stored_debit = account.debit_balance or Decimal('0')
            stored_credit = account.credit_balance or Decimal('0')
            
            # Calcular diferencias
            debit_diff = abs(real_debit - stored_debit)
            credit_diff = abs(real_credit - stored_credit)
            
            # Si hay diferencias significativas (más de 1 centavo)
            if debit_diff > Decimal('0.01') or credit_diff > Decimal('0.01'):
                discrepancies.append({
                    'account': account,
                    'real_debit': real_debit,
                    'stored_debit': stored_debit,
                    'debit_diff': debit_diff,
                    'real_credit': real_credit,
                    'stored_credit': stored_credit,
                    'credit_diff': credit_diff
                })
        
        # Mostrar resultados
        print(f"📊 Resumen de validación:")
        print(f"   - Cuentas verificadas: {total_accounts_checked}")
        print(f"   - Cuentas con movimientos: {accounts_with_movements}")
        print(f"   - Discrepancias encontradas: {len(discrepancies)}")
        print()
        
        if discrepancies:
            print("❌ DISCREPANCIAS ENCONTRADAS:")
            print("-" * 80)
            
            for disc in discrepancies[:10]:  # Mostrar solo las primeras 10
                acc = disc['account']
                print(f"Cuenta: {acc.code} - {acc.name}")
                print(f"  Débitos  -> Real: {disc['real_debit']:>12.2f} | Almacenado: {disc['stored_debit']:>12.2f} | Diff: {disc['debit_diff']:>8.2f}")
                print(f"  Créditos -> Real: {disc['real_credit']:>12.2f} | Almacenado: {disc['stored_credit']:>12.2f} | Diff: {disc['credit_diff']:>8.2f}")
                print()
            
            if len(discrepancies) > 10:
                print(f"... y {len(discrepancies) - 10} discrepancias más")
                
        else:
            print("✅ ¡Todos los saldos están correctos!")
        
        # Información adicional sobre journal entries
        posted_entries_count = db.query(JournalEntry).filter(
            JournalEntry.status == JournalEntryStatus.POSTED
        ).count()
        
        total_posted_lines = db.execute(text("""
            SELECT COUNT(*) 
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            WHERE je.status = 'POSTED'
        """)).scalar()
        
        print(f"📈 Información adicional:")
        print(f"   - Journal entries contabilizados: {posted_entries_count}")
        print(f"   - Líneas contables contabilizadas: {total_posted_lines}")
        
        return discrepancies
        
    finally:
        db.close()

def fix_account_balances():
    """
    Corrige los saldos de las cuentas recalculándolos desde los journal entries
    """
    db = SessionLocal()
    
    try:
        print("🔧 Corrigiendo saldos de cuentas contables...")
        print("=" * 60)
        
        # Obtener todas las cuentas que permiten movimientos
        accounts = db.query(Account).filter(
            Account.allows_movements == True,
            Account.is_active == True
        ).all()
        
        fixed_count = 0
        
        for account in accounts:
            # Calcular saldos reales desde journal entries POSTED
            real_debit = db.execute(text("""
                SELECT COALESCE(SUM(jel.debit_amount), 0) as total_debit
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_id = :account_id 
                AND je.status = 'POSTED'
            """), {"account_id": str(account.id)}).scalar()
            
            real_credit = db.execute(text("""
                SELECT COALESCE(SUM(jel.credit_amount), 0) as total_credit
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_id = :account_id 
                AND je.status = 'POSTED'
            """), {"account_id": str(account.id)}).scalar()
            
            real_debit = Decimal(str(real_debit))
            real_credit = Decimal(str(real_credit))
            
            # Actualizar los saldos en la cuenta
            old_debit = account.debit_balance or Decimal('0')
            old_credit = account.credit_balance or Decimal('0')
            
            account.debit_balance = real_debit
            account.credit_balance = real_credit
            account.balance = account.get_balance_display()
            
            # Si hubo cambios, incrementar contador
            if (abs(old_debit - real_debit) > Decimal('0.01') or 
                abs(old_credit - real_credit) > Decimal('0.01')):
                fixed_count += 1
                print(f"Corregida: {account.code} - {account.name}")
                print(f"  Débitos:  {old_debit:>12.2f} -> {real_debit:>12.2f}")
                print(f"  Créditos: {old_credit:>12.2f} -> {real_credit:>12.2f}")
                print()
        
        db.commit()
        print(f"✅ Proceso completado. Cuentas corregidas: {fixed_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al corregir saldos: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🏦 Validador de Saldos de Cuentas Contables")
    print("=" * 50)
    print()
    
    try:
        # Primero validar
        discrepancies = validate_account_balances()
        
        if discrepancies:
            print()
            print("¿Desea corregir automáticamente los saldos? (s/N): ", end="")
            response = input().strip().lower()
            
            if response == 's' or response == 'si':
                print()
                fix_account_balances()
            else:
                print("Los saldos no fueron corregidos.")
        
        print("\n🎉 Proceso terminado.")
        
    except KeyboardInterrupt:
        print("\n❌ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        sys.exit(1)
