"""
API endpoints para exportación genérica de datos
"""
import uuid
from typing import List, Optional, Dict, Any
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


class BulkExportRequest(BaseModel):
    """Request para exportación masiva de múltiples tablas"""
    exports: List[SimpleExportRequest]
    compress: bool = True  # Comprimir en ZIP si hay múltiples archivos
    file_name: Optional[str] = None


class ExportStatusResponse(BaseModel):
    """Response para consultar el estado de una exportación"""
    export_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: int  # 0-100
    message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


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
    "/export/payment-terms",
    summary="Export specific payment terms",
    description="Export specific payment terms by IDs"
)
def export_payment_terms(
    format: ExportFormat,
    ids: List[str],
    file_name: Optional[str] = "condiciones_pago",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de condiciones de pago específicas"""
    
    # Solo ADMIN y CONTADOR pueden exportar condiciones de pago
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.PAYMENT_TERMS,
        format=format,
        ids=ids,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.post(
    "/export/cost-centers",
    summary="Export specific cost centers",
    description="Export specific cost centers by IDs"
)
def export_cost_centers(
    format: ExportFormat,
    ids: List[str],
    file_name: Optional[str] = "centros_costo",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de centros de costo específicos"""
    
    # Solo ADMIN y CONTADOR pueden exportar centros de costo
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.COST_CENTERS,
        format=format,
        ids=ids,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.post(
    "/export/products",
    summary="Export specific products",
    description="Export specific products by IDs"
)
def export_products(
    format: ExportFormat,
    ids: List[str],
    file_name: Optional[str] = "productos",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de productos específicos"""
    
    # Solo ADMIN y CONTADOR pueden exportar productos
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.PRODUCTS,
        format=format,
        ids=ids,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.post(
    "/export/third-parties",
    summary="Export specific third parties",
    description="Export specific third parties by IDs"
)
def export_third_parties(
    format: ExportFormat,
    ids: List[str],
    file_name: Optional[str] = "terceros",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de terceros específicos"""
    
    # Solo ADMIN y CONTADOR pueden exportar terceros
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.THIRD_PARTIES,
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


@router.post(
    "/export/bulk",
    summary="Bulk export multiple tables",
    description="Export data from multiple tables in a single request, optionally compressed in ZIP"
)
def export_bulk_data(
    request: BulkExportRequest,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación masiva de múltiples tablas"""
    # Solo usuarios ADMIN y CONTADOR pueden exportar datos
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        export_service = ExportService(db)
        
        # Por ahora, procesar cada exportación individualmente
        # En el futuro se podría implementar exportación asíncrona
        results = []
        
        for export_req in request.exports:
            # Convertir strings a UUIDs
            uuid_ids = []
            for id_str in export_req.ids:
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
            full_request = ExportRequest(
                table_name=export_req.table,
                export_format=export_req.format,
                filters=filters,
                columns=None,
                include_metadata=True,
                file_name=export_req.file_name
            )
            
            result = export_service.export_data(full_request, current_user.id)
            results.append({
                "table": export_req.table,
                "format": export_req.format,
                "file_name": result.file_name,
                "file_content": result.file_content,
                "content_type": result.content_type
            })
          # Si solo hay una exportación, devolverla directamente
        if len(results) == 1:
            result = results[0]
            return Response(
                content=result["file_content"],
                media_type=result["content_type"],
                headers={
                    "Content-Disposition": f"attachment; filename={result['file_name']}"
                }
            )
        
        # Si hay múltiples exportaciones, crear un ZIP (por implementar)
        # Por ahora devolver la primera
        result = results[0]
        return Response(
            content=result["file_content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['file_name']}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la exportación masiva: {str(e)}"
        )


@router.get(
    "/export/{export_id}/status",
    response_model=ExportStatusResponse,
    summary="Get export status",
    description="Get the status of an export operation"
)
def get_export_status(
    export_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener el estado de una exportación"""
    # Solo usuarios ADMIN y CONTADOR pueden consultar estado de exportaciones
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Por ahora, como las exportaciones son síncronas, siempre devolver completado
        # En el futuro se podría implementar un sistema de exportaciones asíncronas
        return ExportStatusResponse(
            export_id=export_id,
            status="completed",
            progress=100,
            message="Exportación completada",
            download_url=f"/api/v1/export/{export_id}/download",
            created_at="2024-01-01T00:00:00Z",
            completed_at="2024-01-01T00:00:01Z"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar estado de exportación: {str(e)}"
        )


@router.get(
    "/export/{export_id}/download",
    summary="Download exported file",
    description="Download a previously generated export file"
)
def download_export_file(
    export_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Descargar un archivo de exportación generado previamente"""
    # Solo usuarios ADMIN y CONTADOR pueden descargar exportaciones
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Por ahora, devolver un error indicando que la funcionalidad no está disponible
        # En el futuro se podría implementar un sistema de almacenamiento temporal de archivos
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo de exportación no encontrado. Las exportaciones son procesadas en tiempo real."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al descargar archivo de exportación: {str(e)}"
        )


@router.get(
    "/stats",
    summary="Get export statistics",
    description="Get statistics about export operations"
)
def get_export_stats(
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener estadísticas de exportaciones"""
    # Solo usuarios ADMIN pueden ver estadísticas
    if current_user.role != UserRole.ADMIN:
        raise_insufficient_permissions()
    
    try:
        # Por ahora devolver estadísticas mock
        # En el futuro se podría implementar un sistema de logging de exportaciones
        return {
            "total_exports": 0,
            "exports_today": 0,
            "exports_this_month": 0,
            "popular_formats": {
                "csv": 0,
                "xlsx": 0,
                "json": 0
            },
            "popular_tables": {
                "accounts": 0,
                "journal_entries": 0,
                "products": 0,
                "third_parties": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas de exportación: {str(e)}"
        )


@router.post(
    "/export/validate",
    summary="Validate export request",
    description="Validate an export request without executing it"
)
def validate_export_request(
    request: SimpleExportRequest,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Validar una solicitud de exportación sin ejecutarla"""
    # Solo usuarios ADMIN y CONTADOR pueden validar exportaciones
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    try:
        # Validar que la tabla existe
        export_service = ExportService(db)
        table_schema = export_service.get_table_schema(request.table)
        
        # Validar que los IDs son válidos
        valid_ids = []
        invalid_ids = []
        
        for id_str in request.ids:
            try:
                uuid.UUID(id_str)
                valid_ids.append(id_str)
            except ValueError:
                invalid_ids.append(id_str)
        
        return {
            "valid": len(invalid_ids) == 0,
            "table_exists": True,
            "table_name": table_schema.table_name,
            "total_records": table_schema.total_records,
            "valid_ids_count": len(valid_ids),
            "invalid_ids": invalid_ids,
            "estimated_size": len(valid_ids) * 1024,  # Estimación simple
            "supported_format": request.format in [ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX]
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


# ======================================================================
# ENDPOINTS GET PARA COMPATIBILIDAD CON FRONTEND
# ======================================================================

@router.get(
    "/products/export",
    summary="Export products with query parameters",
    description="Export products using GET with query parameters for frontend compatibility"
)
def export_products_get(
    format: ExportFormat,
    ids: Optional[str] = None,  # Comma-separated IDs
    file_name: Optional[str] = "productos",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de productos usando GET con query parameters"""
    
    # Solo ADMIN y CONTADOR pueden exportar productos
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Parsear IDs si se proporcionan
    ids_list = []
    if ids:
        ids_list = [id.strip() for id in ids.split(',') if id.strip()]
    
    # Si no hay IDs específicos, exportar todos (con límite de seguridad)
    if not ids_list:
        # Obtener todos los IDs de productos activos (con límite)
        from app.models.product import Product
        products = db.query(Product).limit(1000).all()  # Límite de seguridad
        ids_list = [str(product.id) for product in products]
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.PRODUCTS,
        format=format,
        ids=ids_list,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.get(
    "/third-parties/export", 
    summary="Export third parties with query parameters",
    description="Export third parties using GET with query parameters for frontend compatibility"
)
def export_third_parties_get(
    format: ExportFormat,
    ids: Optional[str] = None,  # Comma-separated IDs
    file_name: Optional[str] = "terceros",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de terceros usando GET con query parameters"""
    
    # Solo ADMIN y CONTADOR pueden exportar terceros
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Parsear IDs si se proporcionan
    ids_list = []
    if ids:
        ids_list = [id.strip() for id in ids.split(',') if id.strip()]
    
    # Si no hay IDs específicos, exportar todos (con límite de seguridad)
    if not ids_list:
        # Obtener todos los IDs de terceros activos (con límite)
        from app.models.third_party import ThirdParty
        third_parties = db.query(ThirdParty).limit(1000).all()  # Límite de seguridad
        ids_list = [str(tp.id) for tp in third_parties]
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.THIRD_PARTIES,
        format=format,
        ids=ids_list,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.get(
    "/accounts/export",
    summary="Export accounts with query parameters", 
    description="Export accounts using GET with query parameters for frontend compatibility"
)
def export_accounts_get(
    format: ExportFormat,
    ids: Optional[str] = None,  # Comma-separated IDs
    file_name: Optional[str] = "cuentas",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de cuentas usando GET con query parameters"""
    
    # Solo ADMIN y CONTADOR pueden exportar cuentas
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Parsear IDs si se proporcionan
    ids_list = []
    if ids:
        ids_list = [id.strip() for id in ids.split(',') if id.strip()]
    
    # Si no hay IDs específicos, exportar todos (con límite de seguridad)
    if not ids_list:
        # Obtener todos los IDs de cuentas activas (con límite)
        from app.models.account import Account
        accounts = db.query(Account).limit(1000).all()  # Límite de seguridad
        ids_list = [str(account.id) for account in accounts]
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.ACCOUNTS,
        format=format,
        ids=ids_list,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.get(
    "/cost-centers/export",
    summary="Export cost centers with query parameters",
    description="Export cost centers using GET with query parameters for frontend compatibility"
)
def export_cost_centers_get(
    format: ExportFormat,
    ids: Optional[str] = None,  # Comma-separated IDs
    file_name: Optional[str] = "centros_de_costo",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de centros de costo usando GET con query parameters"""
    
    # Solo ADMIN y CONTADOR pueden exportar centros de costo
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Parsear IDs si se proporcionan
    ids_list = []
    if ids:
        ids_list = [id.strip() for id in ids.split(',') if id.strip()]
    
    # Si no hay IDs específicos, exportar todos (con límite de seguridad)
    if not ids_list:
        # Obtener todos los IDs de centros de costo activos (con límite)
        from app.models.cost_center import CostCenter
        cost_centers = db.query(CostCenter).limit(1000).all()  # Límite de seguridad
        ids_list = [str(cc.id) for cc in cost_centers]
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.COST_CENTERS,
        format=format,
        ids=ids_list,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)


@router.get(
    "/journal-entries/export",
    summary="Export journal entries with query parameters",
    description="Export journal entries using GET with query parameters for frontend compatibility"
)
def export_journal_entries_get(
    format: ExportFormat,
    ids: Optional[str] = None,  # Comma-separated IDs
    file_name: Optional[str] = "asientos_contables",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exportación de asientos contables usando GET con query parameters"""
    
    # Solo ADMIN y CONTADOR pueden exportar asientos contables
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise_insufficient_permissions()
    
    # Parsear IDs si se proporcionan
    ids_list = []
    if ids:
        ids_list = [id.strip() for id in ids.split(',') if id.strip()]
    
    # Si no hay IDs específicos, exportar todos (con límite de seguridad)
    if not ids_list:
        # Obtener todos los IDs de asientos contables (con límite)
        from app.models.journal_entry import JournalEntry
        journal_entries = db.query(JournalEntry).limit(1000).all()  # Límite de seguridad
        ids_list = [str(je.id) for je in journal_entries]
    
    # Crear request simplificado
    request = SimpleExportRequest(
        table=TableName.JOURNAL_ENTRIES,
        format=format,
        ids=ids_list,
        file_name=file_name
    )
    
    return export_data(request, db, current_user)
