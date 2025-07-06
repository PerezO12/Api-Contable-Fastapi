import re
import secrets
import string
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Dict
from passlib.context import CryptContext

from app.core.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta
) -> str:
    """Crea un token JWT de acceso"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña"""
    return pwd_context.hash(password)


def verify_token(token: str) -> Union[str, None]:
    """Verifica un token JWT y devuelve el subject"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token_data = payload.get("sub")
        return token_data
    except jwt.PyJWTError:
        return None


def validate_password_strength(password: str) -> dict:
    """
    Valida la fortaleza de una contraseña
    Retorna un diccionario con el resultado de la validación
    """
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not any(c.isupper() for c in password):
        errors.append("La contraseña debe contener al menos una letra mayúscula")
    
    if not any(c.islower() for c in password):
        errors.append("La contraseña debe contener al menos una letra minúscula")
    
    if not any(c.isdigit() for c in password):
        errors.append("La contraseña debe contener al menos un número")
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("La contraseña debe contener al menos un carácter especial")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "strength": "débil" if len(errors) > 2 else "media" if len(errors) > 0 else "fuerte"
    }
