#!/usr/bin/env python3
"""
Script para probar modelos sin token de autenticación
"""
import asyncio
import httpx
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_without_token():
    """Probar modelos sin token de autenticación"""
    
    print("🔓 Probando modelos SIN token de autenticación")
    print("=" * 50)
    
    # Headers sin token
    headers = {
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Modelos públicos que pueden funcionar sin token
        public_models = [
            "gpt2",
            "distilgpt2", 
            "microsoft/DialoGPT-small",
            "google/flan-t5-small",
            "facebook/blenderbot_small-90M",
            "bigscience/bloom-560m",
            "EleutherAI/gpt-neo-125M"
        ]
        
        working_models = []
        
        for model in public_models:
            try:
                url = f"https://api-inference.huggingface.co/models/{model}"
                payload = {
                    "inputs": "Hello, how are you?",
                    "parameters": {
                        "max_new_tokens": 20,
                        "temperature": 0.7
                    }
                }
                
                print(f"Probando: {model}")
                response = await client.post(url, headers=headers, json=payload)
                
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    working_models.append(model)
                    print(f"  ✅ FUNCIONA!")
                    print(f"  Respuesta: {result}")
                elif response.status_code == 503:
                    # Modelo cargándose, esperemos un poco
                    print(f"  ⏳ Modelo cargándose, esperando...")
                    await asyncio.sleep(5)
                    
                    # Segundo intento
                    response2 = await client.post(url, headers=headers, json=payload)
                    if response2.status_code == 200:
                        result = response2.json()
                        working_models.append(model)
                        print(f"  ✅ FUNCIONA después de esperar!")
                        print(f"  Respuesta: {result}")
                    else:
                        print(f"  ❌ Sigue sin funcionar: {response2.status_code}")
                        
                elif response.status_code == 401:
                    print(f"  🔒 Requiere autenticación")
                elif response.status_code == 404:
                    print(f"  ❌ No encontrado")
                else:
                    print(f"  ❌ Error: {response.text}")
                    
                print()
                
            except Exception as e:
                print(f"  ❌ Excepción: {e}")
                print()
        
        print("=" * 50)
        print(f"🎯 MODELOS QUE FUNCIONAN SIN TOKEN: {working_models}")
        
        if working_models:
            print(f"\n✅ ¡Encontramos {len(working_models)} modelos que funcionan!")
            print("Podemos usar estos modelos mientras solucionamos el problema del token.")
            
            # Probar el primer modelo con un prompt más complejo
            test_model = working_models[0]
            print(f"\n🧪 Probando {test_model} con prompt complejo...")
            
            try:
                url = f"https://api-inference.huggingface.co/models/{test_model}"
                complex_payload = {
                    "inputs": "Create an invoice for customer John Doe with the following items: 1 laptop for $500, 2 mice for $25 each. Total should be $550.",
                    "parameters": {
                        "max_new_tokens": 100,
                        "temperature": 0.7,
                        "do_sample": True
                    }
                }
                
                response = await client.post(url, headers=headers, json=complex_payload)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Respuesta compleja exitosa:")
                    print(f"{result}")
                else:
                    print(f"❌ Error con prompt complejo: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error probando prompt complejo: {e}")
        else:
            print("\n❌ No encontramos modelos que funcionen sin token.")
            print("Necesitamos definitivamente un token válido de Hugging Face.")


async def main():
    """Función principal"""
    try:
        await test_without_token()
        
        print("\n" + "=" * 50)
        print("📋 INSTRUCCIONES PARA SOLUCIONAR:")
        print("1. Ve a https://huggingface.co/settings/tokens")
        print("2. Crea un nuevo token con permisos de 'Read'")
        print("3. Actualiza el archivo .env o config.py con el nuevo token")
        print("4. Ejecuta nuevamente las pruebas")
        
    except Exception as e:
        logger.error(f"Error en prueba sin token: {e}")
        print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    asyncio.run(main())
