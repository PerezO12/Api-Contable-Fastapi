"""
Script to discover available Hugging Face models and test endpoints
"""
import asyncio
import httpx
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

async def test_models():
    """Test various Hugging Face models to find working ones"""
    print("=== Testing Hugging Face Model Availability ===")
    print(f"Token: {settings.HUGGINGFACE_API_TOKEN[:10]}...")
    print("")
    
    # List of popular models to test
    test_models = [
        # Meta Llama models
        "meta-llama/Llama-3.2-1B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct", 
        "meta-llama/Llama-3.1-8B-Instruct",
        "meta-llama/Llama-2-7b-chat-hf",
        "meta-llama/CodeLlama-7b-Instruct-hf",
        
        # Microsoft models
        "microsoft/DialoGPT-medium",
        "microsoft/DialoGPT-large",
        
        # Google models
        "google/flan-t5-large",
        "google/flan-t5-xl",
        
        # Hugging Face models
        "HuggingFaceH4/zephyr-7b-beta",
        "HuggingFaceH4/zephyr-7b-alpha",
        
        # Mistral models
        "mistralai/Mistral-7B-Instruct-v0.1",
        "mistralai/Mistral-7B-Instruct-v0.2",
        
        # Other popular models
        "bigscience/bloom-7b1",
        "bigscience/bloomz-7b1",
        "EleutherAI/gpt-j-6B",
        "EleutherAI/gpt-neo-2.7B",
        "gpt2",
        "gpt2-medium",
        "gpt2-large",
        "facebook/opt-1.3b",
        "facebook/opt-2.7b"
    ]
    
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    working_models = []
    paused_models = []
    unauthorized_models = []
    not_found_models = []
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for i, model in enumerate(test_models, 1):
            print(f"{i:2d}. Testing {model}...")
            
            try:
                url = f"https://api-inference.huggingface.co/models/{model}"
                payload = {
                    "inputs": "Hello, test message",
                    "parameters": {"max_new_tokens": 10}
                }
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    print(f"    ✅ WORKING")
                    working_models.append(model)
                elif response.status_code == 503:
                    print(f"    ⚠️  Loading (503)")
                    # Sometimes 503 means the model is loading, let's try once more
                    await asyncio.sleep(2)
                    response2 = await client.post(url, json=payload, headers=headers)
                    if response2.status_code == 200:
                        print(f"    ✅ WORKING (after retry)")
                        working_models.append(model)
                    else:
                        print(f"    ⚠️  Still loading/unavailable")
                elif response.status_code == 400:
                    error_text = response.text
                    if "paused" in error_text.lower():
                        print(f"    ❌ PAUSED")
                        paused_models.append(model)
                    else:
                        print(f"    ❌ Bad Request: {error_text[:100]}")
                elif response.status_code == 401:
                    print(f"    ❌ UNAUTHORIZED")
                    unauthorized_models.append(model)
                elif response.status_code == 404:
                    print(f"    ❌ NOT FOUND")
                    not_found_models.append(model)
                else:
                    print(f"    ❌ Error {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"    ❌ Exception: {e}")
    
    print("")
    print("=== RESULTS SUMMARY ===")
    print(f"✅ WORKING MODELS ({len(working_models)}):")
    for model in working_models:
        print(f"   - {model}")
    
    print(f"\n⚠️  PAUSED MODELS ({len(paused_models)}):")
    for model in paused_models:
        print(f"   - {model}")
    
    print(f"\n❌ UNAUTHORIZED MODELS ({len(unauthorized_models)}):")
    for model in unauthorized_models:
        print(f"   - {model}")
        
    print(f"\n❌ NOT FOUND MODELS ({len(not_found_models)}):")
    for model in not_found_models:
        print(f"   - {model}")
        
    print("")
    if working_models:
        print("RECOMMENDED CONFIGURATION:")
        print(f"Primary model: {working_models[0]}")
        print("Fallback models:", working_models[1:5] if len(working_models) > 1 else [])
    else:
        print("⚠️ No working models found! Check your token permissions or try again later.")

if __name__ == "__main__":
    asyncio.run(test_models())
