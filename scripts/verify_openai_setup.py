"""
Script de prueba básico para verificar que el código OpenAI está bien estructurado
Sin hacer llamadas reales a la API
"""
from app.services.openai_client import openai_client
from openai import OpenAI

def test_imports_and_structure():
    """Verifica que las importaciones y estructura estén correctas"""
    print("🧪 Verificando importaciones y estructura...")
    
    try:
        # Verificar que el cliente se puede importar
        assert openai_client is not None
        print("✅ Cliente OpenAI importado correctamente")
        
        # Verificar que tiene los métodos necesarios
        assert hasattr(openai_client, 'generate_response')
        assert hasattr(openai_client, 'generate_with_retry')
        assert hasattr(openai_client, 'test_connection')
        print("✅ Métodos del cliente presentes")
        
        # Verificar que el cliente interno se puede instanciar
        assert hasattr(openai_client, 'client')
        assert isinstance(openai_client.client, OpenAI)
        print("✅ Cliente OpenAI interno configurado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en estructura: {e}")
        return False


def test_configuration():
    """Verifica que la configuración esté presente"""
    print("\n🧪 Verificando configuración...")
    
    try:
        from app.config import settings
        
        # Verificar que existe la clave de OpenAI
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert settings.OPENAI_API_KEY is not None
        assert len(settings.OPENAI_API_KEY) > 10  # Al menos parece una API key
        print("✅ API Key de OpenAI configurada")
        
        # Verificar que tiene los modelos configurados
        assert hasattr(openai_client, 'model_name')
        assert hasattr(openai_client, 'fallback_model')
        assert openai_client.model_name == "gpt-4o-mini"
        assert openai_client.fallback_model == "gpt-3.5-turbo"
        print("✅ Modelos configurados correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False


def test_chat_service_imports():
    """Verifica que el servicio de chat use OpenAI correctamente"""
    print("\n🧪 Verificando servicio de chat...")
    
    try:
        from app.services.chat_service import ChatService
        
        # Verificar que el archivo se puede importar sin errores
        assert ChatService is not None
        print("✅ ChatService importado correctamente")
        
        # Verificar que tiene el método principal
        assert hasattr(ChatService, 'process_chat_message')
        print("✅ Método process_chat_message presente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en ChatService: {e}")
        return False


def main():
    """Función principal de pruebas sin API"""
    print("🚀 Verificando integración OpenAI (sin llamadas a API)")
    print("=" * 50)
    
    tests = [
        ("Importaciones y estructura", test_imports_and_structure),
        ("Configuración", test_configuration),
        ("Servicio de chat", test_chat_service_imports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIÓN:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado final: {passed}/{total} verificaciones exitosas")
    
    if passed == total:
        print("🎉 ¡Toda la estructura está correcta! El código está listo para usar OpenAI.")
        print("\n💡 NOTA: Para usar completamente, necesitas:")
        print("   - Una API key válida de OpenAI con créditos disponibles")
        print("   - O configurar un plan de pago en OpenAI")
    else:
        print("⚠️ Algunas verificaciones fallaron. Revisa la estructura del código.")


if __name__ == "__main__":
    main()
