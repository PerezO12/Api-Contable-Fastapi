"""
API endpoints for journal entries management.
Following best practices from estructura.md and practicas.md
"""
import uuid
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.journal_entry import JournalEntryStatus, TransactionOrigin
from app.schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryDetailResponse,
    JournalEntryDetailWithPayments,
    JournalEntryListResponse,
    JournalEntryStatistics,
    JournalEntryFilter,
    JournalEntryCancel,
    JournalEntryPost,
    JournalEntryResetToDraft,
    JournalEntryResetToDraftValidation,
    BulkJournalEntryResetToDraft,
    BulkJournalEntryResetToDraftResult,
    BulkJournalEntryApprove,
    JournalEntryApproveValidation,
    BulkJournalEntryApproveResult,
    BulkJournalEntryPost,
    JournalEntryPostValidation,
    BulkJournalEntryPostResult,
    BulkJournalEntryCancel,
    JournalEntryCancelValidation,
    BulkJournalEntryCancelResult,
    BulkJournalEntryReverse,
    JournalEntryReverseValidation,
    BulkJournalEntryReverseResult,
    BulkJournalEntryDelete,
    BulkJournalEntryDeleteResult,
    JournalEntryDeleteValidation
)
from app.services.journal_entry_service import JournalEntryService
from app.utils.exceptions import (
    JournalEntryNotFoundError,
    JournalEntryError,
    BalanceError,
    raise_journal_entry_not_found,
    raise_validation_error,
    raise_insufficient_permissions
)

router = APIRouter()


