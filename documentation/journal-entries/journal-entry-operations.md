# Operaciones de Asientos Contables

Este documento describe las operaciones disponibles para manejar asientos contables en el sistema API Contable.

## 📝 Creación de Asientos

### Proceso de Creación

La creación de asientos contables implica los siguientes pasos:

1. **Validación de datos iniciales**
   - Comprobación de campos requeridos
   - Validación de cuentas existentes
   - Verificación de que las cuentas permiten movimientos
   - Verificación de requisitos de terceros y centros de costo

2. **Generación de número de asiento**
   - Formato estándar basado en tipo y fecha: `[TIPO]-[AÑO]-[SECUENCIA]`
   - Ejemplo: `JE-2025-000123` para un asiento regular del año 2025

3. **Validación de líneas**
   - Cada línea debe tener débito O crédito (no ambos ni ninguno)
   - Los importes no pueden ser negativos
   - Se verifica que las cuentas permiten movimientos
   - Se validan requisitos adicionales (terceros, centros de costo)

4. **Verificación de balance**
   - Total débitos debe ser igual a total créditos
   - Se calculan los totales para almacenamiento y referencia rápida

5. **Persistencia en base de datos**
   - Creación transaccional del asiento y sus líneas
   - Estado inicial: DRAFT (borrador)

### Schema para Creación

```python
class JournalEntryCreate(JournalEntryBase):
    """Schema para crear asientos contables"""
    lines: List[JournalEntryLineCreate] = Field(..., min_length=2, description="Líneas del asiento (mínimo 2)")
    
    @field_validator('lines')
    @classmethod
    def validate_lines_balance(cls, v):
        """Valida que el asiento esté balanceado"""
        if len(v) < 2:
            raise ValueError("Un asiento debe tener al menos 2 líneas")
        
        total_debit = sum(line.debit_amount or Decimal('0') for line in v)
        total_credit = sum(line.credit_amount or Decimal('0') for line in v)
        
        if total_debit != total_credit:
            raise ValueError(f"El asiento no está balanceado: Débitos={total_debit}, Créditos={total_credit}")
        
        if total_debit == 0:
            raise ValueError("El asiento debe tener movimientos con montos mayores a cero")
        
        return v
```

### Implementación del Servicio

```python
async def create_journal_entry(
    self, 
    entry_data: JournalEntryCreate, 
    created_by_id: uuid.UUID
) -> JournalEntry:
    """Crear un nuevo asiento contable"""
    
    # Validación inicial de cuentas en batch para optimizar rendimiento
    account_ids = [line.account_id for line in entry_data.lines]
    accounts_result = await self.db.execute(
        select(Account).where(Account.id.in_(account_ids))
    )
    accounts_dict = {account.id: account for account in accounts_result.scalars().all()}
    
    # Validar que todas las cuentas existen
    missing_accounts = set(account_ids) - set(accounts_dict.keys())
    if missing_accounts:
        raise AccountNotFoundError(account_id=str(list(missing_accounts)[0]))
    
    # Validar que todas las cuentas permiten movimientos
    invalid_accounts = [
        f"{account.code} - {account.name}" 
        for account in accounts_dict.values() 
        if not account.allows_movements
    ]
    if invalid_accounts:
        raise JournalEntryError(f"Las siguientes cuentas no permiten movimientos: {', '.join(invalid_accounts)}")
    
    # Generar número de asiento
    entry_number = await self.generate_entry_number(entry_data.entry_type)
    
    # Crear las líneas y validar balance
    journal_lines = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    
    for line_number, line_data in enumerate(entry_data.lines, 1):
        # Validaciones de línea
        if line_data.debit_amount < 0 or line_data.credit_amount < 0:
            raise JournalEntryError(f"Los montos no pueden ser negativos en línea {line_number}")
        
        # ... más validaciones ...
        
        journal_lines.append(journal_line)
        total_debit += line_data.debit_amount
        total_credit += line_data.credit_amount
    
    # Validar balance
    if total_debit != total_credit:
        raise BalanceError(
            expected_balance=str(total_debit),
            actual_balance=str(total_credit),
            account_info=f"Asiento {entry_number}"
        )
    
    # Crear el asiento principal
    journal_entry = JournalEntry(
        number=entry_number,
        reference=entry_data.reference,
        description=entry_data.description,
        entry_type=entry_data.entry_type,
        entry_date=entry_data.entry_date,
        status=JournalEntryStatus.DRAFT,
        created_by_id=created_by_id,
        notes=entry_data.notes,
        total_debit=total_debit,
        total_credit=total_credit
    )
    
    # Persistir en base de datos
    # ... transacción ...
    
    return journal_entry
```

