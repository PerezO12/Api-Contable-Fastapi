"""
Configuración base para tests de integración
"""
import asyncio
import pytest
import uuid
from typing import AsyncGenerator, Dict, Any
import httpx
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_async_db
from app.models.base import Base
from app.services.auth_service import AuthService

# Base de datos de test en memoria
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Engine de test
test_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
)

# SessionMaker de test
TestSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override de la sesión de base de datos para tests"""
    async with TestSessionLocal() as session:
        yield session


# Override de la dependencia de DB
app.dependency_overrides[get_async_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Fixture para el event loop de asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Configurar la base de datos de test"""
    # Crear todas las tablas
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Limpiar después de todos los tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Fixture para obtener una sesión de base de datos limpia para cada test"""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Fixture para el cliente HTTP de test"""
    # Using httpx with ASGI transport
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> Dict[str, Any]:
    """Fixture que crea un usuario administrador para tests"""
    auth_service = AuthService(db_session)
    
    # Crear usuario admin con email único para evitar conflictos
    unique_suffix = str(uuid.uuid4())[:8]
    from app.schemas.user import UserCreateByAdmin
    from app.models.user import UserRole
    
    user_data = UserCreateByAdmin(
        email=f"admin-{unique_suffix}@test.com",
        full_name="Test Admin",
        role=UserRole.ADMIN,
        notes="Usuario administrador para tests",
        temporary_password="Admin123!"
    )
    
    admin_user = await auth_service.create_user_by_admin(
        user_data, 
        created_by_id=uuid.uuid4()  # UUID dummy para el creador
    )
    
    # Establecer una contraseña conocida
    admin_user.hashed_password = auth_service._hash_password("Admin123!")
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    
    return {
        "id": str(admin_user.id),
        "email": admin_user.email,
        "password": "Admin123!",
        "full_name": admin_user.full_name,
        "role": admin_user.role,
        "user_obj": admin_user
    }


@pytest.fixture
async def contador_user(db_session: AsyncSession, admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Fixture que crea un usuario contador para tests"""
    auth_service = AuthService(db_session)
    
    # Crear usuario contador con email único
    unique_suffix = str(uuid.uuid4())[:8]
    from app.schemas.user import UserCreateByAdmin
    from app.models.user import UserRole
    
    user_data = UserCreateByAdmin(
        email=f"contador-{unique_suffix}@test.com",
        full_name="Test Contador",
        role=UserRole.CONTADOR,
        notes="Usuario contador para tests",
        temporary_password="Contador123!"
    )
    
    contador_user = await auth_service.create_user_by_admin(
        user_data, 
        created_by_id=uuid.UUID(admin_user["id"])
    )
    
    # Establecer una contraseña conocida
    contador_user.hashed_password = auth_service._hash_password("Contador123!")
    db_session.add(contador_user)
    await db_session.commit()
    await db_session.refresh(contador_user)
    
    return {
        "id": str(contador_user.id),
        "email": contador_user.email,
        "password": "Contador123!",
        "full_name": contador_user.full_name,
        "role": contador_user.role,
        "user_obj": contador_user
    }


@pytest.fixture
async def readonly_user(db_session: AsyncSession, admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Fixture que crea un usuario de solo lectura para tests"""
    auth_service = AuthService(db_session)
    
    # Crear usuario readonly con email único
    unique_suffix = str(uuid.uuid4())[:8]
    from app.schemas.user import UserCreateByAdmin
    from app.models.user import UserRole
    
    user_data = UserCreateByAdmin(
        email=f"readonly-{unique_suffix}@test.com",
        full_name="Test ReadOnly",
        role=UserRole.SOLO_LECTURA,
        notes="Usuario de solo lectura para tests",
        temporary_password="ReadOnly123!"
    )
    
    readonly_user = await auth_service.create_user_by_admin(
        user_data, 
        created_by_id=uuid.UUID(admin_user["id"])
    )
    
    # Establecer una contraseña conocida
    readonly_user.hashed_password = auth_service._hash_password("ReadOnly123!")
    db_session.add(readonly_user)
    await db_session.commit()
    await db_session.refresh(readonly_user)
    
    return {
        "id": str(readonly_user.id),
        "email": readonly_user.email,
        "password": "ReadOnly123!",
        "full_name": readonly_user.full_name,
        "role": readonly_user.role,
        "user_obj": readonly_user
    }


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    """Helper para obtener token de autenticación"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def auth_headers_admin(client: AsyncClient, admin_user: Dict[str, Any]) -> Dict[str, str]:
    """Headers de autenticación para usuario admin"""
    token = await get_auth_token(client, admin_user["email"], admin_user["password"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_contador(client: AsyncClient, contador_user: Dict[str, Any]) -> Dict[str, str]:
    """Headers de autenticación para usuario contador"""
    token = await get_auth_token(client, contador_user["email"], contador_user["password"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_readonly(client: AsyncClient, readonly_user: Dict[str, Any]) -> Dict[str, str]:
    """Headers de autenticación para usuario readonly"""
    token = await get_auth_token(client, readonly_user["email"], readonly_user["password"])
    return {"Authorization": f"Bearer {token}"}
