"""
Test script para simular el escenario real de importación que está fallando
con TIMESTAMP WITH TIME ZONE en PostgreSQL.

Este script simula exactamente el flujo de importación que está causando el error.
"""
import asyncio
import sys
import os
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

# Configurar logging para ver todos los detalles
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Añadir el directorio de la aplicación al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.account import Account
from app.services.bulk_import_service import BulkImportService
from app.schemas.generic_import import ModelMetadata, FieldMetadata, FieldType

class MockAsyncSession:
    """Mock avanzado de sesión async para capturar exactamente qué se envía a PostgreSQL"""
    def __init__(self):
        self.committed = False
        self.executed_statements = []
        self.executed_data = []
        
    async def execute(self, stmt):
        """Capturar statement y datos para análisis"""
        self.executed_statements.append(stmt)
        
        # Extraer datos si están disponibles
        if hasattr(stmt, 'values_clause'):
            # Para insert statements
            if hasattr(stmt.values_clause, 'data'):
                self.executed_data.extend(stmt.values_clause.data)
            elif hasattr(stmt, 'values') and callable(stmt.values):
                # Para otros tipos de statements
                pass
        
        # Log del statement ejecutado
        print(f"\n🔍 STATEMENT EJECUTADO:")
        print(f"Tipo: {type(stmt).__name__}")
        print(f"Statement: {str(stmt)}")
        
        # Si es un insert, analizar los datos
        if 'INSERT' in str(stmt).upper():
            # Intentar extraer los valores para análisis
            compiled = stmt.compile(compile_kwargs={"literal_binds": True})
            print(f"SQL Compilado: {compiled}")
            
            # Verificar si hay datos en el statement
            if hasattr(stmt, 'parameters'):
                for i, params in enumerate(stmt.parameters[:3]):  # Solo los primeros 3
                    print(f"\nParametros registro {i}:")
                    for key, value in params.items():
                        if 'created_at' in key.lower() or 'updated_at' in key.lower():
                            print(f"  {key}: {value} (tipo: {type(value)}, tzinfo: {getattr(value, 'tzinfo', 'N/A')})")
        
        return MockResult()
        
    async def commit(self):
        self.committed = True
        print("✅ COMMIT ejecutado")
        
    async def rollback(self):
        print("🔄 ROLLBACK ejecutado")
        
    async def close(self):
        print("🔒 CLOSE ejecutado")
        
    def add(self, instance):
        print(f"➕ ADD: {type(instance).__name__}")

class MockResult:
    def scalar_one_or_none(self):
        return None

async def test_real_import_scenario():
    """Simula el escenario real de importación masiva que está fallando"""
    
    print("🚀 INICIANDO PRUEBA DE ESCENARIO REAL DE IMPORTACIÓN")
    print("="*80)
    
    # Crear mock session avanzado
    mock_session = MockAsyncSession()
    service = BulkImportService(mock_session)  # type: ignore
    
    # Metadatos del modelo Account (simulando configuración real)
    model_metadata = ModelMetadata(
        model_name="Account",
        table_name="accounts",
        business_key_fields=["code"],  # Como en el sistema real
        display_name="Account",
        description="Accounts model",
        fields=[]  # Agregamos campo requerido
    )
    
    # Datos de prueba que simulan importación masiva real (100 registros)
    print(f"📋 Generando datos de prueba (100 registros)...")
    
    test_records = []
    for i in range(100):
        record = {
            'code': f'ACCOUNT_{i:04d}',
            'name': f'Test Account {i:04d}',
            'account_type': 'asset',
            'balance': Decimal(f'{(i+1)*100}.00'),
            'level': 1,
            'allows_reconciliation': False,
            'is_active': True,
            'allows_movements': True,
            'requires_third_party': False,
            'requires_cost_center': False,
            # Nota: NO incluimos created_at/updated_at porque se generan automáticamente
        }
        test_records.append(record)
    
    print(f"✅ Generados {len(test_records)} registros de prueba")
    
    # Probar diferentes políticas de importación
    import_policies = ["create_only", "upsert"]
    
    for policy in import_policies:
        print(f"\n🔧 PROBANDO POLÍTICA: {policy}")
        print("-" * 50)
        
        # Reset del mock session
        mock_session.executed_statements.clear()
        mock_session.executed_data.clear()
        mock_session.committed = False
        
        try:
            # Ejecutar importación bulk (esto debería generar el error)
            result = await service.bulk_import_records(
                model_class=Account,
                model_metadata=model_metadata,
                records=test_records,
                import_policy=policy,
                skip_errors=False,
                user_id="test-user-id",
                batch_start_row=1
            )
            
            print(f"\n📊 RESULTADOS DE IMPORTACIÓN:")
            print(f"Total procesados: {result.total_processed}")
            print(f"Exitosos: {result.total_successful}")
            print(f"Fallidos: {result.total_failed}")
            print(f"Actualizados: {result.total_updated}")
            print(f"Tiempo: {result.processing_time_seconds:.2f}s")
            
            # Verificar si se ejecutó commit
            if mock_session.committed:
                print("✅ Transacción commitada exitosamente")
            else:
                print("❌ Transacción NO fue commitada")
                
            # Analizar statements ejecutados
            print(f"\n🔍 ANÁLISIS DE STATEMENTS:")
            print(f"Total statements ejecutados: {len(mock_session.executed_statements)}")
            
            for i, stmt in enumerate(mock_session.executed_statements):
                print(f"Statement {i+1}: {type(stmt).__name__}")
                
        except Exception as e:
            print(f"\n💥 ERROR DURANTE IMPORTACIÓN:")
            print(f"Tipo: {type(e).__name__}")
            print(f"Mensaje: {str(e)}")
            
            import traceback
            print(f"\nTraceback completo:")
            traceback.print_exc()
    
    print(f"\n🎯 CONCLUSIONES:")
    print("- Si se ven mensajes de warnings sobre naive timestamps, el sistema está funcionando")
    print("- Si se ven 'FINAL Record X created_at/updated_at' con tzinfo=UTC, los timestamps están correctos")
    print("- Si hay errores, indican dónde está fallando la conversión de timezone")

