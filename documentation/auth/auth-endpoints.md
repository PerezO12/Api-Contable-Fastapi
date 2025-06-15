# Endpoints de Autenticación - ACTUALIZADO

## Descripción General

Los endpoints de autenticación proporcionan las funcionalidades necesarias para el login, logout, renovación de tokens y gestión de sesiones. Todos los endpoints están diseñados siguiendo las mejores prácticas de seguridad y estándares REST.

## Base URL

```
Base URL: /api/v1/auth
```

## Endpoints Disponibles

### 🔐 POST /login
Autenticación de usuario con email y contraseña.

#### Request
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "usuario@empresa.com",
  "password": "mi_password_seguro"
}
```

#### Schema de Request
```python
class UserLogin(BaseModel):
    email: str  # Email del usuario
    password: str  # Contraseña del usuario
```

#### Response Exitosa (200)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "usuario@empresa.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "CONTADOR",
    "is_active": true
  }
}
```

#### Códigos de Error
- **401 Unauthorized**: Credenciales inválidas
- **404 Not Found**: Usuario no encontrado
- **422 Unprocessable Entity**: Formato de datos inválido

---

### 🔐 POST /login/form
Autenticación compatible con OAuth2PasswordRequestForm (para compatibilidad).

#### Request
```http
POST /api/v1/auth/login/form
Content-Type: application/x-www-form-urlencoded

username=usuario@empresa.com&password=mi_password_seguro
```

#### Response Exitosa (200)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 🔄 POST /refresh
Renueva el token de acceso usando el refresh token.

#### Request
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Schema de Request
```python
class RefreshTokenRequest(BaseModel):
    refresh_token: str
```

#### Response Exitosa (200)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer", 
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Códigos de Error
- **401 Unauthorized**: Refresh token inválido o expirado
- **422 Unprocessable Entity**: Formato de request inválido

---

### 🚪 POST /logout
Cierre de sesión del usuario autenticado.

#### Request
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "message": "Logged out successfully"
}
```

#### Códigos de Error
- **401 Unauthorized**: Token inválido o expirado
- **500 Internal Server Error**: Error durante el logout

---

### 👤 POST /setup-admin
Endpoint especial para crear el primer usuario administrador del sistema.

**NOTA IMPORTANTE**: Este endpoint solo funciona si no existe ningún administrador en el sistema. Es útil para la configuración inicial.

#### Request
```http
POST /api/v1/auth/setup-admin
Content-Type: application/json
```

#### Response Exitosa (200)
```json
{
  "id": "admin-uuid-here",
  "email": "admin@sistema.com",
  "first_name": "Administrador",
  "last_name": "Sistema",
  "role": "ADMIN",
  "is_active": true,
  "must_change_password": true,
  "created_at": "2024-06-15T14:30:00Z",
  "updated_at": "2024-06-15T14:30:00Z"
}
```

#### Códigos de Error
- **409 Conflict**: Ya existe un usuario administrador en el sistema
- **500 Internal Server Error**: Error creando el administrador

---

## Flujos de Integración

### Flujo Completo de Autenticación

```python
import httpx
import asyncio
from datetime import datetime, timedelta

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
    
    async def login(self, email: str, password: str):
        """Autenticar usuario"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"])
                return data["user"]
            else:
                raise Exception(f"Login failed: {response.json()}")
    
    async def make_authenticated_request(self, method: str, url: str, **kwargs):
        """Hacer request autenticado con renovación automática de token"""
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)
            
            # Si token expiró, intentar renovar
            if response.status_code == 401:
                await self.refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = await client.request(method, url, **kwargs)
            
            return response
    
    async def refresh_access_token(self):
        """Renueva el access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            
            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens["access_token"]
                self.refresh_token = tokens["refresh_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=tokens["expires_in"])
            else:
                raise Exception("Token refresh failed")
    
    async def logout(self):
        """Cerrar sesión"""
        if self.access_token:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/auth/logout",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
        
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

# Ejemplo de uso
async def main():
    api = ApiClient("http://localhost:8000/api/v1")
    
    # Login
    user = await api.login("usuario@empresa.com", "password")
    print(f"Logged in as: {user['email']}")
    
    # Hacer request autenticado
    response = await api.make_authenticated_request(
        "GET", "http://localhost:8000/api/v1/users/me"
    )
    print(f"User info: {response.json()}")
    
    # Logout
    await api.logout()
```

### Integración con Frontend (JavaScript)

```javascript
class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }
  
  async login(email, password) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
      const tokens = await response.json();
      this.accessToken = tokens.access_token;
      this.refreshToken = tokens.refresh_token;
      
      // Almacenar de forma segura
      localStorage.setItem('access_token', this.accessToken);
      localStorage.setItem('refresh_token', this.refreshToken);
      
      return tokens.user;
    } else {
      const error = await response.json();
      throw new Error(error.detail);
    }
  }
  
  async makeAuthenticatedRequest(url, options = {}) {
    // Agregar header de autorización
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.accessToken}`
    };
    
    let response = await fetch(url, options);
    
    // Si token expiró, intentar renovar
    if (response.status === 401) {
      await this.refreshAccessToken();
      options.headers['Authorization'] = `Bearer ${this.accessToken}`;
      response = await fetch(url, options);
    }
    
    return response;
  }
  
  async refreshAccessToken() {
    const response = await fetch(`${this.baseUrl}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });
    
    if (response.ok) {
      const tokens = await response.json();
      this.accessToken = tokens.access_token;
      localStorage.setItem('access_token', this.accessToken);
    } else {
      // Refresh falló, redirect a login
      this.logout();
      window.location.href = '/login';
    }
  }
  
  async logout() {
    if (this.accessToken) {
      await fetch(`${this.baseUrl}/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.accessToken}` }
      });
    }
    
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

