"""
Utilidades para manejo de tokens JWT y autenticación
Siguiendo las mejores prácticas de seguridad
"""
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Union

from fastapi import HTTPException, status
from app.core.settings import settings


class JWTManager:
    """Gestor de tokens JWT para el sistema de autenticación"""
    
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or settings.SECRET_KEY
        self.algorithm = algorithm
        self.access_token_expire_minutes = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30)
        self.refresh_token_expire_days = getattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS', 7)
    
    def create_access_token(
        self, 
        user_id: Union[str, uuid.UUID], 
        email: str,
        role: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Crea un token de acceso JWT"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "type": "access",
            "iat": now,
            "exp": expire,
            "jti": str(uuid.uuid4())  # JWT ID único
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self, 
        user_id: Union[str, uuid.UUID],
        email: str
    ) -> str:
        """Crea un token de actualización JWT"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "refresh",
            "iat": now,
            "exp": expire,
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decodifica y valida un token JWT"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verifica un token de acceso y retorna el payload"""
        payload = self.decode_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo de token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verifica un token de actualización y retorna el payload"""
        payload = self.decode_token(token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo de token inválido para actualización",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    def get_token_jti(self, token: str) -> str:
        """Extrae el JTI (JWT ID) de un token"""
        payload = self.decode_token(token)
        return payload.get("jti", "")
    
    def is_token_expired(self, token: str) -> bool:
        """Verifica si un token ha expirado sin lanzar excepción"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # No verificar expiración automáticamente
            )
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc)
            return True
        except jwt.InvalidTokenError:
            return True


# Instancia global del gestor JWT
jwt_manager = JWTManager()


def create_token_pair(user_id: Union[str, uuid.UUID], email: str, role: str) -> Dict[str, str]:
    """Crea un par de tokens (acceso y actualización)"""
    access_token = jwt_manager.create_access_token(user_id, email, role)
    refresh_token = jwt_manager.create_refresh_token(user_id, email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def extract_token_from_header(authorization: str) -> str:
    """Extrae el token del header Authorization"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header de autorización faltante",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Esquema de autorización inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de autorización inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_token_permissions(payload: Dict[str, Any], required_permissions: list) -> bool:
    """Valida si un token tiene los permisos requeridos"""
    user_role = payload.get("role", "")
    
    # Mapeo básico de permisos por rol
    role_permissions = {
        "admin": ["*"],  # Todos los permisos
        "contador": [
            "accounts:read", "accounts:write", "accounts:delete",
            "entries:read", "entries:write", "entries:delete", 
            "reports:read", "reports:export"
        ],
        "solo_lectura": [
            "accounts:read", "entries:read", "reports:read"
        ]
    }
    
    user_permissions = role_permissions.get(user_role, [])
    
    # Admin tiene todos los permisos
    if "*" in user_permissions:
        return True
    
    # Verificar permisos específicos
    return all(perm in user_permissions for perm in required_permissions)
