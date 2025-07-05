#!/usr/bin/env python3
"""
Script de prueba para la contabilización en lote de pagos

Demuestra el uso de las nuevas funcionalidades:
1. Validación en lote
2. Contabilización optimizada por lotes
3. Manejo de errores y estadísticas
"""
import requests
import json
import uuid
from typing import List, Dict, Any
from datetime import datetime

# Configuración de la API
API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

class BulkPaymentTester:
    """
    Clase para probar las operaciones de contabilización en lote
    """
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.auth_token = None
    
    def authenticate(self, username: str = "admin", password: str = "admin"):
        """Autenticar con la API"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data={"username": username, "password": password}
            )
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                self.session.headers["Authorization"] = f"Bearer {self.auth_token}"
                print("✓ Authentication successful")
                return True
            else:
                print(f"✗ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False
    
    def get_draft_payments(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener pagos en estado DRAFT para probar"""
        try:
            response = self.session.get(
                f"{self.base_url}/payments/",
                params={"status": "draft", "limit": limit}
            )
            if response.status_code == 200:
                data = response.json()
                payments = data.get("items", [])
                print(f"✓ Found {len(payments)} draft payments")
                return payments
            else:
                print(f"✗ Failed to get payments: {response.status_code}")
                return []
        except Exception as e:
            print(f"✗ Error getting payments: {e}")
            return []
    
    def validate_bulk_posting(self, payment_ids: List[str]) -> Dict[str, Any]:
        """Validar contabilización en lote"""
        try:
            print(f"\n🔍 Validating bulk posting for {len(payment_ids)} payments...")
            
            response = self.session.post(
                f"{self.base_url}/payments/bulk/validate-posting",
                json=payment_ids
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✓ Validation completed:")
                print(f"  - Total payments: {result['total_payments']}")
                print(f"  - Can post: {result['can_confirm_count']}")
                print(f"  - Blocked: {result['blocked_count']}")
                print(f"  - With warnings: {result['warnings_count']}")
                
                # Mostrar algunos detalles
                for validation in result['validation_results'][:3]:  # Primeros 3
                    status = "✓" if validation['can_confirm'] else "✗"
                    print(f"  {status} {validation['payment_number']}: "
                          f"{len(validation['blocking_reasons'])} errors, "
                          f"{len(validation['warnings'])} warnings")
                
                return result
            else:
                print(f"✗ Validation failed: {response.status_code}")
                print(response.text)
                return {}
                
        except Exception as e:
            print(f"✗ Validation error: {e}")
            return {}
    
    def bulk_post_payments(
        self, 
        payment_ids: List[str], 
        posting_notes: str | None = None,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Contabilizar pagos en lote"""
        try:
            print(f"\n📝 Bulk posting {len(payment_ids)} payments...")
            
            # Construir URL con parámetros
            url = f"{self.base_url}/payments/bulk/post?batch_size={batch_size}"
            if posting_notes:
                url += f"&posting_notes={posting_notes}"
            
            response = self.session.post(url, json=payment_ids)
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✓ Bulk posting completed:")
                print(f"  - Operation: {result['operation']}")
                print(f"  - Total: {result['total_payments']}")
                print(f"  - Successful: {result['successful']}")
                print(f"  - Failed: {result['failed']}")
                print(f"  - Summary: {result['summary']}")
                
                # Mostrar algunos resultados
                successful_results = [r for r in result['results'] if r['success']]
                failed_results = [r for r in result['results'] if not r['success']]
                
                if successful_results:
                    print(f"\n✓ Successful postings (showing first 3):")
                    for result_item in successful_results[:3]:
                        print(f"  ✓ {result_item['payment_number']}: {result_item['message']}")
                
                if failed_results:
                    print(f"\n✗ Failed postings:")
                    for result_item in failed_results:
                        print(f"  ✗ {result_item['payment_number']}: {result_item['error']}")
                
                return result
            else:
                print(f"✗ Bulk posting failed: {response.status_code}")
                print(response.text)
                return {}
                
        except Exception as e:
            print(f"✗ Bulk posting error: {e}")
            return {}
    
    def test_bulk_workflow(self, max_payments: int = 20):
        """Probar el flujo completo de contabilización en lote"""
        print("=" * 60)
        print("🚀 TESTING BULK PAYMENT POSTING WORKFLOW")
        print("=" * 60)
        
        # 1. Autenticar
        if not self.authenticate():
            return False
        
        # 2. Obtener pagos en borrador
        draft_payments = self.get_draft_payments(max_payments)
        if not draft_payments:
            print("❌ No draft payments found for testing")
            return False
        
        # Extraer IDs
        payment_ids = [payment["id"] for payment in draft_payments[:max_payments]]
        
        # 3. Validar contabilización
        validation_result = self.validate_bulk_posting(payment_ids)
        if not validation_result:
            print("❌ Validation failed")
            return False
        
        # 4. Contabilizar solo los que pueden ser contabilizados
        valid_payments = [
            r["payment_id"] for r in validation_result["validation_results"]
            if r["can_confirm"]
        ]
        
        if not valid_payments:
            print("❌ No payments can be posted")
            return False
        
        # 5. Realizar contabilización en lote
        posting_notes = f"Bulk posting test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        posting_result = self.bulk_post_payments(
            valid_payments, 
            posting_notes=posting_notes,
            batch_size=5
        )
        
        if posting_result:
            print("\n" + "=" * 60)
            print("✅ BULK POSTING TEST COMPLETED SUCCESSFULLY")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ BULK POSTING TEST FAILED")
            print("=" * 60)
            return False
    
    def demo_api_calls(self):
        """Demostrar todas las llamadas API disponibles"""
        print("=" * 60)
        print("📖 BULK PAYMENT API ENDPOINTS DEMO")
        print("=" * 60)
        
        print("\n1. Validate bulk posting:")
        print("POST /api/v1/payments/bulk/validate-posting")
        print("Body: [\"payment_id_1\", \"payment_id_2\", ...]")
        
        print("\n2. Bulk post payments:")
        print("POST /api/v1/payments/bulk/post")
        print("Body: {")
        print("  \"payment_ids\": [\"id1\", \"id2\"],")
        print("  \"posting_notes\": \"Optional notes\",")
        print("  \"batch_size\": 50")
        print("}")
        
        print("\n3. Bulk confirm payments (alternative):")
        print("POST /api/v1/payments/bulk/confirm")
        print("Body: {")
        print("  \"payment_ids\": [\"id1\", \"id2\"],")
        print("  \"confirmation_notes\": \"Optional notes\",")
        print("  \"force\": false")
        print("}")
        
        print("\n4. Bulk cancel payments:")
        print("POST /api/v1/payments/bulk/cancel")
        print("Body: {")
        print("  \"payment_ids\": [\"id1\", \"id2\"],")
        print("  \"cancellation_reason\": \"Reason for cancellation\"")
        print("}")
        
        print("\n5. Bulk delete payments:")
        print("DELETE /api/v1/payments/bulk/delete")
        print("Body: {")
        print("  \"payment_ids\": [\"id1\", \"id2\"],")
        print("  \"force\": false")
        print("}")


def main():
    """Función principal para ejecutar las pruebas"""
    tester = BulkPaymentTester()
    
    # Mostrar ejemplos de API
    tester.demo_api_calls()
    
    # Preguntar si ejecutar pruebas
    print("\n" + "=" * 60)
    choice = input("¿Ejecutar pruebas con datos reales? (y/N): ").strip().lower()
    
    if choice in ['y', 'yes', 'sí', 'si']:
        success = tester.test_bulk_workflow(max_payments=10)
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n💥 Some tests failed!")
    else:
        print("\n👋 Demo completed. Run with real data when ready.")


if __name__ == "__main__":
    main()
