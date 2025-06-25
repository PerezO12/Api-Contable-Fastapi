"""
Bulk Import Service - Optimized for Performance
Inspired by Odoo's import system with enhanced error handling and reporting
"""
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Union
from decimal import Decimal

from sqlalchemy import text, select, insert, update, and_, or_, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert, TIMESTAMP
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.inspection import inspect

from app.schemas.generic_import import (
    ModelMetadata, FieldMetadata, ValidationError, 
    ImportExecutionResponse
)


logger = logging.getLogger(__name__)


class BulkImportResult:
    """Resultado detallado de importación bulk"""
    
    def __init__(self):
        self.successful_records: List[Dict[str, Any]] = []
        self.failed_records: List[Dict[str, Any]] = []
        self.updated_records: List[Dict[str, Any]] = []
        self.skipped_records: List[Dict[str, Any]] = []
        
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.total_updated = 0
        self.total_skipped = 0
        
        self.processing_time_seconds = 0.0
        self.records_per_second = 0.0
        
        self.errors_by_type: Dict[str, int] = {}
        self.detailed_errors: List[Dict[str, Any]] = []
        
    def add_success(self, record_data: Dict[str, Any], row_number: int):
        """Agregar registro exitoso"""
        self.successful_records.append({
            "row_number": row_number,
            "data": record_data,
            "status": "created"
        })
        self.total_successful += 1
        
    def add_update(self, record_data: Dict[str, Any], row_number: int):
        """Agregar registro actualizado"""
        self.updated_records.append({
            "row_number": row_number,
            "data": record_data,
            "status": "updated"
        })
        self.total_updated += 1
        
    def add_failure(self, record_data: Dict[str, Any], row_number: int, error: str, error_type: str = "unknown"):
        """Agregar registro fallido"""
        self.failed_records.append({
            "row_number": row_number,
            "data": record_data,
            "error": error,
            "error_type": error_type,
            "status": "failed"
        })
        self.total_failed += 1
        
        # Contar errores por tipo
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        
        # Agregar error detallado
        self.detailed_errors.append({
            "row_number": row_number,
            "error_type": error_type,
            "message": error,
            "field_data": record_data
        })
        
    def add_skip(self, record_data: Dict[str, Any], row_number: int, reason: str):
        """Agregar registro omitido"""
        self.skipped_records.append({
            "row_number": row_number,
            "data": record_data,
            "reason": reason,
            "status": "skipped"
        })
        self.total_skipped += 1
        
    def finalize(self, start_time: float):
        """Finalizar y calcular métricas"""
        self.total_processed = self.total_successful + self.total_failed + self.total_updated + self.total_skipped
        self.processing_time_seconds = time.time() - start_time
        
        if self.processing_time_seconds > 0:
            self.records_per_second = self.total_processed / self.processing_time_seconds
            
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen ejecutivo"""
        return {
            "total_processed": self.total_processed,
            "successful": self.total_successful,
            "updated": self.total_updated,
            "failed": self.total_failed,
            "skipped": self.total_skipped,
            "processing_time_seconds": round(self.processing_time_seconds, 2),
            "records_per_second": round(self.records_per_second, 2),
            "errors_by_type": self.errors_by_type,
            "success_rate": round((self.total_successful + self.total_updated) / max(self.total_processed, 1) * 100, 2)
        }


class BulkImportService:
    """
    Servicio optimizado para importaciones masivas
    Implementa estrategias de Odoo con optimizaciones para PostgreSQL
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retry_attempts = 3
        self.retry_delays = [0.1, 0.5, 1.0]  # Backoff exponencial
        
    def _convert_timestamp_fields(self, record: Dict[str, Any], model_class: type) -> Dict[str, Any]:
        """
        Convierte todos los campos datetime que son TIMESTAMP WITH TIME ZONE a timezone-aware.
        
        Esta función es crucial para evitar errores con PostgreSQL cuando se usan campos
        TIMESTAMP WITH TIME ZONE en operaciones bulk insert/upsert.
        
        Args:
            record: Diccionario con los datos del registro
            model_class: Clase del modelo SQLAlchemy
            
        Returns:
            Diccionario con campos datetime convertidos a timezone-aware (UTC)
        """
        converted_record = record.copy()
        
        try:
            # Obtener información de columnas del modelo
            mapper = inspect(model_class)
            
            for column_name, column in mapper.columns.items():
                if column_name not in record:
                    continue
                    
                value = record[column_name]
                if value is None:
                    continue
                
                # Verificar si es un campo TIMESTAMP WITH TIME ZONE
                is_timestamp_with_tz = False
                
                # Verificar tipo DateTime con timezone=True
                if isinstance(column.type, DateTime) and getattr(column.type, 'timezone', False):
                    is_timestamp_with_tz = True
                
                # Verificar tipo TIMESTAMP de PostgreSQL con timezone
                elif isinstance(column.type, TIMESTAMP) and getattr(column.type, 'timezone', False):
                    is_timestamp_with_tz = True
                
                # Si es un campo TIMESTAMP WITH TIME ZONE y el valor es datetime
                if is_timestamp_with_tz and isinstance(value, datetime):
                    if value.tzinfo is None:
                        # Convertir datetime naive a UTC
                        converted_record[column_name] = value.replace(tzinfo=timezone.utc)
                        logger.debug(f"Converted naive datetime to UTC for field {column_name}")
                    else:
                        # Ya tiene timezone, mantener el valor
                        converted_record[column_name] = value
                
        except Exception as e:
            # En caso de error en la inspección, aplicar conversión a campos conocidos
            logger.warning(f"Error inspecting model {model_class.__name__}: {e}. Using fallback conversion.")
            
            # Campos conocidos que típicamente son TIMESTAMP WITH TIME ZONE
            timestamp_fields = ['created_at', 'updated_at', 'deleted_at', 'date', 'invoice_date', 'due_date']
            
            for field_name in timestamp_fields:
                if field_name in record and isinstance(record[field_name], datetime):
                    value = record[field_name]
                    if value.tzinfo is None:
                        converted_record[field_name] = value.replace(tzinfo=timezone.utc)
                        logger.debug(f"Converted naive datetime to UTC for field {field_name} (fallback)")
        
        return converted_record
    
    def _validate_record_for_insert(self, record: Dict[str, Any], model_class: type) -> tuple[bool, str]:
        """
        Valida que un registro tenga los datos necesarios para ser insertado.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Validaciones básicas para Account
            if model_class.__name__ == 'Account':
                # Campos requeridos
                required_fields = ['code', 'name', 'account_type']
                for field in required_fields:
                    if field not in record or record[field] is None or str(record[field]).strip() == '':
                        return False, f"Missing or empty required field: {field}"
                
                # Validar código de cuenta
                if len(str(record['code']).strip()) == 0:
                    return False, "Account code cannot be empty"
                    
                # Validar nombre de cuenta
                if len(str(record['name']).strip()) == 0:
                    return False, "Account name cannot be empty"
                
                # Validar tipo de cuenta
                valid_account_types = ['activo', 'pasivo', 'patrimonio', 'ingreso', 'gasto', 'costos']
                account_type = str(record.get('account_type', '')).lower().strip()
                if account_type not in valid_account_types:
                    return False, f"Invalid account_type: {account_type}. Must be one of: {valid_account_types}"
                
                # Validar parent_id si existe
                if 'parent_id' in record and record['parent_id'] is not None:
                    try:
                        if isinstance(record['parent_id'], str):
                            uuid.UUID(record['parent_id'])
                    except (ValueError, TypeError):
                        return False, "Invalid parent_id format, must be a valid UUID"
                
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
        
    async def bulk_import_records(
        self,
        model_class: type,
        model_metadata: ModelMetadata,
        records: List[Dict[str, Any]],
        import_policy: str = "create_only",
        skip_errors: bool = False,
        user_id: Optional[str] = None,
        batch_start_row: int = 1
    ) -> BulkImportResult:
        """
        Importación masiva optimizada con manejo de errores detallado
        
        Args:
            model_class: Clase del modelo SQLAlchemy
            model_metadata: Metadatos del modelo
            records: Lista de registros a importar
            import_policy: Política de importación (create_only, upsert, update_only)
            skip_errors: Continuar en caso de errores
            user_id: ID del usuario que ejecuta la importación
            batch_start_row: Número de fila inicial para reportes
        """
        start_time = time.time()
        result = BulkImportResult()
        
        if not records:
            result.finalize(start_time)
            return result
            
        logger.info(f"Starting bulk import: {len(records)} records, policy: {import_policy}")
        
        # Timestamp unificado para todo el batch - GARANTIZAR QUE SIEMPRE SEA UTC
        unified_timestamp = datetime.now(timezone.utc)
        
        # VALIDACIÓN CRÍTICA: Asegurar que unified_timestamp tiene timezone UTC
        if unified_timestamp.tzinfo is None:
            unified_timestamp = unified_timestamp.replace(tzinfo=timezone.utc)
            logger.warning("unified_timestamp was naive, forced to UTC")
        elif unified_timestamp.tzinfo != timezone.utc:
            unified_timestamp = unified_timestamp.astimezone(timezone.utc)
            logger.warning("unified_timestamp was not UTC, converted to UTC")
        
        # Usar user_id por defecto si no se proporciona
        effective_user_id = user_id or "system"
        
        try:
            if import_policy == "create_only":
                await self._bulk_create_only(
                    model_class, model_metadata, records, result, 
                    skip_errors, effective_user_id, unified_timestamp, batch_start_row
                )
            elif import_policy == "upsert":
                await self._bulk_upsert(
                    model_class, model_metadata, records, result,
                    skip_errors, effective_user_id, unified_timestamp, batch_start_row
                )
            elif import_policy == "update_only":
                # Para update_only, usar la misma lógica que upsert pero solo actualizando
                await self._bulk_upsert(
                    model_class, model_metadata, records, result,
                    skip_errors, effective_user_id, unified_timestamp, batch_start_row
                )
            else:
                raise ValueError(f"Unsupported import policy: {import_policy}")
                
        except Exception as e:
            logger.error(f"Critical error in bulk import: {e}")
            # En caso de error crítico, marcar todos los registros como fallidos
            for i, record in enumerate(records):
                if i >= len(result.successful_records + result.failed_records + result.updated_records):
                    result.add_failure(record, batch_start_row + i, f"Critical error: {str(e)}", "critical_error")
        
        result.finalize(start_time)
        logger.info(f"Bulk import completed: {result.get_summary()}")
        
        return result
    
    async def _bulk_create_only(
        self,
        model_class: type,
        model_metadata: ModelMetadata,
        records: List[Dict[str, Any]],
        result: BulkImportResult,
        skip_errors: bool,
        user_id: str,
        unified_timestamp: datetime,
        batch_start_row: int
    ):
        """Implementación optimizada para create_only"""
        
        # 1. Pre-validar duplicados si hay business keys
        if model_metadata.business_key_fields:
            await self._validate_duplicates_batch(
                model_class, model_metadata, records, result, batch_start_row
            )
            
            # Filtrar registros que pasaron validación
            valid_records = []
            valid_indices = []
            for i, record in enumerate(records):
                row_number = batch_start_row + i
                is_failed = any(fr["row_number"] == row_number for fr in result.failed_records)
                if not is_failed:
                    valid_records.append(record)
                    valid_indices.append(i)
            
            if not valid_records:
                return
                
            records = valid_records
        else:
            valid_indices = list(range(len(records)))
        
        # 2. Preparar datos para bulk insert
        bulk_data = []
        for i, record in enumerate(records):
            # Agregar timestamps y metadatos
            prepared_record = record.copy()
            prepared_record.update({
                'id': uuid.uuid4(),
                'created_at': unified_timestamp,
                'updated_at': unified_timestamp
            })
            
            # VALIDACIÓN CRÍTICA: Asegurar que los timestamps asignados tienen timezone
            if 'created_at' in prepared_record:
                if isinstance(prepared_record['created_at'], datetime):
                    if prepared_record['created_at'].tzinfo is None:
                        prepared_record['created_at'] = prepared_record['created_at'].replace(tzinfo=timezone.utc)
                        logger.warning(f"created_at was naive in record {i}, forced to UTC")
                        
            if 'updated_at' in prepared_record:
                if isinstance(prepared_record['updated_at'], datetime):
                    if prepared_record['updated_at'].tzinfo is None:
                        prepared_record['updated_at'] = prepared_record['updated_at'].replace(tzinfo=timezone.utc)
                        logger.warning(f"updated_at was naive in record {i}, forced to UTC")
            
            if user_id and hasattr(model_class, 'created_by_id'):
                try:
                    # Convertir user_id a UUID si es string
                    if isinstance(user_id, str):
                        prepared_record['created_by_id'] = uuid.UUID(user_id)
                    else:
                        prepared_record['created_by_id'] = user_id
                except (ValueError, TypeError):
                    # Si no se puede convertir, usar None
                    prepared_record['created_by_id'] = None
            
            # CRÍTICO: Asegurar que unified_timestamp mantenga timezone antes de conversión
            if 'created_at' in prepared_record and isinstance(prepared_record['created_at'], datetime):
                if prepared_record['created_at'].tzinfo is None:
                    prepared_record['created_at'] = prepared_record['created_at'].replace(tzinfo=timezone.utc)
                    logger.warning(f"Fixed naive created_at in bulk_create record {i}")
            
            if 'updated_at' in prepared_record and isinstance(prepared_record['updated_at'], datetime):
                if prepared_record['updated_at'].tzinfo is None:
                    prepared_record['updated_at'] = prepared_record['updated_at'].replace(tzinfo=timezone.utc)
                    logger.warning(f"Fixed naive updated_at in bulk_create record {i}")
                
            bulk_data.append(prepared_record)
        
        # 3. Ejecutar bulk insert con reintentos
        try:
            await self._execute_with_retry(
                lambda: self._perform_bulk_insert(model_class, bulk_data)
            )
            
            # Marcar todos como exitosos
            for i, record in enumerate(records):
                original_index = valid_indices[i] if model_metadata.business_key_fields else i
                result.add_success(record, batch_start_row + original_index)
                
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            
            if skip_errors:
                # Intentar inserción fila por fila
                await self._fallback_individual_inserts(
                    model_class, records, result, user_id, 
                    unified_timestamp, batch_start_row, valid_indices
                )
            else:
                # Marcar todos como fallidos
                for i, record in enumerate(records):
                    original_index = valid_indices[i] if model_metadata.business_key_fields else i
                    result.add_failure(
                        record, batch_start_row + original_index, 
                        f"Bulk insert failed: {str(e)}", "bulk_insert_error"
                    )
    
    async def _bulk_upsert(
        self,
        model_class: type,
        model_metadata: ModelMetadata,
        records: List[Dict[str, Any]],
        result: BulkImportResult,
        skip_errors: bool,
        user_id: str,
        unified_timestamp: datetime,
        batch_start_row: int
    ):
        """Implementación optimizada para upsert usando PostgreSQL ON CONFLICT"""
        
        if not model_metadata.business_key_fields:
            # Sin business keys, solo crear
            await self._bulk_create_only(
                model_class, model_metadata, records, result,
                skip_errors, user_id, unified_timestamp, batch_start_row
            )
            return
        
        # Preparar datos para upsert
        bulk_data = []
        for i, record in enumerate(records):
            prepared_record = record.copy()
            prepared_record.update({
                'updated_at': unified_timestamp
            })
            
            # VALIDACIÓN CRÍTICA: Asegurar que updated_at tiene timezone
            if 'updated_at' in prepared_record:
                if isinstance(prepared_record['updated_at'], datetime):
                    if prepared_record['updated_at'].tzinfo is None:
                        prepared_record['updated_at'] = prepared_record['updated_at'].replace(tzinfo=timezone.utc)
                        logger.warning(f"updated_at was naive in upsert record {i}, forced to UTC")
            
            # Solo agregar created_at si es nuevo registro
            if 'id' not in prepared_record:
                prepared_record.update({
                    'id': uuid.uuid4(),
                    'created_at': unified_timestamp
                })
                
                # VALIDACIÓN CRÍTICA: Asegurar que created_at tiene timezone
                if 'created_at' in prepared_record:
                    if isinstance(prepared_record['created_at'], datetime):
                        if prepared_record['created_at'].tzinfo is None:
                            prepared_record['created_at'] = prepared_record['created_at'].replace(tzinfo=timezone.utc)
                            logger.warning(f"created_at was naive in upsert record {i}, forced to UTC")
                
            if user_id and hasattr(model_class, 'created_by_id'):
                if 'created_by_id' not in prepared_record:
                    try:
                        # Convertir user_id a UUID si es string
                        if isinstance(user_id, str):
                            prepared_record['created_by_id'] = uuid.UUID(user_id)
                        else:
                            prepared_record['created_by_id'] = user_id
                    except (ValueError, TypeError):
                        prepared_record['created_by_id'] = None
            
            # CRÍTICO: Asegurar que unified_timestamp mantenga timezone antes de conversión
            if 'created_at' in prepared_record and isinstance(prepared_record['created_at'], datetime):
                if prepared_record['created_at'].tzinfo is None:
                    prepared_record['created_at'] = prepared_record['created_at'].replace(tzinfo=timezone.utc)
                    logger.warning(f"Fixed naive created_at in bulk_upsert record {i}")
            
            if 'updated_at' in prepared_record and isinstance(prepared_record['updated_at'], datetime):
                if prepared_record['updated_at'].tzinfo is None:
                    prepared_record['updated_at'] = prepared_record['updated_at'].replace(tzinfo=timezone.utc)
                    logger.warning(f"Fixed naive updated_at in bulk_upsert record {i}")
                    
            bulk_data.append(prepared_record)
        
        try:
            # Ejecutar upsert con PostgreSQL ON CONFLICT
            updated_count = await self._execute_with_retry(
                lambda: self._perform_bulk_upsert(model_class, model_metadata, bulk_data)
            )
            
            # Determinar cuáles fueron actualizados vs creados
            created_count = len(records) - updated_count
            
            for i, record in enumerate(records):
                if i < created_count:
                    result.add_success(record, batch_start_row + i)
                else:
                    result.add_update(record, batch_start_row + i)
                    
        except Exception as e:
            logger.error(f"Bulk upsert failed: {e}")
            
            if skip_errors:
                # Fallback a procesamiento individual
                await self._fallback_individual_upserts(
                    model_class, model_metadata, records, result,
                    user_id, unified_timestamp, batch_start_row
                )
            else:
                for i, record in enumerate(records):
                    result.add_failure(
                        record, batch_start_row + i,
                        f"Bulk upsert failed: {str(e)}", "bulk_upsert_error"
                    )
    
    async def _validate_duplicates_batch(
        self,
        model_class: type,
        model_metadata: ModelMetadata,
        records: List[Dict[str, Any]],
        result: BulkImportResult,
        batch_start_row: int
    ):
        """Validar duplicados en batch usando una sola query"""
        
        if not model_metadata.business_key_fields:
            return
            
        # Extraer valores de business keys
        business_key_values = []
        for record in records:
            key_value = {}
            for key_field in model_metadata.business_key_fields:
                if key_field in record and record[key_field] is not None:
                    key_value[key_field] = record[key_field]
            
            if key_value:
                business_key_values.append(key_value)
        
        if not business_key_values:
            return
        
        # Construir query para verificar existencia
        try:
            conditions = []
            for key_values in business_key_values:
                condition_parts = []
                for key_field, value in key_values.items():
                    condition_parts.append(getattr(model_class, key_field) == value)
                
                if condition_parts:
                    conditions.append(and_(*condition_parts))
            
            if conditions:
                query = select(model_class).where(or_(*conditions))
                existing_result = await self.db.execute(query)
                existing_records = existing_result.scalars().all()
                
                # Crear set de valores existentes para comparación rápida
                existing_keys = set()
                for existing in existing_records:
                    key_tuple = tuple(
                        getattr(existing, key_field) 
                        for key_field in model_metadata.business_key_fields
                    )
                    existing_keys.add(key_tuple)
                
                # Marcar duplicados
                for i, record in enumerate(records):
                    record_key_tuple = tuple(
                        record.get(key_field) 
                        for key_field in model_metadata.business_key_fields
                    )
                    
                    if record_key_tuple in existing_keys:
                        key_field = model_metadata.business_key_fields[0]
                        key_value = record.get(key_field)
                        result.add_failure(
                            record, batch_start_row + i,
                            f"Duplicate value '{key_value}' for field '{key_field}'",
                            "duplicate_key"
                        )
                        
        except Exception as e:
            logger.warning(f"Error validating duplicates: {e}")
            # En caso de error, continuar sin validación
    
    async def _perform_bulk_insert(self, model_class: type, bulk_data: List[Dict[str, Any]]):
        """Ejecutar bulk insert optimizado con validación de tipos y timezone"""
        
        if not bulk_data:
            return
        
        # Filtrar y limpiar datos para evitar campos no válidos
        processed_data = []
        
        # Obtener información de las columnas del modelo para filtrar campos válidos
        try:
            mapper = inspect(model_class)
            valid_columns = set(mapper.columns.keys())
        except Exception as e:
            logger.warning(f"Could not inspect model {model_class.__name__}: {e}")
            # Fallback: usar campos comunes conocidos para Account
            valid_columns = {
                'id', 'code', 'name', 'account_type', 'category', 'description',
                'parent_id', 'level', 'is_active', 'allows_movements', 
                'requires_third_party', 'requires_cost_center', 'allows_reconciliation',
                'balance', 'debit_balance', 'credit_balance', 'notes',
                'created_by_id', 'created_at', 'updated_at'
            }
        
        for i, record in enumerate(bulk_data):
            try:
                # 0. Validación inicial del registro
                is_valid, validation_error = self._validate_record_for_insert(record, model_class)
                if not is_valid:
                    logger.warning(f"Record {i} failed validation: {validation_error}")
                    continue
                
                # 1. Filtrar solo campos válidos del modelo
                filtered_record = {
                    key: value for key, value in record.items() 
                    if key in valid_columns and value is not None
                }
                
                # 2. Convertir timestamps a timezone-aware
                timestamp_converted = self._convert_timestamp_fields(filtered_record, model_class)
                
                # 3. Aplicar conversiones de tipos
                processed_record = self._ensure_correct_data_types(timestamp_converted, model_class)
                
                # 4. Validaciones adicionales para campos críticos
                if 'account_type' in processed_record:
                    # Asegurar que account_type sea un valor válido del enum
                    if isinstance(processed_record['account_type'], str):
                        # Convertir a enum si es necesario
                        try:
                            from app.models.account import AccountType
                            processed_record['account_type'] = AccountType(processed_record['account_type'].lower())
                        except ValueError:
                            logger.warning(f"Invalid account_type in record {i}: {processed_record['account_type']}")
                            continue
                
                # 5. Validar campos requeridos finales
                required_fields = ['code', 'name', 'account_type']
                missing_fields = [field for field in required_fields if field not in processed_record or processed_record[field] is None]
                if missing_fields:
                    logger.warning(f"Record {i} missing required fields after processing: {missing_fields}")
                    continue
                
                processed_data.append(processed_record)
                
            except Exception as e:
                logger.error(f"Error processing record {i} for bulk insert: {e}")
                logger.debug(f"Problematic record: {record}")
                continue
        
        if not processed_data:
            logger.warning("No valid records to insert after processing")
            return
        
        # Dividir en chunks más pequeños para evitar problemas con consultas muy grandes
        chunk_size = 100  # Reducir el tamaño del chunk
        for chunk_start in range(0, len(processed_data), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(processed_data))
            chunk = processed_data[chunk_start:chunk_end]
            
            try:
                # Ejecutar insert para este chunk
                stmt = insert(model_class).values(chunk)
                await self.db.execute(stmt)
                logger.debug(f"Bulk inserted chunk {chunk_start // chunk_size + 1}: {len(chunk)} records")
                
            except Exception as e:
                logger.error(f"Failed to insert chunk {chunk_start // chunk_size + 1}: {e}")
                # Intentar inserción individual para este chunk
                await self._fallback_individual_inserts_chunk(model_class, chunk, chunk_start)
        
        await self.db.commit()
        logger.info(f"Completed bulk insert: {len(processed_data)} records processed")
    
    async def _fallback_individual_inserts_chunk(self, model_class: type, chunk: List[Dict[str, Any]], chunk_start: int):
        """Inserción individual de emergencia para un chunk que falló"""
        for i, record in enumerate(chunk):
            try:
                instance = model_class(**record)
                self.db.add(instance)
                await self.db.flush()  # Flush individual
                logger.debug(f"Individual insert successful for record {chunk_start + i}")
            except Exception as e:
                logger.error(f"Individual insert failed for record {chunk_start + i}: {e}")
                await self.db.rollback()
                continue
    
    def _ensure_correct_data_types(self, record: Dict[str, Any], model_class: type) -> Dict[str, Any]:
        """Asegura que los tipos de datos sean correctos para SQLAlchemy"""
        processed = record.copy()
        
        # Manejar campos especiales conocidos
        for field_name, value in record.items():
            if value is None:
                continue
                
            try:
                # Convertir UUIDs string a UUID objects
                if field_name in ['id', 'created_by_id', 'parent_id'] and isinstance(value, str):
                    try:
                        processed[field_name] = uuid.UUID(value)
                    except (ValueError, TypeError):
                        if field_name == 'id':
                            processed[field_name] = uuid.uuid4()
                        else:
                            processed[field_name] = None
                
                # Asegurar que datetime tenga timezone para campos timestamp
                elif field_name in ['created_at', 'updated_at'] and isinstance(value, datetime):
                    if value.tzinfo is None:
                        processed[field_name] = value.replace(tzinfo=timezone.utc)
                    else:
                        processed[field_name] = value
                
                # Convertir decimales apropiadamente
                elif field_name in ['balance', 'debit_balance', 'credit_balance'] and value is not None:
                    try:
                        processed[field_name] = Decimal(str(value))
                    except (ValueError, TypeError):
                        processed[field_name] = Decimal('0.00')
                
                # Manejar booleanos
                elif field_name in ['is_active', 'allows_movements', 'requires_third_party', 
                                  'requires_cost_center', 'allows_reconciliation']:
                    if isinstance(value, str):
                        processed[field_name] = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        processed[field_name] = bool(value)
                
                # Manejar enteros
                elif field_name == 'level':
                    try:
                        processed[field_name] = int(value)
                    except (ValueError, TypeError):
                        processed[field_name] = 1
                
                # Manejar strings (limpiar espacios en blanco)
                elif field_name in ['code', 'name', 'description', 'notes'] and isinstance(value, str):
                    cleaned_value = value.strip()
                    processed[field_name] = cleaned_value if cleaned_value else None
                
                # Para account_type, asegurar que es un enum válido
                elif field_name == 'account_type':
                    if isinstance(value, str):
                        # Normalizar el valor
                        normalized_value = value.lower().strip()
                        # Mapeo de valores comunes
                        type_mapping = {
                            'activo': 'activo',
                            'asset': 'activo',
                            'pasivo': 'pasivo', 
                            'liability': 'pasivo',
                            'patrimonio': 'patrimonio',
                            'equity': 'patrimonio',
                            'ingreso': 'ingreso',
                            'income': 'ingreso',
                            'revenue': 'ingreso',
                            'gasto': 'gasto',
                            'expense': 'gasto',
                            'costos': 'costos',
                            'cost': 'costos'
                        }
                        processed[field_name] = type_mapping.get(normalized_value, normalized_value)
                    
            except Exception as e:
                logger.warning(f"Error processing field {field_name} with value {value}: {e}")
                # En caso de error, mantener el valor original o usar un default seguro
                if field_name in ['balance', 'debit_balance', 'credit_balance']:
                    processed[field_name] = Decimal('0.00')
                elif field_name in ['is_active', 'allows_movements']:
                    processed[field_name] = True
                elif field_name == 'level':
                    processed[field_name] = 1
        
        return processed
    
    async def _perform_bulk_upsert(
        self, 
        model_class: type, 
        model_metadata: ModelMetadata, 
        bulk_data: List[Dict[str, Any]]
    ) -> int:
        """Ejecutar bulk upsert con PostgreSQL ON CONFLICT y validación de tipos y timezone"""
        
        if not bulk_data:
            return 0
        
        # Procesar cada registro para asegurar tipos correctos y timestamps timezone-aware
        processed_data = []
        for i, record in enumerate(bulk_data):
            
            # DEBUGGING: Log timestamps antes del procesamiento
            if 'created_at' in record:
                logger.debug(f"Upsert Record {i} created_at before processing: {record['created_at']} (tzinfo: {getattr(record['created_at'], 'tzinfo', 'N/A')})")
            if 'updated_at' in record:
                logger.debug(f"Upsert Record {i} updated_at before processing: {record['updated_at']} (tzinfo: {getattr(record['updated_at'], 'tzinfo', 'N/A')})")
            
            # Primero convertir timestamps a timezone-aware
            timestamp_converted = self._convert_timestamp_fields(record, model_class)
            
            # DEBUGGING: Log timestamps después de conversión de timezone
            if 'created_at' in timestamp_converted:
                logger.debug(f"Upsert Record {i} created_at after timestamp conversion: {timestamp_converted['created_at']} (tzinfo: {getattr(timestamp_converted['created_at'], 'tzinfo', 'N/A')})")
            if 'updated_at' in timestamp_converted:
                logger.debug(f"Upsert Record {i} updated_at after timestamp conversion: {timestamp_converted['updated_at']} (tzinfo: {getattr(timestamp_converted['updated_at'], 'tzinfo', 'N/A')})")
                
            # Luego aplicar otras conversiones de tipos
            processed_record = self._ensure_correct_data_types(timestamp_converted, model_class)
            
            # DEBUGGING: Log timestamps después de conversión de tipos
            if 'created_at' in processed_record:
                logger.debug(f"Upsert Record {i} created_at after type conversion: {processed_record['created_at']} (tzinfo: {getattr(processed_record['created_at'], 'tzinfo', 'N/A')})")
            if 'updated_at' in processed_record:
                logger.debug(f"Upsert Record {i} updated_at after type conversion: {processed_record['updated_at']} (tzinfo: {getattr(processed_record['updated_at'], 'tzinfo', 'N/A')})")
                
            processed_data.append(processed_record)
            
        # DEBUGGING: Log final de timestamps antes del upsert
        for i, record in enumerate(processed_data[:3]):  # Solo los primeros 3 para no spamear
            if 'created_at' in record:
                logger.info(f"FINAL Upsert Record {i} created_at: {record['created_at']} (tzinfo: {getattr(record['created_at'], 'tzinfo', 'N/A')})")
            if 'updated_at' in record:
                logger.info(f"FINAL Upsert Record {i} updated_at: {record['updated_at']} (tzinfo: {getattr(record['updated_at'], 'tzinfo', 'N/A')})")
            
        # Crear statement con ON CONFLICT
        stmt = pg_insert(model_class).values(processed_data)
        
        # Configurar ON CONFLICT basado en business keys
        conflict_columns = model_metadata.business_key_fields
        update_dict = {
            key: stmt.excluded[key] 
            for key in processed_data[0].keys() 
            if key not in ['id', 'created_at'] + conflict_columns
        }
        
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns,
            set_=update_dict
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        # PostgreSQL no retorna fácilmente cuántos fueron actualizados vs insertados
        # Por simplicidad, asumimos que todos fueron procesados correctamente
        return 0  # Será ajustado por lógica del llamador
    
    async def _fallback_individual_inserts(
        self,
        model_class: type,
        records: List[Dict[str, Any]],
        result: BulkImportResult,
        user_id: str,
        unified_timestamp: datetime,
        batch_start_row: int,
        valid_indices: List[int]
    ):
        """Fallback a inserciones individuales cuando falla bulk insert"""
        
        for i, record in enumerate(records):
            original_index = valid_indices[i] if valid_indices else i
            row_number = batch_start_row + original_index
            
            try:
                # Preparar registro individual
                prepared_record = record.copy()
                prepared_record.update({
                    'id': uuid.uuid4(),
                    'created_at': unified_timestamp,
                    'updated_at': unified_timestamp
                })
                
                if user_id and hasattr(model_class, 'created_by_id'):
                    prepared_record['created_by_id'] = user_id
                
                # CRÍTICO: Asegurar que unified_timestamp mantenga timezone
                if 'created_at' in prepared_record and isinstance(prepared_record['created_at'], datetime):
                    if prepared_record['created_at'].tzinfo is None:
                        prepared_record['created_at'] = prepared_record['created_at'].replace(tzinfo=timezone.utc)
                
                if 'updated_at' in prepared_record and isinstance(prepared_record['updated_at'], datetime):
                    if prepared_record['updated_at'].tzinfo is None:
                        prepared_record['updated_at'] = prepared_record['updated_at'].replace(tzinfo=timezone.utc)
                
                # Convertir timestamps a timezone-aware antes de crear la instancia
                prepared_record = self._convert_timestamp_fields(prepared_record, model_class)
                prepared_record = self._ensure_correct_data_types(prepared_record, model_class)
                
                # Crear instancia y guardar
                instance = model_class(**prepared_record)
                self.db.add(instance)
                await self.db.commit()
                
                result.add_success(record, row_number)
                
            except Exception as e:
                await self.db.rollback()
                error_type = self._classify_error(e)
                result.add_failure(record, row_number, str(e), error_type)
                
                logger.debug(f"Individual insert failed for row {row_number}: {e}")
    
    async def _fallback_individual_upserts(
        self,
        model_class: type,
        model_metadata: ModelMetadata,
        records: List[Dict[str, Any]],
        result: BulkImportResult,
        user_id: str,
        unified_timestamp: datetime,
        batch_start_row: int
    ):
        """Fallback a upserts individuales"""
        
        for i, record in enumerate(records):
            row_number = batch_start_row + i
            
            try:
                # Buscar registro existente
                business_key_values = {}
                for key_field in model_metadata.business_key_fields:
                    if key_field in record:
                        business_key_values[key_field] = record[key_field]
                
                existing = None
                if business_key_values:
                    query = select(model_class)
                    for key, value in business_key_values.items():
                        query = query.where(getattr(model_class, key) == value)
                    
                    existing_result = await self.db.execute(query)
                    existing = existing_result.scalar_one_or_none()
                
                if existing:
                    # Actualizar
                    update_record = self._convert_timestamp_fields(record, model_class)
                    update_record = self._ensure_correct_data_types(update_record, model_class)
                    
                    for key, value in update_record.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    
                    existing.updated_at = unified_timestamp
                    await self.db.commit()
                    result.add_update(record, row_number)
                    
                else:
                    # Crear
                    prepared_record = record.copy()
                    prepared_record.update({
                        'id': uuid.uuid4(),
                        'created_at': unified_timestamp,
                        'updated_at': unified_timestamp
                    })
                    
                    if user_id and hasattr(model_class, 'created_by_id'):
                        prepared_record['created_by_id'] = user_id
                    
                    # CRÍTICO: Asegurar que unified_timestamp mantenga timezone
                    if 'created_at' in prepared_record and isinstance(prepared_record['created_at'], datetime):
                        if prepared_record['created_at'].tzinfo is None:
                            prepared_record['created_at'] = prepared_record['created_at'].replace(tzinfo=timezone.utc)
                    
                    if 'updated_at' in prepared_record and isinstance(prepared_record['updated_at'], datetime):
                        if prepared_record['updated_at'].tzinfo is None:
                            prepared_record['updated_at'] = prepared_record['updated_at'].replace(tzinfo=timezone.utc)
                    
                    # Convertir timestamps a timezone-aware antes de crear la instancia
                    prepared_record = self._convert_timestamp_fields(prepared_record, model_class)
                    prepared_record = self._ensure_correct_data_types(prepared_record, model_class)
                    
                    instance = model_class(**prepared_record)
                    self.db.add(instance)
                    await self.db.commit()
                    result.add_success(record, row_number)
                    
            except Exception as e:
                await self.db.rollback()
                error_type = self._classify_error(e)
                result.add_failure(record, row_number, str(e), error_type)
    
    async def _execute_with_retry(self, operation, max_retries: Optional[int] = None):
        """Ejecutar operación con reintentos y backoff exponencial"""
        
        max_retries = max_retries or self.retry_attempts
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await operation()
                
            except (IntegrityError, SQLAlchemyError) as e:
                last_exception = e
                
                if attempt < max_retries - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed: {e}")
                    raise e
                    
        # Si llegamos aquí, todos los intentos fallaron
        if last_exception:
            raise last_exception
        else:
            raise Exception("Operation failed after all retry attempts")
    
    def _classify_error(self, error: Exception) -> str:
        """Clasificar tipo de error para reportes"""
        
        error_str = str(error).lower()
        
        if "unique" in error_str or "duplicate" in error_str:
            return "duplicate_key"
        elif "not null" in error_str:
            return "missing_required_field"
        elif "foreign key" in error_str:
            return "invalid_reference"
        elif "check constraint" in error_str:
            return "constraint_violation"
        elif "timeout" in error_str or "deadlock" in error_str:
            return "database_timeout"
        else:
            return "unknown_error"
