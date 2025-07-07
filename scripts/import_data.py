#!/usr/bin/env python3
"""
Script de gestión para ejecutar todos los scripts de importación de datos
"""
import asyncio
import argparse
import sys
import os

# Agregar el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.data_import.import_world_currencies import import_world_currencies
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def run_currency_import():
    """Ejecutar importación de monedas"""
    try:
        await import_world_currencies()
    except Exception as e:
        logger.error(f"Error en importación de monedas: {str(e)}")
        raise


async def run_all_imports():
    """Ejecutar todas las importaciones disponibles"""
    logger.info("🚀 Iniciando todas las importaciones de datos...")
    
    # Lista de importaciones a ejecutar
    imports = [
        ("Monedas mundiales", run_currency_import),
        # Aquí se pueden agregar más importaciones en el futuro
        # ("Cuentas contables", run_accounts_import),
        # ("Centros de costo", run_cost_centers_import),
    ]
    
    success_count = 0
    error_count = 0
    
    for name, import_func in imports:
        try:
            logger.info(f"📥 Ejecutando importación: {name}")
            await import_func()
            logger.info(f"✅ Completado: {name}")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ Error en {name}: {str(e)}")
            error_count += 1
    
    logger.info(f"""
    ═══════════════════════════════════════════════════════════
    RESUMEN DE IMPORTACIONES
    ═══════════════════════════════════════════════════════════
    ✅ Exitosas: {success_count}
    ❌ Con errores: {error_count}
    📊 Total: {success_count + error_count}
    ═══════════════════════════════════════════════════════════
    """)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Gestión de importaciones de datos")
    parser.add_argument(
        "action", 
        choices=["currencies", "all"], 
        help="Tipo de importación a ejecutar"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Forzar ejecución ignorando variables de entorno"
    )
    
    args = parser.parse_args()
    
    # Si se usa --force, establecer temporalmente MAP_CURRENCY=true
    if args.force:
        os.environ["MAP_CURRENCY"] = "true"
        logger.info("🔧 Modo forzado activado - ignorando configuraciones de entorno")
    
    try:
        if args.action == "currencies":
            asyncio.run(run_currency_import())
        elif args.action == "all":
            asyncio.run(run_all_imports())
    except KeyboardInterrupt:
        logger.info("❌ Importación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
