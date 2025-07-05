"""
Test the API endpoint directly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_payment_api():
    """Test the payment API endpoint"""
    try:
        # Test the API endpoint (assuming it's running on port 8000)
        base_url = "http://localhost:8000"
        
        # First, let's try to get a token by logging in
        # We need to check if the server is running
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            print(f"Server health check: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("Server is not running. Please start the API server first.")
            return
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return
            
        # Try to get payments without authentication first to see what happens
        try:
            response = requests.get(f"{base_url}/api/v1/payments/", timeout=10)
            print(f"Payments endpoint status: {response.status_code}")
            print(f"Response: {response.text[:500]}")  # First 500 chars
        except Exception as e:
            print(f"Error calling payments endpoint: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_api()