## 🔍 Consultas de Asientos

### Consulta Individual

```python
async def get_journal_entry_by_id(self, entry_id: uuid.UUID) -> Optional[JournalEntry]:
    """Obtener un asiento por ID"""
    result = await self.db.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account))
        .options(selectinload(JournalEntry.created_by))
        .options(selectinload(JournalEntry.posted_by))
        .where(JournalEntry.id == entry_id)
    )
    return result.scalar_one_or_none()
```

### Consulta por Número

```python
async def get_journal_entry_by_number(self, number: str) -> Optional[JournalEntry]:
    """Obtener un asiento por número"""
    result = await self.db.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account))
        .options(selectinload(JournalEntry.created_by))
        .options(selectinload(JournalEntry.posted_by))
        .where(JournalEntry.number == number)
    )
    return result.scalar_one_or_none()
```

### Listado con Filtros

```python
async def get_journal_entries(
    self,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[JournalEntryFilter] = None
) -> Tuple[List[JournalEntry], int]:
    """Obtener lista de asientos contables con filtros"""
    query = select(JournalEntry)
    
    # Aplicar filtros si existen
    if filters:
        if filters.status:
            query = query.where(JournalEntry.status == filters.status)
        if filters.start_date:
            query = query.where(JournalEntry.entry_date >= filters.start_date)
        if filters.end_date:
            query = query.where(JournalEntry.entry_date <= filters.end_date)
        # ... más filtros ...
    
    # Obtener total para paginación
    count_query = select(func.count()).select_from(query.subquery())
    total = await self.db.scalar(count_query)
    
    # Ejecutar consulta principal con paginación y ordenamiento
    query = (
        query.options(selectinload(JournalEntry.created_by))
        .order_by(desc(JournalEntry.entry_date))
        .offset(skip)
        .limit(limit)
    )
    
    result = await self.db.execute(query)
    journal_entries = result.scalars().all()
    
    return journal_entries, total or 0
```

## ✅ Aprobación de Asientos

### Proceso de Aprobación

```python
async def approve_journal_entry(
    self, 
    entry_id: uuid.UUID, 
    approved_by_id: uuid.UUID
) -> JournalEntry:
    """Aprobar un asiento contable"""
    
    journal_entry = await self.get_journal_entry_by_id(entry_id)
    
    if not journal_entry:
        raise JournalEntryNotFoundError(entry_id=entry_id)
    
    if journal_entry.status not in [JournalEntryStatus.DRAFT, JournalEntryStatus.PENDING]:
        raise JournalEntryError("Solo se pueden aprobar asientos en estado borrador o pendiente")
    
    # Ejecutar método de aprobación del modelo
    try:
        journal_entry.approve(approved_by_id)
    except ValueError as e:
        raise JournalEntryError(str(e))
    
    await self.db.commit()
    await self.db.refresh(journal_entry)
    
    return journal_entry
```

## 📊 Contabilización de Asientos

### Proceso de Contabilización

```python
async def post_journal_entry(
    self, 
    entry_id: uuid.UUID, 
    posted_by_id: uuid.UUID,
    post_data: Optional[JournalEntryPost] = None
) -> JournalEntry:
    """Contabilizar un asiento"""
    
    journal_entry = await self.get_journal_entry_by_id(entry_id)
    
    if not journal_entry:
        raise JournalEntryError("Asiento no encontrado")
    
    if not journal_entry.can_be_posted:
        raise JournalEntryError("El asiento no puede ser contabilizado en su estado actual")
    
    # Contabilizar
    success = journal_entry.post(posted_by_id)
    if not success:
        raise JournalEntryError("No se pudo contabilizar el asiento")
    
    # Actualizar notas si se proporcionan
    if post_data and post_data.reason:
        if journal_entry.notes:
            journal_entry.notes += f"\\n\\nContabilizado: {post_data.reason}"
        else:
            journal_entry.notes = f"Contabilizado: {post_data.reason}"
    
    await self.db.commit()
    await self.db.refresh(journal_entry)
    
    return journal_entry
```

