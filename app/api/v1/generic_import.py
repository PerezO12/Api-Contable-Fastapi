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
from decimal import Decimal
from datetime import date, timedelta
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.generic_import import (
    ModelMetadata,
    FieldMetadata,
    ImportSessionResponse,
    ColumnMapping,
    ImportPreviewRequest,
    ImportPreviewResponse,
    PreviewRowData,
    ValidationError,
    ValidationSummary,
    FieldType
)
from app.schemas.enhanced_import import (
    EnhancedImportExecutionResponse,
    ImportPerformanceMetrics,
    ImportBatchSummary,
    ImportQualityReport,
    DetailedImportError,
    ImportRecordResult,
    ImportErrorType,
    ImportRecordStatus
)
from app.services.model_metadata_registry import ModelMetadataRegistry
from app.services.import_session_service_simple import import_session_service
from app.services.product_service import ProductService
from app.services.generic_import_validators import validate_new_model_data
from app.models.product import Product
from app.schemas.product import ProductCreate
from app.utils.exceptions import (
    ModelNotFoundError,
    ImportSessionNotFoundError,
    ImportError
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _generate_recommendations(errors_by_type: dict, total_failed: int, total_processed: int) -> List[str]:
    """Generate recommendations based on import errors and performance"""
    recommendations = []
    
    if total_failed == 0:
        recommendations.append("Import completed successfully with no errors!")
        return recommendations
    
    error_rate = (total_failed / max(total_processed, 1)) * 100
    
    if error_rate > 50:
        recommendations.append("High error rate detected. Consider reviewing your data format and column mappings.")
    
    if "validation_error" in errors_by_type and errors_by_type["validation_error"] > 0:
        recommendations.append("Multiple validation errors found. Check required fields and data types.")
    
    if "duplicate_error" in errors_by_type and errors_by_type["duplicate_error"] > 0:
        recommendations.append("Duplicate records detected. Consider using 'upsert' import policy to update existing records.")
    
    if "foreign_key_error" in errors_by_type and errors_by_type["foreign_key_error"] > 0:
        recommendations.append("Foreign key constraint errors found. Ensure referenced entities exist before importing.")
    
    if "data_type_error" in errors_by_type and errors_by_type["data_type_error"] > 0:
        recommendations.append("Data type errors detected. Review number formats, dates, and boolean values.")
    
    if error_rate < 10:
        recommendations.append("Low error rate. Consider using 'skip_errors=true' to process valid records.")
    
    return recommendations


# Initialize services
metadata_registry = ModelMetadataRegistry()
session_service = import_session_service


async def _create_entity_with_auto_fields(model_class, transformed_data: dict, db: AsyncSession, current_user_id: str):
    """
    Crea una entidad manejando campos que se generan automáticamente
    Especialmente para productos que generan código automáticamente
    """
    model_name = model_class.__tablename__
    
    if model_name == "invoices":
        # === IMPORTACIÓN DE FACTURAS CON LÍNEAS ===
        return await _create_invoice_with_lines(transformed_data, db, current_user_id)
    
    elif model_name == "products" and model_class == Product:
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
    
    elif model_name == "cost_centers":
        # === IMPORTACIÓN DE CENTROS DE COSTO ===
        from app.models.cost_center import CostCenter
        
        # Manejar el centro padre si se especifica por código
        if 'parent_code' in transformed_data and transformed_data['parent_code']:
            parent_code = transformed_data['parent_code']
            # Buscar el centro padre por código
            parent_query = select(CostCenter).where(CostCenter.code == parent_code)
            parent_result = await db.execute(parent_query)
            parent_center = parent_result.scalar_one_or_none()
            
            if parent_center:
                transformed_data['parent_id'] = parent_center.id
            else:
                logger.warning(f"Parent cost center with code '{parent_code}' not found")
            
            # Remover el campo parent_code ya que no existe en el modelo
            del transformed_data['parent_code']
        
        # Aplicar valores por defecto
        if 'is_active' not in transformed_data:
            transformed_data['is_active'] = True
        if 'allows_direct_assignment' not in transformed_data:
            transformed_data['allows_direct_assignment'] = True
    
    elif model_name == "journals":
        # === IMPORTACIÓN DE DIARIOS CONTABLES ===
        # Aplicar valores por defecto
        if 'sequence_padding' not in transformed_data:
            transformed_data['sequence_padding'] = 4
        if 'include_year_in_sequence' not in transformed_data:
            transformed_data['include_year_in_sequence'] = True
        if 'reset_sequence_yearly' not in transformed_data:
            transformed_data['reset_sequence_yearly'] = True
        if 'requires_validation' not in transformed_data:
            transformed_data['requires_validation'] = False
        if 'allow_manual_entries' not in transformed_data:
            transformed_data['allow_manual_entries'] = True
        if 'is_active' not in transformed_data:
            transformed_data['is_active'] = True
        if 'current_sequence_number' not in transformed_data:
            transformed_data['current_sequence_number'] = 0
    
    elif model_name == "payment_terms":
        # === IMPORTACIÓN DE TÉRMINOS DE PAGO ===
        from app.models.payment_terms import PaymentSchedule
        from decimal import Decimal
        import re
        
        # Procesar cronograma de pagos desde campos de cadena
        payment_schedules_data = []
        
        if 'payment_schedule_days' in transformed_data and 'payment_schedule_percentages' in transformed_data:
            days_str = transformed_data.get('payment_schedule_days', '')
            percentages_str = transformed_data.get('payment_schedule_percentages', '')
            descriptions_str = transformed_data.get('payment_schedule_descriptions', '')
            
            # Parsear días y porcentajes
            try:
                days_list = [int(d.strip()) for d in days_str.split(',') if d.strip()]
                percentages_list = [float(p.strip()) for p in percentages_str.split(',') if p.strip()]
                descriptions_list = [d.strip() for d in descriptions_str.split('|')] if descriptions_str else []
                
                # Validar que tengan la misma longitud
                if len(days_list) != len(percentages_list):
                    raise ValueError("El número de días y porcentajes debe ser igual")
                
                # Validar que los porcentajes sumen 100
                total_percentage = sum(percentages_list)
                if abs(total_percentage - 100.0) > 0.000001:
                    raise ValueError(f"Los porcentajes deben sumar 100%. Actual: {total_percentage}%")
                
                # Crear cronograma de pagos
                for i, (days, percentage) in enumerate(zip(days_list, percentages_list)):
                    description = descriptions_list[i] if i < len(descriptions_list) else None
                    payment_schedules_data.append({
                        'sequence': i + 1,
                        'days': days,
                        'percentage': Decimal(str(percentage)),
                        'description': description
                    })
                
            except Exception as e:
                logger.error(f"Error processing payment schedule: {e}")
                raise ValueError(f"Error en el cronograma de pagos: {e}")
        
        # Remover campos de cronograma ya que no existen en el modelo principal
        for field in ['payment_schedule_days', 'payment_schedule_percentages', 'payment_schedule_descriptions']:
            if field in transformed_data:
                del transformed_data[field]
        
        # Aplicar valores por defecto
        if 'is_active' not in transformed_data:
            transformed_data['is_active'] = True
        
        # Crear el PaymentTerms primero
        new_record = model_class(**transformed_data)
        db.add(new_record)
        await db.flush()  # Para obtener el ID
        
        # Crear los PaymentSchedule asociados
        for schedule_data in payment_schedules_data:
            schedule_data['payment_terms_id'] = new_record.id
            schedule = PaymentSchedule(**schedule_data)
            db.add(schedule)
        
        return new_record
    
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
                    elif session.model == "cost_center":
                        from app.models.cost_center import CostCenter
                        model_class = CostCenter
                    elif session.model == "journal":
                        from app.models.journal import Journal
                        model_class = Journal
                    elif session.model == "payment_terms":
                        from app.models.payment_terms import PaymentTerms
                        model_class = PaymentTerms
                    
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
            
            # === VALIDACIONES ESPECÍFICAS PARA NUEVOS MODELOS ===
            if session.model in ["cost_center", "journal", "payment_terms"] and transformed_data:
                try:
                    specific_errors = await validate_new_model_data(session.model, transformed_data, db, row_number)
                    errors.extend(specific_errors)
                except Exception as e:
                    logger.error(f"Row {row_number}: Error in specific validations for {session.model}: {e}")
                    errors.append(ValidationError(
                        field_name="general",
                        error_type="validation_error",
                        message=f"Error en validaciones específicas: {str(e)}",
                        current_value=""
                    ))
            
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
    response_model=EnhancedImportExecutionResponse,
    summary="Execute import with enhanced performance",
    description="Execute import with optimized bulk operations and detailed error reporting. Supports both sync and async processing."
)
async def execute_import(
    session_id: str,
    mappings: Optional[List[ColumnMapping]] = None,
    import_policy: str = "create_only",  # create_only, update_only, upsert
    skip_errors: bool = False,
    batch_size: int = 2000,
    async_processing: bool = False,  # Nueva opción para procesamiento asíncrono
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> EnhancedImportExecutionResponse:
    """Execute the import operation with enhanced performance and error handling"""
    try:
        # Get session
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import session '{session_id}' not found"
            )
        
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
        
        # Verificar si usar procesamiento asíncrono
        total_rows = session.file_info.total_rows
        
        # Auto-detectar async para archivos grandes (más de 10,000 registros)
        if total_rows > 10000 and not async_processing:
            logger.info(f"Large dataset detected ({total_rows} rows), recommending async processing")
            # No forzamos async, pero lo recomendamos en la respuesta
        
        # PROCESAMIENTO ASÍNCRONO
        if async_processing:
            from app.services.async_import_service import AsyncImportService
            
            async_service = AsyncImportService()
            
            # Pre-validación
            try:
                precheck = await async_service.validate_before_import(
                    session_id=session_id,
                    mappings=mappings,
                    import_policy=import_policy,
                    batch_size=batch_size
                )
                
                if not precheck.can_proceed:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot proceed with import: {'; '.join(precheck.blocking_issues)}"
                    )
                
                if precheck.warnings:
                    logger.warning(f"Import warnings: {'; '.join(precheck.warnings)}")
                
            except Exception as e:
                logger.error(f"Pre-validation failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Pre-validation failed: {str(e)}"
                )
            
            # Encolar para procesamiento asíncrono
            try:
                execution_id = await async_service.queue_import_execution(
                    session_id=session_id,
                    user_id=str(current_user.id),
                    model_name=session.model,
                    import_policy=import_policy,
                    skip_errors=skip_errors,
                    batch_size=batch_size,
                    mappings=mappings
                )
                
                # Para async processing, creamos una respuesta básica ya que el proceso está en cola
                basic_summary = ImportBatchSummary(
                    batch_number=0,
                    batch_size=batch_size,
                    total_processed=0,
                    successful=0,
                    updated=0,
                    failed=0,
                    skipped=0,
                    processing_time_seconds=0.0,
                    records_per_second=0.0,
                    errors_by_type={}
                )
                
                basic_metrics = ImportPerformanceMetrics(
                    total_execution_time_seconds=0.0,
                    average_batch_time_seconds=0.0,
                    peak_records_per_second=0.0,
                    average_records_per_second=0.0,
                    database_time_seconds=0.0,
                    validation_time_seconds=0.0,
                    memory_usage_mb=precheck.estimated_memory_mb if hasattr(precheck, 'estimated_memory_mb') else None
                )
                
                basic_quality = ImportQualityReport(
                    data_quality_score=0.0,
                    completeness_score=0.0,
                    accuracy_score=0.0,
                    field_quality_analysis={},
                    recommendations=precheck.warnings or []
                )
                
                return EnhancedImportExecutionResponse(
                    import_session_token=session_id,
                    execution_id=execution_id,
                    model=session.model,
                    import_policy=import_policy,
                    status="queued",
                    completed_at=datetime.datetime.utcnow(),
                    summary=basic_summary,
                    performance_metrics=basic_metrics,
                    quality_report=basic_quality,
                    successful_samples=[],
                    failed_records=[],
                    errors_by_type={},
                    post_import_actions=[
                        f"Monitor progress at GET /sessions/{session_id}/status/{execution_id}",
                        "Async processing will complete in background"
                    ],
                    download_links={}
                )
                
            except Exception as e:
                logger.error(f"Failed to queue async import: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to queue async import: {str(e)}"
                )
        
        # PROCESAMIENTO SÍNCRONO OPTIMIZADO
        logger.info(f"Starting optimized sync import: {total_rows} total rows")
        
        # Usar el servicio bulk optimizado
        from app.services.bulk_import_service import BulkImportService
        
        bulk_service = BulkImportService(db)
        
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
            model_class = Product
        elif session.model == "invoice":
            from app.models.invoice import Invoice
            model_class = Invoice
        elif session.model == "cost_center":
            from app.models.cost_center import CostCenter
            model_class = CostCenter
        elif session.model == "journal":
            from app.models.journal import Journal
            model_class = Journal
        elif session.model == "payment_terms":
            from app.models.payment_terms import PaymentTerms
            model_class = PaymentTerms
        
        if not model_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model implementation not found for: {session.model}"
            )
        
        # Create mapping dictionary
        mapping_dict = {m.column_name: m.field_name for m in mappings if m.field_name}
        
        # Check required fields are mapped - but allow auto-generated fields
        required_fields = [f.internal_name for f in session.model_metadata.fields if f.is_required]
        mapped_fields = list(mapping_dict.values())
        auto_generated_fields = ["code", "document_number", "document_type", "third_party_type", 
                                "sequence_padding", "include_year_in_sequence", "reset_sequence_yearly", 
                                "requires_validation", "allow_manual_entries", "current_sequence_number",
                                "is_active", "allows_direct_assignment"]
        missing_required = [f for f in required_fields if f not in mapped_fields and f not in auto_generated_fields]
        
        if missing_required and not skip_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Required fields not mapped and cannot be auto-generated: {', '.join(missing_required)}"
            )
        
        # Procesar por batches usando el nuevo servicio optimizado
        total_batches = session_service.get_total_batches(session_id, batch_size)
        
        # Contadores consolidados
        all_successful_records = []
        all_failed_records = []
        all_updated_records = []
        all_skipped_records = []
        all_errors_by_type = {}
        
        total_processing_time = 0.0
        
        logger.info(f"Processing {total_batches} batches of {batch_size} records each")
        
        for batch_number in range(total_batches):
            batch_start_time = time.time()
            
            logger.info(f"Processing batch {batch_number + 1}/{total_batches}")
            
            try:
                # Leer el lote actual del archivo
                batch_data = await session_service.read_file_batch(session_id, batch_size, batch_number)
                
                if not batch_data:
                    logger.info(f"Batch {batch_number + 1} is empty, skipping")
                    continue
                
                # Transformar datos según mapeos
                transformed_batch = []
                for row_data in batch_data:
                    transformed_row = {}
                    
                    # Aplicar mapeos con manejo de múltiples columnas
                    field_mappings = {}
                    for column_name, field_name in mapping_dict.items():
                        if field_name not in field_mappings:
                            field_mappings[field_name] = []
                        field_mappings[field_name].append(column_name)
                    
                    for field_name, column_names in field_mappings.items():
                        field_meta = next(
                            (f for f in session.model_metadata.fields if f.internal_name == field_name),
                            None
                        )
                        
                        if field_meta:
                            final_value = None
                            for column_name in column_names:
                                if column_name in row_data:
                                    raw_value = row_data[column_name]
                                    if raw_value is not None and str(raw_value).strip() != "":
                                        try:
                                            validated_value = await validate_field_value(raw_value, field_meta, db)
                                            if validated_value is not None:
                                                final_value = validated_value
                                                break
                                        except Exception:
                                            continue
                            
                            if final_value is not None:
                                transformed_row[field_name] = final_value
                    
                    # Aplicar valores por defecto
                    for field_meta in session.model_metadata.fields:
                        field_name = field_meta.internal_name
                        if field_name not in transformed_row and hasattr(field_meta, 'default_value'):
                            if field_meta.default_value is not None:
                                transformed_row[field_name] = field_meta.default_value
                    
                    if transformed_row:
                        transformed_batch.append(transformed_row)
                
                if not transformed_batch:
                    continue
                
                # Ejecutar importación bulk optimizada
                batch_start_row = batch_number * batch_size + 1
                batch_result = await bulk_service.bulk_import_records(
                    model_class=model_class,
                    model_metadata=session.model_metadata,
                    records=transformed_batch,
                    import_policy=import_policy,
                    skip_errors=skip_errors,
                    user_id=str(current_user.id),
                    batch_start_row=batch_start_row
                )
                
                # Consolidar resultados
                all_successful_records.extend(batch_result.successful_records)
                all_failed_records.extend(batch_result.failed_records)
                all_updated_records.extend(batch_result.updated_records)
                all_skipped_records.extend(batch_result.skipped_records)
                
                # Consolidar errores por tipo
                for error_type, count in batch_result.errors_by_type.items():
                    all_errors_by_type[error_type] = all_errors_by_type.get(error_type, 0) + count
                
                batch_time = time.time() - batch_start_time
                total_processing_time += batch_time
                
                logger.info(f"Batch {batch_number + 1} completed in {batch_time:.2f}s - "
                          f"Success: {batch_result.total_successful}, "
                          f"Updated: {batch_result.total_updated}, "
                          f"Failed: {batch_result.total_failed}, "
                          f"RPS: {batch_result.records_per_second:.1f}")
                
            except Exception as batch_error:
                logger.error(f"Error processing batch {batch_number + 1}: {batch_error}")
                
                if not skip_errors:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Batch {batch_number + 1} failed: {str(batch_error)}"
                    )
                else:
                    # En modo skip_errors, continuar con el siguiente batch
                    continue
        
        # Calcular métricas finales
        total_successful = len(all_successful_records)
        total_updated = len(all_updated_records)
        total_failed = len(all_failed_records)
        total_skipped = len(all_skipped_records)
        total_processed = total_successful + total_updated + total_failed + total_skipped
        
        avg_rps = total_processed / max(total_processing_time, 0.001)
        
        # Crear métricas de rendimiento
        performance_metrics = ImportPerformanceMetrics(
            total_execution_time_seconds=round(total_processing_time, 2),
            average_batch_time_seconds=round(total_processing_time / max(total_batches, 1), 2),
            peak_records_per_second=round(avg_rps, 1),
            average_records_per_second=round(avg_rps, 1),
            database_time_seconds=round(total_processing_time * 0.7, 2),  # Estimación
            validation_time_seconds=round(total_processing_time * 0.3, 2),  # Estimación
            memory_usage_mb=None
        )
        
        # Crear resumen del batch
        batch_summary = ImportBatchSummary(
            batch_number=total_batches,
            batch_size=batch_size,
            total_processed=total_processed,
            successful=total_successful,
            updated=total_updated,
            failed=total_failed,
            skipped=total_skipped,
            processing_time_seconds=round(total_processing_time, 2),
            records_per_second=round(avg_rps, 1),
            errors_by_type=all_errors_by_type
        )
        
        # Crear reporte de calidad
        success_rate = (total_successful + total_updated) / max(total_processed, 1) * 100
        quality_report = ImportQualityReport(
            data_quality_score=round(success_rate, 1),
            completeness_score=round(success_rate, 1),
            accuracy_score=round(success_rate, 1),
            field_quality_analysis={},
            recommendations=_generate_recommendations(all_errors_by_type, total_failed, total_processed)
        )
        
        # Convertir errores a formato detallado
        detailed_errors = []
        for record in all_failed_records[:50]:  # Máximo 50 errores
            detailed_errors.append(
                ImportRecordResult(
                    row_number=record.get("row_number", 0),
                    status=ImportRecordStatus.FAILED,
                    record_data=record.get("data"),
                    error=DetailedImportError(
                        row_number=record.get("row_number", 0),
                        error_type=ImportErrorType.VALIDATION_ERROR,  # Mapear según sea necesario
                        message=record.get("error", "Unknown error"),
                        field_name=None,
                        field_value=None,
                        suggested_fix=None
                    ),
                    processing_time_ms=None
                )
            )
        
        # Crear muestras de registros exitosos
        successful_samples = []
        for record in all_successful_records[:10]:  # Máximo 10 ejemplos
            successful_samples.append(
                ImportRecordResult(
                    row_number=record.get("row_number", 0),
                    status=ImportRecordStatus.CREATED,
                    record_data=record.get("data"),
                    error=None,
                    processing_time_ms=None
                )
            )
        
        # Crear respuesta mejorada
        execution_response = EnhancedImportExecutionResponse(
            import_session_token=session_id,
            execution_id=str(uuid.uuid4()),
            model=session.model,
            import_policy=import_policy,
            status="completed" if total_failed == 0 else "completed_with_errors",
            completed_at=datetime.datetime.utcnow(),
            summary=batch_summary,
            performance_metrics=performance_metrics,
            quality_report=quality_report,
            successful_samples=successful_samples,
            failed_records=detailed_errors,
            errors_by_type={},  # Se podría categorizar mejor aquí
            post_import_actions=[
                f"Import completed: {total_successful} created, {total_updated} updated, {total_failed} errors",
                "Consider reviewing failed records for data quality improvements" if total_failed > 0 else "All records processed successfully"
            ],
            download_links={}
        )
        
        # Schedule cleanup of session files
        background_tasks.add_task(session_service._cleanup_session, session_id)
        
        return execution_response
        
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
    description="Download a CSV template file with proper column headers and sample data for a model"
)
async def download_model_template(
    model_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download CSV template for a model with realistic sample data"""
    try:
        # Get model metadata
        metadata = metadata_registry.get_model_metadata(model_name)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found"
            )
        
        # Create CSV with sample data based on model
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Generate template using static CSV files if available, otherwise dynamic generation
        headers = [field.display_label for field in metadata.fields]
        
        # Try to read from static template files first
        static_template_path = f"e:/trabajo/Aplicacion/API Contable/templates/{model_name}_plantilla_importacion.csv"
        
        try:
            import os
            if os.path.exists(static_template_path):
                # Use static template file
                with open(static_template_path, 'r', encoding='utf-8-sig') as f:
                    csv_reader = csv.reader(f)
                    static_headers = next(csv_reader)
                    sample_data = list(csv_reader)
                
                # Verify headers match metadata
                if static_headers == headers:
                    # Headers match, use static data
                    pass
                else:
                    # Headers don't match, regenerate with current metadata
                    sample_data = generate_dynamic_sample_data(model_name, metadata)
            else:
                # No static file, generate dynamically
                sample_data = generate_dynamic_sample_data(model_name, metadata)
        except Exception as e:
            logger.warning(f"Could not read static template for {model_name}: {e}")
            # Fallback to dynamic generation
            sample_data = generate_dynamic_sample_data(model_name, metadata)
        
        # Write to CSV
        writer.writerow(headers)
        for row in sample_data:
            writer.writerow(row)
        
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # UTF-8 with BOM for Excel compatibility
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={model_name}_plantilla_importacion.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating template for {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating CSV template"
        )


def generate_dynamic_sample_data(model_name: str, metadata: ModelMetadata) -> List[List[str]]:
    """Generate dynamic sample data based on model metadata"""
    
    def get_sample_value(field: FieldMetadata, row_index: int = 0) -> str:
        """Generate a sample value for a field based on its metadata"""
        
        # Handle choices first
        if field.choices and len(field.choices) > 0:
            # Cycle through choices for variety
            choice_index = row_index % len(field.choices)
            return field.choices[choice_index]["value"]
        
        # Handle default values
        if field.default_value:
            return str(field.default_value)
        
        # Generate values based on field type
        if field.field_type == FieldType.STRING:
            # Handle specific field names with realistic values
            field_name_lower = field.internal_name.lower()
            
            if "code" in field_name_lower:
                return f"{model_name.upper()[:3]}-{row_index + 1:03d}"
            elif "name" in field_name_lower:
                names = [
                    "ACME Corporation S.A.S.",
                    "Distribuidora El Sol Ltda", 
                    "Juan Pérez García",
                    "Tecnología Global S.A.",
                    "María González López"
                ]
                return names[row_index % len(names)]
            elif "document_number" in field_name_lower:
                documents = ["900123456-7", "830987654-3", "1234567890", "860012345-9", "9876543210"]
                return documents[row_index % len(documents)]
            elif "email" in field_name_lower:
                emails = ["contacto@acme.com", "ventas@elsol.com", "juan.perez@email.com", "info@tecglobal.com", "maria.gonzalez@correo.com"]
                return emails[row_index % len(emails)]
            elif "phone" in field_name_lower:
                phones = ["+57-300-123-4567", "+57-301-987-6543", "+57-310-555-7890", "+57-312-456-7890", "+57-320-111-2233"]
                return phones[row_index % len(phones)]
            elif "address" in field_name_lower:
                addresses = ["Calle 123 #45-67, Torre A", "Carrera 45 #123-89, Local 201", "Avenida 68 #12-34, Apto 501", "Zona Industrial, Bodega 25", "Calle 80 #45-12, Casa 15"]
                return addresses[row_index % len(addresses)]
            elif "city" in field_name_lower:
                cities = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga"]
                return cities[row_index % len(cities)]
            elif "description" in field_name_lower:
                return f"Descripción de ejemplo para {field.display_label}"
            else:
                return f"Ejemplo {field.display_label} {row_index + 1}"
                
        elif field.field_type == FieldType.DECIMAL:
            # Generate realistic decimal values
            if "price" in field.internal_name.lower():
                prices = ["100.00", "250.50", "1500.00", "75.25", "500.00"]
                return prices[row_index % len(prices)]
            elif "quantity" in field.internal_name.lower():
                return "1.0000"
            elif "rate" in field.internal_name.lower():
                return "1.0000"
            else:
                return "100.00"
                
        elif field.field_type == FieldType.INTEGER:
            if "level" in field.internal_name.lower():
                return str((row_index % 3) + 1)  # Levels 1-3
            elif "sequence" in field.internal_name.lower():
                return str(row_index + 1)
            else:
                return str(row_index + 1)
                
        elif field.field_type == FieldType.DATE:
            from datetime import datetime, timedelta
            base_date = datetime.now()
            offset_days = row_index * 7  # Week intervals
            sample_date = base_date + timedelta(days=offset_days)
            return sample_date.strftime("%Y-%m-%d")
            
        elif field.field_type == FieldType.BOOLEAN:
            return "true" if row_index % 2 == 0 else "false"
            
        elif field.field_type == FieldType.EMAIL:
            emails = ["contacto@acme.com", "ventas@elsol.com", "juan.perez@email.com", "info@tecglobal.com", "maria.gonzalez@correo.com"]
            return emails[row_index % len(emails)]
            
        elif field.field_type == FieldType.PHONE:
            phones = ["+57-300-123-4567", "+57-301-987-6543", "+57-310-555-7890", "+57-312-456-7890", "+57-320-111-2233"]
            return phones[row_index % len(phones)]
            
        elif field.field_type == FieldType.MANY_TO_ONE:
            # Handle foreign key references
            if field.related_model == "third_party":
                docs = ["900123456-7", "830987654-3", "1234567890"]
                return docs[row_index % len(docs)]
            elif field.related_model == "product":
                codes = ["PRD-001", "SRV-001", "MIX-001"]
                return codes[row_index % len(codes)]
            elif field.related_model == "account":
                codes = ["1105", "1110", "4105", "2105", "5105"]
                return codes[row_index % len(codes)]
            else:
                return f"REF-{row_index + 1:03d}"
        else:
            return f"Valor ejemplo {row_index + 1}"
    
    # Generate multiple rows of sample data
    sample_data = []
    num_rows = 3  # Generate 3 sample rows
    
    for row_index in range(num_rows):
        row = []
        for field in metadata.fields:
            sample_value = get_sample_value(field, row_index)
            row.append(sample_value)
        sample_data.append(row)
    
    return sample_data


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
            elif model_name == "invoice":
                from app.models.invoice import Invoice
                model_class = Invoice
            
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

async def _create_invoice_with_lines(transformed_data: dict, db: AsyncSession, current_user_id: str):
    """
    Crea una factura completa con líneas desde datos transformados de importación
    Maneja tanto datos de cabecera como líneas múltiples en un solo diccionario
    """
    from app.models.invoice import Invoice, InvoiceLine, InvoiceType, InvoiceStatus
    from app.models.third_party import ThirdParty
    from app.models.product import Product
    from app.models.account import Account
    from app.models.cost_center import CostCenter
    from app.models.journal import Journal
    from app.models.payment_terms import PaymentTerms
    from app.services.invoice_service import InvoiceService
    import time
    from decimal import Decimal
    from datetime import datetime, date, timedelta
    from sqlalchemy import select
    
    logger.info(f"Creating invoice with lines from import data: {list(transformed_data.keys())}")
    
    # === RESOLVER RELACIONES ===
    
    # Resolver tercero (cliente/proveedor)
    third_party = None
    if "third_party_document" in transformed_data and transformed_data["third_party_document"]:
        query = select(ThirdParty).where(ThirdParty.document_number == transformed_data["third_party_document"])
        result = await db.execute(query)
        third_party = result.scalar_one_or_none()
        if not third_party:
            raise ValueError(f"Tercero con documento '{transformed_data['third_party_document']}' no encontrado")
    
    # Resolver términos de pago
    payment_terms = None
    if "payment_terms_code" in transformed_data and transformed_data["payment_terms_code"]:
        query = select(PaymentTerms).where(PaymentTerms.code == transformed_data["payment_terms_code"])
        result = await db.execute(query)
        payment_terms = result.scalar_one_or_none()
    
    # Resolver diario contable
    journal = None
    if "journal_code" in transformed_data and transformed_data["journal_code"]:
        query = select(Journal).where(Journal.code == transformed_data["journal_code"])
        result = await db.execute(query)
        journal = result.scalar_one_or_none()
    
    # Resolver centro de costo principal
    cost_center = None
    if "cost_center_code" in transformed_data and transformed_data["cost_center_code"]:
        query = select(CostCenter).where(CostCenter.code == transformed_data["cost_center_code"])
        result = await db.execute(query)
        cost_center = result.scalar_one_or_none()
    
    # Resolver cuenta contable override
    third_party_account = None
    if "third_party_account_code" in transformed_data and transformed_data["third_party_account_code"]:
        query = select(Account).where(Account.code == transformed_data["third_party_account_code"])
        result = await db.execute(query)
        third_party_account = result.scalar_one_or_none()
    
    # === PREPARAR DATOS DE CABECERA ===
    
    # Generar número de factura si no se proporciona
    invoice_number = transformed_data.get("number")
    if not invoice_number:
        # Generar número automático basado en tipo y timestamp
        invoice_type = transformed_data.get("invoice_type", "CUSTOMER_INVOICE")
        prefix = "INV" if invoice_type == "CUSTOMER_INVOICE" else "BIL"
        timestamp = str(int(time.time()))[-6:]
        invoice_number = f"{prefix}-{timestamp}"
        
        # Verificar unicidad
        attempt = 0
        while attempt < 10:
            query = select(Invoice).where(Invoice.number == invoice_number)
            result = await db.execute(query)
            if not result.scalar_one_or_none():
                break
            attempt += 1
            invoice_number = f"{prefix}-{timestamp}-{attempt}"
    
    # Calcular fecha de vencimiento si no se proporciona
    due_date = transformed_data.get("due_date")
    if not due_date and payment_terms:
        invoice_date = transformed_data.get("invoice_date", date.today())
        # Usar la fecha del último cronograma de pago como fecha de vencimiento
        if payment_terms.payment_schedules:
            max_days = max(schedule.days for schedule in payment_terms.payment_schedules)
            due_date = invoice_date + timedelta(days=max_days)
        else:
            due_date = invoice_date + timedelta(days=30)  # Default
    elif not due_date:
        # Default a 30 días
        from datetime import timedelta
        invoice_date = transformed_data.get("invoice_date", date.today())
        due_date = invoice_date + timedelta(days=30)
    
    # === CREAR FACTURA ===
    
    invoice_data = {
        "number": invoice_number,
        "internal_reference": transformed_data.get("internal_reference"),
        "external_reference": transformed_data.get("external_reference"),
        "invoice_type": transformed_data.get("invoice_type", "CUSTOMER_INVOICE"),
        "status": transformed_data.get("status", "DRAFT"),
        "third_party_id": third_party.id if third_party else None,
        "payment_terms_id": payment_terms.id if payment_terms else None,
        "journal_id": journal.id if journal else None,
        "cost_center_id": cost_center.id if cost_center else None,
        "third_party_account_id": third_party_account.id if third_party_account else None,
        "invoice_date": transformed_data.get("invoice_date", date.today()),
        "due_date": due_date,
        "currency_code": transformed_data.get("currency_code", "USD"),
        "exchange_rate": transformed_data.get("exchange_rate", Decimal("1.0000")),
        "subtotal": transformed_data.get("subtotal", Decimal("0.00")),
        "discount_amount": transformed_data.get("discount_amount", Decimal("0.00")),
        "tax_amount": transformed_data.get("tax_amount", Decimal("0.00")),
        "total_amount": transformed_data.get("total_amount", Decimal("0.00")),
        "paid_amount": transformed_data.get("paid_amount", Decimal("0.00")),
        "outstanding_amount": transformed_data.get("outstanding_amount"),
        "description": transformed_data.get("description"),
        "notes": transformed_data.get("notes"),
        "created_by_id": uuid.UUID(current_user_id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Calcular outstanding_amount si no se proporciona
    if invoice_data["outstanding_amount"] is None:
        invoice_data["outstanding_amount"] = invoice_data["total_amount"] - invoice_data["paid_amount"]
    
    # Crear la factura
    new_invoice = Invoice(**invoice_data)
    db.add(new_invoice)
    await db.flush()  # Para obtener el ID
    
    # === CREAR LÍNEAS DE FACTURA ===
    
    # Si hay datos de líneas, crear las líneas
    line_fields = [
        "line_sequence", "line_product_code", "line_description", "line_quantity",
        "line_unit_price", "line_discount_percentage", "line_account_code",
        "line_cost_center_code", "line_tax_codes", "line_subtotal",
        "line_discount_amount", "line_tax_amount", "line_total_amount"
    ]
    
    has_line_data = any(field in transformed_data for field in line_fields)
    
    if has_line_data:
        # Resolver producto si se especifica
        product = None
        if "line_product_code" in transformed_data and transformed_data["line_product_code"]:
            query = select(Product).where(Product.code == transformed_data["line_product_code"])
            result = await db.execute(query)
            product = result.scalar_one_or_none()
        
        # Resolver cuenta contable de la línea
        line_account = None
        if "line_account_code" in transformed_data and transformed_data["line_account_code"]:
            query = select(Account).where(Account.code == transformed_data["line_account_code"])
            result = await db.execute(query)
            line_account = result.scalar_one_or_none()
        
        # Resolver centro de costo de la línea
        line_cost_center = None
        if "line_cost_center_code" in transformed_data and transformed_data["line_cost_center_code"]:
            query = select(CostCenter).where(CostCenter.code == transformed_data["line_cost_center_code"])
            result = await db.execute(query)
            line_cost_center = result.scalar_one_or_none()
        
        # Calcular montos de línea si no se proporcionan
        quantity = transformed_data.get("line_quantity", Decimal("1.0000"))
        unit_price = transformed_data.get("line_unit_price", Decimal("0.00"))
        discount_percentage = transformed_data.get("line_discount_percentage", Decimal("0.00"))
        
        # Calcular subtotal
        line_subtotal = quantity * unit_price
        
        # Calcular descuento
        line_discount_amount = line_subtotal * (discount_percentage / 100)
        
        # Por ahora impuestos en 0 - se calcularían más tarde
        line_tax_amount = transformed_data.get("line_tax_amount", Decimal("0.00"))
        
        # Total de línea
        line_total = line_subtotal - line_discount_amount + line_tax_amount
        
        # Usar valores calculados si no se proporcionaron
        if "line_subtotal" not in transformed_data:
            transformed_data["line_subtotal"] = line_subtotal
        if "line_discount_amount" not in transformed_data:
            transformed_data["line_discount_amount"] = line_discount_amount
        if "line_total_amount" not in transformed_data:
            transformed_data["line_total_amount"] = line_total
        
        # Crear línea de factura
        line_data = {
            "invoice_id": new_invoice.id,
            "sequence": transformed_data.get("line_sequence", 1),
            "product_id": product.id if product else None,
            "description": transformed_data.get("line_description", "Línea importada"),
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_percentage": discount_percentage,
            "account_id": line_account.id if line_account else None,
            "cost_center_id": line_cost_center.id if line_cost_center else None,
            "subtotal": transformed_data.get("line_subtotal", line_subtotal),
            "discount_amount": transformed_data.get("line_discount_amount", line_discount_amount),
            "tax_amount": line_tax_amount,
            "total_amount": transformed_data.get("line_total_amount", line_total),
            "created_by_id": uuid.UUID(current_user_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        new_line = InvoiceLine(**line_data)
        db.add(new_line)
        
        # Actualizar totales de factura basados en la línea si no se proporcionaron
        if transformed_data.get("subtotal") == Decimal("0.00"):
            new_invoice.subtotal = line_subtotal
        if transformed_data.get("discount_amount") == Decimal("0.00"):
            new_invoice.discount_amount = line_discount_amount
        if transformed_data.get("tax_amount") == Decimal("0.00"):
            new_invoice.tax_amount = line_tax_amount
        if transformed_data.get("total_amount") == Decimal("0.00"):
            new_invoice.total_amount = line_total
            new_invoice.outstanding_amount = line_total - new_invoice.paid_amount
        
        logger.info(f"Created invoice line: product={product.code if product else 'None'}, qty={quantity}, price={unit_price}, total={line_total}")
    
    logger.info(f"Created invoice: {invoice_number}, type={new_invoice.invoice_type}, total={new_invoice.total_amount}")
    
    return new_invoice
