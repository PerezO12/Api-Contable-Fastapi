#!/usr/bin/env python3
"""
Script para probar el sistema de fallback mejorado
"""
import asyncio
import sys
import os

# Agregar el directorio de la aplicación al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.fallback_ai_client import fallback_client

async def test_fallback():
    """Prueba el sistema de fallback con diferentes mensajes"""
    
    test_messages = [
        "hola, en que puedes ayudarme",
        "probando como funciona esto",
        "qué es una factura",
        "cómo crear una factura",
        "explícame la partida doble",
        "qué reportes puedo generar",
        "ayuda con cuentas",
        "hello, how can you help",
        "olá, em que pode me ajudar"
    ]
    
    print("🧪 Probando sistema de fallback mejorado")
    print("=" * 50)
    
    for message in test_messages:
        print(f"\n📝 Mensaje: '{message}'")
        
        # Probar detección de idioma
        detected_lang = fallback_client._detect_language(message)
        print(f"🌐 Idioma detectado: {detected_lang}")
        
        # Generar respuesta
        response = await fallback_client.generate_response(message)
        if response:
            print(f"🤖 Respuesta: {response[:100]}...")
        else:
            print("🤖 Respuesta: Sin respuesta")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_fallback())
