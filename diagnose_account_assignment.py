#!/usr/bin/env python3
"""
Script para diagnosticar la asignación de cuentas en los asientos contables
Detecta cuando las mismas cuentas se usan en ambos lados del asiento.
"""

import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import SessionLocal
from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.journal import Journal, JournalType
from app.models.bank_journal_config import BankJournalConfig
from app.models.account import Account
from app.models.journal_entry import JournalEntry, JournalEntryLine
from app.models.third_party import ThirdParty
from decimal import Decimal
from datetime import datetime, date
import uuid

def diagnose_account_assignment():
    """Diagnosticar la configuración de cuentas en journals bancarios"""
    
    print("🔍 DIAGNÓSTICO DE ASIGNACIÓN DE CUENTAS")
    print("=" * 50)
    
    # Obtener sesión de base de datos
    session = SessionLocal()
    
    try:
        # 1. Revisar configuración del journal bancario
        print("\n1. CONFIGURACIÓN DEL JOURNAL BANCARIO")
        print("-" * 40)
        
        bank_journal = session.query(Journal).filter(
            Journal.type == JournalType.BANK
        ).first()
        
        if not bank_journal:
            print("❌ No hay journal bancario configurado")
            return
        
        print(f"✅ Journal bancario encontrado: {bank_journal.name} (ID: {bank_journal.id})")
        
        # Obtener configuración bancaria
        bank_config = bank_journal.get_bank_config()
        if not bank_config:
            print("❌ No hay configuración bancaria para el journal")
            return
        
        print(f"✅ Configuración bancaria encontrada")
        
        # 2. Revisar cuentas configuradas
        print("\n2. CUENTAS CONFIGURADAS EN EL JOURNAL BANCARIO")
        print("-" * 50)
        
        def print_account_info(account, label):
            if account:
                print(f"  {label}: {account.code} - {account.name} (ID: {account.id})")
            else:
                print(f"  {label}: ❌ NO CONFIGURADA")
        
        print_account_info(bank_journal.default_account, "Cuenta por defecto del journal")
        print_account_info(bank_config.inbound_receipt_account, "Cuenta recibo entrada")
        print_account_info(bank_config.outbound_pending_account, "Cuenta pendiente salida")
        print_account_info(bank_config.loss_account, "Cuenta de pérdidas")
        print_account_info(bank_config.profit_account, "Cuenta de ganancias")
        print_account_info(bank_config.bank_account, "Cuenta bancaria principal")
        
        # 3. Obtener un pago para probar
        print("\n3. PRUEBA CON PAGO EXISTENTE")
        print("-" * 40)
        
        # Buscar un pago a proveedor en estado borrador
        payment = session.query(Payment).filter(
            Payment.payment_type == PaymentType.SUPPLIER_PAYMENT,
            Payment.status == PaymentStatus.DRAFT
        ).first()
        
        if not payment:
            print("❌ No hay pagos en borrador para probar")
            return
        
        print(f"✅ Pago encontrado: {payment.number} - {payment.amount}")
        print(f"   Tercero: {payment.third_party.name if payment.third_party else 'N/A'}")
        print(f"   Cuenta bancaria: {payment.account.code} - {payment.account.name}")
        print(f"   Tipo: {payment.payment_type}")
        
        # 4. Simular determinación de cuentas
        print("\n4. SIMULACIÓN DE DETERMINACIÓN DE CUENTAS")
        print("-" * 50)
        
        # Cuenta bancaria (siempre la del pago)
        bank_account = payment.account
        print(f"  Cuenta bancaria (HABER): {bank_account.code} - {bank_account.name}")
        
        # Cuenta de gastos (según configuración del journal)
        if bank_config.outbound_pending_account:
            expense_account = bank_config.outbound_pending_account
            print(f"  Cuenta gastos (DEBE): {expense_account.code} - {expense_account.name}")
        else:
            print("  Cuenta gastos (DEBE): ❌ NO CONFIGURADA")
            expense_account = None
        
        # 5. Verificar si son la misma cuenta
        print("\n5. VERIFICACIÓN DE CONFLICTO")
        print("-" * 40)
        
        if expense_account and bank_account.id == expense_account.id:
            print("🚨 PROBLEMA DETECTADO: La cuenta bancaria y la cuenta de gastos son la misma!")
            print(f"   Ambas apuntan a: {bank_account.code} - {bank_account.name}")
            print("   Esto causa que el asiento se cancele a sí mismo (débito = crédito en la misma cuenta)")
        elif expense_account:
            print("✅ Las cuentas son diferentes, el asiento debería impactar correctamente")
        else:
            print("❌ Falta configurar la cuenta de gastos")
        
        # 6. Buscar cuentas de gastos disponibles
        print("\n6. CUENTAS DE GASTOS DISPONIBLES")
        print("-" * 40)
        
        expense_accounts = session.query(Account).filter(
            Account.code.like('5%'),
            Account.is_active == True
        ).order_by(Account.code).all()
        
        print(f"  Encontradas {len(expense_accounts)} cuentas de gastos:")
        for acc in expense_accounts[:5]:  # Mostrar solo las primeras 5
            print(f"    {acc.code} - {acc.name}")
        
        # 7. Revisar asientos existentes con problemas
        print("\n7. ASIENTOS CONTABLES CON PROBLEMAS")
        print("-" * 50)
        
        # Buscar asientos donde ambas líneas usan la misma cuenta
        problematic_entries = session.query(JournalEntry).join(
            JournalEntryLine
        ).filter(
            JournalEntry.transaction_origin.in_(['PAYMENT', 'COLLECTION'])
        ).all()
        
        problem_count = 0
        for entry in problematic_entries:
            lines = session.query(JournalEntryLine).filter(
                JournalEntryLine.journal_entry_id == entry.id
            ).all()
            
            if len(lines) == 2:
                account_ids = set(line.account_id for line in lines)
                if len(account_ids) == 1:  # Misma cuenta en ambas líneas
                    problem_count += 1
                    if problem_count <= 3:  # Mostrar solo los primeros 3
                        print(f"    Asiento {entry.number}: {entry.description}")
                        print(f"      Ambas líneas usan cuenta: {lines[0].account.code} - {lines[0].account.name}")
        
        if problem_count == 0:
            print("  ✅ No se encontraron asientos con este problema")
        else:
            print(f"  🚨 Se encontraron {problem_count} asientos con el mismo problema")
        
        print("\n" + "=" * 50)
        print("DIAGNÓSTICO COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    diagnose_account_assignment()
