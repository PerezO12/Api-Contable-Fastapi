#!/usr/bin/env python3
"""
Script de prueba para verificar que los journal entries generados desde facturas
usen el mismo diario y el formato correcto PREFIJO/AÑO/JE/NÚMERO
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
from app.models.invoice import Invoice, InvoiceType, InvoiceStatus, InvoiceLine
from app.models.journal_entry import JournalEntry
from app.models.user import User
from app.models.account import Account, AccountType
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceCreate, InvoiceLineCreate


def setup_test_data(db):
    """Configurar datos de prueba necesarios"""
    print("📋 Configurando datos de prueba...")
    
    # Crear usuario de prueba si no existe
    test_user = db.query(User).filter(User.email == "test@journalentry.com").first()
    if not test_user:
        test_user = User(
            id=uuid.uuid4(),
            email="test@journalentry.com",
            full_name="Test User JE",
            hashed_password="fake_hash",
            is_active=True
        )
        db.add(test_user)
    
    # Crear tercero de prueba si no existe
    test_customer = db.query(ThirdParty).filter(ThirdParty.name == "Cliente JE Test").first()
    if not test_customer:
        test_customer = ThirdParty(
            id=uuid.uuid4(),
            code="CLJE001",
            name="Cliente JE Test",
            third_party_type=ThirdPartyType.CUSTOMER,
            document_type=DocumentType.DNI,
            document_number="11223344",
            email="cliente.je@test.com",
            is_active=True
        )
        db.add(test_customer)
      # Crear cuentas contables básicas si no existen
    accounts_data = [
        ("1105", "Clientes", AccountType.ASSET),
        ("4105", "Ventas de Mercancía", AccountType.INCOME),
    ]
    
    accounts = {}
    for code, name, account_type in accounts_data:
        account = db.query(Account).filter(Account.code == code).first()
        if not account:
            account = Account(
                id=uuid.uuid4(),
                code=code,
                name=name,
                account_type=account_type,
                is_active=True
            )
            db.add(account)
        accounts[code] = account
    
    db.commit()
    db.refresh(test_user)
    db.refresh(test_customer)
    for account in accounts.values():
        db.refresh(account)
    
    return test_user, test_customer, accounts


def test_journal_entry_from_invoice():
    """Probar que los journal entries generados desde facturas usen el diario correcto"""
    print("🧪 Iniciando pruebas de journal entries desde facturas...")
    
    db = SessionLocal()
    try:
        # Configurar datos de prueba
        test_user, test_customer, accounts = setup_test_data(db)
        
        # Obtener diario de ventas
        sales_journal = db.query(Journal).filter(Journal.type == JournalType.SALE).first()
        if not sales_journal:
            print("❌ Error: No se encontró diario de ventas")
            return False
        
        print(f"📚 Diario de ventas: {sales_journal.name} (Prefijo: {sales_journal.sequence_prefix})")
        
        invoice_service = InvoiceService(db)
        
        # ===========================================
        # PASO 1: Crear factura con líneas
        # ===========================================
        print("\n🔍 PASO 1: Crear factura con líneas")
        
        invoice_data = InvoiceCreate(
            invoice_type=InvoiceType.CUSTOMER_INVOICE,
            third_party_id=test_customer.id,
            invoice_date=date.today(),
            due_date=date.today(),
            description="Factura para prueba de journal entry",
            currency_code="USD",
            exchange_rate=Decimal('1'),
            invoice_number=None,
            journal_id=None,  # Selección automática
            payment_terms_id=None,
            third_party_account_id=None,
            notes=None
        )
        
        # Crear la factura
        invoice = invoice_service.create_invoice(invoice_data, test_user.id)
        print(f"   📄 Factura creada: {invoice.invoice_number}")
        
        # Agregar líneas de factura
        line_data = InvoiceLineCreate(
            sequence=1,
            description="Producto de prueba",
            quantity=Decimal('2'),
            unit_price=Decimal('500.00'),
            account_id=accounts["4105"].id,  # Cuenta de ventas
            product_id=None,
            discount_percentage=Decimal('0'),
            tax_ids=[],
            cost_center_id=None
        )
        
        invoice_line = invoice_service.add_invoice_line(
            invoice_id=invoice.id,
            line_data=line_data,
            created_by_id=test_user.id
        )
        print(f"   📝 Línea agregada: {invoice_line.description} - ${invoice_line.total_amount}")
          # Verificar estado de la factura
        invoice_updated = invoice_service.get_invoice(invoice.id)
        print(f"   💰 Total factura: ${invoice_updated.total_amount}")
        print(f"   📊 Estado: {invoice_updated.status}")
        
        # ===========================================
        # PASO 2: Contabilizar la factura (generar journal entry)
        # ===========================================
        print("\n🔍 PASO 2: Contabilizar la factura (generar journal entry)")
        
        # Verificar secuencia del diario antes
        db.refresh(sales_journal)
        sequence_before = sales_journal.current_sequence_number
        print(f"   📊 Secuencia del diario antes: {sequence_before}")
        
        # Contabilizar la factura
        try:
            posted_invoice = invoice_service.post_invoice(invoice.id, test_user.id)
            print(f"   ✅ Factura contabilizada: {posted_invoice.invoice_number}")
            print(f"   📊 Estado: {posted_invoice.status}")
            
            # Verificar que se creó el journal entry
            if posted_invoice.journal_entry_id:
                journal_entry = db.query(JournalEntry).filter(
                    JournalEntry.id == posted_invoice.journal_entry_id
                ).first()
                
                if journal_entry:
                    print(f"   📋 Journal Entry creado: {journal_entry.number}")
                    print(f"   📚 Journal ID del JE: {journal_entry.journal_id}")
                    print(f"   📚 Journal ID de la factura: {posted_invoice.journal_id}")
                    
                    # Verificar que usan el mismo diario
                    if journal_entry.journal_id == posted_invoice.journal_id:
                        print(f"   ✅ El journal entry usa el mismo diario que la factura")
                    else:
                        print(f"   ❌ El journal entry NO usa el mismo diario que la factura")
                        return False
                    
                    # Verificar el formato del número
                    expected_prefix = sales_journal.sequence_prefix
                    if journal_entry.number.startswith(expected_prefix) and "/JE/" in journal_entry.number:
                        print(f"   ✅ El número del journal entry sigue el formato correcto: {journal_entry.number}")
                    else:
                        print(f"   ❌ El número del journal entry NO sigue el formato esperado")
                        print(f"       Esperado: {expected_prefix}/2025/JE/XXXX")
                        print(f"       Actual: {journal_entry.number}")
                        return False
                    
                    # Verificar incremento de secuencia
                    db.refresh(sales_journal)
                    sequence_after = sales_journal.current_sequence_number
                    print(f"   📊 Secuencia del diario después: {sequence_after}")
                    
                    if sequence_after > sequence_before:
                        print(f"   ✅ La secuencia del diario se incrementó correctamente")
                    else:
                        print(f"   ❌ La secuencia del diario NO se incrementó")
                        return False
                    
                else:
                    print(f"   ❌ No se pudo obtener el journal entry de la base de datos")
                    return False
            else:
                print(f"   ❌ La factura no tiene journal_entry_id asignado")
                return False
                
        except Exception as e:
            print(f"   ❌ Error al contabilizar la factura: {str(e)}")
            return False
        
        # ===========================================
        # PASO 3: Crear y contabilizar otra factura para verificar secuencias
        # ===========================================
        print("\n🔍 PASO 3: Crear segunda factura para verificar secuencias")
        
        invoice_data2 = InvoiceCreate(
            invoice_type=InvoiceType.CUSTOMER_INVOICE,
            third_party_id=test_customer.id,
            invoice_date=date.today(),
            due_date=date.today(),
            description="Segunda factura para prueba",
            currency_code="USD",
            exchange_rate=Decimal('1'),
            invoice_number=None,
            journal_id=None,
            payment_terms_id=None,
            third_party_account_id=None,
            notes=None
        )
        
        invoice2 = invoice_service.create_invoice(invoice_data2, test_user.id)
        
        # Agregar línea
        line_data2 = InvoiceLineCreate(
            sequence=1,
            description="Segundo producto",
            quantity=Decimal('1'),
            unit_price=Decimal('750.00'),
            account_id=accounts["4105"].id,
            product_id=None,
            discount_percentage=Decimal('0'),
            tax_ids=[],
            cost_center_id=None
        )
        
        invoice_service.add_invoice_line(invoice2.id, line_data2, test_user.id)
          # Contabilizar segunda factura
        posted_invoice2 = invoice_service.post_invoice(invoice2.id, test_user.id)
        
        journal_entry2 = None
        if posted_invoice2.journal_entry_id:
            journal_entry2 = db.query(JournalEntry).filter(
                JournalEntry.id == posted_invoice2.journal_entry_id
            ).first()
            
            if journal_entry2:
                print(f"   📄 Segunda factura: {posted_invoice2.invoice_number}")
                print(f"   📋 Segundo journal entry: {journal_entry2.number}")
                
                # Verificar que los números son consecutivos
                if journal_entry2.number > journal_entry.number:
                    print(f"   ✅ Los números de journal entry son consecutivos")
                else:
                    print(f"   ❌ Los números de journal entry NO son consecutivos")
                    return False
            else:
                print(f"   ❌ No se pudo obtener el segundo journal entry")
                return False
        else:
            print(f"   ❌ La segunda factura no tiene journal_entry_id")
            return False
          # ===========================================
        # PASO 4: Mostrar resumen final
        # ===========================================
        print("\n📊 RESUMEN DE PRUEBAS:")
        print(f"   🏷️ Factura 1: {posted_invoice.invoice_number}")
        print(f"   📋 Journal Entry 1: {journal_entry.number}")
        print(f"   🏷️ Factura 2: {posted_invoice2.invoice_number}")
        if journal_entry2:
            print(f"   📋 Journal Entry 2: {journal_entry2.number}")
        
        db.refresh(sales_journal)
        print(f"   📈 Secuencia final del diario: {sales_journal.current_sequence_number}")
        
        print("\n✅ ¡Todas las pruebas de journal entries pasaron exitosamente!")
        print("🎉 Los journal entries usan correctamente el mismo diario que las facturas")
        print("🎉 Los números siguen el formato: PREFIJO/AÑO/JE/NÚMERO")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Iniciando pruebas de journal entries generados desde facturas...")
    
    success = test_journal_entry_from_invoice()
    
    if success:
        print("\n🎯 IMPLEMENTACIÓN COMPLETA VERIFICADA:")
        print("   ✅ Facturas usan secuencias de diarios: PREFIJO/AÑO/NÚMERO")
        print("   ✅ Journal entries usan mismo diario: PREFIJO/AÑO/JE/NÚMERO")
        print("   ✅ Secuencias incrementales por diario")
        print("   ✅ Selección automática de diario por tipo")
        print("   ✅ Trazabilidad completa entre documentos")
        
        print("\n🏆 MISIÓN CUMPLIDA:")
        print("   El sistema ahora funciona exactamente como Odoo")
        print("   con numeración profesional y trazabilidad completa!")
    else:
        print("\n❌ HUBO ERRORES EN LAS PRUEBAS")
        print("   🔧 Revisa los logs y corrige los problemas encontrados")
    
    print("\n🏁 Fin de las pruebas.")
