"""
Bank Reconciliation API endpoints.
Provides endpoints for managing bank reconciliation operations.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.bank_reconciliation_service import BankReconciliationService
from app.schemas.bank_reconciliation import (
    BankReconciliationCreate,
    BankReconciliationUpdate,
    BankReconciliationResponse,
    BankReconciliationListResponse,
    BankReconciliationAutoRequest,
    BankReconciliationAutoResponse
)
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError

router = APIRouter()


@router.post("/", response_model=BankReconciliationResponse, status_code=http_status.HTTP_201_CREATED)
async def create_reconciliation(
    reconciliation_data: BankReconciliationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new bank reconciliation.
    
    Args:
        reconciliation_data: Bank reconciliation creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created bank reconciliation
        
    Raises:
        HTTPException: If validation fails or reconciliation cannot be created
    """
    try:
        service = BankReconciliationService(db)
        reconciliation = service.create_reconciliation(reconciliation_data, current_user.id)
        return reconciliation
    except (NotFoundError, ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=BankReconciliationListResponse)
async def list_reconciliations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status: Optional[str] = Query(None, description="Filter by reconciliation status"),
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by account ID"),
    extract_id: Optional[uuid.UUID] = Query(None, description="Filter by bank extract ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List bank reconciliations with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Number of records to return
        status: Filter by reconciliation status
        account_id: Filter by account ID
        extract_id: Filter by bank extract ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of bank reconciliations with pagination
    """
    try:
        service = BankReconciliationService(db)
        reconciliations = service.list_reconciliations(
            skip=skip,
            limit=limit,
            status=status,
            account_id=account_id,
            extract_id=extract_id
        )
        return reconciliations
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{reconciliation_id}", response_model=BankReconciliationResponse)
async def get_reconciliation(
    reconciliation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific bank reconciliation by ID.
    
    Args:
        reconciliation_id: Bank reconciliation ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Bank reconciliation details
        
    Raises:
        HTTPException: If reconciliation not found
    """
    try:
        service = BankReconciliationService(db)
        reconciliation = service.get_reconciliation(reconciliation_id)
        return reconciliation
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/{reconciliation_id}", response_model=BankReconciliationResponse)
async def update_reconciliation(
    reconciliation_id: uuid.UUID,
    reconciliation_data: BankReconciliationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a bank reconciliation.
    
    Args:
        reconciliation_id: Bank reconciliation ID
        reconciliation_data: Bank reconciliation update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated bank reconciliation
        
    Raises:
        HTTPException: If reconciliation not found or update fails
    """
    try:
        service = BankReconciliationService(db)
        reconciliation = service.update_reconciliation(reconciliation_id, reconciliation_data, current_user.id)
        return reconciliation
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/{reconciliation_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_reconciliation(
    reconciliation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a bank reconciliation.
    
    Args:
        reconciliation_id: Bank reconciliation ID
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If reconciliation not found or cannot be deleted
    """
    try:
        service = BankReconciliationService(db)
        service.delete_reconciliation(reconciliation_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/auto-reconcile", response_model=BankReconciliationAutoResponse)
async def auto_reconcile(
    auto_request: BankReconciliationAutoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Automatically reconcile bank extract lines with payments and invoices.
    
    Args:
        auto_request: Auto reconciliation request parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Auto reconciliation results
        
    Raises:
        HTTPException: If auto reconciliation fails
    """
    try:
        service = BankReconciliationService(db)
        result = service.auto_reconcile(
            extract_id=auto_request.extract_id,
            account_id=auto_request.account_id,
            tolerance_amount=auto_request.tolerance_amount,
            tolerance_days=auto_request.tolerance_days,
            created_by_id=current_user.id
        )
        return result
    except (NotFoundError, ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{reconciliation_id}/confirm", response_model=BankReconciliationResponse)
async def confirm_reconciliation(
    reconciliation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirm a bank reconciliation.
    
    Args:
        reconciliation_id: Bank reconciliation ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Confirmed bank reconciliation
        
    Raises:
        HTTPException: If reconciliation not found or cannot be confirmed
    """
    try:
        service = BankReconciliationService(db)
        reconciliation = service.confirm_reconciliation(reconciliation_id, current_user.id)
        return reconciliation
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{reconciliation_id}/cancel", response_model=BankReconciliationResponse)
async def cancel_reconciliation(
    reconciliation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a bank reconciliation.
    
    Args:
        reconciliation_id: Bank reconciliation ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Cancelled bank reconciliation
        
    Raises:
        HTTPException: If reconciliation not found or cannot be cancelled
    """
    try:
        service = BankReconciliationService(db)
        reconciliation = service.cancel_reconciliation(reconciliation_id, current_user.id)
        return reconciliation
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
