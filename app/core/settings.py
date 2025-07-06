"""
Configuración unificada y centralizada de la aplicación

Este módulo implementa un sistema de configuración por capas:
1. Configuración base con valores por defecto
2. Configuración específica por ambiente
3. Variables de entorno (highest priority)
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache

from pydantic import (
    AnyHttpUrl, 
    EmailStr, 
    field_validator, 
    computed_field,
    model_validator
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Configuración base compartida entre todos los ambientes"""
    
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignorar variables extra del .env
    )
    
    # Información básica del proyecto
    PROJECT_NAME: str = "Sistema Contable API"
    APP_NAME: str = "API Contable"
    PROJECT_DESCRIPTION: str = "API para sistema de contabilidad con FastAPI y SQLAlchemy"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Configuración de entorno
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Configuración de base de datos
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "accounting_system"
    
    # Configuración JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Configuración CORS
    BACKEND_CORS_ORIGINS: List[str] = []
    
    # Configuración de seguridad
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Configuración de paginación
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Configuración de email (opcional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None  # Cambiado de EmailStr a str para permitir vacío
    EMAILS_FROM_NAME: Optional[str] = "Sistema Contable"
    
    # Usuario administrador por defecto
    DEFAULT_ADMIN_EMAIL: str = "admin@contable.com"  # Cambiado de EmailStr a str
    DEFAULT_ADMIN_PASSWORD: str = "Admin123!"
    DEFAULT_ADMIN_FULL_NAME: str = "Administrador Sistema"
    
    # Configuración de cuentas por defecto
    DEFAULT_ICMS_ACCOUNT_CODE: str = "4.1.1.01"
    DEFAULT_ICMS_ACCOUNT_NAME: str = "ICMS sobre Vendas"
    DEFAULT_IPI_ACCOUNT_CODE: str = "4.1.1.02"
    DEFAULT_IPI_ACCOUNT_NAME: str = "IPI sobre Vendas"
    DEFAULT_PIS_ACCOUNT_CODE: str = "4.1.1.03"
    DEFAULT_PIS_ACCOUNT_NAME: str = "PIS sobre Vendas"
    DEFAULT_COFINS_ACCOUNT_CODE: str = "4.1.1.04"
    DEFAULT_COFINS_ACCOUNT_NAME: str = "COFINS sobre Vendas"
    
    # Configuración de IA (desactivada por defecto)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7
    HUGGINGFACE_API_TOKEN: str = ""
    TOGETHER_API_KEY: str = ""
    TOGETHER_MODEL: str = "deepseek-ai/DeepSeek-V3"
    TOGETHER_MAX_TOKENS: str = "1000"
    TOGETHER_TEMPERATURE: str = "0.7"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            import ast
            try:
                return ast.literal_eval(v)
            except ValueError:
                return [v]
        return []
    
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Construir URL de base de datos desde componentes."""
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @computed_field
    @property
    def ASYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        """Construir URL de base de datos asíncrona desde componentes."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @model_validator(mode='after')
    def validate_environment_specific_settings(self):
        """Validar configuraciones específicas del ambiente."""
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == secrets.token_urlsafe(32):
                raise ValueError("SECRET_KEY debe ser configurada en producción")
            if self.DEBUG:
                self.DEBUG = False  # Forzar DEBUG=False en producción
        return self


class DevelopmentConfig(BaseConfig):
    """Configuración para desarrollo"""
    
    model_config = SettingsConfigDict(
        env_file=[".env.development", ".env.local"],  # .env.local tiene prioridad
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # CORS más permisivo para desarrollo
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080"
    ]


class ProductionConfig(BaseConfig):
    """Configuración para producción"""
    
    model_config = SettingsConfigDict(
        env_file=".env.production",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Configuración más restrictiva para producción
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4  # 4 horas en producción
    RATE_LIMIT_PER_MINUTE: int = 30  # Más restrictivo
    
    # CORS específico para producción
    BACKEND_CORS_ORIGINS: List[str] = []  # Debe ser configurado vía variables de entorno


class TestingConfig(BaseConfig):
    """Configuración para testing"""
    
    model_config = SettingsConfigDict(
        env_file=".env.testing",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    
    # Base de datos específica para testing
    DB_NAME: str = "accounting_system_test"
    
    # Tokens de corta duración para testing
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    
    # Configuración de email desactivada para testing
    SMTP_HOST: Optional[str] = None


# Mapeo de configuraciones por ambiente
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


@lru_cache()
def get_settings() -> BaseConfig:
    """
    Obtener configuración basada en la variable de entorno ENVIRONMENT.
    
    Usa cache para evitar recrear la configuración en cada llamada.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()


# Instancia global de configuración
settings = get_settings()
