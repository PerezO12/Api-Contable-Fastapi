from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1 import api_router
from app.database import create_async_db_and_tables, AsyncSessionLocal
from app.services.auth_service import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Intentar crear las tablas de la base de datos
    try:
        await create_async_db_and_tables()
        print("✅ Conexión a base de datos establecida")
        
        # Crear usuario administrador por defecto si no existe
        async with AsyncSessionLocal() as db:
            try:
                admin_user = await AuthService.ensure_default_admin_exists(db)
                if admin_user:
                    print(f"✅ Usuario administrador por defecto creado: {admin_user.email}")
                else:
                    print("ℹ️ Usuario administrador ya existe")
            except Exception as admin_error:
                print(f"⚠️ Error al crear usuario administrador: {admin_error}")
    except Exception as db_error:
        print(f"⚠️ Error de conexión a base de datos: {db_error}")
        print("ℹ️ La aplicación iniciará sin conexión a BD")
    
    yield
    
    # Shutdown: Cleanup si es necesario
    print("🛑 Cerrando aplicación...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=False,  # Debe ser False cuando allow_origins=["*"]
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
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
