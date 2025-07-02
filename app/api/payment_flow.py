"""
Payment Flow API endpoints - Implementa el flujo completo de pagos.

Endpoints implementados:
- POST /payment-flow/import - Importar extracto con auto-matching
- POST /payment-flow/confirm/{payment_id} - Confirmar pago
- GET /payment-flow/status/{extract_id} - Estado del flujo
- GET /payment-flow/drafts - Pagos en borrador pendientes
"""
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.bank_extract import BankExtractImport
from app.schemas.payment import (
    PaymentFlowImportResult, PaymentFlowStatus, PaymentConfirmation,
    PaymentResponse, PaymentAutoMatchResult
)
from app.services.payment_flow_service import PaymentFlowService
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/import", response_model=Dict[str, Any])
def import_payments_with_auto_matching(
    extract_data: BankExtractImport,
    auto_match: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    PASO 2: Importar extracto bancario con auto-vinculación de pagos
    
    Flujo:
    1. Importa el extracto bancario
    2. Para cada línea, busca facturas coincidentes
    3. Crea pagos en borrador vinculados automáticamente
    """
    try:
        service = PaymentFlowService(db)
        result = service.import_payments_with_auto_matching(
            extract_data=extract_data,
            created_by_id=current_user.id,
            auto_match=auto_match
        )
        
        logger.info(f"Payment import completed by user {current_user.email}: {result['payments_created']} payments created")
        return result
        
    except (NotFoundError, ValidationError, BusinessRuleError) as e:
        logger.error(f"Business error in payment import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in payment import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during payment import"
        )


@router.post("/import-file", response_model=Dict[str, Any])
async def import_payments_from_file(
    file: UploadFile = File(...),
    extract_name: str = Form(...),
    account_id: str = Form(...),
    statement_date: str = Form(...),
    auto_match: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Importar extracto bancario desde archivo (CSV, Excel, etc.)
    """
    try:
        # Validar archivo
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Aquí iría la lógica de parsing del archivo según el formato
        # Por ahora retornamos un placeholder
        # TODO: Implementar parsers para CSV, Excel, MT940, etc.
        
        return {
            "message": "File upload endpoint ready - parsing logic to be implemented",
            "filename": file.filename,
            "size": len(file_content),
            "extract_name": extract_name,
            "account_id": account_id
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing uploaded file"
        )


@router.post("/confirm/{payment_id}", response_model=PaymentResponse)
def confirm_payment(
    payment_id: uuid.UUID,
    confirmation: PaymentConfirmation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    PASO 3: Confirmar pago (DRAFT → POSTED)
    
    Flujo:
    1. Valida el pago en borrador
    2. Genera asiento contable en diario de banco
    3. Concilia automáticamente con facturas
    4. Actualiza estado de facturas
    """
    try:
        service = PaymentFlowService(db)
        result = service.confirm_payment(
            payment_id=payment_id,
            confirmed_by_id=current_user.id
        )
        
        logger.info(f"Payment {payment_id} confirmed by user {current_user.email}")
        return result
        
    except NotFoundError as e:
        logger.error(f"Payment not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (ValidationError, BusinessRuleError) as e:
        logger.error(f"Business error confirming payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error confirming payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during payment confirmation"
        )


@router.get("/status/{extract_id}", response_model=PaymentFlowStatus)
def get_payment_flow_status(
    extract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estado del flujo de pagos para un extracto específico
    """
    try:
        service = PaymentFlowService(db)
        status_info = service.get_payment_flow_status(extract_id)
        return PaymentFlowStatus(**status_info)
        
    except NotFoundError as e:
        logger.error(f"Extract not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting payment flow status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/drafts", response_model=List[PaymentResponse])
def get_draft_payments(
    limit: int = 50,
    offset: int = 0,
    third_party_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de pagos en borrador pendientes de confirmación
    """
    try:
        from app.models.payment import Payment, PaymentStatus
        from sqlalchemy.orm import joinedload
        
        query = db.query(Payment).options(
            joinedload(Payment.third_party),
            joinedload(Payment.payment_invoices)
        ).filter(Payment.status == PaymentStatus.DRAFT)
        
        if third_party_id:
            query = query.filter(Payment.third_party_id == third_party_id)
        
        payments = query.offset(offset).limit(limit).all()
        
        return [PaymentResponse.from_orm(payment) for payment in payments]
        
    except Exception as e:
        logger.error(f"Error getting draft payments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/pending-reconciliation", response_model=Dict[str, Any])
def get_pending_reconciliation_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resumen de pagos pendientes de conciliación
    """
    try:
        from app.models.payment import Payment, PaymentStatus
        from app.models.bank_extract import BankExtract, BankExtractLine
        from sqlalchemy import func, and_
        
        # Pagos en borrador
        draft_payments = db.query(func.count(Payment.id)).filter(
            Payment.status == PaymentStatus.DRAFT
        ).scalar()
        
        # Líneas de extracto sin vincular
        unmatched_lines = db.query(func.count(BankExtractLine.id)).filter(
            BankExtractLine.payment_id.is_(None)
        ).scalar()
        
        # Líneas con pagos en borrador
        draft_matches = db.query(func.count(BankExtractLine.id)).join(Payment).filter(
            Payment.status == PaymentStatus.DRAFT
        ).scalar()
        
        return {
            "draft_payments": draft_payments,
            "unmatched_extract_lines": unmatched_lines,
            "draft_matches": draft_matches,
            "total_pending": draft_payments + unmatched_lines
        }
        
    except Exception as e:
        logger.error(f"Error getting reconciliation summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/batch-confirm", response_model=Dict[str, Any])
def batch_confirm_payments(
    payment_ids: List[uuid.UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirmar múltiples pagos en lote
    """
    try:
        service = PaymentFlowService(db)
        results = []
        errors = []
        
        for payment_id in payment_ids:
            try:
                result = service.confirm_payment(
                    payment_id=payment_id,
                    confirmed_by_id=current_user.id
                )
                results.append({
                    "payment_id": payment_id,
                    "success": True,
                    "payment_number": result.payment_number
                })
            except Exception as e:
                errors.append({
                    "payment_id": payment_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "total_requested": len(payment_ids),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in batch confirm: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during batch confirmation"
        )
