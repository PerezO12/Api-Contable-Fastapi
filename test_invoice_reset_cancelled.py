#!/usr/bin/env python3
"""
Script de prueba para verificar que las facturas canceladas se pueden restablecer a borrador
"""

import asyncio
import uuid
from datetime import datetime
from decimal import Decimal

# Configurar el path para importar desde la aplicación
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.models.invoice import Invoice, InvoiceStatus, InvoiceType
from app.models.third_party import ThirdParty, ThirdPartyType
from app.models.journal_entry import JournalEntry, JournalEntryStatus
from app.services.invoice_service import InvoiceService
from app.database import get_db
from app.config import settings

def test_reset_cancelled_invoice():
    """Test que demuestra que una factura cancelada se puede restablecer a borrador"""
    
    print("🔄 Iniciando prueba de reset de factura cancelada...")
    
    # Simular base de datos en memoria o usar configuración de test
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    
    # Crear engine en memoria para test
    engine = create_engine("sqlite:///test_reset_cancelled.db", echo=True)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("📊 Creando datos de prueba...")
        
        # Crear un tercero de prueba
        test_customer = ThirdParty(
            id=uuid.uuid4(),
            name="Cliente de Prueba Reset",
            document_number="12345678",
            third_party_type=ThirdPartyType.CUSTOMER,
            email="test@example.com"
        )
        db.add(test_customer)
          # Crear una factura de prueba
        test_invoice = Invoice(
            id=uuid.uuid4(),
            number="FAC-RESET-001",
            invoice_type=InvoiceType.CUSTOMER_INVOICE,
            third_party_id=test_customer.id,
            invoice_date=datetime.now().date(),
            due_date=datetime.now().date(),
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("19.00"),
            total_amount=Decimal("119.00"),
            status=InvoiceStatus.CANCELLED,  # Estado cancelado
            currency_code="COP",
            created_by_id=uuid.uuid4(),  # Usuario ficticio
            cancelled_by_id=uuid.uuid4(),  # Fue cancelada por alguien
            cancelled_at=datetime.now(),
            notes="Factura cancelada para prueba de reset"
        )
        db.add(test_invoice)
        db.commit()
        
        print(f"✅ Factura creada: {test_invoice.number} en estado {test_invoice.status}")
        
        # Inicializar el servicio
        service = InvoiceService(db)
        
        # Intentar resetear a borrador
        print(f"🔄 Intentando resetear factura {test_invoice.number} desde CANCELLED a DRAFT...")
        
        reset_result = service.reset_to_draft(
            invoice_id=test_invoice.id,
            reset_by_id=uuid.uuid4(),  # Usuario que hace el reset
            reason="Prueba de reset desde estado cancelado"
        )
        
        print(f"✅ Reset exitoso! Estado final: {reset_result.status}")
        print(f"📝 Notas: {reset_result.notes}")
        
        # Verificar que el reset fue exitoso
        updated_invoice = db.query(Invoice).filter(Invoice.id == test_invoice.id).first()
        
        assert updated_invoice.status == InvoiceStatus.DRAFT, f"Estado esperado DRAFT, obtenido {updated_invoice.status}"
        assert updated_invoice.cancelled_by_id is None, "cancelled_by_id debería ser None"
        assert updated_invoice.cancelled_at is None, "cancelled_at debería ser None"
        
        print("✅ Todas las verificaciones pasaron correctamente!")
        print("🎉 La funcionalidad de reset desde CANCELLED funciona!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()
        # Limpiar archivo de test
        if os.path.exists("test_reset_cancelled.db"):
            os.remove("test_reset_cancelled.db")


def test_bulk_reset_cancelled_invoices():
    """Test del reset bulk incluyendo facturas canceladas"""
    
    print("\n🔄 Iniciando prueba de reset BULK con facturas canceladas...")
    
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    
    # Crear engine en memoria para test
    engine = create_engine("sqlite:///test_bulk_reset_cancelled.db", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("📊 Creando datos de prueba para bulk reset...")
        
        # Crear un tercero de prueba
        test_customer = ThirdParty(
            id=uuid.uuid4(),
            name="Cliente Bulk Reset",
            document_number="87654321",
            third_party_type=ThirdPartyType.CUSTOMER,
            email="bulk@example.com"
        )
        db.add(test_customer)
        
        # Crear facturas en diferentes estados
        invoices_data = [
            ("FAC-BULK-001", InvoiceStatus.POSTED, "Factura contabilizada"),
            ("FAC-BULK-002", InvoiceStatus.CANCELLED, "Factura cancelada"),
            ("FAC-BULK-003", InvoiceStatus.CANCELLED, "Otra factura cancelada"),
            ("FAC-BULK-004", InvoiceStatus.DRAFT, "Factura en borrador")  # Esta debería ser skipped
        ]
        
        created_invoices = []
          for number, status, notes in invoices_data:
            invoice = Invoice(
                id=uuid.uuid4(),
                number=number,
                invoice_type=InvoiceType.CUSTOMER_INVOICE,
                third_party_id=test_customer.id,
                invoice_date=datetime.now().date(),
                due_date=datetime.now().date(),
                subtotal=Decimal("100.00"),
                tax_amount=Decimal("19.00"),
                total_amount=Decimal("119.00"),
                status=status,
                currency_code="COP",
                created_by_id=uuid.uuid4(),
                notes=notes
            )
            
            if status == InvoiceStatus.POSTED:
                invoice.posted_by_id = uuid.uuid4()
                invoice.posted_at = datetime.now()
            elif status == InvoiceStatus.CANCELLED:
                invoice.cancelled_by_id = uuid.uuid4()
                invoice.cancelled_at = datetime.now()
                
            db.add(invoice)
            created_invoices.append(invoice)
        
        db.commit()
        
        print(f"✅ Creadas {len(created_invoices)} facturas de prueba")
        
        # Inicializar el servicio
        service = InvoiceService(db)
        
        # Preparar IDs para bulk reset (excluir la DRAFT)
        invoice_ids = [inv.id for inv in created_invoices if inv.status != InvoiceStatus.DRAFT]
        
        print(f"🔄 Ejecutando bulk reset para {len(invoice_ids)} facturas...")
        print(f"   Estados: {[inv.status for inv in created_invoices if inv.status != InvoiceStatus.DRAFT]}")
        
        # Ejecutar bulk reset
        bulk_result = service.bulk_reset_to_draft_invoices(
            invoice_ids=invoice_ids,
            reset_by_id=uuid.uuid4(),
            reason="Prueba bulk reset con facturas canceladas",
            force_reset=False,
            stop_on_error=False
        )
        
        print(f"✅ Bulk reset completado!")
        print(f"   Total solicitadas: {bulk_result['total_requested']}")
        print(f"   Exitosas: {bulk_result['successful']}")
        print(f"   Fallidas: {bulk_result['failed']}")
        print(f"   Omitidas: {bulk_result['skipped']}")
        
        # Verificar resultados
        for invoice in created_invoices:
            updated_invoice = db.query(Invoice).filter(Invoice.id == invoice.id).first()
            print(f"   {updated_invoice.number}: {invoice.status} → {updated_invoice.status}")
        
        # Verificaciones
        expected_successful = 3  # POSTED + 2 CANCELLED
        assert bulk_result['successful'] == expected_successful, f"Se esperaban {expected_successful} exitosas, se obtuvieron {bulk_result['successful']}"
        
        print("✅ Bulk reset funcionó correctamente con facturas canceladas!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba bulk: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()
        # Limpiar archivo de test
        if os.path.exists("test_bulk_reset_cancelled.db"):
            os.remove("test_bulk_reset_cancelled.db")


if __name__ == "__main__":
    print("🧪 Ejecutando tests de reset de facturas canceladas...\n")
    
    # Test individual
    success1 = test_reset_cancelled_invoice()
    
    # Test bulk
    success2 = test_bulk_reset_cancelled_invoices()
    
    if success1 and success2:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        print("✅ Las facturas canceladas ahora se pueden restablecer a borrador")
    else:
        print("\n❌ Algunos tests fallaron")
        sys.exit(1)
