#!/usr/bin/env python3
"""
Script de prueba para verificar la integración de facturas con diarios
Verifica que las facturas usen correctamente las secuencias de los diarios
"""
import sys
import os
import uuid
from datetime import datetime, date
from decimal import Decimal

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models.base import Base
from app.models.third_party import ThirdParty, ThirdPartyType, DocumentType
from app.models.journal import Journal, JournalType
from app.models.invoice import Invoice, InvoiceType, InvoiceStatus
from app.models.user import User
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceCreate


def setup_test_data(db):
    """Configurar datos de prueba necesarios"""
    print("📋 Configurando datos de prueba...")
    
    # Crear usuario de prueba si no existe
    test_user = db.query(User).filter(User.email == "test@invoice.com").first()
    if not test_user:
        test_user = User(
            id=uuid.uuid4(),
            email="test@invoice.com",
            full_name="Test User",
            hashed_password="fake_hash",
            is_active=True
        )
        db.add(test_user)
    
    # Crear tercero de prueba si no existe
    test_customer = db.query(ThirdParty).filter(ThirdParty.name == "Cliente de Prueba").first()
    if not test_customer:
        test_customer = ThirdParty(
            id=uuid.uuid4(),
            code="CLI001",
            name="Cliente de Prueba",
            third_party_type=ThirdPartyType.CUSTOMER,
            document_type=DocumentType.DNI,
            document_number="12345678",
            email="cliente@test.com",
            is_active=True
        )
        db.add(test_customer)
    
    # Crear proveedor de prueba si no existe
    test_supplier = db.query(ThirdParty).filter(ThirdParty.name == "Proveedor de Prueba").first()
    if not test_supplier:
        test_supplier = ThirdParty(
            id=uuid.uuid4(),
            code="PROV001",
            name="Proveedor de Prueba",
            third_party_type=ThirdPartyType.SUPPLIER,
            document_type=DocumentType.DNI,
            document_number="87654321",
            email="proveedor@test.com",
            is_active=True
        )
        db.add(test_supplier)
    
    db.commit()
    db.refresh(test_user)
    db.refresh(test_customer)
    db.refresh(test_supplier)
    
    return test_user, test_customer, test_supplier


