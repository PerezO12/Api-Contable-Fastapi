# Endpoints de Autenticación

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
  "password": "mi_contraseña_segura"
}
```

#### Schema de Request
```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str
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

#### Schema de Response
```python
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
```

#### Códigos de Error
- **400 Bad Request**: Datos de entrada inválidos
- **401 Unauthorized**: Credenciales incorrectas
- **423 Locked**: Cuenta bloqueada por intentos fallidos
- **422 Unprocessable Entity**: Formato de email inválido

#### Ejemplo de Error
```json
{
  "detail": "Credenciales inválidas"
}
```

#### Ejemplo de Uso
```python
import httpx

async def login_user(email: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            return tokens
        else:
            raise Exception(f"Login failed: {response.text}")

# Uso
tokens = await login_user("admin@contable.com", "Admin123!")
access_token = tokens["access_token"]
```

---

### 🔐 POST /login/form
Autenticación compatible con OAuth2PasswordRequestForm.

#### Request
```http
POST /api/v1/auth/login/form
Content-Type: application/x-www-form-urlencoded

username=usuario@empresa.com&password=mi_contraseña_segura
```

#### Parámetros Form
- `username`: Email del usuario (OAuth2 estándar usa 'username')
- `password`: Contraseña del usuario

#### Response
Misma estructura que `/login`

