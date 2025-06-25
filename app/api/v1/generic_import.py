"""
Generic Data Import Assistant API Endpoints
Simplified version with core functionality
"""
import logging
import datetime
import math
import time
import csv
import io
import hashlib
import uuid
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.generic_import import (
    ModelMetadata,
    ImportSessionResponse,
    ColumnMapping,
    ImportPreviewRequest,
    ImportPreviewResponse,
    PreviewRowData,
    ValidationError,
    ValidationSummary
)
from app.services.model_metadata_registry import ModelMetadataRegistry
from app.services.import_session_service_simple import import_session_service
from app.services.product_service import ProductService
from app.models.product import Product
from app.schemas.product import ProductCreate
from app.utils.exceptions import (
    ModelNotFoundError,
    ImportSessionNotFoundError,
    ImportError
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
metadata_registry = ModelMetadataRegistry()
session_service = import_session_service


async def _create_entity_with_auto_fields(model_class, transformed_data: dict, db: AsyncSession, current_user_id: str):
    """
    Crea una entidad manejando campos que se generan automáticamente
    Especialmente para productos que generan código automáticamente
    """
    model_name = model_class.__tablename__
    
    if model_name == "products" and model_class == Product:
        # Para productos, generar código automáticamente si no se proporciona
        
        if 'code' not in transformed_data or not transformed_data['code']:
            # Generar código automáticamente usando método mejorado
            name = transformed_data.get('name', 'UNNAMED')
            product_type = transformed_data.get('product_type', 'product')
            
            # Determinar prefijo según tipo de producto
            if product_type == 'service':
                prefix = "SRV"
            elif product_type == 'both':
                prefix = "MIX"
            else:  # 'product' o None
                prefix = "PRD"
            
            # Limpiar el nombre para crear una base del código
            clean_name = ''.join(c.upper() for c in name if c.isalnum())[:6]
            if len(clean_name) < 3:
                clean_name = clean_name.ljust(3, 'X')
            
            # Buscar el siguiente número secuencial para este patrón
            base_pattern = f"{prefix}-{clean_name}-"
            
            # Consultar códigos existentes con este patrón
            query = select(Product.code).where(Product.code.like(f"{base_pattern}%"))
            result = await db.execute(query)
            existing_codes = [row[0] for row in result.fetchall()]
            
            # Extraer números secuenciales y encontrar el máximo
            max_number = 0
            for code in existing_codes:
                if code.startswith(base_pattern):
                    try:
                        # Extraer la parte numérica después del patrón base
                        remaining = code[len(base_pattern):]
                        # Dividir por '-' para obtener la parte numérica (antes de cualquier sufijo adicional)
                        parts = remaining.split('-')
                        if parts[0].isdigit():
                            max_number = max(max_number, int(parts[0]))
                    except (ValueError, IndexError):
                        continue
            
            # Generar siguiente número secuencial
            next_number = max_number + 1
            
            # Generar sufijo aleatorio para garantizar unicidad (3 caracteres)
            import random
            import string
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
            
            # Código final: PREFIX-NAMEPART-SEQUENCE-RANDOM
            final_code = f"{prefix}-{clean_name}-{next_number:03d}-{random_suffix}"
            
            # Verificar unicidad (debería ser extremadamente raro que colisione)
            max_attempts = 10
            attempt = 0
            while attempt < max_attempts:
                check_query = select(Product).where(Product.code == final_code)
                check_result = await db.execute(check_query)
                existing = check_result.scalar_one_or_none()
                
                if not existing:
                    transformed_data['code'] = final_code
                    logger.info(f"Generated unique product code: {final_code} for product: {name}")
                    break
                
                # Generar nuevo sufijo aleatorio si hay colisión
                random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
                final_code = f"{prefix}-{clean_name}-{next_number:03d}-{random_suffix}"
                attempt += 1
            
            # Si aún hay colisión después de intentos máximos, usar timestamp
            if attempt >= max_attempts:
                timestamp = str(int(time.time()))[-8:]
                transformed_data['code'] = f"{prefix}-{clean_name}-{timestamp}"
                logger.warning(f"Used timestamp fallback code: {transformed_data['code']}")
        
        # Aplicar valores por defecto para productos
        if 'product_type' not in transformed_data:
            transformed_data['product_type'] = 'product'
        if 'status' not in transformed_data:
            transformed_data['status'] = 'active'  # Product usa 'status', no 'is_active'
        if 'measurement_unit' not in transformed_data:
            transformed_data['measurement_unit'] = 'unit'
        if 'purchase_price' not in transformed_data:
            transformed_data['purchase_price'] = 0.0
        if 'sale_price' not in transformed_data:
            transformed_data['sale_price'] = 0.0
        if 'min_sale_price' not in transformed_data:
            transformed_data['min_sale_price'] = 0.0
        if 'suggested_price' not in transformed_data:
            transformed_data['suggested_price'] = 0.0
        if 'tax_category' not in transformed_data:
            transformed_data['tax_category'] = 'EXEMPT'
        if 'tax_rate' not in transformed_data:
            transformed_data['tax_rate'] = 0.0
        if 'manage_inventory' not in transformed_data:
            transformed_data['manage_inventory'] = False
        if 'current_stock' not in transformed_data:
            transformed_data['current_stock'] = 0.0
        if 'min_stock' not in transformed_data:
            transformed_data['min_stock'] = 0.0
        if 'max_stock' not in transformed_data:
            transformed_data['max_stock'] = 0.0
        if 'reorder_point' not in transformed_data:
            transformed_data['reorder_point'] = 0.0
    
    # Crear la entidad
    new_record = model_class(**transformed_data)
    db.add(new_record)
    return new_record


@router.get(
    "/config",
    summary="Get import configuration",
    description="Get default configuration values and limits for imports"
)
async def get_import_config(
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Get import configuration and limits"""
    return {
        "batch_size": {
            "default": 2000,
            "min": 1,
            "max": 10000,
            "description": "Number of rows to process per batch"
        },
        "preview_rows": {
            "default": 10,
            "min": 5,
            "max": 50,
            "description": "Number of rows to show in preview"
        },
        "supported_formats": ["csv", "xlsx", "xls"],
        "max_file_size_mb": 100,
        "session_timeout_hours": 2
    }


@router.get(
    "/models",
    response_model=List[str],
    summary="Get available models for import",
    description="Returns a list of all models that support generic import"
)
async def get_available_models(
    current_user: User = Depends(get_current_active_user)
) -> List[str]:
    """Get list of available models for import"""
    try:
        return metadata_registry.get_available_models()
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving available models"
        )


@router.get(
    "/models/{model_name}/metadata",
    response_model=ModelMetadata,
    summary="Get model metadata",
    description="Returns metadata for a specific model including field definitions and constraints"
)
async def get_model_metadata(
    model_name: str,
    current_user: User = Depends(get_current_active_user)
) -> ModelMetadata:
    """Get metadata for a specific model"""
    try:
        metadata = metadata_registry.get_model_metadata(model_name)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found or not supported for import"
            )
        return metadata
    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting model metadata for {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving model metadata"
        )


@router.post(
    "/sessions",
    response_model=ImportSessionResponse,
    summary="Create import session and upload file",
    description="Upload a CSV/XLSX file and create a new import session with sample data"
)
async def create_import_session(
    background_tasks: BackgroundTasks,
    model_name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportSessionResponse:
    """Create a new import session with file upload"""
    try:
        # Validate model exists
        metadata = metadata_registry.get_model_metadata(model_name)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found or not supported for import"
            )

        # TODO: Add permission checks based on model and user permissions

        # Create import session
        session = await session_service.create_session(file, model_name, str(current_user.id))
        
        return ImportSessionResponse(
            import_session_token=session.token,
            model=session.model,
            model_display_name=session.model_metadata.display_name,
            file_info=session.file_info,
            detected_columns=session.detected_columns,
            sample_rows=session.sample_rows
        )
        
    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating import session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating import session"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=ImportSessionResponse,
    summary="Get import session details",
    description="Retrieve details of an existing import session"
)
async def get_import_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
) -> ImportSessionResponse:
    """Get import session details"""
    try:
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import session '{session_id}' not found"
            )
        
        # TODO: Add ownership check - ensure user owns this session
        
        return ImportSessionResponse(
            import_session_token=session.token,
            model=session.model,
            model_display_name=session.model_metadata.display_name,
            file_info=session.file_info,
            detected_columns=session.detected_columns,
            sample_rows=session.sample_rows
        )
        
    except ImportSessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting import session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving import session"
        )


@router.delete(
    "/sessions/{session_id}",
    summary="Delete import session",
    description="Delete an import session and clean up associated files"
)
async def delete_import_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Delete import session and clean up files"""
    try:
        # TODO: Implement session deletion
        return {"message": f"Import session '{session_id}' deleted successfully"}
        
    except ImportSessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting import session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting import session"
        )


@router.get(
    "/sessions/{session_id}/batch-info",
    summary="Get batch information",
    description="Get information about batches for a session"
)
async def get_batch_info(
    session_id: str,
    batch_size: int = 2000,
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Get batch information for a session"""
    try:
        # Get session
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import session '{session_id}' not found"
            )
        
        # Calculate total batches
        total_batches = session_service.get_total_batches(session_id, batch_size)
        
        return {
            "total_batches": total_batches,
            "total_rows": session.file_info.total_rows,
            "batch_size": batch_size
        }
        
    except Exception as e:
        logger.error(f"Error getting batch info for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting batch information"
        )


@router.get(
    "/sessions/{session_id}/mapping-suggestions",
    summary="Get mapping suggestions",
    description="Get automatic suggestions for mapping CSV columns to model fields"
)
async def get_mapping_suggestions(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Get automatic mapping suggestions based on column names and model fields"""
    try:
        # Get session
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import session '{session_id}' not found"
            )
        
        # Get column names from detected columns
        column_names = [col.name for col in session.detected_columns]
        
        # Get model fields
        model_fields = session.model_metadata.fields
        
        # Generate automatic suggestions
        suggestions = []
        
        for column in session.detected_columns:
            best_match = None
            best_confidence = 0.0
            
            # Simple fuzzy matching algorithm
            for field in model_fields:
                confidence = calculate_field_match_confidence(column.name, field)
                if confidence > best_confidence and confidence > 0.3:  # Minimum confidence threshold
                    best_match = field.internal_name
                    best_confidence = confidence
            
            suggestions.append({
                "column_name": column.name,
                "suggested_field": best_match,
                "confidence": best_confidence,
                "sample_values": column.sample_values,
                "reason": f"Name similarity: {best_confidence:.2f}" if best_match else "No confident match found"
            })
        
        # Also provide information about available fields
        available_fields = []
        for field in model_fields:
            available_fields.append({
                "internal_name": field.internal_name,
                "display_label": field.display_label,
                "field_type": field.field_type,
                "is_required": field.is_required,
                "description": getattr(field, 'description', None)
            })
        
        return {
            "session_id": session_id,
            "model": session.model,
            "suggestions": suggestions,
            "available_fields": available_fields,
            "auto_mappable_count": sum(1 for s in suggestions if s["suggested_field"])
        }
        
    except ImportSessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting mapping suggestions for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting mapping suggestions"
        )


