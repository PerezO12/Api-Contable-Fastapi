#!/usr/bin/env python3
"""
Script para configurar entorno virtual para el servicio de chat con IA
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def get_python_executable():
    """Encuentra el ejecutable de Python correcto"""
    python_commands = ['python3', 'python', 'py']
    
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, check=True)
            if 'Python 3.' in result.stdout:
                return cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    raise RuntimeError("No se encontró Python 3. Instalar Python 3.8+ primero.")

def create_virtual_environment():
    """Crea el entorno virtual"""
    print("🔧 Creando entorno virtual...")
    
    python_cmd = get_python_executable()
    venv_path = Path("venv_ai_chat")
    
    if venv_path.exists():
        print(f"⚠️ El entorno virtual {venv_path} ya existe.")
        response = input("¿Quieres recrearlo? (y/N): ").strip().lower()
        if response in ['y', 'yes', 'sí', 's']:
            import shutil
            shutil.rmtree(venv_path)
            print("🗑️ Entorno virtual anterior eliminado")
        else:
            return venv_path
    
    try:
        subprocess.run([python_cmd, '-m', 'venv', str(venv_path)], check=True)
        print(f"✅ Entorno virtual creado en: {venv_path}")
        return venv_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando entorno virtual: {e}")
        sys.exit(1)

def get_activation_command(venv_path):
    """Obtiene el comando de activación según el SO"""
    if platform.system() == "Windows":
        if os.path.exists("powershell.exe") or "powershell" in os.environ.get("SHELL", ""):
            return f"{venv_path}\\Scripts\\Activate.ps1"
        else:
            return f"{venv_path}\\Scripts\\activate.bat"
    else:
        return f"source {venv_path}/bin/activate"

def get_pip_executable(venv_path):
    """Obtiene la ruta del pip del entorno virtual"""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def install_dependencies(venv_path):
    """Instala las dependencias en el entorno virtual"""
    print("📦 Instalando dependencias...")
    
    pip_cmd = get_pip_executable(venv_path)
    
    # Actualizar pip primero
    try:
        subprocess.run([str(pip_cmd), 'install', '--upgrade', 'pip'], check=True)
        print("✅ pip actualizado")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error actualizando pip: {e}")
    
    # Instalar dependencias desde requirements.txt
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        try:
            subprocess.run([str(pip_cmd), 'install', '-r', str(requirements_file)], check=True)
            print("✅ Dependencias principales instaladas")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando dependencias: {e}")
            return False
    else:
        print("⚠️ Archivo requirements.txt no encontrado")
        
        # Instalar dependencias críticas manualmente
        critical_packages = [
            'fastapi>=0.115.0',
            'uvicorn[standard]>=0.34.0',
            'sqlalchemy>=2.0.0',
            'asyncpg>=0.30.0',
            'transformers>=4.46.0',
            'torch>=2.5.0',
            'langdetect>=1.0.9',
            'httpx>=0.28.0',
            'pydantic>=2.0.0',
            'python-multipart',
            'python-jose[cryptography]',
            'passlib[bcrypt]',
            'alembic>=1.16.0'
        ]
        
        for package in critical_packages:
            try:
                print(f"Instalando {package}...")
                subprocess.run([str(pip_cmd), 'install', package], check=True)
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Error instalando {package}: {e}")
    
    return True

def create_activation_scripts(venv_path):
    """Crea scripts de activación convenientes"""
    print("📝 Creando scripts de activación...")
    
    activation_cmd = get_activation_command(venv_path)
    
    # Script para Windows (PowerShell)
    if platform.system() == "Windows":
        ps_script = f"""
# Activar entorno virtual para API Contable con IA
Write-Host "🤖 Activando entorno virtual para API Contable con IA..." -ForegroundColor Green

# Activar entorno
& "{venv_path}\\Scripts\\Activate.ps1"

# Configurar variables de entorno
$env:PYTHONPATH = Get-Location
$env:HUGGINGFACE_API_TOKEN = "hf_exampletoken123"

Write-Host "✅ Entorno activado. Comandos útiles:" -ForegroundColor Green
Write-Host "  python start_ai_chat.py         - Verificar e iniciar servicio" -ForegroundColor Yellow
Write-Host "  uvicorn app.main:app --reload   - Iniciar servidor FastAPI" -ForegroundColor Yellow
Write-Host "  python examples/chat_example.py - Probar chat" -ForegroundColor Yellow
Write-Host "  deactivate                      - Desactivar entorno" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 Documentación: documentation/AI_CHAT_SERVICE.md" -ForegroundColor Cyan
Write-Host "🌐 Servidor: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 Docs: http://localhost:8000/docs" -ForegroundColor Cyan
"""
        
        with open("activate_ai_env.ps1", "w", encoding="utf-8") as f:
            f.write(ps_script)
        
        # Script para Command Prompt
        cmd_script = f"""@echo off
echo 🤖 Activando entorno virtual para API Contable con IA...

call "{venv_path}\\Scripts\\activate.bat"

set PYTHONPATH=%CD%
set HUGGINGFACE_API_TOKEN=hf_exampletoken123

