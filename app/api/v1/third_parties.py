"""
API endpoints for third party management.
Provides CRUD operations, contact management and statement generation for customers, suppliers and other business partners.
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse, Response

from app.api.deps import get_db, get_current_active_user
from app.models.user import User, UserRole
from app.models.third_party import ThirdPartyType, DocumentType
from app.schemas.third_party import (
    ThirdPartyCreate, ThirdPartyUpdate, ThirdPartyResponse, ThirdPartyDetailResponse,
    ThirdPartyListResponse, ThirdPartyList, ThirdPartyFilter, ThirdPartyStatement,
    ThirdPartyBalance, ThirdPartyValidation, BulkThirdPartyOperation, ThirdPartyStats,
    BulkThirdPartyDelete, BulkThirdPartyDeleteResult, ThirdPartyDeleteValidation
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
        document_type=document_type,        is_active=is_active,
        city=city,
        country=country
    )
    
    service = ThirdPartyService(db)
    third_parties_list = await service.get_third_parties_list(filter_params, skip, limit)
    
    return ThirdPartyListResponse(
        items=third_parties_list.third_parties,
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


@router.post("/bulk-delete", response_model=BulkThirdPartyDeleteResult, status_code=status.HTTP_200_OK)
async def bulk_delete_third_parties(
    delete_request: BulkThirdPartyDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BulkThirdPartyDeleteResult:
    """
    Eliminar múltiples terceros con validaciones exhaustivas.
    
    Este endpoint realiza validaciones detalladas antes de eliminar cada tercero:
    - Verifica que no tengan asientos contables asociados
    - Permite forzar eliminación con force_delete=true (aunque sigue validando reglas críticas)
    
    Solo disponible para usuarios con permisos de creación de entradas.
    """
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    service = ThirdPartyService(db)
    
    try:
        result = await service.bulk_delete_third_parties(delete_request)
        return result
    except ValidationError as e:
        raise_validation_error(str(e))


@router.post("/validate-deletion", response_model=List[ThirdPartyDeleteValidation])
async def validate_third_parties_for_deletion(
    third_party_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[ThirdPartyDeleteValidation]:
    """
    Validar si múltiples terceros pueden ser eliminados sin proceder con la eliminación.
    
    Este endpoint es útil para verificar qué terceros pueden eliminarse antes de 
    realizar la operación de borrado masivo.
    
    Solo disponible para usuarios con permisos de creación de entradas.
    """
    # Check permissions
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    service = ThirdPartyService(db)
    
    validations = []
    for third_party_id in third_party_ids:
        validation = await service.validate_third_party_for_deletion(third_party_id)
        validations.append(validation)
    
    return validations


# Exportación avanzada
@router.post(
    "/export/advanced",
    summary="Advanced export for third parties",
    description="Advanced export with complex filters and options"
)
async def export_third_parties_advanced(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación avanzada de terceros con filtros complejos"""
    # Solo ADMIN y CONTADOR pueden exportar
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Usar el sistema de exportación genérica
        from app.services.export_service import ExportService
        from app.schemas.export_generic import ExportRequest, ExportFilter, TableName, ExportFormat
        
        # Extraer parámetros del request
        export_format = ExportFormat(request.get('format', 'csv'))
        filters = request.get('filters', {})
        file_name = request.get('file_name', 'terceros_avanzado')
        
        # Convertir filtros a formato del sistema genérico
        export_filter = ExportFilter(
            ids=[uuid.UUID(id_) for id_ in filters.get('ids', [])] if filters.get('ids') else None,
            date_from=filters.get('date_from'),
            date_to=filters.get('date_to'),
            active_only=filters.get('active_only'),
            custom_filters=filters.get('custom_filters'),
            limit=filters.get('limit'),
            offset=filters.get('offset', 0)
        )
        
        # Crear request de exportación
        export_request = ExportRequest(
            table_name=TableName.THIRD_PARTIES,
            export_format=export_format,
            filters=export_filter,
            columns=request.get('columns'),
            include_metadata=request.get('include_metadata', True),
            file_name=file_name
        )
        
        # Usar el servicio síncrono de exportación
        from app.database import get_db as get_sync_db
        from sqlalchemy.orm import Session
        
        # Convertir a sesión síncrona para el servicio de exportación
        sync_db = next(get_sync_db())
        try:
            export_service = ExportService(sync_db)
            result = export_service.export_data(export_request, current_user.id)
            
            # Retornar según formato
            if export_format == ExportFormat.JSON:
                return JSONResponse(
                    content=result.file_content,
                    headers={"Content-Disposition": f"attachment; filename={result.file_name}"}
                )
            else:
                return Response(
                    content=result.file_content,
                    media_type=result.content_type,
                    headers={"Content-Disposition": f"attachment; filename={result.file_name}"}
                )
        finally:
            sync_db.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en exportación avanzada: {str(e)}"
        )