async def test_timezone_edge_cases():
    """Prueba casos edge específicos con timezones"""
    
    print("\n🌍 PRUEBA DE CASOS EDGE CON TIMEZONES")
    print("="*50)
    
    mock_session = MockAsyncSession()
    service = BulkImportService(mock_session)  # type: ignore
    
    # Caso 1: Record con timestamps naive
    print("\n🧪 Caso 1: Record con timestamps naive")
    record_naive = {
        'code': 'TEST_NAIVE',
        'name': 'Test Naive Timestamps',
        'account_type': 'asset',
        'created_at': datetime(2024, 1, 1, 10, 0, 0),  # Sin timezone
        'updated_at': datetime(2024, 1, 1, 11, 0, 0),  # Sin timezone
    }
    
    converted = service._convert_timestamp_fields(record_naive, Account)
    print(f"created_at convertido: {converted['created_at']} (tzinfo: {converted['created_at'].tzinfo})")
    print(f"updated_at convertido: {converted['updated_at']} (tzinfo: {converted['updated_at'].tzinfo})")
    
    # Caso 2: Record con timestamps ya timezone-aware
    print("\n🧪 Caso 2: Record con timestamps timezone-aware")
    record_aware = {
        'code': 'TEST_AWARE',
        'name': 'Test Aware Timestamps',
        'account_type': 'asset',
        'created_at': datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        'updated_at': datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    }
    
    converted_aware = service._convert_timestamp_fields(record_aware, Account)
    print(f"created_at convertido: {converted_aware['created_at']} (tzinfo: {converted_aware['created_at'].tzinfo})")
    print(f"updated_at convertido: {converted_aware['updated_at']} (tzinfo: {converted_aware['updated_at'].tzinfo})")
    
    # Caso 3: Record sin timestamps (generación automática)
    print("\n🧪 Caso 3: Record sin timestamps (generación automática)")
    record_no_timestamps: Dict[str, Any] = {
        'code': 'TEST_AUTO',
        'name': 'Test Auto Timestamps',
        'account_type': 'asset',
    }
    
    # Simular el proceso que ocurre en bulk_import_records
    unified_timestamp = datetime.now(timezone.utc)
    print(f"unified_timestamp generado: {unified_timestamp} (tzinfo: {unified_timestamp.tzinfo})")
    
    prepared: Dict[str, Any] = record_no_timestamps.copy()
    prepared['created_at'] = unified_timestamp
    prepared['updated_at'] = unified_timestamp
    
    final_converted = service._convert_timestamp_fields(prepared, Account)
    print(f"created_at final: {final_converted['created_at']} (tzinfo: {final_converted['created_at'].tzinfo})")
    print(f"updated_at final: {final_converted['updated_at']} (tzinfo: {final_converted['updated_at'].tzinfo})")

if __name__ == "__main__":
    print("🔧 TEST DE ESCENARIO REAL DE IMPORTACIÓN POSTGRESQL")
    print("="*80)
    
    try:
        # Ejecutar pruebas
        asyncio.run(test_timezone_edge_cases())
        asyncio.run(test_real_import_scenario())
        
        print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS")
        print("\n📝 PRÓXIMOS PASOS:")
        print("1. Revisar logs de DEBUG para identificar dónde se pierden los timezones")
        print("2. Verificar que todos los timestamps tengan tzinfo=UTC antes del insert")
        print("3. Si persiste el error, el problema puede estar en SQLAlchemy o el driver PostgreSQL")
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