## ❌ Cancelación de Asientos

### Proceso de Cancelación

```python
async def cancel_journal_entry(
    self, 
    entry_id: uuid.UUID, 
    cancelled_by_id: uuid.UUID,
    cancel_data: JournalEntryCancel
) -> JournalEntry:
    """Cancelar un asiento contable"""
    
    journal_entry = await self.get_journal_entry_by_id(entry_id)
    
    if not journal_entry:
        raise JournalEntryNotFoundError(entry_id=entry_id)
    
    if journal_entry.status == JournalEntryStatus.CANCELLED:
        raise JournalEntryError("El asiento ya está cancelado")
    
    # Si está contabilizado, necesitamos crear un asiento de reversión
    if journal_entry.status == JournalEntryStatus.POSTED:
        # Revertir efectos en cuentas y crear asiento de reversión
        reversal_entry = await self._create_reversal_entry(
            journal_entry, 
            cancelled_by_id,
            f"Reversión por cancelación: {cancel_data.reason}"
        )
        
        # Marcar el asiento como cancelado
        journal_entry.status = JournalEntryStatus.CANCELLED
        journal_entry.cancelled_by_id = cancelled_by_id
        journal_entry.cancelled_at = datetime.now(timezone.utc)
        
        if journal_entry.notes:
            journal_entry.notes += f"\\n\\nCancelado: {cancel_data.reason}"
        else:
            journal_entry.notes = f"Cancelado: {cancel_data.reason}"
    else:
        # Si no está contabilizado, solo actualizamos el estado
        journal_entry.status = JournalEntryStatus.CANCELLED
        journal_entry.cancelled_by_id = cancelled_by_id
        journal_entry.cancelled_at = datetime.now(timezone.utc)
        journal_entry.notes = f"Cancelado: {cancel_data.reason}"
    
    await self.db.commit()
    await self.db.refresh(journal_entry)
    
    return journal_entry
```

## ↩️ Reversión de Asientos

### Creación de Asientos de Reversión

```python
async def _create_reversal_entry(
    self, 
    original_entry: JournalEntry,
    created_by_id: uuid.UUID,
    reason: str
) -> JournalEntry:
    """Crear un asiento de reversión a partir de uno original"""
    
    # Generar número para el nuevo asiento
    reversal_number = await self.generate_entry_number(JournalEntryType.REVERSAL)
    
    # Crear el nuevo asiento con información invertida
    reversal_entry = JournalEntry(
        number=reversal_number,
        reference=f"REV-{original_entry.number}",
        description=f"Reversión de asiento {original_entry.number}",
        entry_type=JournalEntryType.REVERSAL,
        entry_date=datetime.now(timezone.utc).date(),
        status=JournalEntryStatus.DRAFT,
        created_by_id=created_by_id,
        notes=reason,
        total_debit=original_entry.total_credit,  # Los valores se invierten
        total_credit=original_entry.total_debit    # Los valores se invierten
    )
    
    self.db.add(reversal_entry)
    await self.db.flush()  # Para obtener el ID
    
    # Crear las líneas invertidas
    for original_line in original_entry.lines:
        reversal_line = JournalEntryLine(
            journal_entry_id=reversal_entry.id,
            account_id=original_line.account_id,
            # Invertir débito y crédito
            debit_amount=original_line.credit_amount,
            credit_amount=original_line.debit_amount,
            description=f"Reversión: {original_line.description}",
            reference=original_line.reference,
            third_party_id=original_line.third_party_id,
            cost_center_id=original_line.cost_center_id,
            line_number=original_line.line_number
        )
        self.db.add(reversal_line)
    
    # Aprobar y contabilizar el asiento de reversión inmediatamente
    await self.db.flush()
    
    reversal_entry.approve(created_by_id)
    reversal_entry.post(created_by_id)
    
    await self.db.commit()
    await self.db.refresh(reversal_entry)
    
    return reversal_entry
```

