"""
Script de prueba para verificar la integración con OpenAI
"""
import asyncio
import logging
from app.services.openai_client import openai_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_openai_connection():
    """Prueba la conexión con OpenAI"""
    print("🧪 Probando conexión con OpenAI...")
    
    # Test de conexión básico
    if openai_client.test_connection():
        print("✅ Conexión con OpenAI exitosa")
    else:
        print("❌ Error en la conexión con OpenAI")
        return False
    
    return True


async def test_simple_chat():
    """Prueba un chat simple"""
    print("\n🧪 Probando chat simple...")
    
    prompt = "Hello, can you help me with accounting questions?"
    
    try:
        response = await openai_client.generate_response(prompt)
        if response:
            print(f"✅ Respuesta recibida: {response}")
            return True
        else:
            print("❌ No se recibió respuesta")
            return False
    except Exception as e:
        print(f"❌ Error en chat simple: {e}")
        return False


async def test_haiku_generation():
    """Reproduce el ejemplo del haiku del tutorial de OpenAI"""
    print("\n🧪 Probando generación de haiku sobre IA...")
    
    prompt = "write a haiku about ai"
    
    try:
        response = await openai_client.generate_response(prompt)
        if response:
            print(f"✅ Haiku generado:\n{response}")
            return True
        else:
            print("❌ No se pudo generar el haiku")
            return False
    except Exception as e:
        print(f"❌ Error generando haiku: {e}")
        return False


async def test_invoice_function_call():
    """Prueba la funcionalidad de creación de facturas"""
    print("\n🧪 Probando llamada a función de factura...")
    
    prompt = "Create an invoice for customer ID 123 with one item: Product A, quantity 2, price $50 each, for today's date"
    
    try:
        response = await openai_client.generate_response(prompt)
        if response:
            print(f"✅ Respuesta de función: {response}")
            # Verificar si contiene la llamada a función
            if "<function_call>" in response and "create_invoice" in response:
                print("✅ Función de factura detectada correctamente")
            else:
                print("⚠️ Respuesta recibida pero sin función de factura")
            return True
        else:
            print("❌ No se recibió respuesta para función de factura")
            return False
    except Exception as e:
        print(f"❌ Error en función de factura: {e}")
        return False


async def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de integración con OpenAI")
    print("=" * 50)
    
    tests = [
        ("Conexión básica", test_openai_connection),
        ("Chat simple", test_simple_chat),
        ("Generación de haiku", test_haiku_generation),
        ("Función de factura", test_invoice_function_call)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE RESULTADOS:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado final: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! OpenAI está funcionando correctamente.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa la configuración.")


if __name__ == "__main__":
    asyncio.run(main())
