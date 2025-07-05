#!/usr/bin/env python3
"""
Script de prueba para el flujo de confirmación de pagos
Verifica que el flujo de Odoo está implementado correctamente
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.payment_flow_service import PaymentFlowService
from app.models.payment import Payment, PaymentStatus
from app.models.journal_entry import JournalEntry
from app.models.journal import Journal
from app.models.account import Account
import uuid

def test_payment_confirmation():
    """Prueba el flujo completo de confirmación de pagos"""
    print("=== TESTING PAYMENT CONFIRMATION FLOW ===")
    
    # Conectar a la DB
    db = SessionLocal()
    
    try:
        # 1. Buscar un pago en estado DRAFT
        payment = db.query(Payment).filter(Payment.status == PaymentStatus.DRAFT).first()
        
        if not payment:
            print("❌ No DRAFT payments found. Creating one for testing...")
            # TODO: Crear un pago de prueba
            return
        
        print(f"📝 Found payment to confirm:")
        print(f"   Number: {payment.number}")
        print(f"   Status: {payment.status}")
        print(f"   Amount: {payment.amount}")
        print(f"   Third party: {payment.third_party.name if payment.third_party else 'None'}")
        print(f"   Account ID: {payment.account_id}")
        print(f"   Journal ID: {payment.journal_id}")
        
        # 2. Verificar que tiene diario asignado
        if not payment.journal_id:
            print("❌ Payment has no journal assigned")
            return
            
        journal = db.query(Journal).filter(Journal.id == payment.journal_id).first()
        if not journal:
            print(f"❌ Journal {payment.journal_id} not found")
            return
            
        print(f"   Journal: {journal.name} ({journal.type})")
        
        # 3. Verificar cuenta del diario
        if not journal.default_account_id:
            print(f"❌ Journal {journal.name} has no default account")
            return
            
        treasury_account = db.query(Account).filter(Account.id == journal.default_account_id).first()
        print(f"   Treasury account: {treasury_account.code} - {treasury_account.name}")
        
        # 4. Verificar cuentas de partner disponibles
        if payment.payment_type.value == 'customer_payment':
            partner_accounts = db.query(Account).filter(Account.code.like('1305%')).all()
            account_type = "receivable (1305%)"
        else:
            partner_accounts = db.query(Account).filter(Account.code.like('2205%')).all()
            account_type = "payable (2205%)"
            
        if not partner_accounts:
            print(f"❌ No {account_type} accounts found")
            return
            
        print(f"   Partner accounts available: {len(partner_accounts)} {account_type}")
        
        # 5. Intentar confirmar el pago
        print("\n🔄 Confirming payment...")
        service = PaymentFlowService(db)
        
        # Usar un UUID de usuario válido o crear uno de prueba
        confirmed_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        
        result = service.confirm_payment(payment.id, confirmed_user_id)
        
        print("✅ Payment confirmed successfully!")
        print(f"   Status: {result.status}")
        print(f"   Journal Entry ID: {result.journal_entry_id}")
        
        # 6. Verificar que se creó el asiento contable
        if result.journal_entry_id:
            journal_entry = db.query(JournalEntry).filter(JournalEntry.id == result.journal_entry_id).first()
            if journal_entry:
                print(f"   Journal Entry Number: {journal_entry.number}")
                print(f"   Journal Entry Status: {journal_entry.status}")
                print(f"   Total Debit: {journal_entry.total_debit}")
                print(f"   Total Credit: {journal_entry.total_credit}")
                print(f"   Lines count: {len(journal_entry.lines)}")
                
                for line in journal_entry.lines:
                    print(f"     Line {line.sequence}: {line.account.code} - {line.account.name}")
                    print(f"       Debit: {line.debit_amount}, Credit: {line.credit_amount}")
                    print(f"       Description: {line.description}")
            else:
                print("❌ Journal entry not found")
        
        print("\n✅ Payment confirmation flow completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during payment confirmation: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_payment_confirmation()
        if not payment:
            print("❌ No hay pagos en estado DRAFT para probar")
            return
        
        print(f"🔍 Probando pago: {payment.number} (ID: {payment.id})")
        print(f"   - Estado: {payment.status}")
        print(f"   - Monto: {payment.amount}")
        print(f"   - Journal ID: {payment.journal_id}")
        print(f"   - Account ID: {payment.account_id}")
        
        # Check if journal exists and has default account
        if payment.journal_id:
            journal = db.query(Journal).filter(Journal.id == payment.journal_id).first()
            if journal:
                print(f"   - Journal: {journal.name} ({journal.code})")
                print(f"   - Journal Default Account ID: {journal.default_account_id}")
                
                if journal.default_account_id:
                    account = db.query(Account).filter(Account.id == journal.default_account_id).first()
                    if account:
                        print(f"   - Default Account: {account.name} ({account.code})")
                    else:
                        print("   ❌ Default account not found")
                else:
                    print("   ⚠️ Journal has no default account configured")
            else:
                print("   ❌ Journal not found")
        else:
            print("   ⚠️ Payment has no journal assigned")
        
        # Check payment account
        if payment.account_id:
            payment_account = db.query(Account).filter(Account.id == payment.account_id).first()
            if payment_account:
                print(f"   - Payment Account: {payment_account.name} ({payment_account.code})")
            else:
                print("   ❌ Payment account not found")
        
        # Now test the validation
        print(f"\n🧪 Probando validación de cuentas...")
        service = PaymentService(db)
        try:
            accounts_config = service._get_default_accounts_for_payment(payment)
            print(f"✅ Validación exitosa:")
            print(f"   - Bank Account ID: {accounts_config.get('bank_account_id')}")
            print(f"   - Counterpart Account ID: {accounts_config.get('counterpart_account_id')}")
            print(f"   - Journal ID: {accounts_config.get('journal_id')}")
        except Exception as e:
            print(f"❌ Error en validación: {str(e)}")
            
        # Test full confirmation
        print(f"\n🚀 Probando confirmación completa...")
        try:
            # Create a dummy user ID for testing
            dummy_user_id = uuid.uuid4()
            result = service.confirm_payment(payment.id, dummy_user_id)
            print(f"✅ Confirmación exitosa:")
            print(f"   - Estado final: {result.status}")
            print(f"   - Número: {result.number}")
        except Exception as e:
            print(f"❌ Error en confirmación: {str(e)}")
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_payment_confirmation()
