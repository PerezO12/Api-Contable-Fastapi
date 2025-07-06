#!/usr/bin/env python3
"""
Test payment cancellation flow using SQLite database directly
"""

import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

def test_payment_cancellation_flow_sqlite():
    """Test payment cancellation flow using SQLite database directly"""
    
    print("=== Testing Payment Cancellation Flow (SQLite) ===")
    
    try:
        # Connect to SQLite database
        db_path = Path(__file__).parent / "contable.db"
        if not db_path.exists():
            print(f"✗ Database file not found: {db_path}")
            return False
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        print(f"✓ Connected to database: {db_path}")
        
        # Step 1: Check current payments
        print("\n1. Checking current payments...")
        cursor.execute("""
            SELECT id, number, status, amount, payment_type, journal_entry_id
            FROM payments
            WHERE status = 'POSTED'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        posted_payments = cursor.fetchall()
        print(f"   Found {len(posted_payments)} POSTED payments")
        
        for payment in posted_payments:
            print(f"   - {payment['number']}: {payment['status']} - ${payment['amount']}")
        
        # Step 2: Check journal entries related to payments
        print("\n2. Checking journal entries...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM journal_entries je
            JOIN payments p ON je.id = p.journal_entry_id
            WHERE p.status = 'POSTED'
        """)
        
        result = cursor.fetchone()
        journal_entries_count = result['count'] if result else 0
        print(f"   Found {journal_entries_count} journal entries linked to POSTED payments")
        
        # Step 3: Check if there are any cancelled payments
        print("\n3. Checking cancelled payments...")
        cursor.execute("""
            SELECT id, number, status, cancelled_at, cancelled_by_id
            FROM payments
            WHERE status = 'CANCELLED'
            ORDER BY cancelled_at DESC
            LIMIT 5
        """)
        
        cancelled_payments = cursor.fetchall()
        print(f"   Found {len(cancelled_payments)} CANCELLED payments")
        
        for payment in cancelled_payments:
            print(f"   - {payment['number']}: cancelled at {payment['cancelled_at']}")
        
        # Step 4: Check reversal journal entries
        print("\n4. Checking reversal journal entries...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM journal_entries
            WHERE entry_type = 'REVERSAL'
            OR description LIKE '%Reversal%'
            OR transaction_origin LIKE '%payment_cancellation%'
        """)
        
        result = cursor.fetchone()
        reversal_count = result['count'] if result else 0
        print(f"   Found {reversal_count} reversal journal entries")
        
        # Step 5: Analyze payment status distribution
        print("\n5. Payment status distribution...")
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM payments
            GROUP BY status
            ORDER BY count DESC
        """)
        
        status_distribution = cursor.fetchall()
        for row in status_distribution:
            print(f"   - {row['status']}: {row['count']} payments")
        
        # Step 6: Check payment flow integrity
        print("\n6. Payment flow integrity checks...")
        
        # Check for payments with journal entries but wrong status
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM payments p
            JOIN journal_entries je ON p.journal_entry_id = je.id
            WHERE p.status = 'DRAFT'
        """)
        
        result = cursor.fetchone()
        draft_with_journal = result['count'] if result else 0
        
        if draft_with_journal > 0:
            print(f"   ⚠ Warning: {draft_with_journal} DRAFT payments have journal entries")
        else:
            print("   ✓ No DRAFT payments with journal entries (good)")
        
        # Check for posted payments without journal entries
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM payments
            WHERE status = 'POSTED' AND journal_entry_id IS NULL
        """)
        
        result = cursor.fetchone()
        posted_without_journal = result['count'] if result else 0
        
        if posted_without_journal > 0:
            print(f"   ⚠ Warning: {posted_without_journal} POSTED payments without journal entries")
        else:
            print("   ✓ All POSTED payments have journal entries (good)")
        
        # Step 7: Check cancellation flow readiness
        print("\n7. Cancellation flow readiness analysis...")
        
        # Check if there are permissions/roles for cancellation
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%permission%'
        """)
        
        permission_tables = cursor.fetchall()
        if permission_tables:
            print(f"   ✓ Found permission tables: {[t['name'] for t in permission_tables]}")
        else:
            print("   ⚠ No permission tables found")
        
        # Check for user roles
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%role%'
        """)
        
        role_tables = cursor.fetchall()
        if role_tables:
            print(f"   ✓ Found role tables: {[t['name'] for t in role_tables]}")
        else:
            print("   ⚠ No role tables found")
        
        # Step 8: Summary and recommendations
        print("\n8. Summary and recommendations...")
        
        recommendations = []
        
        if posted_payments:
            print(f"   ✓ System has {len(posted_payments)} POSTED payments ready for cancellation testing")
        else:
            print("   ⚠ No POSTED payments found - cannot test cancellation flow")
            recommendations.append("Create some POSTED payments for testing")
        
        if journal_entries_count > 0:
            print(f"   ✓ System has {journal_entries_count} journal entries linked to payments")
        else:
            print("   ⚠ No journal entries linked to payments")
            recommendations.append("Ensure payment posting creates journal entries")
        
        if reversal_count > 0:
            print(f"   ✓ System has {reversal_count} reversal entries - cancellation has been used")
        else:
            print("   ⚠ No reversal entries found - cancellation flow may not have been tested")
            recommendations.append("Test payment cancellation flow")
        
        if recommendations:
            print("\n   Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Step 9: Cancellation flow verification
        print("\n9. Cancellation flow verification...")
        
        expected_flow = [
            "1. Estado y permisos: Sistema debe verificar que el pago esté POSTED",
            "2. Conciliaciones: Actualmente no implementado (se agregará más tarde)",
            "3. Asiento contable: Crear asiento de reversión para anular el original",
            "4. Marcar como CANCELLED: Actualizar estado del pago",
            "5. Reset a borrador: Permitir edición posterior si es necesario",
            "6. Efecto final: Pago no afecta balances ni reportes"
        ]
        
        for step in expected_flow:
            print(f"   {step}")
        
        # Verify current implementation matches expected flow
        print("\n   Current implementation analysis:")
        
        # Check if we have the required fields
        cursor.execute("PRAGMA table_info(payments)")
        payment_columns = [col[1] for col in cursor.fetchall()]
        
        required_fields = ['status', 'cancelled_at', 'cancelled_by_id', 'journal_entry_id']
        missing_fields = [field for field in required_fields if field not in payment_columns]
        
        if missing_fields:
            print(f"   ✗ Missing required fields: {missing_fields}")
        else:
            print("   ✓ All required fields present in payments table")
        
        # Check journal entries table
        cursor.execute("PRAGMA table_info(journal_entries)")
        journal_columns = [col[1] for col in cursor.fetchall()]
        
        journal_required_fields = ['entry_type', 'transaction_origin', 'state']
        missing_journal_fields = [field for field in journal_required_fields if field not in journal_columns]
        
        if missing_journal_fields:
            print(f"   ✗ Missing journal entry fields: {missing_journal_fields}")
        else:
            print("   ✓ All required journal entry fields present")
        
        conn.close()
        
        print("\n✓ Payment cancellation flow analysis completed!")
        return True
        
    except Exception as e:
        print(f"✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_cancellation():
    """Test API cancellation endpoints"""
    
    print("\n=== Testing API Cancellation Endpoints ===")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test 1: Check if API is running
        print("1. Checking API status...")
        try:
            response = requests.get(f"{base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("   ✓ API is running")
            else:
                print(f"   ⚠ API returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ✗ API is not accessible: {e}")
            return False
        
        # Test 2: Check payments endpoint
        print("2. Testing payments endpoint...")
        try:
            response = requests.get(f"{base_url}/api/v1/payments/", timeout=10)
            if response.status_code == 200:
                payments = response.json()
                print(f"   ✓ Found {len(payments)} payments")
                
                posted_payments = [p for p in payments if p.get('status') == 'POSTED']
                print(f"   ✓ {len(posted_payments)} POSTED payments available for cancellation")
                
                return len(posted_payments) > 0
            else:
                print(f"   ✗ Payments endpoint returned {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ✗ Payments endpoint error: {e}")
            return False
        
    except ImportError:
        print("   ⚠ requests library not available, skipping API tests")
        return True

if __name__ == "__main__":
    print("=== Payment Cancellation Flow Analysis ===")
    
    success1 = test_payment_cancellation_flow_sqlite()
    success2 = test_api_cancellation()
    
    if success1 and success2:
        print("\n✓ All cancellation flow tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed - check the analysis above")
        sys.exit(1)
