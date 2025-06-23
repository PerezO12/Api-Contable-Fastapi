#!/usr/bin/env python3
"""
Script para verificar si las líneas de factura devuelven información de productos
"""
import uuid
from app.database import get_session
from app.services.invoice_service import InvoiceService

def test_invoice_with_product_info():
    # Conectar a la base de datos
    db = next(get_session())
    service = InvoiceService(db)

    # Obtener una factura específica
    invoice_id = 'bf85f55a-5ea6-46cc-ae7a-e2db2ba7e6c5'
    try:
        invoice = service.get_invoice_with_lines(uuid.UUID(invoice_id))
        print('Factura obtenida:')
        print(f'ID: {invoice.id}')
        print(f'Número: {invoice.invoice_number}')
        print(f'Líneas: {len(invoice.lines)}')
        
        for i, line in enumerate(invoice.lines):
            print(f'Línea {i+1}:')
            print(f'  Product ID: {line.product_id}')
            print(f'  Product Name: {line.product_name if hasattr(line, "product_name") else "NO DISPONIBLE"}')
            print(f'  Product Code: {line.product_code if hasattr(line, "product_code") else "NO DISPONIBLE"}')
            print(f'  Description: {line.description}')
            
            # Verificar el tipo de objeto
            print(f'  Tipo de línea: {type(line)}')
            print(f'  Atributos: {[attr for attr in dir(line) if not attr.startswith("_")]}')
            print('---')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_invoice_with_product_info()
