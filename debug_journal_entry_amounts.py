"""
Script para debuggear por qué los asientos contables muestran montos en 0
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
    # Buscar la factura VEN/2025/0003
    invoice = db.query(Invoice).filter(Invoice.number == "VEN/2025/0003").first()
    
    if not invoice:
        print("❌ Factura VEN/2025/0003 no encontrada")
        exit(1)
    
    print(f"✅ Factura encontrada: {invoice.number}")
    print(f"   Estado: {invoice.status}")
    print(f"   Tipo: {invoice.invoice_type}")
    print(f"   Total: {invoice.total_amount}")
    print(f"   Subtotal: {invoice.subtotal}")
    print(f"   Impuestos: {invoice.tax_amount}")
    print(f"   Descuentos: {invoice.discount_amount}")
    print(f"   Journal Entry ID: {invoice.journal_entry_id}")
    
    # Obtener líneas de la factura
    lines = db.query(InvoiceLine).filter(InvoiceLine.invoice_id == invoice.id).all()
    print(f"\n📋 Líneas de la factura ({len(lines)}):")
    
    total_calculated = Decimal('0')
    for i, line in enumerate(lines, 1):
        line_subtotal = line.quantity * line.unit_price
        discount_amount = Decimal('0')
        if line.discount_percentage:
            discount_amount = line_subtotal * (line.discount_percentage / 100)
        line_total = line_subtotal - discount_amount
        total_calculated += line_total
        
        print(f"   Línea {i}:")
        print(f"     Descripción: {line.description}")
        print(f"     Cantidad: {line.quantity}")
        print(f"     Precio unitario: {line.unit_price}")
        print(f"     Subtotal (qty * price): {line_subtotal}")
        print(f"     Descuento %: {line.discount_percentage}")
        print(f"     Descuento $: {discount_amount}")
        print(f"     Total línea: {line_total}")
        print(f"     Account ID: {line.account_id}")
    
    print(f"\n💰 Total calculado de líneas: {total_calculated}")
    
    # Buscar el journal entry
    if invoice.journal_entry_id:
        journal_entry = db.query(JournalEntry).options(
            joinedload(JournalEntry.lines).joinedload(JournalEntryLine.account)
        ).filter(JournalEntry.id == invoice.journal_entry_id).first()
        
        if journal_entry:
            print(f"\n📊 Asiento contable: {journal_entry.number}")
            print(f"   Estado: {journal_entry.status}")
            print(f"   Descripción: {journal_entry.description}")
            
            je_lines = db.query(JournalEntryLine).filter(
                JournalEntryLine.journal_entry_id == journal_entry.id
            ).order_by(JournalEntryLine.line_number).all()
            
            total_debit = Decimal('0')
            total_credit = Decimal('0')
            
            print(f"\n📝 Líneas del asiento ({len(je_lines)}):")
            for je_line in je_lines:
                account = db.query(Account).filter(Account.id == je_line.account_id).first()
                account_name = account.name if account else "Cuenta no encontrada"
                
                total_debit += je_line.debit_amount
                total_credit += je_line.credit_amount
                
                print(f"   Línea {je_line.line_number}:")
                print(f"     Cuenta: {account_name} ({je_line.account_id})")
                print(f"     Descripción: {je_line.description}")
                print(f"     Débito: {je_line.debit_amount}")
                print(f"     Crédito: {je_line.credit_amount}")
            
            print(f"\n💸 Totales del asiento:")
            print(f"   Total Débito: {total_debit}")
            print(f"   Total Crédito: {total_credit}")
            print(f"   Balance: {total_debit - total_credit}")
            
            if total_debit == 0 and total_credit == 0:
                print("\n🚨 PROBLEMA DETECTADO: Todas las líneas del asiento tienen montos en 0")
                print("\nPosibles causas:")
                print("1. Las líneas de la factura tienen cantidad o precio en 0")
                print("2. Error en el cálculo de descuentos")
                print("3. Error en la determinación de cuentas contables")
                print("4. Error en el procesamiento de payment terms")
        else:
            print("❌ Journal entry no encontrado")
    else:
        print("❌ La factura no tiene journal entry asociado")

except Exception as e:
    print(f"❌ Error durante el debug: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
