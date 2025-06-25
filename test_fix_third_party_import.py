#!/usr/bin/env python3
"""
Test para verificar la corrección de la importación de terceros
"""
import asyncio
import json
import logging
from pathlib import Path

import httpx

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del test
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Datos de prueba con solo los campos mínimos
TEST_CSV_CONTENT = """name,third_party_type
Adrian Cliente,CUSTOMER
Pedro Sahss,CUSTOMER
Cliente de Prueba,CUSTOMER
Proveedor de Prueba,SUPPLIER
Juan Pérez García,EMPLOYEE"""

async def login() -> str:
    """Login para obtener token"""
    logger.info("🔐 Iniciando login...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={
                "email": "admin@contable.com", 
                "password": "admin123"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Login falló: {response.status_code} - {response.text}")
        
        result = response.json()
        token = result.get("access_token")
        if not token:
            raise Exception("No se obtuvo token de acceso")
        
        logger.info("✅ Login exitoso")
        return token


async def get_model_metadata(token: str) -> dict:
    """Obtener metadata del modelo third_party"""
    logger.info("📋 Obteniendo metadata del modelo third_party...")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/generic-import/models/third_party/metadata",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error obteniendo metadata: {response.status_code} - {response.text}")
            raise Exception("Obtener metadata falló")
        
        metadata = response.json()
        logger.info("✅ Metadata obtenida:")
        logger.info(f"  - Modelo: {metadata.get('model_name')}")
        logger.info(f"  - Campos requeridos: {[f['internal_name'] for f in metadata.get('fields', []) if f.get('is_required')]}")
        logger.info(f"  - Campos con defaults: {[f['internal_name'] for f in metadata.get('fields', []) if f.get('default_value')]}")
        
        return metadata


async def create_import_session(token: str) -> str:
    """Crear sesión de importación"""
    logger.info("📤 Creando sesión de importación...")
    
    async with httpx.AsyncClient() as client:
        files = {"file": ("terceros_test.csv", TEST_CSV_CONTENT, "text/csv")}
        data = {"model_name": "third_party"}
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/generic-import/sessions",
            files=files,
            data=data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error creando sesión: {response.status_code} - {response.text}")
            raise Exception("Creación de sesión falló")
        
        result = response.json()
        session_token = result.get("import_session_token")
        
        logger.info("✅ Sesión creada exitosamente:")
        logger.info(f"  - Token sesión: {session_token}")
        logger.info(f"  - Modelo: {result.get('model')}")
        logger.info(f"  - Columnas detectadas: {[col['name'] for col in result.get('detected_columns', [])]}")
        logger.info(f"  - Filas de muestra: {result.get('sample_row_count', 0)}")
        
        return session_token


async def get_mapping_suggestions(token: str, session_token: str) -> dict:
    """Obtener sugerencias de mapeo"""
    logger.info("🧭 Obteniendo sugerencias de mapeo...")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/generic-import/sessions/{session_token}/mapping-suggestions",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error obteniendo sugerencias: {response.status_code} - {response.text}")
            return {}
        
        suggestions = response.json()
        logger.info("✅ Sugerencias obtenidas:")
        
        for suggestion in suggestions.get("suggestions", []):
            logger.info(f"  - '{suggestion['column_name']}' -> '{suggestion.get('suggested_field', 'No sugerencia')}' (confianza: {suggestion.get('confidence', 0):.2f})")
        
        return suggestions


