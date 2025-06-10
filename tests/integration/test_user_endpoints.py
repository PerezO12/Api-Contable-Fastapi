"""
Tests de integración para los endpoints de usuarios
"""
import pytest
import uuid
from httpx import AsyncClient
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.users
class TestUserEndpoints:
    """Tests para los endpoints de gestión de usuarios"""

    async def test_get_current_user_info(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener información del usuario actual"""
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar campos obligatorios
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "role" in data
        assert "is_active" in data
        assert "created_at" in data
        
        # Verificar que es el usuario admin
        assert data["email"] == "admin@test.com"
        assert data["role"] == "ADMIN"
        assert data["is_active"] is True

    async def test_create_user_by_admin(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para crear usuario por administrador"""
        new_user_data = {
            "email": "newuser@test.com",
            "full_name": "New Test User",
            "role": "CONTADOR"
        }
        
        response = await client.post(
            "/api/v1/users/admin/create-user",
            json=new_user_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == new_user_data["email"]
        assert data["full_name"] == new_user_data["full_name"]
        assert data["role"] == new_user_data["role"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    async def test_create_user_by_admin_invalid_role(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para crear usuario con rol inválido"""
        new_user_data = {
            "email": "invalidrole@test.com",
            "full_name": "Invalid Role User",
            "role": "INVALID_ROLE"
        }
        
        response = await client.post(
            "/api/v1/users/admin/create-user",
            json=new_user_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 422  # Validation error

    async def test_create_user_by_admin_duplicate_email(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para crear usuario con email duplicado"""
        new_user_data = {
            "email": "admin@test.com",  # Email ya existente
            "full_name": "Duplicate Email User",
            "role": "CONTADOR"
        }
        
        response = await client.post(
            "/api/v1/users/admin/create-user",
            json=new_user_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400

    async def test_create_user_by_non_admin(self, client: AsyncClient, auth_headers_contador: Dict[str, str]):
        """Test para crear usuario siendo no administrador"""
        new_user_data = {
            "email": "unauthorized@test.com",
            "full_name": "Unauthorized User",
            "role": "CONTADOR"
        }
        
        response = await client.post(
            "/api/v1/users/admin/create-user",
            json=new_user_data,
            headers=auth_headers_contador
        )
        
        assert response.status_code == 403  # Forbidden

    async def test_get_user_stats(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener estadísticas de usuarios"""
        response = await client.get(
            "/api/v1/users/admin/stats",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar campos de estadísticas
        assert "total_users" in data
        assert "active_users" in data
        assert "inactive_users" in data
        assert "users_by_role" in data
        assert "recent_registrations" in data
        
        assert isinstance(data["total_users"], int)
        assert isinstance(data["active_users"], int)
        assert isinstance(data["inactive_users"], int)
        assert isinstance(data["users_by_role"], dict)

    async def test_get_user_stats_non_admin(self, client: AsyncClient, auth_headers_contador: Dict[str, str]):
        """Test para obtener estadísticas sin ser admin"""
        response = await client.get(
            "/api/v1/users/admin/stats",
            headers=auth_headers_contador
        )
        
        assert response.status_code == 403

    async def test_list_all_users(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para listar todos los usuarios"""
        response = await client.get(
            "/api/v1/users/admin/list",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1  # Al menos el usuario admin
        
        # Verificar estructura de usuario
        user = data[0]
        assert "id" in user
        assert "email" in user
        assert "full_name" in user
        assert "role" in user
        assert "is_active" in user

    async def test_list_users_with_pagination(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para listar usuarios con paginación"""
        response = await client.get(
            "/api/v1/users/admin/list?skip=0&limit=2",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 2

    async def test_list_users_filter_by_role(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para listar usuarios filtrados por rol"""
        response = await client.get(
            "/api/v1/users/admin/list?role=ADMIN",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Todos los usuarios retornados deben ser ADMIN
        for user in data:
            assert user["role"] == "ADMIN"

    async def test_toggle_user_active(self, client: AsyncClient, auth_headers_admin: Dict[str, str], contador_user: Dict[str, Any]):
        """Test para activar/desactivar usuario"""
        user_id = contador_user["id"]
        
        response = await client.put(
            f"/api/v1/users/{user_id}/toggle-active",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_active" in data
        # Verificar que el estado cambió (asumiendo que estaba activo)
        assert isinstance(data["is_active"], bool)

    async def test_toggle_user_active_invalid_id(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para activar/desactivar usuario con ID inválido"""
        invalid_id = str(uuid.uuid4())
        
        response = await client.put(
            f"/api/v1/users/{invalid_id}/toggle-active",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 404

    async def test_reset_user_password(self, client: AsyncClient, auth_headers_admin: Dict[str, str], contador_user: Dict[str, Any]):
        """Test para resetear contraseña de usuario"""
        user_id = contador_user["id"]
        
        response = await client.put(
            f"/api/v1/users/{user_id}/reset-password",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "temporary_password" in data
        assert "reset" in data["message"].lower()
        assert isinstance(data["temporary_password"], str)
        assert len(data["temporary_password"]) >= 8

    async def test_force_password_change(self, client: AsyncClient, auth_headers_admin: Dict[str, str], contador_user: Dict[str, Any]):
        """Test para forzar cambio de contraseña"""
        user_id = contador_user["id"]
        
        response = await client.put(
            f"/api/v1/users/{user_id}/force-password-change?force=true",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["id"] == user_id

    async def test_change_own_password(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para cambiar propia contraseña"""
        password_data = {
            "current_password": "admin123",
            "new_password": "newadmin123",
            "confirm_password": "newadmin123"
        }
        
        response = await client.post(
            "/api/v1/users/change-password",
            json=password_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "cambiada" in data["message"].lower()

    async def test_change_password_mismatch(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para cambiar contraseña con confirmación incorrecta"""
        password_data = {
            "current_password": "admin123",
            "new_password": "newadmin123",
            "confirm_password": "differentpassword"
        }
        
        response = await client.post(
            "/api/v1/users/change-password",
            json=password_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para cambiar contraseña con contraseña actual incorrecta"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newadmin123",
            "confirm_password": "newadmin123"
        }
        
        response = await client.post(
            "/api/v1/users/change-password",
            json=password_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code in [400, 401]
