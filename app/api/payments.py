"""
Payment API endpoints for managing payments.
Implements complete payment workflow following modern async patterns.
"""
import uuid
from typing import Optional, List
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, UploadFile, Form
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.payment import PaymentStatus, PaymentType
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse,
    PaymentListResponse, PaymentSummary,
    BulkPaymentResetRequest, BulkPaymentConfirmationRequest, BulkPaymentValidationRequest,
    BulkPaymentCancelRequest, BulkPaymentDeleteRequest
)
from app.services.payment_service import PaymentService
from app.services.payment_flow_service import PaymentFlowService
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.api.deps import get_current_user
from app.models.user import User
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================
# ENDPOINTS BULK DE ALTO RENDIMIENTO (hasta 1000 elementos)
# NOTA: ESTOS DEBEN IR ANTES QUE LAS RUTAS CON PATH PARAMETERS
# =============================================

@router.post("/bulk/confirm", response_model=dict)
async def bulk_confirm_payments(
    request: BulkPaymentConfirmationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirmar/Contabilizar múltiples pagos en lote de forma optimizada
    
    FLUJO CORREGIDO:
    - Solo procesa pagos en estado DRAFT
    - DRAFT → POSTED (contabilización con journal entry)
    - Temporalmente POSTED hasta implementar conciliación
    
    Permite procesar hasta 1000 pagos simultáneamente con:
    - Procesamiento en lotes para optimizar rendimiento
    - Validaciones por lotes
    - Rollback automático en caso de errores críticos
    - Reporte detallado de éxitos y errores
    
    Body format: {"payment_ids": ["uuid1", "uuid2", ...], "confirmation_notes": "optional"}
    """
    try:
        logger.info(f"🚀 [API_BULK_CONFIRM] Received bulk confirm request for {len(request.payment_ids)} payments")
        logger.info(f"👤 [API_BULK_CONFIRM] User: {current_user.email} (ID: {current_user.id})")
        logger.info(f"📝 [API_BULK_CONFIRM] Request data: {request.dict()}")
        
        # Los UUIDs ya están validados por el esquema Pydantic
        payment_uuid_list = request.payment_ids
        
        logger.info(f"🔧 [API_BULK_CONFIRM] Creating PaymentFlowService instance")
        service = PaymentFlowService(db)
        
        logger.info(f"🚀 [API_BULK_CONFIRM] Calling service.bulk_confirm_payments")
        result = await service.bulk_confirm_payments(
            payment_uuid_list, 
            current_user.id, 
            confirmation_notes=request.confirmation_notes,
            force=request.force
        )
        
        logger.info(f"✅ [API_BULK_CONFIRM] Service completed successfully")
        logger.info(f"📊 [API_BULK_CONFIRM] Service results: {result}")
        
        # Analizar los resultados para determinar el código de respuesta HTTP apropiado
        total_payments = result.get("total_payments", 0)
        successful = result.get("successful", 0)
        failed = result.get("failed", 0)
        
        logger.info(f"📊 [API_BULK_CONFIRM] Analysis: Total={total_payments}, Successful={successful}, Failed={failed}")
        
        # Si no se procesó ningún pago exitosamente, es un error crítico
        if total_payments > 0 and successful == 0:
            error_msg = f"No se pudo confirmar ningún pago. {failed} pagos fallaron."
            logger.warning(f"❌ [API_BULK_CONFIRM] Bulk confirm operation failed completely: 0/{total_payments} payments confirmed")
            logger.error(f"❌ [API_BULK_CONFIRM] Raising HTTP 422 error: {error_msg}")
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=error_msg
            )
        
        # Si más del 50% de los pagos fallaron, loggear warning
        if total_payments > 0 and (failed / total_payments) > 0.5:
            logger.warning(f"⚠️ [API_BULK_CONFIRM] Bulk confirm operation had significant failures: {successful}/{total_payments} payments confirmed")
        
        logger.info(f"✅ [API_BULK_CONFIRM] Returning successful result")
        return result
        
    except ValidationError as e:
        logger.error(f"❌ [API_BULK_CONFIRM] ValidationError: {str(e)}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        logger.error(f"❌ [API_BULK_CONFIRM] BusinessRuleError: {str(e)}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"💥 [API_BULK_CONFIRM] Unexpected error: {str(e)}")
        logger.error(f"💥 [API_BULK_CONFIRM] Exception type: {type(e).__name__}")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.post("/bulk/reset-to-draft", response_model=dict)
async def bulk_reset_payments_to_draft(
    request: BulkPaymentResetRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resetear múltiples pagos a borrador en lote desde cualquier estado
    
    Permite resetear hasta 500 pagos simultáneamente desde cualquier estado:
    - DRAFT: Ya en borrador (éxito sin cambios)
    - CONFIRMED: Solo cambio de estado
    - POSTED: Eliminación de asientos contables + cambio de estado
    - CANCELLED: Reactivación + eliminación de asientos + cambio de estado
    
    Procesamiento optimizado en lotes con reporte detallado de resultados.
    
    Body format: {"payment_ids": ["uuid1", "uuid2", ...], "reset_reason": "optional"}
    """
    try:
        # Los UUIDs ya están validados por el esquema Pydantic
        payment_uuid_list = request.payment_ids
        
        service = PaymentFlowService(db)
        result = await service.bulk_reset_to_draft(payment_uuid_list, current_user.id)
        
        # Analizar los resultados para determinar el código de respuesta HTTP apropiado
        total_payments = result.get("total_payments", 0)
        successful = result.get("successful", 0)
        failed = result.get("failed", 0)
        
        # Si no se procesó ningún pago exitosamente, es un error crítico
        if total_payments > 0 and successful == 0:
            logger.warning(f"Bulk reset operation failed completely: 0/{total_payments} payments reset")
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=f"No se pudo resetear ningún pago. {failed} pagos fallaron."
            )
        
        # Si más del 50% de los pagos fallaron, loggear warning
        if total_payments > 0 and (failed / total_payments) > 0.5:
            logger.warning(f"Bulk reset operation had significant failures: {successful}/{total_payments} payments reset")
        
        return result
        
    except ValidationError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk/cancel", response_model=dict)