def calculate_field_match_confidence(column_name: str, field_meta) -> float:
    """Calculate confidence score for matching a column name to a field"""
    column_lower = column_name.lower().strip()
    field_name_lower = field_meta.internal_name.lower()
    field_label_lower = field_meta.display_label.lower()
    
    # Exact match
    if column_lower == field_name_lower or column_lower == field_label_lower:
        return 1.0
    
    # Contains match
    if column_lower in field_name_lower or field_name_lower in column_lower:
        return 0.8
    
    if column_lower in field_label_lower or field_label_lower in column_lower:
        return 0.7
    
    # Common field name patterns
    common_patterns = {
        'id': ['id', 'identifier', 'codigo', 'code'],
        'name': ['name', 'nombre', 'description', 'descripcion'],
        'email': ['email', 'correo', 'mail'],
        'phone': ['phone', 'telefono', 'tel'],
        'date': ['date', 'fecha'],
        'amount': ['amount', 'monto', 'valor', 'value', 'precio', 'price'],
        'quantity': ['quantity', 'cantidad', 'qty'],
        'address': ['address', 'direccion', 'domicilio']
    }
    
    field_keywords = field_name_lower.split('_') + field_label_lower.split()
    column_keywords = column_lower.replace('_', ' ').split()
    
    for pattern_key, pattern_values in common_patterns.items():
        if any(keyword in pattern_values for keyword in field_keywords):
            if any(keyword in pattern_values for keyword in column_keywords):
                return 0.6
    
    # Partial word match
    for field_word in field_keywords:
        for col_word in column_keywords:
            if field_word and col_word and (
                field_word.startswith(col_word) or col_word.startswith(field_word)
            ):
                return 0.4
    
    return 0.0
