# Endpoints de Gestión de Usuarios

## Descripción General

Los endpoints de gestión de usuarios proporcionan funcionalidades completas para la administración de cuentas de usuario, incluyendo operaciones CRUD, gestión de contraseñas, estadísticas y operaciones administrativas. Estos endpoints están protegidos según el sistema de roles implementado.

## Base URL

```
Base URL: /api/v1/users
```

## Endpoints Disponibles

### 👤 GET /me
Obtiene la información del usuario autenticado actual.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "usuario@empresa.com",
  "full_name": "Juan Pérez",
  "role": "CONTADOR",
  "is_active": true,
  "notes": "Usuario del departamento contable",
  "last_login": "2025-06-10T10:30:00Z",
  "force_password_change": false,
  "login_attempts": 0,
  "locked_until": null,
  "password_changed_at": "2025-06-01T09:00:00Z",
  "created_by_id": "admin-uuid",
  "created_at": "2025-06-01T09:00:00Z",
  "updated_at": "2025-06-10T10:30:00Z"
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
    notes: Optional[str]
    last_login: Optional[datetime]
    force_password_change: bool
    login_attempts: int
    locked_until: Optional[datetime]
    password_changed_at: Optional[datetime]
    created_by_id: Optional[UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

#### Ejemplo de Uso
```python
async def get_current_user_info(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/users/me",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.text}")
```

---

### 🔑 PUT /me/password
Cambia la contraseña del usuario autenticado.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
PUT /api/v1/users/me/password
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "current_password": "mi_contraseña_actual",
  "new_password": "mi_nueva_contraseña_123!",
  "confirm_password": "mi_nueva_contraseña_123!"
}
```

#### Schema de Request
```python
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        # Validación automática de fortaleza
        pass
