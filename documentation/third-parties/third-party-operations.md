# Operaciones Masivas de Terceros

El sistema de operaciones masivas permite gestionar grandes volúmenes de datos de terceros de manera eficiente y segura. Incluye funcionalidades de importación, actualización masiva, sincronización y operaciones de mantenimiento que optimizan la administración de terceros a gran escala.

## Características de las Operaciones Masivas

### ✅ **Importación Masiva**
- Soporte para múltiples formatos (CSV, XLSX, JSON)
- Validación automática durante la importación
- Manejo de errores y reportes detallados
- Procesamiento en lotes para grandes volúmenes

### ✅ **Actualización Masiva**
- Filtros avanzados para selección de terceros
- Actualización segura con validaciones
- Rollback automático en caso de errores
- Auditoría completa de cambios realizados

### ✅ **Sincronización con Sistemas Externos**
- Conectores para ERPs y CRMs
- Mapeo flexible de campos
- Resolución automática de conflictos
- Scheduling de sincronizaciones automáticas

### ✅ **Operaciones de Mantenimiento**
- Limpieza de datos duplicados
- Normalización de información
- Actualización de estados masiva
- Optimización de bases de datos

## Importación Masiva de Terceros

### **Formatos Soportados**

#### **1. Formato CSV**
```csv
code,name,document_type,document_number,third_party_type,email,phone,address,city,country,payment_terms,credit_limit,is_active
CUST-001,Cliente Ejemplo S.A.S.,NIT,900123456-1,CUSTOMER,cliente@ejemplo.com,+57 300 123 4567,Calle 123 #45-67,Bogotá,Colombia,30 días,5000000.00,true
PROV-001,Proveedor Test Ltda.,NIT,800987654-2,SUPPLIER,provee@test.com,+57 301 987 6543,Carrera 45 #12-34,Medellín,Colombia,15 días,2000000.00,true
```

#### **2. Formato Excel**
- Hojas separadas por tipo de tercero
- Validaciones en celdas
- Formatos de datos predefinidos
- Plantillas descargables

#### **3. Formato JSON**
```json
{
  "third_parties": [
    {
      "code": "CUST-001",
      "name": "Cliente Ejemplo S.A.S.",
      "document_type": "NIT",
      "document_number": "900123456-1",
      "third_party_type": "CUSTOMER",
      "business_type": "Tecnología",
      "email": "cliente@ejemplo.com",
      "phone": "+57 300 123 4567",
      "address": "Calle 123 #45-67",
      "city": "Bogotá",
      "country": "Colombia",
      "payment_terms": "30 días",
      "credit_limit": 5000000.00,
      "is_active": true,
      "custom_fields": {
        "industry": "Software",
        "account_manager": "Juan Pérez"
      }
    }
  ]
}
```

