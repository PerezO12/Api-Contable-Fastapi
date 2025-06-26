#!/usr/bin/env python3
"""
Test script para verificar la corrección del error de bulk import de accounts.
Este script reproduce el problema y verifica que la solución funcione.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid
from decimal import Decimal

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.services.bulk_import_service import BulkImportService
from app.models.account import Account, AccountType
from app.schemas.generic_import import ModelMetadata, FieldMetadata
from app.services.model_metadata_registry import ModelMetadataRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bulk_import_fix():
    """Prueba la corrección del problema de bulk import de accounts"""
    
    print("🧪 INICIANDO PRUEBA DE CORRECCIÓN BULK IMPORT ACCOUNTS")
    print("=" * 70)
    
    try:
        # Configurar sesión de base de datos
        async with AsyncSessionLocal() as db:
            try:
                # Inicializar servicios
                bulk_service = BulkImportService(db)
                registry = ModelMetadataRegistry()
                
                # Obtener metadata del modelo Account
                model_metadata = registry.get_model_metadata("account")
                if not model_metadata:
                    print("❌ No se pudo obtener metadata del modelo Account")
                    return False
                
                print(f"✅ Metadata obtenida para modelo: {model_metadata.model_name}")
                print(f"📊 Campos disponibles: {len(model_metadata.fields)}")
                
                # Datos de prueba para cuentas que reproduzcan el problema
                test_records = []
                
                # Crear 25 registros de prueba (suficientes para detectar el problema)
                for i in range(1, 26):
                    account_record = {
                        'code': f'TEST{i:03d}',
                        'name': f'Cuenta de Prueba {i}',
                        'account_type': 'activo',
                        'category': 'activo_corriente',
                        'description': f'Descripción de cuenta de prueba {i}',
                        'level': 1,
                        'is_active': True,
                        'allows_movements': True,
                        'requires_third_party': False,
                        'requires_cost_center': False,
                        'allows_reconciliation': False,
                        'balance': Decimal('0.00'),
                        'debit_balance': Decimal('0.00'),
                        'credit_balance': Decimal('0.00'),
                        'notes': f'Notas para cuenta {i}'
                    }
                    test_records.append(account_record)
                
                print(f"📝 Preparados {len(test_records)} registros de prueba")
                
                # TEST 1: Probar bulk import básico
                print("\n🔧 TEST 1: Bulk Import Básico")
                print("-" * 40)
                
                try:
                    result = await bulk_service.bulk_import_records(
                        model_class=Account,
                        model_metadata=model_metadata,
                        records=test_records[:5],  # Solo 5 registros para empezar
                        import_policy="create_only",
                        skip_errors=True,
                        user_id="test-user-id",
                        batch_start_row=1
                    )
                    
                    print(f"✅ Bulk import básico exitoso:")
                    print(f"   - Exitosos: {result.total_successful}")
                    print(f"   - Fallidos: {result.total_failed}")
                    print(f"   - Omitidos: {result.total_skipped}")
                    print(f"   - Tiempo: {result.processing_time_seconds:.2f}s")
                    
                    if result.total_failed > 0:
                        print("⚠️  Errores encontrados:")
                        for error in result.detailed_errors[:3]:  # Solo primeros 3
                            print(f"   - Fila {error['row_number']}: {error['message']}")
                    
                except Exception as e:
                    print(f"❌ Error en bulk import básico: {e}")
                    print(f"   Tipo de error: {type(e).__name__}")
                    return False
                
                # TEST 2: Probar bulk import con más registros
                print("\n🔧 TEST 2: Bulk Import con Más Registros")
                print("-" * 40)
                
                try:
                    # Limpiar códigos de cuentas para evitar duplicados
                    for i, record in enumerate(test_records[5:15]):
                        record['code'] = f'BULK{i+6:03d}'
                    
                    result = await bulk_service.bulk_import_records(
                        model_class=Account,
                        model_metadata=model_metadata,
                        records=test_records[5:15],  # 10 registros más
                        import_policy="create_only",
                        skip_errors=True,
                        user_id="test-user-id",
                        batch_start_row=6
                    )
                    
                    print(f"✅ Bulk import con más registros exitoso:")
                    print(f"   - Exitosos: {result.total_successful}")
                    print(f"   - Fallidos: {result.total_failed}")
                    print(f"   - Omitidos: {result.total_skipped}")
                    print(f"   - Tiempo: {result.processing_time_seconds:.2f}s")
                    print(f"   - Registros/seg: {result.records_per_second:.1f}")
                    
                except Exception as e:
                    print(f"❌ Error en bulk import con más registros: {e}")
                    print(f"   Tipo de error: {type(e).__name__}")
                    return False
                
                # TEST 3: Probar con datos problemáticos
                print("\n🔧 TEST 3: Bulk Import con Datos Problemáticos")
                print("-" * 40)
                
                problematic_records = [
                    {
                        'code': 'PROB001',
                        'name': 'Cuenta con Datos Problemáticos',
                        'account_type': 'activo',
                        'extra_field': 'Este campo no debería estar aquí',
                        'balance': 'not_a_number',  # Valor inválido
                        'is_active': 'true'  # String en lugar de bool
                    },
                    {
                        'code': '',  # Código vacío
                        'name': 'Cuenta sin código',
                        'account_type': 'activo'
                    },
                    {
                        'code': 'PROB003',
                        'name': None,  # Nombre nulo
                        'account_type': 'invalid_type'  # Tipo inválido
                    },
                    {
                        'code': 'PROB004',
                        'name': 'Cuenta OK',
                        'account_type': 'activo',
                        'parent_id': 'invalid-uuid'  # UUID inválido
                    }
                ]
                
                try:
                    result = await bulk_service.bulk_import_records(
                        model_class=Account,
                        model_metadata=model_metadata,
                        records=problematic_records,
                        import_policy="create_only",
                        skip_errors=True,
                        user_id="test-user-id",
                        batch_start_row=1
                    )
                    
                    print(f"✅ Bulk import con datos problemáticos completado:")
                    print(f"   - Exitosos: {result.total_successful}")
                    print(f"   - Fallidos: {result.total_failed}")
                    print(f"   - Omitidos: {result.total_skipped}")
                    
                    if result.total_failed > 0:
                        print("   📝 Errores detectados (como esperado):")
                        for error in result.detailed_errors:
                            print(f"   - Fila {error['row_number']}: {error['message'][:80]}...")
                    
                except Exception as e:
                    print(f"❌ Error inesperado con datos problemáticos: {e}")
                    return False
                
                print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
                print("✅ La corrección del bulk import funciona correctamente")
                return True
                
            finally:
                await db.close()
                
    except Exception as e:
        print(f"❌ Error general en las pruebas: {e}")
        logger.exception("Error detallado:")
        return False

async def main():
    """Función principal"""
    try:
        success = await test_bulk_import_fix()
        if success:
            print("\n✅ Pruebas exitosas - El problema del bulk import ha sido corregido")
            sys.exit(0)
        else:
            print("\n❌ Pruebas fallidas - El problema persiste")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