async def bulk_cancel_payments(
    request: BulkPaymentCancelRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancelar múltiples pagos en lote
    
    Permite cancelar hasta 1000 pagos simultáneamente:
    - Creación de asientos de reversión
    - Reversión de conciliaciones con facturas
    - Cambio de estado a CANCELLED
    - Procesamiento optimizado en lotes
    
    Body format: {"payment_ids": ["uuid1", "uuid2", ...], "cancellation_reason": "reason"}
    """
    try:
        logger.info(f"Bulk cancel request received from user {current_user.id}")
        logger.info(f"Request payload: payment_ids count={len(request.payment_ids)}, reason='{request.cancellation_reason}'")
        
        # Los UUIDs ya están validados por el esquema Pydantic
        payment_uuid_list = request.payment_ids
        cancellation_reason = request.cancellation_reason
        
        if not payment_uuid_list:
            logger.warning("Empty payment_ids list received")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Payment IDs list cannot be empty"
            )
        
        logger.info(f"Processing bulk cancellation for {len(payment_uuid_list)} payments")
        
        service = PaymentFlowService(db)
        result = await service.bulk_cancel_payments(payment_uuid_list, current_user.id, cancellation_reason)
        
        # Analizar los resultados para determinar el código de respuesta HTTP apropiado
        total_payments = result.get("total_payments", 0)
        successful = result.get("successful", 0)
        failed = result.get("failed", 0)
        
        logger.info(f"Bulk cancellation results: {successful}/{total_payments} successful, {failed} failed")
        
        # Si no se procesó ningún pago exitosamente, es un error crítico
        if total_payments > 0 and successful == 0:
            logger.warning(f"Bulk cancel operation failed completely: 0/{total_payments} payments cancelled")
            
            # Obtener detalles de los errores para proporcionar mejor información
            error_details = []
            user_validation_errors = 0
            other_errors = 0
            
            for payment_id, result_data in result.get("results", {}).items():
                if not result_data.get("success", False):
                    error_msg = result_data.get('error', 'Unknown error')
                    error_details.append(f"Payment {payment_id}: {error_msg}")
                    
                    # Detectar errores específicos para dar mejores mensajes
                    if "User with ID" in error_msg and "not found" in error_msg:
                        user_validation_errors += 1
                    else:
                        other_errors += 1
            
            # Mensaje específico según el tipo de error más común
            if user_validation_errors > other_errors:
                summary_msg = f"Authentication error: Invalid user session. Please log in again and try again."
            else:
                error_summary = "; ".join(error_details[:3])  # Mostrar solo los primeros 3 errores
                if len(error_details) > 3:
                    error_summary += f" (and {len(error_details) - 3} more errors)"
                summary_msg = f"Unable to cancel payments. Errors: {error_summary}"
            
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=summary_msg
            )
        
        # Si más del 50% de los pagos fallaron, loggear warning
        if total_payments > 0 and (failed / total_payments) > 0.5:
            logger.warning(f"Bulk cancel operation had significant failures: {successful}/{total_payments} payments cancelled")
        
        logger.info(f"Bulk cancellation completed successfully")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as e:
        logger.error(f"Validation error in bulk cancel: {str(e)}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        logger.error(f"Business rule error in bulk cancel: {str(e)}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in bulk cancel: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/bulk/delete", response_model=dict)
async def bulk_delete_payments(
    request: BulkPaymentDeleteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar múltiples pagos en lote
    
    Permite eliminar hasta 1000 pagos simultáneamente:
    - Solo pagos en estado DRAFT pueden ser eliminados
    - Eliminación física de la base de datos
    - Procesamiento optimizado en lotes pequeños
    - Validaciones por lotes
    
    Body format: {"payment_ids": ["uuid1", "uuid2", ...]}
    """
    try:
        # Los UUIDs ya están validados por el esquema Pydantic
        payment_uuid_list = request.payment_ids
        
        service = PaymentFlowService(db)
        result = await service.bulk_delete_payments(payment_uuid_list, current_user.id)
        
        # Analizar los resultados para determinar el código de respuesta HTTP apropiado
        total_payments = result.get("total_payments", 0)
        successful = result.get("successful", 0)
        failed = result.get("failed", 0)
        
        # Si no se procesó ningún pago exitosamente, es un error crítico
        if total_payments > 0 and successful == 0:
            logger.warning(f"Bulk delete operation failed completely: 0/{total_payments} payments deleted")
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=f"No se pudo eliminar ningún pago. {failed} pagos fallaron."
            )
        
        # Si más del 50% de los pagos fallaron, loggear warning
        if total_payments > 0 and (failed / total_payments) > 0.5:
            logger.warning(f"Bulk delete operation had significant failures: {successful}/{total_payments} payments deleted")
        
        return result
        
    except ValidationError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))



