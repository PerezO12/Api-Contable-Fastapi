import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # Token Configuration - 8 hours by default as per specification
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days for refresh tokens
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = []

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
    
    # Project Information
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
    
    # Default Tax Accounts Configuration
    DEFAULT_ICMS_ACCOUNT_CODE: str = "4.1.1.01"
    DEFAULT_ICMS_ACCOUNT_NAME: str = "ICMS sobre Vendas"
    DEFAULT_IPI_ACCOUNT_CODE: str = "4.1.1.02"
    DEFAULT_IPI_ACCOUNT_NAME: str = "IPI sobre Vendas"
    DEFAULT_PIS_ACCOUNT_CODE: str = "4.1.1.03"
    DEFAULT_PIS_ACCOUNT_NAME: str = "PIS sobre Vendas"
    DEFAULT_COFINS_ACCOUNT_CODE: str = "4.1.1.04"
    DEFAULT_COFINS_ACCOUNT_NAME: str = "COFINS sobre Vendas"
    
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Build database URL from components."""
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

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
    MAX_PAGE_SIZE: int = 100
    
    # Security settings as per specification
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30
    
    # Default Admin User Configuration (created on first startup)
    DEFAULT_ADMIN_EMAIL: EmailStr = "admin@contable.com"
    DEFAULT_ADMIN_PASSWORD: str = "Admin123!"
    DEFAULT_ADMIN_FULL_NAME: str = "Administrador Sistema"

    # Environment
    ENVIRONMENT: str = "development"
    
    # OpenAI Configuration - DESACTIVADO TEMPORALMENTE
    OPENAI_API_KEY: str = ""  # Desactivado
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # No se usa
    OPENAI_MAX_TOKENS: int = 1000  # No se usa
    OPENAI_TEMPERATURE: float = 0.7  # No se usa
    DEBUG: bool = True

    # AI Chat Configuration - DESACTIVADO TEMPORALMENTE
    HUGGINGFACE_API_TOKEN: str = ""  # Desactivado
    
    # Together AI Configuration - DESACTIVADO TEMPORALMENTE
    TOGETHER_API_KEY: str = ""  # Desactivado
    TOGETHER_MODEL: str = "deepseek-ai/DeepSeek-V3"  # No se usa
    TOGETHER_MAX_TOKENS: str = "1000"  # No se usa
    TOGETHER_TEMPERATURE: str = "0.7"  # No se usa


settings = Settings()
