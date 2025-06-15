# Actualizaciones de Líneas de Asiento - Payment Terms Integration

## Descripción General

Las líneas de asiento contable han sido actualizadas para soportar gestión avanzada de fechas de facturación y condiciones de pago, permitiendo un control más granular sobre vencimientos y cronogramas de pago.

## Nuevos Campos en JournalEntryLine

### Campos de Facturación y Pago

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
```

### Relaciones Agregadas

```python
# Relación con condiciones de pago
payment_terms: Mapped[Optional["PaymentTerms"]] = relationship(
    "PaymentTerms", 
    lazy="select"
)
```

## Propiedades Calculadas Nuevas

### payment_terms_code y payment_terms_name
```python
@property
def payment_terms_code(self) -> Optional[str]:
    """Retorna el código de las condiciones de pago"""
    return self.payment_terms.code if self.payment_terms else None

@property
def payment_terms_name(self) -> Optional[str]:
    """Retorna el nombre de las condiciones de pago"""
    return self.payment_terms.name if self.payment_terms else None
```

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

## Validaciones Actualizadas

### Validación de Campos de Pago
```python
def validate_payment_fields(self) -> List[str]:
    """
    Valida campos relacionados con pagos y facturación
    
    Returns:
        Lista de errores encontrados
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
    
    # Validar que las condiciones de pago estén activas
    if (self.payment_terms_id and self.payment_terms and 
        not self.payment_terms.is_active):
        errors.append(
            f"Las condiciones de pago '{self.payment_terms.code}' están inactivas"
        )
    
    return errors
```

### Validación Integrada
```python
def validate_line(self) -> List[str]:
    """
    Valida la línea del asiento (actualizado con validaciones de pago)
    """
    errors = []
    
    # Validaciones existentes...
    if self.debit_amount > 0 and self.credit_amount > 0:
        errors.append("Una línea no puede tener débito y crédito al mismo tiempo")
    
    if self.debit_amount == 0 and self.credit_amount == 0:
        errors.append("Una línea debe tener débito o crédito")
    
    if self.debit_amount < 0 or self.credit_amount < 0:
        errors.append("Los importes no pueden ser negativos")
    
    # Nuevas validaciones de pago
    payment_errors = self.validate_payment_fields()
    errors.extend(payment_errors)
    
    return errors
```

## Schemas Actualizados

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
    
    # Nuevos campos de pago
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_terms_id: Optional[UUID] = None
    
    @model_validator(mode='after')
    def validate_payment_fields(self):
        """Valida campos de pago"""
        if self.payment_terms_id and self.due_date:
            raise ValueError(
                "No se puede especificar condiciones de pago y fecha de vencimiento manual"
            )
        
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
    id: UUID
    journal_entry_id: UUID
    account_id: UUID
    debit_amount: Decimal
    credit_amount: Decimal
    description: Optional[str] = None
    reference: Optional[str] = None
    third_party_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    line_number: int
    
    # Campos de pago
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_terms_id: Optional[UUID] = None
    
    # Campos calculados
    effective_invoice_date: date
    effective_due_date: Optional[date] = None
    amount: Decimal
    movement_type: str
    
    # Información relacionada
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    third_party_code: Optional[str] = None
    third_party_name: Optional[str] = None
    cost_center_code: Optional[str] = None
    cost_center_name: Optional[str] = None
    payment_terms_code: Optional[str] = None
    payment_terms_name: Optional[str] = None
    
    # Cronograma de pagos
    payment_schedule: List[dict] = []
    
    model_config = ConfigDict(from_attributes=True)
```

## Migración de Base de Datos

### Scripts de Migración

#### Alembic Migration
```python
"""Add payment fields to journal_entry_lines

Revision ID: e947d2ee609f
Revises: be3cec477e27
Create Date: 2025-06-14 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Agregar nuevos campos
    op.add_column('journal_entry_lines', 
                  sa.Column('invoice_date', sa.Date(), nullable=True,
                           comment='Fecha de la factura (diferente a fecha de creación del asiento)'))
    
    op.add_column('journal_entry_lines', 
                  sa.Column('due_date', sa.Date(), nullable=True,
                           comment='Fecha de vencimiento manual de la factura'))
    
    op.add_column('journal_entry_lines', 
                  sa.Column('payment_terms_id', sa.UUID(), nullable=True,
                           comment='Condiciones de pago aplicables a esta línea'))
    
    # Crear foreign key constraint
    op.create_foreign_key('fk_journal_entry_lines_payment_terms',
                         'journal_entry_lines', 'payment_terms',
                         ['payment_terms_id'], ['id'])
    
    # Crear índices para performance
    op.create_index('idx_journal_entry_lines_invoice_date',
                   'journal_entry_lines', ['invoice_date'])
    
    op.create_index('idx_journal_entry_lines_due_date',
                   'journal_entry_lines', ['due_date'])
    
    op.create_index('idx_journal_entry_lines_payment_terms',
                   'journal_entry_lines', ['payment_terms_id'])

def downgrade():
    # Eliminar índices
    op.drop_index('idx_journal_entry_lines_payment_terms')
    op.drop_index('idx_journal_entry_lines_due_date')
    op.drop_index('idx_journal_entry_lines_invoice_date')
    
    # Eliminar foreign key
    op.drop_constraint('fk_journal_entry_lines_payment_terms', 
                      'journal_entry_lines', type_='foreignkey')
    
    # Eliminar columnas
    op.drop_column('journal_entry_lines', 'payment_terms_id')
    op.drop_column('journal_entry_lines', 'due_date')
    op.drop_column('journal_entry_lines', 'invoice_date')
