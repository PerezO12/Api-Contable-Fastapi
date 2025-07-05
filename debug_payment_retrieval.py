"""
Debug script to test payment retrieval
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.payment_service import PaymentService
from app.models.payment import Payment
import json

def test_payment_retrieval():
    """Test payment retrieval to debug the empty data issue"""
    db = SessionLocal()
    try:
        # First, let's see how many payments are in the database
        total_payments = db.query(Payment).count()
        print(f"Total payments in database: {total_payments}")
        
        # Get the first few payments directly
        payments = db.query(Payment).limit(5).all()
        print(f"Direct query returned {len(payments)} payments")
        
        for payment in payments:
            print(f"Payment ID: {payment.id}, Number: {payment.number}, Amount: {payment.amount}, Status: {payment.status}")
        
        # Now test the service
        payment_service = PaymentService(db)
        result = payment_service.get_payments(page=1, size=10)
        
        print(f"\nService result:")
        print(f"Total: {result.total}")
        print(f"Data length: {len(result.data)}")
        print(f"Page: {result.page}")
        print(f"Per page: {result.per_page}")
        print(f"Pages: {result.pages}")
        
        if result.data:
            print("Payment data found:")
            for payment in result.data:
                print(f"- ID: {payment.id}, Number: {payment.number}")
        else:
            print("No payment data in result!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_payment_retrieval()
