"""
Find working Llama and other language models on Hugging Face
"""
import asyncio
import httpx
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

async def find_working_models():
    """Find working models on HuggingFace"""
    print("=== Finding Working Language Models ===")
    
    # Alternative models to test - focusing on open and available ones
    candidate_models = [
        # Open Llama alternatives
        "microsoft/DialoGPT-medium",
        "microsoft/DialoGPT-large", 
        "facebook/blenderbot-400M-distill",
        "facebook/blenderbot-1B-distill",
        
        # Smaller models that are usually available
        "gpt2",
        "gpt2-medium", 
        "distilgpt2",
        "EleutherAI/gpt-neo-125M",
        "EleutherAI/gpt-neo-1.3B",
        
        # Instruction-tuned models
        "google/flan-t5-small",
        "google/flan-t5-base",
        "google/flan-t5-large",
        
        # Other open models
        "bigscience/bloom-560m",
        "bigscience/bloom-1b1",
        "bigscience/bloomz-560m",
        
        # Recent open models
        "microsoft/DialoGPT-small",
        "facebook/opt-125m",
        "facebook/opt-350m",
        "facebook/opt-1.3b",
        
        # Code models (often available)
        "Salesforce/codegen-350M-mono",
        "microsoft/CodeGPT-small-py",
        
        # Chat models
        "togethercomputer/RedPajama-INCITE-Chat-3B-v1",
        "togethercomputer/RedPajama-INCITE-7B-Chat",
        
        # Multilingual models
        "Helsinki-NLP/opus-mt-en-pt",
        "Helsinki-NLP/opus-mt-en-es"
    ]
    
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    working_models = []
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for i, model in enumerate(candidate_models, 1):
            print(f"{i:2d}. Testing {model}...")
            
            try:
                url = f"https://api-inference.huggingface.co/models/{model}"
                
                # Use appropriate payload based on model type
                if "flan-t5" in model or "t5" in model:
                    payload = {
                        "inputs": "translate English to Portuguese: Hello, how are you?",
                        "parameters": {"max_new_tokens": 50}
                    }
                elif "opus-mt" in model:
                    payload = {
                        "inputs": "Hello, how are you?"
                    }
                elif "codegen" in model or "CodeGPT" in model:
                    payload = {
                        "inputs": "def hello():",
                        "parameters": {"max_new_tokens": 30}
                    }
                else:
                    payload = {
                        "inputs": "Hello, I need help with",
                        "parameters": {
                            "max_new_tokens": 30,
                            "temperature": 0.7
                        }
                    }
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"    ✅ WORKING - Response: {str(result)[:80]}...")
                    working_models.append(model)
                    
                elif response.status_code == 503:
                    print(f"    ⚠️  Loading (503) - trying again...")
                    # Wait and retry once
                    await asyncio.sleep(3)
                    response2 = await client.post(url, json=payload, headers=headers)
                    if response2.status_code == 200:
                        result = response2.json()
                        print(f"    ✅ WORKING (after retry) - Response: {str(result)[:80]}...")
                        working_models.append(model)
                    else:
                        print(f"    ⚠️  Still loading/unavailable")
                        
                elif response.status_code == 400:
                    if "paused" in response.text.lower():
                        print(f"    ❌ PAUSED")
                    else:
                        print(f"    ❌ Bad Request: {response.text[:100]}")
                        
                elif response.status_code == 404:
                    print(f"    ❌ NOT FOUND")
                    
                elif response.status_code == 401:
                    print(f"    ❌ UNAUTHORIZED")
                    
                else:
                    print(f"    ❌ Error {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"    ❌ Exception: {str(e)[:100]}")
    
    print()
    print("=== WORKING MODELS FOUND ===")
    if working_models:
        for i, model in enumerate(working_models, 1):
            print(f"{i}. {model}")
            
        print()
        print("RECOMMENDED UPDATE FOR hf_client.py:")
        print(f"Primary model: {working_models[0]}")
        if len(working_models) > 1:
            print(f"Fallback models: {working_models[1:]}")
            
        # Test the best working model with NFe prompt
        print()
        print("=== Testing Best Model with NFe Prompt ===")
        await test_nfe_generation(working_models[0], client, headers)
        
    else:
        print("❌ No working models found!")
        print("This suggests either:")
        print("1. Token permissions issue")
        print("2. API endpoint problems") 
        print("3. All tested models are currently unavailable")

async def test_nfe_generation(model_name: str, client: httpx.AsyncClient, headers: dict):
    """Test NFe generation with a working model"""
    print(f"Testing NFe generation with {model_name}...")
    
    try:
        url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        nfe_prompt = """You are a Brazilian tax expert. Create a simple NFe (Nota Fiscal Eletrônica) JSON structure for:
- Emitente: ABC Company, CNPJ: 12.345.678/0001-90
- Cliente: John Silva, CPF: 123.456.789-00  
- Product: Laptop, Price: R$ 2000

Respond with JSON structure:"""

        payload = {
            "inputs": nfe_prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.5
            }
        }
        
        response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ NFe test successful!")
            
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                generated_text = result.get("generated_text", "")
            else:
                generated_text = str(result)
                
            print(f"Generated response: {generated_text[:300]}...")
        else:
            print(f"❌ NFe test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ NFe test error: {e}")

if __name__ == "__main__":
    asyncio.run(find_working_models())
