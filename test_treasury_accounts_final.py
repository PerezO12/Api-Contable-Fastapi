#!/usr/bin/env python3
"""
Test company settings endpoint correctly
"""

import requests
import json

def test_company_settings_correct():
    """Test the correct company settings endpoint"""
    
    base_url = "http://localhost:8000"
    
    try:
        print("Testing company settings endpoint (GET /)...")
        response = requests.get(f"{base_url}/api/v1/company-settings/", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            settings = response.json()
            print("✓ Company settings retrieved successfully")
            
            # Print relevant treasury fields
            print("\nTreasury Account Configuration:")
            print(f"  Cash Account ID: {settings.get('default_cash_account_id')}")
            print(f"  Cash Account Name: {settings.get('default_cash_account_name')}")
            print(f"  Bank Account ID: {settings.get('default_bank_account_id')}")
            print(f"  Bank Account Name: {settings.get('default_bank_account_name')}")
            
            # Validate the issue
            cash_id = settings.get('default_cash_account_id')
            cash_name = settings.get('default_cash_account_name')
            bank_id = settings.get('default_bank_account_id')
            bank_name = settings.get('default_bank_account_name')
            
            print("\nValidation:")
            if cash_id and cash_name:
                print("  ✓ Cash account properly configured")
            elif cash_id and not cash_name:
                print("  ✗ ISSUE: Cash account ID exists but name is missing!")
            else:
                print("  ⚠ Cash account not configured")
                
            if bank_id and bank_name:
                print("  ✓ Bank account properly configured")
            elif bank_id and not bank_name:
                print("  ✗ ISSUE: Bank account ID exists but name is missing!")
            else:
                print("  ⚠ Bank account not configured")
                
            if cash_name and bank_name:
                print("\n✓ SUCCESS: Treasury accounts are showing names correctly!")
                print("✓ The backend is working properly")
                print("✓ Frontend should display these names now")
                return True
            else:
                print("\n✗ ISSUE: Treasury account names are not being returned")
                return False
                
        else:
            print(f"Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_company_settings_correct()
    if success:
        print("\n🎉 The treasury accounts issue is RESOLVED!")
        print("   The backend is properly returning account names.")
        print("   If the frontend still shows empty fields, it's a frontend issue.")
    else:
        print("\n❌ The treasury accounts issue persists.")
        print("   The backend is not returning account names properly.")