@router.post("/bulk/validate", response_model=dict)
async def validate_bulk_confirmation(
    request: BulkPaymentValidationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validar múltiples pagos antes de confirmación en lote
    
    Valida hasta 1000 pagos para identificar:
    - Pagos que no pueden ser confirmados
    - Errores de validación por lotes
    - Estadísticas de validación
    - Recomendaciones de corrección
    
    Body format: {"payment_ids": ["uuid1", "uuid2", ...]}
    """
    try:
        # Los UUIDs ya están validados por el esquema Pydantic
        payment_uuid_list = request.payment_ids
        
        service = PaymentFlowService(db)
        return await service.validate_bulk_confirmation(payment_uuid_list)
    except ValidationError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================
# ENDPOINTS DE IMPORTACIÓN DE EXTRACTOS BANCARIOS
# =============================================

@router.post("/import", response_model=dict)
async def import_payments_with_auto_matching(
    extract_data: dict = Body(..., description="Datos del extracto bancario"),
    auto_match: bool = Body(True, description="Activar auto-vinculación con facturas"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Importar extracto bancario con auto-vinculación de pagos
    
    Flujo:
    1. Importa el extracto bancario
    2. Para cada línea, busca facturas coincidentes
    3. Crea pagos en borrador vinculados automáticamente
    """
    try:
        # TODO: Implementar import_payments_with_auto_matching en PaymentFlowService
        # service = PaymentFlowService(db)
        # result = await service.import_payments_with_auto_matching(
        #     extract_data=extract_data,
        #     created_by_id=current_user.id,
        #     auto_match=auto_match
        # )
        
        # Placeholder mientras se implementa la funcionalidad
        result = {
            "message": "Import endpoint ready - implementation pending",
            "payments_created": 0,
            "matches_found": 0,
            "auto_match_enabled": auto_match,
            "created_by": current_user.email,
            "status": "pending_implementation"
        }
        
        logger.info(f"Payment import requested by user {current_user.email}")
        return result
        
    except (NotFoundError, ValidationError, BusinessRuleError) as e:
        logger.error(f"Business error in payment import: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in payment import: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during payment import"
        )


@router.post("/import-file", response_model=dict)
async def import_payments_from_file(
    file: UploadFile = File(..., description="Archivo del extracto (CSV, Excel, etc.)"),
    extract_name: str = Form(..., description="Nombre del extracto"),
    account_id: str = Form(..., description="ID de la cuenta bancaria"),
    statement_date: str = Form(..., description="Fecha del extracto"),
    auto_match: bool = Form(True, description="Activar auto-vinculación"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Importar extracto bancario desde archivo (CSV, Excel, etc.)
    
    Permite cargar archivos de extractos bancarios y procesarlos automáticamente:
    - Soporte para múltiples formatos (CSV, Excel, MT940, etc.)
    - Auto-vinculación con facturas existentes
    - Creación automática de pagos en borrador
    """
    try:
        # Validar archivo
        if not file.filename:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Validar tipo de archivo
        allowed_extensions = {'.csv', '.xlsx', '.xls', '.txt'}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Leer contenido del archivo
        file_content = await file.read()
        
        # TODO: Implementar parsers específicos para cada formato
        # Por ahora retornamos información del archivo recibido
        return {
            "message": "File uploaded successfully - parsing implementation pending",
            "filename": file.filename,
            "size": len(file_content),
            "extract_name": extract_name,
            "account_id": account_id,
            "statement_date": statement_date,
            "auto_match": auto_match,
            "file_type": file_extension,
            "status": "pending_implementation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing uploaded file"
        )


# =============================================
# ENDPOINT DE DEBUG TEMPORAL
# =============================================

@router.post("/debug/reset-request", response_model=dict)
async def debug_reset_request(
    request: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint temporal para debuggear el formato de request del frontend
    """
    logger.info(f"Raw request received: {request}")
    logger.info(f"Request type: {type(request)}")
    
    # Intentar crear el schema
    try:
        from app.schemas.payment import BulkPaymentResetRequest
        reset_request = BulkPaymentResetRequest(**request)
        logger.info(f"Schema validation successful: {reset_request}")
        return {
            "status": "success",
            "message": "Request format is valid",
            "parsed_payment_ids": [str(pid) for pid in reset_request.payment_ids],
            "count": len(reset_request.payment_ids)
        }
    except Exception as e:
        logger.error(f"Schema validation failed: {str(e)}")
        return {
            "status": "error", 
            "message": f"Schema validation failed: {str(e)}",
            "raw_request": request
        }


# =============================================
# ENDPOINTS PRINCIPALES
# =============================================

@router.get("/", response_model=PaymentListResponse)
async def get_payments(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    date_from: Optional[date] = Query(None, description="Filter payments from this date"),
    date_to: Optional[date] = Query(None, description="Filter payments to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de pagos con filtros
    
    Permite filtrar por cliente, estado, rango de fechas, etc.
    """
    try:
        service = PaymentService(db)
        return await service.get_payments(
            customer_id=customer_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/", response_model=PaymentResponse, status_code=http_status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear un nuevo pago
    
    Flujo:
    1. Cliente creado previamente
    2. Crear pago en estado DRAFT
    3. Confirmar pago para generar asiento contable
    4. Asignar a facturas específicas
    """
    try:
        service = PaymentService(db)
        return await service.create_payment(payment_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


# Endpoints adicionales para workflow completo

@router.get("/types/", response_model=List[dict])
def get_payment_types():
    """Obtener tipos de pago disponibles"""
    return [{"value": t.value, "label": t.value.replace("_", " ").title()} for t in PaymentType]


@router.get("/statuses/", response_model=List[dict])
async def get_payment_statuses():
    """Obtener estados de pago disponibles"""
    return [{"value": s.value, "label": s.value.replace("_", " ").title()} for s in PaymentStatus]


@router.get("/summary/statistics", response_model=PaymentSummary)
async def get_payment_summary(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID"),
    date_from: Optional[date] = Query(None, description="Filter payments from this date"),
    date_to: Optional[date] = Query(None, description="Filter payments to this date"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener resumen estadístico de pagos
    
    Útil para dashboards y reportes ejecutivos
    """
    try:
        service = PaymentService(db)
        return await service.get_payment_summary()
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================
# ENDPOINTS CON PATH PARAMETERS (van al final)
# =============================================

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener pago por ID"""
    try:
        service = PaymentService(db)
        return await service.get_payment(payment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: uuid.UUID,
    payment_data: PaymentUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar pago
    
    Solo se puede actualizar si está en estado DRAFT o PENDING
    """
    try:
        service = PaymentService(db)
        return await service.update_payment(payment_id, payment_data)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{payment_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar pago
    
    Solo se puede eliminar si está en estado DRAFT
    """
    try:
        service = PaymentService(db)
        await service.delete_payment(payment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirmar pago siguiendo el flujo completo
    
    Flujo implementado:
    1. Validaciones previas
    2. Determinación de cuentas contables desde el diario y partner  
    3. Construcción del asiento contable (account.move)
    4. Creación y publicación del asiento
    5. Enlace entre pago y asiento
    6. Reconciliación automática con facturas
    7. Actualización de estados de facturas
    """
    try:
        # Usar PaymentFlowService que implementa el flujo completo
        service = PaymentFlowService(db)
        return await service.confirm_payment(payment_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{payment_id}/reset-to-draft", response_model=PaymentResponse)
async def reset_payment_to_draft(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resetear pago a borrador desde cualquier estado
    
    Permite resetear pagos desde los siguientes estados:
    - DRAFT: Ya está en borrador (retorna éxito sin cambios)
    - CONFIRMED: Cambia a DRAFT (no hay asiento contable que eliminar)
    - POSTED: Elimina asiento contable y cambia a DRAFT  
    - CANCELLED: Reactiva el pago eliminando asiento y cambia a DRAFT
    
    Esto permite editar pagos que previamente estaban confirmados o contabilizados.
    """
    try:
        service = PaymentFlowService(db)
        return await service.reset_payment_to_draft(payment_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))