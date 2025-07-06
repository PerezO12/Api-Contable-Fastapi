"""
Servicio de OpenAI para el sistema contable
"""
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from app.core.settings import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Servicio para manejar la comunicación con OpenAI"""
    
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente de OpenAI"""
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        logger.info("Servicios de OpenAI desactivados temporalmente")
        self.client = None
        return
    
    def is_available(self) -> bool:
        """Verifica si el servicio de OpenAI está disponible"""
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        return False
    
    async def generate_chat_response(self, user_message: str) -> Dict[str, Any]:
        """
        Genera una respuesta de chat usando OpenAI
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Diccionario con la respuesta y metadatos
        """
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        logger.info("Solicitud de chat rechazada - servicios de IA desactivados")
        return {
            "success": False,
            "error": "Servicios de IA desactivados temporalmente",
            "message": "Los servicios de inteligencia artificial están temporalmente desactivados."
        }
    
    def _build_system_prompt(self) -> str:
        """Construye el prompt del sistema para el asistente contable"""
        return """Eres un asistente virtual experto en contabilidad integrado en un sistema web contable desarrollado por mi equipo. 

CARACTERÍSTICAS:
- Hablas español e inglés perfectamente
- Tienes conocimiento profundo en contabilidad, finanzas y administración empresarial
- Estás integrado en un sistema contable moderno con FastAPI y React
- Puedes ayudar con facturación, reportes, análisis financiero y consultas contables

FUNCIONALIDADES DEL SISTEMA:
- Creación y gestión de facturas
- Registro de transacciones contables
- Generación de reportes financieros (Balance General, Estado de Resultados, Flujo de Caja)
- Gestión de clientes y proveedores
- Control de inventario y productos
- Análisis de costos y rentabilidad
- Cumplimiento fiscal y tributario

INSTRUCCIONES:
1. Responde de manera profesional pero amigable
2. Proporciona explicaciones claras y prácticas
3. Si te preguntan sobre funciones específicas del sistema, explica cómo usarlas
4. Para consultas complejas de contabilidad, desglosa la información paso a paso
5. Siempre mantén el contexto de ser parte de un sistema contable moderno
6. Si no estás seguro de algo, admítelo y sugiere alternativas

¿En qué puedo ayudarte hoy con tu contabilidad?"""


# Instancia global del servicio
openai_service = OpenAIService()
