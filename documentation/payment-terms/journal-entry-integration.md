# Integración con Asientos Contables

## Descripción General

El módulo de condiciones de pago se integra directamente con el sistema de asientos contables, permitiendo gestionar fechas de facturación y vencimientos de manera flexible y automatizada.

## Nuevos Campos en Journal Entry Lines

### Campos Agregados

```python
class JournalEntryLine(Base):
    # ... campos existentes ...
    
    # Fechas de facturación y pago
    invoice_date: Mapped[Optional[date]] = mapped_column(
        Date, 
        nullable=True,
        comment="Fecha de la factura (diferente a fecha de creación del asiento)"
    )
    
    due_date: Mapped[Optional[date]] = mapped_column(
        Date, 
        nullable=True,
        comment="Fecha de vencimiento manual de la factura"
    )
    
    # Condiciones de pago
    payment_terms_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("payment_terms.id"), 
        nullable=True,
        comment="Condiciones de pago aplicables a esta línea"
    )
    
    # Relación
    payment_terms: Mapped[Optional["PaymentTerms"]] = relationship(
        "PaymentTerms", 
        lazy="select"
    )
```

## Propiedades Calculadas

### effective_invoice_date
```python
@property
def effective_invoice_date(self) -> date:
    """
    Retorna la fecha de factura efectiva
    Si no hay invoice_date específica, usa la fecha del asiento
    """
    if self.invoice_date:
        return self.invoice_date
    return self.journal_entry.entry_date.date()
```

### effective_due_date
```python
@property
def effective_due_date(self) -> Optional[date]:
    """
    Retorna la fecha de vencimiento efectiva
    Prioridad: due_date manual > calculada desde payment_terms
    """
    # 1. Fecha manual tiene prioridad
    if self.due_date:
        return self.due_date
    
    # 2. Calcular desde condiciones de pago
    if self.payment_terms and self.payment_terms.payment_schedules:
        last_schedule = max(
            self.payment_terms.payment_schedules, 
            key=lambda x: x.days
        )
        invoice_datetime = datetime.combine(
            self.effective_invoice_date, 
            datetime.min.time()
        )
        due_datetime = last_schedule.calculate_payment_date(invoice_datetime)
        return due_datetime.date()
    
    return None
```

### get_payment_schedule()
```python
def get_payment_schedule(self) -> List[dict]:
    """
    Retorna el cronograma de pagos completo para esta línea
    
    Returns:
        Lista de diccionarios con información de cada pago programado
    """
    if not self.payment_terms:
        # Pago único con fecha manual
        if self.due_date:
            return [{
                'sequence': 1,
                'days': (self.due_date - self.effective_invoice_date).days,
                'percentage': Decimal('100.00'),
                'amount': self.amount,
                'payment_date': self.due_date,
                'description': 'Pago único'
            }]
        return []
    
    # Cronograma basado en condiciones de pago
    invoice_datetime = datetime.combine(
        self.effective_invoice_date, 
        datetime.min.time()
    )
    payment_schedule = []
    
    for schedule in self.payment_terms.payment_schedules:
        payment_date = schedule.calculate_payment_date(invoice_datetime)
        payment_amount = schedule.calculate_amount(self.amount)
        
        payment_schedule.append({
            'sequence': schedule.sequence,
            'days': schedule.days,
            'percentage': schedule.percentage,
            'amount': payment_amount,
            'payment_date': payment_date.date(),
            'description': schedule.description or f'Pago {schedule.sequence}'
        })
    
    return sorted(payment_schedule, key=lambda x: x['sequence'])
```

## Casos de Uso Prácticos

### Caso 1: Factura con Condiciones de Pago Estándar

```json
{
  "entry_date": "2025-06-14",
  "description": "Venta a cliente con términos 30 días",
  "lines": [
    {
      "account_id": "uuid-cuenta-clientes",
      "debit_amount": 10000,
      "invoice_date": "2025-06-14",
      "payment_terms_id": "uuid-30d",
      "description": "Factura #001"
    },
    {
      "account_id": "uuid-cuenta-ventas",
      "credit_amount": 10000,
      "description": "Venta de productos"
    }
  ]
}
```

**Resultado Automático:**
- `effective_invoice_date`: 2025-06-14
- `effective_due_date`: 2025-07-14 (30 días después)

### Caso 2: Factura con Pago Fraccionado

```json
{
  "entry_date": "2025-06-14",
  "description": "Venta con pago fraccionado 30-60",
  "lines": [
    {
      "account_id": "uuid-cuenta-clientes",
      "debit_amount": 20000,
      "invoice_date": "2025-06-14",
      "payment_terms_id": "uuid-30-60",
      "description": "Factura #002"
    }
  ]
}
```

**Cronograma Generado:**
```json
[
  {
    "sequence": 1,
    "days": 30,
    "percentage": 50.00,
    "amount": 10000,
    "payment_date": "2025-07-14",
    "description": "Primer pago - 50%"
  },
  {
    "sequence": 2,
    "days": 60,
    "percentage": 50.00,
    "amount": 10000,
    "payment_date": "2025-08-13",
    "description": "Segundo pago - 50%"
  }
]
```

