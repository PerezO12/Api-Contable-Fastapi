"""
Utilidades para el servicio de chat IA
"""
import json
import re
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class FunctionCall(BaseModel):
    """Modelo para llamadas de función parseadas del modelo IA"""
    name: str
    arguments: Dict[str, Any]


class InvoiceArguments(BaseModel):
    """Modelo para validar argumentos de creación de factura"""
    customer_id: int
    date: str
    items: list
    discount: Optional[float] = 0.0
    notes: Optional[str] = ""


def parse_ai_response(response: str) -> tuple[bool, Optional[FunctionCall], str]:
    """
    Parsea la respuesta del modelo IA para detectar si es una llamada de función
    
    Args:
        response: Respuesta del modelo IA
        
    Returns:
        Tupla (es_funcion, funcion_parseada, texto_limpio)
    """
    try:
        # Limpiar la respuesta
        cleaned_response = response.strip()
        
        # Buscar patrones de JSON en la respuesta
        json_patterns = [
            r'\{[^{}]*"name"\s*:\s*"create_invoice"[^{}]*\}',
            r'\{.*?"name".*?:.*?"create_invoice".*?\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                try:
                    # Intentar parsear como JSON
                    json_data = json.loads(match)
                    
                    if isinstance(json_data, dict) and json_data.get("name") == "create_invoice":
                        function_call = FunctionCall(**json_data)
                        logger.info("✅ Función create_invoice detectada y parseada")
                        return True, function_call, cleaned_response
                        
                except json.JSONDecodeError:
                    continue
                except ValidationError as e:
                    logger.warning(f"JSON válido pero estructura incorrecta: {e}")
                    continue
        
        # Si no se encontró JSON válido, buscar inicio de JSON
        if '{' in cleaned_response and '"name"' in cleaned_response and 'create_invoice' in cleaned_response:
            logger.info("Posible función detectada pero no parseada correctamente")
            # Intentar extraer y limpiar JSON
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                potential_json = cleaned_response[start_idx:end_idx]
                try:
                    json_data = json.loads(potential_json)
                    if isinstance(json_data, dict) and json_data.get("name") == "create_invoice":
                        function_call = FunctionCall(**json_data)
                        return True, function_call, cleaned_response
                except:
                    pass
        
        # No es una función, es texto normal
        return False, None, cleaned_response
        
    except Exception as e:
        logger.error(f"Error parseando respuesta IA: {e}")
        return False, None, response


def validate_invoice_arguments(arguments: Dict[str, Any]) -> tuple[bool, Optional[InvoiceArguments], str]:
    """
    Valida los argumentos para crear una factura
    
    Args:
        arguments: Diccionario con argumentos de la función
        
    Returns:
        Tupla (es_valido, argumentos_validados, mensaje_error)
    """
    try:
        validated_args = InvoiceArguments(**arguments)
        
        # Validaciones adicionales
        if validated_args.customer_id <= 0:
            return False, None, "customer_id must be a positive integer"
        
        if not validated_args.items or len(validated_args.items) == 0:
            return False, None, "items list cannot be empty"
        
        # Validar estructura básica de items
        for i, item in enumerate(validated_args.items):
            if not isinstance(item, dict):
                return False, None, f"Item {i} must be an object"
            
            required_fields = ['product_id', 'quantity', 'unit_price']
            for field in required_fields:
                if field not in item:
                    return False, None, f"Item {i} missing required field: {field}"
        
        return True, validated_args, ""
        
    except ValidationError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.warning(error_msg)
        return False, None, error_msg
    
    except Exception as e:
        error_msg = f"Unexpected error validating arguments: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def build_conversation_prompt(user_message: str, history: list, context_type: str = "general") -> str:
    """
    Construye el prompt completo para enviar al modelo IA con contexto contable especializado
    
    Args:
        user_message: Mensaje actual del usuario (en inglés)
        history: Historial de conversación
        context_type: Tipo de contexto contable ('general', 'invoicing', 'accounting', 'reports')
        
    Returns:
        Prompt completo en inglés
    """
    
    # Definir contextos especializados
    context_prompts = {
        "general": """You are a helpful AI assistant for an accounting software system. You help users with accounting questions, financial management, and can perform accounting operations like creating invoices.

You specialize in:
- Double-entry bookkeeping principles
- Chart of accounts management
- Invoice and billing operations
- Financial reporting basics
- Tax accounting fundamentals
- Business expense tracking""",
        
        "invoicing": """You are an AI assistant specialized in invoice and billing operations for an accounting system. You excel at:
- Creating detailed invoices with proper formatting
- Understanding customer billing requirements
- Calculating taxes, discounts, and totals
- Managing product catalogs and pricing
- Payment terms and collection processes
- Invoice status tracking and follow-ups""",
        
        "accounting": """You are an AI assistant specialized in accounting operations and bookkeeping. You excel at:
- Journal entries and double-entry bookkeeping
- Account reconciliation procedures
- Financial statement preparation
- General ledger management
- Accounts receivable and payable
- Month-end and year-end closing procedures""",
        
        "reports": """You are an AI assistant specialized in financial reporting and analysis. You excel at:
- Generating profit & loss statements
- Balance sheet analysis
- Cash flow reporting
- Financial ratios and KPIs
- Budget vs actual analysis
- Tax reporting requirements"""
    }
    
    # Seleccionar el prompt base según el contexto
    base_prompt = context_prompts.get(context_type, context_prompts["general"])
    
    prompt_parts = [
        base_prompt,
        "",
        "IMPORTANT INSTRUCTION FOR INVOICE CREATION:",
        "If the user wants to create an invoice, respond ONLY with a JSON object:",
        "{",
        '  "name": "create_invoice",',
        '  "arguments": {',
        '    "customer_id": <number>,',
        '    "date": "<YYYY-MM-DD>",',
        '    "items": [',
        '      {',
        '        "product_id": <number>,',
        '        "quantity": <number>,',
        '        "unit_price": <number>',
        '      }',
        '    ],',
        '    "discount": <optional_number>,',
        '    "notes": "<optional_string>"',
        '  }',
        '}',
        "",
        "Otherwise, respond in clear, helpful language with specific accounting guidance.",
        "Always provide practical, actionable advice when possible.",
        "",
        "Conversation history:"
    ]
    
    # Añadir historial si existe
    if history:
        for msg in history[-5:]:  # Solo últimos 5 mensajes
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            prompt_parts.append(f"{role.capitalize()}: {content}")
    
    # Añadir mensaje actual
    prompt_parts.extend([
        f"User: {user_message}",
        "Assistant:"
    ])
    
    return "\n".join(prompt_parts)


def clean_response_text(response: str) -> str:
    """
    Limpia la respuesta eliminando prefijos comunes del modelo
    
    Args:
        response: Respuesta del modelo
        
    Returns:
        Respuesta limpia
    """
    # Remover prefijos comunes
    prefixes_to_remove = [
        "Assistant:",
        "AI:",
        "Bot:",
        "Response:"
    ]
    
    cleaned = response.strip()
    
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    return cleaned
