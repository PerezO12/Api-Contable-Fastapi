import re
from typing import Any, Dict, Optional
from pydantic import validator
from email_validator import validate_email, EmailNotValidError

from app.utils.security import validate_password_strength


def validate_email_format(email: str) -> str:
    """Valida el formato de un email"""
    try:
        # Usar email-validator para validación robusta
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError:
        raise ValueError("Formato de email inválido")


def validate_user_password(password: str) -> str:
    """Valida la fortaleza de una contraseña"""
    validation_result = validate_password_strength(password)
    
    if not validation_result["is_valid"]:
        error_message = "Contraseña no cumple los requisitos: " + "; ".join(validation_result["errors"])
        raise ValueError(error_message)
    
    return password


def validate_full_name(name: str) -> str:
    """Valida el nombre completo del usuario"""
    if not name or len(name.strip()) < 2:
        raise ValueError("El nombre completo debe tener al menos 2 caracteres")
    
    if len(name) > 100:
        raise ValueError("El nombre completo no puede exceder 100 caracteres")
    
    # Permitir solo letras, espacios, guiones y apostrofes
    if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", name):
        raise ValueError("El nombre solo puede contener letras, espacios, guiones y apostrofes")
    
    return name.strip().title()  # Capitalizar nombres


def validate_user_role(role: str) -> str:
    """Valida que el rol sea uno de los permitidos"""
    from app.models.user import UserRole
    
    valid_roles = [r.value for r in UserRole]
    if role not in valid_roles:
        raise ValueError(f"Rol inválido. Roles válidos: {', '.join(valid_roles)}")
    
    return role


def validate_notes(notes: Optional[str]) -> Optional[str]:
    """Valida las notas del usuario"""
    if notes is None:
        return None
    
    if len(notes) > 500:
        raise ValueError("Las notas no pueden exceder 500 caracteres")
    
    return notes.strip() if notes.strip() else None


class UserValidators:
    """Clase con validadores para modelos de usuario"""
    
    @classmethod
    def email_validator(cls, v: str) -> str:
        return validate_email_format(v)
    
    @classmethod
    def password_validator(cls, v: str) -> str:
        return validate_user_password(v)
    
    @classmethod
    def full_name_validator(cls, v: str) -> str:
        return validate_full_name(v)
    
    @classmethod
    def role_validator(cls, v: str) -> str:
        return validate_user_role(v)
    
    @classmethod
    def notes_validator(cls, v: Optional[str]) -> Optional[str]:
        return validate_notes(v)


def validate_pagination_params(skip: int, limit: int) -> Dict[str, int]:
    """Valida parámetros de paginación"""
    if skip < 0:
        raise ValueError("El parámetro 'skip' debe ser mayor o igual a 0")
    
    if limit < 1:
        raise ValueError("El parámetro 'limit' debe ser mayor a 0")
    
    if limit > 1000:
        raise ValueError("El parámetro 'limit' no puede ser mayor a 1000")
    
    return {"skip": skip, "limit": limit}


def validate_uuid_format(uuid_str: str) -> str:
    """Valida el formato de un UUID"""
    import uuid
    
    try:
        uuid.UUID(uuid_str)
        return uuid_str
    except ValueError:
        raise ValueError("Formato de UUID inválido")
