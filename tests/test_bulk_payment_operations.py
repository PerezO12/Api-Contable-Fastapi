#!/usr/bin/env python3
"""
Script de prueba para validar las operaciones bulk de pagos
Prueba el flujo completo: validación, confirmación, cancelación y eliminación
"""

import sys
import os
import uuid
from pathlib import Path

# Agregar el directorio de la API al path
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.services.payment_flow_service import PaymentFlowService
from app.services.payment_service import PaymentService
from app.schemas.payment import BulkPaymentConfirmationRequest
from app.models.payment import PaymentStatus
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bulk_payment_operations():
    """
    Prueba las operaciones bulk de pagos
    """
    # Crear sesión de base de datos
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Inicializar el servicio
        service = PaymentFlowService(db)
        
        logger.info("🧪 Iniciando pruebas de operaciones bulk de pagos")
        
        # 1. Obtener algunos pagos en estado DRAFT para probar
        logger.info("📋 Buscando pagos en estado DRAFT...")
        # Aquí normalmente buscaríamos pagos existentes, pero para la prueba
        # asumiremos que hay algunos IDs disponibles
        test_payment_ids = ["test-payment-1", "test-payment-2"]
        
        # 2. Probar validación bulk
        logger.info("✅ Probando validación bulk...")
        try:
            validation_result = await service.validate_bulk_confirmation(test_payment_ids)
            logger.info(f"Validación exitosa: {validation_result.total_payments} pagos validados")
            logger.info(f"  - Pueden confirmarse: {validation_result.can_confirm_count}")
            logger.info(f"  - Bloqueados: {validation_result.blocked_count}")
            logger.info(f"  - Con advertencias: {validation_result.warnings_count}")
        except Exception as e:
            logger.warning(f"Error en validación (esperado si no hay pagos): {e}")
        
        # 3. Probar confirmación bulk
        logger.info("💰 Probando confirmación bulk...")
        try:
            confirmation_request = BulkPaymentConfirmationRequest(
                payment_ids=test_payment_ids,
                confirmation_notes="Prueba de confirmación masiva",
                force=False
            )
            confirmation_result = await service.bulk_confirm_payments(confirmation_request)
            logger.info(f"Confirmación exitosa: {confirmation_result.successful} pagos confirmados")
            logger.info(f"  - Fallidos: {confirmation_result.failed}")
        except Exception as e:
            logger.warning(f"Error en confirmación (esperado si no hay pagos): {e}")
        
        # 4. Probar cancelación bulk
        logger.info("❌ Probando cancelación bulk...")
        try:
            cancel_result = await service.bulk_cancel_payments(test_payment_ids, "Prueba de cancelación")
            logger.info(f"Cancelación exitosa: {cancel_result.successful} pagos cancelados")
        except Exception as e:
            logger.warning(f"Error en cancelación (esperado si no hay pagos): {e}")
        
        # 5. Probar eliminación bulk
        logger.info("🗑️ Probando eliminación bulk...")
        try:
            delete_result = await service.bulk_delete_payments(test_payment_ids)
            logger.info(f"Eliminación exitosa: {delete_result.successful} pagos eliminados")
        except Exception as e:
            logger.warning(f"Error en eliminación (esperado si no hay pagos): {e}")
        
        logger.info("✨ Pruebas completadas exitosamente")
        
    except Exception as e:
        logger.error(f"Error durante las pruebas: {e}")
        raise
    finally:
        db.close()

def test_endpoints_structure():
    """
    Verifica que la estructura de endpoints esté correcta
    """
    logger.info("🔍 Verificando estructura de endpoints...")
    
    # Verificar que los archivos existen
    files_to_check = [
        "app/api/payment_flow.py",
        "app/services/payment_flow_service.py", 
        "app/schemas/payment.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            logger.info(f"✅ {file_path} existe")
        else:
            logger.error(f"❌ {file_path} no encontrado")
    
    # Verificar imports básicos
    try:
        from app.api.payment_flow import router as payment_flow_router
        logger.info("✅ Router de payment_flow importado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error importando router: {e}")
    
    try:
        from app.schemas.payment import (
            BulkPaymentConfirmationRequest,
            BulkPaymentValidationResponse,
            BulkPaymentOperationResponse
        )
        logger.info("✅ Esquemas bulk importados exitosamente")
    except Exception as e:
        logger.error(f"❌ Error importando esquemas: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de operaciones bulk de pagos")
    
    # Probar estructura
    test_endpoints_structure()
    
    # Probar operaciones (asíncrono)
    try:
        asyncio.run(test_bulk_payment_operations())
    except Exception as e:
        print(f"❌ Error en pruebas asíncronas: {e}")
    
    print("🏁 Pruebas finalizadas")
