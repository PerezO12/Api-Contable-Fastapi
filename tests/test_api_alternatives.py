#!/usr/bin/env python3
"""
Script para probar la Inference API sin token y con diferentes URLs
"""
import asyncio
import httpx
import json


async def test_inference_api_alternatives():
    """Prueba diferentes configuraciones de la Inference API"""
    
    print("🔧 Probando alternativas de la Inference API")
    print("=" * 50)
    
    # URLs a probar
    base_urls = [
        "https://api-inference.huggingface.co/models",
        "https://huggingface.co/api/models",  # URL alternativa
        "https://api.huggingface.co/models"   # URL alternativa
    ]
    
    # Modelos simples para probar
    test_models = [
        "gpt2",
        "distilgpt2",
        "microsoft/DialoGPT-small"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        for base_url in base_urls:
            print(f"\n🌐 Probando URL base: {base_url}")
            
            for model in test_models:
                full_url = f"{base_url}/{model}"
                
                # Probar sin token
                print(f"   📝 {model} (sin token):")
                try:
                    payload = {
                        "inputs": "Hello world",
                        "parameters": {
                            "max_new_tokens": 5,
                            "temperature": 0.7
                        }
                    }
                    
                    response = await client.post(full_url, json=payload)
                    
                    print(f"      Status: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        print(f"      ✅ Éxito: {str(result)[:100]}...")
                        return full_url.replace(f"/{model}", ""), model  # Devolver URL base exitosa
                    elif response.status_code == 503:
                        print(f"      ⏳ Modelo cargándose...")
                    elif response.status_code == 401:
                        print(f"      🔒 Token requerido")
                    else:
                        print(f"      ❌ Error: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"      ❌ Excepción: {e}")
        
        print(f"\n🚫 Ninguna configuración funcionó")
        
        # Última prueba: verificar si la API está funcionando para otros
        print(f"\n🔍 Verificando estado general de HF...")
        try:
            response = await client.get("https://status.huggingface.co/api/v2/summary.json")
            if response.status_code == 200:
                status = response.json()
                print(f"   Estado HF: {status.get('status', {}).get('description', 'Desconocido')}")
            else:
                print(f"   No se pudo verificar estado: {response.status_code}")
        except:
            print(f"   No se pudo conectar al status de HF")


async def test_gradio_alternatives():
    """Prueba APIs alternativas como Gradio Spaces"""
    
    print(f"\n🎭 Probando alternativas Gradio...")
    
    # Algunos spaces públicos que podrían funcionar
    gradio_urls = [
        "https://huggingface.co/spaces/microsoft/DialoGPT-medium/api/predict",
        "https://huggingface.co/spaces/huggingface/ChatGPT-like/api/predict"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in gradio_urls:
            try:
                payload = {
                    "data": ["Hello, how are you?"]
                }
                
                response = await client.post(url, json=payload)
                print(f"   {url}: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"      ✅ Gradio funciona: {str(result)[:100]}...")
                    return url
                    
            except Exception as e:
                print(f"   ❌ {url}: {e}")
    
    return None


async def main():
    working_url = await test_inference_api_alternatives()
    
    if not working_url:
        gradio_url = await test_gradio_alternatives()
        
        if gradio_url:
            print(f"\n💡 Sugerencia: Usar Gradio Space como alternativa")
        else:
            print(f"\n🤔 Recomendaciones:")
            print(f"   1. Verificar conectividad a huggingface.co")
            print(f"   2. Usar un VPN si hay restricciones regionales")
            print(f"   3. Considerar usar la API de OpenAI como alternativa")
            print(f"   4. Verificar si HF Inference API está en mantenimiento")


if __name__ == "__main__":
    asyncio.run(main())
