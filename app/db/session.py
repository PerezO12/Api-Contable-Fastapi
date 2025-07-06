from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator, Generator

from app.core.settings import settings
from app.models.base import Base

# Sync engine for migrations and synchronous operations
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, 
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG  # SQL logging when debug is enabled
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine for asynchronous operations
async_engine = create_async_engine(
    settings.ASYNC_SQLALCHEMY_DATABASE_URI, 
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG  # SQL logging when debug is enabled
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


# Dependency for sync sessions
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


# Dependency for async sessions
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


# Database operations
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