### **Proceso de Importación**
```python
async def import_third_parties_bulk(
    file_data: bytes,
    file_format: str,
    import_options: ImportOptions,
    user_id: UUID
) -> BulkImportResult:
    """Importa terceros en lote desde archivo"""
    
    import_session = await create_import_session(user_id, file_format)
    
    try:
        # 1. Parsear archivo según formato
        raw_data = await parse_import_file(file_data, file_format)
        
        # 2. Validar estructura de datos
        validation_result = await validate_import_structure(raw_data, import_options)
        if validation_result.has_errors:
            return BulkImportResult(
                session_id=import_session.id,
                status="VALIDATION_FAILED",
                errors=validation_result.errors
            )
        
        # 3. Procesar en lotes
        batch_size = import_options.batch_size or 100
        total_records = len(raw_data)
        processed_count = 0
        success_count = 0
        error_count = 0
        errors = []
        
        for i in range(0, total_records, batch_size):
            batch = raw_data[i:i + batch_size]
            
            # Procesar lote
            batch_result = await process_import_batch(
                batch, import_options, import_session.id
            )
            
            processed_count += len(batch)
            success_count += batch_result.success_count
            error_count += batch_result.error_count
            errors.extend(batch_result.errors)
            
            # Actualizar progreso
            await update_import_progress(
                import_session.id,
                processed_count / total_records * 100
            )
        
        # 4. Finalizar importación
        final_status = "COMPLETED" if error_count == 0 else "COMPLETED_WITH_ERRORS"
        
        await finalize_import_session(
            import_session.id,
            final_status,
            success_count,
            error_count
        )
        
        return BulkImportResult(
            session_id=import_session.id,
            status=final_status,
            total_records=total_records,
            processed_records=processed_count,
            success_count=success_count,
            error_count=error_count,
            errors=errors
        )
        
    except Exception as e:
        await mark_import_session_failed(import_session.id, str(e))
        raise

async def process_import_batch(
    batch_data: List[dict],
    options: ImportOptions,
    session_id: UUID
) -> BatchProcessResult:
    """Procesa un lote de terceros para importación"""
    
    success_count = 0
    error_count = 0
    errors = []
    
    async with db.begin() as transaction:
        try:
            for row_index, row_data in enumerate(batch_data):
                try:
                    # Validar datos del tercero
                    third_party_data = await validate_third_party_data(
                        row_data, options
                    )
                    
                    # Verificar duplicados
                    existing = await check_existing_third_party(
                        third_party_data.code,
                        third_party_data.document_number
                    )
                    
                    if existing and not options.allow_updates:
                        raise ValueError(f"Tercero ya existe: {third_party_data.code}")
                    
                    # Crear o actualizar tercero
                    if existing and options.allow_updates:
                        third_party = await update_third_party(
                            existing.id, third_party_data
                        )
                        operation = "UPDATED"
                    else:
                        third_party = await create_third_party(third_party_data)
                        operation = "CREATED"
                    
                    # Registrar operación exitosa
                    await log_import_operation(
                        session_id, row_index, third_party.id, operation, "SUCCESS"
                    )
                    
                    success_count += 1
                    
                except Exception as row_error:
                    error_info = ImportError(
                        row_number=row_index + 1,
                        field=getattr(row_error, 'field', None),
                        error_message=str(row_error),
                        data=row_data
                    )
                    errors.append(error_info)
                    
                    # Registrar error
                    await log_import_operation(
                        session_id, row_index, None, "CREATE", "ERROR", str(row_error)
                    )
                    
                    error_count += 1
                    
                    # Continuar con el siguiente registro si se permite
                    if not options.stop_on_error:
                        continue
                    else:
                        raise row_error
            
            # Confirmar transacción del lote
            await transaction.commit()
            
        except Exception as batch_error:
            # Rollback en caso de error del lote
            await transaction.rollback()
            
            # Si stop_on_error está activado, propagar el error
            if options.stop_on_error:
                raise
    
    return BatchProcessResult(
        success_count=success_count,
        error_count=error_count,
        errors=errors
    )
```

### **Validaciones de Importación**
```python
async def validate_third_party_data(
    row_data: dict,
    options: ImportOptions
) -> ThirdPartyCreate:
    """Valida datos de un tercero para importación"""
    
    errors = []
    
    # Validaciones obligatorias
    required_fields = ['code', 'name', 'document_type', 'document_number', 'third_party_type']
    for field in required_fields:
        if not row_data.get(field):
            errors.append(f"Campo requerido faltante: {field}")
    
    # Validar formato de documento
    if row_data.get('document_type') and row_data.get('document_number'):
        try:
            validate_document(
                row_data['document_type'],
                row_data['document_number'],
                row_data.get('country', 'Colombia')
            )
        except ValueError as e:
            errors.append(f"Documento inválido: {str(e)}")
    
    # Validar email
    if row_data.get('email'):
        try:
            validate_email(row_data['email'])
        except ValueError as e:
            errors.append(f"Email inválido: {str(e)}")
    
    # Validar teléfono
    if row_data.get('phone'):
        try:
            validate_phone(row_data['phone'], row_data.get('country', 'CO'))
        except ValueError as e:
            errors.append(f"Teléfono inválido: {str(e)}")
    
    # Validar tipo de tercero
    if row_data.get('third_party_type') not in ['CUSTOMER', 'SUPPLIER', 'EMPLOYEE', 'OTHER']:
        errors.append("Tipo de tercero inválido")
    
    # Validar límite de crédito
    if row_data.get('credit_limit'):
        try:
            credit_limit = Decimal(str(row_data['credit_limit']))
            if credit_limit < 0:
                errors.append("Límite de crédito no puede ser negativo")
        except (ValueError, InvalidOperation):
            errors.append("Límite de crédito debe ser un número válido")
    
    # Validaciones personalizadas según opciones
    if options.custom_validations:
        custom_errors = await apply_custom_validations(row_data, options.custom_validations)
        errors.extend(custom_errors)
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Crear objeto validado
    return ThirdPartyCreate(**row_data)

async def check_existing_third_party(code: str, document_number: str) -> Optional[ThirdParty]:
    """Verifica si ya existe un tercero con el código o documento"""
    
    result = await db.execute(
        select(ThirdParty).where(
            or_(
                ThirdParty.code == code,
                ThirdParty.document_number == document_number
            )
        )
    )
    
    return result.scalar_one_or_none()
```

