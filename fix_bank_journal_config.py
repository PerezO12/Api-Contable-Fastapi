#!/usr/bin/env python3
"""
Script para corregir la configuración del journal bancario
para que use cuentas contables apropiadas.
"""

import sys
import os
import uuid
from decimal import Decimal

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.journal import Journal, JournalType
from app.models.bank_journal_config import BankJournalConfig
from app.models.account import Account

def fix_bank_journal_configuration():
    """
    Corrige la configuración del journal bancario para usar cuentas apropiadas
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=== Corrigiendo configuración de journal bancario ===")
        
        # 1. Obtener el journal bancario
        bank_journal = db.query(Journal).filter(
            Journal.type == JournalType.BANK,
            Journal.is_active == True
        ).first()
        
        if not bank_journal:
            print("No se encontró journal bancario")
            return
        
        print(f"Journal bancario: {bank_journal.name} ({bank_journal.code})")
        
        # 2. Obtener la configuración bancaria
        bank_config = bank_journal.get_bank_config()
        if not bank_config:
            print("No se encontró configuración bancaria")
            return
        
        print(f"Configuración bancaria encontrada")
        
        # 3. Mostrar configuración actual
        print(f"\n--- Configuración actual ---")
        print(f"Cuenta bancaria: {bank_config.bank_account.name if bank_config.bank_account else 'N/A'}")
        print(f"Cuenta recibo: {bank_config.inbound_receipt_account.name if bank_config.inbound_receipt_account else 'N/A'}")
        print(f"Cuenta pendientes salida: {bank_config.outbound_pending_account.name if bank_config.outbound_pending_account else 'N/A'}")
        print(f"Cuenta ganancias: {bank_config.profit_account.name if bank_config.profit_account else 'N/A'}")
        print(f"Cuenta pérdidas: {bank_config.loss_account.name if bank_config.loss_account else 'N/A'}")
        
        # 4. Buscar cuentas apropiadas
        print(f"\n--- Buscando cuentas apropiadas ---")
        
        # Cuenta bancaria (debe ser activo - código 1.x)
        bank_account = db.query(Account).filter(
            Account.code.like('1%'),
            Account.name.ilike('%banco%'),
            Account.is_active == True
        ).first()
        
        # Cuenta de gastos no asignados (código 5.x)
        expense_account = db.query(Account).filter(
            Account.code.like('5%'),
            Account.is_active == True
        ).first()
        
        # Cuenta de ingresos no asignados (código 4.x)  
        income_account = db.query(Account).filter(
            Account.code.like('4%'),
            Account.is_active == True
        ).first()
        
        # Cuenta transitoria o pendientes (código 2.x)
        pending_account = db.query(Account).filter(
            Account.code.like('2%'),
            Account.is_active == True
        ).first()
        
        print(f"Cuenta bancaria encontrada: {bank_account.code} - {bank_account.name}" if bank_account else "No se encontró cuenta bancaria")
        print(f"Cuenta gastos encontrada: {expense_account.code} - {expense_account.name}" if expense_account else "No se encontró cuenta de gastos")
        print(f"Cuenta ingresos encontrada: {income_account.code} - {income_account.name}" if income_account else "No se encontró cuenta de ingresos")
        print(f"Cuenta pendientes encontrada: {pending_account.code} - {pending_account.name}" if pending_account else "No se encontró cuenta pendientes")
        
        # 5. Actualizar configuración si es necesario
        needs_update = False
        
        if bank_account and bank_config.bank_account_id != bank_account.id:
            print(f"\n🔧 Actualizando cuenta bancaria principal")
            bank_config.bank_account_id = bank_account.id
            needs_update = True
        
        if income_account and bank_config.inbound_receipt_account_id != income_account.id:
            print(f"🔧 Actualizando cuenta de recibo (ingresos)")
            bank_config.inbound_receipt_account_id = income_account.id
            needs_update = True
        
        if expense_account and bank_config.outbound_pending_account_id != expense_account.id:
            print(f"🔧 Actualizando cuenta de pagos pendientes (gastos)")
            bank_config.outbound_pending_account_id = expense_account.id
            needs_update = True
        
        # Si no hay cuenta de pendientes, usar la de gastos
        if not bank_config.outbound_pending_account_id and expense_account:
            print(f"🔧 Configurando cuenta de pagos pendientes con cuenta de gastos")
            bank_config.outbound_pending_account_id = expense_account.id
            needs_update = True
        
        if needs_update:
            db.add(bank_config)
            db.commit()
            print(f"\n✅ Configuración actualizada")
        else:
            print(f"\n✅ Configuración ya está correcta")
        
        # 6. Mostrar configuración final
        db.refresh(bank_config)
        print(f"\n--- Configuración final ---")
        print(f"Cuenta bancaria: {bank_config.bank_account.name if bank_config.bank_account else 'N/A'}")
        print(f"Cuenta recibo: {bank_config.inbound_receipt_account.name if bank_config.inbound_receipt_account else 'N/A'}")
        print(f"Cuenta pendientes salida: {bank_config.outbound_pending_account.name if bank_config.outbound_pending_account else 'N/A'}")
        print(f"Cuenta ganancias: {bank_config.profit_account.name if bank_config.profit_account else 'N/A'}")
        print(f"Cuenta pérdidas: {bank_config.loss_account.name if bank_config.loss_account else 'N/A'}")
        
        # 7. Validar configuración
        errors = bank_config.validate_configuration()
        if errors:
            print(f"\n⚠ Errores de validación:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"\n✅ Configuración válida")
        
        print("\n=== Corrección completada ===")
        
    except Exception as e:
        print(f"Error durante la corrección: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_bank_journal_configuration()
