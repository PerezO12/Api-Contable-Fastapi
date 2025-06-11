"""
API endpoints para exportación genérica de datos
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.database import get_db as get_sync_db
from app.models.user import User, UserRole
from app.schemas.export_generic import (
    ExportRequest, ExportResponse, ExportFormat, TableName,
    TableSchema, AvailableTablesResponse, ExportFilter, ColumnInfo
)
from app.services.export_service import ExportService
from app.utils.exceptions import raise_insufficient_permissions, raise_validation_error

router = APIRouter()


class SimpleExportRequest(BaseModel):
    """Request simplificado para exportación por IDs"""
    table: TableName
    format: ExportFormat
    ids: List[str]
    file_name: Optional[str] = None


@router.get(
    "/tables",
    response_model=AvailableTablesResponse,
    summary="Get available tables for export",
    description="Returns list of all available tables that can be exported with their schemas"
)
def get_available_tables(
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene todas las tablas disponibles para exportación"""
    # Solo usuarios ADMIN y CONTADOR pueden ver información de tablas
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    export_service = ExportService(db)
    return export_service.get_available_tables()


@router.get(
    "/tables/{table_name}",
    response_model=TableSchema,
    summary="Get table schema",
    description="Returns detailed schema information for a specific table"
)
def get_table_schema(
    table_name: TableName,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene el schema detallado de una tabla específica"""
    # Solo usuarios ADMIN y CONTADOR pueden ver esquemas de tablas
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        export_service = ExportService(db)
        return export_service.get_table_schema(table_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al obtener esquema de tabla: {str(e)}"
        )


@router.post(
    "/export",
    summary="Export specific records from any table",
    description="Export specific records by IDs from any available table in CSV, JSON, or XLSX format"
)
def export_data(
    request: SimpleExportRequest,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exporta registros específicos de cualquier tabla usando lista de IDs"""
    # Solo usuarios ADMIN y CONTADOR pueden exportar datos
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Convertir strings a UUIDs
        uuid_ids = []
        for id_str in request.ids:
            try:
                uuid_ids.append(uuid.UUID(id_str))
            except ValueError:
                raise_validation_error(f"ID inválido: {id_str}")
        
        # Crear filtros con IDs específicos
        filters = ExportFilter(
            ids=uuid_ids,
            date_from=None,
            date_to=None,
            active_only=None,
            custom_filters=None,
            limit=None,
            offset=0
        )
        
        # Crear request completo
        export_request = ExportRequest(
            table_name=request.table,
            export_format=request.format,
            filters=filters,
            columns=None,
            include_metadata=True,
            file_name=request.file_name
        )
        
        export_service = ExportService(db)
        result = export_service.export_data(export_request, current_user.id)
        
        # Determinar tipo de respuesta según formato
        if request.format == ExportFormat.JSON:
            return JSONResponse(
                content=result.file_content,
                headers={
                    "Content-Disposition": f"attachment; filename={result.file_name}"
                }
            )
        elif request.format == ExportFormat.CSV:
            return Response(
                content=result.file_content,
                media_type=result.content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={result.file_name}"
                }
            )
        elif request.format == ExportFormat.XLSX:
            return Response(
                content=result.file_content,
                media_type=result.content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={result.file_name}"
                }
            )
        else:
            raise_validation_error(f"Formato no soportado: {request.format}")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la exportación: {str(e)}"
        )


@router.get(
    "/formats",
    summary="Get supported export formats",
    description="Returns list of supported export formats"
)
def get_export_formats(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene los formatos de exportación soportados"""
    return {
        "formats": [
            {
                "value": ExportFormat.CSV,
                "name": "CSV",
                "description": "Archivo de valores separados por comas",
                "extension": "csv",
                "mime_type": "text/csv"
            },
            {
                "value": ExportFormat.JSON,
                "name": "JSON",
                "description": "Archivo de formato JSON",
                "extension": "json",
                "mime_type": "application/json"
            },
            {
                "value": ExportFormat.XLSX,
                "name": "Excel",
                "description": "Archivo de Excel",
                "extension": "xlsx",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        ]
    }


@router.post(
    "/export/users",
    summary="Export specific users",
    description="Export specific users by IDs"
)
def export_users(
    format: ExportFormat,
    ids: List[str],
    file_name: Optional[str] = "usuarios",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de usuarios específicos"""
    # Solo ADMIN puede exportar usuarios
    if current_user.role != UserRole.ADMIN:
        raise_insufficient_permissions()
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.USERS,
        format=format,
        ids=ids,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.post(
    "/export/accounts",
    summary="Export specific accounts",
    description="Export specific accounts by IDs"
)
def export_accounts(
    format: ExportFormat,
    ids: List[str],
    file_name: Optional[str] = "plan_cuentas",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de cuentas específicas"""
    
    # Solo ADMIN y CONTADOR pueden exportar cuentas
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.ACCOUNTS,
        format=format,
        ids=ids,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.post(
    "/export/journal-entries",
    summary="Export specific journal entries",
    description="Export specific journal entries by IDs"
)
def export_journal_entries(
    format: ExportFormat,
    ids: List[str],
    file_name: Optional[str] = "asientos_contables",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de asientos contables específicos"""
    
    # Solo ADMIN y CONTADOR pueden exportar asientos
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.JOURNAL_ENTRIES,
        format=format,
        ids=ids,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.post(
    "/export/advanced",
    summary="Advanced export with complex filters",
    description="Export data with advanced filtering options using request body"
)
def export_data_advanced(
    request: ExportRequest,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación avanzada con filtros complejos mediante request body"""
    # Solo usuarios ADMIN y CONTADOR pueden exportar datos
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        export_service = ExportService(db)
        result = export_service.export_data(request, current_user.id)
        
        # Determinar tipo de respuesta según formato
        if request.export_format == ExportFormat.JSON:
            return JSONResponse(
                content=result.file_content,
                headers={
                    "Content-Disposition": f"attachment; filename={result.file_name}"
                }
            )
        elif request.export_format == ExportFormat.CSV:
            return Response(
                content=result.file_content,
                media_type=result.content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={result.file_name}"
                }
            )
        elif request.export_format == ExportFormat.XLSX:
            return Response(
                content=result.file_content,
                media_type=result.content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={result.file_name}"
                }
            )
        else:
            raise_validation_error(f"Formato no soportado: {request.export_format}")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la exportación: {str(e)}"
        )
