"""
Test específico para verificar las correcciones en el sistema de importación genérica
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

# Datos de prueba similares a los del ejemplo del error
TEST_CSV_CONTENT = """name,third_party_type
Adrian Cliente,CUSTOMER
Pedro Sahss,CUSTOMER
Cliente de Prueba,CUSTOMER
Proveedor de Prueba,CUSTOMER
Cliente JE Test,CUSTOMER
Proveedor XYZ Ltda.,CUSTOMER
Juan Pérez García,CUSTOMER"""

async def login() -> str:
    """Login para obtener token"""
    logger.info("Iniciando login...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",            json={
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
        
        logger.info("Login exitoso")
        return token


async def create_import_session(token: str) -> str:
    """Crear sesión de importación"""
    logger.info("=== CREANDO SESIÓN DE IMPORTACIÓN ===")
    
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
        
        logger.info(f"Sesión creada exitosamente:")
        logger.info(f"  - Token sesión: {session_token}")
        logger.info(f"  - Modelo: {result.get('model')}")
        logger.info(f"  - Columnas detectadas: {[col['name'] for col in result.get('detected_columns', [])]}")
        
        return session_token


async def test_preview_with_mappings(token: str, session_token: str):
    """Test de preview con mapeos similares al ejemplo del problema"""
    logger.info("=== TEST PREVIEW CON MAPEOS ===")
    
    # Mapeos similares a los del problema - muchos sin field_name
    mappings = [
        {"column_name": "name", "field_name": "name"},
        {"column_name": "third_party_type"},  # Sin field_name
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
        logger.info(f"Preview exitoso:")
        logger.info(f"  - Filas analizadas: {result.get('validation_summary', {}).get('total_rows_analyzed', 0)}")
        logger.info(f"  - Filas válidas: {result.get('validation_summary', {}).get('valid_rows', 0)}")
        logger.info(f"  - Filas con errores: {result.get('validation_summary', {}).get('rows_with_errors', 0)}")
        logger.info(f"  - Puede proceder: {result.get('can_proceed', False)}")
        logger.info(f"  - Puede omitir errores: {result.get('can_skip_errors', False)}")
        
        return True


async def test_execute_import_with_skip_errors(token: str, session_token: str):
    """Test de ejecución con skip_errors=true"""
    logger.info("=== TEST EJECUCIÓN CON SKIP ERRORS ===")
    
    # Mapeos mejorados - incluir field_name donde sea posible
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
        logger.info(f"Ejecución completada:")
        logger.info(f"  - Status: {result.get('status')}")
        logger.info(f"  - Total filas: {result.get('total_rows')}")
        logger.info(f"  - Filas exitosas: {result.get('successful_rows')}")
        logger.info(f"  - Filas con errores: {result.get('error_rows')}")
        logger.info(f"  - Filas omitidas: {result.get('skipped_rows')}")
        
        if result.get('skipped_details'):
            logger.info("Detalles de filas omitidas:")
            for detail in result.get('skipped_details', []):
                logger.info(f"    - {detail}")
        
        if result.get('errors'):
            logger.info("Errores:")
            for error in result.get('errors', []):
                logger.info(f"    - {error}")
        
        # Verificar que no todas las filas fueron omitidas
        total_processed = result.get('successful_rows', 0) + result.get('error_rows', 0)
        total_skipped = result.get('skipped_rows', 0)
        
        if total_processed > 0:
            logger.info("✅ ÉXITO: Algunas filas fueron procesadas exitosamente")
        else:
            logger.warning("⚠️  ADVERTENCIA: Todas las filas fueron omitidas")
        
        return total_processed > 0


async def main():
    """Función principal del test"""
    try:
        # Login
        token = await login()
        
        # Crear sesión de importación
        session_token = await create_import_session(token)
        
        # Test preview
        await test_preview_with_mappings(token, session_token)
        
        # Test ejecución con skip_errors
        success = await test_execute_import_with_skip_errors(token, session_token)
        
        if success:
            logger.info("✅ TEST COMPLETADO EXITOSAMENTE")
        else:
            logger.error("❌ TEST FALLÓ")
            
    except Exception as e:
        logger.error(f"Error en test: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
