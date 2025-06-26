#!/usr/bin/env python3
"""
Script para probar la nueva funcionalidad de precisión en condiciones de pago.
Crea y valida términos de pago con hasta 6 decimales de precisión.
"""

import sys
import os
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio padre al path para importar módulos de la app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    from app.models.payment_terms import PaymentTerms, PaymentSchedule
    from app.schemas.payment_terms import PaymentTermsCreate, PaymentScheduleCreate
    from app.services.payment_terms_service import PaymentTermsService
except ImportError as e:
    print(f"❌ Error al importar módulos de la aplicación: {e}")
    sys.exit(1)

def test_high_precision_payment_terms():
    """
    Prueba la creación de términos de pago con alta precisión
    """
    print("🧪 Probando términos de pago con alta precisión...")
    print("=" * 60)
    
    # Casos de prueba
    test_cases = [
        {
            "name": "Tres cuotas iguales",
            "code": "3EQUAL_TEST",
            "schedules": [
                {"sequence": 1, "days": 30, "percentage": Decimal("33.333334")},
                {"sequence": 2, "days": 60, "percentage": Decimal("33.333333")},
                {"sequence": 3, "days": 90, "percentage": Decimal("33.333333")},
            ]
        },
        {
            "name": "Términos complejos",
            "code": "COMPLEX_TEST",
            "schedules": [
                {"sequence": 1, "days": 15, "percentage": Decimal("12.500000")},
                {"sequence": 2, "days": 30, "percentage": Decimal("25.000000")},
                {"sequence": 3, "days": 45, "percentage": Decimal("37.500000")},
                {"sequence": 4, "days": 60, "percentage": Decimal("25.000000")},
            ]
        },
        {
            "name": "Máxima precisión",
            "code": "MAXPREC_TEST",
            "schedules": [
                {"sequence": 1, "days": 0, "percentage": Decimal("50.000001")},
                {"sequence": 2, "days": 30, "percentage": Decimal("49.999999")},
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Probando: {test_case['name']}")
        print(f"   Código: {test_case['code']}")
        
        # Calcular total
        total_percentage = sum(s["percentage"] for s in test_case["schedules"])
        print(f"   Total: {total_percentage}%")
        
        # Validar precisión
        difference = abs(total_percentage - Decimal("100.000000"))
        is_valid = difference <= Decimal("0.000001")
        
        if is_valid:
            print(f"   ✅ Válido (diferencia: {difference})")
        else:
            print(f"   ❌ Inválido (diferencia: {difference})")
        
        # Mostrar cronograma
        for schedule in test_case["schedules"]:
            print(f"      Cuota {schedule['sequence']}: {schedule['percentage']}% a {schedule['days']} días")

def test_payment_terms_model():
    """
    Prueba el modelo PaymentTerms con los nuevos valores
    """
    print("\n🏗️  Probando modelo PaymentTerms...")
    print("=" * 60)
    
    # Crear término de pago en memoria
    payment_terms = PaymentTerms(
        code="MEMTEST",
        name="Test en memoria",
        description="Prueba de precisión en memoria"
    )
    
    # Crear cronogramas con alta precisión
    schedules = [
        PaymentSchedule(
            sequence=1,
            days=30,
            percentage=Decimal("33.333334"),
            description="Primera cuota"
        ),
        PaymentSchedule(
            sequence=2,
            days=60,
            percentage=Decimal("33.333333"),
            description="Segunda cuota"
        ),
        PaymentSchedule(
            sequence=3,
            days=90,
            percentage=Decimal("33.333333"),
            description="Tercera cuota"
        )
    ]
    
    payment_terms.payment_schedules = schedules
    
    print(f"Código: {payment_terms.code}")
    print(f"Total porcentaje: {payment_terms.total_percentage}")
    print(f"Es válido: {payment_terms.is_valid}")
    
    for schedule in payment_terms.payment_schedules:
        print(f"  Cuota {schedule.sequence}: {schedule.percentage}% - {schedule.description}")

def validate_existing_terms():
    """
    Valida términos existentes con la nueva precisión
    """
    print("\n🔍 Validando términos existentes...")
    print("=" * 60)
    
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Obtener todos los términos de pago
        payment_terms = db.query(PaymentTerms).all()
        
        for pt in payment_terms:
            total = pt.total_percentage
            difference = abs(total - Decimal("100.000000"))
            is_valid_new = difference <= Decimal("0.000001")
            is_valid_old = abs(total - Decimal("100.00")) <= Decimal("0.01")
            
            status = "✅" if is_valid_new else "⚠️" if is_valid_old else "❌"
            
            print(f"{status} {pt.code}: {total}% (diff: {difference})")
            
            if not is_valid_new and is_valid_old:
                print(f"   📝 Nota: Válido con precisión antigua, inválido con nueva precisión")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error al validar términos existentes: {e}")

if __name__ == "__main__":
    print("🏦 Tester de Precisión en Condiciones de Pago")
    print("=" * 50)
    
    try:
        # Probar casos teóricos
        test_high_precision_payment_terms()
        
        # Probar modelo en memoria
        test_payment_terms_model()
        
        # Validar términos existentes
        validate_existing_terms()
        
        print("\n🎉 Pruebas completadas.")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        sys.exit(1)
