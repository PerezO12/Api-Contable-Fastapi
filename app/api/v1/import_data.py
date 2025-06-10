"""
API endpoints para importación de datos contables
Soporte empresarial para CSV, XLSX, JSON con validaciones robustas y procesamiento por lotes
"""
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.import_data import (
    ImportRequest, ImportPreviewRequest, ImportPreviewResponse, ImportResult,
    ImportStatusResponse, ImportConfiguration, ImportFormat, ImportDataType,
    ImportValidationLevel, ImportTemplateResponse
)
from app.services.import_data_service import ImportDataService
from app.utils.exceptions import (
    ImportError as ImportException,
    raise_validation_error,
    raise_insufficient_permissions
)

router = APIRouter()


@router.post(
    "/preview",
    response_model=ImportPreviewResponse,
    summary="Preview import data",
    description="Preview and validate import data without actually importing"
)
async def preview_import(
    request: ImportPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportPreviewResponse:
    """
    Preview importación - analiza el archivo y muestra una vista previa
    sin importar los datos realmente.
    """
    # Verificar permisos según el tipo de datos
    if request.configuration.data_type == ImportDataType.ACCOUNTS:
        if not current_user.can_modify_accounts:
            raise_insufficient_permissions()
    elif request.configuration.data_type == ImportDataType.JOURNAL_ENTRIES:
        if not current_user.can_create_entries:
            raise_insufficient_permissions()
    
    try:
        service = ImportDataService(db)
        result = await service.preview_import(
            file_content=request.file_content,
            filename=request.filename,
            config=request.configuration,
            preview_rows=request.preview_rows
        )
        return result
        
    except ImportException as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en preview de importación: {str(e)}"
        )


