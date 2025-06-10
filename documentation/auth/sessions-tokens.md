# Sesiones y Tokens JWT

## Descripción General

El sistema de sesiones y tokens del API Contable implementa un mecanismo robusto de autenticación basado en JWT (JSON Web Tokens) con gestión avanzada de sesiones, que incluye tokens de acceso y actualización, tracking de sesiones activas, y capacidades de revocación granular.

## Arquitectura de Tokens

### Tipos de Tokens

#### Access Token (Token de Acceso)
- **Propósito**: Autenticación de requests individuales
- **Duración**: 30 minutos (configurable)
- **Uso**: Header Authorization en cada request
- **Contenido**: Información mínima del usuario y permisos

#### Refresh Token (Token de Actualización)
- **Propósito**: Renovación de access tokens
- **Duración**: 7 días (configurable)
- **Uso**: Endpoint específico de renovación
- **Seguridad**: Almacenado de forma segura, una sola vez

### Estructura de Tokens

#### Access Token Claims
```json
{
  "sub": "usuario-uuid-aqui",           # User ID
  "email": "usuario@empresa.com",       # Email del usuario
  "role": "CONTADOR",                   # Rol del usuario
  "type": "access",                     # Tipo de token
  "iat": 1709640000,                    # Issued at (timestamp)
  "exp": 1709641800,                    # Expiration (timestamp)
  "jti": "token-uuid-unico"             # JWT ID único
}
```

#### Refresh Token Claims
```json
{
  "sub": "usuario-uuid-aqui",           # User ID
  "email": "usuario@empresa.com",       # Email del usuario
  "type": "refresh",                    # Tipo de token
  "iat": 1709640000,                    # Issued at
  "exp": 1710244800,                    # Expiration (7 días)
  "jti": "refresh-token-uuid-unico"     # JWT ID único
}
```

## Gestión de Sesiones

### Modelo UserSession

```python
class UserSession(Base):
    """Modelo para tracking de sesiones activas"""
    id: UUID                          # Identificador único
    user_id: UUID                     # ID del usuario
    token_jti: str                    # JWT ID del access token
    expires_at: datetime              # Fecha de expiración
    ip_address: str                   # IP de origen
    user_agent: str                   # Agente de usuario
    created_at: datetime              # Fecha de creación
    
    @property
    def is_expired(self) -> bool:
        """Verifica si la sesión ha expirado"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def time_remaining(self) -> timedelta:
        """Tiempo restante de la sesión"""
        return self.expires_at - datetime.now(timezone.utc)
```

### Ciclo de Vida de Sesiones

#### 1. Creación de Sesión
```python
# Durante login exitoso
async def create_session(user_id, token_jti, ip_address, user_agent):
    session = UserSession(
        user_id=user_id,
        token_jti=token_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(session)
    await db.commit()
```

#### 2. Validación de Sesión
```python
# En cada request autenticado
async def validate_session(token_jti):
    session = await get_session_by_jti(token_jti)
    
    if not session:
        raise TokenError("Sesión no encontrada")
    
    if session.is_expired:
        await delete_session(session)
        raise TokenError("Sesión expirada")
    
    return session
```

#### 3. Renovación de Sesión
```python
# Al usar refresh token
async def refresh_session(refresh_token):
    # Validar refresh token
    payload = decode_token(refresh_token)
    
    # Crear nuevo access token
    new_access_token = create_access_token(
        user_id=payload["sub"],
        email=payload["email"],
        role=payload["role"]
    )
    
    # Actualizar sesión existente
    await update_session_token(old_jti, new_jti)
```

#### 4. Revocación de Sesión
```python
# Logout o revocación manual
async def revoke_session(token_jti):
    session = await get_session_by_jti(token_jti)
    if session:
        await delete_session(session)
        return True
    return False
```

## JWTManager - Gestor de Tokens

### Clase Principal
```python
class JWTManager:
    """Gestor de tokens JWT para el sistema de autenticación"""
    
    def __init__(self, secret_key=None, algorithm="HS256"):
        self.secret_key = secret_key or settings.SECRET_KEY
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def create_access_token(self, user_id, email, role) -> str:
        """Crea un token de acceso JWT"""
        
    def create_refresh_token(self, user_id, email) -> str:
        """Crea un token de actualización JWT"""
        
    def decode_token(self, token) -> Dict[str, Any]:
        """Decodifica y valida un token JWT"""
        
    def extract_token_from_header(self, authorization_header) -> str:
        """Extrae el token del header Authorization"""
        
    def verify_token_signature(self, token) -> bool:
        """Verifica la firma del token"""
```

### Funciones Principales

