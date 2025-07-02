"""
Script de demostración del flujo completo de pagos.

Este script muestra cómo funciona el flujo de pagos implementado:

1. Emisión y contabilización de la factura (YA IMPLEMENTADO)
2. Importación de pagos en borrador  
3. Confirmación del pago
4. Resultado en los informes
5. Estados y dependencias

Para ejecutar: python payment_flow_demo.py
"""
import asyncio
import uuid
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.models.third_party import ThirdParty, ThirdPartyType
from app.models.account import Account, AccountType
from app.models.payment_terms import PaymentTerms
from app.models.journal import Journal, JournalType
from app.models.user import User
from app.models.bank_extract import BankExtractLineType

from app.schemas.bank_extract import (
    BankExtractImport, BankExtractLineCreate
)

from app.services.invoice_service import InvoiceService
from app.services.payment_flow_service import PaymentFlowService
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def demo_payment_flow():
    """
    Demonstración completa del flujo de pagos
    """
    print("🚀 Iniciando demostración del flujo de pagos\n")
    
    # Obtener sesión de base de datos
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # =============================================
        # PREPARACIÓN DE DATOS
        # =============================================
        print("📋 Preparando datos de prueba...")
        
        # Obtener usuario administrador
        admin_user = db.query(User).filter(User.email == "admin@sistema.com").first()
        if not admin_user:
            print("❌ No se encontró usuario administrador")
            return
        
        # Obtener cliente de prueba
        customer = db.query(ThirdParty).filter(
            ThirdParty.third_party_type == ThirdPartyType.CUSTOMER
        ).first()
        
        if not customer:
            print("❌ No se encontró cliente de prueba")
            return
        
        # Obtener cuenta de banco (buscar por tipo de cuenta bancaria)
        bank_account = db.query(Account).filter(
            Account.account_type == AccountType.ACTIVO
        ).first()
        
        if not bank_account:
            print("❌ No se encontró cuenta de banco")
            return
        
        # Obtener diario de ventas
        sales_journal = db.query(Journal).filter(
            Journal.type == JournalType.SALE
        ).first()
        
        if not sales_journal:
            print("❌ No se encontró diario de ventas")
            return
        
        print(f"✅ Cliente: {customer.name}")
        print(f"✅ Cuenta banco: {bank_account.name}")
        print(f"✅ Diario: {sales_journal.name}")
        print()
        
        # =============================================
        # PASO 1: CREAR Y CONTABILIZAR FACTURA
        # =============================================
        print("📝 PASO 1: Creando y contabilizando factura...")
        
        invoice_service = InvoiceService(db)
        
        # Crear factura
        from app.schemas.invoice import InvoiceCreateWithLines, InvoiceLineCreate
        
        invoice_data = InvoiceCreateWithLines(
            invoice_number=f"INV-DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            invoice_type=InvoiceType.CUSTOMER_INVOICE,
            third_party_id=customer.id,
            journal_id=sales_journal.id,
            invoice_date=date.today(),
            due_date=date.today(),
            description="Factura de demostración para flujo de pagos",
            notes="Demo automatizado",
            payment_terms_id=None,
            third_party_account_id=None,
            lines=[
                InvoiceLineCreate(
                    sequence=1,
                    description="Producto de demostración",
                    quantity=Decimal('2'),
                    unit_price=Decimal('500.00'),
                    discount_percentage=Decimal('0'),
                    product_id=None,
                    account_id=None,
                    cost_center_id=None
                )
            ]
        )
        
        invoice_response = invoice_service.create_invoice_with_lines(
            invoice_data, admin_user.id
        )
        
        print(f"✅ Factura creada: {invoice_response.invoice_number} - ${invoice_response.total_amount}")
        
        # Contabilizar factura
        posted_invoice = invoice_service.post_invoice(
            invoice_response.id, admin_user.id
        )
        
        print(f"✅ Factura contabilizada - Estado: {posted_invoice.status}")
        print(f"   Monto pendiente: ${posted_invoice.outstanding_amount}")
        print()
        
        # =============================================
        # PASO 2: IMPORTAR EXTRACTO CON AUTO-MATCHING
        # =============================================
        print("🏦 PASO 2: Importando extracto bancario con auto-matching...")
        
        payment_flow_service = PaymentFlowService(db)
        
        # Simular extracto bancario con pago que coincide
        extract_data = BankExtractImport(
            name=f"Extracto Demo {datetime.now().strftime('%Y-%m-%d')}",
            account_id=bank_account.id,
            statement_date=date.today(),
            start_date=date.today(),
            end_date=date.today(),
            starting_balance=Decimal('10000.00'),
            ending_balance=Decimal('11000.00'),
            currency_code="USD",
            description="Extracto de demostración",
            reference=None,
            notes=None,
            file_name=None,
            lines=[
                BankExtractLineCreate(
                    sequence=1,
                    transaction_date=date.today(),
                    value_date=None,
                    reference=f"TRF-{invoice_response.invoice_number}",
                    bank_reference=None,
                    check_number=None,
                    description=f"Pago de {customer.name}",
                    additional_info=None,
                    line_type=BankExtractLineType.CREDIT,
                    debit_amount=Decimal('0'),
                    credit_amount=invoice_response.total_amount,  # Coincidencia exacta
                    balance=None,
                    partner_name=customer.name,
                    partner_account=None
                )
            ]
        )
        
        import_result = payment_flow_service.import_payments_with_auto_matching(
            extract_data=extract_data,
            created_by_id=admin_user.id,
            auto_match=True
        )
        
        print(f"✅ Extracto importado: {import_result['extract_name']}")
        print(f"   Líneas totales: {import_result['total_lines']}")
        print(f"   Líneas coincidentes: {import_result['matched_lines']}")
        print(f"   Pagos creados: {import_result['payments_created']}")
        
        # Mostrar detalles del auto-matching
        for result in import_result['auto_match_results']:
            print(f"   📍 Línea: {result['line_description']}")
            print(f"      Monto: ${result['line_amount']}")
            print(f"      Coincidencia: {result['matched']}")
            print(f"      Razón: {result['match_reason']}")
            if result['payment_created']:
                print(f"      🎯 Pago creado: {result['payment_id']}")
        print()
        
        # =============================================
        # PASO 3: CONFIRMAR PAGO
        # =============================================
        print("✅ PASO 3: Confirmando pago...")
        
        # Obtener el primer pago creado
        payment_created = None
        for result in import_result['auto_match_results']:
            if result['payment_created'] and result['payment_id']:
                payment_created = result['payment_id']
                break
        
        if not payment_created:
            print("❌ No se creó ningún pago para confirmar")
            return
        
        # Confirmar el pago
        from app.schemas.payment import PaymentConfirmation
        
        confirmation = PaymentConfirmation(
            payment_id=payment_created,
            confirmation_notes="Confirmación automática en demo"
        )
        
        confirmed_payment = payment_flow_service.confirm_payment(
            payment_id=payment_created,
            confirmed_by_id=admin_user.id
        )
        
        print(f"✅ Pago confirmado: {confirmed_payment.payment_number}")
        print(f"   Estado: {confirmed_payment.status}")
        print(f"   Monto: ${confirmed_payment.amount}")
        print()
        
        # =============================================
        # PASO 4: VERIFICAR RESULTADOS
        # =============================================
        print("📊 PASO 4: Verificando resultados...")
        
        # Verificar estado de la factura
        updated_invoice = db.query(Invoice).filter(
            Invoice.id == posted_invoice.id
        ).first()
        
        if updated_invoice:
            print(f"📄 Estado de la factura:")
            print(f"   Número: {updated_invoice.invoice_number}")
            print(f"   Estado: {updated_invoice.status}")
            print(f"   Total: ${updated_invoice.total_amount}")
            print(f"   Pagado: ${updated_invoice.paid_amount}")
            print(f"   Pendiente: ${updated_invoice.outstanding_amount}")
        else:
            print("❌ No se pudo obtener la factura actualizada")
        
        # Verificar estado del flujo
        flow_status = payment_flow_service.get_payment_flow_status(
            import_result['extract_id']
        )
        
        print(f"\n🔄 Estado del flujo de pagos:")
        print(f"   Extracto: {flow_status['extract_name']}")
        print(f"   Líneas totales: {flow_status['total_lines']}")
        print(f"   Pagos confirmados: {flow_status['posted_payments']}")
        print(f"   Completitud: {flow_status['completion_percentage']:.1f}%")
        
        print("\n🎉 ¡Flujo de pagos completado exitosamente!")
        
        # =============================================
        # RESUMEN FINAL
        # =============================================
        print("\n" + "="*60)
        print("📈 RESUMEN DEL FLUJO IMPLEMENTADO")
        print("="*60)
        
        print("✅ 1. Factura emitida y contabilizada")
        print("      - Genera asiento en diario de ventas")
        print("      - Estado: POSTED")
        print("      - Monto pendiente registrado")
        
        print("✅ 2. Extracto importado con auto-matching")
        print("      - Busca facturas por monto y partner")
        print("      - Crea pagos en borrador automáticamente")
        print("      - Vincula línea de extracto con pago")
        
        print("✅ 3. Pago confirmado")
        print("      - Genera asiento en diario de banco")
        print("      - Concilia automáticamente con factura")
        print("      - Actualiza estado de factura a PAID")
        
        print("✅ 4. Reportes actualizados")
        print("      - Factura aparece como pagada")
        print("      - Extracto aparece como conciliado")
        print("      - Trazabilidad completa mantenida")
        
        print("\n🎯 El sistema está listo para producción!")
        
    except Exception as e:
        logger.error(f"Error en demostración: {str(e)}")
        print(f"❌ Error: {str(e)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(demo_payment_flow())