## Actualización Masiva

### **Filtros de Selección**
```python
class BulkUpdateFilters:
    # Filtros básicos
    third_party_type: Optional[str] = None
    is_active: Optional[bool] = None
    country: Optional[str] = None
    city: Optional[str] = None
    
    # Filtros comerciales
    payment_terms: Optional[str] = None
    business_type: Optional[str] = None
    risk_level: Optional[str] = None
    
    # Filtros de saldo
    has_balance: Optional[bool] = None
    balance_greater_than: Optional[Decimal] = None
    balance_less_than: Optional[Decimal] = None
    
    # Filtros de fecha
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    last_movement_after: Optional[date] = None
    last_movement_before: Optional[date] = None
    
    # Filtros de riesgo
    risk_score_greater_than: Optional[int] = None
    overdue_days_greater_than: Optional[int] = None
    
    # Filtros personalizados
    custom_criteria: Optional[dict] = None

async def bulk_update_third_parties(
    filters: BulkUpdateFilters,
    updates: ThirdPartyBulkUpdate,
    user_id: UUID,
    dry_run: bool = False
) -> BulkUpdateResult:
    """Actualiza terceros en lote según filtros"""
    
    # 1. Obtener terceros que coinciden con filtros
    matching_third_parties = await get_third_parties_by_filters(filters)
    
    if not matching_third_parties:
        return BulkUpdateResult(
            total_matched=0,
            updated_count=0,
            error_count=0,
            errors=[]
        )
    
    # 2. Validar actualizaciones
    validation_result = await validate_bulk_updates(updates, matching_third_parties)
    if validation_result.has_errors and not dry_run:
        return BulkUpdateResult(
            total_matched=len(matching_third_parties),
            updated_count=0,
            error_count=len(validation_result.errors),
            errors=validation_result.errors
        )
    
    # 3. Ejecutar en modo dry-run si se solicita
    if dry_run:
        return BulkUpdateResult(
            total_matched=len(matching_third_parties),
            updated_count=len(matching_third_parties),
            error_count=0,
            errors=[],
            dry_run=True,
            preview=matching_third_parties[:10]  # Muestra de resultados
        )
    
    # 4. Ejecutar actualizaciones
    update_session = await create_bulk_update_session(user_id, filters, updates)
    
    updated_count = 0
    error_count = 0
    errors = []
    
    async with db.begin() as transaction:
        try:
            for third_party in matching_third_parties:
                try:
                    # Aplicar actualizaciones
                    await apply_updates_to_third_party(third_party, updates, user_id)
                    
                    # Registrar operación exitosa
                    await log_bulk_operation(
                        update_session.id,
                        third_party.id,
                        "UPDATE",
                        "SUCCESS"
                    )
                    
                    updated_count += 1
                    
                except Exception as update_error:
                    error_info = BulkUpdateError(
                        third_party_id=third_party.id,
                        third_party_name=third_party.name,
                        error_message=str(update_error)
                    )
                    errors.append(error_info)
                    
                    # Registrar error
                    await log_bulk_operation(
                        update_session.id,
                        third_party.id,
                        "UPDATE",
                        "ERROR",
                        str(update_error)
                    )
                    
                    error_count += 1
            
            # Confirmar transacción
            await transaction.commit()
            
            # Finalizar sesión
            await finalize_bulk_update_session(
                update_session.id,
                "COMPLETED" if error_count == 0 else "COMPLETED_WITH_ERRORS",
                updated_count,
                error_count
            )
            
        except Exception as session_error:
            await transaction.rollback()
            await mark_bulk_update_session_failed(update_session.id, str(session_error))
            raise
    
    return BulkUpdateResult(
        session_id=update_session.id,
        total_matched=len(matching_third_parties),
        updated_count=updated_count,
        error_count=error_count,
        errors=errors
    )

async def get_third_parties_by_filters(filters: BulkUpdateFilters) -> List[ThirdParty]:
    """Obtiene terceros que coinciden con los filtros especificados"""
    
    query = select(ThirdParty)
    
    # Aplicar filtros básicos
    if filters.third_party_type:
        query = query.where(ThirdParty.third_party_type == filters.third_party_type)
    
    if filters.is_active is not None:
        query = query.where(ThirdParty.is_active == filters.is_active)
    
    if filters.country:
        query = query.where(ThirdParty.country == filters.country)
    
    if filters.city:
        query = query.where(ThirdParty.city == filters.city)
    
    # Aplicar filtros comerciales
    if filters.payment_terms:
        query = query.where(ThirdParty.payment_terms == filters.payment_terms)
    
    if filters.business_type:
        query = query.where(ThirdParty.business_type == filters.business_type)
    
    if filters.risk_level:
        query = query.where(ThirdParty.risk_level == filters.risk_level)
    
    # Aplicar filtros de fecha
    if filters.created_after:
        query = query.where(ThirdParty.created_at >= filters.created_after)
    
    if filters.created_before:
        query = query.where(ThirdParty.created_at <= filters.created_before)
    
    # Aplicar filtros de saldo (requiere join con movimientos)
    if filters.has_balance is not None or filters.balance_greater_than or filters.balance_less_than:
        subquery = select(
            JournalEntryLine.third_party_id,
            func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label('balance')
        ).group_by(JournalEntryLine.third_party_id).subquery()
        
        query = query.outerjoin(subquery, ThirdParty.id == subquery.c.third_party_id)
        
        if filters.has_balance is not None:
            if filters.has_balance:
                query = query.where(subquery.c.balance != 0)
            else:
                query = query.where(or_(subquery.c.balance == 0, subquery.c.balance.is_(None)))
        
        if filters.balance_greater_than:
            query = query.where(subquery.c.balance > filters.balance_greater_than)
        
        if filters.balance_less_than:
            query = query.where(subquery.c.balance < filters.balance_less_than)
    
    # Aplicar filtros personalizados
    if filters.custom_criteria:
        query = await apply_custom_filters(query, filters.custom_criteria)
    
    result = await db.execute(query)
    return list(result.scalars().all())
```

