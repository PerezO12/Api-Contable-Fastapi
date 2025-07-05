"""
Test basic public models that should be available without special permissions
"""
import asyncio
import httpx
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

async def test_basic_models():
    """Test very basic public models"""
    print("=== Testing Basic Public Models ===")
    
    # Very basic models that should be publicly available
    basic_models = [
        "distilbert-base-uncased",
        "bert-base-uncased",
        "gpt2",
        "distilgpt2",
        "t5-small",
        "google/flan-t5-small",
        "google/flan-t5-base"
    ]
    
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Also test without token (public access)
    headers_no_token = {
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for model in basic_models:
            print(f"Testing {model}:")
            
            # Test with token first
            try:
                url = f"https://api-inference.huggingface.co/models/{model}"
                
                # For text generation models
                if "gpt" in model or "t5" in model or "flan" in model:
                    payload = {
                        "inputs": "Hello world",
                        "parameters": {"max_new_tokens": 10}
                    }
                else:
                    # For other models, try text classification
                    payload = {
                        "inputs": "Hello world"
                    }
                
                print(f"  With token: ", end="")
                response = await client.post(url, json=payload, headers=headers)
                print(f"{response.status_code} - {response.text[:100]}")
                
                print(f"  Without token: ", end="")
                response2 = await client.post(url, json=payload, headers=headers_no_token)
                print(f"{response2.status_code} - {response2.text[:100]}")
                
            except Exception as e:
                print(f"  Error: {e}")
            
            print()
    
    # Test if we can access model info without making inference
    print("=== Testing Model Info Endpoint ===")
    for model in ["gpt2", "distilgpt2"]:
        try:
            url = f"https://huggingface.co/api/models/{model}"
            print(f"Model info for {model}: ", end="")
            response = await client.get(url)
            print(f"{response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Pipeline tag: {data.get('pipeline_tag')}")
                print(f"  Task: {data.get('task')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_models())
