#!/usr/bin/env python
"""
Script para depurar el error de importación
"""
import traceback
import sys

try:
    print("Importando app.main...")
    from app.main import app
    print("✅ app.main importado exitosamente")
    
except Exception as e:
    print("❌ Error al importar app.main:")
    print(f"Error: {e}")
    print("\nTraceback completo:")
    traceback.print_exc()
    sys.exit(1)
