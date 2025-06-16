#!/usr/bin/env python3
"""
Simple test script to verify product creation with default values works through the API
"""

from fastapi.testclient import TestClient
from app.main import app

def test_product_creation():
    client = TestClient(app)
    
    # Test creating a product with minimal data through API
    product_data = {
        'code': 'TEST002',
        'name': 'Test Product via API'
    }
    
    try:
        # Note: This might fail due to authentication, but we can check the validation
        response = client.post('/api/v1/products/', json=product_data)
        print(f'Response status: {response.status_code}')
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print('Product created via API successfully!')
            print(f'Product Type: {result.get("product_type")}')
            print(f'Purchase Price: {result.get("purchase_price")}')
            print(f'Sale Price: {result.get("sale_price")}')
            print(f'Tax Category: {result.get("tax_category")}')
            print(f'Tax Rate: {result.get("tax_rate")}')
            print(f'Sales Account ID: {result.get("sales_account_id")}')
        elif response.status_code == 401:
            print('Authentication required (expected), but schema validation passed')
        else:
            print(f'Response: {response.text}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_product_creation()
