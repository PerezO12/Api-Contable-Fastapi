"""
Script de validación básica del sistema de pagos y facturación
"""
from app.database import SessionLocal
from app.services.payment_service import PaymentService
from app.services.invoice_service import InvoiceService
from app.services.bank_extract_service import BankExtractService
from app.services.bank_reconciliation_service import BankReconciliationService
from sqlalchemy import text

def validate_services():
    """Validar que los servicios se puedan instanciar correctamente"""
    with SessionLocal() as db:
        try:
            # Verificar instanciación de servicios
            payment_service = PaymentService(db)
            print("✅ PaymentService: OK")
            
            invoice_service = InvoiceService(db)
            print("✅ InvoiceService: OK")
            
            bank_extract_service = BankExtractService(db)
            print("✅ BankExtractService: OK")
            
            bank_reconciliation_service = BankReconciliationService(db)
            print("✅ BankReconciliationService: OK")
            
            # Verificar tablas
            tables = [
                'payments', 'payment_invoices', 'invoices', 'invoice_lines',
                'bank_extracts', 'bank_extract_lines', 'bank_reconciliations'
            ]
            
            for table in tables:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"✅ Tabla {table}: {count} registros")
                except Exception as e:
                    print(f"❌ Error en tabla {table}: {e}")
            
            print("\n🎉 Validación completada exitosamente!")
            
        except Exception as e:
            print(f"❌ Error durante la validación: {e}")
            raise

if __name__ == "__main__":
    validate_services()
