from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator, Generator

from app.config import settings
from app.models.base import Base

# Crear URL asíncrona para PostgreSQL
def get_async_database_url() -> str:
    """Convierte la URL de PostgreSQL a formato asyncpg"""
    url = settings.DATABASE_URL
    if url and url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    elif url and url.startswith("postgresql+psycopg"):
        return url.replace("postgresql+psycopg", "postgresql+asyncpg")
    return url or "postgresql+asyncpg://postgres:@localhost:5432/accounting_system"

# Sync engine para migraciones y operaciones síncronas
engine = create_engine(
    settings.DATABASE_URL or "postgresql://postgres:@localhost:5432/accounting_system",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG  # SQL logging en debug
)

# Async engine para operaciones asíncronas
async_engine = create_async_engine(
    get_async_database_url(),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

# Session makers
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    class_=Session
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


# Dependency para FastAPI (síncrono)
def get_db() -> Generator[Session, None, None]:
    """Dependency para obtener sesión de base de datos síncrona"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Dependency para FastAPI (asíncrono)
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para obtener sesión de base de datos asíncrona"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Para crear las tablas
def create_db_and_tables():
    """Crea todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)


def drop_db_and_tables():
    """Elimina todas las tablas de la base de datos"""
    Base.metadata.drop_all(bind=engine)


async def create_async_db_and_tables():
    """Crea todas las tablas en la base de datos (versión asíncrona)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
