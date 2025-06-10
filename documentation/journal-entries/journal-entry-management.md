# Gestión de Asientos Contables

Este documento describe el sistema de gestión de asientos contables (Journal Entries) en el API Contable.

## 📋 Descripción General

Los asientos contables son el componente principal del sistema de contabilidad, permitiendo registrar transacciones financieras utilizando el principio de partida doble. Cada asiento contable consiste en un encabezado (header) y múltiples líneas de detalle que afectan diferentes cuentas contables.

## 🏗️ Arquitectura

El módulo de asientos contables implementa el patrón Header-Detail para representar la estructura de partida doble:

- **Header (Encabezado)**: Contiene información general del asiento como fecha, referencia, descripción y estado
- **Detail (Detalle/Líneas)**: Contiene los movimientos específicos que afectan a cada cuenta

## 📊 Modelo de Datos

### JournalEntry (Asiento Contable)

```python
class JournalEntry(Base):
    """
    Modelo de asientos contables (encabezado)
    Implementa el patrón Header-Detail para doble partida
    """
    __tablename__ = "journal_entries"
    
    # Información básica del asiento
    number: Mapped[str]              # Número único del asiento
    reference: Mapped[Optional[str]] # Referencia externa opcional
    description: Mapped[str]         # Descripción general del asiento
    
    # Tipo de asiento
    entry_type: Mapped[JournalEntryType]
    
    # Fechas
    entry_date: Mapped[datetime]             # Fecha del asiento
    posting_date: Mapped[Optional[datetime]] # Fecha de contabilización
    
    # Estado y control
    status: Mapped[JournalEntryStatus]
    
    # Totales (para validación de cuadre)
    total_debit: Mapped[Decimal]
    total_credit: Mapped[Decimal]
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID]
    approved_by_id: Mapped[Optional[uuid.UUID]]
    posted_by_id: Mapped[Optional[uuid.UUID]]
    cancelled_by_id: Mapped[Optional[uuid.UUID]]
    
    # Fechas de auditoría
    approved_at: Mapped[Optional[datetime]]
    posted_at: Mapped[Optional[datetime]]
    cancelled_at: Mapped[Optional[datetime]]
    
    # Metadatos
    notes: Mapped[Optional[str]]
    external_reference: Mapped[Optional[str]]
    
    # Relationships
    lines: Mapped[List["JournalEntryLine"]]
    created_by: Mapped["User"]
    approved_by: Mapped[Optional["User"]]
    posted_by: Mapped[Optional["User"]]
    cancelled_by: Mapped[Optional["User"]]
```

### JournalEntryLine (Línea de Asiento)

```python
class JournalEntryLine(Base):
    """
    Modelo de líneas de asientos contables (detalle)
    Cada línea representa un movimiento en una cuenta
    """
    __tablename__ = "journal_entry_lines"

    # Relación con el asiento
    journal_entry_id: Mapped[uuid.UUID]
    
    # Relación con la cuenta
    account_id: Mapped[uuid.UUID]
    
    # Importes
    debit_amount: Mapped[Decimal]  # Monto débito
    credit_amount: Mapped[Decimal] # Monto crédito
    
    # Descripción específica de la línea
    description: Mapped[Optional[str]]
    
    # Referencias adicionales
    reference: Mapped[Optional[str]]
    third_party_id: Mapped[Optional[str]]  # Para cuentas que requieren terceros
    cost_center_id: Mapped[Optional[str]]  # Para centros de costo
    
    # Orden de la línea en el asiento
    line_number: Mapped[int]

    # Relationships
    journal_entry: Mapped["JournalEntry"]
    account: Mapped["Account"]
```

## 🔍 Propiedades Calculadas

El modelo JournalEntry incluye propiedades calculadas para facilitar la gestión y validación:

```python
@property
def is_balanced(self) -> bool:
    """Verifica si el asiento está balanceado (suma débitos = suma créditos)"""
    return self.total_debit == self.total_credit

@property
def can_be_posted(self) -> bool:
    """Verifica si el asiento puede ser contabilizado"""
    return (
        self.status == JournalEntryStatus.APPROVED and
        self.is_balanced and
        len(self.lines) >= 2 and  # Mínimo 2 líneas para doble partida
        all(line.is_valid for line in self.lines)
    )

@property
def can_be_modified(self) -> bool:
    """Verifica si el asiento puede ser modificado"""
    return self.status in [JournalEntryStatus.DRAFT, JournalEntryStatus.PENDING]
```

## 🧪 Métodos de Validación

Implementa métodos de validación para garantizar la integridad de los datos:

```python
def calculate_totals(self) -> None:
    """Calcula los totales de débito y crédito"""
    self.total_debit = Decimal(str(sum(line.debit_amount for line in self.lines)))
    self.total_credit = Decimal(str(sum(line.credit_amount for line in self.lines)))

def validate_entry(self) -> List[str]:
    """
    Valida el asiento contable y retorna lista de errores
    """
    errors = []
    
    # Validar que tenga al menos 2 líneas
    if len(self.lines) < 2:
        errors.append("El asiento debe tener al menos 2 líneas")
    
    # Validar balance
    if not self.is_balanced:
        errors.append(f"El asiento no está balanceado. Débitos: {self.total_debit}, Créditos: {self.total_credit}")
    
    # Validar líneas individuales
    for i, line in enumerate(self.lines, 1):
        line_errors = line.validate_line()
        for error in line_errors:
            errors.append(f"Línea {i}: {error}")
    
    # Validar que no todas las líneas sean cero
    total_amount = Decimal(str(sum(line.debit_amount + line.credit_amount for line in self.lines)))
    if total_amount == 0:
        errors.append("El asiento no puede tener todas las líneas en cero")
    
    return errors
```

## 🔄 Ciclo de Vida

Los asientos contables siguen un ciclo de vida bien definido:

1. **Creación (DRAFT)**: El asiento se crea inicialmente en estado borrador
2. **Aprobación (APPROVED)**: El asiento es revisado y aprobado
3. **Contabilización (POSTED)**: El asiento se contabiliza, afectando los saldos de las cuentas
4. **Cancelación (CANCELLED)** *(opcional)*: El asiento puede ser cancelado

Cada transición de estado requiere validaciones específicas y puede actualizar metadatos de auditoría.

## 🚦 Estados del Asiento

Los asientos contables pueden tener los siguientes estados:

```python
class JournalEntryStatus(str, Enum):
    """Estados del asiento contable"""
    DRAFT = "draft"       # Borrador
    PENDING = "pending"   # Pendiente de aprobación
    APPROVED = "approved" # Aprobado
    POSTED = "posted"     # Contabilizado
    CANCELLED = "cancelled" # Anulado
```

## 🔐 Seguridad y Auditoría

Cada asiento contable registra:

- Quién lo creó
- Quién lo aprobó
- Quién lo contabilizó
- Quién lo canceló (si aplica)
- Fechas de cada operación

Esta información facilita la auditoría y trazabilidad de todas las operaciones contables.

## 📝 Consideraciones Especiales

- **Invariabilidad**: Una vez contabilizado, un asiento no puede ser modificado
- **Partida Doble**: El total de débitos debe ser igual al total de créditos
- **Líneas Mínimas**: Un asiento debe tener al menos 2 líneas
- **Validación de Cuentas**: Las cuentas deben permitir movimientos
