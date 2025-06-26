#!/usr/bin/env python3
"""
Script para verificar el estado de la base de datos después de la importación
"""

import httpx
import json

BASE_URL = "http://localhost:8000"
TEST_CREDENTIALS = {
    "email": "admin@contable.com",
    "password": "Admin123!"
}

def check_database_status():
    """Verificar estado de la base de datos"""
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    try:
        # Login
        response = client.post("/api/v1/auth/login", json=TEST_CREDENTIALS)
        if response.status_code != 200:
            print(f"❌ Error en login: {response.status_code}")
            return
        
        token = response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Login exitoso")
        
        # Listar NFe
        response = client.get("/api/v1/nfe/")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            items = data.get('items', [])
            
            print(f"\n📊 ESTADO DE LA BASE DE DATOS:")
            print(f"   Total NFe: {total}")
            
            if items:
                print(f"\n📋 ÚLTIMAS NFe IMPORTADAS:")
                for nfe in items[:10]:  # Mostrar las primeras 10
                    print(f"   - NFe {nfe.get('numero_nfe')}: {nfe.get('nome_emitente')} -> {nfe.get('nome_destinatario')}")
                    print(f"     Status: {nfe.get('status')} | Valor: R$ {nfe.get('valor_total_nfe', 0)}")
                    print(f"     Data emissão: {nfe.get('data_emissao', 'N/A')}")
                    print()
                    
                # Agrupar por status
                status_count = {}
                for nfe in items:
                    status = nfe.get('status', 'UNKNOWN')
                    status_count[status] = status_count.get(status, 0) + 1
                
                print(f"📈 DISTRIBUIÇÃO POR STATUS (amostra de {len(items)}):")
                for status, count in status_count.items():
                    print(f"   - {status}: {count}")
            else:
                print("   Nenhuma NFe encontrada")
        else:
            print(f"❌ Error al listar NFe: {response.status_code} - {response.text}")
            
        # Verificar también contadores de entidades
        try:
            from app.database import get_db
            from app.models.nfe import NFe
            from app.models.invoice import Invoice
            from app.models.third_party import ThirdParty
            from app.models.product import Product
            
            db = next(get_db())
            
            nfe_count = db.query(NFe).count()
            invoice_count = db.query(Invoice).count()
            third_party_count = db.query(ThirdParty).count()
            product_count = db.query(Product).count()
            
            print(f"\n🗃️  CONTADORES DE ENTIDADES EN BD:")
            print(f"   NFe total: {nfe_count}")
            print(f"   Facturas total: {invoice_count}")
            print(f"   Terceros total: {third_party_count}")
            print(f"   Productos total: {product_count}")
            
            db.close()
            
        except Exception as e:
            print(f"⚠️  No se pudo acceder directamente a la BD: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        client.close()

if __name__ == "__main__":
    check_database_status()