async def test_preview_with_mappings(token: str, session_token: str):
    """Test de preview con mapeos"""
    logger.info("👀 Ejecutando preview con mapeos...")
    
    # Mapeos explícitos basados en las columnas detectadas
    mappings = [
        {"column_name": "name", "field_name": "name"},
        {"column_name": "third_party_type", "field_name": "third_party_type"},
    ]
    
    preview_request = {
        "column_mappings": mappings,
        "preview_rows": 10
    }
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/generic-import/sessions/{session_token}/preview",
            json=preview_request,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error en preview: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        validation_summary = result.get('validation_summary', {})
        
        logger.info("✅ Preview exitoso:")
        logger.info(f"  - Filas analizadas: {validation_summary.get('total_rows_analyzed', 0)}")
        logger.info(f"  - Filas válidas: {validation_summary.get('valid_rows', 0)}")
        logger.info(f"  - Filas con errores: {validation_summary.get('rows_with_errors', 0)}")
        logger.info(f"  - Puede proceder: {result.get('can_proceed', False)}")
        logger.info(f"  - Puede omitir errores: {result.get('can_skip_errors', False)}")
        
        # Mostrar errores si los hay
        if validation_summary.get('validation_errors'):
            logger.warning("⚠️ Errores de validación encontrados:")
            for error in validation_summary['validation_errors'][:3]:  # Solo los primeros 3
                logger.warning(f"  - {error}")
        
        return True


async def test_execute_import_with_create_only(token: str, session_token: str):
    """Test de ejecución con create_only y skip_errors=true"""
    logger.info("🚀 Ejecutando importación con create_only y skip_errors=true...")
    
    # Mapeos explícitos
    mappings = [
        {"column_name": "name", "field_name": "name"},
        {"column_name": "third_party_type", "field_name": "third_party_type"},
    ]
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        params = {
            "import_policy": "create_only",
            "skip_errors": "true"
        }
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/generic-import/sessions/{session_token}/execute",
            json=mappings,
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            logger.error(f"Error en ejecución: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        
        logger.info("✅ Ejecución completada:")
        logger.info(f"  - Estado: {result.get('status')}")
        logger.info(f"  - Filas totales: {result.get('total_rows', 0)}")
        logger.info(f"  - Filas exitosas: {result.get('successful_rows', 0)}")
        logger.info(f"  - Filas con errores: {result.get('error_rows', 0)}")
        logger.info(f"  - Filas omitidas: {result.get('skipped_rows', 0)}")
        logger.info(f"  - Mensaje: {result.get('message', '')}")
        
        # Mostrar errores si los hay
        if result.get('errors'):
            logger.error("❌ Errores encontrados:")
            for error in result['errors']:
                logger.error(f"  - {error}")
        
        # Mostrar detalles de filas omitidas
        if result.get('skipped_details'):
            logger.warning("⚠️ Filas omitidas:")
            for detail in result['skipped_details']:
                logger.warning(f"  - {detail}")
        
        # Determinar si el test fue exitoso
        successful = result.get('successful_rows', 0) > 0 and result.get('error_rows', 0) == 0
        
        if successful:
            logger.info("🎉 Test de importación EXITOSO - Se crearon terceros correctamente")
        else:
            logger.error("💥 Test de importación FALLÓ - No se crearon terceros o hubo errores")
        
        return successful


async def run_complete_test():
    """Ejecutar test completo"""
    logger.info("🧪 Iniciando test completo de importación de terceros...")
    
    try:
        # 1. Login
        token = await login()
        
        # 2. Obtener metadata
        metadata = await get_model_metadata(token)
        
        # 3. Crear sesión
        session_token = await create_import_session(token)
        
        # 4. Obtener sugerencias
        suggestions = await get_mapping_suggestions(token, session_token)
        
        # 5. Test preview
        preview_success = await test_preview_with_mappings(token, session_token)
        
        if not preview_success:
            logger.error("💥 Preview falló - deteniendo test")
            return False
        
        # 6. Test ejecución
        execution_success = await test_execute_import_with_create_only(token, session_token)
        
        if execution_success:
            logger.info("🎉 TEST COMPLETO EXITOSO")
        else:
            logger.error("💥 TEST COMPLETO FALLÓ")
        
        return execution_success
        
    except Exception as e:
        logger.error(f"💥 Error en test: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_complete_test())
    exit(0 if success else 1)
