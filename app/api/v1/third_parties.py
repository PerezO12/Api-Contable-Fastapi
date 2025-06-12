"""
API endpoints for third party management.
Provides CRUD operations, contact management and statement generation for customers, suppliers and other business partners.
"""
import uuid
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.third_party import ThirdPartyType, DocumentType
from app.schemas.third_party import (
    ThirdPartyCreate, ThirdPartyUpdate, ThirdPartyResponse, ThirdPartyDetailResponse,
    ThirdPartyListResponse, ThirdPartyList, ThirdPartyFilter, ThirdPartyStatement,
    ThirdPartyBalance, ThirdPartyValidation, BulkThirdPartyOperation, ThirdPartyStats
)
from app.services.third_party_service import ThirdPartyService
from app.utils.exceptions import (
    NotFoundError, ConflictError, ValidationError, BusinessLogicError,
    raise_not_found, raise_validation_error, raise_conflict_error,
    raise_insufficient_permissions
)

router = APIRouter()


@router.post(
    "/",
    response_model=ThirdPartyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create third party",
    description="Create a new third party (customer, supplier, employee, etc.)"
)
async def create_third_party(
    third_party_data: ThirdPartyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyResponse:
    """Create a new third party."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = ThirdPartyService(db)
        third_party = await service.create_third_party(third_party_data)
        return ThirdPartyResponse.model_validate(third_party)
    except ConflictError as e:
        raise_conflict_error(str(e))
    except ValidationError as e:
        raise_validation_error(str(e))


@router.get(
    "/",
    response_model=ThirdPartyListResponse,
    summary="Get third parties",
    description="Get paginated list of third parties with filtering"
)
async def get_third_parties(
    search: Optional[str] = Query(None, description="Search in code, name, document number"),
    third_party_type: Optional[ThirdPartyType] = Query(None, description="Filter by third party type"),
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    country: Optional[str] = Query(None, description="Filter by country"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyListResponse:
    """Get paginated list of third parties."""
    
    filter_params = ThirdPartyFilter(
        search=search,
        third_party_type=third_party_type,
        document_type=document_type,
        is_active=is_active,
        city=city,
        country=country
    )
    
    service = ThirdPartyService(db)
    third_parties_list = await service.get_third_parties_list(filter_params, skip, limit)
    
    return ThirdPartyListResponse(
        items=[ThirdPartyResponse.model_validate(tp) for tp in third_parties_list.third_parties],
        total=third_parties_list.total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{third_party_id}",
    response_model=ThirdPartyDetailResponse,
    summary="Get third party",
    description="Get third party by ID with detailed information"
)
async def get_third_party(
    third_party_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyDetailResponse:
    """Get third party by ID."""
    
    service = ThirdPartyService(db)
    third_party = await service.get_third_party_by_id(third_party_id)
    
    if not third_party:
        raise_not_found("Tercero no encontrado")
    
    return ThirdPartyDetailResponse.model_validate(third_party)


@router.get(
    "/code/{code}",
    response_model=ThirdPartyResponse,
    summary="Get third party by code",
    description="Get third party by unique code"
)
async def get_third_party_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyResponse:
    """Get third party by code."""
    
    service = ThirdPartyService(db)
    third_party = await service.get_third_party_by_code(code)
    
    if not third_party:
        raise_not_found("Tercero no encontrado")
    
    return ThirdPartyResponse.model_validate(third_party)


@router.get(
    "/document/{document_type}/{document_number}",
    response_model=ThirdPartyResponse,
    summary="Get third party by document",
    description="Get third party by document type and number"
)
async def get_third_party_by_document(
    document_type: DocumentType,
    document_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyResponse:
    """Get third party by document."""
    
    service = ThirdPartyService(db)
    third_party = await service.get_third_party_by_document(document_type, document_number)
    
    if not third_party:
        raise_not_found("Tercero no encontrado")
    
    return ThirdPartyResponse.model_validate(third_party)


@router.put(
    "/{third_party_id}",
    response_model=ThirdPartyResponse,
    summary="Update third party",
    description="Update third party information"
)
async def update_third_party(
    third_party_id: uuid.UUID,
    third_party_data: ThirdPartyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyResponse:
    """Update third party."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = ThirdPartyService(db)
        third_party = await service.update_third_party(third_party_id, third_party_data)
        return ThirdPartyResponse.model_validate(third_party)
    except NotFoundError:
        raise_not_found("Tercero no encontrado")
    except ConflictError as e:
        raise_conflict_error(str(e))
    except ValidationError as e:
        raise_validation_error(str(e))


@router.delete(
    "/{third_party_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete third party",
    description="Delete third party if no movements exist"
)
async def delete_third_party(
    third_party_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete third party."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = ThirdPartyService(db)
        await service.delete_third_party(third_party_id)
        return {"message": "Tercero eliminado exitosamente"}
    except NotFoundError:
        raise_not_found("Tercero no encontrado")
    except BusinessLogicError as e:
        raise_validation_error(str(e))


@router.get(
    "/type/{third_party_type}",
    response_model=List[ThirdPartyResponse],
    summary="Get third parties by type",
    description="Get all active third parties of a specific type"
)
async def get_third_parties_by_type(
    third_party_type: ThirdPartyType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[ThirdPartyResponse]:
    """Get third parties by type."""
    
    service = ThirdPartyService(db)
    third_parties = await service.get_third_parties_by_type(third_party_type)
    
    return [ThirdPartyResponse.model_validate(tp) for tp in third_parties]


@router.get(
    "/{third_party_id}/statement",
    response_model=ThirdPartyStatement,
    summary="Get third party statement",
    description="Generate third party account statement for a period"
)
async def get_third_party_statement(
    third_party_id: uuid.UUID,
    start_date: date = Query(..., description="Start date for the statement"),
    end_date: date = Query(..., description="End date for the statement"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyStatement:
    """Get third party statement."""
    
    try:
        service = ThirdPartyService(db)
        statement = await service.get_third_party_statement(third_party_id, start_date, end_date)
        return statement
    except NotFoundError:
        raise_not_found("Tercero no encontrado")


@router.get(
    "/{third_party_id}/balance",
    response_model=ThirdPartyBalance,
    summary="Get third party balance",
    description="Get current balance and credit information for third party"
)
async def get_third_party_balance(
    third_party_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyBalance:
    """Get third party balance."""
    
    try:
        service = ThirdPartyService(db)
        balance = await service.get_third_party_balance(third_party_id)
        return balance
    except NotFoundError:
        raise_not_found("Tercero no encontrado")


@router.get(
    "/{third_party_id}/validate",
    response_model=ThirdPartyValidation,
    summary="Validate third party",
    description="Validate third party data and uniqueness constraints"
)
async def validate_third_party(
    third_party_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyValidation:
    """Validate third party."""
    
    service = ThirdPartyService(db)
    validation = await service.validate_third_party(third_party_id)
    return validation


@router.get(
    "/statistics/summary",
    response_model=ThirdPartyStats,
    summary="Get third party statistics",
    description="Get third party distribution and usage statistics"
)
async def get_third_party_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ThirdPartyStats:
    """Get third party statistics."""
    
    service = ThirdPartyService(db)
    stats = await service.get_third_party_stats()
    return stats


@router.post(
    "/bulk-operation",
    summary="Bulk third party operation",
    description="Perform bulk operations on multiple third parties"
)
async def bulk_third_party_operation(
    operation_data: BulkThirdPartyOperation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform bulk operation on third parties."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    service = ThirdPartyService(db)
    results = await service.bulk_operation(operation_data)
    return results
