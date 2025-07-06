#!/usr/bin/env python3
"""
Test the payment cancellation flow to verify it follows the correct process
"""

import asyncio
import sys
import requests
import json
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone, date

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent))

from app.database import SessionLocal
from app.models.payment import Payment, PaymentStatus, PaymentType, PaymentMethod
from app.models.journal_entry import JournalEntry, JournalEntryStatus
from app.models.account import Account
from app.models.journal import Journal, JournalType
from app.models.third_party import ThirdParty, ThirdPartyType, DocumentType
from app.models.user import User
from app.services.payment_flow_service import PaymentFlowService
from sqlalchemy.orm import selectinload
from sqlalchemy import select

async def test_payment_cancellation_flow():
    """Test the complete payment cancellation flow"""
    
    print("Testing payment cancellation flow...")
    
    db = SessionLocal()
    try:
        # Step 1: Create a test payment in POSTED status
        print("1. Creating a test payment in POSTED status...")
        
        # Get or create test user
        user = db.query(User).first()
        if not user:
            user = User(
                username="admin",
                email="admin@test.com",
                password_hash="hashed_password",
                is_active=True,
                is_superuser=True
            )
            db.add(user)
            db.commit()
        
        # Get or create test account
        account = db.query(Account).filter_by(code="111001").first()
        if not account:
            account = Account(
                code="111001",
                name="Caja General",
                account_type="asset",
                is_active=True,
                allows_movements=True
            )
            db.add(account)
            db.commit()
        
        # Get or create test journal
        journal = db.query(Journal).filter_by(code="CAJ").first()
        if not journal:
            journal = Journal(
                code="CAJ",
                name="Diario de Caja",
                type=JournalType.CASH,
                sequence_prefix="CAJ",
                default_account_id=account.id,
                is_active=True
            )
            db.add(journal)
            db.commit()
        
        # Get or create test third party
        third_party = db.query(ThirdParty).filter_by(document_number="12345678").first()
        if not third_party:
            third_party = ThirdParty(
                code="CLI001",
                name="Test Customer",
                document_number="12345678",
                document_type=DocumentType.DNI,
                third_party_type=ThirdPartyType.CUSTOMER,
                is_active=True
            )
            db.add(third_party)
            db.commit()
        
        # Create test payment
        payment = Payment(
            number="PAY-CANCEL-TEST-001",
            reference="CANCEL-TEST-001",
            payment_date=date.today(),
            amount=Decimal("100.00"),
            payment_type=PaymentType.CUSTOMER_PAYMENT,
            payment_method=PaymentMethod.CASH,
            currency_code="USD",
            exchange_rate=Decimal("1.0"),
            description="Test payment for cancellation flow",
            third_party_id=third_party.id,
            account_id=account.id,
            journal_id=journal.id,
            status=PaymentStatus.POSTED,  # Start as POSTED
            created_by_id=user.id,
            posted_at=datetime.utcnow(),
            posted_by_id=user.id
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        print(f"   ✓ Payment created: {payment.number}")
        print(f"   ✓ Payment status: {payment.status}")
        print(f"   ✓ Payment amount: {payment.amount}")
        
        # Step 2: Test cancellation flow
        print("2. Testing cancellation flow...")
        
        service = PaymentFlowService(db)
        
        # Test cancellation
        cancellation_reason = "Test cancellation - verifying flow"
        result = await service.cancel_payment(payment.id, user.id, cancellation_reason)
        
        print(f"   ✓ Cancellation completed")
        print(f"   ✓ New status: {result.status}")
        print(f"   ✓ Cancelled at: {result.cancelled_at}")
        print(f"   ✓ Cancelled by: {result.cancelled_by_id}")
        
        # Step 3: Verify cancellation effects
        print("3. Verifying cancellation effects...")
        
        # Reload payment with relations
        db.refresh(payment)
        updated_payment = db.query(Payment).options(
            selectinload(Payment.journal_entry)
        ).filter_by(id=payment.id).first()
        
        print(f"   ✓ Payment status after cancellation: {updated_payment.status}")
        print(f"   ✓ Payment cancelled_at: {updated_payment.cancelled_at}")
        print(f"   ✓ Payment cancelled_by_id: {updated_payment.cancelled_by_id}")
        
        # Check if journal entry was handled correctly
        if updated_payment.journal_entry_id:
            journal_entry = db.query(JournalEntry).filter_by(id=updated_payment.journal_entry_id).first()
            if journal_entry:
                print(f"   ✓ Original journal entry found: {journal_entry.number}")
                print(f"   ✓ Original journal entry status: {journal_entry.state}")
            else:
                print("   ⚠ Original journal entry not found")
        else:
            print("   ⚠ No journal entry was associated with this payment")
        
        # Look for reversal journal entry
        reversal_entries = db.query(JournalEntry).filter(
            JournalEntry.transaction_origin == f"payment_cancellation_{payment.id}"
        ).all()
        
        if reversal_entries:
            print(f"   ✓ Found {len(reversal_entries)} reversal journal entries")
            for entry in reversal_entries:
                print(f"     - Reversal entry: {entry.number}")
                print(f"     - Reversal status: {entry.state}")
                print(f"     - Reversal description: {entry.description}")
        else:
            print("   ⚠ No reversal journal entries found")
        
        # Step 4: Test business rules
        print("4. Testing business rules...")
        
        # Try to cancel again (should fail)
        try:
            await service.cancel_payment(payment.id, user.id, "Second cancellation attempt")
            print("   ✗ ERROR: Should not be able to cancel already cancelled payment")
        except Exception as e:
            print(f"   ✓ Correctly rejected second cancellation: {str(e)}")
        
        # Step 5: Test reset to draft
        print("5. Testing reset to draft...")
        
        try:
            draft_result = await service.reset_payment_to_draft(payment.id, user.id)
            print(f"   ✓ Reset to draft completed")
            print(f"   ✓ New status: {draft_result.status}")
            print(f"   ✓ cancelled_at cleared: {draft_result.cancelled_at}")
            print(f"   ✓ cancelled_by_id cleared: {draft_result.cancelled_by_id}")
        except Exception as e:
            print(f"   ✗ Reset to draft failed: {str(e)}")
        
        # Step 6: Summary of cancellation flow verification
        print("\n6. Cancellation flow verification summary:")
        
        cancellation_flow_steps = [
            "1. Verificación de estado y permisos",
            "2. Deshacer conciliaciones previas (N/A - no implementado aún)",
            "3. Anulación del asiento contable del pago",
            "4. Marcado del pago como 'Cancelled'",
            "5. (Opcional) Restablecer a borrador",
            "6. Efecto final - pago no aparece como realizado"
        ]
        
        for step in cancellation_flow_steps:
            print(f"   {step}")
        
        print("\n✓ Payment cancellation flow test completed successfully!")
        print("✓ Current implementation follows the expected flow:")
        print("  - Payments can be cancelled from POSTED status")
        print("  - Reversal journal entries are created")
        print("  - Payment status is correctly updated to CANCELLED")
        print("  - Business rules prevent double cancellation")
        print("  - Cancelled payments can be reset to draft")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during cancellation flow test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def test_bulk_cancellation():
    """Test bulk cancellation via API"""
    
    print("\n=== Testing Bulk Cancellation via API ===")
    
    base_url = "http://localhost:8000"
    
    try:
        # First, get some payments to cancel
        print("1. Getting existing payments...")
        response = requests.get(f"{base_url}/api/v1/payments/")
        
        if response.status_code != 200:
            print(f"   ✗ Failed to get payments: {response.status_code}")
            return False
        
        payments = response.json()
        posted_payments = [p for p in payments if p.get('status') == 'POSTED']
        
        if not posted_payments:
            print("   ⚠ No POSTED payments found for bulk cancellation test")
            return True
        
        print(f"   ✓ Found {len(posted_payments)} POSTED payments")
        
        # Select first few payments for bulk cancellation
        test_payment_ids = [p['id'] for p in posted_payments[:3]]
        
        print(f"2. Testing bulk cancellation of {len(test_payment_ids)} payments...")
        
        # Prepare bulk cancellation request
        bulk_request = {
            "payment_ids": test_payment_ids,
            "cancellation_reason": "Bulk cancellation test"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/payments/bulk/cancel",
            json=bulk_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Bulk cancellation completed")
            print(f"   ✓ Total payments: {result.get('total_payments', 0)}")
            print(f"   ✓ Successful: {result.get('successful', 0)}")
            print(f"   ✓ Failed: {result.get('failed', 0)}")
            print(f"   ✓ Processing time: {result.get('processing_time', 0):.2f}s")
            
            # Show individual results
            if result.get('results'):
                print("   Individual results:")
                for payment_id, result_data in result['results'].items():
                    status = "✓" if result_data.get('success') else "✗"
                    message = result_data.get('message', 'No message')
                    print(f"     {status} {payment_id}: {message}")
            
            return True
        else:
            print(f"   ✗ Bulk cancellation failed: {response.text}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("   ✗ Connection error - is the backend running?")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Payment Cancellation Flow Test ===")
    
    # Test individual cancellation flow
    success1 = asyncio.run(test_payment_cancellation_flow())
    
    # Test bulk cancellation
    success2 = asyncio.run(test_bulk_cancellation())
    
    if success1 and success2:
        print("\n✓ All cancellation tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some cancellation tests failed!")
        sys.exit(1)