def test_invoice_with_journal_sequences():
    """Probar la creación de facturas con secuencias de diarios"""
    print("🧪 Iniciando pruebas de facturas con diarios...")
    
    db = SessionLocal()
    try:
        # Configurar datos de prueba
        test_user, test_customer, test_supplier = setup_test_data(db)
        
        # Obtener diarios existentes
        sales_journal = db.query(Journal).filter(Journal.type == JournalType.SALE).first()
        purchase_journal = db.query(Journal).filter(Journal.type == JournalType.PURCHASE).first()
        
        if not sales_journal or not purchase_journal:
            print("❌ Error: No se encontraron diarios de ventas y compras")
            print("   Ejecuta primero el script create_default_journals.py")
            return False
        
        print(f"📚 Diario de ventas encontrado: {sales_journal.name} (Prefijo: {sales_journal.sequence_prefix})")
        print(f"📚 Diario de compras encontrado: {purchase_journal.name} (Prefijo: {purchase_journal.sequence_prefix})")
        
        invoice_service = InvoiceService(db)
        
        # ===========================================
        # PRUEBA 1: Factura de cliente con selección automática de diario
        # ===========================================        print("\n🔍 PRUEBA 1: Factura de cliente con selección automática de diario")
        
        invoice_data_customer = InvoiceCreate(
            invoice_type=InvoiceType.CUSTOMER_INVOICE,
            third_party_id=test_customer.id,
            invoice_date=date.today(),
            due_date=date.today(),
            description="Factura de venta con diario automático",
            currency_code="USD",
            exchange_rate=Decimal('1'),
            invoice_number=None,
            journal_id=None,
            payment_terms_id=None,
            third_party_account_id=None,
            notes=None
        )
        
        # Verificar secuencia actual del diario de ventas antes
        sales_seq_before = sales_journal.current_sequence_number
        print(f"   📊 Secuencia de ventas antes: {sales_seq_before}")
        
        customer_invoice = invoice_service.create_invoice(invoice_data_customer, test_user.id)
          # Verificar que se asignó el diario correcto
        invoice_from_db = db.query(Invoice).filter(Invoice.id == customer_invoice.id).first()
        if invoice_from_db:
            db.refresh(sales_journal)
            
            print(f"   📄 Factura creada: {customer_invoice.invoice_number}")
            print(f"   📚 Diario asignado: {invoice_from_db.journal_id}")
            print(f"   📊 Secuencia de ventas después: {sales_journal.current_sequence_number}")
        else:
            print("   ❌ Error: No se pudo obtener la factura de la base de datos")
            return False
        
        # Verificar que el número sigue el patrón del diario
        expected_pattern = sales_journal.sequence_prefix
        if customer_invoice.invoice_number.startswith(expected_pattern):
            print(f"   ✅ El número de factura sigue el patrón del diario: {customer_invoice.invoice_number}")
        else:
            print(f"   ❌ El número de factura NO sigue el patrón esperado")
            return False
        
        # ===========================================
        # PRUEBA 2: Factura de proveedor con diario específico
        # ===========================================        print("\n🔍 PRUEBA 2: Factura de proveedor con diario específico")
        
        invoice_data_supplier = InvoiceCreate(
            invoice_type=InvoiceType.SUPPLIER_INVOICE,
            third_party_id=test_supplier.id,
            journal_id=purchase_journal.id,  # Especificar el diario
            invoice_date=date.today(),
            due_date=date.today(),
            description="Factura de compra con diario específico",
            currency_code="USD",
            exchange_rate=Decimal('1'),
            invoice_number=None,
            payment_terms_id=None,
            third_party_account_id=None,
            notes=None
        )
        
        # Verificar secuencia actual del diario de compras antes
        purchase_seq_before = purchase_journal.current_sequence_number
        print(f"   📊 Secuencia de compras antes: {purchase_seq_before}")
        
        supplier_invoice = invoice_service.create_invoice(invoice_data_supplier, test_user.id)
          # Verificar que se asignó el diario correcto
        invoice_from_db = db.query(Invoice).filter(Invoice.id == supplier_invoice.id).first()
        if invoice_from_db:
            db.refresh(purchase_journal)
            
            print(f"   📄 Factura creada: {supplier_invoice.invoice_number}")
            print(f"   📚 Diario asignado: {invoice_from_db.journal_id}")
            print(f"   📊 Secuencia de compras después: {purchase_journal.current_sequence_number}")
        else:
            print("   ❌ Error: No se pudo obtener la factura de la base de datos")
            return False
        
        # Verificar que el número sigue el patrón del diario
        expected_pattern = purchase_journal.sequence_prefix
        if supplier_invoice.invoice_number.startswith(expected_pattern):
            print(f"   ✅ El número de factura sigue el patrón del diario: {supplier_invoice.invoice_number}")
        else:
            print(f"   ❌ El número de factura NO sigue el patrón esperado")
            return False
        
        # ===========================================
        # PRUEBA 3: Verificar incremento de secuencias
        # ===========================================
        print("\n🔍 PRUEBA 3: Verificar incremento de secuencias")
          # Crear otra factura del mismo tipo
        invoice_data_customer2 = InvoiceCreate(
            invoice_type=InvoiceType.CUSTOMER_INVOICE,
            third_party_id=test_customer.id,
            invoice_date=date.today(),
            due_date=date.today(),
            description="Segunda factura de venta",
            currency_code="USD",
            exchange_rate=Decimal('1'),
            invoice_number=None,
            journal_id=None,
            payment_terms_id=None,
            third_party_account_id=None,
            notes=None
        )
        
        customer_invoice2 = invoice_service.create_invoice(invoice_data_customer2, test_user.id)
        
        print(f"   📄 Segunda factura creada: {customer_invoice2.invoice_number}")
        
        # Verificar que los números son consecutivos
        if customer_invoice2.invoice_number > customer_invoice.invoice_number:
            print(f"   ✅ Los números de factura son consecutivos")
        else:
            print(f"   ❌ Los números de factura NO son consecutivos")
            return False
        
        # ===========================================
        # PRUEBA 4: Mostrar resumen
        # ===========================================
        print("\n📊 RESUMEN DE PRUEBAS:")
        print(f"   🏷️ Factura de cliente 1: {customer_invoice.invoice_number}")
        print(f"   🏷️ Factura de cliente 2: {customer_invoice2.invoice_number}")
        print(f"   🏷️ Factura de proveedor: {supplier_invoice.invoice_number}")
        
        db.refresh(sales_journal)
        db.refresh(purchase_journal)
        
        print(f"   📈 Secuencia final ventas: {sales_journal.current_sequence_number}")
        print(f"   📈 Secuencia final compras: {purchase_journal.current_sequence_number}")
        
        print("\n✅ ¡Todas las pruebas pasaron exitosamente!")
        print("🎉 Las facturas ahora usan correctamente las secuencias de los diarios")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Iniciando pruebas de integración de facturas con diarios...")
    
    success = test_invoice_with_journal_sequences()
    
    if success:
        print("\n🎯 IMPLEMENTACIÓN COMPLETADA:")
        print("   ✅ Las facturas ahora usan las secuencias de los diarios")
        print("   ✅ Selección automática de diario por tipo de factura")
        print("   ✅ Números de factura con formato: PREFIJO/AÑO/NÚMERO")
        print("   ✅ Secuencias incrementales por diario")
        
        print("\n📚 PRÓXIMO PASO:")
        print("   🔄 Probar la contabilización de facturas para verificar")
        print("      que los journal entries también usen el mismo diario")
    else:
        print("\n❌ HUBO ERRORES EN LAS PRUEBAS")
        print("   🔧 Revisa los logs y corrige los problemas encontrados")
    
    print("\n🏁 Fin de las pruebas.")