@router.post(
    "/sessions/{session_id}/mapping",
    summary="Set column mappings",
    description="Configure how CSV columns map to model fields with automatic suggestions"
)
async def set_column_mappings(
    session_id: str,
    mappings: List[ColumnMapping],
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Set column mappings for import session"""
    try:
        # Get session
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import session '{session_id}' not found"
            )
        
        # TODO: Add ownership check - ensure user owns this session
          # Validate mappings against model metadata
        model_metadata = session.model_metadata
        valid_fields = {field.internal_name for field in model_metadata.fields}
        
        validation_errors = []
        for mapping in mappings:
            if mapping.field_name and mapping.field_name not in valid_fields:
                validation_errors.append(f"Field '{mapping.field_name}' not found in model '{session.model}'")
        
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid field mappings: {', '.join(validation_errors)}"
            )
        
        # Store mappings in session
        mapping_saved = await session_service.update_session_mappings(session_id, mappings)
        if not mapping_saved:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save column mappings to session"
            )
        
        return {
            "message": "Column mappings configured and saved successfully",
            "session_id": session_id,
            "mappings_count": len(mappings),
            "mapped_fields": [m.field_name for m in mappings if m.field_name],
            "available_fields": [field.internal_name for field in model_metadata.fields]
        }
        
    except ImportSessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error setting mappings for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting column mappings"
        )


@router.post(
    "/sessions/{session_id}/validate-full",
    response_model=ImportPreviewResponse,
    summary="Validate entire file",
    description="Validate ALL rows in the file to show complete statistics before import"
)
async def validate_full_file(
    session_id: str,
    preview_request: ImportPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportPreviewResponse:
    """Validate entire file data with complete statistics"""
    try:
        # Get session
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import session '{session_id}' not found"
            )
        
        # Get column mappings
        mappings = preview_request.column_mappings
        if not mappings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No column mappings provided. Please set mappings first."
            )
        
        # Create mapping dictionary for easy lookup
        mapping_dict = {m.column_name: m.field_name for m in mappings if m.field_name}
        
        # Read ALL data from the file
        logger.info(f"Validating entire file for session {session_id}")
        all_data = await session_service.read_full_file_data(session_id)
        total_rows = len(all_data)
        
        # Initialize validation statistics
        validation_summary = ValidationSummary(
            total_rows_analyzed=total_rows,
            valid_rows=0,
            rows_with_errors=0,
            rows_with_warnings=0,
            error_breakdown={}
        )
        
        # We'll show only first 10 rows in preview_data but validate ALL rows
        preview_rows = []
        error_counts = {}
        
        # Process all rows for validation
        for i, row_data in enumerate(all_data):
            row_number = i + 1
            
            # Transform row according to mappings
            transformed_data = {}
            errors = []
            warnings = []
            
            for column_name, field_name in mapping_dict.items():
                if column_name in row_data:
                    raw_value = row_data[column_name]
                    
                    try:
                        # Find field metadata
                        field_meta = next(
                            (f for f in session.model_metadata.fields if f.internal_name == field_name),
                            None
                        )
                        
                        if not field_meta:
                            errors.append(ValidationError(
                                field_name=field_name,
                                error_type="field_not_found",
                                message=f"Field '{field_name}' not found in model metadata",
                                current_value=str(raw_value) if raw_value is not None else None
                            ))
                            continue
                        
                        # Validate and transform the value
                        validated_value = await validate_field_value(
                            raw_value, field_meta, db
                        )
                        transformed_data[field_name] = validated_value
                        
                    except Exception as e:
                        logger.error(f"Error transforming field {field_name} for row {row_number}: {e}")
                        errors.append(ValidationError(
                            field_name=field_name,
                            error_type="transformation_error",
                            message=f"Error transforming value: {str(e)}",
                            current_value=str(raw_value) if raw_value is not None else None
                        ))
            
            # Count errors for statistics
            for error in errors:
                error_type = f"{error.field_name}:{error.error_type}"
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            # Update validation summary
            if errors:
                validation_summary.rows_with_errors += 1
            elif warnings:
                validation_summary.rows_with_warnings += 1
            else:
                validation_summary.valid_rows += 1
            
            # Only add first 10 rows to preview_data for display
            if i < 10:
                validation_status = 'error' if errors else ('warning' if warnings else 'valid')
                preview_rows.append(PreviewRowData(
                    row_number=row_number,
                    original_data=row_data,
                    transformed_data=transformed_data,
                    validation_status=validation_status,
                    errors=errors,
                    warnings=warnings
                ))
        
        # Set error breakdown
        validation_summary.error_breakdown = error_counts
        
        # Determine if can proceed
        can_proceed = validation_summary.rows_with_errors == 0
        can_skip_errors = validation_summary.rows_with_errors > 0
        
        # Create blocking issues list
        blocking_issues = []
        if validation_summary.rows_with_errors > 0:
            blocking_issues.append(f"{validation_summary.rows_with_errors} rows have validation errors (can be skipped)")
        
        logger.info(f"Full validation completed for session {session_id}: {validation_summary.valid_rows} valid, {validation_summary.rows_with_errors} errors, {validation_summary.rows_with_warnings} warnings")
        
        return ImportPreviewResponse(
            import_session_token=session_id,
            model=session.model,
            total_rows=total_rows,
            preview_data=preview_rows,
            validation_summary=validation_summary,
            can_proceed=can_proceed,
            blocking_issues=blocking_issues,
            can_skip_errors=can_skip_errors,
            skip_errors_available=can_skip_errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating full file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating file: {str(e)}"
        )


@router.post(
    "/sessions/{session_id}/preview",
    response_model=ImportPreviewResponse,
    summary="Preview import data",
    description="Validate and preview how data will be imported with current mappings"
)
async def preview_import(
    session_id: str,
    preview_request: ImportPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ImportPreviewResponse:
    """Preview import data with validation"""
    try:
        # Get session
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import session '{session_id}' not found"
            )
        
        # TODO: Add ownership check - ensure user owns this session
        
        # Get column mappings
        mappings = preview_request.column_mappings
        if not mappings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No column mappings provided. Please set mappings first."
            )
        
        # Create mapping dictionary for easy lookup
        mapping_dict = {m.column_name: m.field_name for m in mappings if m.field_name}
        
        # Determine if this is a batch preview request
        batch_size = preview_request.batch_size if hasattr(preview_request, 'batch_size') and preview_request.batch_size is not None else 1000
        batch_number = preview_request.batch_number if hasattr(preview_request, 'batch_number') and preview_request.batch_number is not None else None
        
        # Get data for preview based on batch parameters
        if batch_number is not None:
            # Batch preview - get specific batch data
            try:
                batch_data = await session_service.read_file_batch(
                    session_id, 
                    batch_size=batch_size, 
                    batch_number=batch_number
                )
                sample_data = batch_data
                sample_size = len(batch_data)
                
                # Calculate batch info
                total_batches = session_service.get_total_batches(session_id, batch_size)
                batch_info = {
                    "current_batch": batch_number,
                    "total_batches": total_batches,
                    "batch_size": batch_size,
                    "total_rows": session.file_info.total_rows,
                    "current_batch_rows": len(batch_data)
                }
            except Exception as e:
                logger.error(f"Error reading batch {batch_number}: {e}")
                # Fallback to sample data
                sample_size = min(getattr(preview_request, 'preview_rows', 10), len(session.sample_rows))
                sample_data = session.sample_rows[:sample_size]
                batch_info = None
        else:
            # Regular preview - use sample data
            preview_rows_count = getattr(preview_request, 'preview_rows', 10)
            sample_size = min(preview_rows_count, len(session.sample_rows))
            sample_data = session.sample_rows[:sample_size]
            batch_info = None        # Validate and transform sample data
        preview_rows = []
        validation_summary = ValidationSummary(
            total_rows_analyzed=sample_size,
            valid_rows=0,
            rows_with_errors=0,
            rows_with_warnings=0,
            error_breakdown={}
        )
        
        for i, row_data in enumerate(sample_data):
            row_number = i + 1            # Transform row according to mappings
            transformed_data = {}
            errors = []
            warnings = []
            
            for column_name, field_name in mapping_dict.items():
                if column_name in row_data:
                    raw_value = row_data[column_name]
                    
                    # Debug logging for name field
                    if field_name == "name":
                        logger.debug(f"Row {row_number}: Processing field '{field_name}' from column '{column_name}' - Raw value: {repr(raw_value)}")
                    
                    try:
                        # Find field metadata
                        field_meta = next(
                            (f for f in session.model_metadata.fields if f.internal_name == field_name),
                            None
                        )
                        
                        if field_meta:
                            # Validate and transform value
                            validated_value = await validate_field_value(
                                raw_value, field_meta, db
                            )
                            transformed_data[field_name] = validated_value
                            
                            # Debug logging for name field
                            if field_name == "name":
                                logger.debug(f"Row {row_number}: Field '{field_name}' validated successfully - Result: {repr(validated_value)}")
                        else:
                            errors.append(ValidationError(
                                field_name=field_name,
                                error_type="field_not_found",
                                message=f"Field '{field_name}' not found in model metadata",
                                current_value=str(raw_value) if raw_value is not None else None
                            ))
                    
                    except Exception as e:
                        # Debug logging for name field
                        if field_name == "name":
                            logger.debug(f"Row {row_number}: Field '{field_name}' validation failed - Error: {str(e)}")
                        
                        # Still try to add a reasonable value to transformed_data for display purposes
                        if raw_value is not None:
                            try:
                                # For display, convert NaN to None
                                if isinstance(raw_value, float):
                                    import math
                                    if math.isnan(raw_value):
                                        display_value = None
                                    else:
                                        display_value = raw_value
                                else:
                                    display_value = raw_value
                                transformed_data[field_name] = display_value
                                
                                # Debug logging for name field
                                if field_name == "name":
                                    logger.debug(f"Row {row_number}: Added display value for '{field_name}': {repr(display_value)}")
                            except:
                                transformed_data[field_name] = None
                        
                        errors.append(ValidationError(
                            field_name=field_name,
                            error_type="validation_error",
                            message=str(e),
                            current_value=str(raw_value) if raw_value is not None else None
                        ))
                        
                        # Update error breakdown
                        error_type = type(e).__name__
                        validation_summary.error_breakdown[error_type] = (
                            validation_summary.error_breakdown.get(error_type, 0) + 1
                        )            # Check required fields - BUT only if they weren't already processed and validated
            required_fields = [f.internal_name for f in session.model_metadata.fields if f.is_required]
            
            # Get list of fields that were already processed (either successfully or with errors)
            processed_fields = set()
            for column_name, field_name in mapping_dict.items():
                if column_name in row_data:
                    processed_fields.add(field_name)
            
            # Apply default values for fields that weren't mapped but have default values
            for field_meta in session.model_metadata.fields:
                field_name = field_meta.internal_name
                if (field_name not in processed_fields and 
                    field_name not in transformed_data and 
                    hasattr(field_meta, 'default_value') and 
                    field_meta.default_value is not None):
                    
                    transformed_data[field_name] = field_meta.default_value
                    if field_name in ["third_party_type", "is_active"]:
                        logger.debug(f"Row {row_number}: Applied default value for unmapped field '{field_name}': {field_meta.default_value}")
            
            for req_field in required_fields:
                # Skip validation if this field was already processed in the mapping loop above
                if req_field in processed_fields:
                    # Debug logging
                    if req_field == "name":
                        field_value = transformed_data.get(req_field)
                        logger.debug(f"Row {row_number}: Skipping secondary validation for '{req_field}' (already processed) - Value: {repr(field_value)}")
                    continue
                
                # Only check unmapped required fields
                field_value = transformed_data.get(req_field)
                is_missing_or_empty = (
                    req_field not in transformed_data or 
                    field_value is None or 
                    (isinstance(field_value, str) and field_value.strip() == "")
                )
                
                # Debug logging
                if req_field == "name":
                    logger.debug(f"Row {row_number}: Checking unmapped required field '{req_field}' - Value: {repr(field_value)}, Missing/Empty: {is_missing_or_empty}")
                
                if is_missing_or_empty:
                    errors.append(ValidationError(
                        field_name=req_field,
                        error_type="required_field_missing",
                        message=f"Required field '{req_field}' is missing or empty (not mapped)",
                        current_value=repr(field_value)
                    ))
            
            # Check uniqueness constraints for business key fields
            if session.model_metadata.business_key_fields and transformed_data:
                business_key_values = {}
                for key_field in session.model_metadata.business_key_fields:
                    if key_field in transformed_data and transformed_data[key_field] is not None:
                        business_key_values[key_field] = transformed_data[key_field]
                
                if business_key_values:
                    # Get model class for database query
                    model_class = None
                    if session.model == "third_party":
                        from app.models.third_party import ThirdParty
                        model_class = ThirdParty
                    elif session.model == "account":
                        from app.models.account import Account
                        model_class = Account
                    elif session.model == "product":
                        from app.models.product import Product
                        model_class = Product
                    
                    if model_class:
                        try:
                            # Check if record already exists (case sensitive)
                            query = select(model_class)
                            for key, value in business_key_values.items():
                                query = query.where(getattr(model_class, key) == value)
                            existing = await db.execute(query)
                            if existing.scalar_one_or_none():
                                # Get field metadata to create proper error
                                key_field = list(business_key_values.keys())[0]  # Usually just one key field
                                key_value = business_key_values[key_field]
                                errors.append(ValidationError(
                                    field_name=key_field,
                                    error_type="duplicate_value",
                                    message=f"Value '{key_value}' already exists (case sensitive)",
                                    current_value=str(key_value)
                                ))
                        except Exception as e:
                            logger.warning(f"Row {row_number}: Error checking uniqueness: {e}")
            
            # Determine validation status
            if errors:
                validation_status = "error"
                validation_summary.rows_with_errors += 1
            elif warnings:
                validation_status = "warning"
                validation_summary.rows_with_warnings += 1
            else:
                validation_status = "valid"
                validation_summary.valid_rows += 1
            
            preview_rows.append(PreviewRowData(
                row_number=row_number,
                original_data=row_data,
                transformed_data=transformed_data,
                validation_status=validation_status,
                errors=errors,
                warnings=warnings
            ))
          # Determine if can proceed
        can_proceed = validation_summary.rows_with_errors == 0
        blocking_issues = []
        
        # Check if errors can be skipped (only validation errors, not structural issues)
        can_skip_errors = True
        skip_errors_available = True
        
        if validation_summary.rows_with_errors > 0:
            # Analyze types of errors to see if they can be skipped
            skippable_error_types = {"duplicate_value", "validation_error", "invalid_choice"}
            non_skippable_found = False
            
            for row in preview_rows:
                if row.errors:
                    for error in row.errors:
                        if error.error_type not in skippable_error_types:
                            non_skippable_found = True
                            break
                if non_skippable_found:
                    break
            
            if non_skippable_found:
                can_skip_errors = False
                blocking_issues.append(f"{validation_summary.rows_with_errors} rows have validation errors")
            else:
                blocking_issues.append(f"{validation_summary.rows_with_errors} rows have validation errors (can be skipped)")
          # Check if essential fields are mapped
        essential_fields = [f.internal_name for f in session.model_metadata.fields if f.is_required]
        mapped_essential = [f for f in essential_fields if f in mapping_dict.values()]
        missing_essential = [f for f in essential_fields if f not in mapped_essential]
        
        if missing_essential:
            blocking_issues.append(f"Required fields not mapped: {', '.join(missing_essential)}")
            can_proceed = False
            # Missing required fields cannot be skipped
            can_skip_errors = False
        
        return ImportPreviewResponse(
            import_session_token=session_id,
            model=session.model,
            total_rows=session.file_info.total_rows,  # Use actual file total, not sample size
            preview_data=preview_rows,
            validation_summary=validation_summary,
            can_proceed=can_proceed,
            blocking_issues=blocking_issues,
            can_skip_errors=can_skip_errors,
            skip_errors_available=skip_errors_available,
            batch_info=batch_info
        )
        
    except ImportSessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error previewing import for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error previewing import data"
        )


async def validate_field_value(raw_value: Any, field_meta, db: AsyncSession):
    """Validate and transform a field value according to its metadata"""
    # Debug logging for name field
    if field_meta.internal_name == "name":
        logger.debug(f"Validating field '{field_meta.internal_name}' - Raw value: {repr(raw_value)} (type: {type(raw_value)})")
    
    # Handle None and empty values
    if raw_value is None or raw_value == "" or (isinstance(raw_value, str) and raw_value.strip() == ""):
        if field_meta.is_required:
            if field_meta.internal_name == "name":
                logger.debug(f"Field '{field_meta.internal_name}' is required but empty - raising error")
            raise ValueError(f"Required field cannot be empty")
        
        # If field is not required but has a default value, use it
        if hasattr(field_meta, 'default_value') and field_meta.default_value is not None:
            if field_meta.internal_name in ["third_party_type"]:
                logger.debug(f"Using default value for '{field_meta.internal_name}': {field_meta.default_value}")
            return field_meta.default_value
        
        return None
      # Handle pandas NaN values that might have slipped through
    try:
        import math
        if isinstance(raw_value, float) and math.isnan(raw_value):
            if field_meta.is_required:
                raise ValueError(f"Required field cannot be empty")
            return None
    except (TypeError, ValueError):
        # Not a valid number, continue with normal processing
        pass
    
    # Convert to string for processing
    str_value = str(raw_value).strip()
    
    # Special handling for enum fields with choices
    if field_meta.choices:
        # Extract valid values from choices
        valid_values = [choice["value"] for choice in field_meta.choices]
        
        # Check if the value is already a valid enum value
        if str_value in valid_values:
            return str_value
        
        # Try to map from enum representation like "ThirdPartyType.CUSTOMER" to "customer"
        if "." in str_value:
            # Extract the last part after the dot (e.g., "CUSTOMER" from "ThirdPartyType.CUSTOMER")
            enum_name = str_value.split(".")[-1]
            
            # Try to find a matching enum value
            for choice in field_meta.choices:
                if choice["value"].upper() == enum_name.upper():
                    return choice["value"]
                if choice["label"].upper() == enum_name.upper():
                    return choice["value"]
            
            # If no direct match, try some common mappings
            enum_mappings = {
                "CUSTOMER": "customer",
                "SUPPLIER": "supplier", 
                "EMPLOYEE": "employee",
                "SHAREHOLDER": "shareholder",
                "BANK": "bank",
                "GOVERNMENT": "government",
                "OTHER": "other",
                "RUT": "rut",
                "NIT": "nit",
                "CUIT": "cuit",
                "RFC": "rfc",
                "PASSPORT": "passport",
                "DNI": "dni"
            }
            
            if enum_name.upper() in enum_mappings:
                mapped_value = enum_mappings[enum_name.upper()]
                if mapped_value in valid_values:
                    return mapped_value
        
        # If still no match found, try case-insensitive comparison
        for choice in field_meta.choices:
            if choice["value"].lower() == str_value.lower():
                return choice["value"]
            if choice["label"].lower() == str_value.lower():
                return choice["value"]
        
        # If no match found, raise error with valid options
        valid_options = ", ".join([f"{choice['value']} ({choice['label']})" for choice in field_meta.choices])
        raise ValueError(f"Invalid choice '{str_value}'. Valid options: {valid_options}")
      # Validate based on field type
    if field_meta.field_type == "string":
        if field_meta.max_length and len(str_value) > field_meta.max_length:
            raise ValueError(f"Text too long (max {field_meta.max_length} characters)")
        return str_value
    
    elif field_meta.field_type == "integer" or field_meta.field_type == "decimal":
        try:
            # Handle "nan" values
            if str_value.lower() == "nan":
                if field_meta.is_required:
                    raise ValueError("Required field cannot be empty or NaN")
                return None
                
            num_value = float(str_value)
            if field_meta.min_value is not None and num_value < field_meta.min_value:
                raise ValueError(f"Value too small (min {field_meta.min_value})")
            if field_meta.max_value is not None and num_value > field_meta.max_value:
                raise ValueError(f"Value too large (max {field_meta.max_value})")
            return num_value
        except ValueError:
            raise ValueError(f"Invalid number format: {str_value}")
    
    elif field_meta.field_type == "date":
        # Simple date parsing - in production you'd use more sophisticated parsing
        import datetime
        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    return datetime.datetime.strptime(str_value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Could not parse date: {str_value}")
        except Exception:
            raise ValueError(f"Invalid date format: {str_value}")
    
    elif field_meta.field_type == "boolean":
        lower_val = str_value.lower()
        if lower_val in ["true", "1", "yes", "si", "sí"]:
            return True
        elif lower_val in ["false", "0", "no"]:
            return False
        else:
            raise ValueError(f"Invalid boolean value: {str_value}")
    
    elif field_meta.field_type == "email":
        # Handle "nan" values
        if str_value.lower() == "nan":
            if field_meta.is_required:
                raise ValueError("Required field cannot be empty or NaN")
            return None
        return str_value
    
    elif field_meta.field_type == "phone":
        # Handle "nan" values  
        if str_value.lower() == "nan":
            if field_meta.is_required:
                raise ValueError("Required field cannot be empty or NaN")
            return None
        return str_value
    
    elif field_meta.field_type == "many_to_one":
        # For many-to-one relationships, we'd need to look up the related record
        # This is a simplified version - in production you'd query the database
        if not str_value:
            return None
        # TODO: Implement actual database lookup
        return str_value
    
    else:
        # Default: return as string, but handle "nan" values
        if str_value.lower() == "nan":
            if field_meta.is_required:
                raise ValueError("Required field cannot be empty or NaN")
            return None
        return str_value


@router.post(
    "/sessions/{session_id}/execute",
    summary="Execute import",
    description="Execute the actual import with validation and error handling. If no mappings are provided, uses the mappings saved in the session from /mapping endpoint."
)
async def execute_import(
    session_id: str,
    mappings: Optional[List[ColumnMapping]] = None,  # Hacer mappings opcional
    import_policy: str = "create_only",  # create_only, update_only, upsert
    skip_errors: bool = False,  # Nueva opción para omitir filas con errores
    batch_size: int = 2000,  # Tamaño del lote para procesar
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Execute the import operation"""
    try:
        # Get session
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import session '{session_id}' not found"
            )
        
        # TODO: Add ownership check - ensure user owns this session
        
        # Validate import policy
        valid_policies = ["create_only", "update_only", "upsert"]
        if import_policy not in valid_policies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid import policy. Must be one of: {', '.join(valid_policies)}"
            )
        
        # Validate batch_size
        if batch_size < 1 or batch_size > 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size must be between 1 and 10000"
            )
        
        # Validate mappings - use saved mappings if none provided
        if not mappings:
            # Try to get mappings from session
            saved_mappings = await session_service.get_session_mappings(session_id)
            if saved_mappings:
                mappings = saved_mappings
                logger.info(f"Using saved column mappings from session: {len(mappings)} mappings")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No column mappings provided and no saved mappings found in session. Please configure column mappings first using /sessions/{session_id}/mapping endpoint."
                )
        else:
            logger.info(f"Using provided column mappings: {len(mappings)} mappings")
        
        if not mappings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No column mappings available"
            )
          # Create mapping dictionary
        mapping_dict = {m.column_name: m.field_name for m in mappings if m.field_name}        # Check required fields are mapped - but allow auto-generated fields
        required_fields = [f.internal_name for f in session.model_metadata.fields if f.is_required]
        mapped_fields = list(mapping_dict.values())
        auto_generated_fields = ["code", "document_number", "document_type", "third_party_type"]  # Fields that can be auto-generated
        missing_required = [f for f in required_fields if f not in mapped_fields and f not in auto_generated_fields]
        
        if missing_required and not skip_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Required fields not mapped and cannot be auto-generated: {', '.join(missing_required)}"
            )
        
        # Implementación real de importación por lotes
        total_rows = session.file_info.total_rows  # Total real de filas en el archivo
        total_batches = session_service.get_total_batches(session_id, batch_size)
        successful_rows = 0
        error_rows = 0
        skipped_rows = 0
        errors = []
        skipped_details = []
        
        logger.info(f"Starting batch import: {total_rows} total rows, {total_batches} batches of {batch_size} rows each")
        
        # Obtener el modelo SQLAlchemy correspondiente
        model_class = None
        if session.model == "third_party":
            from app.models.third_party import ThirdParty
            model_class = ThirdParty
        elif session.model == "account":
            from app.models.account import Account
            model_class = Account
        elif session.model == "product":
            from app.models.product import Product
            model_class = Product        # Agregar más modelos según se necesiten
        
        if not model_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model implementation not found for: {session.model}"
            )
        
        # Improve mappings by attempting automatic mapping for unmapped columns
        improved_mapping_dict = mapping_dict.copy()
        unmapped_columns = [m.column_name for m in mappings if not m.field_name]
        
        if unmapped_columns:
            logger.info(f"Attempting automatic mapping for unmapped columns: {unmapped_columns}")
            
            for column_name in unmapped_columns:
                # Try direct name matching first
                for field_meta in session.model_metadata.fields:
                    if field_meta.internal_name.lower() == column_name.lower():
                        improved_mapping_dict[column_name] = field_meta.internal_name
                        logger.info(f"Auto-mapped column '{column_name}' to field '{field_meta.internal_name}' (exact match)")
                        break
                
                # If no exact match, try partial matching for common fields
                if column_name not in improved_mapping_dict:
                    column_lower = column_name.lower()
                    for field_meta in session.model_metadata.fields:
                        field_lower = field_meta.internal_name.lower()
                        
                        # Check for common patterns
                        if (
                            (column_lower in field_lower or field_lower in column_lower) and
                            len(field_lower) > 2  # Avoid matching very short fields
                        ):
                            improved_mapping_dict[column_name] = field_meta.internal_name
                            logger.info(f"Auto-mapped column '{column_name}' to field '{field_meta.internal_name}' (partial match)")
                            break
          # Use the improved mapping dictionary
        mapping_dict = improved_mapping_dict
        logger.info(f"Final mapping dictionary: {mapping_dict}")
        
        # Procesar archivo por lotes
        current_row_number = 0
        
        for batch_number in range(total_batches):
            logger.info(f"Processing batch {batch_number + 1}/{total_batches}")
            
            try:
                # Leer el lote actual del archivo
                batch_data = await session_service.read_file_batch(session_id, batch_size, batch_number)
                
                if not batch_data:
                    logger.info(f"Batch {batch_number + 1} is empty, skipping")
                    continue
                
                logger.info(f"Batch {batch_number + 1}: Processing {len(batch_data)} rows")
                
                # Procesar cada fila del lote
                for i, row_data in enumerate(batch_data):
                    current_row_number += 1
                    savepoint = None  # Initialize savepoint variable
                    
                    if current_row_number % 100 == 0:  # Log progress every 100 rows
                        logger.info(f"Processing row {current_row_number}/{total_rows}")
                    
                    try:
                        # Si skip_errors está habilitado, usar transacciones individuales
                        if skip_errors:
                            # Usar savepoint para aislar cada fila
                            savepoint = await db.begin_nested()
                            logger.debug(f"Row {current_row_number}: Created savepoint for skip_errors mode")
                        else:
                            logger.debug(f"Row {current_row_number}: Processing in normal mode (no savepoint)")
                            
                        # Transformar fila según mapeos - manejar múltiples columnas mapeadas al mismo campo
                        transformed_data = {}
                        
                        logger.debug(f"Row {current_row_number}: Mapping dict: {mapping_dict}")
                        
                        # Group mappings by field_name to handle multiple columns mapping to same field
                        field_mappings = {}
                        for column_name, field_name in mapping_dict.items():
                            if field_name not in field_mappings:
                                field_mappings[field_name] = []
                            field_mappings[field_name].append(column_name)
                        
                        logger.debug(f"Row {current_row_number}: Field mappings: {field_mappings}")
                        
                        # Process each target field
                        for field_name, column_names in field_mappings.items():
                            field_meta = next(
                                (f for f in session.model_metadata.fields if f.internal_name == field_name),
                                None
                            )
                            
                            if field_meta:
                                # Try each column until we find a valid non-null value
                                final_value = None
                                
                                for column_name in column_names:
                                    if column_name in row_data:
                                        raw_value = row_data[column_name]
                                        
                                        # Skip null/empty/nan values unless this is the only option
                                        if raw_value is None or raw_value == "" or str(raw_value).lower() == "nan":
                                            continue
                                        
                                        try:
                                            validated_value = await validate_field_value(raw_value, field_meta, db)
                                            if validated_value is not None:
                                                final_value = validated_value
                                                break  # Use the first valid value found
                                        except Exception as e:
                                            # Log validation error but continue trying other columns
                                            logger.warning(f"Validation failed for {column_name} -> {field_name}: {e}")
                                            continue
                                
                                # If no valid value found from preferred columns, try fallback with null/empty handling
                                if final_value is None:
                                    for column_name in column_names:
                                        if column_name in row_data:
                                            raw_value = row_data[column_name]
                                            try:
                                                validated_value = await validate_field_value(raw_value, field_meta, db)
                                                final_value = validated_value
                                                break
                                            except Exception:
                                                continue
                                
                                # Set the final value for this field
                                if final_value is not None:
                                    transformed_data[field_name] = final_value
                        
                        # Apply default values for missing fields before checking required fields
                        for field_meta in session.model_metadata.fields:
                            field_name = field_meta.internal_name
                            if field_name not in transformed_data or transformed_data[field_name] is None:
                                # Check if field has a default value
                                if hasattr(field_meta, 'default_value') and field_meta.default_value is not None:
                                    # Apply proper type conversion for default values
                                    default_value = field_meta.default_value
                                    
                                    # Convert string boolean defaults to actual booleans
                                    if field_meta.field_type == "boolean" and isinstance(default_value, str):
                                        if default_value.lower() in ["true", "1", "yes", "si", "sí"]:
                                            default_value = True
                                        elif default_value.lower() in ["false", "0", "no"]:
                                            default_value = False
                                        else:
                                            logger.warning(f"Invalid boolean default value '{default_value}' for field '{field_name}', using False")
                                            default_value = False
                                    
                                    transformed_data[field_name] = default_value
                                    logger.debug(f"Row {current_row_number}: Applied default value for '{field_name}': {default_value} (type: {type(default_value)})")
                                
                                # Special handling for auto-generated fields
                                elif field_name == "code" and session.model == "third_party":
                                    # Generate a unique code for third parties if not provided
                                    if "name" in transformed_data and transformed_data["name"]:
                                        # Generate code from name (first 3 letters + row number + timestamp for uniqueness)
                                        name_part = ''.join(c.upper() for c in transformed_data["name"] if c.isalpha())[:3]
                                        if len(name_part) < 3:
                                            name_part = name_part.ljust(3, 'X')  # Pad with X if name is too short
                                        timestamp_suffix = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
                                        generated_code = f"{name_part}{current_row_number:03d}{timestamp_suffix}"
                                        
                                        # Ensure the code doesn't exceed max length (if there's a limit)
                                        if len(generated_code) > 20:  # Assuming max 20 chars for code
                                            generated_code = generated_code[:20]
                                        
                                        transformed_data[field_name] = generated_code
                                        logger.info(f"Row {current_row_number}: Generated unique code '{generated_code}' from name '{transformed_data['name']}'")
                                    else:
                                        # Generate generic code if no name available
                                        timestamp_suffix = str(int(time.time()))[-4:]
                                        generated_code = f"TP{current_row_number:04d}{timestamp_suffix}"
                                        transformed_data[field_name] = generated_code
                                        logger.info(f"Row {current_row_number}: Generated generic code '{generated_code}'")
                                
                                # Auto-generate document_number if not provided
                                elif field_name == "document_number" and session.model == "third_party":
                                    if "name" in transformed_data and transformed_data["name"]:
                                        # Generate a document number from name hash
                                        name_hash = hashlib.md5(transformed_data["name"].encode()).hexdigest()[:8]
                                        generated_doc = f"DOC{name_hash.upper()}"
                                        transformed_data[field_name] = generated_doc
                                        logger.info(f"Row {current_row_number}: Generated document number '{generated_doc}' from name hash")
                                    else:
                                        generated_doc = f"DOC{current_row_number:06d}"
                                        transformed_data[field_name] = generated_doc
                                        logger.info(f"Row {current_row_number}: Generated generic document number '{generated_doc}'")
                                
                                # Special defaults for common third_party fields
                                elif field_name == "document_type" and session.model == "third_party":
                                    transformed_data[field_name] = "other"
                                    logger.debug(f"Row {current_row_number}: Applied default value for '{field_name}': other")
                                
                                elif field_name == "is_active" and session.model == "third_party":
                                    transformed_data[field_name] = True
                                    logger.debug(f"Row {current_row_number}: Applied default value for '{field_name}': True")
                                
                                elif field_name == "is_tax_withholding_agent" and session.model == "third_party":
                                    transformed_data[field_name] = False
                                    logger.debug(f"Row {current_row_number}: Applied default value for '{field_name}': False")
                                
                                elif field_name == "third_party_type" and session.model == "third_party":
                                    transformed_data[field_name] = "customer"  # Default to customer (lowercase as in enum)
                                    logger.debug(f"Row {current_row_number}: Applied default value for '{field_name}': customer")
                        
                        logger.debug(f"Row {current_row_number}: Transformed data after defaults: {transformed_data}")
                        
                        # Verificar campos requeridos después de aplicar defaults
                        required_fields = [f.internal_name for f in session.model_metadata.fields if f.is_required]
                        missing_required = []
                        
                        for req_field in required_fields:
                            field_value = transformed_data.get(req_field)
                            is_missing_or_empty = (
                                req_field not in transformed_data or 
                                field_value is None or 
                                (isinstance(field_value, str) and field_value.strip() == "")
                            )
                            
                            if is_missing_or_empty:
                                missing_required.append(req_field)
                                logger.warning(f"Row {current_row_number}: Required field '{req_field}' is missing or empty. Value: {repr(field_value)}")
                        
                        if missing_required:
                            if skip_errors:
                                if savepoint:
                                    await savepoint.rollback()
                                skipped_rows += 1
                                skip_reason = f"Row {current_row_number}: Missing required fields: {', '.join(missing_required)}"
                                skipped_details.append(skip_reason)
                                logger.warning(f"Skipping row {current_row_number} due to missing required fields: {missing_required}")
                                continue
                            else:
                                raise Exception(f"Missing required fields: {', '.join(missing_required)}")
                        
                        # Crear/actualizar registro en la base de datos
                        if transformed_data:
                            if import_policy == "create_only":
                                # Solo crear - verificar que no exista
                                business_key_values = {}
                                for key_field in session.model_metadata.business_key_fields:
                                    if key_field in transformed_data:
                                        business_key_values[key_field] = transformed_data[key_field]
                                
                                if business_key_values:
                                    # Verificar si ya existe
                                    query = select(model_class)
                                    for key, value in business_key_values.items():
                                        query = query.where(getattr(model_class, key) == value)
                                    existing = await db.execute(query)
                                    if existing.scalar_one_or_none():
                                        if skip_errors:
                                            if savepoint:
                                                await savepoint.rollback()
                                            skipped_rows += 1
                                            # Create more specific error message for uniqueness violation
                                            key_field = list(business_key_values.keys())[0]  # Usually just one key field
                                            key_value = business_key_values[key_field]
                                            skip_reason = f"Row {current_row_number}: {key_field}: Value '{key_value}' already exists (case sensitive)"
                                            skipped_details.append(skip_reason)
                                            logger.info(f"Skipping row {current_row_number} due to duplicate: {skip_reason}")
                                            continue
                                        else:
                                            error_rows += 1
                                            key_field = list(business_key_values.keys())[0]
                                            key_value = business_key_values[key_field]
                                            errors.append(f"Row {current_row_number}: Value '{key_value}' already exists for field '{key_field}' (case sensitive)")
                                            continue
                                
                                # Crear nuevo registro
                                new_record = await _create_entity_with_auto_fields(model_class, transformed_data, db, str(current_user.id))
                                # No agregamos a db aquí porque _create_entity_with_auto_fields ya lo hace
                                
                            elif import_policy == "upsert":
                                # Crear o actualizar
                                business_key_values = {}
                                for key_field in session.model_metadata.business_key_fields:
                                    if key_field in transformed_data:
                                        business_key_values[key_field] = transformed_data[key_field]
                                
                                if business_key_values:
                                    # Buscar registro existente
                                    query = select(model_class)
                                    for key, value in business_key_values.items():
                                        query = query.where(getattr(model_class, key) == value)
                                    result = await db.execute(query)
                                    existing_record = result.scalar_one_or_none()
                                    
                                    if existing_record:
                                        # Actualizar registro existente
                                        for key, value in transformed_data.items():
                                            if hasattr(existing_record, key):
                                                setattr(existing_record, key, value)
                                    else:
                                        # Crear nuevo registro
                                        new_record = await _create_entity_with_auto_fields(model_class, transformed_data, db, str(current_user.id))
                                        # No agregamos a db aquí porque _create_entity_with_auto_fields ya lo hace
                                else:
                                    # Sin business key, solo crear
                                    new_record = await _create_entity_with_auto_fields(model_class, transformed_data, db, str(current_user.id))
                                    # No agregamos a db aquí porque _create_entity_with_auto_fields ya lo hace
                            
                            # Manejar confirmación según el modo de errores
                            if skip_errors:
                                # En modo skip_errors, usar savepoints para aislar cada fila
                                if savepoint:
                                    try:
                                        await savepoint.commit()
                                        successful_rows += 1
                                        logger.debug(f"Successfully processed row {current_row_number}: {transformed_data}")
                                    except Exception as db_error:
                                        await savepoint.rollback()
                                        skipped_rows += 1
                                        
                                        # Create more descriptive error messages based on error type
                                        error_str = str(db_error)
                                        if "NotNullViolationError" in error_str:
                                            # Extract the column name from the error
                                            if "code" in error_str:
                                                skip_reason = f"Row {current_row_number}: Missing required field 'code' (auto-generation failed)"
                                            elif "name" in error_str:
                                                skip_reason = f"Row {current_row_number}: Missing required field 'name'"
                                            else:
                                                skip_reason = f"Row {current_row_number}: Missing required field - {error_str.split('column')[1].split('of')[0].strip() if 'column' in error_str else 'unknown field'}"
                                        elif "UniqueViolationError" in error_str or "duplicate key" in error_str.lower():
                                            skip_reason = f"Row {current_row_number}: Duplicate record found"
                                        elif "ForeignKeyViolationError" in error_str:
                                            skip_reason = f"Row {current_row_number}: Invalid reference to related record"
                                        else:
                                            skip_reason = f"Row {current_row_number}: Database error - {str(db_error)}"
                                        
                                        skipped_details.append(skip_reason)
                                        logger.warning(f"Skipping row {current_row_number} due to database error: {skip_reason}")
                                        continue
                                else:
                                    # Fallback cuando no hay savepoint - contar como exitoso pero no confirmar aún
                                    successful_rows += 1
                                    logger.debug(f"Processed row {current_row_number} (no savepoint): {transformed_data}")
                            else:
                                # En modo normal, solo contar - el commit se hará al final
                                successful_rows += 1
                                logger.debug(f"Processed row {current_row_number}: {transformed_data}")
                        
                    except Exception as e:
                        if skip_errors:
                            if savepoint:
                                await savepoint.rollback()
                            skipped_rows += 1
                            skip_reason = f"Row {current_row_number}: Processing error - {str(e)}"
                            skipped_details.append(skip_reason)
                            logger.warning(f"Skipping row {current_row_number} due to processing error: {str(e)}")
                            continue
                        else:
                            error_rows += 1
                            error_msg = f"Row {current_row_number}: {str(e)}"
                            errors.append(error_msg)
                            logger.error(f"Error processing row {current_row_number}: {e}")
                
                # Commit batch in normal mode (not skip_errors)
                if not skip_errors and successful_rows > 0:
                    try:
                        await db.commit()
                        logger.info(f"Committed batch {batch_number + 1} with {len(batch_data)} rows")
                    except Exception as e:
                        await db.rollback()
                        logger.error(f"Error committing batch {batch_number + 1}: {e}")
                        # In normal mode, if batch fails, all rows in batch become errors
                        batch_successful = successful_rows  # Remember how many were successful before this batch
                        error_rows += len(batch_data)
                        errors.append(f"Batch {batch_number + 1} failed: {str(e)}")
                        successful_rows = batch_successful  # Reset to before this batch
                        
            except Exception as batch_error:
                logger.error(f"Error processing batch {batch_number + 1}: {batch_error}")
                if not skip_errors:
                    # In normal mode, batch error affects all rows in batch
                    error_rows += batch_size if batch_number < total_batches - 1 else (total_rows - batch_number * batch_size)
                    errors.append(f"Batch {batch_number + 1} failed: {str(batch_error)}")
                else:
                    # In skip_errors mode, individual rows were already handled
                    pass
        
        # Final commit for skip_errors mode if needed
        if skip_errors:
            # En modo skip_errors, las filas exitosas ya fueron comiteadas individualmente
            # Solo necesitamos hacer commit final si hay cambios pendientes
            try:
                await db.commit()
                logger.info(f"Final commit completed for skip_errors mode - {successful_rows} records were already committed individually")
            except Exception as e:
                logger.warning(f"Final commit failed in skip_errors mode: {e} - Individual commits should have already succeeded")
                await db.rollback()
                logger.error(f"Error committing transaction: {e}")
                # Convertir todos los éxitos en errores si falla el commit
                error_rows += successful_rows
                errors.append(f"Transaction failed: {str(e)}")
                successful_rows = 0
        
        # Calculate execution summary
        execution_summary = {
            "session_id": session_id,
            "model": session.model,
            "import_policy": import_policy,
            "skip_errors": skip_errors,
            "batch_size": batch_size,
            "total_batches": total_batches,
            "status": "completed" if error_rows == 0 else "completed_with_errors",
            "total_rows": total_rows,
            "successful_rows": successful_rows,
            "error_rows": error_rows,
            "skipped_rows": skipped_rows,
            "errors": errors[:10],  # Limit to first 10 errors
            "skipped_details": skipped_details[:10] if skip_errors else [],  # Show skipped details when relevant
            "message": f"Import completed: {successful_rows} successful, {error_rows} errors, {skipped_rows} skipped (Processed in {total_batches} batches of {batch_size} rows)"
        }
        
        # Schedule cleanup of session files
        background_tasks.add_task(session_service._cleanup_session, session_id)
        
        return execution_summary
        
    except ImportSessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error executing import for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error executing import"
        )


