#!/usr/bin/env python3
"""
Script to check for third party codes with special characters
"""
import sqlite3
import re

def check_codes():
    """Check for codes with special characters"""
    db_path = "./contable.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, code, name FROM third_parties')
        rows = cursor.fetchall()
        
        # Pattern for allowed characters: letters, numbers, dots, hyphens, underscores
        pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
        
        print(f"Total third parties found: {len(rows)}")
        print("Checking for codes with special characters...")
        
        problems_found = 0
        for row in rows:
            code = row[1]
            if not pattern.match(code):
                print(f'❌ ID: {row[0]}, Code: {repr(code)}, Name: {row[2]}')
                problems_found += 1
        
        if problems_found == 0:
            print("✅ No codes with special characters found")
        else:
            print(f"❌ Found {problems_found} codes with special characters")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_codes()
