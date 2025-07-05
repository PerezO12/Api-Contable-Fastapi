#!/usr/bin/env python3
"""
Script para verificar y diagnosticar problemas del sistema de IA
"""
import os
import sys
import logging
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    dependencies = {
        'openai': 'openai',
        'langdetect': 'langdetect', 
        'transformers': 'transformers',
        'torch': 'torch',
        'sentencepiece': 'sentencepiece'
    }
    
    results = {}
    for name, module in dependencies.items():
        try:
            __import__(module)
            results[name] = "✅ Instalado"
        except ImportError as e:
            results[name] = f"❌ No instalado: {e}"
    
    return results

def check_openai_config():
    """Verifica la configuración de OpenAI"""
    try:
        from app.config import settings
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        if not api_key:
            return "❌ OPENAI_API_KEY no configurada"
        
        if api_key.startswith('sk-'):
            # Verificar que la clave no esté vencida o sin cuota
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                
                # Intentar una llamada simple para verificar la clave
                response = client.models.list()
                return "✅ Clave OpenAI válida"
                
            except Exception as e:
                if "insufficient_quota" in str(e):
                    return "⚠️ Clave válida pero sin cuota disponible"
                elif "invalid_api_key" in str(e):
                    return "❌ Clave OpenAI inválida"
                else:
                    return f"⚠️ Error verificando OpenAI: {e}"
        else:
            return "❌ Formato de clave OpenAI inválido"
            
    except Exception as e:
        return f"❌ Error verificando configuración: {e}"

def check_translation_service():
    """Verifica el servicio de traducción"""
    try:
        from app.services.translation import translation_service
        
        # Verificar detección de idioma
        lang = translation_service.detect_language("Hola mundo")
        if lang != 'es':
            return f"⚠️ Detección de idioma incorrecta: {lang}"
        
        # Intentar cargar pipelines
        if not translation_service.pipelines_loaded:
            translation_service._load_translation_pipelines()
        
        # Verificar traducción
        resultado = translation_service.translate_to_english("Hola mundo", "es")
        
        if resultado == "Hola mundo":
            return "⚠️ Traducción usando fallback (sin modelos)"
        else:
            return "✅ Traducción funcionando"
            
    except Exception as e:
        return f"❌ Error en servicio de traducción: {e}"

def check_huggingface_config():
    """Verifica la configuración de HuggingFace"""
    try:
        from app.config import settings
        token = getattr(settings, 'HUGGINGFACE_API_TOKEN', None)
        
        if not token:
            return "❌ HUGGINGFACE_API_TOKEN no configurada"
        
        if token.startswith('hf_'):
            return "✅ Token HuggingFace configurado"
        else:
            return "⚠️ Formato de token HuggingFace inválido"
            
    except Exception as e:
        return f"❌ Error verificando configuración HF: {e}"

def main():
    """Función principal de diagnóstico"""
    print("🔍 Diagnóstico del Sistema de IA")
    print("=" * 50)
    
    # Verificar dependencias
    print("\n📦 Dependencias:")
    deps = check_dependencies()
    for name, status in deps.items():
        print(f"  {name}: {status}")
    
    # Verificar OpenAI
    print(f"\n🤖 OpenAI: {check_openai_config()}")
    
    # Verificar HuggingFace
    print(f"\n🤗 HuggingFace: {check_huggingface_config()}")
    
    # Verificar traducción
    print(f"\n🌐 Traducción: {check_translation_service()}")
    
    print("\n" + "=" * 50)
    print("✅ Diagnóstico completado")
    
    # Sugerencias
    print("\n💡 Sugerencias:")
    
    missing_deps = [name for name, status in deps.items() if "❌" in status]
    if missing_deps:
        print(f"  - Instalar dependencias faltantes: pip install {' '.join(missing_deps)}")
    
    openai_status = check_openai_config()
    if "sin cuota" in openai_status:
        print("  - Verificar cuota de OpenAI en https://platform.openai.com/account/usage")
        print("  - Agregar créditos a la cuenta de OpenAI")
    
    if "fallback" in check_translation_service():
        print("  - Los modelos T5 no están cargados, verificar instalación de transformers y torch")

if __name__ == "__main__":
    main()
