#!/usr/bin/env python3
"""
Script para instalar y configurar las dependencias de IA
"""
import subprocess
import sys
import os

def install_dependencies():
    """Instala las dependencias necesarias"""
    dependencies = [
        "transformers==4.36.2",
        "torch==2.1.2"
    ]
    
    print("📦 Instalando dependencias de IA...")
    
    for dep in dependencies:
        print(f"Instalando {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {dep}: {e}")
            return False
    
    return True

def verify_installation():
    """Verifica que las dependencias estén instaladas"""
    try:
        import transformers
        import torch
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Error verificando instalación: {e}")
        return False

def main():
    print("🚀 Configuración del Sistema de IA")
    print("=" * 40)
    
    # Instalar dependencias
    if install_dependencies():
        print("\n🔍 Verificando instalación...")
        if verify_installation():
            print("\n✅ Sistema de IA configurado correctamente")
            print("\n💡 Ejecuta 'python check_ai_system.py' para diagnóstico completo")
        else:
            print("\n❌ Error en la verificación")
    else:
        print("\n❌ Error instalando dependencias")

if __name__ == "__main__":
    main()
