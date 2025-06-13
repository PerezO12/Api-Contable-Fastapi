"""
API endpoints for cost center management.
Provides CRUD operations, hierarchy management and reporting for cost centers.
"""
import uuid
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.cost_center import (
    CostCenterCreate, CostCenterUpdate, CostCenterResponse, CostCenterDetailResponse,
    CostCenterListResponse, CostCenterList, CostCenterFilter, CostCenterReport,
    CostCenterValidation, BulkCostCenterOperation, CostCenterStats, BulkCostCenterDelete,
    BulkCostCenterDeleteResult, CostCenterDeleteValidation, CostCenterImportResult
)
from app.services.cost_center_service import CostCenterService
from app.utils.exceptions import (
    NotFoundError, ConflictError, ValidationError, BusinessLogicError,
    raise_not_found, raise_validation_error, raise_conflict_error,
    raise_insufficient_permissions
)

router = APIRouter()


@router.post(
    "/",
    response_model=CostCenterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create cost center",
    description="Create a new cost center with hierarchical support"
)
async def create_cost_center(
    cost_center_data: CostCenterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterResponse:
    """Create a new cost center."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = CostCenterService(db)
        cost_center = await service.create_cost_center(cost_center_data)
        return CostCenterResponse.model_validate(cost_center)
    except ConflictError as e:
        raise_conflict_error(str(e))
    except ValidationError as e:
        raise_validation_error(str(e))


@router.get(
    "/",
    response_model=CostCenterListResponse,
    summary="Get cost centers",
    description="Get paginated list of cost centers with filtering"
)
async def get_cost_centers(
    search: Optional[str] = Query(None, description="Search in code, name or description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_id: Optional[uuid.UUID] = Query(None, description="Filter by parent cost center"),
    allows_direct_assignment: Optional[bool] = Query(None, description="Filter by assignment capability"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterListResponse:
    """Get paginated list of cost centers."""
    
    filter_params = CostCenterFilter(
        search=search,
        is_active=is_active,
        parent_id=parent_id,
        allows_direct_assignment=allows_direct_assignment
    )
    
    service = CostCenterService(db)
    cost_centers_list = await service.get_cost_centers_list(filter_params, skip, limit)
    
    return CostCenterListResponse(
        items=cost_centers_list.cost_centers,
        total=cost_centers_list.total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{cost_center_id}",
    response_model=CostCenterDetailResponse,
    summary="Get cost center",
    description="Get cost center by ID with hierarchy information"
)
async def get_cost_center(
    cost_center_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterDetailResponse:
    """Get cost center by ID."""
    
    service = CostCenterService(db)
    cost_center = await service.get_cost_center_by_id(cost_center_id)
    
    if not cost_center:
        raise_not_found("Centro de costo no encontrado")
    
    return CostCenterDetailResponse.model_validate(cost_center)


@router.get(
    "/code/{code}",
    response_model=CostCenterResponse,
    summary="Get cost center by code",
    description="Get cost center by unique code"
)
async def get_cost_center_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterResponse:
    """Get cost center by code."""
    
    service = CostCenterService(db)
    cost_center = await service.get_cost_center_by_code(code)
    
    if not cost_center:
        raise_not_found("Centro de costo no encontrado")
    
    return CostCenterResponse.model_validate(cost_center)


@router.put(
    "/{cost_center_id}",
    response_model=CostCenterResponse,
    summary="Update cost center",
    description="Update cost center information"
)
async def update_cost_center(
    cost_center_id: uuid.UUID,
    cost_center_data: CostCenterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterResponse:
    """Update cost center."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = CostCenterService(db)
        cost_center = await service.update_cost_center(cost_center_id, cost_center_data)
        return CostCenterResponse.model_validate(cost_center)
    except NotFoundError:
        raise_not_found("Centro de costo no encontrado")
    except ValidationError as e:
        raise_validation_error(str(e))


@router.delete(
    "/{cost_center_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete cost center",
    description="Delete cost center if no movements exist"
)
async def delete_cost_center(
    cost_center_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete cost center."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        service = CostCenterService(db)
        await service.delete_cost_center(cost_center_id)
        return {"message": "Centro de costo eliminado exitosamente"}
    except NotFoundError:
        raise_not_found("Centro de costo no encontrado")
    except BusinessLogicError as e:
        raise_validation_error(str(e))


@router.get(
    "/hierarchy/tree",
    response_model=List[CostCenterDetailResponse],
    summary="Get cost center hierarchy",
    description="Get hierarchical tree of cost centers"
)
async def get_cost_center_hierarchy(
    parent_id: Optional[uuid.UUID] = Query(None, description="Parent cost center ID (null for root)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[CostCenterDetailResponse]:
    """Get cost center hierarchy."""
    
    service = CostCenterService(db)
    hierarchy = await service.get_cost_center_hierarchy(parent_id)
    
    return [CostCenterDetailResponse.model_validate(cc) for cc in hierarchy]


@router.get(
    "/{cost_center_id}/report",
    response_model=CostCenterReport,
    summary="Get cost center report",
    description="Generate cost center activity report for a period"
)
async def get_cost_center_report(
    cost_center_id: uuid.UUID,
    start_date: date = Query(..., description="Start date for the report"),
    end_date: date = Query(..., description="End date for the report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterReport:
    """Get cost center report."""
    
    try:
        service = CostCenterService(db)
        report = await service.get_cost_center_report(cost_center_id, start_date, end_date)
        return report
    except NotFoundError:
        raise_not_found("Centro de costo no encontrado")


@router.get(
    "/{cost_center_id}/validate",
    response_model=CostCenterValidation,
    summary="Validate cost center",
    description="Validate cost center data and hierarchy"
)
async def validate_cost_center(
    cost_center_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterValidation:
    """Validate cost center."""
    
    service = CostCenterService(db)
    validation = await service.validate_cost_center(cost_center_id)
    return validation


@router.get(
    "/statistics/summary",
    response_model=CostCenterStats,
    summary="Get cost center statistics",
    description="Get cost center usage and distribution statistics"
)
async def get_cost_center_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CostCenterStats:
    """Get cost center statistics."""
    
    service = CostCenterService(db)
    stats = await service.get_cost_center_stats()
    return stats


@router.post(
    "/bulk-operation",
    summary="Bulk cost center operation",
    description="Perform bulk operations on multiple cost centers"
)
async def bulk_cost_center_operation(
    operation_data: BulkCostCenterOperation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform bulk operation on cost centers."""
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    service = CostCenterService(db)
    results = await service.bulk_operation(operation_data)
    return results


@router.post("/bulk-delete", response_model=BulkCostCenterDeleteResult, status_code=status.HTTP_200_OK)
async def bulk_delete_cost_centers(
    delete_request: BulkCostCenterDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BulkCostCenterDeleteResult:
    """
    Eliminar múltiples centros de costo con validaciones exhaustivas.
    
    Este endpoint realiza validaciones detalladas antes de eliminar cada centro de costo:
    - Verifica que no tengan asientos contables asociados
    - Verifica que no tengan centros de costo hijos
    - Verifica que no estén siendo utilizados en otras partes del sistema
    - Permite forzar eliminación con force_delete=true
    
    Requiere permisos de creación de asientos.
    """
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    service = CostCenterService(db)
    
    try:
        result = await service.bulk_delete_cost_centers(delete_request, current_user.id)
        return result
    except ValidationError as e:
        raise_validation_error(str(e))


@router.post("/validate-deletion", response_model=List[CostCenterDeleteValidation])
async def validate_cost_centers_for_deletion(
    cost_center_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[CostCenterDeleteValidation]:
    """
    Validar si múltiples centros de costo pueden ser eliminados sin proceder con la eliminación.
    
    Este endpoint es útil para verificar qué centros de costo pueden eliminarse antes de 
    realizar la operación de borrado masivo.
    
    Requiere permisos de creación de asientos.
    """
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    service = CostCenterService(db)
    
    validations = []
    for cost_center_id in cost_center_ids:
        validation = await service.validate_cost_center_for_deletion(cost_center_id)
        validations.append(validation)
    
    return validations


@router.post("/import", response_model=CostCenterImportResult, status_code=status.HTTP_201_CREATED)
async def import_cost_centers(
    file_content: str,  # En producción usar UploadFile de FastAPI
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CostCenterImportResult:
    """
    Importar centros de costo desde archivo CSV/Excel.
    
    El archivo debe contener las siguientes columnas:
    - code: Código único del centro de costo (requerido)
    - name: Nombre del centro de costo (requerido)
    - description: Descripción (opcional)
    - parent_code: Código del centro de costo padre (opcional)
    - is_active: Si está activo (opcional, por defecto true)
    - allows_direct_assignment: Si permite asignación directa (opcional, por defecto true)
    - manager_name: Nombre del responsable (opcional)
    - budget_code: Código presupuestario (opcional)
    - notes: Notas adicionales (opcional)
    
    Requiere permisos de creación de asientos.
    """
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    service = CostCenterService(db)
    return await service.import_cost_centers_from_csv(file_content, current_user.id)


@router.get("/export/csv")
async def export_cost_centers_csv(
    is_active: Optional[bool] = None,
    parent_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Exportar centros de costo a formato CSV.
    
    Genera un archivo CSV con todos los centros de costo y sus propiedades,
    útil para respaldo o para preparar archivos de importación masiva.
    """
    service = CostCenterService(db)
    # En producción retornar StreamingResponse con el CSV
    return await service.export_cost_centers_to_csv(is_active, parent_id)