### **Operaciones Masivas Específicas**

#### **1. Actualización de Términos de Pago**
```python
async def bulk_update_payment_terms(
    old_terms: str,
    new_terms: str,
    third_party_type: str = None
) -> BulkUpdateResult:
    """Actualiza términos de pago masivamente"""
    
    filters = BulkUpdateFilters(
        payment_terms=old_terms,
        third_party_type=third_party_type
    )
    
    updates = ThirdPartyBulkUpdate(
        payment_terms=new_terms,
        updated_reason=f"Cambio masivo de términos: {old_terms} -> {new_terms}"
    )
    
    return await bulk_update_third_parties(filters, updates, user_id)
```

#### **2. Actualización de Estados por País**
```python
async def bulk_update_status_by_country(
    country: str,
    new_status: bool,
    reason: str
) -> BulkUpdateResult:
    """Actualiza estado de terceros por país"""
    
    filters = BulkUpdateFilters(country=country)
    
    updates = ThirdPartyBulkUpdate(
        is_active=new_status,
        updated_reason=reason
    )
    
    return await bulk_update_third_parties(filters, updates, user_id)
```

#### **3. Clasificación Automática de Riesgo**
```python
async def bulk_classify_risk_levels() -> BulkUpdateResult:
    """Clasifica automáticamente niveles de riesgo basado en comportamiento"""
    
    # Obtener todos los terceros activos con saldo
    filters = BulkUpdateFilters(
        is_active=True,
        has_balance=True
    )
    
    third_parties = await get_third_parties_by_filters(filters)
    
    updated_count = 0
    for tp in third_parties:
        # Calcular score de riesgo
        aging_analysis = await perform_aging_analysis(tp.id)
        risk_score = aging_analysis.risk_score
        
        # Clasificar riesgo
        if risk_score >= 80:
            risk_level = "HIGH"
        elif risk_score >= 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Actualizar si cambió
        if tp.risk_level != risk_level:
            await update_third_party(
                tp.id,
                ThirdPartyUpdate(
                    risk_level=risk_level,
                    updated_reason="Clasificación automática de riesgo"
                )
            )
            updated_count += 1
    
    return BulkUpdateResult(
        total_matched=len(third_parties),
        updated_count=updated_count,
        error_count=0
    )
```