```

#### Response Exitosa (200)
```json
{
  "message": "Contraseña actualizada exitosamente"
}
```

#### Códigos de Error
- **400 Bad Request**: Las contraseñas nuevas no coinciden
- **401 Unauthorized**: Contraseña actual incorrecta
- **422 Unprocessable Entity**: Nueva contraseña no cumple criterios

#### Ejemplo de Uso
```python
async def change_password(access_token: str, current_pwd: str, new_pwd: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "current_password": current_pwd,
        "new_password": new_pwd,
        "confirm_password": new_pwd
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            "http://localhost:8000/api/v1/users/me/password",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            print("Password changed successfully")
        else:
            error = response.json()
            raise Exception(error["detail"])
```

---

### 👥 GET /
Obtiene la lista de usuarios del sistema (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
GET /api/v1/users?skip=0&limit=50&role=CONTADOR&is_active=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `skip` (int, opcional): Número de registros a omitir (default: 0)
- `limit` (int, opcional): Máximo número de registros (default: 100)
- `role` (UserRole, opcional): Filtrar por rol específico
- `is_active` (bool, opcional): Filtrar por estado activo/inactivo

#### Response Exitosa (200)
```json
[
  {
    "id": "user-uuid-1",
    "email": "contador@empresa.com", 
    "full_name": "María García",
    "role": "CONTADOR",
    "is_active": true,
    "last_login": "2025-06-10T08:00:00Z",
    "created_at": "2025-05-15T10:00:00Z"
  },
  {
    "id": "user-uuid-2",
    "email": "consulta@empresa.com",
    "full_name": "Carlos López",
    "role": "SOLO_LECTURA", 
    "is_active": true,
    "last_login": "2025-06-09T16:30:00Z",
    "created_at": "2025-05-20T14:00:00Z"
  }
]
```

#### Schema de Response
```python
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
```

---

### 📊 GET /stats
Obtiene estadísticas de usuarios del sistema (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
GET /api/v1/users/stats
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "total_users": 25,
  "active_users": 22,
  "locked_users": 1,
  "users_by_role": {
    "ADMIN": 2,
    "CONTADOR": 8,
    "SOLO_LECTURA": 15
  },
  "recent_logins": 12
}
```

#### Schema de Response
```python
class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    locked_users: int
    users_by_role: dict[str, int]
    recent_logins: int  # Últimas 24 horas
```

---

### ➕ POST /admin/create-user
Crea un nuevo usuario (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/users/admin/create-user
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "email": "nuevo.usuario@empresa.com",
  "full_name": "Ana Martínez",
  "role": "CONTADOR",
  "temporary_password": "TempPass123!",
  "notes": "Nueva contadora del equipo",
  "force_password_change": true
}
```

#### Schema de Request
```python
class UserCreateByAdmin(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.SOLO_LECTURA
    notes: Optional[str] = Field(None, max_length=1000)
    temporary_password: str = Field(..., min_length=8, max_length=100)
    force_password_change: bool = True
```

#### Response Exitosa (201)
```json
{
  "id": "new-user-uuid",
  "email": "nuevo.usuario@empresa.com",
  "full_name": "Ana Martínez",
  "role": "CONTADOR",
  "is_active": true,
  "notes": "Nueva contadora del equipo",
  "force_password_change": true,
  "created_by_id": "admin-uuid",
  "created_at": "2025-06-10T11:00:00Z"
}
```

#### Códigos de Error
- **400 Bad Request**: Email ya existe
- **422 Unprocessable Entity**: Datos de entrada inválidos
- **403 Forbidden**: No es administrador

---

### ✏️ PUT /{user_id}
Actualiza los datos de un usuario específico (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
PUT /api/v1/users/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "full_name": "Ana Martínez Rodríguez",
  "role": "ADMIN",
  "notes": "Promovida a administradora"
}
```

#### Schema de Request
```python
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    notes: Optional[str] = Field(None, max_length=1000)
    force_password_change: Optional[bool] = None
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "nuevo.usuario@empresa.com",
  "full_name": "Ana Martínez Rodríguez",
  "role": "ADMIN",
  "is_active": true,
  "notes": "Promovida a administradora",
  "updated_at": "2025-06-10T11:30:00Z"
}
```

---

### 🔄 PUT /{user_id}/toggle-active
Activa o desactiva un usuario (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
PUT /api/v1/users/123e4567-e89b-12d3-a456-426614174000/toggle-active
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "usuario@empresa.com",
  "full_name": "Usuario Test",
  "role": "CONTADOR",
  "is_active": false,
  "updated_at": "2025-06-10T11:45:00Z"
}
```

---

### 🔑 PUT /{user_id}/reset-password
Resetea la contraseña de un usuario y genera una temporal (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
PUT /api/v1/users/123e4567-e89b-12d3-a456-426614174000/reset-password
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "message": "Contraseña reseteada exitosamente",
  "temporary_password": "NewTemp789!"
}
```

#### ⚠️ Consideraciones de Seguridad
- La contraseña temporal debe comunicarse por canal seguro
- El usuario debe cambiar la contraseña en el primer login
- La contraseña temporal no debe guardarse en logs

---

### 🔒 PUT /{user_id}/force-password-change
Fuerza a un usuario a cambiar su contraseña en el próximo login (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
PUT /api/v1/users/123e4567-e89b-12d3-a456-426614174000/force-password-change?force=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `force` (bool, opcional): true para forzar, false para quitar (default: true)

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "usuario@empresa.com",
  "full_name": "Usuario Test",
  "force_password_change": true,
  "updated_at": "2025-06-10T12:00:00Z"
}
```

---

### 🗑️ DELETE /{user_id}
Elimina un usuario del sistema (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
DELETE /api/v1/users/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "message": "Usuario eliminado exitosamente"
}
```

#### Códigos de Error
- **404 Not Found**: Usuario no encontrado
- **409 Conflict**: No se puede eliminar (por ejemplo, tiene datos asociados)

---

### 📱 GET /{user_id}/sessions
Obtiene las sesiones activas de un usuario (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
GET /api/v1/users/123e4567-e89b-12d3-a456-426614174000/sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "active_sessions": [
    {
      "session_id": "session-jti-1",
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "created_at": "2025-06-10T10:00:00Z",
      "expires_at": "2025-06-10T10:30:00Z",
      "is_current": false
    },
    {
      "session_id": "session-jti-2", 
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "ip_address": "192.168.1.101",
      "user_agent": "Chrome Mobile...",
      "created_at": "2025-06-10T11:00:00Z",
      "expires_at": "2025-06-10T11:30:00Z",
      "is_current": true
    }
  ],
  "total_sessions": 2
}
```

#### Schema de Response
```python
class UserSessionsListResponse(BaseModel):
    user_id: UUID
    active_sessions: List[UserSessionResponse]
    total_sessions: int

class UserSessionResponse(BaseModel):
    session_id: str
    user_id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    expires_at: datetime
    is_current: bool = False
```

---

### 🚪 POST /{user_id}/revoke-sessions
Revoca todas las sesiones de un usuario (logout forzado) (solo administradores).

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/users/123e4567-e89b-12d3-a456-426614174000/revoke-sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "message": "Todas las sesiones han sido revocadas",
  "revoked_sessions": 3
}
```

## Flujos de Integración

### Gestión Completa de Usuario por Admin
```python
class UserManagement:
    def __init__(self, admin_token: str, base_url: str):
        self.admin_token = admin_token
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {admin_token}"}
    
    async def create_user(self, user_data: dict):
        """Crea un nuevo usuario"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users/admin/create-user",
                headers=self.headers,
                json=user_data
            )
            return response.json()
    
    async def get_user_stats(self):
        """Obtiene estadísticas de usuarios"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/stats",
                headers=self.headers
            )
            return response.json()
    
    async def list_users(self, filters: dict = None):
        """Lista usuarios con filtros opcionales"""
        params = filters or {}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users",
                headers=self.headers,
                params=params
            )
            return response.json()
    
    async def reset_user_password(self, user_id: str):
        """Resetea contraseña de usuario"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/users/{user_id}/reset-password",
                headers=self.headers
            )
            return response.json()
    
    async def toggle_user_status(self, user_id: str):
        """Activa/desactiva usuario"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/users/{user_id}/toggle-active",
                headers=self.headers
            )
            return response.json()

# Ejemplo de uso
admin_mgmt = UserManagement(admin_token, "http://localhost:8000/api/v1")

# Crear usuario
new_user = await admin_mgmt.create_user({
    "email": "nuevo@empresa.com",
    "full_name": "Nuevo Usuario", 
    "role": "CONTADOR",
    "temporary_password": "TempPass123!"
})

# Ver estadísticas
stats = await admin_mgmt.get_user_stats()
print(f"Total usuarios: {stats['total_users']}")

# Resetear contraseña si es necesario
reset_result = await admin_mgmt.reset_user_password(new_user["id"])
print(f"Nueva contraseña temporal: {reset_result['temporary_password']}")
```

### Autogestión de Usuario
```python
class UserSelfManagement:
    def __init__(self, access_token: str, base_url: str):
        self.access_token = access_token
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {access_token}"}
    
    async def get_my_info(self):
        """Obtiene información del usuario actual"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/me",
                headers=self.headers
            )
            return response.json()
    
    async def change_password(self, current_pwd: str, new_pwd: str):
        """Cambia la contraseña del usuario"""
        data = {
            "current_password": current_pwd,
            "new_password": new_pwd,
            "confirm_password": new_pwd
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/users/me/password",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 200:
                return True
            else:
                error = response.json()
                raise Exception(error["detail"])

# Ejemplo de uso
user_mgmt = UserSelfManagement(user_token, "http://localhost:8000/api/v1")

# Ver mi información
my_info = await user_mgmt.get_my_info()
print(f"Bienvenido, {my_info['full_name']}")

# Cambiar contraseña si es forzado
if my_info['force_password_change']:
    await user_mgmt.change_password("old_password", "new_secure_password123!")
    print("Contraseña actualizada")
```

## Validaciones y Reglas de Negocio

### Creación de Usuario
- Email debe ser único en el sistema
- Contraseña temporal debe cumplir criterios de fortaleza
- Solo admin puede asignar rol ADMIN
- Usuario se crea con `force_password_change = True` por defecto

### Actualización de Usuario
- Email no puede modificarse directamente
- Solo admin puede cambiar roles
- Cambios de rol se auditan automáticamente
- No se puede cambiar el propio rol

### Eliminación de Usuario
- No se puede eliminar el último administrador
- No se puede eliminar a uno mismo
- Eliminación es física (datos se pierden)
- Se recomienda desactivar en lugar de eliminar

### Gestión de Contraseñas
- Contraseña actual requerida para cambios
- Nueva contraseña debe cumplir criterios de seguridad
- No se puede reutilizar la contraseña actual
- Reset por admin genera contraseña temporal segura

## Códigos de Error Comunes

### 400 Bad Request
```json
{
  "detail": "Email ya existe en el sistema",
  "error_code": "EMAIL_ALREADY_EXISTS"
}
```

### 403 Forbidden  
```json
{
  "detail": "Permisos insuficientes para esta operación",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

### 404 Not Found
```json
{
  "detail": "Usuario no encontrado",
  "error_code": "USER_NOT_FOUND"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Testing de Endpoints

### Tests para Usuarios Regulares
```python
def test_get_current_user(client, authenticated_user):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {authenticated_user.access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == authenticated_user.email

def test_change_password_success(client, authenticated_user):
    response = client.put(
        "/api/v1/users/me/password",
        headers={"Authorization": f"Bearer {authenticated_user.access_token}"},
        json={
            "current_password": "current_password",
            "new_password": "NewSecure123!",
            "confirm_password": "NewSecure123!"
        }
    )
    
    assert response.status_code == 200

def test_change_password_wrong_current(client, authenticated_user):
    response = client.put(
        "/api/v1/users/me/password",
        headers={"Authorization": f"Bearer {authenticated_user.access_token}"},
        json={
            "current_password": "wrong_password",
            "new_password": "NewSecure123!",
            "confirm_password": "NewSecure123!"
        }
    )
    
    assert response.status_code == 401
```

### Tests para Administradores
```python
def test_admin_create_user(client, admin_user):
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "CONTADOR", 
        "temporary_password": "TempPass123!"
    }
    
    response = client.post(
        "/api/v1/users/admin/create-user",
        headers={"Authorization": f"Bearer {admin_user.access_token}"},
        json=user_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["role"] == user_data["role"]

def test_admin_get_user_stats(client, admin_user):
    response = client.get(
        "/api/v1/users/stats",
        headers={"Authorization": f"Bearer {admin_user.access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "users_by_role" in data

def test_non_admin_cannot_create_user(client, regular_user):
    response = client.post(
        "/api/v1/users/admin/create-user",
        headers={"Authorization": f"Bearer {regular_user.access_token}"},
        json={"email": "test@test.com", "full_name": "Test"}
    )
    
    assert response.status_code == 403
```

## Referencias

- [Autenticación y Seguridad](./authentication.md)
- [Gestión de Usuarios](./user-management.md)
- [Roles y Permisos](./roles-permissions.md)
- [Endpoints de Autenticación](./auth-endpoints.md)
- [Sesiones y Tokens](./sessions-tokens.md)
