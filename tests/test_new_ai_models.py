#!/usr/bin/env python3
"""
Script para probar los nuevos modelos de IA implementados
"""
import asyncio
import logging
import os
import sys

# Agregar el directorio de la aplicación al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.hf_client import hf_client
from app.services.translation import translation_service
from app.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_models():
    """Prueba los modelos de IA implementados"""
    
    print("🧪 Probando nuevos modelos de IA")
    print("=" * 50)
    
    # Verificar configuración
    print(f"Token configurado: {settings.HUGGINGFACE_API_TOKEN[:10]}...")
    print(f"Modelo principal: {hf_client.model_name}")
    print(f"Modelos fallback: {hf_client.fallback_models}")
    print()
    
    # 1. Probar disponibilidad de modelos
    print("1. Verificando disponibilidad de modelos...")
    models_to_check = [hf_client.model_name] + hf_client.fallback_models[:3]  # Solo los primeros 3
    
    for model in models_to_check:
        health = await hf_client.check_model_health(model)
        status_icon = "✅" if health["available"] else "❌"
        error_msg = health.get("error", "Sin error específico")
        status_msg = "Disponible" if health["available"] else f"No disponible - {error_msg}"
        print(f"   {status_icon} {model}: {status_msg}")
    
    print()
    
    # 2. Encontrar modelo disponible
    print("2. Buscando modelo disponible...")
    available_model = await hf_client.find_available_model()
    if available_model:
        print(f"   ✅ Modelo recomendado: {available_model}")
    else:
        print("   ❌ No se encontró ningún modelo disponible")
        return
    
    print()
    
    # 3. Probar generación básica
    print("3. Probando generación básica...")
    test_prompt = "Hello, how can I help you today?"
    
    try:
        response = await hf_client.generate_with_retry(test_prompt)
        if response and response.strip():
            print(f"   ✅ Respuesta recibida: {response[:100]}...")
        else:
            print("   ❌ No se recibió respuesta válida")
    except Exception as e:
        print(f"   ❌ Error en generación: {e}")
    
    print()
    
    # 4. Probar generación multilingüe (si estamos usando BloomZ)
    if "bloomz" in available_model.lower():
        print("4. Probando capacidades multilingües de BloomZ...")
        
        multilingual_prompts = [
            "Hola, ¿cómo estás?",
            "Olá, como você está?", 
            "Bonjour, comment allez-vous?"
        ]
        
        for prompt in multilingual_prompts:
            try:
                response = await hf_client.generate_response(prompt)
                print(f"   📝 '{prompt}' -> '{response[:80] if response else 'Sin respuesta'}...'")
            except Exception as e:
                print(f"   ❌ Error con '{prompt}': {e}")
    
    print()
    
    # 5. Probar generación con formato de factura
    print("5. Probando generación con instrucciones de factura...")
    invoice_prompt = "Create an invoice for John Doe with 1 laptop for $500"
    
    try:
        invoice_response = await hf_client.generate_response_with_invoice_support(invoice_prompt)
        if invoice_response:
            print(f"   ✅ Respuesta de factura: {invoice_response[:150]}...")
            
            # Verificar si contiene JSON
            if "create_invoice" in invoice_response and "{" in invoice_response:
                print("   🎯 ¡Formato JSON detectado!")
            else:
                print("   ℹ️  Respuesta conversacional (no JSON)")
        else:
            print("   ❌ No se recibió respuesta para factura")
    except Exception as e:
        print(f"   ❌ Error en generación de factura: {e}")
    
    print()
    
    # 6. Probar integración con traducción
    print("6. Probando integración con traducción...")
    try:
        # Verificar que el servicio de traducción esté disponible
        if hasattr(translation_service, 'process_text'):
            test_spanish = "Crea una factura para María González"
            detected_lang, original, english = translation_service.process_text(test_spanish)
            print(f"   📋 Original: {original}")
            print(f"   🌍 Idioma detectado: {detected_lang}")
            print(f"   🔄 Traducido: {english}")
            
            # Respuesta de IA en inglés
            ai_response = await hf_client.generate_response_with_invoice_support(english)
            if ai_response:
                # Traducir de vuelta
                back_translated = translation_service.translate_from_english(ai_response[:100], detected_lang)
                print(f"   🤖 Respuesta IA: {ai_response[:80]}...")
                print(f"   🔄 De vuelta a {detected_lang}: {back_translated}")
            
        else:
            print("   ⚠️  Servicio de traducción no disponible")
            
    except Exception as e:
        print(f"   ❌ Error en integración de traducción: {e}")
    
    print()
    print("🎉 Prueba completada!")
    
    # Cerrar cliente HTTP
    await hf_client.close()


async def main():
    """Función principal"""
    try:
        await test_models()
    except KeyboardInterrupt:
        print("\n👋 Prueba cancelada por el usuario")
    except Exception as e:
        logger.error(f"Error en prueba principal: {e}")
        print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    asyncio.run(main())