echo ✅ Entorno activado. Comandos útiles:
echo   python start_ai_chat.py         - Verificar e iniciar servicio
echo   uvicorn app.main:app --reload   - Iniciar servidor FastAPI
echo   python examples/chat_example.py - Probar chat
echo   deactivate                      - Desactivar entorno
echo.
echo 📚 Documentación: documentation/AI_CHAT_SERVICE.md
echo 🌐 Servidor: http://localhost:8000
echo 📖 Docs: http://localhost:8000/docs
"""
        
        with open("activate_ai_env.bat", "w", encoding="utf-8") as f:
            f.write(cmd_script)
            
    else:
        # Script para Unix/Linux/macOS
        bash_script = f"""#!/bin/bash
echo "🤖 Activando entorno virtual para API Contable con IA..."

# Activar entorno
source {venv_path}/bin/activate

# Configurar variables de entorno
export PYTHONPATH=$(pwd)
export HUGGINGFACE_API_TOKEN="hf_exampletoken123"

echo "✅ Entorno activado. Comandos útiles:"
echo "  python start_ai_chat.py         - Verificar e iniciar servicio"
echo "  uvicorn app.main:app --reload   - Iniciar servidor FastAPI"
echo "  python examples/chat_example.py - Probar chat"
echo "  deactivate                      - Desactivar entorno"
echo ""
echo "📚 Documentación: documentation/AI_CHAT_SERVICE.md"
echo "🌐 Servidor: http://localhost:8000"
echo "📖 Docs: http://localhost:8000/docs"
"""
        
        with open("activate_ai_env.sh", "w", encoding="utf-8") as f:
            f.write(bash_script)
        
        # Hacer ejecutable
        os.chmod("activate_ai_env.sh", 0o755)

def create_env_file():
    """Crea archivo .env de ejemplo"""
    env_content = """# Configuración para API Contable con IA

# ===== BASE DE DATOS =====
SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://contable_user:contable_password@localhost:5432/contable_db

# ===== HUGGING FACE API =====
# ⚠️ IMPORTANTE: Reemplazar con tu token real de Hugging Face
# Obtener en: https://huggingface.co/settings/tokens
HUGGINGFACE_API_TOKEN=hf_exampletoken123

# ===== CONFIGURACIÓN DE LA API =====
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=true
ENVIRONMENT=development

# ===== CORS =====
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# ===== ADMIN POR DEFECTO =====
DEFAULT_ADMIN_EMAIL=admin@contable.com
DEFAULT_ADMIN_PASSWORD=Admin123!

# ===== CONFIGURACIÓN DE EMAIL (OPCIONAL) =====
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=tu_email@gmail.com
# SMTP_PASSWORD=tu_password_de_aplicacion
# EMAILS_FROM_EMAIL=tu_email@gmail.com
# EMAILS_FROM_NAME=Sistema Contable
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print("✅ Archivo .env creado")
    else:
        print("ℹ️ Archivo .env ya existe, no se sobrescribió")

def print_next_steps(venv_path):
    """Muestra los próximos pasos"""
    activation_cmd = get_activation_command(venv_path)
    
    print("\n" + "="*60)
    print("🎉 ¡Entorno virtual configurado exitosamente!")
    print("="*60)
    
    print("\n📋 PRÓXIMOS PASOS:")
    
    print(f"\n1️⃣ Activar el entorno virtual:")
    if platform.system() == "Windows":
        print("   PowerShell: .\\activate_ai_env.ps1")
        print("   CMD:        activate_ai_env.bat")
    else:
        print("   source activate_ai_env.sh")
    
    print(f"\n2️⃣ Configurar tu token de Hugging Face:")
    print("   - Editar archivo .env")
    print("   - Reemplazar 'hf_exampletoken123' con tu token real")
    print("   - Obtener token en: https://huggingface.co/settings/tokens")
    
    print(f"\n3️⃣ Configurar base de datos PostgreSQL:")
    print("   - Editar SQLALCHEMY_DATABASE_URI en .env")
    print("   - O usar docker-compose up -d para PostgreSQL local")
    
    print(f"\n4️⃣ Verificar e iniciar el servicio:")
    print("   python start_ai_chat.py")
    
    print(f"\n📚 RECURSOS:")
    print("   - Documentación: documentation/AI_CHAT_SERVICE.md")
    print("   - Ejemplos: python examples/chat_example.py")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Chat Health: http://localhost:8000/api/v1/ai/chat/health")

def main():
    """Función principal"""
    print("🤖 Configurador de Entorno Virtual - API Contable con IA")
    print("="*60)
    
    # Verificar que estamos en el directorio correcto
    current_dir = Path.cwd()
    if not (current_dir / "app" / "main.py").exists():
        print("❌ Error: Ejecuta este script desde el directorio raíz del proyecto")
        print("   (donde está el archivo app/main.py)")
        sys.exit(1)
    
    try:
        # 1. Crear entorno virtual
        venv_path = create_virtual_environment()
        
        # 2. Instalar dependencias
        if not install_dependencies(venv_path):
            print("❌ Falló la instalación de dependencias")
            sys.exit(1)
        
        # 3. Crear scripts de activación
        create_activation_scripts(venv_path)
        
        # 4. Crear archivo .env
        create_env_file()
        
        # 5. Mostrar próximos pasos
        print_next_steps(venv_path)
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