#### Creación de Tokens
```python
def create_token_pair(user_id: UUID, email: str, role: str) -> dict:
    """Crea un par de tokens (access + refresh)"""
    jwt_manager = JWTManager()
    
    access_token = jwt_manager.create_access_token(
        user_id=user_id,
        email=email,
        role=role
    )
    
    refresh_token = jwt_manager.create_refresh_token(
        user_id=user_id,
        email=email
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # 30 minutos en segundos
    }
```

#### Validación de Tokens
```python
def validate_access_token(token: str) -> TokenData:
    """Valida un access token y retorna los datos"""
    jwt_manager = JWTManager()
    
    try:
        payload = jwt_manager.decode_token(token)
        
        # Verificar tipo de token
        if payload.get("type") != "access":
            raise TokenError("Token type invalid")
        
        # Verificar expiración
        exp = payload.get("exp")
        if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise TokenError("Token expired")
        
        return TokenData(
            user_id=UUID(payload["sub"]),
            email=payload["email"],
            role=UserRole(payload["role"]),
            jti=payload["jti"]
        )
        
    except jwt.PyJWTError as e:
        raise TokenError(f"Token validation failed: {str(e)}")
```

## Flujos de Autenticación

### Flujo de Login
```
1. Usuario envía credenciales → POST /auth/login
2. Sistema valida email/contraseña
3. Si válido: crear tokens (access + refresh)
4. Crear sesión en base de datos
5. Retornar tokens al cliente
6. Cliente almacena tokens (secure storage)
```

### Flujo de Request Autenticado
```
1. Cliente incluye access token → Authorization: Bearer <token>
2. Sistema extrae y valida token
3. Verifica sesión activa en base de datos
4. Si válido: procesar request
5. Si inválido: retornar 401 Unauthorized
```

### Flujo de Renovación
```
1. Access token expira/próximo a expirar
2. Cliente envía refresh token → POST /auth/refresh
3. Sistema valida refresh token
4. Si válido: crear nuevo access token
5. Actualizar sesión en base de datos
6. Retornar nuevo access token
```

### Flujo de Logout
```
1. Cliente solicita logout → POST /auth/logout
2. Sistema extrae token del header
3. Revoca sesión en base de datos
4. Token queda invalidado
5. Cliente elimina tokens almacenados
```

## Configuración de Seguridad

### Variables de Entorno
```env
# JWT Configuration
SECRET_KEY=your-super-secret-key-here-256-bits
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Session Management
MAX_CONCURRENT_SESSIONS=5
SESSION_CLEANUP_INTERVAL_HOURS=24
ENFORCE_SINGLE_SESSION=false
```

### Configuración en settings.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Session Settings
    MAX_CONCURRENT_SESSIONS: int = 5
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24
    ENFORCE_SINGLE_SESSION: bool = False
    
    class Config:
        env_file = ".env"
```

## Seguridad de Tokens

### Protecciones Implementadas

#### Contra Token Replay
- **JTI únicos**: Cada token tiene un identificador único
- **Tracking de sesiones**: Sesiones activas registradas en BD
- **Revocación granular**: Invalidación de tokens específicos

#### Contra Token Hijacking
- **IP Tracking**: Registro de IP de origen
- **User Agent**: Validación de navegador/dispositivo
- **Tiempo de vida corto**: Access tokens expiran rápidamente

#### Contra Brute Force
- **Rate limiting**: Límite de requests por IP
- **Bloqueo temporal**: Cuenta bloqueada tras fallos
- **Logging**: Registro de intentos fallidos

### Validaciones de Seguridad
```python
async def validate_token_security(token_data: TokenData, request: Request):
    """Validaciones adicionales de seguridad"""
    
    # Obtener sesión activa
    session = await get_session_by_jti(token_data.jti)
    if not session:
        raise TokenError("Session not found")
    
    # Validar IP (opcional, configurable)
    if settings.ENFORCE_IP_VALIDATION:
        client_ip = request.client.host
        if session.ip_address != client_ip:
            logger.warning(f"IP mismatch for session {token_data.jti}")
            # Opcional: revocar sesión por seguridad
    
    # Validar User Agent (opcional)
    if settings.ENFORCE_USER_AGENT_VALIDATION:
        client_user_agent = request.headers.get("User-Agent")
        if session.user_agent != client_user_agent:
            logger.warning(f"User Agent mismatch for session {token_data.jti}")
    
    return True
```

## Gestión de Sesiones Múltiples

### Sesiones Concurrentes
```python
async def manage_concurrent_sessions(user_id: UUID, new_session: UserSession):
    """Gestiona sesiones concurrentes del usuario"""
    
    # Obtener sesiones activas del usuario
    active_sessions = await get_user_active_sessions(user_id)
    
    # Si excede el límite, eliminar las más antiguas
    if len(active_sessions) >= settings.MAX_CONCURRENT_SESSIONS:
        sessions_to_remove = active_sessions[:-settings.MAX_CONCURRENT_SESSIONS + 1]
        for session in sessions_to_remove:
            await revoke_session(session.token_jti)
    
    # Agregar nueva sesión
    await create_session(new_session)
