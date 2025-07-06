#!/usr/bin/env python3
"""
Test script to reproduce the 422 error in bulk payment cancellation
"""
import asyncio
import sys
sys.path.append('.')

from app.database import get_async_db
from app.services.payment_flow_service import PaymentFlowService
from app.models.payment import Payment, PaymentStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

# Configure logging to see detailed errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bulk_cancel_error():
    """Test bulk cancel with real payment data to reproduce the 422 error"""
    
    # Get database session
    async for db in get_async_db():
        try:
            # 1. First, get some actual payments from the database
            logger.info("🔍 Finding payments for bulk cancel test...")
            
            # Get payments in different states
            stmt = select(Payment).where(
                Payment.status.in_([PaymentStatus.DRAFT, PaymentStatus.POSTED])
            ).limit(5)
            
            result = await db.execute(stmt)
            payments = result.scalars().all()
            
            if not payments:
                logger.error("❌ No payments found for testing")
                return
                
            payment_ids = [p.id for p in payments]
            logger.info(f"✅ Found {len(payments)} payments for testing:")
            for p in payments:
                logger.info(f"  - {p.number} (ID: {p.id}, Status: {p.status})")
            
            # 2. Test the bulk cancel service directly
            logger.info("\n🚀 Testing bulk cancel service...")
            
            service = PaymentFlowService(db)
            
            # Test with a fake user ID (this might be the issue)
            fake_user_id = uuid.uuid4()
            logger.info(f"👤 Using fake user ID: {fake_user_id}")
            
            try:
                result = await service.bulk_cancel_payments(
                    payment_ids=payment_ids,
                    cancelled_by_id=fake_user_id,
                    cancellation_reason="Test cancellation"
                )
                
                logger.info(f"✅ Bulk cancel successful:")
                logger.info(f"  - Total: {result.get('total_payments', 0)}")
                logger.info(f"  - Successful: {result.get('successful', 0)}")
                logger.info(f"  - Failed: {result.get('failed', 0)}")
                
                # Print detailed results
                for payment_id, result_data in result.get('results', {}).items():
                    if result_data.get('success'):
                        logger.info(f"  ✅ {payment_id}: {result_data.get('message', 'Success')}")
                    else:
                        logger.error(f"  ❌ {payment_id}: {result_data.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"❌ Bulk cancel failed with error: {str(e)}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                logger.error(f"❌ This might be the 422 error cause!")
                
                # Let's check what the actual error details are
                import traceback
                logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
                
        except Exception as e:
            logger.error(f"💥 Database error: {str(e)}")
            import traceback
            logger.error(f"💥 Full traceback:\n{traceback.format_exc()}")
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(test_bulk_cancel_error())
