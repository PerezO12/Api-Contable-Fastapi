# Gestión de Usuarios

## Descripción General

El módulo de gestión de usuarios proporciona un sistema completo de administración de cuentas de usuario con funcionalidades CRUD, gestión de roles, y operaciones administrativas. Está diseñado para manejar desde operaciones básicas hasta administración avanzada de usuarios en el sistema contable.

## Características Principales

### 👤 Gestión Completa de Usuarios
- **CRUD Completo**: Crear, leer, actualizar y eliminar usuarios
- **Gestión de Perfiles**: Información personal y profesional
- **Estados de Usuario**: Activo, inactivo, bloqueado
- **Jerarquía**: Sistema de usuarios creados por administradores

### 🔧 Funcionalidades Administrativas
- **Creación por Admin**: Solo administradores pueden crear usuarios
- **Reset de Contraseñas**: Generación de contraseñas temporales
- **Bloqueo/Desbloqueo**: Control de acceso de usuarios
- **Estadísticas**: Métricas y reportes de usuarios

### 📊 Operaciones Masivas
- **Activación/Desactivación**: Múltiples usuarios simultáneamente
- **Filtrado Avanzado**: Búsqueda por múltiples criterios
- **Exportación**: Listados de usuarios en diferentes formatos

## Arquitectura del Servicio

### AuthService - Funciones de Gestión de Usuarios

```python
class AuthService:
    # Operaciones básicas CRUD
    async def create_user_by_admin(user_data, created_by_id) -> User
    async def get_user_by_id(user_id) -> User
    async def get_user_by_email(email) -> User
    async def update_user(user_id, user_data) -> User
    async def delete_user(user_id) -> bool
    
    # Gestión de contraseñas
    async def reset_user_password(user_id) -> str
    async def change_user_password(user_id, password_data) -> bool
    async def force_password_change(user_id, force) -> User
    
    # Estados de usuario
    async def toggle_user_active(user_id) -> User
    
    # Listado y estadísticas
    async def get_users_list(skip, limit, filters) -> List[UserResponse]
    async def get_user_stats() -> UserStatsResponse
```

## Schemas de Usuario

### Schemas Principales

#### UserRead - Información Completa
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

#### UserCreateByAdmin - Creación por Administrador
```python
class UserCreateByAdmin(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.SOLO_LECTURA
    notes: Optional[str] = Field(None, max_length=1000)
    temporary_password: str = Field(..., min_length=8, max_length=100)
    force_password_change: bool = True
```

#### UserResponse - Listado Simplificado
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

#### UserUpdate - Actualización de Datos
```python
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    notes: Optional[str] = Field(None, max_length=1000)
    force_password_change: Optional[bool] = None
```

### Schemas Especializados

#### UserStatsResponse - Estadísticas del Sistema
```python
class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    locked_users: int
    users_by_role: dict[str, int]
    recent_logins: int  # Últimas 24 horas
```

#### PasswordChangeRequest - Cambio de Contraseña
```python
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
```

#### UserSessionInfo - Información de Sesión
```python
class UserSessionInfo(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    permissions: dict
    last_login: Optional[datetime]
    session_expires_at: Optional[datetime]
    ip_address: Optional[str]
```

## Roles de Usuario

### ADMIN (Administrador)
**Permisos:**
- Gestión completa de usuarios
- Creación de nuevos usuarios
- Modificación de roles y permisos
- Acceso a todas las funcionalidades del sistema
- Configuración del sistema
- Auditoría y logs completos

**Responsabilidades:**
- Crear cuentas de usuario
- Asignar roles apropiados
- Monitorear actividad del sistema
- Gestionar configuraciones de seguridad

### CONTADOR
**Permisos:**
- Gestión completa de cuentas contables
- Creación y modificación de asientos
- Acceso a reportes financieros
- Importación/exportación de datos
- Consulta de información de usuarios (limitada)

**Restricciones:**
- No puede gestionar usuarios
- No puede cambiar configuraciones del sistema
- No puede acceder a logs de auditoría completos

### SOLO_LECTURA
**Permisos:**
- Consulta de reportes financieros básicos
- Visualización del plan de cuentas
- Consulta de asientos históricos
- Exportación básica de reportes

**Restricciones:**
- No puede crear ni modificar registros
- No puede acceder a funciones administrativas
- No puede ver información sensible de otros usuarios

## Operaciones de Usuario

### Creación de Usuario (Solo Admin)

```python
# Datos requeridos
user_data = {
    "email": "nuevo.usuario@empresa.com",
    "full_name": "Nuevo Usuario",
    "role": "CONTADOR",
    "temporary_password": "TempPass123!",
    "notes": "Usuario del departamento contable"
}

# El sistema automáticamente:
# 1. Valida la fortaleza de la contraseña temporal
# 2. Hashea la contraseña
# 3. Establece force_password_change = True
# 4. Registra quién creó el usuario
# 5. Establece timestamps de creación
```

### Actualización de Usuario

```python
# Campos actualizables
update_data = {
    "full_name": "Nombre Actualizado",
    "role": "SOLO_LECTURA",  # Solo admin puede cambiar roles
    "notes": "Información actualizada"
}

# Campos NO actualizables directamente:
# - email (requiere proceso especial)
# - hashed_password (usar endpoints específicos)
# - created_at, created_by_id
# - login_attempts, locked_until
```

### Reset de Contraseña

