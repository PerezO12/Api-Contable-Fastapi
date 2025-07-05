#!/usr/bin/env python3
"""Test script to debug account selection issue"""

import asyncio
import os
import sys
import uuid
from decimal import Decimal
from datetime import datetime, date

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from app.database import get_async_db
from app.models.account import Account, AccountType, AccountCategory
from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.third_party import ThirdParty
from app.services.payment_flow_service import PaymentFlowService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def test_account_selection():
    """Test account selection to debug the multiple results issue"""
    async for db in get_async_db():
        print("🔍 Testing account selection...")
        
        # Test LIABILITY accounts
        print("\n1. Testing LIABILITY accounts:")
        stmt = select(Account).where(
            Account.account_type == AccountType.LIABILITY,
            Account.category == AccountCategory.CURRENT_LIABILITY,
            Account.is_active == True
        ).order_by(Account.code)
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        print(f"   Found {len(accounts)} LIABILITY accounts:")
        for acc in accounts:
            print(f"     - {acc.code}: {acc.name}")
        
        # Test with limit(1)
        print("\n2. Testing LIABILITY accounts with limit(1):")
        stmt = select(Account).where(
            Account.account_type == AccountType.LIABILITY,
            Account.category == AccountCategory.CURRENT_LIABILITY,
            Account.is_active == True
        ).order_by(Account.code).limit(1)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        if account:
            print(f"   Selected account: {account.code}: {account.name}")
        else:
            print("   No account found")
        
        # Test ASSET accounts
        print("\n3. Testing ASSET accounts:")
        stmt = select(Account).where(
            Account.account_type == AccountType.ASSET,
            Account.category == AccountCategory.CURRENT_ASSET,
            Account.is_active == True
        ).order_by(Account.code)
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        print(f"   Found {len(accounts)} ASSET accounts:")
        for acc in accounts:
            print(f"     - {acc.code}: {acc.name}")
        
        # Test with limit(1)
        print("\n4. Testing ASSET accounts with limit(1):")
        stmt = select(Account).where(
            Account.account_type == AccountType.ASSET,
            Account.category == AccountCategory.CURRENT_ASSET,
            Account.is_active == True
        ).order_by(Account.code).limit(1)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        if account:
            print(f"   Selected account: {account.code}: {account.name}")
        else:
            print("   No account found")
        
        # Test the actual payment flow service methods
        print("\n5. Testing PaymentFlowService methods:")
        payment_service = PaymentFlowService(db)
        
        try:
            # Test supplier payable account
            print("   Testing _get_supplier_payable_account...")
            third_party = ThirdParty(name="Test Supplier", code="TEST001")
            account = await payment_service._get_supplier_payable_account(third_party)
            print(f"   Supplier payable account: {account.code}: {account.name}")
        except Exception as e:
            print(f"   Error getting supplier payable account: {e}")
        
        try:
            # Test customer receivable account
            print("   Testing _get_customer_receivable_account...")
            third_party = ThirdParty(name="Test Customer", code="TEST002")
            account = await payment_service._get_customer_receivable_account(third_party)
            print(f"   Customer receivable account: {account.code}: {account.name}")
        except Exception as e:
            print(f"   Error getting customer receivable account: {e}")
        
        break

if __name__ == "__main__":
    asyncio.run(test_account_selection())
