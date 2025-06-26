"""
Test script para verificar la corrección del problema de TIMESTAMP WITH TIME ZONE
en importaciones bulk a PostgreSQL.

Este script prueba que los campos datetime se conviertan correctamente a timezone-aware
antes de las operaciones bulk insert/upsert.
"""
import asyncio
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal

# Añadir el directorio de la aplicación al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.account import Account
from app.services.bulk_import_service import BulkImportService
from app.schemas.generic_import import ModelMetadata, FieldMetadata, FieldType

class MockSession:
    """Mock de sesión de base de datos para pruebas"""
    def __init__(self):
        self.committed = False
        
    async def execute(self, stmt):
        print(f"Mock execute: {type(stmt).__name__}")
        return MockResult()
        
    async def commit(self):
        self.committed = True
        print("Mock commit")
        
    async def rollback(self):
        print("Mock rollback")
        
    async def close(self):
        print("Mock close")
        
    def add(self, instance):
        print(f"Mock add: {type(instance).__name__}")

class MockResult:
    def scalar_one_or_none(self):
        return None

async def test_timestamp_conversion():
    """Prueba la conversión de campos timestamp antes de bulk insert"""
    
    # Crear instancia del servicio con mock session
    mock_session = MockSession()
    service = BulkImportService(mock_session)  # type: ignore
    
    # Datos de prueba con datetime naive (sin timezone)
    test_data = [
        {
            'code': 'TEST001',
            'name': 'Test Account 1',
            'account_type': 'asset',
            'balance': Decimal('1000.00'),
            'created_at': datetime(2024, 1, 15, 10, 30, 0),  # datetime naive
            'updated_at': datetime(2024, 1, 15, 11, 0, 0),   # datetime naive
        },
        {
            'code': 'TEST002', 
            'name': 'Test Account 2',
            'account_type': 'liability',
            'balance': Decimal('2000.00'),
            'created_at': datetime(2024, 1, 16, 9, 15, 0),   # datetime naive
            'updated_at': datetime(2024, 1, 16, 10, 45, 0),  # datetime naive
        }
    ]
    
    # Probar conversión individual de campos timestamp
    print("=== PRUEBA 1: Conversión individual de campos timestamp ===")
    for i, record in enumerate(test_data):
        print(f"\nRegistro {i+1} - ANTES de conversión:")
        print(f"  created_at: {record['created_at']} (tzinfo: {record['created_at'].tzinfo})")
        print(f"  updated_at: {record['updated_at']} (tzinfo: {record['updated_at'].tzinfo})")
        
        converted = service._convert_timestamp_fields(record, Account)
        
        print(f"Registro {i+1} - DESPUÉS de conversión:")
        print(f"  created_at: {converted['created_at']} (tzinfo: {converted['created_at'].tzinfo})")
        print(f"  updated_at: {converted['updated_at']} (tzinfo: {converted['updated_at'].tzinfo})")
        
        # Verificar que se convirtieron a UTC
        assert converted['created_at'].tzinfo == timezone.utc, "created_at debe tener timezone UTC"
        assert converted['updated_at'].tzinfo == timezone.utc, "updated_at debe tener timezone UTC"
    
    print("\n✅ Conversión de campos timestamp funciona correctamente")
    
    # Probar también con datos ya timezone-aware
    print("\n=== PRUEBA 2: Datos ya timezone-aware ===")
    utc_data = {
        'code': 'TEST003',
        'name': 'Test Account 3',
        'account_type': 'equity',
        'created_at': datetime(2024, 1, 17, 12, 0, 0, tzinfo=timezone.utc),  # ya tiene timezone
        'updated_at': datetime(2024, 1, 17, 13, 30, 0, tzinfo=timezone.utc)  # ya tiene timezone
    }
    
    print(f"ANTES - created_at: {utc_data['created_at']} (tzinfo: {utc_data['created_at'].tzinfo})")
    converted_utc = service._convert_timestamp_fields(utc_data, Account)
    print(f"DESPUÉS - created_at: {converted_utc['created_at']} (tzinfo: {converted_utc['created_at'].tzinfo})")
    
    # Verificar que mantiene el timezone original
    assert converted_utc['created_at'].tzinfo == timezone.utc, "Debe mantener timezone UTC"
    assert converted_utc['updated_at'].tzinfo == timezone.utc, "Debe mantener timezone UTC"
    
    print("✅ Datos timezone-aware se mantienen correctamente")
    
    # Probar con tipos mixed
    print("\n=== PRUEBA 3: Datos con tipos mixtos ===")
    mixed_data = {
        'code': 'TEST004',
        'name': 'Test Account 4',
        'account_type': 'asset',
        'balance': Decimal('5000.00'),
        'created_at': datetime(2024, 1, 18, 8, 0, 0),  # naive
        'updated_at': datetime(2024, 1, 18, 9, 0, 0, tzinfo=timezone.utc),  # aware
        'some_string': 'texto normal',  # no datetime
        'some_number': 42,  # no datetime
        'some_none': None  # None value
    }
    
    converted_mixed = service._convert_timestamp_fields(mixed_data, Account)
    
    print(f"created_at: {converted_mixed['created_at']} (tzinfo: {converted_mixed['created_at'].tzinfo})")
    print(f"updated_at: {converted_mixed['updated_at']} (tzinfo: {converted_mixed['updated_at'].tzinfo})")
    print(f"some_string: {converted_mixed['some_string']} (tipo: {type(converted_mixed['some_string'])})")
    print(f"some_number: {converted_mixed['some_number']} (tipo: {type(converted_mixed['some_number'])})")
    print(f"some_none: {converted_mixed['some_none']}")
    
    # Verificar conversiones correctas
    assert converted_mixed['created_at'].tzinfo == timezone.utc, "created_at naive debe convertirse a UTC"
    assert converted_mixed['updated_at'].tzinfo == timezone.utc, "updated_at aware debe mantenerse"
    assert converted_mixed['some_string'] == 'texto normal', "Strings no deben cambiar"
    assert converted_mixed['some_number'] == 42, "Numbers no deben cambiar"
    assert converted_mixed['some_none'] is None, "None values no deben cambiar"
    
    print("✅ Datos con tipos mixtos se manejan correctamente")
    
    # Probar el método _ensure_correct_data_types también
    print("\n=== PRUEBA 4: Método _ensure_correct_data_types ===")
    test_record = {
        'id': 'some-uuid-string',
        'code': 'TEST005',
        'name': 'Test Account 5',
        'account_type': 'asset',
        'balance': '3000.50',  # string que debe convertirse a Decimal
        'created_at': datetime(2024, 1, 19, 10, 0, 0, tzinfo=timezone.utc),
        'updated_at': datetime(2024, 1, 19, 11, 0, 0, tzinfo=timezone.utc),
        'created_by_id': 'another-uuid-string'
    }
    
    processed = service._ensure_correct_data_types(test_record, Account)
    print(f"balance antes: {test_record['balance']} (tipo: {type(test_record['balance'])})")
    print(f"balance después: {processed['balance']} (tipo: {type(processed['balance'])})")
    
    assert isinstance(processed['balance'], Decimal), "balance debe convertirse a Decimal"
    print("✅ Conversión de tipos funciona correctamente")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de corrección para TIMESTAMP WITH TIME ZONE")
    print("="*70)
    
    try:
        asyncio.run(test_timestamp_conversion())
        print("\n🎉 Todas las pruebas completadas exitosamente")
        print("\n📝 RESUMEN:")
        print("- ✅ Conversión de datetime naive a timezone-aware (UTC)")
        print("- ✅ Mantenimiento de datetime ya timezone-aware")  
        print("- ✅ Manejo correcto de tipos mixtos")
        print("- ✅ Preservación de campos no-datetime")
        print("- ✅ Integración con _ensure_correct_data_types")
        print("\n🔧 La solución está lista para production!")
    except Exception as e:
        print(f"\n💥 Error crítico en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
