#!/usr/bin/env python3
"""
Test script to validate the bulk payment cancellation API with a valid user
"""

import asyncio
import logging
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.services.payment_flow_service import PaymentFlowService
from sqlalchemy import select

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_bulk_cancel_api():
    """Test the bulk payment cancellation API with a valid user"""
    
    # Get database session
    db = None
    try:
        async for db in get_db():
            logger.info("🔍 Finding valid user for testing...")
            
            # Get a valid user
            user_result = await db.execute(select(User).limit(1))
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error("❌ No users found in database")
                return False
                
            logger.info(f"✅ Found user: {user.email} (ID: {user.id})")
            
            logger.info("🔍 Finding payments for bulk cancellation test...")
            
            # Find payments that can be cancelled
            payments_result = await db.execute(
                select(Payment).where(Payment.status == PaymentStatus.POSTED).limit(2)
            )
            payments_list = payments_result.scalars().all()
            
            if not payments_list:
                logger.error("❌ No POSTED payments found for testing")
                return False
                
            payment_ids = [payment.id for payment in payments_list]
            logger.info(f"✅ Found {len(payment_ids)} payments for bulk cancellation:")
            for payment in payments_list:
                logger.info(f"  - {payment.number} (ID: {payment.id}, Status: {payment.status})")
            
            # Test the bulk cancellation service
            logger.info("\n🚀 Testing bulk payment cancellation service...")
            
            # Create a service instance
            service = PaymentFlowService(db)
            
            # Test the service directly
            try:
                results = await service.bulk_cancel_payments(
                    payment_ids=payment_ids,
                    cancelled_by_id=user.id,
                    cancellation_reason="Test bulk cancellation with valid user"
                )
                
                logger.info("✅ Bulk payment cancellation successful!")
                logger.info(f"📊 Results: {results['successful']}/{results['total_payments']} successful")
                
                # Check individual results
                for payment_id, result in results["results"].items():
                    if result["success"]:
                        logger.info(f"  ✅ {result['payment_number']}: {result['message']}")
                    else:
                        logger.error(f"  ❌ {payment_id}: {result['error']}")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Bulk cancellation failed: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                return False
            
            # Only process the first database session
            break
            
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        return False

async def main():
    """Main test function"""
    success = await test_bulk_cancel_api()
    
    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
