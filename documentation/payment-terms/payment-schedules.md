# Cronogramas de Pago

## Descripción General

Los cronogramas de pago (PaymentSchedule) son componentes que definen los términos específicos de cada pago dentro de unas condiciones de pago. Permiten configurar pagos múltiples con diferentes días y porcentajes.

## Modelo de Datos

### PaymentSchedule

```python
class PaymentSchedule(Base):
    __tablename__ = "payment_schedules"
    
    # Identificación
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    payment_terms_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_terms.id"), 
        nullable=False
    )
    
    # Configuración del pago
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    percentage: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), 
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Metadatos
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )
    
    # Relaciones
    payment_terms: Mapped["PaymentTerms"] = relationship(
        "PaymentTerms", 
        back_populates="payment_schedules"
    )
```

## Propiedades y Validaciones

### Campos Obligatorios
- `payment_terms_id`: Referencia a las condiciones de pago padre
- `sequence`: Orden del pago (1, 2, 3, etc.)
- `days`: Días desde la fecha de factura hasta el vencimiento
- `percentage`: Porcentaje del total a pagar (0.01 - 100.00)

### Campos Opcionales
- `description`: Descripción personalizada del cronograma

### Restricciones de Negocio

#### Secuencia Única
```python
@validates('sequence')
def validate_sequence(self, key, sequence):
    if sequence <= 0:
        raise ValueError("La secuencia debe ser un número positivo")
    return sequence
```

#### Días No Negativos
```python
@validates('days')
def validate_days(self, key, days):
    if days < 0:
        raise ValueError("Los días no pueden ser negativos")
    return days
```

#### Porcentaje Válido
```python
@validates('percentage')
def validate_percentage(self, key, percentage):
    if percentage <= 0 or percentage > 100:
        raise ValueError("El porcentaje debe estar entre 0.01 y 100.00")
    return percentage
```

## Métodos de Cálculo

### calculate_payment_date()
```python
def calculate_payment_date(self, invoice_date: datetime) -> datetime:
    """
    Calcula la fecha de pago basada en los días del cronograma
    
    Args:
        invoice_date: Fecha de la factura
        
    Returns:
        Fecha calculada de vencimiento del pago
    """
    from datetime import timedelta
    return invoice_date + timedelta(days=self.days)
```

### calculate_amount()
```python
def calculate_amount(self, total_amount: Decimal) -> Decimal:
    """
    Calcula el importe específico basado en el porcentaje
    
    Args:
        total_amount: Importe total de la factura
        
    Returns:
        Importe calculado para este cronograma
    """
    return (total_amount * self.percentage / Decimal('100')).quantize(
        Decimal('0.01')
    )
```

### is_valid_in_sequence()
```python
def is_valid_in_sequence(self, other_schedules: List['PaymentSchedule']) -> bool:
    """
    Valida que el cronograma sea consistente con otros en la misma condición
    
    Args:
        other_schedules: Otros cronogramas de la misma condición de pago
        
    Returns:
        True si es válido en secuencia
    """
    # Verificar secuencia única
    sequences = [s.sequence for s in other_schedules if s.id != self.id]
    if self.sequence in sequences:
        return False
    
    # Verificar que días posteriores tengan secuencias mayores
    for schedule in other_schedules:
        if schedule.id != self.id:
            if schedule.days > self.days and schedule.sequence < self.sequence:
                return False
            if schedule.days < self.days and schedule.sequence > self.sequence:
                return False
    
    return True
```

## Tipos de Cronogramas Comunes

### 1. Pago Único Inmediato (Contado)
```python
{
    "sequence": 1,
    "days": 0,
    "percentage": 100.00,
    "description": "Pago contado"
}
```

### 2. Pago Único a Plazo
```python
{
    "sequence": 1,
    "days": 30,
    "percentage": 100.00,
    "description": "Pago a 30 días"
}
```

### 3. Pago Fraccionado en Dos Partes
```python
[
    {
        "sequence": 1,
        "days": 30,
        "percentage": 50.00,
        "description": "Primer pago - 50%"
    },
    {
        "sequence": 2,
        "days": 60,
        "percentage": 50.00,
        "description": "Segundo pago - 50%"
    }
]
```

### 4. Pago Escalonado Tres Cuotas
```python
[
    {
        "sequence": 1,
        "days": 15,
        "percentage": 40.00,
        "description": "Entrega inicial - 40%"
    },
    {
        "sequence": 2,
        "days": 30,
        "percentage": 30.00,
        "description": "Segundo pago - 30%"
    },
    {
        "sequence": 3,
        "days": 45,
        "percentage": 30.00,
        "description": "Pago final - 30%"
    }
]
```

### 5. Cronograma Personalizado
```python
[
    {
        "sequence": 1,
        "days": 0,
        "percentage": 20.00,
        "description": "Anticipo - 20%"
    },
    {
        "sequence": 2,
        "days": 30,
        "percentage": 40.00,
        "description": "Pago intermedio - 40%"
    },
    {
        "sequence": 3,
        "days": 60,
        "percentage": 40.00,
        "description": "Pago final - 40%"
    }
]
```

## Validaciones de Cronograma

