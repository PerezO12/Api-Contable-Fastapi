"""
API endpoints for journal entries management.
Following best practices from estructura.md and practicas.md
"""
import uuid
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.journal_entry import JournalEntryStatus
from app.schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryDetailResponse,
    JournalEntryListResponse,
    JournalEntryStatistics,
    JournalEntryFilter,
    JournalEntryCancel,
    JournalEntryPost,
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
            created_by_id=current_user.id
        )
        return JournalEntryResponse.model_validate(journal_entry)
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryListResponse:
    """Get paginated list of journal entries."""
    service = JournalEntryService(db)
    # Create filter object
    filters = JournalEntryFilter(
        status=status,
        account_id=account_id,
        start_date=date_from,
        end_date=date_to,
        search=reference
    )
    
    journal_entries, total = await service.get_journal_entries(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    return JournalEntryListResponse(
        items=[JournalEntryResponse.model_validate(je) for je in journal_entries],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{journal_entry_id}",
    response_model=JournalEntryDetailResponse,
    summary="Get journal entry",
    description="Get journal entry by ID with full details"
)
async def get_journal_entry(
    journal_entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> JournalEntryDetailResponse:
    """Get journal entry by ID."""
    try:
        service = JournalEntryService(db)
        journal_entry = await service.get_journal_entry_by_id(journal_entry_id)
        if not journal_entry:
            raise_journal_entry_not_found()
        return JournalEntryDetailResponse.model_validate(journal_entry)
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
        return JournalEntryResponse.model_validate(journal_entry)
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
        return JournalEntryDetailResponse.model_validate(journal_entry)
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
        return result
    except JournalEntryError as e:
        raise_validation_error(str(e))


@router.post(
    "/bulk-operation",
    summary="Bulk operations on journal entries",
    description="Perform bulk operations (delete, approve, cancel) on multiple journal entries"
)
async def bulk_operation_journal_entries(
    operation: str = Query(..., description="Operation to perform: delete, approve, cancel"),
    journal_entry_ids: List[uuid.UUID] = Query(..., description="List of journal entry IDs"),
    force_operation: bool = Query(False, description="Force operation ignoring warnings"),
    reason: Optional[str] = Query(None, description="Reason for the operation"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform bulk operations on journal entries."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    # Validate operation
    valid_operations = ["delete", "approve", "cancel"]
    if operation not in valid_operations:
        raise_validation_error(f"Invalid operation. Valid operations: {', '.join(valid_operations)}")
    
    try:
        service = JournalEntryService(db)
        
        # Prepare operation data
        operation_data = {
            "force_delete": force_operation if operation == "delete" else False,
            "reason": reason,
            "approved_by_id": current_user.id if operation == "approve" else None,
            "cancelled_by_id": current_user.id if operation == "cancel" else None
        }
        
        result = await service.bulk_operation(
            operation=operation,
            entry_ids=journal_entry_ids,
            operation_data=operation_data
        )
        
        return result
    except JournalEntryError as e:
        raise_validation_error(str(e))
