#!/usr/bin/env python3
"""
Test script to verify the fix for payment cancellation with proper user validation
"""
import asyncio
import sys
sys.path.append('.')

from app.database import get_async_db
from app.services.payment_flow_service import PaymentFlowService
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

# Configure logging to see detailed errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_payment_cancel_with_valid_user():
    """Test payment cancellation with a valid user from the database"""
    
    # Get database session
    async for db in get_async_db():
        try:
            # 1. Get a real user from the database
            logger.info("🔍 Finding valid user for testing...")
            
            user_stmt = select(User).limit(1)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error("❌ No users found in database")
                return
                
            logger.info(f"✅ Found user: {user.email} (ID: {user.id})")
            
            # 2. Get a payment to cancel
            logger.info("🔍 Finding payments for cancellation test...")
            
            payment_stmt = select(Payment).where(
                Payment.status == PaymentStatus.POSTED
            ).limit(1)
            
            payment_result = await db.execute(payment_stmt)
            payment = payment_result.scalar_one_or_none()
            
            if not payment:
                logger.error("❌ No POSTED payments found for testing")
                return
                
            logger.info(f"✅ Found payment: {payment.number} (ID: {payment.id}, Status: {payment.status})")
            
            # 3. Test the cancellation service with valid user
            logger.info("\n🚀 Testing payment cancellation with valid user...")
            
            service = PaymentFlowService(db)
            
            try:
                result = await service.cancel_payment(
                    payment_id=payment.id,
                    cancelled_by_id=user.id,
                    reason="Test cancellation with valid user"
                )
                
                logger.info(f"✅ Payment cancellation successful!")
                logger.info(f"  - Payment: {result.number}")
                logger.info(f"  - Status: {result.status}")
                logger.info(f"  - Cancelled by: {result.cancelled_by_id}")
                logger.info(f"  - Cancelled at: {result.cancelled_at}")
                
            except Exception as e:
                logger.error(f"❌ Payment cancellation failed: {str(e)}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                
                # Check if it's the same foreign key error
                if "ForeignKeyViolationError" in str(e):
                    logger.error("❌ Still getting foreign key error - the fix didn't work")
                elif "User with ID" in str(e) and "not found" in str(e):
                    logger.error("❌ User validation error - but user should exist")
                else:
                    logger.error(f"❌ Different error: {str(e)}")
                
        except Exception as e:
            logger.error(f"💥 Database error: {str(e)}")
            import traceback
            logger.error(f"💥 Full traceback:\n{traceback.format_exc()}")
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(test_payment_cancel_with_valid_user())