```python
# Proceso automático:
# 1. Genera contraseña temporal segura
# 2. Hashea la nueva contraseña
# 3. Establece force_password_change = True
# 4. Resetea contador de intentos fallidos
# 5. Desbloquea cuenta si estaba bloqueada
# 6. Actualiza timestamp de cambio de contraseña
```

## Estados y Transiciones

### Estado Activo
- **Condiciones**: `is_active = True`, no bloqueado
- **Capacidades**: Login normal, acceso según rol
- **Transiciones**: Puede ser desactivado por admin

### Estado Inactivo
- **Condiciones**: `is_active = False`
- **Restricciones**: No puede hacer login
- **Nota**: Sesiones existentes no se revocan automáticamente
- **Transiciones**: Puede ser reactivado por admin

### Estado Bloqueado
- **Condiciones**: `locked_until > now()`
- **Causa**: Múltiples intentos de login fallidos
- **Duración**: Configurable (default: 30 minutos)
- **Desbloqueo**: Automático por tiempo o manual por admin

### Cambio de Contraseña Forzado
- **Condiciones**: `force_password_change = True`
- **Escenarios**: Usuarios nuevos, reset de contraseña
- **Proceso**: Debe cambiar contraseña antes de acceso normal
- **Acceso**: Limitado hasta completar cambio

## Validaciones de Negocio

### Email
- Formato válido de email
- Único en el sistema
- No puede ser modificado directamente
- Case-insensitive para comparaciones

### Nombre Completo
- Longitud: 2-100 caracteres
- Se formatea automáticamente (Title Case)
- Requerido para todos los usuarios

### Rol
- Solo valores válidos del enum UserRole
- Solo admin puede asignar rol ADMIN
- Cambios auditados automáticamente

### Contraseñas Temporales
- Cumplen criterios de fortaleza
- Generadas automáticamente por el sistema
- Válidas hasta primer cambio
- No reutilizables

## Gestión de Sesiones de Usuario

### Sesiones Activas
```python
# Obtener sesiones activas de un usuario
sessions = await auth_service.get_user_active_sessions(user_id)

# Revocar sesión específica
await auth_service.revoke_user_session(token_jti)

# Revocar todas las sesiones de un usuario
count = await auth_service.revoke_all_user_sessions(user_id)
```

### Información de Sesión
- IP de origen
- User Agent del navegador
- Tiempo de creación
- Tiempo de expiración
- Estado actual (activa/expirada)

## Operaciones Masivas

### Activación/Desactivación
```python
# Procesar múltiples usuarios
user_ids = [uuid1, uuid2, uuid3]
for user_id in user_ids:
    await auth_service.toggle_user_active(user_id)
```

### Filtrado Avanzado
```python
# Filtros disponibles
filters = {
    "role": UserRole.CONTADOR,
    "is_active": True,
    "created_after": datetime(2025, 1, 1),
    "email_contains": "@empresa.com"
}

users = await auth_service.get_users_list(
    skip=0, 
    limit=50, 
    **filters
)
```

## Estadísticas de Usuarios

### Métricas Disponibles
- **Total de usuarios**: Conteo general
- **Usuarios activos**: `is_active = True`
- **Usuarios bloqueados**: `locked_until > now()`
- **Por rol**: Distribución de usuarios por rol
- **Logins recientes**: Actividad en últimas 24h

### Uso de Estadísticas
```python
stats = await auth_service.get_user_stats()
print(f"Total: {stats.total_users}")
print(f"Activos: {stats.active_users}")
print(f"Por rol: {stats.users_by_role}")
```

## Integración con Auditoría

### Eventos Auditados Automáticamente
- Creación de usuario
- Actualización de datos
- Cambios de rol
- Activación/desactivación
- Reset de contraseñas
- Bloqueos por seguridad

### Metadata de Auditoría
- Usuario que realizó la acción
- Timestamp preciso
- IP de origen
- Datos antes y después del cambio
- Contexto de la operación

## Consideraciones de Seguridad

### Protección de Datos
- Contraseñas nunca retornadas en APIs
- Información sensible limitada por rol
- Logs de acceso para operaciones críticas

### Validación de Permisos
- Verificación de rol en cada operación
- Solo admin puede crear/modificar usuarios
- Usuarios no pueden modificar su propio rol
- Validación de ownership para operaciones

### Prevención de Ataques
- Rate limiting en operaciones sensibles
- Validación robusta de entrada
- Sanitización automática de datos
- Protección contra inyección

## Casos de Uso Comunes

### Onboarding de Nuevo Empleado
1. Admin crea usuario con contraseña temporal
2. Usuario recibe credenciales por canal seguro
3. Primer login requiere cambio de contraseña
4. Usuario puede acceder según su rol asignado

### Rotación de Personal
1. Admin desactiva usuario saliente
2. Sesiones activas eventualmente expiran
3. Datos históricos se mantienen para auditoría
4. Usuario puede ser reactivado si regresa

### Escalamiento de Privilegios
1. Admin actualiza rol del usuario
2. Cambio auditado automáticamente
3. Nuevos permisos efectivos inmediatamente
4. Usuario notificado del cambio

### Incidente de Seguridad
1. Admin puede bloquear usuario inmediatamente
2. Todas las sesiones se revocan
3. Reset de contraseña obligatorio
4. Investigación con logs de auditoría

## Referencias

- [Autenticación y Seguridad](./authentication.md)
- [Roles y Permisos](./roles-permissions.md)
- [Endpoints de Usuarios](./user-endpoints.md)
- [Sesiones y Tokens](./sessions-tokens.md)
