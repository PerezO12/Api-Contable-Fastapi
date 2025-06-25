"""
Validaciones específicas para la importación genérica de nuevos modelos
Centros de Costo, Diarios y Términos de Pago
"""
from typing import Dict, List, Any, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.cost_center import CostCenter
from app.models.journal import Journal, JournalType  
from app.models.payment_terms import PaymentTerms
from app.schemas.generic_import import ValidationError

logger = logging.getLogger(__name__)


async def validate_cost_center_data(data: Dict[str, Any], db: AsyncSession, row_number: int) -> List[ValidationError]:
    """
    Valida datos específicos de centros de costo durante la importación
    """
    errors = []
    
    # Validar código único
    if 'code' in data and data['code']:
        code = data['code']
        query = select(CostCenter).where(CostCenter.code == code)
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            errors.append(ValidationError(
                field_name="code",
                error_type="duplicate_value",
                message=f"Ya existe un centro de costo con código '{code}'",
                current_value=str(code)
            ))
    
    # Validar nombre único
    if 'name' in data and data['name']:
        name = data['name']
        query = select(CostCenter).where(CostCenter.name == name)
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            errors.append(ValidationError(
                field_name="name",
                error_type="duplicate_value",
                message=f"Ya existe un centro de costo con nombre '{name}'",
                current_value=str(name)
            ))
    
    # Validar que el centro padre existe si se especifica
    if 'parent_code' in data and data['parent_code']:
        parent_code = data['parent_code']
        query = select(CostCenter).where(CostCenter.code == parent_code)
        parent_result = await db.execute(query)
        if not parent_result.scalar_one_or_none():
            errors.append(ValidationError(
                field_name="parent_code",
                error_type="reference_not_found",
                message=f"No se encontró centro de costo padre con código '{parent_code}'",
                current_value=str(parent_code)
            ))
    
    return errors


async def validate_journal_data(data: Dict[str, Any], db: AsyncSession, row_number: int) -> List[ValidationError]:
    """
    Valida datos específicos de diarios durante la importación
    """
    errors = []
    
    # Validar código único
    if 'code' in data and data['code']:
        code = data['code']
        query = select(Journal).where(Journal.code == code)
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            errors.append(ValidationError(
                field_name="code",
                error_type="duplicate_value",
                message=f"Ya existe un diario con código '{code}'",
                current_value=str(code)
            ))
    
    # Validar prefijo de secuencia único
    if 'sequence_prefix' in data and data['sequence_prefix']:
        prefix = data['sequence_prefix']
        query = select(Journal).where(Journal.sequence_prefix == prefix)
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            errors.append(ValidationError(
                field_name="sequence_prefix",
                error_type="duplicate_value",
                message=f"Ya existe un diario con prefijo de secuencia '{prefix}'",
                current_value=str(prefix)
            ))
    
    # Validar tipo de diario
    if 'type' in data and data['type']:
        journal_type = data['type']
        valid_types = [t.value for t in JournalType]
        if journal_type not in valid_types:
            errors.append(ValidationError(
                field_name="type",
                error_type="invalid_choice",
                message=f"Tipo de diario inválido '{journal_type}'. Valores válidos: {', '.join(valid_types)}",
                current_value=str(journal_type)
            ))
    
    # Validar rango de sequence_padding
    if 'sequence_padding' in data and data['sequence_padding'] is not None:
        padding = data['sequence_padding']
        try:
            padding_int = int(padding)
            if padding_int < 1 or padding_int > 10:
                errors.append(ValidationError(
                    field_name="sequence_padding",
                    error_type="value_out_of_range",
                    message=f"El relleno de secuencia debe estar entre 1 y 10. Valor actual: {padding_int}",
                    current_value=str(padding)
                ))
        except (ValueError, TypeError):
            errors.append(ValidationError(
                field_name="sequence_padding",
                error_type="invalid_format",
                message=f"El relleno de secuencia debe ser un número entero",
                current_value=str(padding)
            ))
    
    return errors


