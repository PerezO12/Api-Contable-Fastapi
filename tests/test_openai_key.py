"""
Script simple para probar la API key de OpenAI
"""
import asyncio
import os
import sys
from openai import AsyncOpenAI

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


async def test_openai_key():
    """Prueba simple de la API key de OpenAI"""
    print("🔑 Probando API Key de OpenAI...")
    print("=" * 50)
    
    # Mostrar configuración (parcial por seguridad)
    if settings.OPENAI_API_KEY:
        masked_key = settings.OPENAI_API_KEY[:7] + "..." + settings.OPENAI_API_KEY[-4:]
        print(f"🔧 API Key: {masked_key}")
    else:
        print("❌ API Key no configurada")
        return
    
    print(f"🤖 Modelo: {settings.OPENAI_MODEL}")
    print()
    
    try:
        # Crear cliente con timeout más corto para prueba
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=15.0,  # 15 segundos para prueba
            max_retries=1
        )
        
        print("📡 Enviando petición de prueba...")
        
        # Mensaje muy simple
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Responde en una palabra en español."},
                {"role": "user", "content": "Di 'hola'"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        if response.choices:
            message = response.choices[0].message.content
            print(f"✅ Respuesta recibida: {message}")
            if response.usage:
                print(f"🔢 Tokens usados: {response.usage.total_tokens}")
            print(f"🎯 Modelo usado: {response.model}")
            print("\n🎉 ¡API Key funciona correctamente!")
        else:
            print("❌ No se recibió respuesta")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
        # Diagnóstico del error
        error_str = str(e).lower()
        if "invalid api key" in error_str or "unauthorized" in error_str:
            print("\n🔍 Diagnóstico: API Key inválida")
            print("   - Verifica que la clave esté correcta")
            print("   - Asegúrate de que no haya espacios extra")
            print("   - Confirma que la clave no haya expirado")
        elif "quota" in error_str or "billing" in error_str:
            print("\n🔍 Diagnóstico: Problema de facturación/cuota")
            print("   - Verifica tu cuenta de OpenAI")
            print("   - Confirma que tengas créditos disponibles")
        elif "timeout" in error_str:
            print("\n🔍 Diagnóstico: Problema de conexión")
            print("   - Verifica tu conexión a internet")
            print("   - Puede ser un problema temporal de OpenAI")
        elif "rate limit" in error_str:
            print("\n🔍 Diagnóstico: Límite de velocidad excedido")
            print("   - Espera un momento y vuelve a intentar")
        else:
            print(f"\n🔍 Diagnóstico: Error desconocido")
            print(f"   - Error completo: {e}")


if __name__ == "__main__":
    asyncio.run(test_openai_key())