#### Ejemplo de Uso con FastAPI TestClient
```python
from fastapi.testclient import TestClient

def test_login_form():
    response = client.post(
        "/api/v1/auth/login/form",
        data={"username": "admin@contable.com", "password": "Admin123!"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
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

#### Ejemplo de Uso
```python
async def refresh_access_token(refresh_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        if response.status_code == 200:
            new_tokens = response.json()
            return new_tokens["access_token"]
        else:
            # Refresh token inválido, requerir login
            raise Exception("Please login again")
```

---

### 🚪 POST /logout
Cierre de sesión del usuario autenticado.

#### Request
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Headers Requeridos
- `Authorization`: Bearer token del usuario autenticado

#### Response Exitosa (200)
```json
{
  "message": "Logged out successfully"
}
```

#### Códigos de Error
- **401 Unauthorized**: Token inválido o expirado
- **500 Internal Server Error**: Error durante el logout

#### Ejemplo de Uso
```python
async def logout_user(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/logout",
            headers=headers
        )
        
        if response.status_code == 200:
            print("Logout successful")
            # Eliminar tokens del almacenamiento local
            clear_stored_tokens()
        else:
            print(f"Logout failed: {response.text}")
```

---

### 👤 POST /setup-admin
Endpoint especial para crear el primer usuario administrador.

#### Request
```http
POST /api/v1/auth/setup-admin
```

#### Sin Parámetros
Este endpoint utiliza configuraciones predefinidas del sistema.

#### Response Exitosa (200)
```json
{
  "id": "uuid-del-admin",
  "email": "admin@contable.com",
  "full_name": "Administrador del Sistema",
  "role": "ADMIN",
  "is_active": true,
  "created_at": "2025-06-10T10:30:00Z"
}
```

#### Schema de Response
```python
class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    # ... otros campos
```

#### Códigos de Error
- **409 Conflict**: Ya existe un administrador en el sistema
- **500 Internal Server Error**: Error creando el administrador

#### Ejemplo de Error
```json
{
  "detail": "Ya existe un usuario administrador en el sistema"
}
```

#### Ejemplo de Uso
```python
async def setup_initial_admin():
    """Se ejecuta durante la configuración inicial del sistema"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/setup-admin"
        )
        
        if response.status_code == 200:
            admin_user = response.json()
            print(f"Admin created: {admin_user['email']}")
            return admin_user
        elif response.status_code == 409:
            print("Admin already exists")
            return None
        else:
            raise Exception(f"Failed to create admin: {response.text}")
```

## Configuración de Headers

### Headers de Request Comunes
```http
Content-Type: application/json
Accept: application/json
User-Agent: MyApp/1.0
```

### Headers de Autenticación
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Manejo de Errores

### Estructura de Error Estándar
```json
{
  "detail": "Descripción del error",
  "error_code": "CODIGO_ERROR_OPCIONAL",
  "context": {
    "campo_adicional": "valor_adicional"
  }
}
```

### Códigos de Error Comunes

#### 400 Bad Request
```json
{
  "detail": "Invalid request format",
  "error_code": "VALIDATION_ERROR"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Credenciales inválidas",
  "error_code": "AUTHENTICATION_ERROR"
}
```

#### 423 Locked
```json
{
  "detail": "Cuenta bloqueada hasta 2025-06-10 11:00:00",
  "error_code": "ACCOUNT_LOCKED",
  "context": {
    "locked_until": "2025-06-10T11:00:00Z",
    "attempts": 5
  }
}
```

#### 429 Too Many Requests
```json
{
  "detail": "Too many requests. Try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "context": {
    "retry_after": 60
  }
}
```

## Flujos de Integración

### Flujo Completo de Autenticación
```python
class AuthClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
    
    async def login(self, email: str, password: str):
        """Autentica usuario y almacena tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens["access_token"]
                self.refresh_token = tokens["refresh_token"]
                return True
            else:
                raise Exception(f"Login failed: {response.json()}")
    
    async def make_authenticated_request(self, method: str, url: str, **kwargs):
        """Hace request autenticado con manejo de renovación"""
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
                # Opcionalmente actualizar refresh token
                if "refresh_token" in tokens:
                    self.refresh_token = tokens["refresh_token"]
            else:
                # Refresh token inválido, requerir login
                self.access_token = None
                self.refresh_token = None
                raise Exception("Please login again")
    
    async def logout(self):
        """Cierra sesión del usuario"""
        if self.access_token:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/auth/logout",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
        
        self.access_token = None
        self.refresh_token = None

# Uso del cliente
auth_client = AuthClient("http://localhost:8000/api/v1")
await auth_client.login("admin@contable.com", "Admin123!")

# Hacer requests autenticados
response = await auth_client.make_authenticated_request(
    "GET", "http://localhost:8000/api/v1/users/me"
)
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
      
      return true;
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

### Headers de Seguridad
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Configurar CORS apropiadamente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com"],  # No usar * en producción
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Headers de seguridad adicionales
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### Logging y Auditoría
```python
import logging

logger = logging.getLogger(__name__)

@router.post("/login")
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent")
    
    try:
        # Intentar autenticación
        result = await auth_service.login_user(
            login_data.email, 
            login_data.password
        )
        
        # Log exitoso
        logger.info(
            f"Successful login: {login_data.email} from {client_ip}",
            extra={
                "event": "login_success",
                "email": login_data.email,
                "ip": client_ip,
                "user_agent": user_agent
            }
        )
        
        return result
        
    except AuthenticationError:
        # Log fallido
        logger.warning(
            f"Failed login attempt: {login_data.email} from {client_ip}",
            extra={
                "event": "login_failed",
                "email": login_data.email,
                "ip": client_ip,
                "user_agent": user_agent
            }
        )
        raise_authentication_error("Credenciales inválidas")
```

## Testing de Endpoints

### Tests Unitarios
```python
import pytest
from fastapi.testclient import TestClient

def test_login_success(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "Test123!"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "wrong_password"}
    )
    
    assert response.status_code == 401
    assert "detail" in response.json()

def test_refresh_token(client: TestClient):
    # Primero hacer login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "Test123!"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Probar refresh
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_logout(client: TestClient, authenticated_user):
    """Test con usuario autenticado via fixture"""
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {authenticated_user.access_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
```

### Tests de Integración
```python
@pytest.mark.asyncio
async def test_complete_auth_flow():
    """Test del flujo completo de autenticación"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # 1. Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "Test123!"}
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        
        # 2. Usar access token
        user_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert user_response.status_code == 200
        
        # 3. Refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 200
        
        # 4. Logout
        logout_response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert logout_response.status_code == 200
```

## Referencias

- [Autenticación y Seguridad](./authentication.md)
- [Sesiones y Tokens](./sessions-tokens.md)
- [Endpoints de Usuarios](./user-endpoints.md)
- [Roles y Permisos](./roles-permissions.md)
