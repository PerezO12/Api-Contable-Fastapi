"""
Cliente para interactuar con la API de OpenAI con sistema de fallback
"""
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from app.core.settings import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Cliente para la API de OpenAI con fallback automático"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=30.0  # Timeout de 30 segundos
        )
        # Modelo principal - gpt-4o-mini es muy bueno y económico
        self.model_name = "gpt-4o-mini"
        # Modelo alternativo
        self.fallback_model = "gpt-3.5-turbo"
        
        # Control de estado para usar fallback
        self._use_fallback = False
        self._fallback_reason = None
    
    async def generate_response(self, prompt: str) -> Optional[str]:
        """
        Genera una respuesta usando la API de OpenAI con fallback automático
        
        Args:
            prompt: El prompt para enviar a OpenAI
            
        Returns:
            La respuesta generada o None si hay error
        """
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        logger.info("OpenAI Client desactivado temporalmente")
        return "Los servicios de inteligencia artificial están temporalmente desactivados."
    
    async def _use_fallback_client(self, prompt: str) -> Optional[str]:
        """Usa el cliente fallback"""
        try:
            from app.services.fallback_ai_client import fallback_client
            return await fallback_client.generate_response(prompt)
        except Exception as e:
            logger.error(f"Error en fallback client: {e}")
            return "I'm sorry, I'm having trouble processing your request right now."
    
    async def _try_model(self, model: str, prompt: str) -> Optional[str]:
        """
        Intenta generar una respuesta con un modelo específico
        
        Args:
            model: Nombre del modelo a usar
            prompt: Prompt para enviar al modelo
            
        Returns:
            Respuesta generada o None si hay error
        """
        try:
            # Construir mensajes para chat completion
            messages: List[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": """You are an expert AI assistant for a comprehensive accounting software system. You specialize in helping users with:

ACCOUNTING EXPERTISE:
- Double-entry bookkeeping and chart of accounts
- Journal entries and financial transactions
- Accounts receivable and payable management
- Financial reporting (P&L, Balance Sheet, Cash Flow)
- Tax compliance and calculations
- Business expense tracking and categorization
- Budget planning and variance analysis

INVOICE MANAGEMENT:
When a user requests to create an invoice, respond ONLY with a JSON object in this exact format:
{
  "name": "create_invoice",
  "arguments": {
    "customer_id": <number>,
    "date": "<YYYY-MM-DD>",
    "items": [
      {
        "product_id": <number>,
        "quantity": <number>,
        "unit_price": <number>
      }
    ],
    "discount": <optional_number>,
    "notes": "<optional_string>"
  }
}

GENERAL GUIDANCE:
- Provide practical, actionable accounting advice
- Explain complex concepts in simple terms
- Always consider business context and best practices
- Be concise but thorough in explanations
- Help users understand accounting principles and procedures

You communicate in a professional yet friendly manner, making accounting accessible to users of all experience levels."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,  # Reducido para respuestas más rápidas
                temperature=0.7,
                top_p=0.9,
                timeout=25  # Timeout específico para esta request
            )
            
            if completion.choices and len(completion.choices) > 0:
                response_text = completion.choices[0].message.content
                if response_text:
                    logger.info(f"OpenAI respuesta generada exitosamente con modelo {model}")
                    return response_text.strip()
            
            logger.warning(f"No se recibió respuesta válida del modelo {model}")
            return None
            
        except Exception as e:
            logger.error(f"Error usando modelo {model}: {e}")
            return None
    
    async def generate_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Genera una respuesta con reintentos automáticos
        
        Args:
            prompt: Prompt en inglés para enviar al modelo
            max_retries: Número máximo de reintentos
            
        Returns:
            Respuesta generada por el modelo o fallback
        """
        # Si ya estamos en modo fallback, usar directamente
        if self._use_fallback:
            return await self._use_fallback_client(prompt)
        
        for attempt in range(max_retries):
            try:
                response = await self.generate_response(prompt)
                if response:
                    return response
                    
                logger.warning(f"Intento {attempt + 1} falló, reintentando...")
                
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}: {e}")
                
                # Si es error de quota o timeout en cualquier intento, activar fallback
                if any(keyword in str(e).lower() for keyword in ["quota", "429", "timeout", "timed out", "insufficient_quota"]):
                    self._use_fallback = True
                    if "quota" in str(e).lower() or "429" in str(e) or "insufficient_quota" in str(e).lower():
                        self._fallback_reason = "API quota exceeded during retry"
                    else:
                        self._fallback_reason = "API timeout during retry"
                    logger.warning(f"Error durante reintentos: {self._fallback_reason}, usando fallback")
                    return await self._use_fallback_client(prompt)
                
                if attempt == max_retries - 1:
                    logger.error("Todos los reintentos fallaron, usando fallback")
                    self._use_fallback = True
                    self._fallback_reason = "All retries failed"
                    return await self._use_fallback_client(prompt)
        
        return await self._use_fallback_client(prompt)
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con OpenAI o retorna True si usa fallback
        
        Returns:
            True si la conexión es exitosa o si usa fallback
        """
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        logger.info("Test de conexión OpenAI desactivado temporalmente")
        return False
        
        try:
            messages: List[ChatCompletionMessageParam] = [
                {"role": "user", "content": "Hello, this is a test message."}
            ]
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=10
            )
            
            if completion.choices and len(completion.choices) > 0:
                logger.info("Conexión con OpenAI exitosa")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error probando conexión con OpenAI: {e}")
            
            # Si es error de quota, activar fallback
            if "quota" in str(e).lower() or "429" in str(e) or "insufficient_quota" in str(e).lower():
                self._use_fallback = True
                self._fallback_reason = "Quota exceeded during connection test"
                logger.warning("Quota excedida en test de conexión, activando fallback")
                return True  # Retornar True porque el fallback está disponible
                
            return False
    
    def reset_fallback(self):
        """Resetea el estado de fallback para reintentar OpenAI"""
        self._use_fallback = False
        self._fallback_reason = None
        logger.info("Estado de fallback reseteado, reintentará OpenAI")
    
    def is_using_fallback(self) -> bool:
        """Retorna True si está usando el sistema fallback"""
        return self._use_fallback
    
    def get_fallback_reason(self) -> Optional[str]:
        """Retorna la razón por la que se activó el fallback"""
        return self._fallback_reason


# Instancia global del cliente
openai_client = OpenAIClient()
