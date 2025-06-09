from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1 import api_router
from app.database import create_async_db_and_tables, AsyncSessionLocal
from app.services.auth_service import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Crear las tablas de la base de datos
    await create_async_db_and_tables()
    
    # Crear usuario administrador por defecto si no existe
    async with AsyncSessionLocal() as db:
        try:
            admin_user = await AuthService.ensure_default_admin_exists(db)
            if admin_user:
                print(f"✅ Usuario administrador por defecto creado: {admin_user.email}")
            else:
                print("ℹ️  Usuario administrador ya existe, no se creó uno nuevo")
        except Exception as e:
            print(f"⚠️  Error al crear usuario administrador por defecto: {e}")
    
    yield
    # Shutdown: Cleanup si es necesario
    pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "API Contable - Sistema de Contabilidad",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "accounting-api"}