async def validate_payment_terms_data(data: Dict[str, Any], db: AsyncSession, row_number: int) -> List[ValidationError]:
    """
    Valida datos específicos de términos de pago durante la importación
    """
    errors = []
    
    # Validar código único
    if 'code' in data and data['code']:
        code = data['code']
        query = select(PaymentTerms).where(PaymentTerms.code == code)
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            errors.append(ValidationError(
                field_name="code",
                error_type="duplicate_value",
                message=f"Ya existen términos de pago con código '{code}'",
                current_value=str(code)
            ))
    
    # Validar cronograma de pagos
    days_str = data.get('payment_schedule_days', '')
    percentages_str = data.get('payment_schedule_percentages', '')
    
    if days_str or percentages_str:
        days_list = []
        percentages_list = []
        
        try:
            # Parsear días
            if not days_str.strip():
                errors.append(ValidationError(
                    field_name="payment_schedule_days",
                    error_type="required_field",
                    message="Los días de pago son obligatorios",
                    current_value=""
                ))
            else:
                days_list = [int(d.strip()) for d in days_str.split(',') if d.strip()]
                if not days_list:
                    errors.append(ValidationError(
                        field_name="payment_schedule_days",
                        error_type="invalid_format",
                        message="Debe especificar al menos un día de pago",
                        current_value=days_str
                    ))
                
                # Validar que los días sean no negativos
                for day in days_list:
                    if day < 0:
                        errors.append(ValidationError(
                            field_name="payment_schedule_days",
                            error_type="invalid_value",
                            message=f"Los días de pago no pueden ser negativos: {day}",
                            current_value=days_str
                        ))
                
                # Validar que estén en orden ascendente
                if days_list != sorted(days_list):
                    errors.append(ValidationError(
                        field_name="payment_schedule_days",
                        error_type="invalid_order",
                        message="Los días de pago deben estar en orden ascendente",
                        current_value=days_str
                    ))
            
            # Parsear porcentajes
            if not percentages_str.strip():
                errors.append(ValidationError(
                    field_name="payment_schedule_percentages",
                    error_type="required_field",
                    message="Los porcentajes de pago son obligatorios",
                    current_value=""
                ))
            else:
                percentages_list = [float(p.strip()) for p in percentages_str.split(',') if p.strip()]
                if not percentages_list:
                    errors.append(ValidationError(
                        field_name="payment_schedule_percentages",
                        error_type="invalid_format",
                        message="Debe especificar al menos un porcentaje de pago",
                        current_value=percentages_str
                    ))
                
                # Validar rango de porcentajes
                for percentage in percentages_list:
                    if percentage <= 0 or percentage > 100:
                        errors.append(ValidationError(
                            field_name="payment_schedule_percentages",
                            error_type="value_out_of_range",
                            message=f"Los porcentajes deben estar entre 0.000001 y 100: {percentage}",
                            current_value=percentages_str
                        ))
                
                # Validar que sumen 100%
                total_percentage = sum(percentages_list)
                if abs(total_percentage - 100.0) > 0.000001:
                    errors.append(ValidationError(
                        field_name="payment_schedule_percentages",
                        error_type="invalid_total",
                        message=f"Los porcentajes deben sumar exactamente 100%. Total actual: {total_percentage}%",
                        current_value=percentages_str
                    ))
            
            # Validar que las listas tengan la misma longitud (solo si ambas fueron parseadas exitosamente)
            if days_list and percentages_list and len(days_list) != len(percentages_list):
                errors.append(ValidationError(
                    field_name="payment_schedule_percentages",
                    error_type="length_mismatch",
                    message=f"El número de días ({len(days_list)}) y porcentajes ({len(percentages_list)}) debe ser igual",
                    current_value=percentages_str
                ))
        
        except ValueError as e:
            errors.append(ValidationError(
                field_name="payment_schedule_days" if "invalid literal" in str(e) and days_str in str(e) else "payment_schedule_percentages",
                error_type="invalid_format",
                message=f"Error al procesar cronograma de pagos: {str(e)}",
                current_value=days_str if "invalid literal" in str(e) and days_str in str(e) else percentages_str
            ))
    
    return errors


async def validate_new_model_data(model_name: str, data: Dict[str, Any], db: AsyncSession, row_number: int) -> List[ValidationError]:
    """
    Función principal para validar datos de los nuevos modelos
    """
    if model_name == "cost_center":
        return await validate_cost_center_data(data, db, row_number)
    elif model_name == "journal":
        return await validate_journal_data(data, db, row_number)
    elif model_name == "payment_terms":
        return await validate_payment_terms_data(data, db, row_number)
    else:
        return []