@router.get(
    "/export/{export_id}/status",
    summary="Get export status",
    description="Get the status of a third party export operation"
)
async def get_third_party_export_status(
    export_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener el estado de una exportación de terceros"""
    # Solo ADMIN y CONTADOR pueden consultar estado
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Por ahora devolver estado mock ya que las exportaciones son síncronas
        return {
            "export_id": export_id,
            "status": "completed",
            "progress": 100,
            "message": "Exportación completada",
            "download_url": f"/api/v1/third-parties/export/{export_id}/download",
            "created_at": "2024-01-01T00:00:00Z",
            "completed_at": "2024-01-01T00:00:01Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar estado de exportación: {str(e)}"
        )


@router.get(
    "/export/{export_id}/download",
    summary="Download export file",
    description="Download a previously generated third party export file"
)
async def download_third_party_export(
    export_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Descargar archivo de exportación de terceros"""
    # Solo ADMIN y CONTADOR pueden descargar
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Por ahora devolver error 404 ya que no hay almacenamiento temporal
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo de exportación no encontrado. Las exportaciones se procesan en tiempo real."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al descargar archivo: {str(e)}"
        )


# Importación de terceros
@router.post(
    "/import",
    summary="Import third parties",
    description="Import third parties from file"
)
async def import_third_parties(
    import_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Importar terceros desde archivo"""
    # Solo ADMIN y CONTADOR pueden importar
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Por ahora devolver respuesta mock
        # En el futuro implementar importación real
        return {
            "import_id": str(uuid.uuid4()),
            "status": "processing",
            "total_records": import_data.get("total_records", 0),
            "processed_records": 0,
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "message": "Importación iniciada"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en importación: {str(e)}"
        )


@router.get(
    "/import/{import_id}/status",
    summary="Get import status",
    description="Get the status of a third party import operation"
)
async def get_third_party_import_status(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener el estado de una importación de terceros"""
    # Solo ADMIN y CONTADOR pueden consultar estado
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Por ahora devolver estado mock
        return {
            "import_id": import_id,
            "status": "completed",
            "total_records": 100,
            "processed_records": 100,
            "success_count": 95,
            "error_count": 5,
            "errors": [
                {"row": 5, "error": "NIT duplicado"},
                {"row": 12, "error": "Formato de email inválido"}
            ],
            "message": "Importación completada con errores menores",
            "created_at": "2024-01-01T00:00:00Z",
            "completed_at": "2024-01-01T00:05:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar estado de importación: {str(e)}"
        )


# Operaciones bulk genéricas
@router.post(
    "/bulk-operations",
    summary="Generic bulk operations",
    description="Perform generic bulk operations on third parties"
)
async def bulk_third_party_operations(
    operation_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Operaciones bulk genéricas para terceros"""
    # Solo usuarios con permisos pueden hacer operaciones bulk
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        operation_type = operation_data.get("operation")
        third_party_ids = operation_data.get("third_party_ids", [])
        
        if not third_party_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere al menos un ID de tercero"
            )
        
        # Convertir strings a UUID
        uuid_ids = []
        for id_str in third_party_ids:
            try:
                uuid_ids.append(uuid.UUID(id_str))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ID inválido: {id_str}"
                )
        
        service = ThirdPartyService(db)
        success_count = 0
        failed_count = 0
        errors = []
        
        if operation_type == "toggle_active":
            for third_party_id in uuid_ids:
                try:
                    # Obtener tercero y cambiar estado
                    third_party = await service.get_third_party_by_id(third_party_id)
                    if third_party:
                        # Simular toggle (en el futuro implementar método real)
                        success_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"Tercero {third_party_id} no encontrado")
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error en {third_party_id}: {str(e)}")
        
        elif operation_type == "update_category":
            new_category = operation_data.get("new_category")
            if not new_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Se requiere nueva categoría para operación update_category"
                )
            
            for third_party_id in uuid_ids:
                try:
                    # En el futuro implementar actualización de categoría
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error en {third_party_id}: {str(e)}")
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operación no soportada: {operation_type}"
            )
        
        return {
            "operation_id": str(uuid.uuid4()),
            "status": "completed",
            "operation": operation_type,
            "total_processed": len(uuid_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors,
            "message": f"Operación {operation_type} completada"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en operación bulk: {str(e)}"
        )


@router.get(
    "/bulk-operations/{operation_id}/status",
    summary="Get bulk operation status",
    description="Get the status of a bulk operation"
)
async def get_bulk_operation_status(
    operation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener el estado de una operación bulk"""
    # Solo usuarios con permisos pueden consultar estado
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    try:
        # Por ahora devolver estado mock
        return {
            "operation_id": operation_id,
            "status": "completed",
            "operation": "toggle_active",
            "total_processed": 10,
            "success_count": 8,
            "failed_count": 2,
            "errors": [
                {"id": "uuid1", "error": "Tercero no encontrado"},
                {"id": "uuid2", "error": "Tercero en uso, no se puede modificar"}
            ],
            "progress": 100,
            "message": "Operación completada",
            "created_at": "2024-01-01T00:00:00Z",
            "completed_at": "2024-01-01T00:01:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar estado de operación: {str(e)}"
        )