## Sincronización con Sistemas Externos

### **Conectores de Integración**
```python
class ExternalSystemConnector:
    """Conector base para sistemas externos"""
    
    def __init__(self, config: dict):
        self.config = config
        self.field_mapping = config.get('field_mapping', {})
        self.sync_settings = config.get('sync_settings', {})
    
    async def extract_data(self) -> List[dict]:
        """Extrae datos del sistema externo"""
        raise NotImplementedError
    
    async def transform_data(self, raw_data: List[dict]) -> List[ThirdPartySync]:
        """Transforma datos al formato interno"""
        transformed_data = []
        
        for record in raw_data:
            # Mapear campos
            mapped_record = {}
            for internal_field, external_field in self.field_mapping.items():
                if external_field in record:
                    mapped_record[internal_field] = record[external_field]
            
            # Aplicar transformaciones específicas
            transformed_record = await self.apply_transformations(mapped_record)
            transformed_data.append(ThirdPartySync(**transformed_record))
        
        return transformed_data
    
    async def load_data(self, transformed_data: List[ThirdPartySync]) -> SyncResult:
        """Carga datos transformados al sistema"""
        return await sync_third_parties_data(transformed_data, self.sync_settings)

class ERPConnector(ExternalSystemConnector):
    """Conector específico para sistemas ERP"""
    
    async def extract_data(self) -> List[dict]:
        # Implementación específica para ERP
        # Puede usar APIs REST, SOAP, archivos, etc.
        
        api_client = ERPAPIClient(self.config['api_config'])
        
        # Obtener terceros modificados desde última sincronización
        last_sync = await get_last_sync_timestamp('ERP')
        
        customers = await api_client.get_customers(modified_since=last_sync)
        suppliers = await api_client.get_suppliers(modified_since=last_sync)
        
        return customers + suppliers

class CRMConnector(ExternalSystemConnector):
    """Conector específico para sistemas CRM"""
    
    async def extract_data(self) -> List[dict]:
        crm_client = CRMAPIClient(self.config['api_config'])
        
        # Sincronizar solo clientes desde CRM
        contacts = await crm_client.get_contacts()
        companies = await crm_client.get_companies()
        
        return contacts + companies

async def sync_with_external_system(
    system_type: str,
    config: dict,
    sync_mode: str = "INCREMENTAL"
) -> SyncResult:
    """Sincroniza con sistema externo"""
    
    # Crear conector apropiado
    if system_type == "ERP":
        connector = ERPConnector(config)
    elif system_type == "CRM":
        connector = CRMConnector(config)
    else:
        raise ValueError(f"Tipo de sistema no soportado: {system_type}")
    
    sync_session = await create_sync_session(system_type, sync_mode)
    
    try:
        # Proceso ETL
        raw_data = await connector.extract_data()
        transformed_data = await connector.transform_data(raw_data)
        result = await connector.load_data(transformed_data)
        
        # Actualizar sesión de sincronización
        await finalize_sync_session(
            sync_session.id,
            "COMPLETED",
            result.created_count,
            result.updated_count,
            result.error_count
        )
        
        return result
        
    except Exception as e:
        await mark_sync_session_failed(sync_session.id, str(e))
        raise
```

