#!/usr/bin/env python3
"""
Test payment cancellation functionality quickly
"""

import requests
import json

def test_payment_cancellation():
    """Test payment cancellation endpoint"""
    
    base_url = "http://localhost:8000"
    
    # Test data for bulk cancellation
    test_request = {
        "payment_ids": ["12345678-1234-1234-1234-123456789012"],  # Non-existent ID for testing
        "cancellation_reason": "Test cancellation"
    }
    
    try:
        print("Testing payment bulk cancellation endpoint...")
        response = requests.post(
            f"{base_url}/api/v1/payments/bulk/cancel",
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 422:
            # This is the problematic status code
            try:
                error_detail = response.json()
                print(f"Error Detail: {error_detail}")
            except:
                print(f"Raw Response: {response.text}")
        elif response.status_code == 403:
            print("Authentication required (expected)")
        elif response.status_code == 200:
            result = response.json()
            print(f"Success: {result}")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_payment_cancellation()
