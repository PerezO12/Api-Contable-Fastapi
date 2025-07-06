#!/usr/bin/env python3
"""
Simple test for company settings endpoint
"""

import requests
import json

def test_company_settings():
    """Test company settings endpoint"""
    
    base_url = "http://localhost:8000"
    
    try:
        print("Testing company settings endpoint...")
        response = requests.get(f"{base_url}/api/v1/company-settings/", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            settings = response.json()
            print(f"Found {len(settings)} company settings")
            
            # Debug: Print the type and first few characters
            print(f"Response type: {type(settings)}")
            if isinstance(settings, list):
                print(f"It's a list with {len(settings)} elements")
                if len(settings) > 0:
                    print(f"First element type: {type(settings[0])}")
                    print(f"First element: {settings[0]}")
            else:
                print(f"Response content: {settings}")
            
            if settings and len(settings) > 0:
                first_setting = settings[0]
                
                # Print relevant fields
                print("\nFirst company setting:")
                print(f"  ID: {first_setting.get('id')}")
                print(f"  Company Name: {first_setting.get('company_name')}")
                
                # Treasury account IDs
                print(f"  Cash Account ID: {first_setting.get('default_cash_account_id')}")
                print(f"  Bank Account ID: {first_setting.get('default_bank_account_id')}")
                
                # Treasury account names (these should not be None)
                print(f"  Cash Account Name: {first_setting.get('default_cash_account_name')}")
                print(f"  Bank Account Name: {first_setting.get('default_bank_account_name')}")
                
                # Check if names are missing
                if first_setting.get('default_cash_account_id') and not first_setting.get('default_cash_account_name'):
                    print("  ✗ ISSUE: Cash account ID exists but name is missing!")
                    
                if first_setting.get('default_bank_account_id') and not first_setting.get('default_bank_account_name'):
                    print("  ✗ ISSUE: Bank account ID exists but name is missing!")
                    
                # Show all keys for debugging
                print(f"\nAll keys in first setting: {list(first_setting.keys())}")
            else:
                print("No settings found in response")
        else:
            print(f"Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_company_settings()
