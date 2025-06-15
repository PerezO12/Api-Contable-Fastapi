# Endpoints de Gestión de Usuarios - ACTUALIZADO

## Descripción General

Los endpoints de gestión de usuarios proporcionan funcionalidades completas para la administración de cuentas de usuario, incluyendo operaciones CRUD, gestión de contraseñas, estadísticas y operaciones administrativas. Estos endpoints están protegidos según el sistema de roles implementado.

## Base URL

```
Base URL: /api/v1/users
```

## Autenticación

Todos los endpoints requieren autenticación mediante Bearer Token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints Disponibles

### 👤 GET /me
Obtiene información del usuario actual autenticado.

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
  "first_name": "Juan",
  "last_name": "Pérez",
  "role": "CONTADOR",
  "is_active": true,
  "must_change_password": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### ➕ POST /admin/create-user
Permite a un administrador crear un nuevo usuario con contraseña temporal.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/users/admin/create-user
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "email": "nuevo@empresa.com",
  "first_name": "María",
  "last_name": "González",
  "role": "CONTADOR"
}
```

#### Response Exitosa (200)
```json
{
  "id": "456e7890-e89b-12d3-a456-426614174000",
  "email": "nuevo@empresa.com",
  "first_name": "María",
  "last_name": "González",
  "role": "CONTADOR",
  "is_active": true,
  "must_change_password": true,
  "created_at": "2024-06-15T14:30:00Z",
  "updated_at": "2024-06-15T14:30:00Z"
}
```

---

### 📊 GET /admin/stats
Obtiene estadísticas de usuarios del sistema.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
GET /api/v1/users/admin/stats
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "total_users": 15,
  "active_users": 12,
  "inactive_users": 3,
  "users_by_role": {
    "ADMIN": 2,
    "CONTADOR": 8,
    "SOLO_LECTURA": 5
  },
  "users_requiring_password_change": 3,
  "recent_logins": 8
}
```

---

### 👥 GET /admin/list
Lista todos los usuarios del sistema con paginación y filtros.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Parámetros de Query
- `skip`: int = 0 - Número de registros a omitir
- `limit`: int = 100 - Máximo número de registros a retornar
- `role`: Optional[UserRole] - Filtrar por rol específico

#### Request
```http
GET /api/v1/users/admin/list?skip=0&limit=50&role=CONTADOR
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "contador1@empresa.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "CONTADOR",
    "is_active": true,
    "must_change_password": false,
    "created_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-06-15T09:15:00Z"
  }
]
```

---

### 🔄 PUT /{user_id}/toggle-active
Activa o desactiva un usuario específico.

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
  "first_name": "Juan",
  "last_name": "Pérez",
  "role": "CONTADOR",
  "is_active": false,
  "must_change_password": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-06-15T14:45:00Z"
}
```

---

### 🔑 PUT /{user_id}/reset-password
Resetea la contraseña de un usuario y genera una temporal.

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
  "temporary_password": "TempPass123!"
}
```

---

### 🔒 PUT /{user_id}/force-password-change
Fuerza a un usuario a cambiar su contraseña en el próximo login.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Parámetros de Query
- `force`: bool = true - Si forzar el cambio de contraseña

#### Request
```http
PUT /api/v1/users/123e4567-e89b-12d3-a456-426614174000/force-password-change?force=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "usuario@empresa.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "role": "CONTADOR",
  "is_active": true,
  "must_change_password": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-06-15T14:45:00Z"
}
```

---

