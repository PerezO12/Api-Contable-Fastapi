"""
Test script to verify the new Hugging Face token and model access
Testing meta-llama/Llama-3.1-8B-Instruct for NFe generation
"""
import asyncio
import json
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.hf_client import HuggingFaceClient
from app.config import settings

async def test_token_and_model():
    """Test the new token with meta-llama/Llama-3.1-8B-Instruct"""
    print("=== Testing New HuggingFace Token ===")
    print(f"Token: {settings.HUGGINGFACE_API_TOKEN[:10]}...")
    print(f"Primary Model: meta-llama/Llama-3.1-8B-Instruct")
    print("")
    
    client = HuggingFaceClient()
    
    # Test 1: Simple text generation
    print("1. Testing simple text generation...")
    try:
        response = await client.generate_response("Hello, how are you today?")
        if response:
            print(f"✅ Simple generation successful:")
            print(f"   Response: {response[:100]}...")
        else:
            print(f"❌ No response received")
    except Exception as e:
        print(f"❌ Simple generation error: {e}")
    
    print("")
    
    # Test 2: NFe specific test (Portuguese)
    print("2. Testing NFe generation (Portuguese)...")
    nfe_prompt = """Como especialista em NFe (Nota Fiscal Eletrônica) do Brasil, gere uma estrutura JSON básica para uma NFe com os seguintes dados:
- Emitente: Empresa ABC Ltda, CNPJ: 12.345.678/0001-90
- Destinatário: Cliente XYZ, CPF: 123.456.789-00
- Produto: Notebook Dell, valor: R$ 2.500,00
- ICMS: 18%

Responda apenas com o JSON estruturado."""
    
    try:
        response = await client.generate_response(nfe_prompt)
        if response:
            print(f"✅ NFe generation successful:")
            print(f"   Response length: {len(response)} characters")
            print(f"   First 200 chars: {response[:200]}...")
            
            # Try to parse as JSON
            try:
                if '{' in response and '}' in response:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    json_part = response[json_start:json_end]
                    json_data = json.loads(json_part)
                    print(f"   ✅ Valid JSON structure found and parsed")
                else:
                    print(f"   ⚠️  Response does not contain JSON structure")
            except json.JSONDecodeError:
                print(f"   ⚠️  JSON found but not valid")
        else:
            print(f"❌ No NFe response received")
            
    except Exception as e:
        print(f"❌ NFe generation error: {e}")
    
    print("")
    
    # Test 3: Multilingual test (Spanish)
    print("3. Testing multilingual support (Spanish)...")
    spanish_prompt = """Como experto en facturación electrónica, explica brevemente qué es una NFe brasileña y cuáles son sus principales elementos. Responde en español."""
    
    try:
        response = await client.generate_response(spanish_prompt)
        if response:
            print(f"✅ Spanish response successful:")
            print(f"   Response: {response[:150]}...")
        else:
            print(f"❌ No Spanish response received")
    except Exception as e:
        print(f"❌ Spanish response error: {e}")
    
    print("")
    
    # Test 4: English test
    print("4. Testing English support...")
    english_prompt = """As an expert in Brazilian electronic invoicing, briefly explain what is an NFe and list its main components. Answer in English."""
    
    try:
        response = await client.generate_response(english_prompt)
        if response:
            print(f"✅ English response successful:")
            print(f"   Response: {response[:150]}...")
        else:
            print(f"❌ No English response received")
    except Exception as e:
        print(f"❌ English response error: {e}")
    
    print("")
    
    # Test 5: Model availability check
    print("5. Testing direct model endpoint...")
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as test_client:
            url = f"https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
            payload = {
                "inputs": "Hello",
                "parameters": {"max_new_tokens": 10}
            }
            
            response = await test_client.post(url, json=payload, headers=headers)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Direct model access successful")
                print(f"   Response type: {type(result)}")
            elif response.status_code == 401:
                print(f"❌ Unauthorized - Token issue")
            elif response.status_code == 503:
                print(f"⚠️  Model loading or unavailable")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Direct model test error: {e}")
    
    print("")
    print("=== Test Completed ===")

if __name__ == "__main__":
    asyncio.run(test_token_and_model())
