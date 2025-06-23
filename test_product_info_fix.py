#!/usr/bin/env python3
"""
Test script para verificar que la información de productos se incluye correctamente
en las respuestas de las líneas de factura.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.invoice_service import InvoiceService
from app.models.invoice import Invoice, InvoiceLine
from app.models.product import Product


def test_product_info_in_invoice_lines():
    """
    Test que verifica que la información del producto se incluye en las líneas de factura
    """
    # Configurar conexión a la base de datos
    engine = create_engine("sqlite:///test_product_info.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Inicializar el servicio
        invoice_service = InvoiceService(db)
        
        # Buscar una factura con líneas que tengan productos
        invoice_with_product_lines = db.query(Invoice).join(InvoiceLine).join(Product).first()
        
        if not invoice_with_product_lines:
            print("❌ No se encontraron facturas con líneas que tengan productos asociados")
            print("ℹ️  Para probar esta funcionalidad, primero cree una factura con líneas que incluyan productos")
            return
        
        print(f"✅ Factura encontrada: {invoice_with_product_lines.number}")
          # Obtener la factura con líneas usando el método actualizado
        invoice_with_lines = invoice_service.get_invoice_with_lines(invoice_with_product_lines.id)
        
        print(f"📄 Factura: {invoice_with_lines.invoice_number}")
        print(f"📝 Líneas: {len(invoice_with_lines.lines)}")
        
        # Verificar que las líneas incluyen información del producto
        for i, line in enumerate(invoice_with_lines.lines):
            print(f"\n--- Línea {i + 1} ---")
            print(f"Descripción: {line.description}")
            print(f"Producto ID: {line.product_id}")
            print(f"Producto Nombre: {line.product_name}")
            print(f"Producto Código: {line.product_code}")
            
            if line.product_id and line.product_name:
                print("✅ Información del producto incluida correctamente")
            elif line.product_id and not line.product_name:
                print("❌ Producto ID presente pero falta información del producto")
            else:
                print("ℹ️  Línea sin producto asociado")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("🧪 Probando que la información de productos se incluye en las líneas de factura...")
    test_product_info_in_invoice_lines()