### 🔑 POST /change-password
Permite al usuario cambiar su propia contraseña.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
POST /api/v1/users/change-password
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "current_password": "password_actual",
  "new_password": "nueva_password123!",
  "confirm_password": "nueva_password123!"
}
```

#### Response Exitosa (200)
```json
{
  "message": "Contraseña cambiada exitosamente"
}
```

#### Códigos de Error
- **400 Bad Request**: Las contraseñas no coinciden
- **401 Unauthorized**: Contraseña actual incorrecta
- **422 Unprocessable Entity**: Validación de contraseña falló

---

### 📋 GET /roles
Obtiene la lista de roles disponibles en el sistema.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
GET /api/v1/users/roles
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "value": "ADMIN",
    "label": "Administrador",
    "description": "Acceso completo al sistema"
  },
  {
    "value": "CONTADOR",
    "label": "Contador",
    "description": "Puede crear asientos y acceder a reportes"
  },
  {
    "value": "SOLO_LECTURA",
    "label": "Solo Lectura",
    "description": "Solo puede consultar reportes y datos"
  }
]
```

---

## Flujos de Integración

### Creación de Usuario Completa
```javascript
// 1. Crear usuario (solo admin)
const createResponse = await fetch('/api/v1/users/admin/create-user', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'nuevo@empresa.com',
    first_name: 'María',
    last_name: 'González',
    role: 'CONTADOR'
  })
});

// 2. El usuario cambia su contraseña temporal
const changePasswordResponse = await fetch('/api/v1/users/change-password', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    current_password: 'temporal_password',
    new_password: 'nueva_password123!',
    confirm_password: 'nueva_password123!'
  })
});
```

### Gestión de Usuario por Admin
```javascript
// Obtener estadísticas
const stats = await fetch('/api/v1/users/admin/stats', {
  headers: { 'Authorization': `Bearer ${adminToken}` }
});

// Listar usuarios filtrados
const users = await fetch('/api/v1/users/admin/list?role=CONTADOR&limit=20', {
  headers: { 'Authorization': `Bearer ${adminToken}` }
});

// Desactivar usuario
const toggleResponse = await fetch(`/api/v1/users/${userId}/toggle-active`, {
  method: 'PUT',
  headers: { 'Authorization': `Bearer ${adminToken}` }
});
```

## Validaciones y Reglas de Negocio

### Roles de Usuario
- **ADMIN**: Acceso completo al sistema, puede gestionar usuarios
- **CONTADOR**: Puede crear asientos contables y generar reportes
- **SOLO_LECTURA**: Solo puede consultar reportes existentes

### Contraseñas
- Mínimo 8 caracteres
- Debe contener al menos una mayúscula, minúscula y número
- Caracteres especiales recomendados pero no obligatorios

### Validaciones de Usuario
- Email debe ser único en el sistema
- Nombres no pueden estar vacíos
- Solo admins pueden crear/modificar otros usuarios
- Un usuario puede cambiar su propia contraseña

## Códigos de Error Comunes

### 400 Bad Request
- Datos de entrada inválidos
- Contraseñas no coinciden

### 401 Unauthorized
- Token de autenticación inválido o expirado
- Contraseña actual incorrecta

### 403 Forbidden
- Permisos insuficientes para la operación
- Usuario no es administrador

### 404 Not Found
- Usuario no encontrado
- Endpoint no existe

### 409 Conflict
- Email ya existe en el sistema
- Usuario ya está en el estado solicitado

### 422 Unprocessable Entity
- Validación de contraseña falló
- Formato de email inválido
- Rol no válido

## Testing de Endpoints

### Casos de Prueba Recomendados
1. **Autenticación**: Probar todos los endpoints sin token
2. **Autorización**: Probar endpoints de admin con usuario normal
3. **Validaciones**: Probar con datos inválidos
4. **Flujos completos**: Crear usuario → cambiar contraseña → usar sistema

### Herramientas de Testing
- **Postman**: Colección de endpoints con autenticación
- **pytest**: Tests automatizados de API
- **curl**: Comandos de línea para pruebas rápidas

## Referencias

- [Esquemas de Usuario](../schemas/user-schemas.md)
- [Autenticación JWT](./auth-endpoints.md)
- [Sistema de Roles](../auth/roles-permissions.md)
- [Configuración de Seguridad](../security/security-config.md)
