"""
Script de prueba para verificar la integración con OpenAI
"""
import asyncio
import sys
import os

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.openai_service import openai_service
from app.services.hybrid_chat_service import hybrid_chat_service
from app.config import settings


async def test_openai_integration():
    """Prueba la integración completa con OpenAI"""
    print("🧪 Probando integración con OpenAI...")
    print("=" * 50)
    
    # Verificar configuración
    print(f"🔧 Configuración:")
    print(f"   - Modelo: {settings.OPENAI_MODEL}")
    print(f"   - Max Tokens: {settings.OPENAI_MAX_TOKENS}")
    print(f"   - Temperature: {settings.OPENAI_TEMPERATURE}")
    print(f"   - API Key configurada: {'✅' if settings.OPENAI_API_KEY else '❌'}")
    print()
    
    # Verificar servicios
    print(f"🔍 Estado de servicios:")
    print(f"   - OpenAI disponible: {'✅' if openai_service.is_available() else '❌'}")
    print(f"   - Fallback disponible: {'✅' if hybrid_chat_service.fallback_service.test_connection() else '❌'}")
    print()
    
    # Mensajes de prueba
    test_messages = [
        "Hola, ¿cómo funciona este sistema contable?",
        "How do I create an invoice in the accounting system?",
        "¿Qué es la partida doble en contabilidad?",
        "Explain the balance sheet components"
    ]
    
    print("💬 Probando mensajes de chat:")
    print("-" * 30)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Mensaje: {message}")
        
        try:
            # Probar con el servicio híbrido
            result = await hybrid_chat_service.generate_response(message)
            
            if result.get("success"):
                service_used = result.get("service_used", "unknown")
                response = result.get("message", "")
                
                print(f"   ✅ Servicio usado: {service_used}")
                print(f"   📝 Respuesta: {response[:150]}...")
                
                if result.get("tokens_used"):
                    tokens = result["tokens_used"]
                    print(f"   🔢 Tokens: {tokens.get('total_tokens', 'N/A')}")
                
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   💥 Excepción: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✨ Prueba completada!")


if __name__ == "__main__":
    asyncio.run(test_openai_integration())
