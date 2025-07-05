#!/usr/bin/env python3
"""
Script para probar el sistema de chat IA mejorado
"""
import asyncio
import sys
import os

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chat_service import ChatService
from app.database import get_async_db


async def test_chat_system():
    """Prueba el sistema de chat con diferentes escenarios"""
    
    print("🤖 Probando Sistema de Chat IA Mejorado")
    print("=" * 50)
    
    # Mensajes de prueba
    test_messages = [
        {
            "message": "Hola, ¿de qué trata este sistema?",
            "language": None,
            "context": "general",
            "description": "Pregunta general en español"
        },
        {
            "message": "How do I create an invoice for customer 123?",
            "language": "en",
            "context": "invoicing", 
            "description": "Pregunta sobre facturas en inglés"
        },
        {
            "message": "¿Qué es la partida doble en contabilidad?",
            "language": "es",
            "context": "accounting",
            "description": "Concepto contable en español"
        },
        {
            "message": "Como gerar um relatório de fluxo de caixa?",
            "language": "pt",
            "context": "reports",
            "description": "Pregunta sobre reportes en portugués"
        }
    ]
    
    # Simular sesión de base de datos
    async for db in get_async_db():
        for i, test in enumerate(test_messages, 1):
            print(f"\n📝 Prueba {i}: {test['description']}")
            print(f"💬 Mensaje: {test['message']}")
            print(f"🌐 Idioma: {test['language'] or 'Auto-detección'}")
            print(f"📋 Contexto: {test['context']}")
            print("-" * 30)
            
            try:
                response = await ChatService.process_chat_message(
                    user_message=test['message'],
                    history=[],
                    db=db,
                    preferred_language=test['language'],
                    context_type=test['context']
                )
                
                print(f"✅ Respuesta:")
                print(f"   Contenido: {response['content'][:200]}...")
                print(f"   Idioma detectado: {response.get('detected_language', 'N/A')}")
                print(f"   Idioma respuesta: {response.get('response_language', 'N/A')}")
                print(f"   Contexto usado: {response.get('context_used', 'N/A')}")
                print(f"   Función ejecutada: {response.get('function_executed', False)}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print()
        
        break  # Solo usar la primera sesión de DB


if __name__ == "__main__":
    print("Iniciando pruebas del sistema de chat IA...")
    asyncio.run(test_chat_system())
    print("\n✅ Pruebas completadas!")
