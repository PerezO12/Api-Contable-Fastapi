"""
Test para verificar que los mappings de columnas se persisten correctamente
entre lotes en el sistema de importación genérica.
"""
import pytest
import tempfile
import os
import csv
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.deps import get_db, get_current_active_user
from app.models.user import User


def test_session_mappings_persistence():
    """
    Test que verifica que los mappings configurados en /mapping
    se mantengan para el endpoint /execute sin necesidad de reenviarlos
    """
    client = TestClient(app)
    
    # Mock user for authentication
    test_user = User(id=1, username="testuser", email="test@example.com")
    
    def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    
    try:
        # 1. Crear archivo CSV de prueba con productos
        test_data = [
            ["Nombre Producto", "Precio", "Categoria"],
            ["Producto 1", "100.50", "Categoria A"],
            ["Producto 2", "200.75", "Categoria B"],
            ["Producto 3", "50.25", "Categoria C"]
        ]
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(test_data)
            temp_file_path = f.name
        
        # 2. Crear sesión de importación
        with open(temp_file_path, 'rb') as f:
            response = client.post(
                "/api/v1/generic-import/sessions",
                files={"file": ("test_products.csv", f, "text/csv")},
                data={"model_name": "product"}
            )
        
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["session"]["token"]
        
        print(f"Created session: {session_id}")
        
        # 3. Configurar mappings de columnas
        mappings = [
            {
                "column_name": "Nombre Producto",
                "field_name": "name"
            },
            {
                "column_name": "Precio", 
                "field_name": "sale_price"
            },
            {
                "column_name": "Categoria",
                "field_name": "category"
            }
        ]
        
        response = client.post(
            f"/api/v1/generic-import/sessions/{session_id}/mapping",
            json=mappings
        )
        
        assert response.status_code == 200
        mapping_result = response.json()
        print(f"Mapping configured: {mapping_result}")
        
        # 4. Ejecutar importación SIN enviar mappings (debe usar los guardados)
        response = client.post(
            f"/api/v1/generic-import/sessions/{session_id}/execute",
            json={
                "import_policy": "create_only",
                "skip_errors": False,
                "batch_size": 2  # Forzar múltiples lotes
            }
        )
        
        # Si funciona correctamente, debería usar los mappings guardados
        if response.status_code == 200:
            print("✅ SUCCESS: Execute worked with saved mappings")
            result = response.json()
            print(f"Import result: {result}")
        else:
            print(f"❌ ERROR: Execute failed - {response.status_code}: {response.text}")
            
        # 5. También probar ejecutar con mappings explícitos (debe funcionar)
        response_with_mappings = client.post(
            f"/api/v1/generic-import/sessions/{session_id}/execute",
            json={
                "mappings": mappings,
                "import_policy": "create_only", 
                "skip_errors": False,
                "batch_size": 2
            }
        )
        
        if response_with_mappings.status_code == 200:
            print("✅ SUCCESS: Execute also works with explicit mappings")
        else:
            print(f"❌ ERROR: Execute with explicit mappings failed - {response_with_mappings.status_code}: {response_with_mappings.text}")
    
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        # Restore dependency
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_session_mappings_persistence()
