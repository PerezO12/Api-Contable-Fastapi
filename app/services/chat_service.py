"""
Servicio principal de chat con IA usando OpenAI
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.services.translation import translation_service
from app.services.openai_client import openai_client
from app.utils.chat_utils import (
    parse_ai_response, 
    validate_invoice_arguments, 
    build_conversation_prompt,
    clean_response_text
)

logger = logging.getLogger(__name__)


class ChatService:
    """Servicio principal para el chat con IA"""
    
    @staticmethod
    async def process_chat_message(
        user_message: str, 
        history: List[Dict[str, Any]], 
        db: AsyncSession,
        preferred_language: Optional[str] = None,
        context_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje de chat completo
        
        Args:
            user_message: Mensaje del usuario
            history: Historial de conversación
            db: Sesión de base de datos
            preferred_language: Idioma preferido ('es', 'en', 'pt') o None para detectar automáticamente
            context_type: Tipo de contexto contable ('general', 'invoicing', 'accounting', 'reports')
            
        Returns:
            Respuesta del asistente con metadatos
        """
        try:
            # 1. Determinar idioma: usar preferido o detectar automáticamente
            if preferred_language and preferred_language in ['es', 'en', 'pt']:
                detected_lang = preferred_language
                original_message = user_message
                if preferred_language == 'en':
                    english_message = user_message
                else:
                    # Traducir al inglés para procesamiento
                    english_message = translation_service.translate_to_english(user_message, preferred_language)
                    # Verificar si la traducción falló y usar el texto original
                    if not english_message or english_message == user_message or len(english_message.split()) < 3:
                        logger.warning("Traducción falló, usando texto original para procesamiento")
                        english_message = user_message
            else:
                # Detectar idioma automáticamente
                detected_lang, original_message, english_message = translation_service.process_text(user_message)
                # Verificar si la traducción falló
                if not english_message or english_message == user_message or "el sistema de el sistema" in english_message:
                    logger.warning("Traducción automática falló, usando texto original")
                    english_message = user_message
                # Verificar si realmente se tradujo
                if detected_lang != 'en' and english_message == original_message:
                    # Forzar traducción si no se realizó automáticamente
                    try:
                        english_message = translation_service.translate_to_english(user_message, detected_lang)
                    except Exception as e:
                        logger.warning(f"Error en traducción manual: {e}")
                        # Si falla la traducción, usar el mensaje original
                        english_message = user_message
            
            logger.info(f"Idioma determinado: {detected_lang}")
            logger.info(f"Mensaje original: {original_message}")
            logger.info(f"Mensaje en inglés: {english_message}")
            
            # 2. Construir prompt con contexto contable especializado
            prompt = build_conversation_prompt(english_message, history, context_type)
            logger.info(f"Prompt construido para contexto '{context_type}': {prompt[:200]}...")
            
            # 3. Enviar a OpenAI con reintentos automáticos
            ai_response = await openai_client.generate_with_retry(prompt)
            
            if ai_response is None or ai_response.strip() == "":
                # Error mejorado con más contexto
                error_response = "I'm sorry, I'm having trouble processing your request right now. Please try again in a few moments."
                translated_error = translation_service.translate_from_english(error_response, detected_lang)
                return {
                    "role": "assistant",
                    "content": translated_error,
                    "detected_language": detected_lang,
                    "response_language": detected_lang,
                    "context_used": context_type,
                    "function_executed": False
                }
            
            # 4. Limpiar respuesta
            cleaned_response = clean_response_text(ai_response)
            logger.info(f"Respuesta IA: {cleaned_response}")
            
            # 5. Parsear respuesta para detectar función
            is_function, function_call, response_text = parse_ai_response(cleaned_response)
            
            if is_function and function_call:
                # Es una llamada a función create_invoice
                logger.info("Procesando creación de factura...")
                
                # Validar argumentos
                is_valid, validated_args, error_msg = validate_invoice_arguments(function_call.arguments)
                
                if not is_valid:
                    error_response = f"I couldn't create the invoice due to validation errors: {error_msg}"
                    translated_error = translation_service.translate_from_english(error_response, detected_lang)
                    return {
                        "role": "assistant",
                        "content": translated_error,
                        "detected_language": detected_lang,
                        "response_language": detected_lang,
                        "context_used": context_type,
                        "function_executed": False
                    }
                
                # Crear factura en la base de datos
                try:
                    invoice_id = await ChatService._create_invoice_in_db(validated_args, db)
                    
                    success_response = f"Invoice {invoice_id} created successfully ✅"
                    translated_success = translation_service.translate_from_english(success_response, detected_lang)
                    
                    return {
                        "role": "assistant",
                        "content": translated_success,
                        "detected_language": detected_lang,
                        "response_language": detected_lang,
                        "context_used": context_type,
                        "function_executed": True
                    }
                    
                except Exception as e:
                    logger.error(f"Error creando factura en DB: {e}")
                    error_response = "I'm sorry, there was an error creating the invoice in the database."
                    translated_error = translation_service.translate_from_english(error_response, detected_lang)
                    return {
                        "role": "assistant",
                        "content": translated_error,
                        "detected_language": detected_lang,
                        "response_language": detected_lang,
                        "context_used": context_type,
                        "function_executed": False
                    }
            else:
                # Es texto normal, traducir de vuelta al idioma original
                translated_response = translation_service.translate_from_english(cleaned_response, detected_lang)
                
                return {
                    "role": "assistant",
                    "content": translated_response,
                    "detected_language": detected_lang,
                    "response_language": detected_lang,
                    "context_used": context_type,
                    "function_executed": False
                }
                
        except Exception as e:
            logger.error(f"Error procesando mensaje de chat: {e}")
            
            # Determinar idioma para respuesta de error
            try:
                error_lang = preferred_language if preferred_language else 'es'
                if not preferred_language:
                    # Intentar detectar idioma para el error
                    error_lang, _, _ = translation_service.process_text(user_message)
            except:
                error_lang = 'es'  # Fallback a español
            
            # Respuestas de error en diferentes idiomas
            error_messages = {
                'es': "Lo siento, ha ocurrido un error procesando tu mensaje. Por favor intenta de nuevo.",
                'en': "Sorry, an error occurred processing your message. Please try again.",
                'pt': "Desculpe, ocorreu um erro processando sua mensagem. Por favor, tente novamente."
            }
            
            fallback_response = error_messages.get(error_lang, error_messages['es'])
            
            return {
                "role": "assistant", 
                "content": fallback_response,
                "detected_language": error_lang,
                "response_language": error_lang,
                "context_used": context_type,
                "function_executed": False
            }
    
    @staticmethod
    async def _create_invoice_in_db(validated_args, db: AsyncSession) -> int:
        """
        Crea una factura en la base de datos
        
        Args:
            validated_args: Argumentos validados de la factura
            db: Sesión de base de datos
            
        Returns:
            ID de la factura creada
        """
        # NOTA: Esta es una implementación de ejemplo.
        # En un sistema real, aquí se usarían los modelos y servicios existentes
        # para crear la factura en la base de datos PostgreSQL.
        
        # Por ahora, simulamos la creación y retornamos un ID ficticio
        logger.info(f"Creando factura para customer_id: {validated_args.customer_id}")
        logger.info(f"Items: {validated_args.items}")
        logger.info(f"Fecha: {validated_args.date}")
        
        # TODO: Implementar creación real de factura usando:
        # - Modelos existentes de Invoice, InvoiceItem, etc.
        # - Servicios existentes como InvoiceService
        # - Validaciones de customer_id, product_ids, etc.
        
        # Simulamos ID de factura creada
        simulated_invoice_id = 12345
        
        return simulated_invoice_id
