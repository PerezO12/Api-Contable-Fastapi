#!/usr/bin/env python3
"""
Test script for full file validation functionality
Tests the new /validate-full endpoint
"""

import asyncio
import requests
import json
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1/generic-import"
TEST_FILE_PATH = "test_import_with_errors.csv"

async def test_full_validation():
    """Test the complete validation flow"""
    
    print("🧪 Testing Full File Validation")
    print("=" * 50)
    
    # Step 1: Get available models
    print("📋 Step 1: Getting available models...")
    response = requests.get(f"{BASE_URL}/models")
    if response.status_code != 200:
        print(f"❌ Failed to get models: {response.status_code}")
        return
    
    models = response.json()
    print(f"✅ Available models: {models}")
    
    # Use third_party model for testing
    model_name = "third_party"
    if model_name not in models:
        print(f"❌ Model {model_name} not available")
        return
    
    # Step 2: Create import session
    print(f"\n📤 Step 2: Creating import session for model '{model_name}'...")
    
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ Test file {TEST_FILE_PATH} not found")
        return
    
    with open(TEST_FILE_PATH, 'rb') as f:
        files = {'file': (TEST_FILE_PATH, f, 'text/csv')}
        data = {'model_name': model_name}
        response = requests.post(f"{BASE_URL}/sessions", files=files, data=data)
    
    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    session_data = response.json()
    session_id = session_data['import_session_token']
    print(f"✅ Session created: {session_id}")
    print(f"📊 File info: {session_data['file_info']['total_rows']} rows")
    
    # Step 3: Set up column mappings
    print(f"\n🗂️ Step 3: Setting up column mappings...")
    
    # Simple mapping for third_party model
    mappings = [
        {
            "column_name": "Nombre completo",
            "field_name": "name"
        }
    ]
    
    preview_request = {
        "import_session_token": session_id,
        "column_mappings": mappings,
        "import_policy": "create_only",
        "skip_validation_errors": False,
        "default_values": {
            "document_type": "other",
            "third_party_type": "customer",
            "is_active": True,
            "is_tax_withholding_agent": False
        }
    }
    
    print(f"📋 Mappings: {json.dumps(mappings, indent=2)}")
    
    # Step 4: Test regular preview (sample only)
    print(f"\n👁️ Step 4: Testing regular preview (sample only)...")
    
    response = requests.post(f"{BASE_URL}/sessions/{session_id}/preview", json=preview_request)
    if response.status_code != 200:
        print(f"❌ Failed to generate preview: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    preview_data = response.json()
    print(f"✅ Regular preview completed")
    print(f"📊 Sample validation summary:")
    print(f"  - Total rows analyzed: {preview_data['validation_summary']['total_rows_analyzed']}")
    print(f"  - Valid rows: {preview_data['validation_summary']['valid_rows']}")
    print(f"  - Rows with errors: {preview_data['validation_summary']['rows_with_errors']}")
    print(f"  - Rows with warnings: {preview_data['validation_summary']['rows_with_warnings']}")
    
    # Step 5: Test full file validation
    print(f"\n🔍 Step 5: Testing full file validation...")
    
    response = requests.post(f"{BASE_URL}/sessions/{session_id}/validate-full", json=preview_request)
    if response.status_code != 200:
        print(f"❌ Failed to validate full file: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    full_validation_data = response.json()
    print(f"✅ Full file validation completed")
    print(f"📊 Complete validation summary:")
    print(f"  - Total rows analyzed: {full_validation_data['validation_summary']['total_rows_analyzed']}")
    print(f"  - Valid rows: {full_validation_data['validation_summary']['valid_rows']}")
    print(f"  - Rows with errors: {full_validation_data['validation_summary']['rows_with_errors']}")
    print(f"  - Rows with warnings: {full_validation_data['validation_summary']['rows_with_warnings']}")
    print(f"  - Can proceed: {full_validation_data['can_proceed']}")
    print(f"  - Can skip errors: {full_validation_data['can_skip_errors']}")
    
    if full_validation_data['validation_summary']['error_breakdown']:
        print(f"📋 Error breakdown:")
        for error_type, count in full_validation_data['validation_summary']['error_breakdown'].items():
            print(f"  - {error_type}: {count}")
    
    # Step 6: Compare results
    print(f"\n📊 Step 6: Comparing sample vs full validation...")
    
    sample_total = preview_data['validation_summary']['total_rows_analyzed']
    full_total = full_validation_data['validation_summary']['total_rows_analyzed']
    
    print(f"Sample analyzed: {sample_total} rows")
    print(f"Full analyzed: {full_total} rows")
    print(f"Difference: {full_total - sample_total} additional rows validated")
    
    if full_total > sample_total:
        print("✅ Full validation processed more rows than sample - SUCCESS!")
    else:
        print("⚠️ Full validation processed same number of rows as sample")
    
    # Step 7: Test batch size calculation
    print(f"\n📦 Step 7: Testing batch size calculation...")
    
    response = requests.get(f"{BASE_URL}/config")
    if response.status_code == 200:
        config = response.json()
        default_batch_size = config['batch_size']['default']
        total_rows = full_validation_data['total_rows']
        expected_batches = (total_rows + default_batch_size - 1) // default_batch_size
        
        print(f"Total rows: {total_rows}")
        print(f"Default batch size: {default_batch_size}")
        print(f"Expected batches: {expected_batches}")
    
    print(f"\n🎉 Full validation test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_full_validation())
