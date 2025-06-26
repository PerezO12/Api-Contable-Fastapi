"""
Script de prueba completo para el sistema de importación corregido
Valida upload, preview y ejecución de importación de terceros
"""
import asyncio
import csv
import io
import json
import logging
from pathlib import Path

import httpx
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del test
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Datos de prueba para terceros
TEST_DATA = [
    {
        "codigo": "CLI001",
        "nombre": "Empresa ABC S.A.",
        "nombre_comercial": "ABC Corp",
        "tipo": "customer",
        "tipo_documento": "rut",
        "numero_documento": "76123456-7",
        "email": "contacto@abc.com",
        "telefono": "+56912345678",
        "direccion": "Av. Principal 123",
        "ciudad": "Santiago",
        "pais": "Chile",
        "activo": "true"
    },
    {
        "codigo": "PRV001", 
        "nombre": "Proveedor XYZ Ltda.",
        "nombre_comercial": "XYZ Supply",
        "tipo": "supplier",
        "tipo_documento": "rut",
        "numero_documento": "12345678-9",
        "email": "ventas@xyz.com",
        "telefono": "+56987654321",
        "direccion": "Calle Comercio 456",
        "ciudad": "Valparaíso",
        "pais": "Chile",
        "activo": "true"
    },
    {
        "codigo": "EMP001",
        "nombre": "Juan Pérez García",
        "tipo": "employee",
        "tipo_documento": "rut",
        "numero_documento": "11111111-1",
        "email": "jperez@empresa.com",
        "telefono": "+56911111111",
        "activo": "true"
    }
]


def create_test_csv() -> bytes:
    """Crea un archivo CSV de prueba en memoria"""
    output = io.StringIO()
    fieldnames = [
        "codigo", "nombre", "nombre_comercial", "tipo", "tipo_documento", 
        "numero_documento", "email", "telefono", "direccion", "ciudad", 
        "pais", "activo"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(TEST_DATA)
    
    return output.getvalue().encode('utf-8')


async def login() -> str:
    """Login y obtener token"""
    async with httpx.AsyncClient() as client:        # Usar credenciales de admin por defecto
        login_data = {
            "email": "admin@contable.com",
            "password": "Admin123!"
        }
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json=login_data
        )
        
        if response.status_code != 200:
            logger.error(f"Error en login: {response.status_code} - {response.text}")
            raise Exception("No se pudo hacer login")
        
        result = response.json()
        token = result.get("access_token")
        if not token:
            raise Exception("No se obtuvo token de acceso")
        
        logger.info("Login exitoso")
        return token


async def test_upload_file(token: str) -> str:
    """Test de upload de archivo"""
    logger.info("=== TEST UPLOAD ARCHIVO ===")
    
    csv_content = create_test_csv()
    
    async with httpx.AsyncClient() as client:
        files = {"file": ("terceros_test.csv", csv_content, "text/csv")}
        data = {"model": "third_party"}
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/simple-import/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error en upload: {response.status_code} - {response.text}")
            raise Exception("Upload falló")
        
        result = response.json()
        session_token = result.get("session_token")
        
        logger.info(f"Upload exitoso:")
        logger.info(f"  - Token sesión: {session_token}")
        logger.info(f"  - Archivo: {result.get('file_name')}")
        logger.info(f"  - Total filas: {result.get('total_rows')}")
        logger.info(f"  - Columnas: {result.get('columns')}")
        logger.info(f"  - Muestra: {len(result.get('sample_rows', []))} filas")
        
        return session_token


async def test_preview_import(token: str, session_token: str) -> bool:
    """Test de preview de importación"""
    logger.info("=== TEST PREVIEW IMPORTACIÓN ===")
    
    # Mapeo de columnas a campos del modelo
    mapping = [
        {"column_name": "codigo", "field_name": "code"},
        {"column_name": "nombre", "field_name": "name"},
        {"column_name": "nombre_comercial", "field_name": "commercial_name"},
        {"column_name": "tipo", "field_name": "third_party_type"},
        {"column_name": "tipo_documento", "field_name": "document_type"},
        {"column_name": "numero_documento", "field_name": "document_number"},
        {"column_name": "email", "field_name": "email"},
        {"column_name": "telefono", "field_name": "phone"},
        {"column_name": "direccion", "field_name": "address"},
        {"column_name": "ciudad", "field_name": "city"},
        {"column_name": "pais", "field_name": "country"},
        {"column_name": "activo", "field_name": "is_active"}
    ]
    
    request_data = {
        "session_token": session_token,
        "mapping": mapping,
        "preview_rows": 10
    }
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/simple-import/preview",
            json=request_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error en preview: {response.status_code} - {response.text}")
            raise Exception("Preview falló")
        
        result = response.json()
        
        logger.info(f"Preview exitoso:")
        logger.info(f"  - Total filas: {result.get('total_rows')}")
        logger.info(f"  - Filas preview: {len(result.get('preview_rows', []))}")
        logger.info(f"  - Puede proceder: {result.get('can_proceed')}")
        
        validation_summary = result.get('validation_summary', {})
        logger.info(f"  - Resumen validación:")
        logger.info(f"    - Total errores: {validation_summary.get('total_errors', 0)}")
        logger.info(f"    - Filas válidas: {validation_summary.get('valid_rows', 0)}")
        
        # Mostrar errores si los hay
        if validation_summary.get('total_errors', 0) > 0:
            logger.warning("Errores encontrados en preview:")
            for row in result.get('preview_rows', []):
                if row.get('has_errors'):
                    logger.warning(f"  Fila {row.get('row_number')}: {len(row.get('errors', []))} errores")
                    for error in row.get('errors', []):
                        logger.warning(f"    - {error.get('error_message')}")
        
        return result.get('can_proceed', False)


