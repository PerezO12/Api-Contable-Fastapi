"""
Esquemas para el servicio de chat IA con OpenAI
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Mensaje individual del chat"""
    role: str = Field(..., description="Rol del mensaje: 'user' o 'assistant'")
    content: str = Field(..., description="Contenido del mensaje")


class ChatRequest(BaseModel):
    """Request para el endpoint de chat"""
    message: str = Field(..., description="Mensaje del usuario", min_length=1, max_length=2000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Cómo puedo crear una factura en el sistema?"
            }
        }


class ChatResponse(BaseModel):
    """Respuesta del endpoint de chat"""
    success: bool = Field(..., description="Indica si la respuesta fue exitosa")
    message: str = Field(..., description="Mensaje de respuesta del asistente")
    model: Optional[str] = Field(None, description="Modelo utilizado para generar la respuesta")
    tokens_used: Optional[Dict[str, int]] = Field(None, description="Información sobre tokens utilizados")
    error: Optional[str] = Field(None, description="Mensaje de error si la petición falló")
    service_used: str = Field(default="openai", description="Servicio utilizado: 'openai' o 'fallback'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Para crear una factura necesitas ir al módulo de Facturación...",
                "model": "gpt-3.5-turbo",
                "tokens_used": {
                    "prompt_tokens": 150,
                    "completion_tokens": 75,
                    "total_tokens": 225
                },
                "error": None,
                "service_used": "openai"
            }
        }


class ChatHealthResponse(BaseModel):
    """Respuesta del endpoint de salud del chat"""
    openai_available: bool = Field(..., description="Indica si OpenAI está disponible")
    fallback_available: bool = Field(..., description="Indica si el sistema fallback está disponible")
    current_model: str = Field(..., description="Modelo actualmente configurado")
    api_key_configured: bool = Field(..., description="Indica si la API key está configurada")
    
    class Config:
        json_schema_extra = {
            "example": {
                "openai_available": True,
                "fallback_available": True,
                "current_model": "gpt-3.5-turbo",
                "api_key_configured": True
            }
        }