### Validación Individual
```python
def validate_schedule(schedule: dict) -> List[str]:
    """
    Valida un cronograma individual
    
    Returns:
        Lista de errores encontrados
    """
    errors = []
    
    if schedule.get('sequence', 0) <= 0:
        errors.append("La secuencia debe ser un número positivo")
    
    if schedule.get('days', -1) < 0:
        errors.append("Los días no pueden ser negativos")
    
    percentage = schedule.get('percentage', 0)
    if percentage <= 0 or percentage > 100:
        errors.append("El porcentaje debe estar entre 0.01 y 100.00")
    
    return errors
```

### Validación de Conjunto
```python
def validate_schedules_set(schedules: List[dict]) -> List[str]:
    """
    Valida un conjunto de cronogramas
    
    Returns:
        Lista de errores encontrados
    """
    errors = []
    
    if not schedules:
        errors.append("Debe tener al menos un cronograma")
        return errors
    
    # Verificar secuencias únicas
    sequences = [s.get('sequence') for s in schedules]
    if len(sequences) != len(set(sequences)):
        errors.append("Las secuencias deben ser únicas")
    
    # Verificar porcentajes suman 100%
    total_percentage = sum(s.get('percentage', 0) for s in schedules)
    if abs(total_percentage - 100.00) > 0.01:
        errors.append(f"Los porcentajes deben sumar 100%, suma actual: {total_percentage}%")
    
    # Verificar orden lógico de días
    sorted_schedules = sorted(schedules, key=lambda x: x.get('sequence', 0))
    for i in range(1, len(sorted_schedules)):
        current_days = sorted_schedules[i].get('days', 0)
        previous_days = sorted_schedules[i-1].get('days', 0)
        if current_days < previous_days:
            errors.append(
                f"Los días de secuencia {sorted_schedules[i].get('sequence')} "
                f"no pueden ser menores que la secuencia anterior"
            )
    
    return errors
```

## Casos de Uso Específicos

### Industria Manufacturera
```python
# Pago escalonado por fases de producción
manufacturing_schedule = [
    {
        "sequence": 1,
        "days": 0,
        "percentage": 30.00,
        "description": "Anticipo - Inicio producción"
    },
    {
        "sequence": 2,
        "days": 30,
        "percentage": 40.00,
        "description": "Avance - 50% producción"
    },
    {
        "sequence": 3,
        "days": 60,
        "percentage": 30.00,
        "description": "Final - Entrega producto"
    }
]
```

### Servicios Profesionales
```python
# Pago mensual por servicios
professional_services = [
    {
        "sequence": 1,
        "days": 0,
        "percentage": 25.00,
        "description": "Mes 1"
    },
    {
        "sequence": 2,
        "days": 30,
        "percentage": 25.00,
        "description": "Mes 2"
    },
    {
        "sequence": 3,
        "days": 60,
        "percentage": 25.00,
        "description": "Mes 3"
    },
    {
        "sequence": 4,
        "days": 90,
        "percentage": 25.00,
        "description": "Mes 4"
    }
]
```

### Construcción
```python
# Pagos por hitos de construcción
construction_schedule = [
    {
        "sequence": 1,
        "days": 0,
        "percentage": 15.00,
        "description": "Firma contrato"
    },
    {
        "sequence": 2,
        "days": 30,
        "percentage": 25.00,
        "description": "Cimientos completados"
    },
    {
        "sequence": 3,
        "days": 60,
        "percentage": 35.00,
        "description": "Estructura terminada"
    },
    {
        "sequence": 4,
        "days": 90,
        "percentage": 25.00,
        "description": "Entrega final"
    }
]
```

## Optimizaciones y Performance

### Índices Recomendados
```sql
-- Índice compuesto para búsquedas por condición y secuencia
CREATE INDEX idx_payment_schedules_terms_sequence 
ON payment_schedules(payment_terms_id, sequence);

-- Índice para ordenamiento por días
CREATE INDEX idx_payment_schedules_days 
ON payment_schedules(days);
```

### Consultas Optimizadas
```python
# Cargar cronogramas ordenados por secuencia
schedules = (
    session.query(PaymentSchedule)
    .filter(PaymentSchedule.payment_terms_id == terms_id)
    .order_by(PaymentSchedule.sequence)
    .all()
)

# Encontrar el cronograma con mayor días (último pago)
last_schedule = (
    session.query(PaymentSchedule)
    .filter(PaymentSchedule.payment_terms_id == terms_id)
    .order_by(PaymentSchedule.days.desc())
    .first()
)
```

### Caché de Cálculos
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_payment_dates(payment_terms_id: str, invoice_date: str) -> List[dict]:
    """
    Calcula fechas de pago con caché para términos frecuentemente utilizados
    """
    # Implementación con caché automático
    pass
```

## Migración y Mantenimiento

### Script de Migración
```sql
-- Crear tabla de cronogramas
CREATE TABLE payment_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_terms_id UUID NOT NULL REFERENCES payment_terms(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    days INTEGER NOT NULL CHECK (days >= 0),
    percentage DECIMAL(5,2) NOT NULL CHECK (percentage > 0 AND percentage <= 100),
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraint de secuencia única por condición de pago
    UNIQUE(payment_terms_id, sequence)
);
```

### Verificación de Integridad
```sql
-- Query para verificar que porcentajes suman 100%
SELECT 
    pt.code,
    pt.name,
    SUM(ps.percentage) as total_percentage,
    COUNT(ps.id) as schedules_count
FROM payment_terms pt
JOIN payment_schedules ps ON pt.id = ps.payment_terms_id
WHERE pt.is_active = true
GROUP BY pt.id, pt.code, pt.name
HAVING SUM(ps.percentage) != 100.00;
```