### **Resolución de Conflictos**
```python
async def sync_third_parties_data(
    sync_data: List[ThirdPartySync],
    sync_settings: dict
) -> SyncResult:
    """Sincroniza datos de terceros resolviendo conflictos"""
    
    created_count = 0
    updated_count = 0
    error_count = 0
    conflicts = []
    
    for sync_record in sync_data:
        try:
            # Buscar tercero existente
            existing = await find_existing_third_party(sync_record)
            
            if existing:
                # Verificar si hay conflictos
                conflicts_found = await detect_conflicts(existing, sync_record)
                
                if conflicts_found:
                    # Aplicar estrategia de resolución
                    resolution = await resolve_conflicts(
                        existing, sync_record, conflicts_found, sync_settings
                    )
                    
                    if resolution.action == "UPDATE":
                        await update_third_party(existing.id, resolution.merged_data)
                        updated_count += 1
                    elif resolution.action == "SKIP":
                        continue
                    elif resolution.action == "MANUAL_REVIEW":
                        conflicts.append(ConflictCase(
                            existing_id=existing.id,
                            sync_data=sync_record,
                            conflicts=conflicts_found
                        ))
                        continue
                else:
                    # Actualización sin conflictos
                    update_data = sync_record.to_update_model()
                    await update_third_party(existing.id, update_data)
                    updated_count += 1
            else:
                # Crear nuevo tercero
                create_data = sync_record.to_create_model()
                await create_third_party(create_data)
                created_count += 1
                
        except Exception as e:
            error_count += 1
            await log_sync_error(sync_record, str(e))
    
    return SyncResult(
        created_count=created_count,
        updated_count=updated_count,
        error_count=error_count,
        conflicts=conflicts
    )

async def detect_conflicts(
    existing: ThirdParty,
    sync_record: ThirdPartySync
) -> List[ConflictInfo]:
    """Detecta conflictos entre datos existentes y sincronización"""
    
    conflicts = []
    
    # Conflictos de datos básicos
    if existing.name != sync_record.name:
        conflicts.append(ConflictInfo(
            field="name",
            existing_value=existing.name,
            new_value=sync_record.name,
            conflict_type="VALUE_MISMATCH"
        ))
    
    if existing.email != sync_record.email:
        conflicts.append(ConflictInfo(
            field="email",
            existing_value=existing.email,
            new_value=sync_record.email,
            conflict_type="VALUE_MISMATCH"
        ))
    
    # Conflictos de última modificación
    if (existing.updated_at and sync_record.last_modified and
        existing.updated_at > sync_record.last_modified):
        conflicts.append(ConflictInfo(
            field="last_modified",
            existing_value=existing.updated_at,
            new_value=sync_record.last_modified,
            conflict_type="TIMESTAMP_CONFLICT"
        ))
    
    return conflicts

async def resolve_conflicts(
    existing: ThirdParty,
    sync_record: ThirdPartySync,
    conflicts: List[ConflictInfo],
    sync_settings: dict
) -> ConflictResolution:
    """Resuelve conflictos según configuración"""
    
    strategy = sync_settings.get('conflict_resolution', 'MANUAL_REVIEW')
    
    if strategy == "EXTERNAL_WINS":
        # El sistema externo siempre gana
        return ConflictResolution(
            action="UPDATE",
            merged_data=sync_record.to_update_model()
        )
    
    elif strategy == "INTERNAL_WINS":
        # El sistema interno siempre gana
        return ConflictResolution(action="SKIP")
    
    elif strategy == "TIMESTAMP_BASED":
        # Gana el más reciente
        if sync_record.last_modified > existing.updated_at:
            return ConflictResolution(
                action="UPDATE",
                merged_data=sync_record.to_update_model()
            )
        else:
            return ConflictResolution(action="SKIP")
    
    elif strategy == "FIELD_PRIORITY":
        # Resolver por prioridad de campos
        merged_data = await merge_by_field_priority(
            existing, sync_record, sync_settings.get('field_priorities', {})
        )
        return ConflictResolution(
            action="UPDATE",
            merged_data=merged_data
        )
    
    else:  # MANUAL_REVIEW
        return ConflictResolution(action="MANUAL_REVIEW")
```

## API de Operaciones Masivas

### **Endpoints Principales**

#### **Importación Masiva**
```http
POST /api/v1/third-parties/bulk-import
Content-Type: multipart/form-data

Form Data:
  - file: archivo (CSV, XLSX, JSON)
  - format: string (csv, xlsx, json)
  - options: JSON (opciones de importación)

Response:
{
  "session_id": "uuid",
  "status": "PROCESSING",
  "message": "Importación iniciada",
  "estimated_duration": "5 minutes"
}
```