```

## Casos de Uso Actualizados

### Caso 1: Asiento con Condiciones de Pago
```python
# Crear asiento con condiciones de pago automáticas
journal_entry_data = {
    "entry_date": "2025-06-14",
    "description": "Venta con condiciones 30-60 días",
    "lines": [
        {
            "account_id": "uuid-cuenta-clientes",
            "debit_amount": 20000.00,
            "invoice_date": "2025-06-14",
            "payment_terms_id": "uuid-30-60",
            "third_party_id": "uuid-cliente",
            "description": "Factura #001"
        },
        {
            "account_id": "uuid-cuenta-ventas",
            "credit_amount": 20000.00,
            "description": "Venta productos"
        }
    ]
}

# Resultado automático:
# - effective_invoice_date: 2025-06-14
# - Cronograma: 
#   * 2025-07-14: $10,000 (50%)
#   * 2025-08-13: $10,000 (50%)
# - effective_due_date: 2025-08-13
```

### Caso 2: Fecha de Factura Diferente a Asiento
```python
# Asiento creado después de la factura
journal_entry_data = {
    "entry_date": "2025-06-20",  # Fecha del asiento
    "description": "Registro factura anterior",
    "lines": [
        {
            "account_id": "uuid-cuenta-clientes",
            "debit_amount": 15000.00,
            "invoice_date": "2025-06-10",  # Fecha real de factura
            "payment_terms_id": "uuid-30d",
            "description": "Factura #002"
        }
    ]
}

# Cálculo basado en invoice_date:
# - effective_due_date: 2025-07-10 (30 días desde 2025-06-10)
```

### Caso 3: Vencimiento Manual
```python
# Cliente con términos especiales
journal_entry_data = {
    "entry_date": "2025-06-14",
    "description": "Cliente términos especiales",
    "lines": [
        {
            "account_id": "uuid-cuenta-clientes",
            "debit_amount": 25000.00,
            "invoice_date": "2025-06-14",
            "due_date": "2025-09-15",  # Fecha específica
            "description": "Factura especial #003"
        }
    ]
}

# La fecha manual tiene prioridad:
# - effective_due_date: 2025-09-15
```

## Reportes y Consultas

### Reporte de Vencimientos por Condiciones de Pago
```sql
SELECT 
    je.number as asiento,
    jel.description as concepto,
    jel.debit_amount + jel.credit_amount as importe,
    jel.effective_invoice_date as fecha_factura,
    jel.effective_due_date as vencimiento,
    pt.code as condiciones_codigo,
    pt.name as condiciones_nombre,
    tp.name as tercero
FROM journal_entry_lines jel
JOIN journal_entries je ON jel.journal_entry_id = je.id
LEFT JOIN payment_terms pt ON jel.payment_terms_id = pt.id
LEFT JOIN third_parties tp ON jel.third_party_id = tp.id
WHERE jel.effective_due_date IS NOT NULL
ORDER BY jel.effective_due_date;
```

### Análisis de Cronogramas de Pago
```python
# Obtener cronograma detallado para una línea
def get_detailed_payment_info(line_id: UUID) -> dict:
    line = session.query(JournalEntryLine).filter_by(id=line_id).first()
    
    if not line:
        return {}
    
    return {
        "line_id": line.id,
        "amount": line.amount,
        "invoice_date": line.effective_invoice_date,
        "due_date": line.effective_due_date,
        "payment_terms": {
            "code": line.payment_terms_code,
            "name": line.payment_terms_name
        } if line.payment_terms else None,
        "payment_schedule": line.get_payment_schedule()
    }
```

## Performance y Optimización

### Índices Recomendados
```sql
-- Índices para fechas de facturación y vencimiento
CREATE INDEX idx_journal_entry_lines_invoice_date 
ON journal_entry_lines(invoice_date);

CREATE INDEX idx_journal_entry_lines_due_date 
ON journal_entry_lines(due_date);

-- Índice compuesto para reportes de vencimientos
CREATE INDEX idx_journal_entry_lines_due_payment 
ON journal_entry_lines(due_date, payment_terms_id) 
WHERE due_date IS NOT NULL;

-- Índice para consultas por condiciones de pago
CREATE INDEX idx_journal_entry_lines_payment_terms 
ON journal_entry_lines(payment_terms_id) 
WHERE payment_terms_id IS NOT NULL;
```

### Consultas Optimizadas
```python
# Cargar líneas con condiciones de pago
lines_with_terms = (
    session.query(JournalEntryLine)
    .options(
        joinedload(JournalEntryLine.payment_terms),
        joinedload(JournalEntryLine.third_party)
    )
    .filter(JournalEntryLine.payment_terms_id.isnot(None))
    .all()
)

# Vencimientos próximos con lazy loading controlado
upcoming_due = (
    session.query(JournalEntryLine)
    .options(selectinload(JournalEntryLine.payment_terms))
    .filter(
        JournalEntryLine.due_date.between(start_date, end_date)
    )
    .all()
)
```

## Consideraciones de Compatibilidad

### Retrocompatibilidad
- Los campos nuevos son opcionales (nullable=True)
- Las líneas existentes siguen funcionando sin modificación
- Los cálculos de fechas son backward-compatible

### Migración Gradual
```python
# Script de migración de datos existentes
def migrate_existing_lines():
    # Buscar líneas con patrones de vencimiento conocidos
    lines = session.query(JournalEntryLine).all()
    
    for line in lines:
        # Analizar patrones existentes y asignar condiciones apropiadas
        if line.description and "30 días" in line.description.lower():
            terms_30d = session.query(PaymentTerms).filter_by(code="30D").first()
            if terms_30d:
                line.payment_terms_id = terms_30d.id
        
        # Otros patrones de migración...
    
    session.commit()
```
