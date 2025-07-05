"""
Test the complete payment API flow with authentication
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_payment_api_with_auth():
    """Test the payment API with proper authentication"""
    try:
        base_url = "http://localhost:8000"
        
        # Step 1: Login to get token
        login_data = {
            "username": "admin@example.com",  # Default admin email
            "password": "admin123"  # Default admin password
        }
        
        try:
            login_response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data, timeout=10)
            print(f"Login status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                access_token = token_data["access_token"]
                print("✅ Login successful, got access token")
                
                # Step 2: Test payments endpoint with authentication
                headers = {"Authorization": f"Bearer {access_token}"}
                
                payments_response = requests.get(f"{base_url}/api/v1/payments/", headers=headers, timeout=10)
                print(f"Payments endpoint status: {payments_response.status_code}")
                
                if payments_response.status_code == 200:
                    payments_data = payments_response.json()
                    print("✅ Payments endpoint working!")
                    print(f"Response structure:")
                    print(f"- data: {type(payments_data.get('data'))} with {len(payments_data.get('data', []))} items")
                    print(f"- total: {payments_data.get('total')}")
                    print(f"- page: {payments_data.get('page')}")
                    print(f"- per_page: {payments_data.get('per_page')}")
                    print(f"- pages: {payments_data.get('pages')}")
                    
                    if payments_data.get('data'):
                        print("\nFirst payment:")
                        first_payment = payments_data['data'][0]
                        print(f"- ID: {first_payment.get('id')}")
                        print(f"- Number: {first_payment.get('number')}")
                        print(f"- Amount: {first_payment.get('amount')}")
                        print(f"- Status: {first_payment.get('status')}")
                    else:
                        print("\n❌ No payments in data array (this was the original bug)")
                        
                else:
                    print(f"❌ Payments endpoint failed: {payments_response.text}")
                    
            else:
                print(f"❌ Login failed: {login_response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_api_with_auth()
