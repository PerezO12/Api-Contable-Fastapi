#!/usr/bin/env python3
"""
Test script para verificar que la eliminación en bulk de facturas NFE funciona correctamente
"""

import httpx
import json
from pathlib import Path
import time
from typing import List, Dict, Any

# Configuración del teste
BASE_URL = "http://localhost:8000"

# Credenciales de teste
TEST_CREDENTIALS = {
    "email": "admin@contable.com",
    "password": "Admin123!"
}


class NFEInvoiceDeletionTester:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=300.0)
        self.token = None
    
    def login(self) -> bool:
        """Fazer login e obter token"""
        try:
            response = self.client.post("/api/v1/auth/login", json=TEST_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Login realizado com sucesso")
                return True
            else:
                print(f"❌ Erro no login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na conexão: {str(e)}")
            return False
    
    def get_draft_invoices_from_nfe(self) -> List[Dict[str, Any]]:
        """Buscar facturas en borrador que fueron importadas de NFE"""
        try:
            print("🔍 Buscando facturas en borrador importadas de NFE...")
            
            # Buscar facturas en estado DRAFT
            response = self.client.get("/api/v1/invoices/", params={
                "page": 1,
                "page_size": 100,
                "status": "DRAFT"
            })
            
            if response.status_code == 200:
                result = response.json()
                draft_invoices = result.get('items', [])
                
                # Verificar cuáles están vinculadas a NFE
                nfe_invoices = []
                for invoice in draft_invoices:
                    # Verificar si hay una NFE vinculada a esta factura
                    nfe_response = self.client.get(f"/api/v1/nfe/", params={
                        "invoice_id": invoice["id"]
                    })
                    
                    if nfe_response.status_code == 200:
                        nfe_data = nfe_response.json()
                        if nfe_data.get('total', 0) > 0:
                            nfe_invoices.append(invoice)
                
                print(f"📊 Encontradas {len(draft_invoices)} facturas en borrador, {len(nfe_invoices)} importadas de NFE")
                return nfe_invoices
                
            else:
                print(f"❌ Error al buscar facturas: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error en la búsqueda: {str(e)}")
            return []
    
    def test_bulk_delete_nfe_invoices(self, invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Probar eliminación en bulk de facturas NFE"""
        if not invoices:
            print("⚠️ No hay facturas NFE en borrador para probar")
            return {}
        
        # Tomar las primeras 3 facturas para el test
        test_invoices = invoices[:3]
        invoice_ids = [inv["id"] for inv in test_invoices]
        
        print(f"\n🧪 Probando eliminación en bulk de {len(test_invoices)} facturas NFE:")
        for inv in test_invoices:
            print(f"   - ID: {inv['id']}")
            print(f"     Número: {inv.get('invoice_number', inv.get('number', 'N/A'))}")
            print(f"     Tercero: {inv.get('third_party_name', 'N/A')}")
            print(f"     Total: ${inv.get('total_amount', 'N/A')}")
            print()
        
        delete_request = {
            "invoice_ids": invoice_ids,
            "confirmation": "CONFIRM_DELETE",
            "reason": "Test de eliminación de facturas NFE importadas"
        }
        
        try:
            response = self.client.request(
                method="DELETE",
                url="/api/v1/invoices/bulk/delete",
                json=delete_request
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Eliminación completada exitosamente!")
                self.print_delete_result(result)
                return result
            else:
                print(f"❌ Error en la eliminación: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error en la solicitud: {str(e)}")
            return {"error": str(e)}
    
    def print_delete_result(self, result: Dict[str, Any]):
        """Imprimir resultado de la eliminación"""
        print(f"""
📊 RESULTADO DE LA ELIMINACIÓN:
   Total solicitadas: {result.get('total_requested', 0)}
   Eliminadas exitosamente: {result.get('successful', 0)}
   Fallidas: {result.get('failed', 0)}
   Omitidas: {result.get('skipped', 0)}
   Tiempo de ejecución: {result.get('execution_time_seconds', 0):.2f}s
        """)
        
        failed_items = result.get('failed_items', [])
        if failed_items:
            print(f"❌ ERRORES ({len(failed_items)}):")
            for item in failed_items:
                invoice_number = item.get('invoice_number', item.get('number', 'N/A'))
                print(f"   - {invoice_number}: {item.get('error', 'N/A')}")
        
        skipped_items = result.get('skipped_items', [])
        if skipped_items:
            print(f"⚠️ OMITIDAS ({len(skipped_items)}):")
            for item in skipped_items:
                print(f"   - ID {item.get('id', 'N/A')}: {item.get('reason', 'N/A')}")
    
    def verify_nfe_unlinked(self, original_invoices: List[Dict[str, Any]]) -> bool:
        """Verificar que las NFE fueron desvinculadas correctamente"""
        print("\n🔍 Verificando desvinculación de NFE...")
        
        all_unlinked = True
        for invoice in original_invoices:
            try:
                # Buscar NFE que estaban vinculadas a esta factura
                response = self.client.get("/api/v1/nfe/", params={
                    "chave_nfe": None  # Buscar por otros criterios si es necesario
                })
                
                if response.status_code == 200:
                    nfe_data = response.json()
                    # Verificar que las NFE tengan status UNLINKED y invoice_id null
                    for nfe in nfe_data.get('items', []):
                        if nfe.get('status') == 'UNLINKED':
                            print(f"✅ NFE {nfe.get('numero_nfe')} correctamente desvinculada")
                        else:
                            print(f"⚠️ NFE {nfe.get('numero_nfe')} status: {nfe.get('status')}")
                            
            except Exception as e:
                print(f"❌ Error verificando NFE: {str(e)}")
                all_unlinked = False
        
        return all_unlinked
    
    def run_test(self):
        """Ejecutar test completo"""
        print("🚀 Iniciando test de eliminación en bulk de facturas NFE\n")
        
        # 1. Login
        if not self.login():
            return
        
        # 2. Buscar facturas NFE en borrador
        nfe_invoices = self.get_draft_invoices_from_nfe()
        
        if not nfe_invoices:
            print("⚠️ No se encontraron facturas NFE en borrador para probar")
            print("💡 Sugerencia: Importa algunas NFE primero usando test_nfe_import.py")
            return
        
        # 3. Probar eliminación
        delete_result = self.test_bulk_delete_nfe_invoices(nfe_invoices)
        
        # 4. Verificar desvinculación
        if delete_result.get('successful', 0) > 0:
            self.verify_nfe_unlinked(nfe_invoices)
        
        print("\n✅ Test completado!")
        
        # Resumen
        if delete_result.get('failed', 0) == 0:
            print("🎉 ¡Todas las facturas NFE se eliminaron exitosamente!")
        else:
            print(f"⚠️ {delete_result.get('failed', 0)} facturas fallaron en la eliminación")


def main():
    """Función principal"""
    tester = NFEInvoiceDeletionTester()
    tester.run_test()


if __name__ == "__main__":
    main()