```

### Información de Sesiones para Usuario
```python
@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_my_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene las sesiones activas del usuario actual"""
    sessions = await auth_service.get_user_active_sessions(current_user.id)
    
    return [
        UserSessionResponse(
            session_id=session.token_jti,
            user_id=session.user_id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_current=session.token_jti == current_token_jti
        )
        for session in sessions
    ]
```

## Limpieza y Mantenimiento

### Limpieza Automática de Sesiones
```python
async def cleanup_expired_sessions():
    """Limpia sesiones expiradas automáticamente"""
    
    cutoff_time = datetime.now(timezone.utc)
    
    # Eliminar sesiones expiradas
    result = await db.execute(
        delete(UserSession).where(UserSession.expires_at < cutoff_time)
    )
    
    deleted_count = result.rowcount
    logger.info(f"Cleaned up {deleted_count} expired sessions")
    
    return deleted_count

# Programar limpieza periódica (en startup de la aplicación)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    cleanup_expired_sessions,
    'interval',
    hours=settings.SESSION_CLEANUP_INTERVAL_HOURS,
    id='cleanup_sessions'
)
```

### Estadísticas de Sesiones
```python
async def get_session_statistics():
    """Obtiene estadísticas de sesiones del sistema"""
    
    total_sessions = await db.scalar(select(func.count(UserSession.id)))
    
    active_sessions = await db.scalar(
        select(func.count(UserSession.id))
        .where(UserSession.expires_at > datetime.now(timezone.utc))
    )
    
    expired_sessions = total_sessions - active_sessions
    
    # Sesiones por usuario
    sessions_by_user = await db.execute(
        select(UserSession.user_id, func.count(UserSession.id))
        .group_by(UserSession.user_id)
        .where(UserSession.expires_at > datetime.now(timezone.utc))
    )
    
    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "expired_sessions": expired_sessions,
        "sessions_by_user": dict(sessions_by_user.fetchall())
    }
```

## Schemas de Respuesta

### Token Response
```python
class Token(BaseModel):
    """Schema para respuesta de tokens"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
```

### Session Info Response
```python
class UserSessionResponse(BaseModel):
    """Schema para información de sesión"""
    session_id: str
    user_id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    expires_at: datetime
    is_current: bool = False
```

### Token Data (Internal)
```python
class TokenData(BaseModel):
    """Schema para datos internos del token"""
    user_id: UUID
    email: str
    role: UserRole
    jti: str
```

## Casos de Uso Avanzados

### Revocación de Sesión Específica
```python
@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Revoca una sesión específica del usuario"""
    
    # Verificar que la sesión pertenece al usuario
    session = await get_session_by_jti(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Revocar sesión
    await auth_service.revoke_user_session(session_id)
    
    return {"message": "Session revoked successfully"}
```

### Logout de Todas las Sesiones
```python
@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """Cierra todas las sesiones del usuario"""
    
    revoked_count = await auth_service.revoke_all_user_sessions(current_user.id)
    
    return {
        "message": f"All sessions logged out successfully",
        "revoked_sessions": revoked_count
    }
```

### Forzar Logout por Admin
```python
@router.post("/admin/force-logout/{user_id}")
async def force_logout_user(
    user_id: UUID,
    admin_user: User = Depends(get_current_admin_user)
):
    """Fuerza el logout de todas las sesiones de un usuario"""
    
    revoked_count = await auth_service.revoke_all_user_sessions(user_id)
    
    # Auditar acción
    await audit_service.log_admin_action(
        admin_user.id,
        "FORCE_LOGOUT",
        {"target_user_id": str(user_id), "sessions_revoked": revoked_count}
    )
    
    return {
        "message": f"User {user_id} logged out successfully",
        "revoked_sessions": revoked_count
    }
```

## Troubleshooting Común

### Token Expirado
```
Error: "Token expired"
Solución: Usar refresh token para obtener nuevo access token
```

### Sesión No Encontrada
```
Error: "Session not found"
Causa: Sesión revocada o limpiada
Solución: Login nuevamente
```

### IP Mismatch
```
Error: "IP address validation failed"
Causa: Usuario cambió de red/IP
Solución: Reautenticación o deshabilitar validación de IP
```

### Demasiadas Sesiones
```
Error: "Maximum concurrent sessions exceeded"
Solución: Revocar sesiones antiguas o aumentar límite
```

## Referencias

- [Autenticación y Seguridad](./authentication.md)
- [Gestión de Usuarios](./user-management.md)
- [Endpoints de Autenticación](./auth-endpoints.md)
- [Roles y Permisos](./roles-permissions.md)
