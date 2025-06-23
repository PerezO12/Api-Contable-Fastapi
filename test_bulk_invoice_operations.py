"""
Test script for bulk invoice operations
Demonstrates the complete workflow with bulk operations
"""
import requests
import json
import uuid
from datetime import date, datetime
from typing import List, Dict

BASE_URL = "http://localhost:8000"  # Adjust if needed

class BulkInvoiceWorkflowTester:
    """
    Test class for demonstrating bulk invoice operations
    """
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_invoices = []
        
    def authenticate(self, username: str = "admin", password: str = "admin"):
        """Authenticate and get token"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", data={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def create_test_invoices(self, count: int = 5) -> List[str]:
        """Create test invoices for bulk operations"""
        print(f"\n📝 Creating {count} test invoices...")
        
        created_invoices = []
        
        for i in range(count):
            invoice_data = {
                "invoice_date": date.today().isoformat(),
                "invoice_type": "CUSTOMER_INVOICE",
                "currency_code": "USD",
                "description": f"Test Bulk Invoice {i+1}",
                "third_party_id": str(uuid.uuid4()),  # You'll need a valid third party ID
                "lines": [
                    {
                        "description": f"Test Product {i+1}",
                        "quantity": 1,
                        "unit_price": 100.00 + (i * 10),
                        "tax_ids": []
                    }
                ]
            }
            
            try:
                response = self.session.post(
                    f"{self.base_url}/invoices/",
                    json=invoice_data
                )
                
                if response.status_code == 201:
                    invoice = response.json()
                    created_invoices.append(invoice["id"])
                    print(f"  ✅ Created invoice {i+1}: {invoice['id']} - {invoice['invoice_number']}")
                else:
                    print(f"  ❌ Failed to create invoice {i+1}: {response.status_code}")
                    print(f"     Error: {response.text}")
                    
            except Exception as e:
                print(f"  ❌ Error creating invoice {i+1}: {e}")
        
        self.test_invoices = created_invoices
        print(f"📊 Created {len(created_invoices)} invoices successfully")
        return created_invoices
    
    def validate_bulk_operation(self, invoice_ids: List[str], operation: str):
        """Validate bulk operation before executing"""
        print(f"\n🔍 Validating bulk {operation} operation...")
        
        try:
            params = {
                "operation": operation,
                "invoice_ids": invoice_ids
            }
            
            response = self.session.post(
                f"{self.base_url}/invoices/bulk/validate",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  📊 Validation results:")
                print(f"     Total requested: {result['total_requested']}")
                print(f"     Valid invoices: {result['valid_count']}")
                print(f"     Invalid invoices: {result['invalid_count']}")
                print(f"     Not found: {result['not_found_count']}")
                print(f"     Can proceed: {result['can_proceed']}")
                
                if result['invalid_invoices']:
                    print("  ⚠️ Invalid invoices:")
                    for inv in result['invalid_invoices']:
                        print(f"     - {inv['id']}: {', '.join(inv['reasons'])}")
                
                return result
            else:
                print(f"  ❌ Validation failed: {response.status_code}")
                print(f"     Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Validation error: {e}")
            return None
    
    def bulk_post_invoices(self, invoice_ids: List[str]):
        """Test bulk post operation"""
        print(f"\n📮 Executing bulk POST operation...")
        
        request_data = {
            "invoice_ids": invoice_ids,
            "posting_date": date.today().isoformat(),
            "notes": "Bulk posted via test script",
            "force_post": False,
            "stop_on_error": False
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/invoices/bulk/post",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  📊 Bulk POST results:")
                print(f"     Total requested: {result['total_requested']}")
                print(f"     Successful: {result['successful']}")
                print(f"     Failed: {result['failed']}")
                print(f"     Skipped: {result['skipped']}")
                print(f"     Execution time: {result['execution_time_seconds']}s")
                
                if result['failed_items']:
                    print("  ❌ Failed items:")
                    for item in result['failed_items']:
                        print(f"     - {item['id']}: {item['error']}")
                
                return result
            else:
                print(f"  ❌ Bulk POST failed: {response.status_code}")
                print(f"     Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Bulk POST error: {e}")
            return None
    
    def bulk_cancel_invoices(self, invoice_ids: List[str]):
        """Test bulk cancel operation"""
        print(f"\n❌ Executing bulk CANCEL operation...")
        
        request_data = {
            "invoice_ids": invoice_ids,
            "reason": "Cancelled via bulk test script",
            "stop_on_error": False
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/invoices/bulk/cancel",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  📊 Bulk CANCEL results:")
                print(f"     Total requested: {result['total_requested']}")
                print(f"     Successful: {result['successful']}")
                print(f"     Failed: {result['failed']}")
                print(f"     Skipped: {result['skipped']}")
                print(f"     Execution time: {result['execution_time_seconds']}s")
                
                return result
            else:
                print(f"  ❌ Bulk CANCEL failed: {response.status_code}")
                print(f"     Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Bulk CANCEL error: {e}")
            return None
    
    def bulk_reset_to_draft(self, invoice_ids: List[str]):
        """Test bulk reset to draft operation"""
        print(f"\n🔄 Executing bulk RESET TO DRAFT operation...")
        
        request_data = {
            "invoice_ids": invoice_ids,
            "reason": "Reset to draft via bulk test script",
            "force_reset": False,
            "stop_on_error": False
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/invoices/bulk/reset-to-draft",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  📊 Bulk RESET results:")
                print(f"     Total requested: {result['total_requested']}")
                print(f"     Successful: {result['successful']}")
                print(f"     Failed: {result['failed']}")
                print(f"     Skipped: {result['skipped']}")
                print(f"     Execution time: {result['execution_time_seconds']}s")
                
                return result
            else:
                print(f"  ❌ Bulk RESET failed: {response.status_code}")
                print(f"     Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Bulk RESET error: {e}")
            return None
    
    def bulk_delete_invoices(self, invoice_ids: List[str]):
        """Test bulk delete operation"""
        print(f"\n🗑️ Executing bulk DELETE operation...")
        
        request_data = {
            "invoice_ids": invoice_ids,
            "confirmation": "CONFIRM_DELETE",
            "reason": "Deleted via bulk test script"
        }
        
        try:
            response = self.session.delete(
                f"{self.base_url}/invoices/bulk/delete",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  📊 Bulk DELETE results:")
                print(f"     Total requested: {result['total_requested']}")
                print(f"     Successful: {result['successful']}")
                print(f"     Failed: {result['failed']}")
                print(f"     Skipped: {result['skipped']}")
                print(f"     Execution time: {result['execution_time_seconds']}s")
                
                return result
            else:
                print(f"  ❌ Bulk DELETE failed: {response.status_code}")
                print(f"     Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Bulk DELETE error: {e}")
            return None
    
    def run_complete_workflow_test(self):
        """Run the complete bulk workflow test"""
        print("🚀 Starting Bulk Invoice Operations Workflow Test")
        print("=" * 60)
        
        # 1. Create test invoices
        invoice_ids = self.create_test_invoices(3)
        if not invoice_ids:
            print("❌ Cannot continue without test invoices")
            return
        
        # 2. Validate POST operation
        post_validation = self.validate_bulk_operation(invoice_ids, "post")
        
        # 3. Execute bulk POST
        if post_validation and post_validation.get("can_proceed"):
            post_result = self.bulk_post_invoices(invoice_ids)
            
            if post_result and post_result["successful"] > 0:
                posted_ids = post_result["successful_ids"]
                
                # 4. Validate CANCEL operation
                cancel_validation = self.validate_bulk_operation(posted_ids, "cancel")
                
                # 5. Execute bulk CANCEL (test with some invoices)
                if len(posted_ids) > 1:
                    cancel_ids = posted_ids[:len(posted_ids)//2]  # Cancel half
                    cancel_result = self.bulk_cancel_invoices(cancel_ids)
                    
                    # 6. Reset remaining to draft
                    remaining_ids = [id for id in posted_ids if id not in cancel_ids]
                    if remaining_ids:
                        reset_result = self.bulk_reset_to_draft(remaining_ids)
                        
                        # 7. Delete draft invoices
                        if reset_result and reset_result["successful"] > 0:
                            draft_ids = reset_result["successful_ids"]
                            delete_result = self.bulk_delete_invoices(draft_ids)
        
        print("\n🎉 Bulk workflow test completed!")
        print("=" * 60)


def main():
    """Main test function"""
    print("Bulk Invoice Operations Test Script")
    print("====================================")
    
    # Create tester instance
    tester = BulkInvoiceWorkflowTester()
    
    # Authenticate
    if not tester.authenticate():
        print("Cannot proceed without authentication")
        return
    
    # Run the complete workflow test
    tester.run_complete_workflow_test()


if __name__ == "__main__":
    main()
