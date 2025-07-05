"""
Test the modern models we found in the models list endpoint
"""
import asyncio
import httpx
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

async def test_modern_models():
    """Test the modern models from the API models list"""
    print("=== Testing Modern Models from HF Models List ===")
    
    # These are models we saw in the /api/models endpoint earlier
    modern_models = [
        "tencent/Hunyuan-A13B-Instruct",
        "maya-research/Veena", 
        "Menlo/Jan-nano-128k",
        "AIDC-AI/Ovis-U1-3B",
        "baidu/ERNIE-4.5-21B-A3B-PT",
        
        # Some other likely available models
        "microsoft/phi-2",
        "microsoft/DialoGPT-medium",
        "google/gemma-2b",
        "google/gemma-7b",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "HuggingFaceH4/zephyr-7b-beta",
        
        # Translation models (we know these work)
        "Helsinki-NLP/opus-mt-en-es",
        "Helsinki-NLP/opus-mt-en-pt",
        "Helsinki-NLP/opus-mt-es-en",
        "Helsinki-NLP/opus-mt-pt-en"
    ]
    
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    working_text_gen_models = []
    working_translation_models = []
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        for i, model in enumerate(modern_models, 1):
            print(f"{i:2d}. Testing {model}...")
            
            try:
                url = f"https://api-inference.huggingface.co/models/{model}"
                
                # Use different prompts based on model type
                if "opus-mt" in model:
                    # Translation model
                    if "en-es" in model:
                        payload = {"inputs": "Hello, how are you today?"}
                    elif "en-pt" in model:
                        payload = {"inputs": "Hello, how are you today?"}
                    elif "es-en" in model:
                        payload = {"inputs": "Hola, ¿cómo estás hoy?"}
                    elif "pt-en" in model:
                        payload = {"inputs": "Olá, como você está hoje?"}
                    else:
                        payload = {"inputs": "Hello world"}
                else:
                    # Text generation model
                    payload = {
                        "inputs": "Hello, I am an AI assistant that helps with",
                        "parameters": {
                            "max_new_tokens": 50,
                            "temperature": 0.7,
                            "do_sample": True
                        }
                    }
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"    ✅ WORKING")
                    
                    if "opus-mt" in model:
                        working_translation_models.append(model)
                        print(f"       Translation: {result}")
                    else:
                        working_text_gen_models.append(model)
                        print(f"       Generated: {str(result)[:100]}...")
                        
                elif response.status_code == 503:
                    print(f"    ⚠️  Loading (503) - waiting...")
                    await asyncio.sleep(5)
                    
                    # Retry once
                    response2 = await client.post(url, json=payload, headers=headers)
                    if response2.status_code == 200:
                        result = response2.json()
                        print(f"    ✅ WORKING (after wait)")
                        
                        if "opus-mt" in model:
                            working_translation_models.append(model)
                        else:
                            working_text_gen_models.append(model)
                            print(f"       Generated: {str(result)[:100]}...")
                    else:
                        print(f"    ⚠️  Still unavailable: {response2.status_code}")
                        
                elif response.status_code == 400:
                    if "paused" in response.text.lower():
                        print(f"    ❌ PAUSED")
                    elif "gated" in response.text.lower():
                        print(f"    ❌ GATED (requires approval)")
                    else:
                        print(f"    ❌ Bad Request: {response.text[:150]}")
                        
                elif response.status_code == 404:
                    print(f"    ❌ NOT FOUND")
                    
                elif response.status_code == 401:
                    print(f"    ❌ UNAUTHORIZED")
                    
                else:
                    print(f"    ❌ Error {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"    ❌ Exception: {str(e)[:100]}")
                
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    print()
    print("=== RESULTS ===")
    print(f"✅ Working Text Generation Models ({len(working_text_gen_models)}):")
    for model in working_text_gen_models:
        print(f"   - {model}")
    
    print(f"\n✅ Working Translation Models ({len(working_translation_models)}):")
    for model in working_translation_models:
        print(f"   - {model}")
    
    if working_text_gen_models:
        print(f"\n🎯 BEST OPTION FOR NFE:")
        print(f"Primary model: {working_text_gen_models[0]}")
        if len(working_text_gen_models) > 1:
            print(f"Fallback models: {working_text_gen_models[1:3]}")
            
        # Test NFe generation with the best model
        print(f"\n=== Testing NFe with {working_text_gen_models[0]} ===")
        await test_nfe_with_model(working_text_gen_models[0], client, headers)
        
    elif working_translation_models:
        print(f"\n⚠️  Only translation models available.")
        print(f"Can be used for multilingual support but not for NFe generation.")
        
    else:
        print(f"\n❌ No working models found!")
        print(f"Recommendation: Use the alternative AI client as primary.")

async def test_nfe_with_model(model_name: str, client: httpx.AsyncClient, headers: dict):
    """Test NFe generation capabilities"""
    try:
        url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        # NFe prompt in Portuguese
        nfe_prompt = """Como especialista em NFe brasileira, crie uma estrutura JSON para:
Emitente: ABC Ltda, CNPJ: 12.345.678/0001-90
Cliente: João Silva, CPF: 123.456.789-00
Produto: Notebook, R$ 2.500

JSON da NFe:"""

        payload = {
            "inputs": nfe_prompt,
            "parameters": {
                "max_new_tokens": 400,
                "temperature": 0.3,
                "do_sample": True
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as test_client:
            response = await test_client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ NFe generation test successful!")
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    generated_text = result.get("generated_text", "")
                else:
                    generated_text = str(result)
                    
                print(f"Generated NFe response:")
                print(f"{generated_text[:500]}...")
                
                # Check if it looks like JSON
                if "{" in generated_text and "}" in generated_text:
                    print(f"✅ Response contains JSON structure")
                else:
                    print(f"⚠️  Response doesn't contain clear JSON")
                    
            else:
                print(f"❌ NFe test failed: {response.status_code} - {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ NFe test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_modern_models())
