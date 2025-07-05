#!/usr/bin/env python3
"""
Script simple para verificar la estructura de datos antes de probar confirmación
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.payment import Payment, PaymentStatus
from app.models.journal import Journal
from app.models.account import Account

def check_data():
    db = SessionLocal()
    try:
        print("=== CHECKING DATA STRUCTURE ===")
        
        # Verificar si hay pagos en borrador
        draft_payments = db.query(Payment).filter(Payment.status == PaymentStatus.DRAFT).all()
        print(f'Found {len(draft_payments)} DRAFT payments')
        
        if draft_payments:
            payment = draft_payments[0]  # Tomar el primero
            print(f'\nPayment to test: {payment.number}')
            print(f'  Amount: {payment.amount}')
            print(f'  Journal ID: {payment.journal_id}')
            print(f'  Account ID: {payment.account_id}')
            print(f'  Third party: {payment.third_party.name if payment.third_party else "None"}')
            
            if payment.journal_id:
                journal = db.query(Journal).filter(Journal.id == payment.journal_id).first()
                if journal:
                    print(f'  Journal: {journal.name} ({journal.type})')
                    print(f'  Journal default account: {journal.default_account_id}')
                    
                    if journal.default_account_id:
                        account = db.query(Account).filter(Account.id == journal.default_account_id).first()
                        if account:
                            print(f'    Treasury Account: {account.code} - {account.name}')
                        else:
                            print(f'    ❌ Treasury account not found')
                    else:
                        print(f'    ❌ Journal has no default account')
                else:
                    print(f'  ❌ Journal not found')
            else:
                print(f'  ❌ No journal assigned')
        
        # Verificar cuentas disponibles
        receivable_accounts = db.query(Account).filter(Account.code.like('1305%')).count()
        payable_accounts = db.query(Account).filter(Account.code.like('2205%')).count()
        print(f'\nPartner accounts available:')
        print(f'  Receivable accounts (1305%): {receivable_accounts}')
        print(f'  Payable accounts (2205%): {payable_accounts}')
        
        if receivable_accounts == 0:
            print("❌ No receivable accounts found - need to set up chart of accounts")
        if payable_accounts == 0:
            print("❌ No payable accounts found - need to set up chart of accounts")
            
        return len(draft_payments) > 0 and receivable_accounts > 0 and payable_accounts > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if check_data():
        print("\n✅ Data structure looks good for testing payment confirmation")
    else:
        print("\n❌ Data structure needs setup before testing payment confirmation")
