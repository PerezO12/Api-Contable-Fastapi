#!/bin/bash
set -e

# Script de entrada para Docker que maneja diferentes ambientes

echo "🚀 Iniciando API Contable en ambiente: ${ENVIRONMENT:-production}"

# Validar variables críticas en producción
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "📋 Validando configuración de producción..."
    
    # Validar variables críticas
    required_vars=("SECRET_KEY" "DB_PASSWORD")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ ERROR: Variable $var es requerida en producción"
            exit 1
        fi
    done
    
    echo "✅ Configuración de producción validada"
fi

# Ejecutar migraciones si es necesario
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "🔄 Ejecutando migraciones de base de datos..."
    alembic upgrade head
fi

# Crear usuario admin si es necesario
if [ "${CREATE_ADMIN:-false}" = "true" ]; then
    echo "👤 Creando usuario administrador..."
    python -c "
import asyncio
from app.core.settings import settings
from app.services.auth_service import AuthService
from app.database import get_async_session

async def create_admin():
    async for session in get_async_session():
        auth_service = AuthService(session)
        try:
            await auth_service.create_default_admin_user()
            print('✅ Usuario admin creado exitosamente')
        except Exception as e:
            print(f'ℹ️ Usuario admin: {e}')
        break

asyncio.run(create_admin())
"
fi

# Mostrar información de configuración (sin datos sensibles)
echo "📊 Configuración actual:"
echo "   - Ambiente: ${ENVIRONMENT:-production}"
echo "   - Debug: ${DEBUG:-false}"
echo "   - Base de datos: ${DB_HOST:-localhost}:${DB_PORT:-5432}/${DB_NAME:-accounting_system}"
echo "   - API URL: ${API_V1_STR:-/api/v1}"

# Iniciar la aplicación
echo "🌟 Iniciando servidor API..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --log-level ${LOG_LEVEL:-info} \
    --access-log \
    --use-colors
