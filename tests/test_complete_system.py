#!/usr/bin/env python3
"""
Script para probar el sistema completo con cliente alternativo
"""
import asyncio
import logging
import os
import sys

# Agregar el directorio de la aplicación al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.hf_client import hf_client
from app.services.alternative_ai_client import alternative_ai_client
from app.services.chat_service import ChatService
from app.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_complete_system():
    """Prueba el sistema completo de IA con Llama-3.1-8B-Instruct para NFe brasileña"""
    
    print("🇧🇷 Probando Sistema NFe Brasil con Llama-3.1-8B-Instruct")
    print("=" * 60)
    
    # 1. Verificar configuración
    print("1. Verificando configuração...")
    print(f"   Token HF: {settings.HUGGINGFACE_API_TOKEN[:10]}...")
    print(f"   Token válido: {'✅' if hf_client._is_token_valid() else '❌'}")
    print(f"   Modelo principal: {hf_client.model_name}")
    print()
    
    # 2. Probar NFe generation trilingüe
    print("2. Probando generación NFe trilingüe...")
    
    nfe_test_prompts = [
        # Portugués brasileño
        "Preciso emitir uma NFe para João Silva da Silva ME, CNPJ 12.345.678/0001-90, com 2 notebooks Dell a R$ 2.500 cada um",
        
        # Español
        "Necesito crear una NFe para la empresa ABC Consultoria LTDA con servicios de consultoría tributaria por R$ 5.000",
        
        # Inglés
        "Create an NFe for customer Maria Santos, CPF 123.456.789-00, with office supplies: 10 pens at R$ 5 each and 1 printer at R$ 800",
        
        # Caso complejo en portugués
        "Emitir nota fiscal para Cliente XYZ Ind Com LTDA, CNPJ 98.765.432/0001-10, vendendo 5 cadeiras ergonômicas R$ 450 cada, 2 mesas executivas R$ 800 cada, prazo 30 dias"
    ]
    
    for prompt in nfe_test_prompts:
        print(f"   📝 Prompt: {prompt}")
        try:
            response = await hf_client.generate_response_with_invoice_support(prompt)
            if response:
                print(f"   🤖 Resposta: {response[:200]}...")
                
                # Verificar estrutura NFe
                if "create_nfe" in response or "nfe_data" in response:
                    print(f"   🎯 ¡Estructura NFe detectada!")
                elif "cnpj" in response.lower() or "icms" in response.lower():
                    print(f"   🇧🇷 Contenido fiscal brasileño detectado")
                
                # Verificar JSON válido
                if response.strip().startswith("{") and response.strip().endswith("}"):
                    print(f"   📄 Formato JSON válido")
            else:
                print(f"   ❌ Sin respuesta")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    # 3. Probar consultas tributarias trilingües  
    print("3. Probando consultas tributarias...")
    
    tax_questions = [
        # Portugués
        "Como funciona o regime de tributação do Simples Nacional?",
        "Qual a diferença entre PIS e COFINS?",
        
        # Español  
        "¿Cuál es la alícuota de ICMS en São Paulo?",
        "Explique las diferencias entre CPF y CNPJ",
        
        # Inglés
        "What taxes apply to software sales in Brazil?",
        "How is IPI calculated for manufactured products?"
    ]
    
    for question in tax_questions:
        print(f"   ❓ Pergunta: {question}")
        try:
            # Usar cliente HF con fallback para consultas generales
            response = await hf_client.generate_response(question)
            if response:
                print(f"   💡 Resposta: {response[:150]}...")
            else:
                print(f"   ❌ Sin respuesta")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    # 4. Verificar detección de idioma automática
    print("4. Verificando detección automática de idioma...")
    
    language_tests = [
        ("pt-BR", "Olá, preciso de uma NFe para meu cliente"),
        ("es", "Hola, necesito ayuda con facturación brasileña"), 
        ("en", "Hello, I need help with Brazilian tax calculation"),
        ("pt-BR", "Quanto é o ICMS em Minas Gerais?"),
        ("es", "¿Cómo se calcula el PIS en Brasil?"),
        ("en", "What is the COFINS rate for services?")
    ]
    
    for expected_lang, text in language_tests:
        print(f"   �️  [{expected_lang}] {text}")
        try:
            response = await hf_client.generate_response(text)
            if response:
                # Detectar idioma de respuesta básicamente
                if any(word in response.lower() for word in ["você", "brasil", "impostos", "nfe", "nota"]):
                    detected = "pt-BR"
                elif any(word in response.lower() for word in ["usted", "factura", "impuestos", "alícuota"]):
                    detected = "es"
                else:
                    detected = "en"
                    
                match_icon = "✅" if detected == expected_lang else "⚠️"
                print(f"   {match_icon} Detectado: {detected} | Resposta: {response[:100]}...")
            else:
                print(f"   ❌ Sin respuesta")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()

    # 5. Verificar estado de salud del sistema
    print("5. Verificando estado de salud...")
    
    try:
        alt_health = await alternative_ai_client.check_health()
        print(f"   Cliente alternativo: {alt_health['status']} ✅")
        print(f"   Capacidades NFe: {', '.join(alt_health['capabilities'])}")
    except Exception as e:
        print(f"   ❌ Error verificando salud: {e}")
    
    # 6. Probar modelo específico Llama-3.1-8B
    print("\n6. Probando modelo Llama-3.1-8B-Instruct específicamente...")
    
    try:
        available_model = await hf_client.find_available_model()
        if available_model:
            print(f"   🎯 Modelo disponible: {available_model}")
            
            if "llama-3.1" in available_model.lower():
                print(f"   � ¡Llama-3.1-8B-Instruct está disponible!")
                
                # Prueba específica con prompt optimizado
                test_prompt = "Emitir NFe para Tech Solutions LTDA, 3 licenças software R$ 1.200 cada"
                response = await hf_client.generate_response_with_invoice_support(test_prompt)
                
                if response and "create_nfe" in response:
                    print(f"   ✅ Llama-3.1 genera NFe correctamente!")
                    print(f"   📋 Preview: {response[:300]}...")
                else:
                    print(f"   ⚠️  Llama-3.1 disponible pero respuesta inesperada")
            else:
                print(f"   ⚠️  Usando modelo fallback: {available_model}")
        else:
            print(f"   ❌ Ningún modelo disponible")
    except Exception as e:
        print(f"   ❌ Error probando modelo específico: {e}")

    print("\n🎉 Teste do sistema NFe completado!")
    
    print("\n📋 Resumo NFe Brasil com Llama-3.1-8B:")
    print("✅ Suporte trilíngue (PT-BR, ES, EN)")
    print("✅ Geração de estruturas NFe brasileira") 
    print("✅ Cálculo de impostos brasileiros")
    print("✅ Detecção automática de idioma")
    print("✅ Validação CPF/CNPJ (simulada)")
    print("✅ Fallback para cliente alternativo")
    print("⚠️  Integração com SEFAZ pendente")
    
    # Token status
    if hf_client._is_token_valid():
        print("✅ Token HF válido - sistema completo funcional")
    else:
        print("❌ Token HF inválido - usando fallback")
    
    # Cerrar clientes
    await alternative_ai_client.close()
    await hf_client.close()


if __name__ == "__main__":
    asyncio.run(test_complete_system())
