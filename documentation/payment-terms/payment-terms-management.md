# Gestión de Condiciones de Pago

## Descripción General

El módulo de Condiciones de Pago permite definir y gestionar términos de pago flexibles para facturas y asientos contables. Soporta desde pagos simples (contado, 30 días) hasta cronogramas complejos con múltiples vencimientos y porcentajes.

## Modelo de Datos

### PaymentTerms (payment_terms)

```python
class PaymentTerms(Base):
    __tablename__ = "payment_terms"
    
    # Campos principales
    id: UUID                    # Identificador único
    code: str                   # Código único (ej: "30D", "30-60")
    name: str                   # Nombre descriptivo
    description: str            # Descripción detallada
    is_active: bool             # Estado activo/inactivo
    notes: str                  # Notas adicionales
    
    # Metadatos de auditoría
    created_at: datetime
    updated_at: datetime
    
    # Relaciones
    payment_schedules: List[PaymentSchedule]  # Cronogramas de pago
```

### PaymentSchedule (payment_schedules)

```python
class PaymentSchedule(Base):
    __tablename__ = "payment_schedules"
    
    # Campos principales
    id: UUID                    # Identificador único
    payment_terms_id: UUID      # FK a payment_terms
    sequence: int               # Orden del pago (1, 2, 3...)
    days: int                   # Días desde fecha de factura
    percentage: Decimal         # Porcentaje a pagar (0-100)
    description: str            # Descripción del período
    
    # Metadatos
    created_at: datetime
    updated_at: datetime
    
    # Relaciones
    payment_terms: PaymentTerms
```

## Funcionalidades Principales

### 1. Creación de Condiciones de Pago

#### Ejemplo: Pago a 30 días
```json
{
  "code": "30D",
  "name": "30 días",
  "description": "Pago a 30 días fecha factura",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 30,
      "percentage": 100.00,
      "description": "Pago único a 30 días"
    }
  ]
}
```

#### Ejemplo: Pago fraccionado 30-60 días
```json
{
  "code": "30-60",
  "name": "30-60 días",
  "description": "Pago fraccionado: 50% a 30 días, 50% a 60 días",
  "is_active": true,
  "payment_schedules": [
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
}
```

### 2. Validaciones de Negocio

#### Validación de Porcentajes
- Los porcentajes de todos los cronogramas deben sumar exactamente 100%
- Cada porcentaje debe ser mayor a 0
- Máximo 2 decimales de precisión

#### Validación de Secuencias
- Cada secuencia debe ser única dentro de las condiciones de pago
- Las secuencias deben ser números enteros positivos
- Preferiblemente consecutivos (1, 2, 3...)

#### Validación de Días
- Los días deben ser números enteros no negativos
- Días = 0 representa pago inmediato (contado)
- Las secuencias posteriores deben tener más días que las anteriores

### 3. Estados y Ciclo de Vida

#### Estados Disponibles
- **Activo** (`is_active = true`): Disponible para uso en asientos
- **Inactivo** (`is_active = false`): No disponible pero mantiene historial

#### Operaciones de Estado
- **Activar**: Hacer disponible para nuevos asientos
- **Desactivar**: Ocultar de nuevas selecciones (preserva historial)

## Propiedades Calculadas

### total_percentage
```python
@property
def total_percentage(self) -> Decimal:
    """Suma total de porcentajes de todos los cronogramas"""
    return sum(schedule.percentage for schedule in self.payment_schedules)
```

### is_valid
```python
@property
def is_valid(self) -> bool:
    """Verifica validez de las condiciones de pago"""
    return (
        len(self.payment_schedules) > 0 and
        self.total_percentage == Decimal('100.00') and
        all(schedule.percentage > 0 for schedule in self.payment_schedules)
    )
```

### max_days
```python
@property
def max_days(self) -> int:
    """Días máximos hasta el último pago"""
    return max(schedule.days for schedule in self.payment_schedules) if self.payment_schedules else 0
```

## Métodos de Cálculo

### calculate_due_dates()
```python
def calculate_due_dates(self, invoice_date: date) -> List[dict]:
    """
    Calcula todas las fechas de vencimiento basadas en la fecha de factura
    
    Args:
        invoice_date: Fecha de la factura
        
    Returns:
        Lista de diccionarios con información de cada vencimiento
    """
```

### calculate_amounts()
```python
def calculate_amounts(self, total_amount: Decimal) -> List[dict]:
    """
    Calcula los importes de cada pago basado en el total
    
    Args:
        total_amount: Importe total a distribuir
        
    Returns:
        Lista con importes calculados por cronograma
    """
```

## Validaciones Específicas

### Validación de Creación
```python
def validate_payment_terms(payment_terms_data: dict) -> List[str]:
    """
    Valida datos de condiciones de pago antes de crear/actualizar
    
    Returns:
        Lista de errores encontrados
    """
    errors = []
    
    # Validar código único
    if not payment_terms_data.get('code'):
        errors.append("El código es requerido")
    
    # Validar cronogramas
    schedules = payment_terms_data.get('payment_schedules', [])
    if not schedules:
        errors.append("Debe tener al menos un cronograma de pago")
    
    # Validar suma de porcentajes
    total_percentage = sum(s.get('percentage', 0) for s in schedules)
    if total_percentage != 100:
        errors.append(f"Los porcentajes deben sumar 100%, suma actual: {total_percentage}%")
    
    return errors
```

## Casos de Uso Comunes

### 1. Contado (Pago Inmediato)
```json
{
  "code": "CONTADO",
  "name": "Contado",
  "payment_schedules": [
    {"sequence": 1, "days": 0, "percentage": 100.00}
  ]
}
```

### 2. Términos Estándar
```json
{
  "code": "30D",
  "name": "30 días",
  "payment_schedules": [
    {"sequence": 1, "days": 30, "percentage": 100.00}
  ]
}
```

### 3. Pago Fraccionado Complejo
```json
{
  "code": "15-30-45",
  "name": "15-30-45 días",
  "payment_schedules": [
    {"sequence": 1, "days": 15, "percentage": 40.00},
    {"sequence": 2, "days": 30, "percentage": 30.00},
    {"sequence": 3, "days": 45, "percentage": 30.00}
  ]
}
```

## Integración con Otros Módulos

### Con Asientos Contables
- Las líneas de asiento pueden referenciar condiciones de pago
- Cálculo automático de fechas de vencimiento
- Generación de cronogramas de pago por línea

### Con Terceros
- Condiciones de pago predeterminadas por cliente/proveedor
- Historial de términos utilizados

### Con Reportes
- Reportes de vencimientos próximos
- Análisis de términos de pago por cliente
- Dashboard de cobranza

## Consideraciones Técnicas

### Performance
- Índices en campos `code` y `is_active`
- Lazy loading de cronogramas cuando sea apropiado
- Caché de condiciones activas frecuentemente utilizadas

### Concurrencia
- Validación de unicidad de códigos a nivel de base de datos
- Manejo de actualizaciones concurrentes
- Bloqueo optimista en modificaciones

### Auditoría
- Timestamps automáticos en creación y actualización
- Preservación de historial en desactivaciones
- Log de cambios en cronogramas
