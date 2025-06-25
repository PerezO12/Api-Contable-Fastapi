"""
Import Templates API Endpoints
Handles CSV template downloads for all importable models
"""
import logging
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
import io
import csv

from app.services.model_metadata_registry import ModelMetadataRegistry

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize metadata registry
metadata_registry = ModelMetadataRegistry()

# Base path for templates
TEMPLATES_BASE_PATH = Path(__file__).parent.parent.parent.parent / "templates"


@router.get("/models/{model_name}/template")
async def download_template(model_name: str):
    """
    Descarga la plantilla CSV para un modelo específico
    
    Args:
        model_name: Nombre del modelo (third_party, product, account, invoice)
        
    Returns:
        CSV file with template data
    """
    logger.info(f"🔍 Solicitando plantilla para modelo: {model_name}")
    
    # Validar que el modelo existe
    try:
        available_models = metadata_registry.get_available_models()
        if model_name not in available_models:
            logger.warning(f"❌ Modelo no encontrado: {model_name}")
            raise HTTPException(
                status_code=404, 
                detail=f"Modelo '{model_name}' no encontrado. Modelos disponibles: {', '.join(available_models)}"
            )
        
        # Mapeo de nombres de modelos a archivos de plantilla
        template_files = {
            "third_party": "third_party_plantilla_importacion.csv",
            "product": "product_plantilla_importacion.csv", 
            "account": "account_plantilla_importacion.csv",
            "invoice": "invoice_import_template.csv"
        }
        
        template_filename = template_files.get(model_name)
        if not template_filename:
            logger.warning(f"❌ No hay plantilla disponible para modelo: {model_name}")
            raise HTTPException(
                status_code=404,
                detail=f"No hay plantilla disponible para el modelo '{model_name}'"
            )
        
        template_path = TEMPLATES_BASE_PATH / template_filename
        
        # Verificar que el archivo existe
        if not template_path.exists():
            logger.error(f"❌ Archivo de plantilla no encontrado: {template_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Archivo de plantilla no encontrado para '{model_name}'"
            )
        
        # Leer el contenido del archivo
        with open(template_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Crear response con headers apropiados
        response = Response(
            content=content.encode('utf-8'),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{model_name}_plantilla_importacion.csv"',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        logger.info(f"✅ Plantilla servida exitosamente para modelo: {model_name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error interno al servir plantilla para {model_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al generar plantilla: {str(e)}"
        )


@router.head("/models/{model_name}/template")
async def check_template_availability(model_name: str):
    """
    Verifica si una plantilla está disponible para un modelo específico
    
    Args:
        model_name: Nombre del modelo
        
    Returns:
        HTTP 200 si está disponible, 404 si no
    """
    try:
        available_models = metadata_registry.get_available_models()
        if model_name not in available_models:
            raise HTTPException(status_code=404, detail="Modelo no encontrado")
        
        # Mapeo de nombres de modelos a archivos de plantilla
        template_files = {
            "third_party": "third_party_plantilla_importacion.csv",
            "product": "product_plantilla_importacion.csv", 
            "account": "account_plantilla_importacion.csv",
            "invoice": "invoice_import_template.csv"
        }
        
        template_filename = template_files.get(model_name)
        if not template_filename:
            raise HTTPException(status_code=404, detail="Plantilla no disponible")
        
        template_path = TEMPLATES_BASE_PATH / template_filename
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Archivo de plantilla no encontrado")
        
        return Response(status_code=200)
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno")


@router.get("/models/{model_name}/examples")
async def download_examples(model_name: str, example_type: str = "complete"):
    """
    Descarga ejemplos prácticos para un modelo específico
    
    Args:
        model_name: Nombre del modelo (invoice, third_party, product, account)
        example_type: Tipo de ejemplo (complete, payment_terms, multi_line)
        
    Returns:
        CSV file with example data
    """
    logger.info(f"🔍 Solicitando ejemplos para modelo: {model_name}, tipo: {example_type}")
    
    # Solo soportamos ejemplos para facturas por ahora
    if model_name != "invoice":
        raise HTTPException(
            status_code=404,
            detail=f"Ejemplos no disponibles para el modelo '{model_name}'. Solo están disponibles para 'invoice'"
        )
    
    try:
        # Mapeo de tipos de ejemplos a archivos
        example_files = {
            "complete": "invoice_examples_complete.csv",
            "payment_terms": "invoice_payment_terms_examples.csv", 
            "multi_line": "ejemplo_factura_multiples_productos.csv"
        }
        
        example_filename = example_files.get(example_type)
        if not example_filename:
            available_types = ", ".join(example_files.keys())
            raise HTTPException(
                status_code=404,
                detail=f"Tipo de ejemplo '{example_type}' no disponible. Tipos disponibles: {available_types}"
            )
        
        example_path = TEMPLATES_BASE_PATH / example_filename
        
        # Verificar que el archivo existe
        if not example_path.exists():
            logger.error(f"❌ Archivo de ejemplo no encontrado: {example_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Archivo de ejemplo no encontrado para '{model_name}' tipo '{example_type}'"
            )
        
        # Leer el contenido del archivo
        with open(example_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Crear response con headers apropiados
        response = Response(
            content=content.encode('utf-8'),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{model_name}_ejemplos_{example_type}.csv"',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        logger.info(f"✅ Ejemplos servidos exitosamente para modelo: {model_name}, tipo: {example_type}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error interno al servir ejemplos para {model_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al generar ejemplos: {str(e)}"
        )


@router.get("/models/{model_name}/examples/info")
async def get_examples_info(model_name: str):
    """
    Obtiene información sobre los ejemplos disponibles para un modelo
    
    Args:
        model_name: Nombre del modelo
        
    Returns:
        Información sobre los tipos de ejemplos disponibles
    """
    logger.info(f"🔍 Solicitando información de ejemplos para modelo: {model_name}")
    
    if model_name != "invoice":
        raise HTTPException(
            status_code=404,
            detail=f"Ejemplos no disponibles para el modelo '{model_name}'"
        )
    
    try:
        examples_info = {
            "model": model_name,
            "available_examples": [
                {
                    "type": "complete",
                    "name": "Ejemplos Completos",
                    "description": "Facturas con múltiples productos, diferentes términos de pago y casos complejos",
                    "filename": "invoice_ejemplos_complete.csv",
                    "includes": [
                        "Facturas de venta y compra",
                        "Múltiples productos por factura", 
                        "Diferentes términos de pago",
                        "Notas de crédito y débito",
                        "Diversos estados de factura"
                    ]
                },
                {
                    "type": "payment_terms",
                    "name": "Términos de Pago",
                    "description": "Ejemplos específicos de todos los términos de pago disponibles",
                    "filename": "invoice_ejemplos_payment_terms.csv",
                    "includes": [
                        "COD (Cash on Delivery)",
                        "NET15, NET30, NET45, NET60, NET90",
                        "2/10NET30 (descuento por pronto pago)",
                        "EOM (End of Month)",
                        "CIA (Cash in Advance)",
                        "IMMEDIATE (pago inmediato)"
                    ]
                },
                {
                    "type": "multi_line",
                    "name": "Múltiples Productos",
                    "description": "Ejemplos de facturas con múltiples líneas de productos",
                    "filename": "invoice_ejemplos_multi_line.csv",
                    "includes": [
                        "Facturas con 2-3 productos diferentes",
                        "Diferentes precios y cantidades",
                        "Descuentos por línea",
                        "Cuentas contables diferentes por producto"
                    ]
                }
            ]
        }
        
        logger.info(f"✅ Información de ejemplos servida para modelo: {model_name}")
        return examples_info
        
    except Exception as e:
        logger.error(f"❌ Error al obtener información de ejemplos para {model_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.head("/models/{model_name}/examples")
async def check_examples_availability(model_name: str, example_type: str = "complete"):
    """
    Verifica si los ejemplos están disponibles para un modelo específico
    
    Args:
        model_name: Nombre del modelo
        example_type: Tipo de ejemplo
        
    Returns:
        HTTP 200 si están disponibles, 404 si no
    """
    try:
        if model_name != "invoice":
            raise HTTPException(status_code=404, detail="Ejemplos no disponibles")
        
        example_files = {
            "complete": "invoice_examples_complete.csv",
            "payment_terms": "invoice_payment_terms_examples.csv", 
            "multi_line": "ejemplo_factura_multiples_productos.csv"
        }
        
        example_filename = example_files.get(example_type)
        if not example_filename:
            raise HTTPException(status_code=404, detail="Tipo de ejemplo no disponible")
        
        example_path = TEMPLATES_BASE_PATH / example_filename
        if not example_path.exists():
            raise HTTPException(status_code=404, detail="Archivo de ejemplo no encontrado")
        
        return Response(status_code=200)
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno")
