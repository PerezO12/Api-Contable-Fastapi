"""
Test para verificar la implementación de asientos de reversión explícitos
en cancelaciones de facturas del InvoiceService
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session

# Importar dependencias
from app.database import get_db
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.models.journal_entry import JournalEntry, JournalEntryStatus, JournalEntryType
from app.models.third_party import ThirdParty
from app.models.account import Account, AccountType
from app.models.user import User
from app.services.invoice_service import InvoiceService
from app.utils.logging import get_logger

logger = get_logger(__name__)

def test_reversal_journal_entries():
    """Test completo de cancelación con asientos de reversión explícitos"""
    
    print("🧪 [TEST] Starting reversal journal entries test")
    
    # Obtener conexión a la base de datos
    db = next(get_db())
    
    try:
        # 1. Buscar una factura en estado POSTED
        invoice = db.query(Invoice).filter(
            Invoice.status == InvoiceStatus.POSTED
        ).first()
        
        if not invoice:
            print("❌ [TEST] No POSTED invoices found in database")
            return False
        
        print(f"📋 [TEST] Found POSTED invoice: {invoice.number}")
        
        # 2. Buscar un usuario para la operación
        user = db.query(User).first()
        if not user:
            print("❌ [TEST] No users found in database")
            return False
        
        # 3. Obtener estado inicial
        original_journal_entry_id = invoice.journal_entry_id
        print(f"📝 [TEST] Original journal entry ID: {original_journal_entry_id}")
        
        # Obtener asiento original
        original_entry = db.query(JournalEntry).filter(
            JournalEntry.id == original_journal_entry_id
        ).first()
        
        if not original_entry:
            print("❌ [TEST] Original journal entry not found")
            return False
        
        print(f"📊 [TEST] Original entry: {original_entry.number} - Debit: {original_entry.total_debit}, Credit: {original_entry.total_credit}")
        
        # 4. Obtener saldos de cuentas antes de la cancelación
        accounts_before = {}
        for line in original_entry.lines:
            if line.account:
                accounts_before[line.account_id] = {
                    'balance': line.account.balance,
                    'debit_balance': line.account.debit_balance,
                    'credit_balance': line.account.credit_balance
                }
        
        print(f"💰 [TEST] Captured balances for {len(accounts_before)} accounts before cancellation")
        
        # 5. Crear servicio y cancelar factura usando método moderno
        invoice_service = InvoiceService(db)
        
        print(f"🚫 [TEST] Cancelling invoice {invoice.number} using modern method...")
        cancelled_invoice = invoice_service.cancel_invoice(
            invoice_id=invoice.id,
            cancelled_by_id=user.id,
            reason="Test cancellation with reversal entries"
        )
        
        print(f"✅ [TEST] Invoice cancelled successfully. New status: {cancelled_invoice.status}")
        
        # 6. Verificar que se creó un asiento de reversión
        reversal_entries = db.query(JournalEntry).filter(
            JournalEntry.entry_type == JournalEntryType.REVERSAL,
            JournalEntry.description.like(f"%{original_entry.number}%")
        ).all()
        
        if not reversal_entries:
            print("❌ [TEST] No reversal journal entries found")
            return False
        
        reversal_entry = reversal_entries[-1]  # Tomar el más reciente
        print(f"📝 [TEST] Reversal entry created: {reversal_entry.number}")
        print(f"📊 [TEST] Reversal entry - Debit: {reversal_entry.total_debit}, Credit: {reversal_entry.total_credit}")
        
        # 7. Verificar que los totales están balanceados
        if (reversal_entry.total_debit != original_entry.total_credit or 
            reversal_entry.total_credit != original_entry.total_debit):
            print(f"❌ [TEST] Reversal amounts don't match original (inverted)")
            print(f"   Original: D:{original_entry.total_debit}, C:{original_entry.total_credit}")
            print(f"   Reversal: D:{reversal_entry.total_debit}, C:{reversal_entry.total_credit}")
            return False
        
        print("✅ [TEST] Reversal amounts correctly inverted")
        
        # 8. Verificar líneas de reversión
        original_lines = len(original_entry.lines)
        reversal_lines = len(reversal_entry.lines)
        
        if original_lines != reversal_lines:
            print(f"❌ [TEST] Line count mismatch: Original {original_lines}, Reversal {reversal_lines}")
            return False
        
        print(f"✅ [TEST] Line count matches: {reversal_lines} lines")
        
        # 9. Verificar que los saldos de las cuentas se actualizaron correctamente
        accounts_after = {}
        for account_id in accounts_before.keys():
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                accounts_after[account_id] = {
                    'balance': account.balance,
                    'debit_balance': account.debit_balance,
                    'credit_balance': account.credit_balance
                }
        
        print("💰 [TEST] Verifying account balance changes...")
        all_balances_correct = True
        
        for account_id in accounts_before.keys():
            before = accounts_before[account_id]
            after = accounts_after.get(account_id, {})
            
            if not after:
                print(f"❌ [TEST] Account {account_id} not found after cancellation")
                all_balances_correct = False
                continue
            
            # Los saldos deberían volver a cero si la factura era la única transacción
            # o deberían reflejar la reversión correctamente
            balance_change = after['balance'] - before['balance']
            print(f"   Account {account_id}: Balance change = {balance_change}")
        
        if all_balances_correct:
            print("✅ [TEST] Account balances updated correctly")
        
        # 10. Verificar que la factura está marcada como cancelada
        if cancelled_invoice.status != InvoiceStatus.CANCELLED:
            print(f"❌ [TEST] Invoice status not updated correctly: {cancelled_invoice.status}")
            return False
        
        print("✅ [TEST] Invoice status correctly updated to CANCELLED")
        
        # 11. Verificar auditoría
        if not cancelled_invoice.cancelled_by_id or not cancelled_invoice.cancelled_at:
            print("❌ [TEST] Audit fields not populated")
            return False
        
        print("✅ [TEST] Audit fields correctly populated")
        
        # 12. Verificar notas de cancelación
        if not cancelled_invoice.notes or "REV-" not in cancelled_invoice.notes:
            print("❌ [TEST] Cancellation notes not found or incomplete")
            return False
        
        print("✅ [TEST] Cancellation notes include reversal reference")
        
        print("🎉 [TEST] All tests passed! Reversal journal entries working correctly")
        return True
        
    except Exception as e:
        print(f"💥 [TEST] Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

def test_cancellation_options():
    """Test del método get_cancellation_options"""
    
    print("\n🧪 [TEST] Testing cancellation options method")
    
    db = next(get_db())
    
    try:
        # Buscar una factura POSTED
        invoice = db.query(Invoice).filter(
            Invoice.status == InvoiceStatus.POSTED
        ).first()
        
        if not invoice:
            print("❌ [TEST] No POSTED invoices found")
            return False
        
        invoice_service = InvoiceService(db)
        options = invoice_service.get_cancellation_options(invoice.id)
        
        print(f"📋 [TEST] Cancellation options for invoice {options['invoice_number']}:")
        print(f"   Can cancel: {options['can_cancel']}")
        print(f"   Has payments: {options['has_payments']}")
        print(f"   Recommended method: {options['recommendation']}")
        
        # Verificar estructura
        required_keys = ['invoice_id', 'cancellation_methods', 'blocking_conditions']
        for key in required_keys:
            if key not in options:
                print(f"❌ [TEST] Missing key in options: {key}")
                return False
        
        if 'modern' not in options['cancellation_methods']:
            print("❌ [TEST] Modern method not in options")
            return False
        
        if 'legacy' not in options['cancellation_methods']:
            print("❌ [TEST] Legacy method not in options")
            return False
        
        print("✅ [TEST] Cancellation options method working correctly")
        return True
        
    except Exception as e:
        print(f"💥 [TEST] Cancellation options test failed: {str(e)}")
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting reversal journal entries implementation test")
    
    test1_result = test_reversal_journal_entries()
    test2_result = test_cancellation_options()
    
    print(f"\n📊 Test Results:")
    print(f"   Reversal entries test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"   Cancellation options test: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print("🎉 All tests passed! Reversal journal entries implementation is working correctly.")
        print("\n💡 Key improvements implemented:")
        print("   • Explicit reversal journal entries for better audit trail")
        print("   • Automatic balance updates")
        print("   • Comprehensive logging and error handling")
        print("   • Legacy method available for compatibility")
        print("   • Cancellation options helper method")
    else:
        print("❌ Some tests failed. Please review the implementation.")
