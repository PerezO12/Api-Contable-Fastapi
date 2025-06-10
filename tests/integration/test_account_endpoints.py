"""
Tests de integración para los endpoints de cuentas contables
"""
import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.accounts
class TestAccountEndpoints:
    """Tests para los endpoints de gestión de cuentas contables"""

    @pytest.fixture
    async def sample_account_data(self):
        """Datos de muestra para crear cuenta"""
        return {
            "code": "1001",
            "name": "Caja",
            "account_type": "ACTIVO",
            "category": "ACTIVO_CORRIENTE",
            "description": "Cuenta de efectivo en caja",
            "is_active": True
        }

    async def test_create_account_admin(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para crear cuenta siendo administrador"""
        response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verificar campos obligatorios
        assert "id" in data
        assert "code" in data
        assert "name" in data
        assert "account_type" in data
        assert "category" in data
        assert "balance" in data
        assert "is_active" in data
        assert "created_at" in data
        
        # Verificar valores
        assert data["code"] == sample_account_data["code"]
        assert data["name"] == sample_account_data["name"]
        assert data["account_type"] == sample_account_data["account_type"]
        assert data["category"] == sample_account_data["category"]
        assert data["is_active"] == sample_account_data["is_active"]
        assert data["balance"] == "0.00"  # Balance inicial

    async def test_create_account_contador(self, client: AsyncClient, auth_headers_contador: Dict[str, str], sample_account_data):
        """Test para crear cuenta siendo contador"""
        sample_account_data["code"] = "1002"  # Diferente código para evitar duplicado
        
        response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_contador
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "1002"

    async def test_create_account_readonly_forbidden(self, client: AsyncClient, auth_headers_readonly: Dict[str, str], sample_account_data):
        """Test para crear cuenta siendo usuario de solo lectura"""
        sample_account_data["code"] = "1003"
        
        response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_readonly
        )
        
        assert response.status_code == 403

    async def test_create_account_duplicate_code(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para crear cuenta con código duplicado"""
        # Crear primera cuenta
        await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        
        # Intentar crear segunda cuenta con mismo código
        response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400

    async def test_create_account_invalid_type(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para crear cuenta con tipo inválido"""
        sample_account_data["account_type"] = "TIPO_INVALIDO"
        
        response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 422

    async def test_list_accounts(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para listar cuentas"""
        # Crear una cuenta primero
        await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        
        response = await client.get(
            "/api/v1/accounts/",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Verificar estructura de cuenta
        account = data[0]
        assert "id" in account
        assert "code" in account
        assert "name" in account
        assert "account_type" in account

    async def test_list_accounts_with_filters(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para listar cuentas con filtros"""
        response = await client.get(
            "/api/v1/accounts/?account_type=ACTIVO&is_active=true&limit=10",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Verificar que los filtros se aplicaron
        for account in data:
            assert account["account_type"] == "ACTIVO"
            assert account["is_active"] is True

    async def test_list_accounts_pagination(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para listar cuentas con paginación"""
        response = await client.get(
            "/api/v1/accounts/?skip=0&limit=5",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 5

    async def test_get_account_tree(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener árbol de cuentas"""
        response = await client.get(
            "/api/v1/accounts/tree",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)

    async def test_get_account_stats(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener estadísticas de cuentas"""
        response = await client.get(
            "/api/v1/accounts/stats",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar campos de estadísticas
        assert "total_accounts" in data
        assert "active_accounts" in data
        assert "accounts_by_type" in data
        assert "accounts_by_category" in data
        
        assert isinstance(data["total_accounts"], int)
        assert isinstance(data["active_accounts"], int)
        assert isinstance(data["accounts_by_type"], dict)

    async def test_get_specific_account(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para obtener cuenta específica"""
        # Crear cuenta primero
        create_response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        created_account = create_response.json()
        account_id = created_account["id"]
        
        # Obtener cuenta específica
        response = await client.get(
            f"/api/v1/accounts/{account_id}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == account_id
        assert data["code"] == sample_account_data["code"]
        assert data["name"] == sample_account_data["name"]

    async def test_get_nonexistent_account(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener cuenta inexistente"""
        nonexistent_id = str(uuid.uuid4())
        
        response = await client.get(
            f"/api/v1/accounts/{nonexistent_id}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 404

    async def test_update_account(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para actualizar cuenta"""
        # Crear cuenta primero
        create_response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        created_account = create_response.json()
        account_id = created_account["id"]
        
        # Actualizar cuenta
        update_data = {
            "name": "Caja Actualizada",
            "description": "Descripción actualizada"
        }
        
        response = await client.put(
            f"/api/v1/accounts/{account_id}",
            json=update_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["code"] == sample_account_data["code"]  # No debe cambiar

    async def test_update_account_readonly_forbidden(self, client: AsyncClient, auth_headers_readonly: Dict[str, str], sample_account_data):
        """Test para actualizar cuenta siendo usuario de solo lectura"""
        # Primero crear cuenta como admin
        admin_headers = {}  # Necesitaríamos crear admin headers aquí
        
        # Simular que existe una cuenta
        account_id = str(uuid.uuid4())
        update_data = {"name": "Nuevo nombre"}
        
        response = await client.put(
            f"/api/v1/accounts/{account_id}",
            json=update_data,
            headers=auth_headers_readonly
        )
        
        assert response.status_code == 403

    async def test_delete_account(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para eliminar cuenta"""
        # Crear cuenta primero
        create_response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        created_account = create_response.json()
        account_id = created_account["id"]
        
        # Eliminar cuenta
        response = await client.delete(
            f"/api/v1/accounts/{account_id}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 204

    async def test_get_account_balance(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para obtener saldo de cuenta"""
        # Crear cuenta primero
        create_response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        created_account = create_response.json()
        account_id = created_account["id"]
        
        # Obtener saldo
        response = await client.get(
            f"/api/v1/accounts/{account_id}/balance",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "account_id" in data
        assert "balance" in data
        assert "as_of_date" in data
        assert data["account_id"] == account_id

    async def test_get_account_movements(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para obtener movimientos de cuenta"""
        # Crear cuenta primero
        create_response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        created_account = create_response.json()
        account_id = created_account["id"]
        
        # Obtener movimientos
        response = await client.get(
            f"/api/v1/accounts/{account_id}/movements",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "account_id" in data
        assert "movements" in data
        assert "period" in data
        assert isinstance(data["movements"], list)

    async def test_validate_account(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_account_data):
        """Test para validar cuenta"""
        # Crear cuenta primero
        create_response = await client.post(
            "/api/v1/accounts/",
            json=sample_account_data,
            headers=auth_headers_admin
        )
        created_account = create_response.json()
        account_id = created_account["id"]
        
        # Validar cuenta
        response = await client.post(
            f"/api/v1/accounts/{account_id}/validate",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data
        assert isinstance(data["is_valid"], bool)
        assert isinstance(data["errors"], list)
        assert isinstance(data["warnings"], list)

    async def test_get_accounts_by_type(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener cuentas por tipo"""
        response = await client.get(
            "/api/v1/accounts/type/ACTIVO",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "account_type" in data
        assert "accounts" in data
        assert data["account_type"] == "ACTIVO"
        assert isinstance(data["accounts"], list)

    async def test_bulk_account_operation_admin_only(self, client: AsyncClient, auth_headers_contador: Dict[str, str]):
        """Test para operación masiva (solo admin)"""
        bulk_operation = {
            "operation": "activate",
            "account_ids": [str(uuid.uuid4())]
        }
        
        response = await client.post(
            "/api/v1/accounts/bulk-operation",
            json=bulk_operation,
            headers=auth_headers_contador
        )
        
        assert response.status_code == 403

    async def test_export_accounts_csv(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para exportar cuentas a CSV"""
        response = await client.get(
            "/api/v1/accounts/export/csv",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
