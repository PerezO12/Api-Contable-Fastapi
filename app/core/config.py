"""
Configuración de la aplicación FastAPI

Este módulo maneja toda la configuración de la aplicación,
incluyendo base de datos, JWT y variables de entorno.

Equivalente en C# a appsettings.json + IConfiguration
"""

import os
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

class Settings(BaseSettings):
    
    # ================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # ================================
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "api_contable_dev2"
    db_user: str = "postgres"
    db_password: str = "123456"
    
    # URL completa opcional (sobrescribe los componentes individuales)
    database_url: Optional[str] = None
    
    # ================================
    # CONFIGURACIÓN JWT
    # ================================
    secret_key: str = "super-secret-key-change-in-production-must-be-very-long"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
      # ================================
    # CONFIGURACIÓN DE APLICACIÓN
    # ================================
    app_name: str = "API Contable"
    project_name: str = "API Contable"  # Para compatibilidad con .env
    debug: bool = True
    environment: str = "development"  # development, staging, production
    
    # CORS origins para el frontend
    backend_cors_origins: str = '["http://localhost", "http://localhost:4200", "http://localhost:3000", "http://localhost:5173"]'
    
    # URLs para notificaciones
    api_url: str = "http://localhost:8000"  # URL base de la API
    frontend_url: str = "http://localhost:3000"  # URL del frontend
    LOGIN_URL: str = api_url + "login"
    RESET_PASSWORD_URL: str = api_url + "reset-password"
    
    # ================================
    # VALIDADORES
    # ================================
    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validar que la clave secreta sea lo suficientemente segura"""
        if len(v) < 32:
            raise ValueError('La clave secreta debe tener al menos 32 caracteres para seguridad')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validar que el entorno sea válido"""
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'El entorno debe ser uno de: {allowed}')
        return v
    
    @property
    def database_connection_url(self) -> str:

        if self.database_url:
            # Si hay una URL completa en variable de entorno, usarla
            return self.database_url
        
        # Generar URL desde componentes individuales
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    @property 
    def production_database_url(self) -> str:
        """
        URL para producción - normalmente desde Cloud SQL o RDS
        
        Ejemplo para Google Cloud SQL:
        postgresql://user:password@/database?host=/cloudsql/project:region:instance
        
        O para AWS RDS:
        postgresql://user:password@rds-endpoint:5432/database
        """
        if self.environment == "production":
            # En producción usarías algo como:
            return "postgresql://user:password@your-cloud-sql-instance:5432/api_contable_prod"
        return self.database_connection_url
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        URL de conexión síncrona para SQLAlchemy.
        Usa psycopg2 como driver (recomendado para operaciones síncronas y migraciones)
        """
        base_url = self.database_connection_url
        if not base_url.startswith("postgresql+"):
            # Asegurar que use psycopg2 para operaciones síncronas
            base_url = base_url.replace("postgresql://", "postgresql+psycopg2://")
        return base_url
    
    @property
    def ASYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        URL de conexión asíncrona para SQLAlchemy.
        Usa asyncpg como driver (recomendado para operaciones asíncronas)
        """
        base_url = self.database_connection_url
        if not base_url.startswith("postgresql+"):
            # Asegurar que use asyncpg para operaciones asíncronas
            base_url = base_url.replace("postgresql://", "postgresql+asyncpg://")
        return base_url
    
    class Config:
        # Archivo .env para variables de entorno
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Permitir campos extra en .env sin error

# Instancia global de configuración
settings = Settings()
