#!/usr/bin/env python3
"""
Check database structure and payment tables
"""

import sqlite3
import sys
from pathlib import Path

def check_database_structure():
    """Check the structure of the SQLite database"""
    
    print("=== Checking Database Structure ===")
    
    try:
        # Connect to SQLite database
        db_path = Path(__file__).parent / "contable.db"
        if not db_path.exists():
            print(f"✗ Database file not found: {db_path}")
            return False
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"✓ Connected to database: {db_path}")
        
        # Step 1: List all tables
        print("\n1. All tables in database:")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['name']}")
        
        # Step 2: Find payment-related tables
        print("\n2. Payment-related tables:")
        payment_tables = [t['name'] for t in tables if 'payment' in t['name'].lower()]
        
        if payment_tables:
            for table in payment_tables:
                print(f"   - {table}")
                
                # Show structure of payment table
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"     Columns ({len(columns)}):")
                for col in columns:
                    print(f"       {col['name']} ({col['type']})")
                
                # Show count of records
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                print(f"     Records: {result['count']}")
        else:
            print("   No payment tables found")
        
        # Step 3: Find journal-related tables
        print("\n3. Journal-related tables:")
        journal_tables = [t['name'] for t in tables if 'journal' in t['name'].lower()]
        
        if journal_tables:
            for table in journal_tables:
                print(f"   - {table}")
                
                # Show count of records
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                print(f"     Records: {result['count']}")
        else:
            print("   No journal tables found")
        
        # Step 4: Check if we have alembic migration table
        print("\n4. Migration status:")
        if 'alembic_version' in [t['name'] for t in tables]:
            cursor.execute("SELECT version_num FROM alembic_version")
            version = cursor.fetchone()
            print(f"   Current migration version: {version['version_num'] if version else 'None'}")
        else:
            print("   No alembic version table found")
        
        # Step 5: Check for account-related tables
        print("\n5. Account-related tables:")
        account_tables = [t['name'] for t in tables if 'account' in t['name'].lower()]
        
        if account_tables:
            for table in account_tables:
                print(f"   - {table}")
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                print(f"     Records: {result['count']}")
        else:
            print("   No account tables found")
        
        # Step 6: Check for company settings
        print("\n6. Company settings tables:")
        company_tables = [t['name'] for t in tables if 'company' in t['name'].lower()]
        
        if company_tables:
            for table in company_tables:
                print(f"   - {table}")
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                print(f"     Records: {result['count']}")
        else:
            print("   No company tables found")
        
        conn.close()
        
        print("\n✓ Database structure analysis completed!")
        return True
        
    except Exception as e:
        print(f"✗ Error during database analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_database_structure()
    sys.exit(0 if success else 1)
