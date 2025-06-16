#!/usr/bin/env python3
"""
Test script to verify the journal entry API fix for validation errors.
This script simulates the scenario where a journal entry has data inconsistency.
"""

import asyncio
import sys
from pydantic import ValidationError
from app.schemas.journal_entry import JournalEntryLineRead
from datetime import datetime, date
import uuid


def test_validation_updated_behavior():
    """Test that having both payment_terms_id and due_date is now allowed."""
    print("Testing updated validation behavior...")
    
    # Create a journal entry line with both payment_terms_id and due_date
    # This should now be allowed since due_date can be auto-calculated from payment terms
    try:
        line_data = {
            "id": str(uuid.uuid4()),
            "journal_entry_id": str(uuid.uuid4()),
            "line_number": 1,
            "account_id": str(uuid.uuid4()),
            "debit_amount": 1000.00,
            "credit_amount": None,
            "description": "Test line with both payment terms and due date",
            "payment_terms_id": str(uuid.uuid4()),  # Now allowed together
            "due_date": date.today(),  # Now allowed together
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # This should now work without raising a ValidationError
        line = JournalEntryLineRead(**line_data)
        print("✅ SUCCESS: Validation correctly allows both payment_terms_id and due_date")
        return True
        
    except ValidationError as e:
        error_messages = [error['msg'] for error in e.errors()]
        print(f"❌ ERROR: Unexpected validation error: {error_messages}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected exception: {e}")
        return False


def test_valid_scenarios():
    """Test that valid scenarios work correctly."""
    print("\nTesting valid scenarios...")
    
    test_cases = [
        {
            "name": "Only payment_terms_id",
            "data": {
                "id": str(uuid.uuid4()),
                "journal_entry_id": str(uuid.uuid4()),
                "line_number": 1,
                "account_id": str(uuid.uuid4()),
                "debit_amount": 1000.00,
                "credit_amount": None,
                "description": "Test line with only payment terms",
                "payment_terms_id": str(uuid.uuid4()),
                "due_date": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        },
        {
            "name": "Only due_date",
            "data": {
                "id": str(uuid.uuid4()),
                "journal_entry_id": str(uuid.uuid4()),
                "line_number": 1,
                "account_id": str(uuid.uuid4()),
                "debit_amount": 1000.00,
                "credit_amount": None,
                "description": "Test line with only due date",
                "payment_terms_id": None,
                "due_date": date.today(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        },
        {
            "name": "Both payment_terms_id and due_date (now allowed)",
            "data": {
                "id": str(uuid.uuid4()),
                "journal_entry_id": str(uuid.uuid4()),
                "line_number": 1,
                "account_id": str(uuid.uuid4()),
                "debit_amount": 1000.00,
                "credit_amount": None,
                "description": "Test line with both payment terms and due date",
                "payment_terms_id": str(uuid.uuid4()),
                "due_date": date.today(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        },
        {
            "name": "Neither payment_terms_id nor due_date",
            "data": {
                "id": str(uuid.uuid4()),
                "journal_entry_id": str(uuid.uuid4()),
                "line_number": 1,
                "account_id": str(uuid.uuid4()),
                "debit_amount": 1000.00,
                "credit_amount": None,
                "description": "Test line with neither payment terms nor due date",
                "payment_terms_id": None,
                "due_date": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        try:
            line = JournalEntryLineRead(**test_case["data"])
            print(f"✅ SUCCESS: {test_case['name']} - validation passed")
        except ValidationError as e:
            print(f"❌ ERROR: {test_case['name']} - unexpected validation error: {e}")
            all_passed = False
        except Exception as e:
            print(f"❌ ERROR: {test_case['name']} - unexpected exception: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Main test function."""
    print("Journal Entry Validation Test")
    print("=" * 40)
    
    # Test 1: Updated validation behavior
    test1_passed = test_validation_updated_behavior()
    
    # Test 2: Valid scenarios
    test2_passed = test_valid_scenarios()
    
    print("\n" + "=" * 40)
    if test1_passed and test2_passed:
        print("🎉 All tests passed! The validation logic is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the validation logic.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