async def test_execute_import(token: str, session_token: str) -> dict:
    """Test de ejecución de importación"""
    logger.info("=== TEST EJECUCIÓN IMPORTACIÓN ===")
    
    # Mismo mapeo que en preview
    mapping = [
        {"column_name": "codigo", "field_name": "code"},
        {"column_name": "nombre", "field_name": "name"},
        {"column_name": "nombre_comercial", "field_name": "commercial_name"},
        {"column_name": "tipo", "field_name": "third_party_type"},
        {"column_name": "tipo_documento", "field_name": "document_type"},
        {"column_name": "numero_documento", "field_name": "document_number"},
        {"column_name": "email", "field_name": "email"},
        {"column_name": "telefono", "field_name": "phone"},
        {"column_name": "direccion", "field_name": "address"},
        {"column_name": "ciudad", "field_name": "city"},
        {"column_name": "pais", "field_name": "country"},
        {"column_name": "activo", "field_name": "is_active"}
    ]
    
    request_data = {
        "session_token": session_token,
        "mapping": mapping,
        "policy": "create_only",
        "batch_size": 100,
        "continue_on_error": False
    }
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/simple-import/execute",
            json=request_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error en ejecución: {response.status_code} - {response.text}")
            raise Exception("Ejecución falló")
        
        result = response.json()
        
        logger.info(f"Ejecución {'exitosa' if result.get('success') else 'falló'}:")
        
        summary = result.get('summary', {})
        logger.info(f"  - Resumen:")
        logger.info(f"    - Total filas: {summary.get('total_rows')}")
        logger.info(f"    - Creados: {summary.get('created_records')}")
        logger.info(f"    - Actualizados: {summary.get('updated_records')}")
        logger.info(f"    - Omitidos: {summary.get('skipped_records')}")
        logger.info(f"    - Fallidos: {summary.get('failed_records')}")
        logger.info(f"    - Tiempo: {summary.get('processing_time'):.2f}s")
        
        # Mostrar IDs creados
        created_ids = result.get('created_ids', [])
        if created_ids:
            logger.info(f"  - IDs creados: {', '.join(created_ids[:5])}{'...' if len(created_ids) > 5 else ''}")
        
        # Mostrar errores si los hay
        errors = result.get('errors', [])
        if errors:
            logger.warning(f"  - Errores ({len(errors)}):")
            for error in errors[:3]:  # Mostrar solo los primeros 3
                logger.warning(f"    Fila {error.get('row_number')}: {error.get('error_message')}")
        
        return result


async def test_get_models(token: str):
    """Test de obtener modelos disponibles"""
    logger.info("=== TEST OBTENER MODELOS ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/simple-import/models",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error obteniendo modelos: {response.status_code} - {response.text}")
            return
        
        result = response.json()
        models = result.get('models', [])
        
        logger.info(f"Modelos disponibles: {len(models)}")
        for model in models:
            logger.info(f"  - {model.get('label')} ({model.get('value')})")
            fields = model.get('fields', [])
            required_fields = [f['name'] for f in fields if f.get('required')]
            logger.info(f"    Campos obligatorios: {', '.join(required_fields)}")


async def main():
    """Función principal de test"""
    try:
        logger.info("Iniciando test completo del sistema de importación")
        
        # 1. Login
        token = await login()
        
        # 2. Test obtener modelos
        await test_get_models(token)
        
        # 3. Test upload
        session_token = await test_upload_file(token)
        
        # 4. Test preview
        can_proceed = await test_preview_import(token, session_token)
        
        if not can_proceed:
            logger.error("Preview detectó errores, no se puede proceder")
            return
        
        # 5. Test ejecución
        result = await test_execute_import(token, session_token)
        
        if result.get('success'):
            logger.info("✅ Test completo exitoso!")
        else:
            logger.error("❌ Test falló en la ejecución")
        
        logger.info("Test completado")
        
    except Exception as e:
        logger.error(f"Error en test: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
