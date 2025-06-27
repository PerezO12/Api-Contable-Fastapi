#!/usr/bin/env python3
"""
Test simple para verificar que las NFE fueron desvinculadas correctamente
"""

import httpx

# Configuración
BASE_URL = "http://localhost:8000"
TEST_CREDENTIALS = {
    "email": "admin@contable.com",
    "password": "Admin123!"
}

def verify_nfe_unlinked():
    """Verificar que hay NFE con status UNLINKED"""
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)
    
    # Login
    response = client.post("/api/v1/auth/login", json=TEST_CREDENTIALS)
    if response.status_code != 200:
        print(f"❌ Error en login: {response.status_code}")
        return
    
    token = response.json().get("access_token")
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    # Buscar NFE con status UNLINKED
    response = client.get("/api/v1/nfe/", params={
        "page": 1,
        "page_size": 100
    })
    
    if response.status_code == 200:
        nfe_data = response.json()
        unlinked_nfes = [nfe for nfe in nfe_data.get('items', []) if nfe.get('status') == 'UNLINKED']
        
        print(f"🔍 Total NFE encontradas: {nfe_data.get('total', 0)}")
        print(f"✅ NFE desvinculadas (UNLINKED): {len(unlinked_nfes)}")
        
        if unlinked_nfes:
            print("\n📋 NFE desvinculadas:")
            for nfe in unlinked_nfes[:5]:  # Mostrar solo las primeras 5
                print(f"   - NFE {nfe.get('numero_nfe')}: Chave {nfe.get('chave_nfe')[:10]}... | invoice_id: {nfe.get('invoice_id')}")
        else:
            print("⚠️ No se encontraron NFE con status UNLINKED")
    else:
        print(f"❌ Error al buscar NFE: {response.status_code}")

if __name__ == "__main__":
    verify_nfe_unlinked()
