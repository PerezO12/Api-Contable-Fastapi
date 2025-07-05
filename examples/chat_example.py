"""
Ejemplo de uso del servicio de chat con IA
"""
import asyncio
import httpx
import json

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
CHAT_ENDPOINT = f"{BASE_URL}/ai/chat"
HEALTH_ENDPOINT = f"{BASE_URL}/ai/chat/health"
TEST_TRANSLATION_ENDPOINT = f"{BASE_URL}/ai/chat/test-translation"


async def test_chat_health():
    """Prueba el endpoint de salud del chat"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(HEALTH_ENDPOINT)
            print("=== Estado del Servicio de Chat ===")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error probando salud del chat: {e}")
            return False


async def test_translation():
    """Prueba el servicio de traducción"""
    async with httpx.AsyncClient() as client:
        try:
            # Probar con diferentes idiomas
            test_texts = [
                "Hola, ¿cómo estás?",  # Español
                "Olá, como você está?",  # Portugués
                "Hello, how are you?"   # Inglés
            ]
            
            print("=== Prueba de Traducción ===")
            for text in test_texts:
                response = await client.post(
                    TEST_TRANSLATION_ENDPOINT,
                    params={"text": text}
                )
                if response.status_code == 200:
                    result = response.json()
                    print(f"\nTexto original: {result['original_text']}")
                    print(f"Idioma detectado: {result['detected_language']}")
                    print(f"Traducción al inglés: {result['english_translation']}")
                    print(f"Traducción de vuelta: {result['back_translation']}")
                else:
                    print(f"Error traduciendo '{text}': {response.status_code}")
                    
        except Exception as e:
            print(f"Error probando traducción: {e}")


async def test_chat_conversation():
    """Prueba una conversación de chat completa"""
    async with httpx.AsyncClient() as client:
        
        print("=== Conversación de Chat ===")
        
        # Historial de conversación
        history = []
        
        # Mensajes de prueba
        test_messages = [
            "Hola, ¿puedes ayudarme?",
            "¿Qué puedes hacer por mí?",
            "Quiero crear una factura para el cliente con ID 123, con fecha 2024-01-15, que incluya el producto ID 456, cantidad 2, precio unitario 100.50",
            "Gracias por tu ayuda"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Mensaje {i} ---")
            print(f"Usuario: {message}")
            
            # Preparar request
            chat_request = {
                "user_message": message,
                "history": history
            }
            
            try:
                response = await client.post(
                    CHAT_ENDPOINT,
                    json=chat_request,
                    timeout=60.0  # Timeout más largo para respuestas de IA
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_response = result["content"]
                    print(f"Asistente: {assistant_response}")
                    
                    # Actualizar historial
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": assistant_response})
                    
                else:
                    print(f"Error en chat: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"Error enviando mensaje: {e}")
            
            # Pausa entre mensajes
            await asyncio.sleep(1)


async def main():
    """Función principal de pruebas"""
    print("🤖 Iniciando pruebas del servicio de chat con IA\n")
    
    # 1. Probar salud del servicio
    health_ok = await test_chat_health()
    
    if not health_ok:
        print("❌ El servicio de chat no está disponible")
        return
    
    print("\n" + "="*50 + "\n")
    
    # 2. Probar traducción
    await test_translation()
    
    print("\n" + "="*50 + "\n")
    
    # 3. Probar conversación completa
    await test_chat_conversation()
    
    print("\n🎉 Pruebas completadas")


if __name__ == "__main__":
    asyncio.run(main())
