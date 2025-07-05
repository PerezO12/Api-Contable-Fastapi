"""
Configuración de startup para servicios de IA
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.services.translation import translation_service
from app.services.hf_client import hf_client

logger = logging.getLogger(__name__)


async def initialize_ai_services():
    """Inicializa todos los servicios de IA necesarios"""
    try:
        logger.info("🚀 Inicializando servicios de IA...")
        
        # Los servicios de traducción se inicializan automáticamente
        # al instanciar translation_service (patrón singleton)
        logger.info("✅ Servicios de traducción inicializados")
        
        # El cliente de HF se inicializa automáticamente
        logger.info("✅ Cliente de Hugging Face configurado")
        
        logger.info("🎉 Todos los servicios de IA están listos")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios de IA: {e}")
        raise


async def cleanup_ai_services():
    """Limpia los recursos de los servicios de IA"""
    try:
        logger.info("🧹 Limpiando servicios de IA...")
        
        # Cerrar cliente HTTP de Hugging Face
        await hf_client.close()
        
        logger.info("✅ Servicios de IA limpiados correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error limpiando servicios de IA: {e}")


@asynccontextmanager
async def ai_lifespan(app: FastAPI):
    """Context manager para el ciclo de vida de servicios de IA"""
    # Startup
    await initialize_ai_services()
    
    try:
        yield
    finally:
        # Shutdown
        await cleanup_ai_services()
