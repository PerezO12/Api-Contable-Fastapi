#!/usr/bin/env python3
"""
Script de gestión para ejecutar scripts de importación de datos
"""
import asyncio
import argparse
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.data_import.import_world_currencies import run_currency_import as import_currency_function
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def run_currency_import(force: bool = False):
    """
    Ejecutar importación de monedas
    """
    if force:
        # Si force=True, eliminar archivo de control para forzar la importación
        control_file = "scripts/.currencies_imported"
        if os.path.exists(control_file):
            os.remove(control_file)
            logger.info("Archivo de control eliminado, forzando reimportación")
    
    await import_currency_function(force=force)


async def main():
    parser = argparse.ArgumentParser(description="Gestor de scripts de importación de datos")
    parser.add_argument(
        'action', 
        choices=['currencies', 'all'],
        help='Acción a ejecutar: currencies (importar monedas) o all (todos los scripts)'
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Forzar la ejecución incluso si ya se ejecutó anteriormente'
    )
    
    args = parser.parse_args()
    
    try:
        if args.action == 'currencies':
            logger.info("Ejecutando importación de monedas...")
            await run_currency_import(force=args.force)
            logger.info("✅ Importación de monedas completada")
            
        elif args.action == 'all':
            logger.info("Ejecutando todos los scripts de importación...")
            await run_currency_import(force=args.force)
            # Aquí se pueden agregar más scripts en el futuro
            logger.info("✅ Todos los scripts de importación completados")
            
    except Exception as e:
        logger.error(f"❌ Error ejecutando scripts: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