@router.post(
    "/upload-file",
    response_model=ImportPreviewResponse,
    summary="Upload and preview file",
    description="Upload a file and get preview for import configuration"
)
async def upload_and_preview_file(
    file: UploadFile = File(...),
    data_type: ImportDataType = Query(..., description="Type of data to import"),
    validation_level: ImportValidationLevel = Query(ImportValidationLevel.STRICT, description="Validation level"),
    batch_size: int = Query(100, ge=1, le=1000, description="Batch size for processing"),
    preview_rows: int = Query(10, ge=1, le=100, description="Number of rows to preview"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportPreviewResponse:
    """
    Subir archivo y obtener preview automático.
    Detecta formato y proporciona configuración sugerida.
    """
    # Verificar permisos
    if data_type == ImportDataType.ACCOUNTS:
        if not current_user.can_modify_accounts:
            raise_insufficient_permissions()
    elif data_type == ImportDataType.JOURNAL_ENTRIES:
        if not current_user.can_create_entries:
            raise_insufficient_permissions()
    
    try:
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Detectar formato por extensión
        extension = file.filename.lower().split('.')[-1] if file.filename else 'csv'
        
        if extension in ['xlsx', 'xls']:
            detected_format = ImportFormat.XLSX
        elif extension == 'json':
            detected_format = ImportFormat.JSON
        else:
            detected_format = ImportFormat.CSV
          # Configuración automática
        config = ImportConfiguration(
            data_type=data_type,
            format=detected_format,
            validation_level=validation_level,
            batch_size=batch_size,
            skip_duplicates=True,
            update_existing=False,
            continue_on_error=False,
            csv_delimiter=',',
            csv_encoding='utf-8',
            xlsx_sheet_name=None,
            xlsx_header_row=1
        )
        
        # Codificar contenido en base64 para el servicio
        import base64
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        service = ImportDataService(db)
        result = await service.preview_import(
            file_content=file_content_b64,
            filename=file.filename or "upload",
            config=config,
            preview_rows=preview_rows
        )
        
        return result
        
    except ImportException as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando archivo: {str(e)}"
        )


@router.post(
    "/import",
    response_model=ImportResult,
    summary="Import data",
    description="Import data from file with full validation and processing"
)
async def import_data(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportResult:
    """
    Importación principal de datos contables.
    Procesa archivos CSV, XLSX o JSON con validaciones empresariales.
    """
    # Verificar permisos según el tipo de datos
    if request.configuration.data_type == ImportDataType.ACCOUNTS:
        if not current_user.can_modify_accounts:
            raise_insufficient_permissions()
    elif request.configuration.data_type == ImportDataType.JOURNAL_ENTRIES:
        if not current_user.can_create_entries:
            raise_insufficient_permissions()
    
    try:
        service = ImportDataService(db)
        result = await service.import_data(
            file_content=request.file_content,
            filename=request.filename,
            config=request.configuration,
            user_id=current_user.id
        )
        
        return result
        
    except ImportException as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en importación: {str(e)}"
        )


@router.post(
    "/import-file",
    response_model=ImportResult,
    summary="Import from uploaded file",
    description="Direct import from uploaded file with automatic configuration"
)
async def import_from_file(
    file: UploadFile = File(...),
    data_type: ImportDataType = Query(..., description="Type of data to import"),
    validation_level: ImportValidationLevel = Query(ImportValidationLevel.STRICT, description="Validation level"),
    batch_size: int = Query(100, ge=1, le=1000, description="Batch size for processing"),
    skip_duplicates: bool = Query(True, description="Skip duplicate records"),
    update_existing: bool = Query(False, description="Update existing records"),
    continue_on_error: bool = Query(False, description="Continue processing on errors"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportResult:
    """
    Importación directa desde archivo subido.
    Configuración automática basada en el tipo de archivo.
    """
    # Verificar permisos
    if data_type == ImportDataType.ACCOUNTS:
        if not current_user.can_modify_accounts:
            raise_insufficient_permissions()
    elif data_type == ImportDataType.JOURNAL_ENTRIES:
        if not current_user.can_create_entries:
            raise_insufficient_permissions()
    
    # Validar tamaño del archivo (máximo 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise_validation_error("El archivo es demasiado grande (máximo 10MB)")
    
    try:
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Detectar formato
        extension = file.filename.lower().split('.')[-1] if file.filename else 'csv'
        
        if extension in ['xlsx', 'xls']:
            detected_format = ImportFormat.XLSX
        elif extension == 'json':
            detected_format = ImportFormat.JSON
        else:
            detected_format = ImportFormat.CSV
          # Configuración automática
        config = ImportConfiguration(
            data_type=data_type,
            format=detected_format,
            validation_level=validation_level,
            batch_size=batch_size,
            skip_duplicates=skip_duplicates,
            update_existing=update_existing,
            continue_on_error=continue_on_error,
            csv_delimiter=',',
            csv_encoding='utf-8',
            xlsx_sheet_name=None,
            xlsx_header_row=1
        )
        
        # Codificar contenido
        import base64
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        service = ImportDataService(db)
        result = await service.import_data(
            file_content=file_content_b64,
            filename=file.filename or "upload",
            config=config,
            user_id=current_user.id
        )
        
        return result
        
    except ImportException as e:
        raise_validation_error(str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en importación: {str(e)}"
        )


@router.get(
    "/templates",
    response_model=ImportTemplateResponse,
    summary="Get import templates",
    description="Get available import templates and formats"
)
async def get_import_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportTemplateResponse:
    """
    Obtener templates de importación disponibles.
    Incluye formatos soportados, columnas requeridas y datos de ejemplo.
    """
    try:
        service = ImportDataService(db)
        templates = await service.get_import_templates()
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo templates: {str(e)}"
        )


@router.get(
    "/templates/{data_type}/download",
    summary="Download import template",
    description="Download a template file for the specified data type"
)
async def download_import_template(
    data_type: ImportDataType,
    format: ImportFormat = Query(ImportFormat.CSV, description="Template format"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Descargar template de importación para el tipo de datos especificado.
    """
    try:
        # Generar contenido del template según el tipo
        if data_type == ImportDataType.ACCOUNTS:
            if format == ImportFormat.CSV:
                template_content = "code,name,account_type,category,parent_code,description,is_active,allows_movements\n"
                template_content += "1001,Caja,ACTIVO,ACTIVO_CORRIENTE,,Dinero en efectivo,true,true\n"
                template_content += "2001,Proveedores,PASIVO,PASIVO_CORRIENTE,,Cuentas por pagar,true,true\n"
                
                return JSONResponse(
                    content={
                        "filename": f"template_cuentas.{format.value}",
                        "content": template_content,
                        "content_type": "text/csv"
                    }
                )
            
        elif data_type == ImportDataType.JOURNAL_ENTRIES:
            if format == ImportFormat.CSV:
                template_content = "entry_date,description,account_code,debit_amount,credit_amount,reference\n"
                template_content += "2024-01-15,Venta de mercadería,1001,1000.00,0.00,FAC-001\n"
                template_content += "2024-01-15,Venta de mercadería,4001,0.00,1000.00,FAC-001\n"
                
                return JSONResponse(
                    content={
                        "filename": f"template_asientos.{format.value}",
                        "content": template_content,
                        "content_type": "text/csv"
                    }
                )
          # Si no se puede generar el template
        raise_validation_error("Template no disponible para la combinación especificada")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando template: {str(e)}"
        )


@router.get(
    "/formats",
    summary="Get supported formats",
    description="Get list of supported import formats and data types"
)
async def get_supported_formats(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Obtener formatos y tipos de datos soportados para importación.
    """
    return {
        "supported_formats": [
            {
                "format": ImportFormat.CSV.value,
                "description": "Comma Separated Values",
                "extensions": [".csv", ".txt"],
                "max_size_mb": 10,
                "supports_multiple_sheets": False
            },
            {
                "format": ImportFormat.XLSX.value,
                "description": "Microsoft Excel Spreadsheet",
                "extensions": [".xlsx", ".xls"],
                "max_size_mb": 10,
                "supports_multiple_sheets": True
            },
            {
                "format": ImportFormat.JSON.value,
                "description": "JavaScript Object Notation",
                "extensions": [".json"],
                "max_size_mb": 10,
                "supports_multiple_sheets": False
            }
        ],
        "supported_data_types": [
            {
                "type": ImportDataType.ACCOUNTS.value,
                "description": "Cuentas contables",
                "required_permissions": ["can_modify_accounts"],
                "supports_hierarchy": True,
                "supports_bulk_operations": True
            },
            {
                "type": ImportDataType.JOURNAL_ENTRIES.value,
                "description": "Asientos contables",
                "required_permissions": ["can_create_entries"],
                "supports_hierarchy": False,
                "supports_bulk_operations": True
            }
        ],
        "validation_levels": [
            {
                "level": ImportValidationLevel.STRICT.value,
                "description": "Falla si hay cualquier error de validación"
            },
            {
                "level": ImportValidationLevel.TOLERANT.value,
                "description": "Procesa registros válidos, reporta errores"
            },
            {
                "level": ImportValidationLevel.PREVIEW.value,
                "description": "Solo valida sin importar datos"
            }
        ],
        "limits": {
            "max_file_size_mb": 10,
            "max_rows_per_import": 10000,
            "max_batch_size": 1000,
            "max_preview_rows": 100
        }
    }


@router.get(
    "/status/{import_id}",
    response_model=ImportStatusResponse,
    summary="Get import status",
    description="Get status and progress of an ongoing import"
)
async def get_import_status(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportStatusResponse:
    """
    Obtener estado de una importación en progreso.
    Nota: Esta funcionalidad requiere implementación de seguimiento asíncrono.
    """
    # TODO: Implementar seguimiento de importaciones asíncronas
    # Por ahora, retornar estado básico
    
    return ImportStatusResponse(
        import_id=import_id,
        status="completed",
        progress_percentage=100.0,
        current_row=None,
        estimated_completion=None,
        summary=None
    )


@router.post(
    "/validate-data",
    summary="Validate import data structure",
    description="Validate data structure without importing"
)
async def validate_import_data(
    data: Dict[str, Any],
    data_type: ImportDataType = Query(..., description="Type of data to validate"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Validar estructura de datos sin importar.
    Útil para validación en tiempo real desde el frontend.
    """
    try:        # Validaciones básicas según el tipo de datos
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        if data_type == ImportDataType.ACCOUNTS:
            # Validar estructura de cuentas
            required_fields = ['code', 'name', 'account_type']
            
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        for field in required_fields:
                            if field not in item or not item.get(field):
                                validation_results["errors"].append(
                                    f"Fila {i+1}: Campo requerido '{field}' faltante o vacío"
                                )
                                validation_results["is_valid"] = False
            
        elif data_type == ImportDataType.JOURNAL_ENTRIES:
            # Validar estructura de asientos
            required_fields = ['entry_date', 'description', 'account_code']
            
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        for field in required_fields:
                            if field not in item or not item.get(field):
                                validation_results["errors"].append(
                                    f"Fila {i+1}: Campo requerido '{field}' faltante o vacío"
                                )
                                validation_results["is_valid"] = False
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en validación: {str(e)}"
        )


# Endpoints adicionales para funcionalidades avanzadas

@router.get(
    "/history",
    summary="Get import history",
    description="Get history of imports performed by the user"
)
async def get_import_history(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Records to return"),
    data_type: Optional[ImportDataType] = Query(None, description="Filter by data type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Obtener historial de importaciones del usuario.
    TODO: Implementar persistencia de historial de importaciones.
    """
    # Placeholder - implementar cuando se agregue persistencia
    return {
        "imports": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }


@router.delete(
    "/cancel/{import_id}",
    summary="Cancel import",
    description="Cancel an ongoing import operation"
)
async def cancel_import(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    Cancelar una importación en progreso.
    TODO: Implementar cancelación de importaciones asíncronas.
    """
    # Placeholder para cancelación
    return {
        "message": f"Importación {import_id} cancelada",
        "status": "cancelled"
    }


# ==========================================
# EXPORT TEMPLATE ENDPOINTS
# ==========================================

@router.get(
    "/templates/accounts/{format}",
    summary="Export accounts template",
    description="Download example template for accounts in CSV, XLSX, or JSON format"
)
async def export_accounts_template(
    format: ImportFormat,
    current_user: User = Depends(get_current_active_user)
):
    """
    Exportar plantilla de ejemplo para importación de cuentas.
    Proporciona la estructura y nombres de columnas requeridos.
    """
    example_accounts = [
        {
            "code": "1105",
            "name": "Caja General",
            "account_type": "ACTIVO",
            "category": "ACTIVO_CORRIENTE",
            "parent_code": "1100",
            "description": "Dinero en efectivo en caja principal",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": False,
            "requires_cost_center": False,
            "notes": "Cuenta para manejo de efectivo"
        },
        {
            "code": "1110",
            "name": "Bancos Moneda Nacional",
            "account_type": "ACTIVO",
            "category": "ACTIVO_CORRIENTE", 
            "parent_code": "1100",
            "description": "Depósitos en bancos en moneda nacional",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": True,
            "requires_cost_center": False,
            "notes": "Requiere especificar el banco como tercero"
        },
        {
            "code": "2105",
            "name": "Proveedores Nacionales",
            "account_type": "PASIVO",
            "category": "PASIVO_CORRIENTE",
            "parent_code": "2100",
            "description": "Cuentas por pagar a proveedores nacionales",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": True,
            "requires_cost_center": False,
            "notes": "Requiere especificar el proveedor"
        }
    ]
    
    if format == ImportFormat.JSON:
        return JSONResponse(
            content={
                "template_info": {
                    "data_type": "accounts",
                    "format": "json",
                    "description": "Plantilla de ejemplo para importación de cuentas contables",
                    "required_fields": ["code", "name", "account_type"],
                    "optional_fields": ["category", "parent_code", "description", "is_active", "allows_movements", "requires_third_party", "requires_cost_center", "notes"]
                },
                "field_descriptions": {
                    "code": "Código único de la cuenta (máximo 20 caracteres)",
                    "name": "Nombre de la cuenta (máximo 200 caracteres)",
                    "account_type": "Tipo de cuenta: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS",
                    "category": "Categoría específica según el tipo de cuenta",
                    "parent_code": "Código de la cuenta padre para estructura jerárquica",
                    "description": "Descripción detallada de la cuenta",
                    "is_active": "true/false - Si la cuenta está activa",
                    "allows_movements": "true/false - Si permite registrar movimientos",
                    "requires_third_party": "true/false - Si requiere especificar tercero en los movimientos",
                    "requires_cost_center": "true/false - Si requiere centro de costo",
                    "notes": "Notas adicionales sobre la cuenta"
                },
                "valid_account_types": ["ACTIVO", "PASIVO", "PATRIMONIO", "INGRESO", "GASTO", "COSTOS"],
                "valid_categories": {
                    "ACTIVO": ["ACTIVO_CORRIENTE", "ACTIVO_NO_CORRIENTE"],
                    "PASIVO": ["PASIVO_CORRIENTE", "PASIVO_NO_CORRIENTE"],
                    "PATRIMONIO": ["CAPITAL", "RESERVAS", "RESULTADOS"],
                    "INGRESO": ["INGRESOS_OPERACIONALES", "INGRESOS_NO_OPERACIONALES"],
                    "GASTO": ["GASTOS_OPERACIONALES", "GASTOS_NO_OPERACIONALES"],
                    "COSTOS": ["COSTO_VENTAS", "COSTOS_PRODUCCION"]
                },
                "example_data": example_accounts
            },
            headers={"Content-Disposition": "attachment; filename=accounts_template.json"}
        )
    
    elif format == ImportFormat.CSV:
        import io
        import csv
        from fastapi.responses import StreamingResponse
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        headers = ["code", "name", "account_type", "category", "parent_code", 
                  "description", "is_active", "allows_movements", "requires_third_party", 
                  "requires_cost_center", "notes"]
        writer.writerow(headers)
        
        # Escribir datos de ejemplo
        for account in example_accounts:
            row = [account.get(field, "") for field in headers]
            writer.writerow(row)
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=accounts_template.csv"}
        )
    
    elif format == ImportFormat.XLSX:
        import io
        import pandas as pd
        from fastapi.responses import StreamingResponse
        
        # Crear DataFrame con los datos de ejemplo
        df = pd.DataFrame(example_accounts)
        
        # Reordenar columnas en orden lógico
        column_order = ["code", "name", "account_type", "category", "parent_code", 
                       "description", "is_active", "allows_movements", "requires_third_party", 
                       "requires_cost_center", "notes"]
        df = df.reindex(columns=column_order)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja con datos de ejemplo
            df.to_excel(writer, sheet_name='Accounts_Template', index=False)
            
            # Hoja con documentación
            doc_data = {
                'Field': column_order,
                'Required': ['Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No'],
                'Description': [
                    'Código único de la cuenta (máximo 20 caracteres)',
                    'Nombre de la cuenta (máximo 200 caracteres)', 
                    'Tipo: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS',
                    'Categoría específica según el tipo de cuenta',
                    'Código de la cuenta padre para jerarquía',
                    'Descripción detallada de la cuenta',
                    'true/false - Si la cuenta está activa',
                    'true/false - Si permite movimientos',
                    'true/false - Si requiere tercero',
                    'true/false - Si requiere centro de costo',
                    'Notas adicionales'
                ]
            }
            doc_df = pd.DataFrame(doc_data)
            doc_df.to_excel(writer, sheet_name='Field_Documentation', index=False)
        
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=accounts_template.xlsx"}
        )


@router.get(
    "/import/{import_id}/summary",
    response_model=Dict[str, Any],
    summary="Get detailed import summary",
    description="Get detailed and user-friendly summary of import results"
)
async def get_import_summary(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Obtener resumen detallado y amigable de los resultados de importación.
    Incluye estadísticas, mensajes de feedback y recomendaciones.
    """
    try:
        # Por ahora, vamos a simular la obtención de datos de importación
        # En una implementación completa, esto vendría de una base de datos de importaciones
        
        # Este es un placeholder - en producción necesitarías almacenar los resultados de importación
        return {
            "import_id": import_id,
            "status": "completed",
            "feedback": {
                "status_message": "Resumen de importación no disponible para este ID",
                "detailed_feedback": [
                    "ℹ️ Para obtener estadísticas detalladas, consulte la respuesta del endpoint de importación directamente"
                ]
            },
            "recommendations": [
                "Use el endpoint POST /import para obtener estadísticas completas en tiempo real",
                "Verifique que el import_id sea válido y corresponda a una importación reciente"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resumen de importación: {str(e)}"
        )
