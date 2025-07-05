"""
Cliente alternativo para IA que puede funcionar sin tokens de Hugging Face
"""
import httpx
import json
import logging
from typing import Dict, Any, Optional
import random

logger = logging.getLogger(__name__)


class AlternativeAIClient:
    """Cliente de IA alternativo que no requiere tokens"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # APIs públicas gratuitas como fallback
        self.public_apis = [
            {
                "name": "dummy_ai",
                "url": None,  # Respuestas simuladas
                "type": "simulation"
            }
        ]
    
    async def generate_response(self, prompt: str) -> Optional[str]:
        """
        Genera una respuesta usando métodos alternativos
        
        Args:
            prompt: El prompt del usuario
            
        Returns:
            Respuesta generada o None si hay error
        """
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        logger.info("Alternative AI Client desactivado temporalmente")
        return "Los servicios de inteligencia artificial están temporalmente desactivados."
    
    def _generate_intelligent_fallback(self, prompt: str) -> str:
        """
        Genera respuestas inteligentes basadas en patrones del prompt
        """
        prompt_lower = prompt.lower()
        
        # Detectar solicitudes de facturas
        if any(word in prompt_lower for word in ['invoice', 'factura', 'create invoice', 'bill']):
            return self._generate_invoice_response(prompt)
        
        # Detectar saludos
        elif any(word in prompt_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            greetings = [
                "Hello! I'm here to help you with your accounting needs. How can I assist you today?",
                "Hi there! I can help you create invoices, manage accounts, and answer questions about your accounting system.",
                "Good day! I'm your accounting assistant. What would you like to do today?"
            ]
            return random.choice(greetings)
        
        # Detectar preguntas sobre el sistema
        elif any(word in prompt_lower for word in ['what can you do', 'help', 'how', 'what']):
            return """I'm an AI assistant for your accounting system. I can help you with:

1. Creating invoices and bills
2. Managing customer and supplier information  
3. Generating financial reports
4. Answering questions about your accounts
5. Processing journal entries

What would you like to do today?"""
        
        # Detectar solicitudes de reportes
        elif any(word in prompt_lower for word in ['report', 'balance', 'statement', 'summary']):
            return "I can help you generate various financial reports. What type of report would you like to create? (Balance sheet, income statement, customer summary, etc.)"
        
        # Respuesta general para conversación
        else:
            responses = [
                "I understand. Could you please provide more details about what you'd like to do?",
                "That's interesting. How can I help you with your accounting needs?",
                "I'm here to assist with your accounting system. What specific task would you like to accomplish?",
                "Thank you for that information. What would you like me to help you with today?"
            ]
            return random.choice(responses)
    
    def _generate_invoice_response(self, prompt: str) -> str:
        """
        Genera respuesta para solicitudes de factura
        """
        # Intentar extraer información básica del prompt
        prompt_lower = prompt.lower()
        
        # Buscar nombres de clientes
        client_indicators = ['for ', 'to ', 'customer ', 'client ']
        client_name = None
        
        for indicator in client_indicators:
            if indicator in prompt_lower:
                parts = prompt_lower.split(indicator)
                if len(parts) > 1:
                    # Tomar palabras después del indicador
                    after_indicator = parts[1].split()
                    if after_indicator:
                        # Tomar hasta 2 palabras como nombre
                        client_name = ' '.join(after_indicator[:2]).title()
                        break
        
        if not client_name:
            client_name = "Customer"
        
        # Buscar montos
        import re
        amounts = re.findall(r'\$(\d+(?:\.\d{2})?)', prompt)
        total_amount = sum(float(amount) for amount in amounts) if amounts else 100.00
        
        # Generar respuesta JSON para crear factura
        invoice_response = {
            "action": "create_invoice",
            "invoice_data": {
                "client_name": client_name,
                "items": [
                    {
                        "description": "Service/Product",
                        "quantity": 1,
                        "unit_price": total_amount
                    }
                ],
                "due_date": "2025-07-30"
            }
        }
        
        return f"I'll help you create an invoice. Based on your request:\n\n{json.dumps(invoice_response, indent=2)}\n\nWould you like me to proceed with creating this invoice?"
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
    
    async def check_health(self) -> Dict[str, Any]:
        """Verifica el estado del cliente alternativo"""
        return {
            "status": "healthy",
            "type": "fallback_ai",
            "message": "Alternative AI client is operational",
            "capabilities": [
                "invoice_creation",
                "general_conversation", 
                "accounting_assistance"
            ]
        }


# Instancia singleton
alternative_ai_client = AlternativeAIClient()
