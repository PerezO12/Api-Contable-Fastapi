# Sistema de Autenticación y Seguridad

## Descripción General

El sistema de autenticación del API Contable proporciona un marco de seguridad robusto y escalable basado en JWT (JSON Web Tokens) con múltiples niveles de protección. Implementa un sistema de roles granular, gestión de sesiones, y validaciones de seguridad avanzadas.

## Características Principales

### 🔐 Autenticación Segura
- **Hashing de contraseñas**: bcrypt con salt automático
- **Tokens JWT**: Access tokens y refresh tokens
- **Validación robusta**: Verificación de fortaleza de contraseñas
- **Sistema anti-brute force**: Bloqueo temporal por intentos fallidos

### 👥 Sistema de Roles
- **ADMIN**: Acceso completo al sistema
- **CONTADOR**: Gestión de operaciones contables
- **SOLO_LECTURA**: Solo consulta de información

### 🛡️ Protección y Seguridad
- **Sesiones activas**: Tracking y gestión de sesiones concurrentes
- **Expiración de tokens**: Tokens con tiempo de vida limitado
- **Revocación de sesiones**: Invalidación manual de tokens
- **Auditoría de accesos**: Registro de actividad de usuarios

## Arquitectura del Sistema

```
app/
├── models/
│   └── user.py              # Modelo User y UserSession
├── schemas/
│   └── user.py              # Schemas Pydantic para validación
├── services/
│   └── auth_service.py      # Lógica de negocio de autenticación
├── api/v1/
│   ├── auth.py             # Endpoints de autenticación
│   └── users.py            # Endpoints de gestión de usuarios
├── utils/
│   ├── security.py         # Utilidades de seguridad
│   ├── jwt_manager.py      # Gestión de tokens JWT
│   └── exceptions.py       # Excepciones personalizadas
└── api/
    └── deps.py             # Dependencias de FastAPI
```

## Flujo de Autenticación

### 1. Login del Usuario
```
Usuario → Email + Contraseña → Validación → Tokens JWT → Sesión Activa
```

### 2. Validación de Requests
```
Request → Token JWT → Validación → Permisos → Acceso/Denegado
```

### 3. Renovación de Tokens
```
Refresh Token → Validación → Nuevo Access Token → Sesión Renovada
```

### 4. Logout
```
Usuario → Logout → Revocación de Tokens → Cierre de Sesión
```

## Componentes Principales

### AuthService
Servicio central que maneja toda la lógica de autenticación:
- Autenticación de usuarios
- Gestión de contraseñas
- Creación y gestión de usuarios
- Administración de sesiones
- Estadísticas de usuarios

### JWTManager
Gestor especializado en tokens JWT:
- Creación de access y refresh tokens
- Validación y decodificación
- Extracción de claims
- Gestión de expiración

### Security Utils
Utilidades de seguridad:
- Validación de fortaleza de contraseñas
- Hashing seguro con bcrypt
- Generación de contraseñas temporales
- Validación de formatos

## Configuración de Seguridad

### Variables de Entorno
```env
# JWT Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin por defecto
DEFAULT_ADMIN_EMAIL=admin@contable.com
DEFAULT_ADMIN_PASSWORD=Admin123!
DEFAULT_ADMIN_FULL_NAME=Administrador del Sistema

# Security Settings
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
```

### Criterios de Contraseña
- **Longitud mínima**: 8 caracteres
- **Mayúsculas**: Al menos 1
- **Minúsculas**: Al menos 1
- **Números**: Al menos 1
- **Caracteres especiales**: Al menos 1

## Modelos de Datos

### Usuario (User)
```python
class User:
    id: UUID                           # Identificador único
    email: str                         # Email único
    full_name: str                     # Nombre completo
    hashed_password: str               # Contraseña hasheada
    role: UserRole                     # Rol del usuario
    is_active: bool                    # Estado activo/inactivo
    last_login: datetime               # Último acceso
    force_password_change: bool        # Forzar cambio de contraseña
    login_attempts: int                # Intentos de login fallidos
    locked_until: datetime             # Fecha hasta la cual está bloqueado
    created_by_id: UUID                # Quien creó el usuario
    created_at: datetime               # Fecha de creación
    updated_at: datetime               # Última actualización
```