// Uso
const api = new ApiClient('http://localhost:8000/api/v1');
await api.login('usuario@empresa.com', 'password');

// Hacer requests autenticados
const response = await api.makeAuthenticatedRequest('/users/me');
const userData = await response.json();
```

## Seguridad y Mejores Prácticas

### Configuración de Tokens
- **Access Token**: Válido por 30 minutos
- **Refresh Token**: Válido por 7 días
- **Algoritmo**: HS256 (HMAC SHA-256)

### Rate Limiting
```python
# Implementar rate limiting en endpoints sensibles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # 5 intentos por minuto por IP
async def login(request: Request, ...):
    # Lógica de login
```

### Validación de Input
```python
@router.post("/login")
async def login(
    login_data: UserLogin,  # Validación automática con Pydantic
    db: AsyncSession = Depends(get_db)
):
    # Los datos ya están validados por el schema
    # Email formato válido, password presente, etc.
```

### Headers de Seguridad Recomendados
```python
# En middleware o responses
headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}
```

## Códigos de Error Comunes

### 400 Bad Request
- Formato de JSON inválido
- Campos requeridos faltantes

### 401 Unauthorized
- Credenciales inválidas
- Token expirado o inválido

### 403 Forbidden
- Usuario inactivo
- Permisos insuficientes

### 404 Not Found
- Usuario no encontrado
- Endpoint no existe

### 409 Conflict
- Admin ya existe (en setup-admin)

### 422 Unprocessable Entity
- Validación de datos falló
- Formato de email inválido

### 429 Too Many Requests
- Rate limit excedido
- Demasiados intentos de login

### 500 Internal Server Error
- Error del servidor
- Error en base de datos

## Testing de Endpoints

### Ejemplo con pytest
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
```

### Ejemplo con curl
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@empresa.com", "password": "password"}'

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token_here"}'

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer your_access_token_here"
```

## Referencias

- [Endpoints de Usuarios](./user-endpoints-updated.md)
- [Esquemas JWT](../schemas/auth-schemas.md)
- [Configuración de Seguridad](../security/jwt-config.md)
- [Manejo de Errores](../errors/auth-errors.md)
