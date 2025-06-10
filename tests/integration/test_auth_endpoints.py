"""
Tests de integración para los endpoints de autenticación
"""
import pytest
from httpx import AsyncClient
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.auth
class TestAuthEndpoints:
    """Tests para los endpoints de autenticación"""
    
    async def test_login_success(self, client: AsyncClient, admin_user: Dict[str, Any]):
        """Test de login exitoso"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": admin_user["email"],
                "password": admin_user["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    async def test_login_invalid_credentials(self, client: AsyncClient, admin_user: Dict[str, Any]):
        """Test de login con credenciales inválidas"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": admin_user["email"],
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test de login con usuario inexistente"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_login_form_oauth2(self, client: AsyncClient, admin_user: Dict[str, Any]):
        """Test de login usando OAuth2PasswordRequestForm"""
        response = await client.post(
            "/api/v1/auth/login/form",
            data={
                "username": admin_user["email"],  # OAuth2 usa 'username' field
                "password": admin_user["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data

    async def test_refresh_token(self, client: AsyncClient, admin_user: Dict[str, Any]):
        """Test de renovación de token"""
        # Primero hacer login para obtener refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": admin_user["email"],
                "password": admin_user["password"]
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Renovar token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test de renovación con refresh token inválido"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401

    async def test_logout(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test de logout"""
        response = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "success" in data["message"].lower()

    async def test_logout_without_auth(self, client: AsyncClient):
        """Test de logout sin autenticación"""
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401

    async def test_setup_admin_when_no_admin_exists(self, client: AsyncClient):
        """Test de creación de admin cuando no existe ninguno"""
        # Este test podría fallar si ya existe un admin
        # En un entorno de test limpio debería funcionar
        response = await client.post("/api/v1/auth/setup-admin")
        
        # Puede ser 201 (creado) o 409 (ya existe)
        assert response.status_code in [200, 201, 409]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "email" in data
            assert "full_name" in data
            assert "role" in data
        else:
            # Ya existe un admin
            data = response.json()
            assert "detail" in data

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test de acceso a endpoint protegido sin token"""
        response = await client.get("/api/v1/users/me")
        
        assert response.status_code == 401

    async def test_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Test de acceso a endpoint protegido con token inválido"""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401

    async def test_protected_endpoint_with_valid_token(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test de acceso a endpoint protegido con token válido"""
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data
        assert "role" in data
