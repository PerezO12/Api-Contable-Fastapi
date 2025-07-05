"""
Servicio híbrido de chat que combina OpenAI con sistema fallback
"""
import logging
from typing import Dict, Any
from app.services.openai_service import openai_service
from app.services.fallback_ai_client import fallback_client

logger = logging.getLogger(__name__)


class HybridChatService:
    """Servicio de chat que usa OpenAI como principal y fallback como respaldo"""
    
    def __init__(self):
        self.openai_service = openai_service
        self.fallback_service = fallback_client
    
    async def generate_response(self, user_message: str) -> Dict[str, Any]:
        """
        Genera una respuesta usando OpenAI primero, fallback como respaldo
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Diccionario con la respuesta y metadatos
        """
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        logger.info("Servicios de IA desactivados - devolviendo mensaje informativo")
        
        return {
            "success": True,
            "message": "Los servicios de inteligencia artificial están temporalmente desactivados. El sistema de contabilidad sigue funcionando normalmente para todas las demás operaciones como facturas, reportes, gestión de clientes y transacciones contables.",
            "model": "disabled",
            "tokens_used": None,
            "error": None,
            "service_used": "disabled"
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de salud de ambos servicios
        
        Returns:
            Diccionario con el estado de los servicios
        """
        return {
            "openai_available": False,
            "fallback_available": False,
            "current_model": "disabled",
            "api_key_configured": False,
            "status": "Los servicios de IA están temporalmente desactivados"
        }


# Instancia global del servicio híbrido
hybrid_chat_service = HybridChatService()