### Sesión de Usuario (UserSession)
```python
class UserSession:
    id: UUID                          # Identificador único
    user_id: UUID                     # ID del usuario
    token_jti: str                    # JWT ID único
    expires_at: datetime              # Fecha de expiración
    ip_address: str                   # IP de origen
    user_agent: str                   # Agente de usuario
    created_at: datetime              # Fecha de creación
```

## Estados de Usuario

### Activo
- Puede autenticarse normalmente
- Acceso completo según su rol
- Puede cambiar su contraseña

### Inactivo
- No puede autenticarse
- Sesiones existentes se mantienen hasta expirar
- Admin puede reactivar

### Bloqueado Temporalmente
- Resultado de múltiples intentos fallidos
- No puede autenticarse hasta que expire el bloqueo
- Admin puede desbloquear manualmente

### Cambio de Contraseña Forzado
- Debe cambiar contraseña en próximo login
- Acceso limitado hasta cambiar contraseña
- Común en usuarios nuevos o reseteos

## Manejo de Errores

### Excepciones Personalizadas
- `AuthenticationError`: Fallos de autenticación
- `UserNotFoundError`: Usuario no encontrado
- `PasswordValidationError`: Contraseña no válida
- `UserValidationError`: Validación de datos de usuario
- `SessionError`: Errores de sesión
- `TokenError`: Errores de token JWT

### Códigos de Error HTTP
- `401 Unauthorized`: Credenciales inválidas
- `403 Forbidden`: Permisos insuficientes
- `423 Locked`: Cuenta bloqueada
- `422 Unprocessable Entity`: Datos de entrada inválidos
- `409 Conflict`: Usuario ya existe

## Seguridad Implementada

### Protección contra Ataques
- **Brute Force**: Bloqueo temporal por intentos fallidos
- **Session Hijacking**: JTI únicos en tokens
- **Token Replay**: Expiración corta de access tokens
- **Privilege Escalation**: Validación estricta de roles

### Mejores Prácticas
- Contraseñas nunca almacenadas en texto plano
- Tokens con claims mínimos necesarios
- Logs de auditoría para acciones críticas
- Validación de entrada en todos los endpoints

## Monitoreo y Auditoría

### Métricas Disponibles
- Total de usuarios por rol
- Usuarios activos vs inactivos
- Intentos de login fallidos
- Sesiones activas concurrentes
- Logins recientes (24h)

### Eventos Auditados
- Login exitoso/fallido
- Cambios de contraseña
- Creación/modificación de usuarios
- Activación/desactivación de cuentas
- Bloqueos por seguridad

## Integración con FastAPI

### Dependencias de Seguridad
```python
# Obtener usuario actual autenticado
current_user = Depends(get_current_active_user)

# Obtener usuario admin
admin_user = Depends(get_current_admin_user)

# Verificar permisos específicos
user_with_permission = Depends(get_user_with_permission("manage_accounts"))
```

### Decoradores de Endpoints
```python
@router.post("/protected-endpoint")
async def protected_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    # Endpoint protegido
    pass
```

## Extensibilidad

El sistema está diseñado para ser extensible:
- Nuevos roles pueden agregarse fácilmente
- Proveedores de autenticación externos (OAuth2, SAML)
- Autenticación multifactor (2FA)
- Políticas de contraseña personalizables
- Integración con sistemas de auditoría externos

## Referencias

- [Gestión de Usuarios](./user-management.md)
- [Roles y Permisos](./roles-permissions.md)
- [Sesiones y Tokens](./sessions-tokens.md)
- [Endpoints de Autenticación](./auth-endpoints.md)
