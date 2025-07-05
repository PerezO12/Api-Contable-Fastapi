"""
Endpoint para el servicio de chat con IA usando OpenAI
"""
from fastapi import APIRouter, HTTPException
import logging

from app.schemas.chat import ChatRequest, ChatResponse, ChatHealthResponse
from app.services.hybrid_chat_service import hybrid_chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal para chat con IA
    
    Recibe un mensaje del usuario y devuelve una respuesta generada por OpenAI
    con fallback a un sistema local si OpenAI no está disponible.
    
    El asistente está especializado en contabilidad y funciona en español e inglés.
    """
    try:
        logger.info(f"Procesando mensaje de chat: {request.message[:100]}...")
        
        # Validar entrada
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
        
        # Generar respuesta usando el servicio híbrido
        response_data = await hybrid_chat_service.generate_response(request.message)
        
        return ChatResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en chat endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno del servidor al procesar el mensaje"
        )


@router.get("/chat/health", response_model=ChatHealthResponse)
async def chat_health():
    """
    Endpoint para verificar el estado del servicio de chat
    
    Retorna información sobre la disponibilidad de OpenAI y el sistema fallback
    """
    try:
        health_data = hybrid_chat_service.get_health_status()
        return ChatHealthResponse(**health_data)
        
    except Exception as e:
        logger.error(f"Error en chat health endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al verificar el estado del servicio de chat"
        )


@router.post("/chat/test")
async def test_chat():
    """
    Endpoint para probar el sistema de chat con mensajes de ejemplo
    """
    try:
        test_messages = [
            "Hola, ¿cómo funciona el sistema?",
            "How do I create an invoice?",
            "¿Qué es la partida doble?",
            "Help me with accounting reports"
        ]
        
        results = []
        
        for message in test_messages:
            logger.info(f"Probando mensaje: {message}")
            response_data = await hybrid_chat_service.generate_response(message)
            
            results.append({
                "input": message,
                "output": response_data.get("message", "")[:200] + "...",
                "service_used": response_data.get("service_used"),
                "success": response_data.get("success")
            })
        
        return {
            "test_results": results,
            "system_health": hybrid_chat_service.get_health_status()
        }
        
    except Exception as e:
        logger.error(f"Error en test de chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error testing chat system: {str(e)}"
        )
