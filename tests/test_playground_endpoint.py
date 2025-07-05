"""
Test script specifically for Hugging Face Playground endpoint
Testing meta-llama/Llama-3.1-8B-Instruct via playground
"""
import asyncio
import httpx
import json
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

async def test_playground_endpoint():
    """Test the HF Playground endpoint specifically"""
    print("=== Testing Hugging Face Playground Endpoint ===")
    print(f"Model: meta-llama/Llama-3.1-8B-Instruct")
    print(f"Token: {settings.HUGGINGFACE_API_TOKEN[:15]}...")
    print()
    
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "NFe-Assistant/1.0"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Try the chat completions endpoint (ChatML format)
        print("1. Testing Chat Completions endpoint...")
        try:
            url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct/v1/chat/completions"
            
            payload = {
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant specialized in Brazilian NFe generation and tax consulting."
                    },
                    {
                        "role": "user", 
                        "content": "Hello, can you help me create a Brazilian NFe?"
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
            
            response = await client.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result:
                    content = result["choices"][0]["message"]["content"]
                    print(f"   ✅ Chat completion successful!")
                    print(f"   Generated: {content[:150]}...")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 2: Try the standard inference endpoint with chat formatting
        print("2. Testing Standard Inference with chat format...")
        try:
            url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
            
            # Format prompt in ChatML style for Llama
            chat_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant specialized in Brazilian NFe generation and tax consulting. You respond in Portuguese, Spanish, or English based on the user's language.<|eot_id|><|start_header_id|>user<|end_header_id|>

Olá, você pode me ajudar a criar uma NFe brasileira?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
            
            payload = {
                "inputs": chat_prompt,
                "parameters": {
                    "max_new_tokens": 300,
                    "temperature": 0.7,
                    "do_sample": True,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1,
                    "return_full_text": False
                }
            }
            
            response = await client.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Standard inference successful!")
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    generated_text = result.get("generated_text", "")
                else:
                    generated_text = str(result)
                    
                print(f"   Generated: {generated_text[:200]}...")
                
            elif response.status_code == 400:
                error_data = response.json()
                if "paused" in response.text.lower():
                    print(f"   ⚠️  Model is paused - needs manual restart")
                else:
                    print(f"   ❌ Bad request: {error_data}")
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 3: Try with simpler prompt format
        print("3. Testing with simple prompt format...")
        try:
            url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
            
            simple_prompt = "Generate a simple greeting in Portuguese:"
            
            payload = {
                "inputs": simple_prompt,
                "parameters": {
                    "max_new_tokens": 50,
                    "temperature": 0.5
                }
            }
            
            response = await client.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Simple prompt successful!")
                print(f"   Result: {json.dumps(result, indent=2)}")
            else:
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 4: Check model status
        print("4. Checking model status...")
        try:
            # Try to get model information
            model_url = "https://huggingface.co/api/models/meta-llama/Llama-3.1-8B-Instruct"
            response = await client.get(model_url)
            
            if response.status_code == 200:
                model_info = response.json()
                print(f"   ✅ Model info accessible")
                print(f"   Pipeline tag: {model_info.get('pipeline_tag')}")
                print(f"   Model ID: {model_info.get('id')}")
                print(f"   Private: {model_info.get('private', False)}")
                print(f"   Gated: {model_info.get('gated', False)}")
            else:
                print(f"   ❌ Cannot access model info: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 5: Try serverless inference endpoint
        print("5. Testing Serverless Inference endpoint...")
        try:
            url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
            
            # Wait for model to load option
            payload = {
                "inputs": "Hello world",
                "options": {
                    "wait_for_model": True
                },
                "parameters": {
                    "max_new_tokens": 20
                }
            }
            
            print("   Waiting for model to load...")
            response = await client.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()
        
        # Test 6: Try DeepSeek-R1-0528 model
        print("6. Testing DeepSeek-R1-0528 model...")
        try:
            url = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1-0528"
            
            # Test with NFe specific prompt in Portuguese
            deepseek_prompt = """Como especialista em NFe (Nota Fiscal Eletrônica) do Brasil, gere uma estrutura JSON básica para uma NFe com os seguintes dados:
- Emitente: Empresa ABC Ltda, CNPJ: 12.345.678/0001-90
- Destinatário: Cliente XYZ, CPF: 123.456.789-00
- Produto: Notebook Dell, valor: R$ 2.500,00
- ICMS: 18%

Responda apenas com o JSON estruturado."""
            
            payload = {
                "inputs": deepseek_prompt,
                "parameters": {
                    "max_new_tokens": 400,
                    "temperature": 0.3,
                    "do_sample": True,
                    "top_p": 0.9,
                    "return_full_text": False
                }
            }
            
            response = await client.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ DeepSeek-R1 successful!")
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    generated_text = result.get("generated_text", "")
                else:
                    generated_text = str(result)
                    
                print(f"   Generated NFe: {generated_text[:300]}...")
                
                # Check if response contains JSON
                if '{' in generated_text and '}' in generated_text:
                    print(f"   ✅ Contains JSON structure")
                else:
                    print(f"   ⚠️  No JSON structure detected")
                
            elif response.status_code == 400:
                if "paused" in response.text.lower():
                    print(f"   ⚠️  DeepSeek model is paused")
                else:
                    print(f"   ❌ Bad request: {response.text[:200]}")
            elif response.status_code == 404:
                print(f"   ❌ DeepSeek model not found")
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 7: Try DeepSeek with chat completions format
        print("7. Testing DeepSeek-R1 with chat completions...")
        try:
            url = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1-0528/v1/chat/completions"
            
            payload = {
                "model": "deepseek-ai/DeepSeek-R1-0528",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a specialized AI assistant for Brazilian NFe (Nota Fiscal Eletrônica) generation and tax consulting. You are trilingual and respond fluently in Portuguese, Spanish, and English."
                    },
                    {
                        "role": "user", 
                        "content": "Crie uma NFe básica para: Empresa ABC vendendo um notebook de R$ 2.500 para Cliente XYZ. Responda em JSON."
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.3
            }
            
            response = await client.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    print(f"   ✅ DeepSeek chat completion successful!")
                    print(f"   Generated: {content[:200]}...")
                else:
                    print(f"   ⚠️  Unexpected response format: {result}")
            else:
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 8: Check DeepSeek model info
        print("8. Checking DeepSeek model information...")
        try:
            model_url = "https://huggingface.co/api/models/deepseek-ai/DeepSeek-R1-0528"
            response = await client.get(model_url)
            
            if response.status_code == 200:
                model_info = response.json()
                print(f"   ✅ DeepSeek model info accessible")
                print(f"   Pipeline tag: {model_info.get('pipeline_tag')}")
                print(f"   Model ID: {model_info.get('id')}")
                print(f"   Private: {model_info.get('private', False)}")
                print(f"   Gated: {model_info.get('gated', False)}")
                print(f"   Downloads: {model_info.get('downloads', 0)}")
            else:
                print(f"   ❌ Cannot access DeepSeek model info: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_playground_endpoint())
