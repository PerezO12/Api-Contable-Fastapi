"""
Servicio profesional de importación de datos contables
Soporte para CSV, XLSX, JSON con validaciones empresariales, batch processing y manejo robusto de errores
"""
import asyncio
import csv
import json
import uuid
import io
import base64
import traceback
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Tuple, Union, Sequence
import logging

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account, AccountType, AccountCategory
from app.models.journal_entry import JournalEntry, JournalEntryType
from app.models.user import User
from app.schemas.import_data import (
    ImportConfiguration, ImportRequest, ImportResult, ImportSummary,
    ImportRowResult, ImportError, ImportPreviewResponse, ImportFormat,
    ImportDataType, ImportValidationLevel, AccountImportRow, JournalEntryImportRow,
    JournalEntryLineImportRow, ImportTemplate, ImportTemplateResponse
)
from app.schemas.account import AccountCreate
from app.schemas.journal_entry import JournalEntryCreate, JournalEntryLineCreate
from app.services.account_service import AccountService
from app.services.journal_entry_service import JournalEntryService
from app.utils.exceptions import (
    ImportError as ImportException, AccountValidationError, AccountNotFoundError,
    JournalEntryError, BalanceError
)

# Configurar logging
logger = logging.getLogger(__name__)


class ImportDataService:
    """Servicio profesional para importación de datos contables"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_service = AccountService(db)
        self.journal_service = JournalEntryService(db)
          # Caché para optimizar lookups durante importación
        self._account_cache: Dict[str, Account] = {}
        self._account_type_cache: Dict[str, AccountType] = {}
        self._category_cache: Dict[str, AccountCategory] = {}
    
    def _convert_pandas_records(self, records: list) -> List[Dict[str, Any]]:
        """Convierte records de pandas a formato compatible con tipos"""
        return [{str(k): v for k, v in record.items()} for record in records]
    
    async def preview_import(
        self, 
        file_content: str, 
        filename: str, 
        config: ImportConfiguration,
        preview_rows: int = 10
    ) -> ImportPreviewResponse:
        """
        Preview de importación - analiza el archivo sin importar datos
        """
        try:
            # Detectar formato si no se especifica
            detected_format = self._detect_format(filename, config.format)
            
            # Parsear datos para preview
            preview_data, column_mapping = await self._parse_file_preview(
                file_content, detected_format, config, preview_rows
            )
            
            # Detectar tipo de datos
            detected_data_type = self._detect_data_type(preview_data, config.data_type)
            
            # Validar preview
            validation_errors = await self._validate_preview_data(
                preview_data, detected_data_type, config
            )
            
            # Generar recomendaciones
            recommendations = self._generate_recommendations(
                preview_data, column_mapping, validation_errors
            )
            
            return ImportPreviewResponse(
                detected_format=detected_format,
                detected_data_type=detected_data_type,
                total_rows=len(preview_data),
                preview_data=preview_data,
                column_mapping=column_mapping,
                validation_errors=validation_errors,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error en preview de importación: {str(e)}")
            raise ImportException(f"Error en preview: {str(e)}")
    async def import_data(
        self, 
        file_content: str, 
        filename: str, 
        config: ImportConfiguration,
        user_id: uuid.UUID
    ) -> ImportResult:
        """
        Importación principal de datos con procesamiento por lotes
        """
        import_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        
        # Inicializar resultado fuera del try para que esté disponible en except
        result = ImportResult(
            import_id=import_id,
            configuration=config,
            summary=ImportSummary(
                total_rows=0,
                processed_rows=0,
                successful_rows=0,
                error_rows=0,
                warning_rows=0,
                skipped_rows=0,
                processing_time_seconds=0.0,
                most_common_errors={}
            ),
            row_results=[],
            global_errors=[],
            started_at=started_at,
            status="processing"
        )
        
        try:
            logger.info(f"Iniciando importación {import_id} para usuario {user_id}")
            
            # Parsear archivo completo
            parsed_data = await self._parse_file_complete(file_content, filename, config)
            result.summary.total_rows = len(parsed_data)
            
            # Validación inicial
            if config.validation_level != ImportValidationLevel.PREVIEW:
                # Inicializar caché para optimización
                await self._initialize_cache()
                
                # Procesar en lotes
                batch_size = config.batch_size
                for i in range(0, len(parsed_data), batch_size):
                    batch = parsed_data[i:i + batch_size]
                    batch_results = await self._process_batch(
                        batch, config, user_id, i + 1
                    )
                    result.row_results.extend(batch_results)
                    
                    # Actualizar estadísticas
                    self._update_summary_from_batch(result.summary, batch_results)
                    
                    # Commit por lote para evitar transacciones muy largas
                    if not config.validation_level == ImportValidationLevel.PREVIEW:
                        await self.db.commit()
            
            # Finalizar resultado
            result.completed_at = datetime.now(timezone.utc)
            result.summary.processing_time_seconds = (
                result.completed_at - started_at
            ).total_seconds()
            result.status = "completed"
            
            logger.info(f"Importación {import_id} completada exitosamente")
            return result
            
        except Exception as e:
            logger.error(f"Error en importación {import_id}: {str(e)}\n{traceback.format_exc()}")
            
            # Rollback en caso de error crítico
            await self.db.rollback()
            
            result.status = "failed"
            result.completed_at = datetime.now(timezone.utc)
            result.global_errors.append(ImportError(
                error_code="IMPORT_FAILED",
                error_message=str(e),
                error_type="system",
                severity="error"
            ))
            
            return result
    async def _parse_file_preview(
        self, 
        file_content: str, 
        format: ImportFormat, 
        config: ImportConfiguration,
        preview_rows: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Parsear archivo para preview"""
        
        if format == ImportFormat.CSV:
            return await self._parse_csv_preview(file_content, config, preview_rows)
        elif format == ImportFormat.XLSX:
            return await self._parse_xlsx_preview(file_content, config, preview_rows)
        elif format == ImportFormat.JSON:
            return await self._parse_json_preview(file_content, config, preview_rows)
        else:
            raise ImportException(f"Formato no soportado: {format}")
    
    async def _parse_csv_preview(
        self, 
        file_content: str, 
        config: ImportConfiguration,
        preview_rows: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Parsear CSV para preview"""
        try:
            # Decodificar contenido
            if file_content.startswith('data:'):
                # Si viene como data URL, extraer contenido
                file_content = file_content.split(',')[1]
            
            try:
                decoded_content = base64.b64decode(file_content).decode(config.csv_encoding)
            except:
                # Si no es base64, asumir que es texto plano
                decoded_content = file_content
            
            # Leer CSV
            csv_reader = csv.DictReader(
                io.StringIO(decoded_content),
                delimiter=config.csv_delimiter
            )
            
            preview_data = []
            column_mapping = {}
            
            for i, row in enumerate(csv_reader):
                if i >= preview_rows:
                    break
                    
                # Limpiar datos
                cleaned_row = {k.strip(): v.strip() if v else None for k, v in row.items()}
                preview_data.append(cleaned_row)
                
                # Mapear columnas en la primera fila
                if i == 0:
                    column_mapping = self._generate_column_mapping(
                        list(cleaned_row.keys()), config.data_type
                    )
            
            return preview_data, column_mapping
            
        except Exception as e:
            raise ImportException(f"Error parseando CSV: {str(e)}")
    
    async def _parse_xlsx_preview(
        self, 
        file_content: str, 
        config: ImportConfiguration,
        preview_rows: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Parsear XLSX para preview"""
        try:
            # Decodificar contenido base64
            file_bytes = base64.b64decode(file_content)
            
            # Leer con pandas
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                sheet_name=config.xlsx_sheet_name or 0,
                header=config.xlsx_header_row - 1,
                nrows=preview_rows
            )
            
            # Limpiar nombres de columnas
            df.columns = [str(col).strip() for col in df.columns]            # Convertir a diccionarios con cast explícito para tipos
            records = df.fillna('').to_dict('records')
            preview_data = self._convert_pandas_records(records)
            
            # Mapear columnas
            column_mapping = self._generate_column_mapping(
                list(df.columns), config.data_type
            )
            
            return preview_data, column_mapping
            
        except Exception as e:
            raise ImportException(f"Error parseando XLSX: {str(e)}")
    
    async def _parse_json_preview(
        self, 
        file_content: str, 
        config: ImportConfiguration,
        preview_rows: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Parsear JSON para preview"""
        try:
            # Decodificar si es base64
            try:
                decoded_content = base64.b64decode(file_content).decode('utf-8')
            except:
                decoded_content = file_content
            
            # Parsear JSON
            json_data = json.loads(decoded_content)
            
            # Extraer datos según estructura
            if isinstance(json_data, list):
                preview_data = json_data[:preview_rows]
            elif isinstance(json_data, dict):
                # Buscar array principal en el JSON
                for key, value in json_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        preview_data = value[:preview_rows]
                        break
                else:
                    preview_data = [json_data]
            else:
                raise ImportException("Estructura JSON no soportada")
            
            # Mapear columnas
            if preview_data:
                columns = list(preview_data[0].keys())
                column_mapping = self._generate_column_mapping(columns, config.data_type)
            else:
                column_mapping = {}
            
            return preview_data, column_mapping
            
        except json.JSONDecodeError as e:
            raise ImportException(f"JSON inválido: {str(e)}")
        except Exception as e:
            raise ImportException(f"Error parseando JSON: {str(e)}")
    
    async def _parse_file_complete(
        self, 
        file_content: str, 
        filename: str, 
        config: ImportConfiguration
    ) -> List[Dict[str, Any]]:
        """Parsear archivo completo para importación"""
        
        format = self._detect_format(filename, config.format)
        
        if format == ImportFormat.CSV:
            return await self._parse_csv_complete(file_content, config)
        elif format == ImportFormat.XLSX:
            return await self._parse_xlsx_complete(file_content, config)
        elif format == ImportFormat.JSON:
            return await self._parse_json_complete(file_content, config)
        else:
            raise ImportException(f"Formato no soportado: {format}")
    
    async def _parse_csv_complete(
        self, 
        file_content: str, 
        config: ImportConfiguration
    ) -> List[Dict[str, Any]]:
        """Parsear CSV completo"""
        try:
            # Decodificar contenido
            try:
                decoded_content = base64.b64decode(file_content).decode(config.csv_encoding)
            except:
                decoded_content = file_content
            
            # Leer CSV
            csv_reader = csv.DictReader(
                io.StringIO(decoded_content),
                delimiter=config.csv_delimiter
            )
            
            data = []
            for i, row in enumerate(csv_reader):
                # Limpiar y agregar número de fila
                cleaned_row = {k.strip(): v.strip() if v else None for k, v in row.items()}
                cleaned_row['row_number'] = i + 2  # +2 porque incluye header y es 1-indexed
                data.append(cleaned_row)
            
            return data
            
        except Exception as e:
            raise ImportException(f"Error parseando CSV completo: {str(e)}")
    
    async def _parse_xlsx_complete(
        self, 
        file_content: str, 
        config: ImportConfiguration
    ) -> List[Dict[str, Any]]:
        """Parsear XLSX completo"""
        try:
            file_bytes = base64.b64decode(file_content)
            
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                sheet_name=config.xlsx_sheet_name or 0,
                header=config.xlsx_header_row - 1
            )
            
            # Limpiar nombres de columnas
            df.columns = [str(col).strip() for col in df.columns]
            
            # Agregar número de fila
            df['row_number'] = range(config.xlsx_header_row + 1, len(df) + config.xlsx_header_row + 1)            # Convertir a diccionarios con cast explícito para tipos
            records = df.fillna('').to_dict('records')
            return self._convert_pandas_records(records)
            
        except Exception as e:
            raise ImportException(f"Error parseando XLSX completo: {str(e)}")
    
    async def _parse_json_complete(
        self, 
        file_content: str, 
        config: ImportConfiguration
    ) -> List[Dict[str, Any]]:
        """Parsear JSON completo"""
        try:
            try:
                decoded_content = base64.b64decode(file_content).decode('utf-8')
            except:
                decoded_content = file_content
            
            json_data = json.loads(decoded_content)
            
            # Extraer datos
            if isinstance(json_data, list):
                data = json_data
            elif isinstance(json_data, dict):
                for key, value in json_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        data = value
                        break
                else:
                    data = [json_data]
            else:
                raise ImportException("Estructura JSON no soportada")
            
            # Agregar número de fila
            for i, item in enumerate(data):
                item['row_number'] = i + 1
            
            return data
            
        except Exception as e:
            raise ImportException(f"Error parseando JSON completo: {str(e)}")
    
    async def _process_batch(
        self, 
        batch: List[Dict[str, Any]], 
        config: ImportConfiguration,
        user_id: uuid.UUID,
        batch_start_row: int
    ) -> List[ImportRowResult]:
        """Procesar un lote de datos"""
        
        batch_results = []
        
        for i, row_data in enumerate(batch):
            row_number = row_data.get('row_number', batch_start_row + i)
            
            try:
                if config.data_type == ImportDataType.ACCOUNTS:
                    result = await self._process_account_row(row_data, config, user_id)
                elif config.data_type == ImportDataType.JOURNAL_ENTRIES:
                    result = await self._process_journal_entry_row(row_data, config, user_id)
                else:
                    raise ImportException(f"Tipo de dato no soportado: {config.data_type}")
                
                result.row_number = row_number
                batch_results.append(result)
                
            except Exception as e:
                logger.error(f"Error procesando fila {row_number}: {str(e)}")
                
                error_result = ImportRowResult(
                    row_number=row_number,
                    status="error",
                    errors=[ImportError(
                        row_number=row_number,
                        error_code="PROCESSING_ERROR",
                        error_message=str(e),
                        error_type="system",
                        severity="error"
                    )]
                )
                batch_results.append(error_result)
                
                # Decidir si continuar según configuración
                if not config.continue_on_error:
                    break
        
        return batch_results
    
    async def _process_account_row(
        self, 
        row_data: Dict[str, Any], 
        config: ImportConfiguration,
        user_id: uuid.UUID
    ) -> ImportRowResult:
        """Procesar una fila de cuenta"""
        
        try:
            # Validar y mapear datos
            account_data = AccountImportRow(**row_data)
            
            # Verificar si la cuenta ya existe
            existing_account = await self.account_service.get_account_by_code(account_data.code)
            
            if existing_account:
                if config.skip_duplicates:
                    return ImportRowResult(
                        row_number=account_data.row_number or 0,
                        status="skipped",
                        entity_code=account_data.code,
                        warnings=[ImportError(
                            error_code="DUPLICATE_SKIPPED",
                            error_message=f"Cuenta {account_data.code} ya existe",
                            error_type="business",
                            severity="warning"
                        )]
                    )
                elif config.update_existing:
                    # TODO: Implementar actualización
                    return ImportRowResult(
                        row_number=account_data.row_number or 0,
                        status="warning",
                        entity_code=account_data.code,
                        warnings=[ImportError(
                            error_code="UPDATE_NOT_IMPLEMENTED",
                            error_message="Actualización de cuentas existentes no implementada",
                            error_type="business",
                            severity="warning"
                        )]
                    )
                else:
                    return ImportRowResult(
                        row_number=account_data.row_number or 0,
                        status="error",
                        entity_code=account_data.code,
                        errors=[ImportError(
                            error_code="DUPLICATE_ACCOUNT",
                            error_message=f"Cuenta {account_data.code} ya existe",
                            error_type="business",
                            severity="error"
                        )]
                    )
            
            # Resolver cuenta padre si se especifica
            parent_id = None
            if account_data.parent_code:
                parent_account = await self.account_service.get_account_by_code(account_data.parent_code)
                if not parent_account:
                    return ImportRowResult(
                        row_number=account_data.row_number or 0,
                        status="error",
                        entity_code=account_data.code,
                        errors=[ImportError(
                            error_code="PARENT_NOT_FOUND",
                            error_message=f"Cuenta padre {account_data.parent_code} no encontrada",
                            error_type="business",
                            severity="error"
                        )]
                    )
                parent_id = parent_account.id
            
            # Crear la cuenta
            account_create = AccountCreate(
                code=account_data.code,
                name=account_data.name,
                description=account_data.description,
                account_type=AccountType(account_data.account_type),
                category=AccountCategory(account_data.category) if account_data.category else None,
                parent_id=parent_id,
                is_active=account_data.is_active,
                allows_movements=account_data.allows_movements,
                requires_third_party=account_data.requires_third_party,
                requires_cost_center=account_data.requires_cost_center,
                notes=account_data.notes
            )
            
            if config.validation_level != ImportValidationLevel.PREVIEW:
                new_account = await self.account_service.create_account(account_create, user_id)
                
                return ImportRowResult(
                    row_number=account_data.row_number or 0,
                    status="success",
                    entity_id=new_account.id,
                    entity_code=new_account.code
                )
            else:
                return ImportRowResult(
                    row_number=account_data.row_number or 0,
                    status="success",
                    entity_code=account_data.code
                )
                
        except Exception as e:
            return ImportRowResult(
                row_number=row_data.get('row_number', 0),
                status="error",
                errors=[ImportError(
                    error_code="ACCOUNT_CREATION_ERROR",
                    error_message=str(e),
                    error_type="validation",
                    severity="error"
                )]
            )
    
    async def _process_journal_entry_row(
        self, 
        row_data: Dict[str, Any], 
        config: ImportConfiguration,
        user_id: uuid.UUID
    ) -> ImportRowResult:
        """Procesar una fila de asiento contable"""
        
        try:
            # Validar y mapear datos
            entry_data = JournalEntryImportRow(**row_data)
            
            # Validar que las cuentas existan
            lines_create = []
            for line in entry_data.lines:
                account = await self._get_account_by_code_cached(line.account_code)
                if not account:
                    return ImportRowResult(
                        row_number=entry_data.row_number or 0,
                        status="error",
                        errors=[ImportError(
                            error_code="ACCOUNT_NOT_FOUND",
                            error_message=f"Cuenta {line.account_code} no encontrada",
                            error_type="business",
                            severity="error"
                        )]
                    )
                
                line_create = JournalEntryLineCreate(
                    account_id=account.id,
                    description=line.description,
                    debit_amount=line.debit_amount or Decimal('0'),
                    credit_amount=line.credit_amount or Decimal('0'),
                    third_party=line.third_party,
                    cost_center=line.cost_center,
                    reference=line.reference
                )
                lines_create.append(line_create)
            
            # Crear el asiento
            journal_create = JournalEntryCreate(
                entry_date=entry_data.entry_date,
                reference=entry_data.reference,
                description=entry_data.description,
                entry_type=JournalEntryType(entry_data.entry_type),
                notes=entry_data.notes,
                lines=lines_create
            )
            
            if config.validation_level != ImportValidationLevel.PREVIEW:
                new_entry = await self.journal_service.create_journal_entry(journal_create, user_id)
                
                return ImportRowResult(
                    row_number=entry_data.row_number or 0,
                    status="success",
                    entity_id=new_entry.id,
                    entity_code=new_entry.number
                )
            else:
                return ImportRowResult(
                    row_number=entry_data.row_number or 0,
                    status="success",
                    entity_code=entry_data.reference or "PREVIEW"
                )
                
        except Exception as e:
            return ImportRowResult(
                row_number=row_data.get('row_number', 0),
                status="error",
                errors=[ImportError(
                    error_code="JOURNAL_ENTRY_CREATION_ERROR",
                    error_message=str(e),
                    error_type="validation",
                    severity="error"
                )]
            )
    
    async def _initialize_cache(self):
        """Inicializar caché para optimización"""
        # Cargar todas las cuentas en caché
        accounts = await self.account_service.get_accounts(limit=10000)
        self._account_cache = {account.code: account for account in accounts}
        
        logger.info(f"Caché inicializado con {len(self._account_cache)} cuentas")
    
    async def _get_account_by_code_cached(self, code: str) -> Optional[Account]:
        """Obtener cuenta por código usando caché"""
        if code in self._account_cache:
            return self._account_cache[code]
        
        # Si no está en caché, buscar en BD y agregar al caché
        account = await self.account_service.get_account_by_code(code)
        if account:
            self._account_cache[code] = account
        
        return account
    
    def _detect_format(self, filename: str, declared_format: ImportFormat) -> ImportFormat:
        """Detectar formato de archivo"""
        if declared_format != ImportFormat.CSV:  # Si se declara específicamente
            return declared_format
        
        # Detectar por extensión
        extension = filename.lower().split('.')[-1]
        
        if extension in ['csv', 'txt']:
            return ImportFormat.CSV
        elif extension in ['xlsx', 'xls']:
            return ImportFormat.XLSX
        elif extension in ['json']:
            return ImportFormat.JSON
        else:
            return declared_format  # Usar el declarado como fallback
    
    def _detect_data_type(
        self, 
        preview_data: List[Dict[str, Any]], 
        declared_type: ImportDataType
    ) -> ImportDataType:
        """Detectar tipo de datos basado en las columnas"""
        if declared_type != ImportDataType.MIXED:
            return declared_type
        
        if not preview_data:
            return declared_type
        
        columns = set(preview_data[0].keys())
        
        # Columnas típicas de cuentas
        account_columns = {'code', 'name', 'account_type', 'parent_code'}
        
        # Columnas típicas de asientos
        entry_columns = {'entry_date', 'description', 'lines', 'account_code', 'debit_amount', 'credit_amount'}
        
        account_score = len(columns.intersection(account_columns))
        entry_score = len(columns.intersection(entry_columns))
        
        if account_score > entry_score:
            return ImportDataType.ACCOUNTS
        elif entry_score > account_score:
            return ImportDataType.JOURNAL_ENTRIES
        else:
            return declared_type
    
    def _generate_column_mapping(
        self, 
        columns: List[str], 
        data_type: ImportDataType
    ) -> Dict[str, str]:
        """Generar mapeo de columnas basado en nombres comunes"""
        
        mapping = {}
        
        # Mapeos comunes para cuentas
        if data_type == ImportDataType.ACCOUNTS:
            column_map = {
                'code': ['code', 'codigo', 'account_code', 'codigo_cuenta'],
                'name': ['name', 'nombre', 'account_name', 'nombre_cuenta'],
                'account_type': ['account_type', 'tipo_cuenta', 'type', 'tipo'],
                'category': ['category', 'categoria', 'account_category'],
                'parent_code': ['parent_code', 'codigo_padre', 'parent', 'padre'],
                'description': ['description', 'descripcion', 'desc'],
                'is_active': ['is_active', 'active', 'activa', 'activo'],
                'allows_movements': ['allows_movements', 'permite_movimientos', 'movements']
            }
        else:
            # Mapeos para asientos
            column_map = {
                'entry_date': ['entry_date', 'fecha', 'date', 'fecha_asiento'],
                'reference': ['reference', 'referencia', 'ref'],
                'description': ['description', 'descripcion', 'desc'],
                'account_code': ['account_code', 'codigo_cuenta', 'code'],
                'debit_amount': ['debit_amount', 'debito', 'debe', 'debit'],
                'credit_amount': ['credit_amount', 'credito', 'haber', 'credit']
            }
        
        # Buscar coincidencias
        for standard_name, variants in column_map.items():
            for col in columns:
                if col.lower().strip() in [v.lower() for v in variants]:
                    mapping[col] = standard_name
                    break
        
        return mapping
    
    async def _validate_preview_data(
        self, 
        preview_data: List[Dict[str, Any]], 
        data_type: ImportDataType,
        config: ImportConfiguration
    ) -> List[ImportError]:
        """Validar datos de preview"""
        
        errors = []
        
        if not preview_data:
            errors.append(ImportError(
                error_code="NO_DATA",
                error_message="No se encontraron datos en el archivo",
                error_type="validation",
                severity="error"
            ))
            return errors
        
        # Validar columnas requeridas
        required_columns = self._get_required_columns(data_type)
        available_columns = set(preview_data[0].keys())
        
        missing_columns = required_columns - available_columns
        if missing_columns:
            errors.append(ImportError(
                error_code="MISSING_COLUMNS",
                error_message=f"Columnas requeridas faltantes: {', '.join(missing_columns)}",
                error_type="validation",
                severity="error"
            ))
        
        return errors
    
    def _get_required_columns(self, data_type: ImportDataType) -> set:
        """Obtener columnas requeridas según el tipo de datos"""
        
        if data_type == ImportDataType.ACCOUNTS:
            return {'code', 'name', 'account_type'}
        elif data_type == ImportDataType.JOURNAL_ENTRIES:
            return {'entry_date', 'description', 'account_code'}
        else:
            return set()
    
    def _generate_recommendations(
        self, 
        preview_data: List[Dict[str, Any]], 
        column_mapping: Dict[str, str],
        validation_errors: List[ImportError]
    ) -> List[str]:
        """Generar recomendaciones para la importación"""
        
        recommendations = []
        
        if len(validation_errors) > 0:
            recommendations.append("Corrija los errores de validación antes de proceder")
        
        if len(column_mapping) < 3:
            recommendations.append("Verifique que las columnas del archivo coincidan con los campos esperados")
        
        if len(preview_data) > 1000:
            recommendations.append("Considere procesar el archivo en lotes más pequeños para mejor rendimiento")
        
        return recommendations
    
    def _update_summary_from_batch(
        self, 
        summary: ImportSummary, 
        batch_results: List[ImportRowResult]
    ):
        """Actualizar resumen con resultados del lote"""
        
        for result in batch_results:
            summary.processed_rows += 1
            
            if result.status == "success":
                summary.successful_rows += 1
            elif result.status == "error":
                summary.error_rows += 1
            elif result.status == "warning":
                summary.warning_rows += 1
            elif result.status == "skipped":
                summary.skipped_rows += 1
            
            # Contar errores comunes
            for error in result.errors:
                error_code = error.error_code
                summary.most_common_errors[error_code] = summary.most_common_errors.get(error_code, 0) + 1
    
    async def get_import_templates(self) -> ImportTemplateResponse:
        """Obtener templates de importación disponibles"""
        
        templates = [
            ImportTemplate(
                data_type=ImportDataType.ACCOUNTS,
                format=ImportFormat.CSV,
                required_columns=['code', 'name', 'account_type'],
                optional_columns=['category', 'parent_code', 'description', 'is_active', 'allows_movements'],
                column_descriptions={
                    'code': 'Código único de la cuenta (ej: 1001)',
                    'name': 'Nombre de la cuenta (ej: Caja)',
                    'account_type': 'Tipo: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS',
                    'category': 'Categoría específica del tipo de cuenta',
                    'parent_code': 'Código de la cuenta padre (opcional)',
                    'description': 'Descripción detallada (opcional)'
                },
                sample_data=[
                    {
                        'code': '1001',
                        'name': 'Caja',
                        'account_type': 'ACTIVO',
                        'category': 'ACTIVO_CORRIENTE',
                        'description': 'Dinero en efectivo'
                    },
                    {
                        'code': '2001',
                        'name': 'Proveedores',
                        'account_type': 'PASIVO',
                        'category': 'PASIVO_CORRIENTE',
                        'description': 'Cuentas por pagar a proveedores'
                    }
                ],
                validation_rules=[
                    'El código debe ser único',
                    'El tipo de cuenta debe ser válido',
                    'Si especifica cuenta padre, debe existir previamente'
                ]
            ),
            ImportTemplate(
                data_type=ImportDataType.JOURNAL_ENTRIES,
                format=ImportFormat.CSV,
                required_columns=['entry_date', 'description', 'account_code', 'debit_amount', 'credit_amount'],
                optional_columns=['reference', 'entry_type', 'third_party', 'cost_center', 'notes'],
                column_descriptions={
                    'entry_date': 'Fecha del asiento (YYYY-MM-DD)',
                    'description': 'Descripción del asiento',
                    'account_code': 'Código de la cuenta contable',
                    'debit_amount': 'Monto débito (usar 0 si es crédito)',
                    'credit_amount': 'Monto crédito (usar 0 si es débito)',
                    'reference': 'Referencia externa (opcional)'
                },
                sample_data=[
                    {
                        'entry_date': '2024-01-15',
                        'description': 'Venta de mercadería',
                        'account_code': '1001',
                        'debit_amount': '1000.00',
                        'credit_amount': '0.00'
                    },
                    {
                        'entry_date': '2024-01-15',
                        'description': 'Venta de mercadería',
                        'account_code': '4001',
                        'debit_amount': '0.00',
                        'credit_amount': '1000.00'
                    }
                ],
                validation_rules=[
                    'Los asientos deben estar balanceados (débitos = créditos)',
                    'Cada asiento debe tener mínimo 2 líneas',
                    'Las cuentas deben existir previamente',
                    'Una línea debe tener monto en débito O crédito, no ambos'
                ]
            )
        ]
        
        return ImportTemplateResponse(
            templates=templates,
            supported_formats=[ImportFormat.CSV, ImportFormat.XLSX, ImportFormat.JSON],
            supported_data_types=[ImportDataType.ACCOUNTS, ImportDataType.JOURNAL_ENTRIES]
        )