@router.post(
    "/",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create journal entry",
    description="Create a new journal entry with multiple line items"
)
async def create_journal_entry(
    journal_entry_data: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryResponse:
    """Create a new journal entry."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        journal_entry = await service.create_journal_entry(
            journal_entry_data,
            created_by_id=current_user.id,
            journal_id=journal_entry_data.journal_id
        )
        
        # Create response manually to avoid Pydantic accessing earliest_due_date property
        response_data = JournalEntryResponse.model_validate({
            "id": journal_entry.id,
            "number": journal_entry.number,
            "entry_date": journal_entry.entry_date,
            "description": journal_entry.description,
            "reference": journal_entry.reference,
            "entry_type": journal_entry.entry_type,
            "transaction_origin": journal_entry.transaction_origin,
            "notes": journal_entry.notes,
            "status": journal_entry.status,
            "total_debit": journal_entry.total_debit,
            "total_credit": journal_entry.total_credit,
            "created_by_id": journal_entry.created_by_id,
            "posted_by_id": journal_entry.posted_by_id,
            "posted_at": journal_entry.posted_at,
            "created_at": journal_entry.created_at,
            "updated_at": journal_entry.updated_at,
            "is_balanced": journal_entry.is_balanced,
            "can_be_posted": journal_entry.can_be_posted,
            "can_be_edited": journal_entry.can_be_modified,
            "created_by_name": journal_entry.created_by.full_name if journal_entry.created_by else None,
            "posted_by_name": journal_entry.posted_by.full_name if journal_entry.posted_by else None,
            "earliest_due_date": None  # Evitar lazy loading
        })
        
        return response_data
    except BalanceError as e:
        raise_validation_error(f"Balance error: {str(e)}")
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.get(
    "/",
    response_model=JournalEntryListResponse,
    summary="List journal entries",
    description="Get paginated list of journal entries with filtering options"
)
async def list_journal_entries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status: Optional[JournalEntryStatus] = Query(None, description="Filter by status"),
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by account"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    reference: Optional[str] = Query(None, description="Filter by reference"),
    transaction_origin: Optional[TransactionOrigin] = Query(None, description="Filter by transaction origin (sale, purchase, etc.)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryListResponse:
    """Get paginated list of journal entries."""
    service = JournalEntryService(db)    # Create filter object
    filters = JournalEntryFilter(
        status=[status] if status else None,
        account_id=account_id,
        start_date=date_from,
        end_date=date_to,
        search_text=reference,
        entry_type=None,
        created_by_id=None,
        min_amount=None,
        max_amount=None,
        transaction_origin=[transaction_origin] if transaction_origin else None
    )
    
    journal_entries, total = await service.get_journal_entries(
        skip=skip,
        limit=limit,
        filters=filters
    )      # Force load relationships to avoid lazy loading during serialization
    journal_entries_data = []
    for je in journal_entries:
        _ = len(je.lines)  # Force load the relationship
        # Force load nested relationships within lines
        for line in je.lines:
            if line.account:
                _ = line.account.code  # Force load account
            if line.third_party:
                _ = line.third_party.name  # Force load third party
            if line.cost_center:
                _ = line.cost_center.name  # Force load cost center
            if line.payment_terms:
                _ = line.payment_terms.code  # Force load payment terms
                if line.payment_terms.payment_schedules:
                    _ = len(line.payment_terms.payment_schedules)
        
        # Prepare journal entry data with calculated fields
        je_data = {col.name: getattr(je, col.name) for col in je.__table__.columns}        # Add computed properties
        je_data.update({
            'is_balanced': je.is_balanced,
            'can_be_posted': je.can_be_posted,
            'can_be_edited': je.can_be_modified,
            'created_by_name': je.created_by.full_name if je.created_by else None,
            'posted_by_name': je.posted_by.full_name if je.posted_by else None,
            'earliest_due_date': je.earliest_due_date  # Include earliest due date calculation
        })
        
        journal_entries_data.append(je_data)
    
    return JournalEntryListResponse(
        items=[JournalEntryResponse.model_validate(je_data) for je_data in journal_entries_data],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{journal_entry_id}",
    response_model=JournalEntryDetailWithPayments,
    summary="Get journal entry",
    description="Get journal entry by ID with full details including payment schedules"
)
async def get_journal_entry(
    journal_entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryDetailWithPayments:
    """Get journal entry by ID with payment schedule details."""
    try:
        service = JournalEntryService(db)
        journal_entry = await service.get_journal_entry_by_id(journal_entry_id)
        if not journal_entry:
            raise_journal_entry_not_found()
              # Force load all relationships to avoid lazy loading during serialization
        _ = len(journal_entry.lines)  # Force load lines
        
        # Prepare journal entry data with payment schedules
        journal_entry_data = {
            **{col.name: getattr(journal_entry, col.name) for col in journal_entry.__table__.columns},
            'lines': []
        }
          # Add computed properties
        journal_entry_data.update({
            'is_balanced': journal_entry.is_balanced,
            'can_be_posted': journal_entry.can_be_posted,
            'can_be_edited': journal_entry.can_be_modified,
            'created_by_name': journal_entry.created_by.full_name if journal_entry.created_by else None,
            'posted_by_name': journal_entry.posted_by.full_name if journal_entry.posted_by else None,
            'earliest_due_date': journal_entry.earliest_due_date  # Include earliest due date calculation
        })
        
        # Process each line and calculate payment schedule
        for line in journal_entry.lines:
            # Force load all line relationships
            if line.account:
                _ = line.account.code
            if line.third_party:
                _ = line.third_party.name
            if line.cost_center:
                _ = line.cost_center.name
            if line.payment_terms:
                _ = line.payment_terms.code
                if line.payment_terms.payment_schedules:
                    _ = len(line.payment_terms.payment_schedules)
            if line.product:
                _ = line.product.code
                
            # Prepare line data with all attributes
            line_data = {col.name: getattr(line, col.name) for col in line.__table__.columns}
            
            # Add computed properties from the model
            line_data.update({
                'account_code': line.account_code,
                'account_name': line.account_name,
                'third_party_code': line.third_party_code,
                'third_party_name': line.third_party_name,
                'third_party_document_type': line.third_party_document_type,
                'third_party_document_number': line.third_party_document_number,
                'third_party_tax_id': line.third_party_tax_id,
                'third_party_email': line.third_party_email,
                'third_party_phone': line.third_party_phone,
                'third_party_address': line.third_party_address,
                'third_party_city': line.third_party_city,
                'third_party_type': line.third_party_type,
                'cost_center_code': line.cost_center_code,
                'cost_center_name': line.cost_center_name,
                'product_code': line.product_code,
                'product_name': line.product_name,
                'product_type': line.product_type,
                'product_measurement_unit': line.product_measurement_unit,
                'payment_terms_code': line.payment_terms_code,
                'payment_terms_name': line.payment_terms_name,
                'payment_terms_description': line.payment_terms_description,
                'subtotal_before_discount': line.subtotal_before_discount,
                'effective_unit_price': line.effective_unit_price,
                'total_discount': line.total_discount,
                'subtotal_after_discount': line.subtotal_after_discount,
                'net_amount': line.net_amount,
                'gross_amount': line.gross_amount,
                'amount': line.amount,
                'movement_type': line.movement_type,
                'effective_invoice_date': line.effective_invoice_date,
                'effective_due_date': line.effective_due_date,
                'payment_schedule': line.get_payment_schedule()  # Calculate payment schedule
            })
            
            journal_entry_data['lines'].append(line_data)
                
        try:
            return JournalEntryDetailWithPayments.model_validate(journal_entry_data)
        except ValidationError as e:
            # Re-raise validation errors as they are now valid errors
            error_messages = [error['msg'] for error in e.errors()]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Error de validación en los datos del asiento",
                    "errors": error_messages,
                    "journal_entry_id": str(journal_entry_id)
                }
            )
                
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()


@router.put(
    "/{journal_entry_id}",
    response_model=JournalEntryResponse,
    summary="Update journal entry",
    description="Update journal entry (only if in draft status)"
)
async def update_journal_entry(
    journal_entry_id: uuid.UUID,
    journal_entry_data: JournalEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryResponse:
    """Update journal entry."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        journal_entry = await service.update_journal_entry(
            journal_entry_id,
            journal_entry_data
        )
        if not journal_entry:
            raise_journal_entry_not_found()
          # Create response manually to avoid Pydantic accessing earliest_due_date property
        response_data = JournalEntryResponse.model_validate({
            "id": journal_entry.id,
            "number": journal_entry.number,
            "entry_date": journal_entry.entry_date,
            "description": journal_entry.description,
            "reference": journal_entry.reference,
            "entry_type": journal_entry.entry_type,
            "transaction_origin": journal_entry.transaction_origin,
            "notes": journal_entry.notes,
            "status": journal_entry.status,
            "total_debit": journal_entry.total_debit,
            "total_credit": journal_entry.total_credit,
            "created_by_id": journal_entry.created_by_id,
            "posted_by_id": journal_entry.posted_by_id,
            "posted_at": journal_entry.posted_at,
            "created_at": journal_entry.created_at,
            "updated_at": journal_entry.updated_at,
            "is_balanced": journal_entry.is_balanced,
            "can_be_posted": journal_entry.can_be_posted,
            "can_be_edited": journal_entry.can_be_modified,
            "created_by_name": journal_entry.created_by.full_name if journal_entry.created_by else None,
            "posted_by_name": journal_entry.posted_by.full_name if journal_entry.posted_by else None,
            "earliest_due_date": None  # Evitar lazy loading
        })
        
        return response_data
        
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.delete(
    "/{journal_entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete journal entry",
    description="Delete journal entry (only if in draft status)"
)
async def delete_journal_entry(
    journal_entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete journal entry."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        deleted = await service.delete_journal_entry(journal_entry_id)
        if not deleted:
            raise_journal_entry_not_found()
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/{journal_entry_id}/approve",
    response_model=JournalEntryResponse,
    summary="Approve journal entry",
    description="Approve journal entry for posting"
)
async def approve_journal_entry(
    journal_entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryResponse:
    """Approve journal entry."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        journal_entry = await service.approve_journal_entry(
            journal_entry_id,
            approved_by_id=current_user.id
        )
        # Force load relationships to avoid lazy loading during serialization
        _ = len(journal_entry.lines)  # Force load the relationship
        return JournalEntryResponse.model_validate(journal_entry)
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/{journal_entry_id}/post",
    response_model=JournalEntryResponse,
    summary="Post journal entry",
    description="Post journal entry to accounts"
)
async def post_journal_entry(
    journal_entry_id: uuid.UUID,
    post_data: Optional[JournalEntryPost] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryResponse:
    """Post journal entry to accounts."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        journal_entry = await service.post_journal_entry(
            journal_entry_id,
            posted_by_id=current_user.id,
            post_data=post_data
        )
        # Force load relationships to avoid lazy loading during serialization
        _ = len(journal_entry.lines)  # Force load the relationship
        return JournalEntryResponse.model_validate(journal_entry)
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/{journal_entry_id}/cancel",
    response_model=JournalEntryResponse,
    summary="Cancel journal entry",
    description="Cancel journal entry"
)
async def cancel_journal_entry(
    journal_entry_id: uuid.UUID,
    cancel_data: JournalEntryCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryResponse:
    """Cancel journal entry."""
    # Check permissions - only admin or contador can cancel
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        journal_entry = await service.cancel_journal_entry(
            journal_entry_id,
            cancelled_by_id=current_user.id,
            cancel_data=cancel_data
        )
        # Force load relationships to avoid lazy loading during serialization
        _ = len(journal_entry.lines)  # Force load the relationship
        return JournalEntryResponse.model_validate(journal_entry)
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/{journal_entry_id}/reverse",
    response_model=JournalEntryResponse,
    summary="Reverse journal entry",
    description="Create reversing journal entry"
)
async def reverse_journal_entry(
    journal_entry_id: uuid.UUID,
    reason: str = Query(..., description="Reason for reversal"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryResponse:
    """Create reversing journal entry."""    # Check permissions - only admin or contador can reverse
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        # Get the original entry first
        original_entry = await service.get_journal_entry_by_id(journal_entry_id)
        if not original_entry:
            raise_journal_entry_not_found()
        
        # Create reversal entry using the private method
        # Type assertion since we've already checked for None
        assert original_entry is not None  # type: ignore
        reversal_entry = await service._create_reversal_entry(
            original_entry,
            created_by_id=current_user.id,
            reason=reason
        )
        # Force load relationships to avoid lazy loading during serialization
        _ = len(reversal_entry.lines)  # Force load the relationship
        return JournalEntryResponse.model_validate(reversal_entry)
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.get(
    "/statistics/summary",
    response_model=JournalEntryStatistics,
    summary="Get journal entry statistics",
    description="Get journal entry statistics and summary"
)
async def get_journal_entry_statistics(
    date_from: Optional[date] = Query(None, description="Statistics from date"),
    date_to: Optional[date] = Query(None, description="Statistics to date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryStatistics:    
    """Get journal entry statistics."""
    service = JournalEntryService(db)
    stats = await service.get_journal_entry_stats(
        start_date=date_from,
        end_date=date_to
    )
    return JournalEntryStatistics.model_validate(stats)


@router.get(
    "/search",
    response_model=List[JournalEntryResponse],
    summary="Search journal entries",
    description="Advanced search for journal entries"
)
async def search_journal_entries(
    filters: JournalEntryFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[JournalEntryResponse]:
    """Search journal entries with advanced filters."""
    service = JournalEntryService(db)
    journal_entries = await service.search_journal_entries(filters)
    
    # Force load relationships to avoid lazy loading during serialization
    for je in journal_entries:
        _ = len(je.lines)  # Force load the relationship
        # Force load nested relationships within lines
        for line in je.lines:
            if line.account:
                _ = line.account.code  # Force load account
            if line.third_party:
                _ = line.third_party.name  # Force load third party
            if line.cost_center:
                _ = line.cost_center.name  # Force load cost center
        
    return [JournalEntryResponse.model_validate(je) for je in journal_entries]


@router.post(
    "/bulk-create",
    response_model=List[JournalEntryResponse],
    summary="Bulk create journal entries",
    description="Create multiple journal entries at once"
)
async def bulk_create_journal_entries(
    entries_data: List[JournalEntryCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[JournalEntryResponse]:
    """Bulk create journal entries."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)        
        journal_entries = await service.bulk_create_journal_entries(
            entries_data,
            created_by_id=current_user.id
        )
          # Force load relationships to avoid lazy loading during serialization
        for je in journal_entries:
            _ = len(je.lines)  # Force load the relationship
            # Force load nested relationships within lines
            for line in je.lines:
                if line.account:
                    _ = line.account.code  # Force load account
                if line.third_party:
                    _ = line.third_party.name  # Force load third party
                if line.cost_center:
                    _ = line.cost_center.name  # Force load cost center
            
        return [JournalEntryResponse.model_validate(je) for je in journal_entries]
    except JournalEntryError as e:
        raise_validation_error(str(e))
    except BalanceError as e:
        raise_validation_error(f"Balance error in bulk creation: {str(e)}")


@router.get(
    "/by-number/{entry_number}",
    response_model=JournalEntryDetailResponse,
    summary="Get journal entry by number",
    description="Get journal entry by entry number"
)
async def get_journal_entry_by_number(
    entry_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryDetailResponse:
    """Get journal entry by entry number."""
    try:
        service = JournalEntryService(db)
        journal_entry = await service.get_journal_entry_by_number(entry_number)
        if not journal_entry:
            raise_journal_entry_not_found()
        
        # Create response manually to avoid Pydantic accessing earliest_due_date property
        response_data = JournalEntryDetailResponse.model_validate({
            "id": journal_entry.id,
            "number": journal_entry.number,
            "entry_date": journal_entry.entry_date,
            "description": journal_entry.description,
            "reference": journal_entry.reference,
            "entry_type": journal_entry.entry_type,
            "transaction_origin": journal_entry.transaction_origin,
            "notes": journal_entry.notes,
            "status": journal_entry.status,
            "total_debit": journal_entry.total_debit,
            "total_credit": journal_entry.total_credit,
            "created_by_id": journal_entry.created_by_id,
            "posted_by_id": journal_entry.posted_by_id,
            "posted_at": journal_entry.posted_at,
            "created_at": journal_entry.created_at,
            "updated_at": journal_entry.updated_at,
            "is_balanced": journal_entry.is_balanced,
            "can_be_posted": journal_entry.can_be_posted,
            "can_be_edited": journal_entry.can_be_modified,
            "created_by_name": journal_entry.created_by.full_name if journal_entry.created_by else None,
            "posted_by_name": journal_entry.posted_by.full_name if journal_entry.posted_by else None,
            "earliest_due_date": None,  # Evitar lazy loading
            "lines": journal_entry.lines  # Incluir las líneas para JournalEntryDetailResponse
        })
        
        return response_data
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()


@router.post(
    "/validate-deletion",
    response_model=List[JournalEntryDeleteValidation],
    summary="Validate journal entries for deletion",
    description="Validate multiple journal entries before deletion to check for errors and warnings"
)
async def validate_journal_entries_for_deletion(
    journal_entry_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[JournalEntryDeleteValidation]:
    """Validate journal entries for deletion."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        validations = []
        
        for entry_id in journal_entry_ids:
            validation = await service.validate_journal_entry_for_deletion(entry_id)
            validations.append(validation)
        
        return validations
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/bulk-delete",
    response_model=BulkJournalEntryDeleteResult,
    summary="Bulk delete journal entries",
    description="Delete multiple journal entries at once (only draft entries can be deleted)"
)
async def bulk_delete_journal_entries(
    bulk_delete_data: BulkJournalEntryDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BulkJournalEntryDeleteResult:
    """Bulk delete journal entries."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        result = await service.bulk_delete_journal_entries(
            entry_ids=bulk_delete_data.journal_entry_ids,
            force_delete=bulk_delete_data.force_delete,
            reason=bulk_delete_data.reason
        )
        
        # Si no se procesó ninguna entrada exitosamente, devolver error
        if result.total_deleted == 0 and result.total_requested > 0:
            error_details = []
            for failed_entry in result.failed_entries:
                error_details.extend(failed_entry.errors)
            
            if error_details:
                raise_validation_error(f"No se pudo eliminar ninguna entrada. Errores: {'; '.join(error_details)}")
            else:
                raise_validation_error("No se encontraron entradas válidas para eliminar")
        
        return result
    except JournalEntryError as e:
        raise_validation_error(str(e))


# ===== OPERACIONES MASIVAS ADICIONALES =====

@router.post(
    "/validate-approve",
    response_model=List[JournalEntryApproveValidation],
    summary="Validate journal entries for approval",
    description="Validate multiple journal entries before approval to check for errors and warnings"
)
async def validate_journal_entries_for_approve(
    journal_entry_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[JournalEntryApproveValidation]:
    """Validate journal entries for approval."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        validations = []
        
        for entry_id in journal_entry_ids:
            validation = await service.validate_journal_entry_for_approve(entry_id)
            validations.append(validation)
        
        return validations
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/bulk-approve",
    response_model=BulkJournalEntryApproveResult,
    summary="Bulk approve journal entries",
    description="Approve multiple journal entries at once (only draft entries can be approved)"
)
async def bulk_approve_journal_entries(
    bulk_approve_data: BulkJournalEntryApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BulkJournalEntryApproveResult:
    """Bulk approve journal entries."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        result = await service.bulk_approve_journal_entries(
            entry_ids=bulk_approve_data.journal_entry_ids,
            approved_by_id=current_user.id,
            force_approve=bulk_approve_data.force_approve,
            reason=bulk_approve_data.reason
        )
          # Si no se procesó ninguna entrada exitosamente, devolver error
        if result.total_approved == 0 and result.total_requested > 0:
            error_details = []
            failed_details = []
            
            for failed_entry in result.failed_entries:
                failed_details.append(f"Asiento {failed_entry.journal_entry_number}: {'; '.join(failed_entry.errors)}")
                error_details.extend(failed_entry.errors)
            
            detailed_message = f"No se pudo aprobar ninguna entrada. Detalles: {' | '.join(failed_details)}"
            
            if error_details:
                raise_validation_error(detailed_message)
            else:
                raise_validation_error("No se encontraron entradas válidas para aprobar")
        
        return result
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/validate-post",
    response_model=List[JournalEntryPostValidation],
    summary="Validate journal entries for posting",
    description="Validate multiple journal entries before posting to check for errors and warnings"
)
async def validate_journal_entries_for_post(
    journal_entry_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[JournalEntryPostValidation]:
    """Validate journal entries for posting."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        validations = []
        
        for entry_id in journal_entry_ids:
            validation = await service.validate_journal_entry_for_post(entry_id)
            validations.append(validation)
        
        return validations
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/bulk-post",
    response_model=BulkJournalEntryPostResult,
    summary="Bulk post journal entries",
    description="Post multiple journal entries to accounts at once (only approved entries can be posted)"
)
async def bulk_post_journal_entries(
    bulk_post_data: BulkJournalEntryPost,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BulkJournalEntryPostResult:
    """Bulk post journal entries."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        result = await service.bulk_post_journal_entries(
            entry_ids=bulk_post_data.journal_entry_ids,
            posted_by_id=current_user.id,
            force_post=bulk_post_data.force_post,
            reason=bulk_post_data.reason
        )
        
        # Si no se procesó ninguna entrada exitosamente, devolver error
        if result.total_posted == 0 and result.total_requested > 0:
            error_details = []
            for failed_entry in result.failed_entries:
                error_details.extend(failed_entry.errors)
            
            if error_details:
                raise_validation_error(f"No se pudo contabilizar ninguna entrada. Errores: {'; '.join(error_details)}")
            else:
                raise_validation_error("No se encontraron entradas válidas para contabilizar")
        
        return result
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/validate-cancel",
    response_model=List[JournalEntryCancelValidation],
    summary="Validate journal entries for cancellation",
    description="Validate multiple journal entries before cancellation to check for errors and warnings"
)
async def validate_journal_entries_for_cancel(
    journal_entry_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[JournalEntryCancelValidation]:
    """Validate journal entries for cancellation."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        validations = []
        
        for entry_id in journal_entry_ids:
            validation = await service.validate_journal_entry_for_cancel(entry_id)
            validations.append(validation)
        
        return validations
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/bulk-cancel",
    response_model=BulkJournalEntryCancelResult,
    summary="Bulk cancel journal entries",
    description="Cancel multiple journal entries at once (creates reversal entries for posted entries)"
)
async def bulk_cancel_journal_entries(
    bulk_cancel_data: BulkJournalEntryCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BulkJournalEntryCancelResult:
    """Bulk cancel journal entries."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        result = await service.bulk_cancel_journal_entries(
            entry_ids=bulk_cancel_data.journal_entry_ids,
            cancelled_by_id=current_user.id,
            force_cancel=bulk_cancel_data.force_cancel,
            reason=bulk_cancel_data.reason
        )
        
        # Si no se procesó ninguna entrada exitosamente, devolver error
        if result.total_cancelled == 0 and result.total_requested > 0:
            error_details = []
            for failed_entry in result.failed_entries:
                error_details.extend(failed_entry.errors)
            
            if error_details:
                raise_validation_error(f"No se pudo cancelar ninguna entrada. Errores: {'; '.join(error_details)}")
            else:
                raise_validation_error("No se encontraron entradas válidas para cancelar")
        
        return result
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/validate-reverse",
    response_model=List[JournalEntryReverseValidation],
    summary="Validate journal entries for reversal",
    description="Validate multiple journal entries before reversal to check for errors and warnings"
)
async def validate_journal_entries_for_reverse(
    journal_entry_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[JournalEntryReverseValidation]:
    """Validate journal entries for reversal."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        validations = []
        
        for entry_id in journal_entry_ids:
            validation = await service.validate_journal_entry_for_reverse(entry_id)
            validations.append(validation)
        
        return validations
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/bulk-reverse",
    response_model=BulkJournalEntryReverseResult,
    summary="Bulk reverse journal entries",
    description="Create reversal entries for multiple posted journal entries at once"
)
async def bulk_reverse_journal_entries(
    bulk_reverse_data: BulkJournalEntryReverse,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BulkJournalEntryReverseResult:
    """Bulk reverse journal entries."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        result = await service.bulk_reverse_journal_entries(
            entry_ids=bulk_reverse_data.journal_entry_ids,
            created_by_id=current_user.id,
            force_reverse=bulk_reverse_data.force_reverse,
            reason=bulk_reverse_data.reason
        )
        
        # Si no se procesó ninguna entrada exitosamente, devolver error
        if result.total_reversed == 0 and result.total_requested > 0:
            error_details = []
            for failed_entry in result.failed_entries:
                error_details.extend(failed_entry.errors)
            
            if error_details:
                raise_validation_error(f"No se pudo revertir ninguna entrada. Errores: {'; '.join(error_details)}")
            else:
                raise_validation_error("No se encontraron entradas válidas para revertir")
        
        return result
    except JournalEntryError as e:
        raise_validation_error(str(e))


# ===== OPERACIÓN RESET TO DRAFT MASIVA =====

@router.post(
    "/validate-reset-to-draft",
    response_model=List[JournalEntryResetToDraftValidation],
    summary="Validate journal entries for reset to draft",
    description="Validate multiple journal entries before resetting to draft to check for errors and warnings"
)
async def validate_journal_entries_for_reset_to_draft(
    journal_entry_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[JournalEntryResetToDraftValidation]:
    """Validate journal entries for reset to draft."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        validations = []
        
        for entry_id in journal_entry_ids:
            validation = await service.validate_journal_entry_for_reset_to_draft(entry_id)
            validations.append(validation)
        
        return validations
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/bulk-reset-to-draft",
    response_model=BulkJournalEntryResetToDraftResult,
    summary="Bulk reset journal entries to draft",
    description="Reset multiple journal entries to draft status at once (only approved/pending entries can be reset)"
)
async def bulk_reset_to_draft_journal_entries(
    bulk_reset_data: BulkJournalEntryResetToDraft,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BulkJournalEntryResetToDraftResult:
    """Bulk reset journal entries to draft."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        result = await service.bulk_reset_journal_entries_to_draft(
            entry_ids=bulk_reset_data.journal_entry_ids,
            reset_by_id=current_user.id,
            force_reset=bulk_reset_data.force_reset,
            reason=bulk_reset_data.reason
        )
        
        # Si no se procesó ninguna entrada exitosamente, devolver error
        if result.total_reset == 0 and result.total_requested > 0:
            error_details = []
            for failed_entry in result.failed_entries:
                error_details.extend(failed_entry.errors)
            
            if error_details:
                raise_validation_error(f"No se pudo restablecer ninguna entrada. Errores: {'; '.join(error_details)}")
            else:
                raise_validation_error("No se encontraron entradas válidas para restablecer a borrador")
        
        return result
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/{journal_entry_id}/reset-to-draft",
    response_model=JournalEntryResponse,
    summary="Reset journal entry to draft",
    description="Reset a journal entry back to draft status"
)
async def reset_journal_entry_to_draft(
    journal_entry_id: uuid.UUID,
    reset_data: JournalEntryResetToDraft,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryResponse:
    """Reset journal entry to draft status."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = JournalEntryService(db)
        journal_entry = await service.reset_journal_entry_to_draft(
            journal_entry_id,
            reset_by_id=current_user.id,
            reset_data=reset_data
        )
        # Force load relationships to avoid lazy loading during serialization
        _ = len(journal_entry.lines)  # Force load the relationship
        return JournalEntryResponse.model_validate(journal_entry)
    except JournalEntryNotFoundError:
        raise_journal_entry_not_found()
    except JournalEntryError as e:
        raise_validation_error(str(e))