#### **Estado de Importación**
```http
GET /api/v1/third-parties/bulk-import/{session_id}/status

Response:
{
  "session_id": "uuid",
  "status": "IN_PROGRESS",
  "progress_percentage": 65.5,
  "processed_records": 655,
  "total_records": 1000,
  "success_count": 620,
  "error_count": 35,
  "estimated_completion": "2024-04-01T15:30:00Z"
}
```

#### **Actualización Masiva**
```http
POST /api/v1/third-parties/bulk-update
Content-Type: application/json

{
  "filters": {
    "third_party_type": "CUSTOMER",
    "country": "Colombia",
    "payment_terms": "30 días"
  },
  "updates": {
    "payment_terms": "15 días",
    "updated_reason": "Cambio de política comercial"
  },
  "dry_run": false
}

Response:
{
  "session_id": "uuid",
  "total_matched": 150,
  "updated_count": 148,
  "error_count": 2,
  "errors": [...]
}
```

#### **Sincronización Externa**
```http
POST /api/v1/third-parties/sync-external
Content-Type: application/json

{
  "system_type": "ERP",
  "config": {
    "api_config": {...},
    "field_mapping": {...},
    "sync_settings": {...}
  },
  "sync_mode": "INCREMENTAL"
}

Response:
{
  "sync_session_id": "uuid",
  "status": "STARTED",
  "estimated_duration": "10 minutes"
}
```

## Casos de Uso Prácticos

### **Caso 1: Migración desde Sistema Legacy**
```python
# Importar terceros desde sistema anterior
import_options = ImportOptions(
    batch_size=50,
    allow_updates=True,
    stop_on_error=False,
    custom_validations=[
        "validate_legacy_codes",
        "normalize_addresses"
    ]
)

# Procesar archivo de migración
result = await import_third_parties_bulk(
    file_data=legacy_data,
    file_format="csv",
    import_options=import_options,
    user_id=admin_user_id
)

print(f"Migración completada: {result.success_count} éxitos, {result.error_count} errores")
```

### **Caso 2: Actualización Masiva por Cambio de Política**
```python
# Actualizar términos de pago para clientes pequeños
small_customer_filters = BulkUpdateFilters(
    third_party_type="CUSTOMER",
    business_type="PYME",
    credit_limit_less_than=1000000
)

updates = ThirdPartyBulkUpdate(
    payment_terms="15 días",
    updated_reason="Nueva política para PYMES"
)

result = await bulk_update_third_parties(
    small_customer_filters,
    updates,
    user_id
)
```

### **Caso 3: Sincronización Automática con CRM**
```python
# Configurar sincronización diaria con CRM
crm_config = {
    "api_config": {
        "base_url": "https://crm.empresa.com/api",
        "api_key": "...",
        "version": "v2"
    },
    "field_mapping": {
        "name": "company_name",
        "email": "primary_email",
        "phone": "main_phone",
        "address": "billing_address"
    },
    "sync_settings": {
        "conflict_resolution": "TIMESTAMP_BASED",
        "sync_mode": "INCREMENTAL"
    }
}

# Programar sincronización
await schedule_sync_job(
    system_type="CRM",
    config=crm_config,
    frequency="daily",
    time="02:00"
)
```

## Beneficios de las Operaciones Masivas

### **Para Administradores**
- **Eficiencia**: Procesamiento rápido de grandes volúmenes
- **Automatización**: Reducción de trabajo manual repetitivo
- **Control**: Validaciones y rollback automático
- **Auditabilidad**: Registro completo de operaciones

### **Para Integración**
- **Flexibilidad**: Múltiples formatos y conectores
- **Confiabilidad**: Manejo robusto de errores
- **Escalabilidad**: Procesamiento en lotes optimizado
- **Sincronización**: Mantenimiento automático de datos

### **Para la Organización**
- **Productividad**: Menor tiempo en tareas administrativas
- **Calidad**: Validaciones automáticas mejoran calidad de datos
- **Consistencia**: Sincronización mantiene datos actualizados
- **Escalabilidad**: Capacidad de manejar crecimiento de datos

---

*Documentación de operaciones masivas de terceros - Sprint 2*
