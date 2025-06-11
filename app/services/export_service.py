"""
Servicio de exportación genérica de datos
"""
import io
import csv
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import uuid
from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.export_generic import (
    ExportRequest, ExportResponse, ExportMetadata, ExportError,
    ExportFormat, TableName, ExportFilter, ColumnInfo,
    TableSchema, AvailableTablesResponse
)
from app.models.base import Base
from app.models import (
    User, Account, JournalEntry, JournalEntryLine,
    AuditLog, UserSession, ChangeTracking,
    SystemConfiguration, CompanyInfo, NumberSequence
)


class ExportService:
    """Servicio para exportación genérica de datos de la base de datos"""
    
    # Mapeo de nombres de tabla a modelos SQLAlchemy
    TABLE_MODEL_MAPPING = {
        TableName.USERS: User,
        TableName.ACCOUNTS: Account,
        TableName.JOURNAL_ENTRIES: JournalEntry,
        TableName.JOURNAL_ENTRY_LINES: JournalEntryLine,
        TableName.AUDIT_LOGS: AuditLog,
        TableName.USER_SESSIONS: UserSession,
        TableName.CHANGE_TRACKING: ChangeTracking,
        TableName.SYSTEM_CONFIGURATION: SystemConfiguration,
        TableName.COMPANY_INFO: CompanyInfo,
        TableName.NUMBER_SEQUENCES: NumberSequence,
    }
    
    # Nombres amigables para las tablas
    TABLE_DISPLAY_NAMES = {
        TableName.USERS: "Usuarios",
        TableName.ACCOUNTS: "Plan de Cuentas",
        TableName.JOURNAL_ENTRIES: "Asientos Contables",
        TableName.JOURNAL_ENTRY_LINES: "Líneas de Asientos",
        TableName.AUDIT_LOGS: "Logs de Auditoría",
        TableName.USER_SESSIONS: "Sesiones de Usuario",
        TableName.CHANGE_TRACKING: "Tracking de Cambios",
        TableName.SYSTEM_CONFIGURATION: "Configuración del Sistema",
        TableName.COMPANY_INFO: "Información de la Empresa",
        TableName.NUMBER_SEQUENCES: "Secuencias de Numeración",
    }
    
    # Campos confidenciales que deben omitirse en las exportaciones
    SENSITIVE_FIELDS = {
        TableName.USERS: [
            'hashed_password',
            'password_hash',
            'password',
            'salt',
            'secret_key',
            'private_key',
            'api_key',
            'token'
        ],
        TableName.USER_SESSIONS: [
            'session_token',
            'refresh_token',
            'access_token'
        ],
        TableName.SYSTEM_CONFIGURATION: [
            'secret_value',
            'password',
            'api_secret',
            'private_key'
        ]
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_available_tables(self) -> AvailableTablesResponse:
        """Obtiene información de todas las tablas disponibles para exportación"""
        tables = []
        for table_name in TableName:
            try:
                model = self.TABLE_MODEL_MAPPING[table_name]
                columns = self._get_table_columns(model, table_name)
                total_records = self.db.query(model).count()
                
                table_schema = TableSchema(
                    table_name=table_name.value,
                    display_name=self.TABLE_DISPLAY_NAMES[table_name],
                    description=f"Tabla {self.TABLE_DISPLAY_NAMES[table_name]}",
                    available_columns=columns,
                    total_records=total_records
                )
                tables.append(table_schema)
            except Exception as e:
                # Log error but continue with other tables
                print(f"Error getting info for table {table_name}: {e}")
        
        return AvailableTablesResponse(
            tables=tables,
            total_tables=len(tables)
        )
    def get_table_schema(self, table_name: TableName) -> TableSchema:
        """Obtiene el schema de una tabla específica"""
        model = self.TABLE_MODEL_MAPPING[table_name]
        columns = self._get_table_columns(model)
        total_records = self.db.query(model).count()
        
        # Obtener datos de muestra
        sample_data = None
        try:
            sample_rows = self.db.query(model).limit(5).all()
            sample_data = [self._model_to_dict(row, table_name=table_name) for row in sample_rows]
        except Exception:
            pass
        
        return TableSchema(
            table_name=table_name.value,
            display_name=self.TABLE_DISPLAY_NAMES[table_name],
            description=f"Tabla {self.TABLE_DISPLAY_NAMES[table_name]}",
            available_columns=columns,
            total_records=total_records,
            sample_data=sample_data
        )
    
    def export_data(self, request: ExportRequest, user_id: uuid.UUID) -> ExportResponse:
        """Exporta datos según los parámetros especificados"""
        try:
            # Obtener modelo de la tabla
            model = self.TABLE_MODEL_MAPPING[request.table_name]
            
            # Construir query con filtros
            query = self._build_query(model, request.filters)
            
            # Obtener datos
            data = query.all()
              # Convertir a diccionarios
            dict_data = [self._model_to_dict(row, request.columns, table_name=request.table_name) for row in data]
            
            # Generar archivo según formato
            file_content, content_type = self._generate_file(
                dict_data, request.export_format, request.file_name or f"{request.table_name.value}_export"
            )
            
            # Crear metadatos
            metadata = ExportMetadata(
                export_date=datetime.utcnow(),
                user_id=user_id,
                table_name=request.table_name.value,
                total_records=self.db.query(model).count(),
                exported_records=len(dict_data),
                filters_applied=request.filters.model_dump(exclude_none=True),
                format=request.export_format,
                file_size_bytes=len(file_content) if isinstance(file_content, (str, bytes)) else None,
                columns_exported=list(dict_data[0].keys()) if dict_data else []
            )
            
            # Generar nombre de archivo
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_name = f"{request.file_name or request.table_name.value}_{timestamp}.{request.export_format.value}"
            
            return ExportResponse(
                file_name=file_name,
                file_content=file_content,
                content_type=content_type,
                metadata=metadata,
                            success=True,
                message=f"Exportación exitosa: {len(dict_data)} registros"
            )
            
        except Exception as e:
            raise Exception(f"Error en la exportación: {str(e)}")
    def _get_table_columns(self, model, table_name: Optional[TableName] = None) -> List[ColumnInfo]:
        """Obtiene información de las columnas de una tabla"""
        columns = []
        inspector = inspect(model)
        
        for column in inspector.columns:
            # Determinar tipo de dato
            data_type = "string"
            if "INTEGER" in str(column.type) or "DECIMAL" in str(column.type) or "NUMERIC" in str(column.type):
                data_type = "number"
            elif "BOOLEAN" in str(column.type):
                data_type = "boolean"
            elif "DATE" in str(column.type) or "TIMESTAMP" in str(column.type):
                data_type = "date"
            
            columns.append(ColumnInfo(
                name=column.name,
                data_type=data_type,
                format=None,
                include=True
            ))
        
        # Filtrar columnas sensibles si se especifica la tabla
        if table_name:
            columns = self._filter_sensitive_columns(columns, table_name)
        
        return columns
    
    def _build_query(self, model, filters: ExportFilter):
        """Construye query con filtros aplicados"""
        query = self.db.query(model)
        
        # Filtro por IDs específicos
        if filters.ids:
            query = query.filter(model.id.in_(filters.ids))
        
        # Filtro por rango de fechas
        if filters.date_from and hasattr(model, 'created_at'):
            query = query.filter(model.created_at >= filters.date_from)
        
        if filters.date_to and hasattr(model, 'created_at'):
            query = query.filter(model.created_at <= filters.date_to)
        
        # Filtro por registros activos
        if filters.active_only is not None and hasattr(model, 'is_active'):
            query = query.filter(model.is_active == filters.active_only)
        
        # Filtros personalizados
        if filters.custom_filters:
            for field, value in filters.custom_filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)
          # Aplicar offset y limit
        if filters.offset:
            query = query.offset(filters.offset)
        
        if filters.limit:
            query = query.limit(filters.limit)
        
        return query
    
    def _model_to_dict(self, model_instance, selected_columns: Optional[List[ColumnInfo]] = None, table_name: Optional[TableName] = None) -> Dict[str, Any]:
        """Convierte una instancia de modelo SQLAlchemy a diccionario"""
        result = {}
        
        # Obtener todas las columnas si no se especifican
        if selected_columns is None:
            columns_to_include = [c.name for c in inspect(model_instance.__class__).columns]
        else:
            columns_to_include = [c.name for c in selected_columns if c.include]
        
        # Filtrar campos sensibles si se especifica la tabla
        if table_name and table_name in self.SENSITIVE_FIELDS:
            sensitive_fields = self.SENSITIVE_FIELDS[table_name]
            columns_to_include = [col for col in columns_to_include if col not in sensitive_fields]
        
        for column_name in columns_to_include:
            try:
                value = getattr(model_instance, column_name)
                
                # Convertir tipos especiales a formatos serializables
                if isinstance(value, Decimal):
                    result[column_name] = float(value)
                elif isinstance(value, datetime):
                    result[column_name] = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    result[column_name] = str(value)
                elif hasattr(value, '__dict__'):  # Relaciones
                    result[column_name] = str(value)
                else:
                    result[column_name] = value
                    
            except AttributeError:
                result[column_name] = None
        
        return result
    
    def _filter_sensitive_columns(self, columns: List[ColumnInfo], table_name: TableName) -> List[ColumnInfo]:
        """Filtra columnas sensibles para una tabla específica"""
        if table_name not in self.SENSITIVE_FIELDS:
            return columns
        
        sensitive_fields = self.SENSITIVE_FIELDS[table_name]
        filtered_columns = []
        
        for column in columns:
            if column.name not in sensitive_fields:
                filtered_columns.append(column)
            else:
                # Agregar una nota sobre campo omitido
                print(f"Campo sensible omitido en exportación: {column.name}")
        
        return filtered_columns
    
    def _generate_file(self, data: List[Dict[str, Any]], format: ExportFormat, base_filename: str) -> tuple[Union[str, bytes], str]:
        """Genera el archivo en el formato especificado"""
        
        if format == ExportFormat.JSON:
            return self._generate_json(data), "application/json"
        elif format == ExportFormat.CSV:
            return self._generate_csv(data), "text/csv"
        elif format == ExportFormat.XLSX:
            return self._generate_xlsx(data), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    def _generate_json(self, data: List[Dict[str, Any]]) -> str:
        """Genera archivo JSON"""
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    def _generate_csv(self, data: List[Dict[str, Any]]) -> str:
        """Genera archivo CSV"""
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    
    def _generate_xlsx(self, data: List[Dict[str, Any]]) -> bytes:
        """Genera archivo Excel"""
        if not data:
            return b""
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        
        return output.getvalue()
