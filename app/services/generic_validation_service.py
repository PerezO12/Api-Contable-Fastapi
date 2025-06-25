"""
Servicio de Validación Genérica para Importaciones
Motor de validaciones configurable basado en metadatos
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.generic_import import (
    ValidationError, FieldMetadata, FieldType, ModelMetadata,
    PreviewRowData, ValidationSummary
)
from app.services.model_metadata_registry import model_registry


class GenericValidationService:
    """
    Motor de validaciones que opera basado en metadatos de modelos
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self._phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
    
    async def validate_preview_rows(
        self,
        rows_data: List[Dict[str, Any]],
        column_mappings: Dict[str, str],  # column_name -> field_name
        model_metadata: ModelMetadata
    ) -> Tuple[List[PreviewRowData], ValidationSummary]:
        """
        Valida filas de preview y genera resumen
        """
        preview_rows = []
        total_errors = 0
        total_warnings = 0
        error_breakdown = {}
        
        for row_num, original_row in enumerate(rows_data, 1):
            # Transformar datos según mapeo
            transformed_data = await self._transform_row_data(
                original_row, 
                column_mappings, 
                model_metadata
            )
            
            # Validar fila transformada
            validation_result = await self._validate_single_row(
                transformed_data,
                model_metadata,
                row_num
            )
            
            # Determinar estado de validación
            if validation_result.errors:
                validation_status = "error"
                total_errors += 1
                
                # Contar tipos de errores
                for error in validation_result.errors:
                    error_type = error.error_type
                    error_breakdown[error_type] = error_breakdown.get(error_type, 0) + 1
            elif validation_result.warnings:
                validation_status = "warning"
                total_warnings += 1
            else:
                validation_status = "valid"
            
            preview_rows.append(PreviewRowData(
                row_number=row_num,
                original_data=original_row,
                transformed_data=transformed_data,
                validation_status=validation_status,
                errors=validation_result.errors,
                warnings=validation_result.warnings
            ))
        
        # Generar resumen
        validation_summary = ValidationSummary(
            total_rows_analyzed=len(rows_data),
            valid_rows=len([r for r in preview_rows if r.validation_status == "valid"]),
            rows_with_errors=total_errors,
            rows_with_warnings=total_warnings,
            error_breakdown=error_breakdown
        )
        
        return preview_rows, validation_summary
    
    async def _transform_row_data(
        self,
        original_row: Dict[str, Any],
        column_mappings: Dict[str, str],
        model_metadata: ModelMetadata
    ) -> Dict[str, Any]:
        """
        Transforma datos de una fila según mapeo y tipos de campo
        """
        transformed_data = {}
        
        for column_name, field_name in column_mappings.items():
            if not field_name:  # Campo ignorado
                continue
            
            # Obtener valor original
            original_value = original_row.get(column_name, '')
            
            # Obtener metadatos del campo
            field_metadata = model_registry.get_field_metadata(model_metadata.model_name, field_name)
            if not field_metadata:
                continue
            
            # Transformar según tipo de campo
            transformed_value = await self._transform_field_value(
                original_value,
                field_metadata
            )
            
            transformed_data[field_name] = transformed_value
        
        return transformed_data
    
    async def _transform_field_value(
        self,
        value: Any,
        field_metadata: FieldMetadata
    ) -> Any:
        """
        Transforma un valor según el tipo de campo
        """
        if value is None or value == '':
            return field_metadata.default_value
        
        str_value = str(value).strip()
        
        try:
            if field_metadata.field_type == FieldType.STRING:
                return str_value
            
            elif field_metadata.field_type == FieldType.INTEGER:
                return int(float(str_value))  # Maneja decimales que deberían ser enteros
            
            elif field_metadata.field_type == FieldType.DECIMAL:
                return float(str_value)
            
            elif field_metadata.field_type == FieldType.BOOLEAN:
                lower_val = str_value.lower()
                if lower_val in ['true', '1', 'yes', 'sí', 'si', 'verdadero']:
                    return True
                elif lower_val in ['false', '0', 'no', 'falso']:
                    return False
                else:
                    return bool(str_value)
            
            elif field_metadata.field_type == FieldType.DATE:
                return self._parse_date(str_value)
            
            elif field_metadata.field_type == FieldType.DATETIME:
                return self._parse_datetime(str_value)
            
            elif field_metadata.field_type == FieldType.EMAIL:
                return str_value.lower()
            
            elif field_metadata.field_type == FieldType.PHONE:
                return self._clean_phone_number(str_value)
            
            elif field_metadata.field_type == FieldType.MANY_TO_ONE:
                # Para relaciones, mantener el valor original para resolución posterior
                return str_value
            
            else:
                return str_value
        
        except Exception:
            # Si hay error en transformación, retornar valor original
            return str_value
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parsea una fecha en varios formatos
        """
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _parse_datetime(self, datetime_str: str) -> Optional[str]:
        """
        Parsea fecha y hora en varios formatos
        """
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M'
        ]
        
        for fmt in formats:
            try:
                parsed_datetime = datetime.strptime(datetime_str, fmt)
                return parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
        
        return None
    
    def _clean_phone_number(self, phone: str) -> str:
        """
        Limpia número de teléfono removiendo caracteres especiales
        """
        # Remover espacios, guiones, paréntesis
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
        return cleaned
    
    async def _validate_single_row(
        self,
        row_data: Dict[str, Any],
        model_metadata: ModelMetadata,
        row_number: int
    ) -> 'RowValidationResult':
        """
        Valida una fila completa de datos
        """
        errors = []
        warnings = []
        
        # Validar campos requeridos
        for field in model_metadata.fields:
            if field.is_required:
                value = row_data.get(field.internal_name)
                if value is None or value == '':
                    errors.append(ValidationError(
                        field_name=field.internal_name,
                        error_type="required_field_missing",
                        message=f"El campo '{field.display_label}' es obligatorio",
                        current_value=str(value) if value is not None else None
                    ))
        
        # Validar cada campo individualmente
        for field_name, value in row_data.items():
            field_metadata = model_registry.get_field_metadata(model_metadata.model_name, field_name)
            if not field_metadata:
                continue
            
            field_errors, field_warnings = await self._validate_field_value(
                value,
                field_metadata,
                row_number
            )
            
            errors.extend(field_errors)
            warnings.extend(field_warnings)
        
        return RowValidationResult(errors=errors, warnings=warnings)
    
    async def _validate_field_value(
        self,
        value: Any,
        field_metadata: FieldMetadata,
        row_number: int
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """
        Valida un valor específico de campo
        """
        errors = []
        warnings = []
        
        if value is None or value == '':
            # Campo vacío ya se validó en campos requeridos
            return errors, warnings
        
        str_value = str(value)
        
        # Validaciones por tipo de campo
        if field_metadata.field_type == FieldType.EMAIL:
            if not self._email_pattern.match(str_value):
                errors.append(ValidationError(
                    field_name=field_metadata.internal_name,
                    error_type="invalid_email_format",
                    message="El formato del email no es válido",
                    current_value=str_value
                ))
        
        elif field_metadata.field_type == FieldType.PHONE:
            if not self._phone_pattern.match(self._clean_phone_number(str_value)):
                warnings.append(ValidationError(
                    field_name=field_metadata.internal_name,
                    error_type="invalid_phone_format",
                    message="El formato del teléfono podría no ser válido",
                    current_value=str_value
                ))
        
        elif field_metadata.field_type == FieldType.INTEGER:
            try:
                int_value = int(float(str_value))
                if field_metadata.min_value is not None and int_value < field_metadata.min_value:
                    errors.append(ValidationError(
                        field_name=field_metadata.internal_name,
                        error_type="value_below_minimum",
                        message=f"El valor debe ser mayor o igual a {field_metadata.min_value}",
                        current_value=str_value
                    ))
                if field_metadata.max_value is not None and int_value > field_metadata.max_value:
                    errors.append(ValidationError(
                        field_name=field_metadata.internal_name,
                        error_type="value_above_maximum",
                        message=f"El valor debe ser menor o igual a {field_metadata.max_value}",
                        current_value=str_value
                    ))
            except (ValueError, InvalidOperation):
                errors.append(ValidationError(
                    field_name=field_metadata.internal_name,
                    error_type="invalid_integer",
                    message="El valor debe ser un número entero",
                    current_value=str_value
                ))
        
        elif field_metadata.field_type == FieldType.DECIMAL:
            try:
                decimal_value = float(str_value)
                if field_metadata.min_value is not None and decimal_value < field_metadata.min_value:
                    errors.append(ValidationError(
                        field_name=field_metadata.internal_name,
                        error_type="value_below_minimum",
                        message=f"El valor debe ser mayor o igual a {field_metadata.min_value}",
                        current_value=str_value
                    ))
                if field_metadata.max_value is not None and decimal_value > field_metadata.max_value:
                    errors.append(ValidationError(
                        field_name=field_metadata.internal_name,
                        error_type="value_above_maximum",
                        message=f"El valor debe ser menor o igual a {field_metadata.max_value}",
                        current_value=str_value
                    ))
            except (ValueError, InvalidOperation):
                errors.append(ValidationError(
                    field_name=field_metadata.internal_name,
                    error_type="invalid_decimal",
                    message="El valor debe ser un número",
                    current_value=str_value
                ))
        
        elif field_metadata.field_type == FieldType.DATE:
            parsed_date = self._parse_date(str_value)
            if parsed_date is None:
                errors.append(ValidationError(
                    field_name=field_metadata.internal_name,
                    error_type="invalid_date_format",
                    message="El formato de fecha no es válido",
                    current_value=str_value
                ))
        
        elif field_metadata.field_type == FieldType.STRING:
            if field_metadata.max_length and len(str_value) > field_metadata.max_length:
                errors.append(ValidationError(
                    field_name=field_metadata.internal_name,
                    error_type="string_too_long",
                    message=f"El texto no puede tener más de {field_metadata.max_length} caracteres",
                    current_value=str_value[:50] + "..." if len(str_value) > 50 else str_value
                ))
        
        elif field_metadata.field_type == FieldType.MANY_TO_ONE:
            # Validar relación many-to-one
            relation_errors = await self._validate_foreign_key(
                str_value,
                field_metadata,
                row_number
            )
            errors.extend(relation_errors)
        
        return errors, warnings
    
    async def _validate_foreign_key(
        self,
        value: str,
        field_metadata: FieldMetadata,
        row_number: int
    ) -> List[ValidationError]:
        """
        Valida que existe el registro relacionado
        """
        errors = []
        
        if not field_metadata.related_model or not field_metadata.search_field:
            return errors
        
        # En un sistema real, aquí se haría consulta a la BD
        # Por ahora, simulamos validación básica
        if not value.strip():
            errors.append(ValidationError(
                field_name=field_metadata.internal_name,
                error_type="empty_foreign_key",
                message=f"Se requiere un valor para {field_metadata.display_label}",
                current_value=value
            ))
        
        # TODO: Implementar consulta real a la BD para verificar existencia
        # related_record = await self._find_related_record(
        #     field_metadata.related_model,
        #     field_metadata.search_field,
        #     value
        # )
        # if not related_record:
        #     errors.append(ValidationError(...))
        
        return errors


class RowValidationResult:
    """Resultado de validación de una fila"""
    def __init__(self, errors: List[ValidationError], warnings: List[ValidationError]):
        self.errors = errors
        self.warnings = warnings