## 📊 Estadísticas de Asientos

```python
async def get_journal_entry_stats(
    self,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> dict:
    """Obtener estadísticas de asientos contables"""
    
    # Construir filtros base
    filters = []
    if start_date:
        filters.append(JournalEntry.entry_date >= start_date)
    if end_date:
        filters.append(JournalEntry.entry_date <= end_date)
    
    # Consulta para total por estado
    total_query = select(
        JournalEntry.status,
        func.count(JournalEntry.id).label("count")
    ).group_by(JournalEntry.status)
    
    if filters:
        total_query = total_query.where(and_(*filters))
    
    total_result = await self.db.execute(total_query)
    totals_by_status = {status.value: count for status, count in total_result.all()}
    
    # Consulta para total por tipo
    type_query = select(
        JournalEntry.entry_type,
        func.count(JournalEntry.id).label("count")
    ).group_by(JournalEntry.entry_type)
    
    if filters:
        type_query = type_query.where(and_(*filters))
    
    type_result = await self.db.execute(type_query)
    totals_by_type = {type_.value: count for type_, count in type_result.all()}
    
    # Consulta para total por mes
    month_query = select(
        func.date_trunc('month', JournalEntry.entry_date).label("month"),
        func.count(JournalEntry.id).label("count")
    ).group_by(text("month")).order_by(text("month"))
    
    if filters:
        month_query = month_query.where(and_(*filters))
    
    month_result = await self.db.execute(month_query)
    totals_by_month = {month.strftime("%Y-%m"): count for month, count in month_result.all()}
    
    # Calcular totales monetarios
    amount_query = select(
        func.sum(JournalEntry.total_debit).label("total_debit"),
        func.sum(JournalEntry.total_credit).label("total_credit")
    ).where(JournalEntry.status == JournalEntryStatus.POSTED)
    
    if filters:
        amount_query = amount_query.where(and_(*filters))
    
    amount_result = await self.db.execute(amount_query)
    amount_totals = amount_result.one_or_none()
    total_amount = amount_totals[0] if amount_totals and amount_totals[0] else Decimal('0')
    
    # Construir resultado
    return {
        "total_entries": sum(totals_by_status.values()),
        "draft_entries": totals_by_status.get(JournalEntryStatus.DRAFT.value, 0),
        "approved_entries": totals_by_status.get(JournalEntryStatus.APPROVED.value, 0),
        "posted_entries": totals_by_status.get(JournalEntryStatus.POSTED.value, 0),
        "cancelled_entries": totals_by_status.get(JournalEntryStatus.CANCELLED.value, 0),
        "total_debit_amount": total_amount,
        "total_credit_amount": total_amount,
        "entries_this_month": totals_by_month.get(datetime.now().strftime("%Y-%m"), 0),
        "entries_this_year": sum(
            count for month, count in totals_by_month.items() 
            if month.startswith(datetime.now().strftime("%Y"))
        ),
        "entries_by_type": totals_by_type,
        "entries_by_month": totals_by_month
    }
```

## 🔄 Operaciones en Lote

```python
async def bulk_create_journal_entries(
    self, 
    entries_data: List[JournalEntryCreate],
    created_by_id: uuid.UUID
) -> List[JournalEntry]:
    """Crear múltiples asientos contables en lote"""
    
    created_entries = []
    errors = []
    
    for entry_data in entries_data:
        try:
            entry = await self.create_journal_entry(entry_data, created_by_id)
            created_entries.append(entry)
        except Exception as e:
            errors.append(str(e))
    
    if errors:
        # Si hay errores, hacemos rollback de todo
        await self.db.rollback()
        raise JournalEntryError(f"Errores en creación masiva: {'; '.join(errors)}")
    
    return created_entries
```
