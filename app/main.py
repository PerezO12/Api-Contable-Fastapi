from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from sqlalchemy import select, text

from app.core.settings import settings
from app.api.v1 import api_router
from app.database import create_async_db_and_tables, AsyncSessionLocal
from app.services.auth_service import AuthService
from app.utils.schema_rebuild import rebuild_schemas
from app.models.account import Account, AccountType, AccountCategory
from datetime import datetime, timezone
import logging

# AI Services
from app.core.ai_startup import initialize_ai_services, cleanup_ai_services

# Configure logging for AI services
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Intentar crear las tablas de la base de datos
    try:
        await create_async_db_and_tables()
        print("✅ Conexión a base de datos establecida")
        
        async with AsyncSessionLocal() as db:
            try:
                # Crear usuario administrador por defecto si no existe
                admin_user = await AuthService.ensure_default_admin_exists(db)
                if admin_user:
                    print(f"✅ Usuario administrador por defecto creado: {admin_user.email}")
                else:
                    print("ℹ️ Usuario administrador ya existe")
                
                # Crear cuentas de impuestos por defecto
                tax_accounts = [
                    {
                        "code": settings.DEFAULT_ICMS_ACCOUNT_CODE,
                        "name": settings.DEFAULT_ICMS_ACCOUNT_NAME,
                        "description": "Cuenta para control de ICMS por pagar/deducible"
                    },
                    {
                        "code": settings.DEFAULT_IPI_ACCOUNT_CODE,
                        "name": settings.DEFAULT_IPI_ACCOUNT_NAME,
                        "description": "Cuenta para control de IPI por pagar/deducible"
                    },
                    {
                        "code": settings.DEFAULT_PIS_ACCOUNT_CODE,
                        "name": settings.DEFAULT_PIS_ACCOUNT_NAME,
                        "description": "Cuenta para control de PIS por pagar/deducible"
                    },
                    {
                        "code": settings.DEFAULT_COFINS_ACCOUNT_CODE,
                        "name": settings.DEFAULT_COFINS_ACCOUNT_NAME,
                        "description": "Cuenta para control de COFINS por pagar/deducible"
                    }
                ]
                
                created_accounts = []
                for account_data in tax_accounts:
                    # Verificar si la cuenta ya existe
                    existing_account = await db.execute(
                        select(Account).where(Account.code == account_data["code"])
                    )
                    if not existing_account.scalar_one_or_none():
                        # Crear la cuenta
                        new_account = Account(
                            code=account_data["code"],
                            name=account_data["name"],
                            description=account_data["description"],
                            account_type=AccountType.LIABILITY,
                            category=AccountCategory.TAXES,  # Categoría específica para impuestos
                            is_active=True,
                            allows_movements=True,
                            requires_third_party=False,
                            requires_cost_center=False,
                            allows_reconciliation=True,
                            created_by_id=admin_user.id if admin_user else None,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        db.add(new_account)
                        created_accounts.append(new_account)
                
                if created_accounts:
                    await db.commit()
                    print(f"✅ {len(created_accounts)} cuentas de impuestos creadas")
                else:
                    print("ℹ️ Todas las cuentas de impuestos ya existen")
                
                # Initialize default currencies
                try:
                    from app.utils.currency_init import initialize_currencies
                    await initialize_currencies()
                    print("✅ Monedas por defecto inicializadas")
                except Exception as currency_error:
                    print(f"⚠️ Error inicializando monedas por defecto: {currency_error}")
                
                # Import all world currencies if enabled
                try:
                    from scripts.data_import.import_world_currencies import run_currency_import
                    await run_currency_import()
                    print("✅ Importación de monedas mundiales completada")
                except Exception as import_error:
                    print(f"⚠️ Error importando monedas mundiales: {import_error}")
                
            except Exception as admin_error:
                print(f"⚠️ Error al crear usuario administrador o cuentas: {admin_error}")
    except Exception as db_error:
        print(f"⚠️ Error de conexión a base de datos: {db_error}")
        print("ℹ️ La aplicación iniciará sin conexión a BD")
    
    # Rebuild schemas to resolve forward references
    rebuild_schemas()
    
    # Initialize AI services
    try:
        await initialize_ai_services()
        print("✅ Servicios de IA inicializados correctamente")
    except Exception as ai_error:
        print(f"⚠️ Error inicializando servicios de IA: {ai_error}")
        print("ℹ️ La aplicación iniciará sin servicios de IA")
    
    yield
    
    # Shutdown: Cleanup
    print("🛑 Cerrando aplicación...")
    try:
        await cleanup_ai_services()
        print("✅ Servicios de IA cerrados correctamente")
    except Exception as cleanup_error:
        print(f"⚠️ Error cerrando servicios de IA: {cleanup_error}")


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
