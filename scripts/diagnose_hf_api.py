#!/usr/bin/env python3
"""
Script para diagnosticar problemas con la API de Hugging Face
"""
import asyncio
import httpx
import logging
import os
import sys

# Agregar el directorio de la aplicación al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_hf_api_basic():
    """Diagnóstico básico de la API de Hugging Face"""
    
    print("🔍 Diagnóstico de API de Hugging Face")
    print("=" * 50)
    
    # Verificar token
    token = settings.HUGGINGFACE_API_TOKEN
    print(f"Token: {token[:10]}...{token[-5:] if len(token) > 15 else ''}")
    print(f"Longitud del token: {len(token)}")
    print()
    
    # Headers básicos
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Probar endpoint básico de información
        print("1. Probando endpoint de información básica...")
        try:
            response = await client.get(
                "https://huggingface.co/api/whoami",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Usuario: {data.get('name', 'Desconocido')}")
                print(f"   ✅ Tipo: {data.get('type', 'Desconocido')}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Excepción: {e}")
        
        print()
        
        # 2. Probar modelos que definitivamente existen
        print("2. Probando modelos básicos conocidos...")
        basic_models = [
            "gpt2",
            "microsoft/DialoGPT-medium", 
            "google/flan-t5-small",
            "facebook/blenderbot_small-90M"
        ]
        
        for model in basic_models:
            try:
                url = f"https://api-inference.huggingface.co/models/{model}"
                payload = {
                    "inputs": "Hello",
                    "parameters": {"max_new_tokens": 10}
                }
                
                response = await client.post(url, headers=headers, json=payload)
                print(f"   {model}:")
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"     ✅ Funciona!")
                    result = response.json()
                    print(f"     Respuesta: {result}")
                elif response.status_code == 503:
                    print(f"     ⏳ Modelo cargándose...")
                elif response.status_code == 404:
                    print(f"     ❌ No encontrado")
                else:
                    print(f"     ❌ Error: {response.text}")
                    
            except Exception as e:
                print(f"     ❌ Excepción: {e}")
        
        print()
        
        # 3. Probar los modelos específicos que queremos usar
        print("3. Probando modelos específicos requeridos...")
        target_models = [
            "bigscience/bloomz-7b1-mt",
            "meta-llama/Llama-2-7b-chat-hf",
            "TheBloke/Llama-2-7B-Chat-AWQ"
        ]
        
        for model in target_models:
            try:
                # Primero verificar si el modelo existe usando la API de modelos
                info_url = f"https://huggingface.co/api/models/{model}"
                info_response = await client.get(info_url)
                
                print(f"   {model}:")
                print(f"     Info API Status: {info_response.status_code}")
                
                if info_response.status_code == 200:
                    print(f"     ✅ Modelo existe")
                    model_info = info_response.json()
                    print(f"     Pipeline tag: {model_info.get('pipeline_tag', 'N/A')}")
                    print(f"     Privado: {model_info.get('private', False)}")
                    
                    # Ahora probar inference
                    inference_url = f"https://api-inference.huggingface.co/models/{model}"
                    payload = {"inputs": "Hello", "parameters": {"max_new_tokens": 10}}
                    
                    inference_response = await client.post(
                        inference_url, 
                        headers=headers, 
                        json=payload
                    )
                    print(f"     Inference Status: {inference_response.status_code}")
                    
                    if inference_response.status_code == 200:
                        print(f"     ✅ Inference funciona!")
                    elif inference_response.status_code == 503:
                        print(f"     ⏳ Modelo cargándose...")
                    elif inference_response.status_code == 401:
                        print(f"     🔒 Acceso denegado - puede requerir permiso especial")
                    else:
                        print(f"     ❌ Error inference: {inference_response.text}")
                        
                elif info_response.status_code == 404:
                    print(f"     ❌ Modelo no existe")
                else:
                    print(f"     ❌ Error info: {info_response.text}")
                    
            except Exception as e:
                print(f"     ❌ Excepción: {e}")
        
        print()
        
        # 4. Buscar modelos alternativos disponibles
        print("4. Buscando modelos alternativos disponibles...")
        alternative_models = [
            "microsoft/DialoGPT-small",
            "microsoft/DialoGPT-medium",
            "google/flan-t5-base",
            "huggingface/CodeBERTa-small-v1",
            "EleutherAI/gpt-neo-1.3B",
            "EleutherAI/gpt-neo-2.7B"
        ]
        
        working_models = []
        
        for model in alternative_models:
            try:
                url = f"https://api-inference.huggingface.co/models/{model}"
                payload = {"inputs": "Hello", "parameters": {"max_new_tokens": 20}}
                
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    working_models.append(model)
                    print(f"   ✅ {model} - FUNCIONA")
                elif response.status_code == 503:
                    print(f"   ⏳ {model} - Cargándose")
                else:
                    print(f"   ❌ {model} - Error {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {model} - Excepción: {e}")
        
        print()
        print(f"🎯 Modelos que funcionan: {working_models}")
        
        if working_models:
            print("\n5. Probando el primer modelo funcional...")
            test_model = working_models[0]
            try:
                url = f"https://api-inference.huggingface.co/models/{test_model}"
                payload = {
                    "inputs": "Create an invoice for John Doe",
                    "parameters": {"max_new_tokens": 50, "temperature": 0.7}
                }
                
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Respuesta de {test_model}:")
                    print(f"   {result}")
                else:
                    print(f"   ❌ Error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error probando {test_model}: {e}")


async def main():
    """Función principal"""
    try:
        await test_hf_api_basic()
    except Exception as e:
        logger.error(f"Error en diagnóstico: {e}")
        print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    asyncio.run(main())
