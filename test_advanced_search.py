#!/usr/bin/env python3
"""
Test script para validar las búsquedas avanzadas en facturas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.invoice_service import InvoiceService
from app.models.invoice import InvoiceStatus, InvoiceType

def test_advanced_search():
    """
    Probar diferentes filtros de búsqueda avanzada
    """
    # Obtener sesión de base de datos
    db = next(get_db())
    service = InvoiceService(db)
    
    print("=== TEST: Búsquedas Avanzadas de Facturas ===")
      # 1. Buscar por número de factura
    print("\n1. Búsqueda por número de factura:")
    try:
        result = service.get_invoices(invoice_number="FAC")
        print(f"   Facturas encontradas con 'FAC' en el número: {result.total}")
        for invoice in result.items[:3]:  # Mostrar solo las primeras 3
            print(f"   - {invoice.invoice_number}: {invoice.description or 'Sin descripción'}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Búsqueda por rango de fechas
    print("\n2. Búsqueda por rango de fechas (últimos 30 días):")
    try:
        from datetime import timedelta
        date_from = date.today() - timedelta(days=30)
        result = service.get_invoices(date_from=date_from)
        print(f"   Facturas desde {date_from}: {result.total}")
        for invoice in result.items[:3]:
            print(f"   - {invoice.invoice_number}: {invoice.invoice_date}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Búsqueda solo fecha hasta
    print("\n3. Búsqueda por fecha hasta (hasta hoy):")
    try:
        date_to = date.today()
        result = service.get_invoices(date_to=date_to)
        print(f"   Facturas hasta {date_to}: {result.total}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Búsqueda por tercero (nombre)
    print("\n4. Búsqueda por nombre de tercero:")
    try:
        result = service.get_invoices(third_party_name="Cliente")
        print(f"   Facturas con 'Cliente' en el nombre: {result.total}")
        for invoice in result.items[:3]:
            print(f"   - {invoice.invoice_number}: {getattr(invoice, 'third_party_name', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Búsqueda por descripción
    print("\n5. Búsqueda por descripción:")
    try:
        result = service.get_invoices(description="servicio")
        print(f"   Facturas con 'servicio' en la descripción: {result.total}")
        for invoice in result.items[:3]:
            print(f"   - {invoice.invoice_number}: {invoice.description or 'Sin descripción'}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 6. Búsqueda por monto mínimo
    print("\n6. Búsqueda por monto mínimo (>= 100000):")
    try:
        result = service.get_invoices(amount_from=Decimal('100000'))
        print(f"   Facturas con monto >= 100,000: {result.total}")
        for invoice in result.items[:3]:
            print(f"   - {invoice.invoice_number}: ${invoice.total_amount or 0:,.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 7. Búsqueda por rango de montos
    print("\n7. Búsqueda por rango de montos (50000 - 500000):")
    try:
        result = service.get_invoices(
            amount_from=Decimal('50000'),
            amount_to=Decimal('500000')
        )
        print(f"   Facturas entre $50,000 y $500,000: {result.total}")
        for invoice in result.items[:3]:
            print(f"   - {invoice.invoice_number}: ${invoice.total_amount or 0:,.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 8. Búsqueda por estado
    print("\n8. Búsqueda por estado (POSTED):")
    try:
        result = service.get_invoices(status=InvoiceStatus.POSTED)
        print(f"   Facturas en estado POSTED: {result.total}")
        for invoice in result.items[:3]:
            print(f"   - {invoice.invoice_number}: {invoice.status}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 9. Búsqueda combinada
    print("\n9. Búsqueda combinada (estado + rango de fechas + ordenamiento):")
    try:
        result = service.get_invoices(
            status=InvoiceStatus.POSTED,
            date_from=date(2024, 1, 1),
            sort_by="total_amount",
            sort_order="desc",
            limit=5
        )
        print(f"   Facturas POSTED desde 2024, ordenadas por monto desc: {result.total}")
        for invoice in result.items:
            print(f"   - {invoice.invoice_number}: ${invoice.total_amount or 0:,.2f} ({invoice.status})")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 10. Test de ordenamiento
    print("\n10. Test de ordenamiento por fecha ascendente:")
    try:
        result = service.get_invoices(
            sort_by="invoice_date",
            sort_order="asc",
            limit=5
        )
        print(f"   Primeras 5 facturas por fecha (más antiguas):")
        for invoice in result.items:
            print(f"   - {invoice.invoice_number}: {invoice.invoice_date}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n=== FIN DE PRUEBAS ===")

if __name__ == "__main__":
    test_advanced_search()
