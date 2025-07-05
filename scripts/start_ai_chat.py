#!/usr/bin/env python3
"""
Script de inicio y verificación del servicio de chat con IA
"""
import asyncio
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    required_packages = [
        'fastapi',
        'transformers', 
        'torch',
        'langdetect',
        'httpx',
        'sqlalchemy',
        'asyncpg'
    ]
    
    missing_packages = []
    
    print("🔍 Verificando dependencias...")
    
    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing_packages.append(package)
            print(f"❌ {package} - No instalado")
        else:
            print(f"✅ {package} - Instalado")
    
    if missing_packages:
        print(f"\n⚠️ Faltan dependencias: {', '.join(missing_packages)}")
        print("Instalar con: pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True


def check_environment():
    """Verifica la configuración del entorno"""
    import os
    
    print("\n🔍 Verificando configuración del entorno...")
    
    # Variables críticas
    critical_vars = {
        'HUGGINGFACE_API_TOKEN': os.getenv('HUGGINGFACE_API_TOKEN', 'hf_exampletoken123'),
        'SQLALCHEMY_DATABASE_URI': os.getenv('SQLALCHEMY_DATABASE_URI', 'No configurado')
    }
    
    issues = []
    
    for var, value in critical_vars.items():
        if var == 'HUGGINGFACE_API_TOKEN':
            if value == 'hf_exampletoken123':
                print(f"⚠️ {var} - Usando token de ejemplo")
                issues.append(f"Configurar {var} con tu token real de Hugging Face")
            else:
                print(f"✅ {var} - Configurado")
        
        elif var == 'SQLALCHEMY_DATABASE_URI':
            if value == 'No configurado':
                print(f"⚠️ {var} - No configurado")
                issues.append(f"Configurar {var} con tu URL de base de datos")
            else:
                print(f"✅ {var} - Configurado")
    
    if issues:
        print("\n⚠️ Problemas de configuración encontrados:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nLa aplicación iniciará pero algunos servicios pueden no funcionar correctamente.")
    
    return len(issues) == 0


async def test_ai_services():
    """Prueba los servicios de IA"""
    print("\n🤖 Probando servicios de IA...")
    
    try:
        # Test de traducción
        from app.services.translation import translation_service
        
        test_text = "Hola mundo"
        detected_lang, original, english = translation_service.process_text(test_text)
        
        print(f"✅ Traducción funcionando:")
        print(f"   Original: {original}")
        print(f"   Idioma detectado: {detected_lang}")
        print(f"   Traducción: {english}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en servicios de IA: {e}")
        return False


def start_server():
    """Inicia el servidor FastAPI"""
    print("\n🚀 Iniciando servidor FastAPI...")
    print("📍 URL: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("🤖 Chat Health: http://localhost:8000/api/v1/ai/chat/health")
    print("\nPresiona Ctrl+C para detener el servidor\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")


async def main():
    """Función principal"""
    print("🤖 Iniciando verificación del servicio de chat con IA\n")
    
    # 1. Verificar dependencias
    if not check_dependencies():
        print("\n❌ No se puede continuar sin las dependencias necesarias")
        sys.exit(1)
    
    # 2. Verificar entorno
    env_ok = check_environment()
    
    # 3. Probar servicios de IA (opcional si hay problemas de entorno)
    if env_ok:
        ai_ok = await test_ai_services()
        if not ai_ok:
            print("⚠️ Los servicios de IA pueden tener problemas, pero el servidor iniciará")
    
    # 4. Preguntar si iniciar servidor
    print("\n" + "="*60)
    response = input("¿Iniciar el servidor FastAPI? (y/N): ").strip().lower()
    
    if response in ['y', 'yes', 'sí', 's']:
        start_server()
    else:
        print("✅ Verificación completada. Usa 'uvicorn app.main:app --reload' para iniciar manualmente.")


if __name__ == "__main__":
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)
    
    # Añadir al PYTHONPATH
    sys.path.insert(0, str(script_dir))
    
    asyncio.run(main())
