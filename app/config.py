import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # Token Configuration - 8 hours by default as per specification
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days for refresh tokens
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)    # Project Information
    PROJECT_NAME: str = "Sistema Contable API"
    APP_NAME: str = "API Contable"  # From .env file
    PROJECT_DESCRIPTION: str = "API para sistema de contabilidad con FastAPI y SQLAlchemy"
    VERSION: str = "1.0.0"
      # Database Configuration
    DB_HOST: str = "localhost"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "accounting_system"
    DB_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"

    # Email Settings for user notifications
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = "Sistema Contable"

    # Security Configuration
    ALGORITHM: str = "HS256"
    
    # Rate Limiting (as per best practices)
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100    # Security settings as per specification
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30
    
    # Default Admin User Configuration (created on first startup)
    DEFAULT_ADMIN_EMAIL: EmailStr = "admin@contable.com"
    DEFAULT_ADMIN_PASSWORD: str = "Admin123!"
    DEFAULT_ADMIN_FULL_NAME: str = "Administrador Sistema"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
