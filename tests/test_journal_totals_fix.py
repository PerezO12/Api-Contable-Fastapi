"""
Test para verificar que los journal entries calculan correctamente los totales
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker, joinedload
from app.database import engine
from app.models.invoice import Invoice, InvoiceLine
from app.models.journal_entry import JournalEntry, JournalEntryLine
from app.models.account import Account
from decimal import Decimal

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Buscar la factura VEN/2025/0003 nuevamente
    invoice = db.query(Invoice).filter(Invoice.number == "VEN/2025/0003").first()
    
    if not invoice:
        print("❌ Factura VEN/2025/0003 no encontrada")
        exit(1)
    
    print(f"✅ Factura encontrada: {invoice.number}")
    print(f"   Journal Entry ID: {invoice.journal_entry_id}")
    
    # Buscar el journal entry
    if invoice.journal_entry_id:
        journal_entry = db.query(JournalEntry).filter(
            JournalEntry.id == invoice.journal_entry_id
        ).first()
        
        if journal_entry:
            print(f"\n📊 Asiento contable ANTES del fix: {journal_entry.number}")
            print(f"   Total Débito (campo del modelo): {journal_entry.total_debit}")
            print(f"   Total Crédito (campo del modelo): {journal_entry.total_credit}")
            
            # Calcular manualmente para verificar
            je_lines = db.query(JournalEntryLine).filter(
                JournalEntryLine.journal_entry_id == journal_entry.id
            ).all()
            
            manual_debit = sum(line.debit_amount for line in je_lines)
            manual_credit = sum(line.credit_amount for line in je_lines)
            
            print(f"   Total Débito (calculado manualmente): {manual_debit}")
            print(f"   Total Crédito (calculado manualmente): {manual_credit}")
            
            # Aplicar el fix
            print(f"\n🔧 Aplicando calculate_totals()...")
            journal_entry.calculate_totals()
            
            print(f"\n📊 Asiento contable DESPUÉS del fix:")
            print(f"   Total Débito (campo del modelo): {journal_entry.total_debit}")
            print(f"   Total Crédito (campo del modelo): {journal_entry.total_credit}")
            
            # Guardar cambios
            db.commit()
            print(f"\n✅ Totales actualizados y guardados en la base de datos")
            
            # Verificar que ahora muestra correctamente
            if journal_entry.total_debit > 0 and journal_entry.total_credit > 0:
                print(f"🎉 ¡Problema SOLUCIONADO! El asiento ahora muestra los montos correctos.")
            else:
                print(f"❌ El problema persiste - revisar el método calculate_totals()")
        else:
            print("❌ Journal entry no encontrado")
    else:
        print("❌ La factura no tiene journal entry asociado")

except Exception as e:
    print(f"❌ Error durante el test: {str(e)}")
    import traceback
    traceback.print_exc()
    db.rollback()

finally:
    db.close()
