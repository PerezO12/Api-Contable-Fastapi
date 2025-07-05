"""
Test different Hugging Face API endpoints and approaches
"""
import asyncio
import httpx
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

async def test_endpoints():
    """Test different HF endpoints"""
    print("=== Testing Hugging Face Endpoints ===")
    print(f"Token: {settings.HUGGINGFACE_API_TOKEN[:20]}...")
    print()
    
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Check if token is valid by accessing user info
        print("1. Testing token validity...")
        try:
            response = await client.get("https://huggingface.co/api/whoami", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                user_info = response.json()
                print(f"   ✅ Token valid - User: {user_info.get('name', 'Unknown')}")
                print(f"   User type: {user_info.get('type', 'Unknown')}")
                print(f"   Plan: {user_info.get('plan', 'Unknown')}")
            else:
                print(f"   ❌ Token invalid: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 2: List available models for inference
        print("2. Testing models list endpoint...")
        try:
            response = await client.get("https://huggingface.co/api/models?filter=text-generation&limit=10")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                models = response.json()
                print(f"   ✅ Found {len(models)} models")
                for i, model in enumerate(models[:5]):
                    print(f"   {i+1}. {model.get('id', 'Unknown ID')}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 3: Try Serverless Inference with a simple model
        print("3. Testing Serverless Inference with microsoft/DialoGPT-medium...")
        try:
            url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            payload = {"inputs": "Hello"}
            
            response = await client.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 4: Try with a definitely available model (GPT2)
        print("4. Testing with GPT2...")
        try:
            url = "https://api-inference.huggingface.co/models/gpt2"
            payload = {
                "inputs": "The future of AI is",
                "parameters": {"max_length": 50}
            }
            
            response = await client.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 5: Try accessing a specific working model from HF Hub
        print("5. Testing specific models from HuggingFace Hub...")
        test_models = [
            "bigscience/bloom-560m",
            "EleutherAI/gpt-neo-125M",
            "facebook/opt-125m"
        ]
        
        for model in test_models:
            try:
                url = f"https://api-inference.huggingface.co/models/{model}"
                payload = {
                    "inputs": "Hello",
                    "parameters": {"max_new_tokens": 10}
                }
                
                response = await client.post(url, json=payload, headers=headers)
                print(f"   {model}: {response.status_code}")
                if response.status_code != 404:
                    print(f"      Response: {response.text[:100]}")
            except Exception as e:
                print(f"   {model}: Error - {e}")
        
        print()
        
        # Test 6: Try the HF Inference Endpoints API (different from Inference API)
        print("6. Testing Inference Endpoints API...")
        try:
            response = await client.get("https://api.endpoints.huggingface.cloud/", headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