@router.get(
    "/templates",
    summary="Get import templates",
    description="Get all available import templates for reuse"
)
async def get_import_templates(
    model_name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> List[dict]:
    """Get import templates"""
    try:
        # For this simplified version, return some example templates
        # In production, you would store and retrieve these from a database
        
        example_templates = []
        
        if not model_name or model_name == "third_party":
            example_templates.append({
                "id": "third_party_basic",
                "name": "Terceros - Mapeo Básico",
                "model": "third_party",
                "description": "Mapeo básico para importar terceros con campos esenciales",
                "mappings": [
                    {"column_name": "codigo", "field_name": "code"},
                    {"column_name": "nombre", "field_name": "name"},
                    {"column_name": "email", "field_name": "email"},
                    {"column_name": "telefono", "field_name": "phone"}
                ],
                "created_by": "System",
                "created_at": "2025-06-23T00:00:00Z"
            })
        
        if not model_name or model_name == "product":
            example_templates.append({
                "id": "product_catalog",
                "name": "Productos - Catálogo Completo",
                "model": "product",
                "description": "Mapeo completo para catálogo de productos",
                "mappings": [
                    {"column_name": "codigo", "field_name": "code"},
                    {"column_name": "nombre", "field_name": "name"},
                    {"column_name": "precio", "field_name": "price"},
                    {"column_name": "categoria", "field_name": "category_id"}
                ],
                "created_by": "System",
                "created_at": "2025-06-23T00:00:00Z"
            })
        
        return example_templates
        
    except Exception as e:
        logger.error(f"Error getting import templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving import templates"
        )


@router.post(
    "/templates",
    summary="Create import template",
    description="Create a new import template for reuse"
)
async def create_import_template(
    template_data: dict,
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Create import template"""
    try:
        # Validate required fields
        required_fields = ["name", "model", "mappings"]
        for field in required_fields:
            if field not in template_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate model exists
        model_name = template_data["model"]
        metadata = metadata_registry.get_model_metadata(model_name)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found"
            )
        
        # TODO: In production, save to database
        # For now, just validate and return success
        
        template_id = f"template_{len(template_data['name'].replace(' ', '_').lower())}"
        
        return {
            "id": template_id,
            "name": template_data["name"],
            "model": template_data["model"],
            "description": template_data.get("description", ""),
            "mappings": template_data["mappings"],
            "created_by": str(current_user.id),
            "created_at": "2025-06-23T00:00:00Z",
            "message": "Template created successfully (note: not persisted in this demo)"
        }
        
    except Exception as e:
        logger.error(f"Error creating import template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating import template"
        )


@router.get(
    "/models/{model_name}/template",
    summary="Download CSV template",
    description="Download a CSV template file with proper column headers for a model"
)
async def download_model_template(
    model_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download CSV template for a model"""
    try:
        # Get model metadata
        metadata = metadata_registry.get_model_metadata(model_name)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found"
            )
        
        # Create CSV headers based on model fields
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header with field labels
        headers = []
        sample_row = []
        
        for field in metadata.fields:
            headers.append(field.display_label)
            
            # Add sample value based on field type
            if field.field_type == "text":
                sample_row.append(f"Ejemplo {field.display_label}")
            elif field.field_type == "number":
                sample_row.append("123.45")
            elif field.field_type == "date":
                sample_row.append("2025-06-23")
            elif field.field_type == "boolean":
                sample_row.append("true")
            elif field.field_type == "email":
                sample_row.append("ejemplo@email.com")
            elif field.field_type == "phone":
                sample_row.append("+1234567890")
            else:
                sample_row.append("Valor ejemplo")
        
        writer.writerow(headers)
        writer.writerow(sample_row)  # Add one sample row
        
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={model_name}_template.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating template for {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating CSV template"
        )


async def validate_row_data(row_data: dict, mapping_dict: dict, model_metadata, db: AsyncSession) -> List[ValidationError]:
    """Pre-validate a row of data to check for errors before processing"""
    validation_errors = []
    
    # Transform row according to mappings
    transformed_data = {}
    
    for column_name, field_name in mapping_dict.items():
        if column_name in row_data:
            raw_value = row_data[column_name]
            
            try:
                # Find field metadata
                field_meta = next(
                    (f for f in model_metadata.fields if f.internal_name == field_name),
                    None
                )
                
                if field_meta:
                    # Validate and transform value
                    validated_value = await validate_field_value(raw_value, field_meta, db)
                    transformed_data[field_name] = validated_value
                else:
                    validation_errors.append(ValidationError(
                        field_name=field_name,
                        error_type="field_not_found",
                        message=f"Field '{field_name}' not found in model metadata",
                        current_value=str(raw_value) if raw_value is not None else None
                    ))
            
            except Exception as e:
                validation_errors.append(ValidationError(
                    field_name=field_name,
                    error_type="validation_error",
                    message=str(e),
                    current_value=str(raw_value) if raw_value is not None else None
                ))
    
    # Check required fields
    required_fields = [f.internal_name for f in model_metadata.fields if f.is_required]
    for req_field in required_fields:
        field_value = transformed_data.get(req_field)
        is_missing_or_empty = (
            req_field not in transformed_data or 
            field_value is None or 
            (isinstance(field_value, str) and field_value.strip() == "")
        )
        
        if is_missing_or_empty:
            validation_errors.append(ValidationError(
                field_name=req_field,
                error_type="required_field_missing",
                message=f"Required field '{req_field}' is missing or empty",
                current_value=repr(field_value) if req_field in transformed_data else None
            ))
    
    # Check uniqueness constraints for business key fields
    if model_metadata.business_key_fields and transformed_data:
        business_key_values = {}
        for key_field in model_metadata.business_key_fields:
            if key_field in transformed_data and transformed_data[key_field] is not None:
                business_key_values[key_field] = transformed_data[key_field]
        
        if business_key_values:
            # Get model class for database query
            model_class = None
            if hasattr(model_metadata, 'model_name'):
                model_name = model_metadata.model_name
            else:
                # Fallback to extract from metadata if model_name not available
                model_name = getattr(model_metadata, 'internal_name', 'unknown')
            
            if model_name == "third_party":
                from app.models.third_party import ThirdParty
                model_class = ThirdParty
            elif model_name == "account":
                from app.models.account import Account
                model_class = Account
            elif model_name == "product":
                from app.models.product import Product
                model_class = Product
            
            if model_class:
                try:
                    # Check if record already exists (case sensitive)
                    query = select(model_class)
                    for key, value in business_key_values.items():
                        query = query.where(getattr(model_class, key) == value)
                    existing = await db.execute(query)
                    if existing.scalar_one_or_none():
                        # Get field metadata to create proper error
                        key_field = list(business_key_values.keys())[0]  # Usually just one key field
                        key_value = business_key_values[key_field]
                        validation_errors.append(ValidationError(
                            field_name=key_field,
                            error_type="duplicate_value",
                            message=f"Value '{key_value}' already exists (case sensitive)",
                            current_value=str(key_value)
                        ))
                except Exception as e:
                    logger.warning(f"Error checking uniqueness: {e}")
    
    return validation_errors