### Caso 3: Fecha de Vencimiento Manual

```json
{
  "entry_date": "2025-06-14",
  "description": "Factura con vencimiento específico",
  "lines": [
    {
      "account_id": "uuid-cuenta-clientes",
      "debit_amount": 15000,
      "invoice_date": "2025-06-10",
      "due_date": "2025-07-20",
      "description": "Factura especial #003"
    }
  ]
}
```

**Resultado:**
- `effective_invoice_date`: 2025-06-10
- `effective_due_date`: 2025-07-20 (fecha manual tiene prioridad)

## Validaciones de Negocio

### Validación de Conflictos
```python
def validate_payment_fields(self) -> List[str]:
    """
    Valida que no haya conflictos entre campos de pago
    """
    errors = []
    
    # No se puede tener condiciones de pago Y fecha manual
    if self.payment_terms_id and self.due_date:
        errors.append(
            "No se puede especificar condiciones de pago y fecha de vencimiento manual simultáneamente"
        )
    
    # Fecha de factura no puede ser futura (opcional)
    if self.invoice_date and self.invoice_date > date.today():
        errors.append("La fecha de factura no puede ser futura")
    
    # Fecha de vencimiento no puede ser anterior a factura
    if (self.invoice_date and self.due_date and 
        self.due_date < self.invoice_date):
        errors.append(
            "La fecha de vencimiento no puede ser anterior a la fecha de factura"
        )
    
    return errors
```

### Validación de Condiciones Activas
```python
def validate_active_payment_terms(self) -> List[str]:
    """
    Valida que las condiciones de pago estén activas
    """
    errors = []
    
    if (self.payment_terms_id and self.payment_terms and 
        not self.payment_terms.is_active):
        errors.append(
            f"Las condiciones de pago '{self.payment_terms.code}' están inactivas"
        )
    
    return errors
```

## Actualización de Schemas

### JournalEntryLineCreate
```python
class JournalEntryLineCreate(BaseModel):
    account_id: UUID
    debit_amount: Decimal = Decimal('0')
    credit_amount: Decimal = Decimal('0')
    description: Optional[str] = None
    reference: Optional[str] = None
    third_party_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    
    # Nuevos campos
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_terms_id: Optional[UUID] = None
    
    @model_validator(mode='after')
    def validate_payment_fields(self):
        """Valida campos de pago"""
        # No se pueden especificar ambos
        if self.payment_terms_id and self.due_date:
            raise ValueError(
                "No se puede especificar condiciones de pago y fecha de vencimiento manual"
            )
        
        # Fecha de vencimiento no anterior a factura
        if (self.invoice_date and self.due_date and 
            self.due_date < self.invoice_date):
            raise ValueError(
                "La fecha de vencimiento no puede ser anterior a la fecha de factura"
            )
        
        return self
```

### JournalEntryLineResponse
```python
class JournalEntryLineResponse(BaseModel):
    # ... campos existentes ...
    
    # Campos de pago
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_terms_id: Optional[UUID] = None
    
    # Campos calculados
    effective_invoice_date: date
    effective_due_date: Optional[date] = None
    
    # Información de condiciones de pago
    payment_terms_code: Optional[str] = None
    payment_terms_name: Optional[str] = None
    
    # Cronograma de pagos
    payment_schedule: List[dict] = []
    
    model_config = ConfigDict(from_attributes=True)
```

## Migración de Datos

### Script de Migración
```sql
-- Agregar nuevos campos a journal_entry_lines
ALTER TABLE journal_entry_lines 
ADD COLUMN invoice_date DATE NULL 
COMMENT 'Fecha de la factura (diferente a fecha de creación del asiento)';

ALTER TABLE journal_entry_lines 
ADD COLUMN due_date DATE NULL 
COMMENT 'Fecha de vencimiento manual de la factura';

ALTER TABLE journal_entry_lines 
ADD COLUMN payment_terms_id UUID NULL 
REFERENCES payment_terms(id)
COMMENT 'Condiciones de pago aplicables a esta línea';

-- Índices para mejorar performance
CREATE INDEX idx_journal_entry_lines_invoice_date 
ON journal_entry_lines(invoice_date);

CREATE INDEX idx_journal_entry_lines_due_date 
ON journal_entry_lines(due_date);

CREATE INDEX idx_journal_entry_lines_payment_terms 
ON journal_entry_lines(payment_terms_id);
```

## Consideraciones de Performance

### Consultas Optimizadas
```python
# Cargar líneas con condiciones de pago
lines = (
    session.query(JournalEntryLine)
    .options(joinedload(JournalEntryLine.payment_terms))
    .filter(JournalEntryLine.journal_entry_id == entry_id)
    .all()
)

# Filtrar por fechas de vencimiento próximas
upcoming_due = (
    session.query(JournalEntryLine)
    .filter(
        or_(
            JournalEntryLine.due_date.between(start_date, end_date),
            # Para condiciones de pago, se requiere join
        )
    )
    .all()
)
```

### Caché de Cálculos
- Calcular cronogramas bajo demanda
- Caché de condiciones de pago activas
- Optimización de consultas de vencimientos
