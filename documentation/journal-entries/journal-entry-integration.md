# Integración de Asientos Contables con Centros de Costo y Terceros

## Descripción General

Durante el Sprint 2, el sistema de asientos contables fue mejorado para integrar completamente los módulos de Centros de Costo y Terceros, permitiendo un mayor control y trazabilidad en los registros contables.

## Cambios en el Modelo de Datos

### Campos Agregados a JournalEntryLine

```python
# Nuevos campos en el modelo JournalEntryLine
third_party_id = Column(UUID(as_uuid=True), ForeignKey('third_parties.id'), nullable=True)
cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=True)

# Nuevas relaciones
third_party = relationship("ThirdParty", back_populates="journal_lines", lazy="select")
cost_center = relationship("CostCenter", back_populates="journal_lines", lazy="select")
```

### Validaciones Implementadas

- **Validación de Terceros**: Verificación de existencia y estado activo
- **Validación de Centros de Costo**: Confirmación de jerarquía y permisos
- **Validación Cruzada**: Coherencia entre cuenta contable, tercero y centro de costo

## Funcionalidades Nuevas

### 1. Asignación Automática de Terceros

```python
# Configuración automática basada en tipos de cuenta
AUTOMATIC_THIRD_PARTY_MAPPING = {
    "CLIENTS": "client_accounts",
    "SUPPLIERS": "supplier_accounts", 
    "EMPLOYEES": "employee_accounts"
}
```

### 2. Distribución por Centros de Costo

```python
# Ejemplo de distribución proporcional
distribution_rules = {
    "cost_center_1": 60,  # 60%
    "cost_center_2": 40   # 40%
}
```

### 3. Reportes Integrados

- **Estados de Cuenta por Tercero**: Movimientos filtrados por tercero específico
- **Análisis por Centro de Costo**: Rentabilidad y presupuesto por centro
- **Reportes Cruzados**: Análisis multidimensional tercero-centro de costo

## Uso de la API

### Crear Asiento con Tercero y Centro de Costo

```json
{
  "reference": "FAC-001",
  "description": "Factura de venta",
  "entry_type": "MANUAL",
  "entry_date": "2024-01-15",
  "lines": [
    {
      "account_id": "uuid-cuentas-por-cobrar",
      "debit_amount": 1000.00,
      "credit_amount": 0.00,
      "description": "Venta a cliente ABC",
      "third_party_id": "uuid-cliente-abc",
      "cost_center_id": "uuid-centro-ventas"
    },
    {
      "account_id": "uuid-ingresos-ventas",
      "debit_amount": 0.00,
      "credit_amount": 1000.00,
      "description": "Ingreso por venta",
      "cost_center_id": "uuid-centro-ventas"
    }
  ]
}
```

### Consultar Asientos con Filtros Avanzados

```python
# Filtros disponibles
filters = JournalEntryFilter(
    third_party_id="uuid-tercero",
    cost_center_id="uuid-centro",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

## Mejoras en el Servicio

### 1. Optimización de Consultas

```python
# Uso de selectinload para evitar N+1 queries
.options(
    selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
    selectinload(JournalEntry.lines).selectinload(JournalEntryLine.third_party),
    selectinload(JournalEntry.lines).selectinload(JournalEntryLine.cost_center)
)
```

### 2. Validaciones Mejoradas

```python
# Validación de coherencia entre entidades
def validate_line_consistency(line_data):
    """Valida coherencia entre cuenta, tercero y centro de costo"""
    if line_data.third_party_id:
        # Verificar que la cuenta permite terceros
        if not line_data.account.allows_third_parties:
            raise ValidationError("La cuenta no permite terceros")
    
    if line_data.cost_center_id:
        # Verificar que el centro permite movimientos
        if not line_data.cost_center.allows_movements:
            raise ValidationError("El centro de costo no permite movimientos")
```

## Casos de Uso Típicos

### 1. Registro de Factura de Compra

```python
# Factura con múltiples centros de costo
lines = [
    {
        "account_id": "cuentas_por_pagar",
        "credit_amount": 2000.00,
        "third_party_id": "proveedor_xyz"
    },
    {
        "account_id": "gastos_administracion", 
        "debit_amount": 1200.00,
        "cost_center_id": "centro_administrativo"
    },
    {
        "account_id": "gastos_ventas",
        "debit_amount": 800.00, 
        "cost_center_id": "centro_comercial"
    }
]
```

### 2. Pago a Proveedor

```python
# Aplicación de pago con referencia a factura original
payment_entry = {
    "reference": "PAG-001",
    "description": "Pago factura PROV-123",
    "lines": [
        {
            "account_id": "cuentas_por_pagar",
            "debit_amount": 2000.00,
            "third_party_id": "proveedor_xyz",
            "reference": "PROV-123"
        },
        {
            "account_id": "banco",
            "credit_amount": 2000.00
        }
    ]
}
```

### 3. Distribución de Gastos Comunes

```python
# Distribución automática entre centros
common_expense = {
    "reference": "DIST-001", 
    "description": "Distribución servicios públicos",
    "distribution_rule": "proportional",
    "centers": [
        {"id": "centro_a", "percentage": 40},
        {"id": "centro_b", "percentage": 35}, 
        {"id": "centro_c", "percentage": 25}
    ]
}
```

## Reportes Disponibles

### 1. Estado de Cuenta por Tercero

```python
# Endpoint: /api/v1/journal-entries/third-party-statement/{third_party_id}
response = {
    "third_party": {...},
    "period": {...},
    "movements": [...],
    "balance": {
        "initial": 0.00,
        "debits": 5000.00,
        "credits": 3000.00,
        "final": 2000.00
    }
}
```

### 2. Análisis por Centro de Costo

```python
# Endpoint: /api/v1/journal-entries/cost-center-analysis/{cost_center_id}  
response = {
    "cost_center": {...},
    "period": {...},
    "summary": {
        "total_movements": 150,
        "total_debits": 25000.00,
        "total_credits": 22000.00,
        "variance": 3000.00
    },
    "by_account": [...]
}
```

## Mejores Prácticas

### 1. Asignación de Terceros

- **Obligatorio**: En cuentas de activos y pasivos con terceros
- **Opcional**: En cuentas de ingresos y gastos 
- **Prohibido**: En cuentas patrimoniales y de resultados acumulados

### 2. Centros de Costo

- **Recomendado**: En todas las transacciones operativas
- **Obligatorio**: En gastos e ingresos directos
- **Opcional**: En movimientos de balance

### 3. Referencias Cruzadas

- Mantener consistencia en referencias entre documentos
- Usar códigos únicos para facilitar trazabilidad
- Documentar propósito en campo description

## Consideraciones Técnicas

### Performance

- Las consultas incluyen índices en `third_party_id` y `cost_center_id`
- Uso de `selectinload` para optimizar carga de relaciones
- Paginación implementada en todas las consultas de listado

### Seguridad

- Validación de permisos por centro de costo
- Auditoria completa de cambios en asientos
- Logs detallados de operaciones con terceros

### Escalabilidad

- Soporte para jerarquías complejas de centros de costo
- Distribuciones automáticas configurables
- Reportes con agregación en base de datos

## Migración de Datos

Los asientos existentes fueron migrados automáticamente:

```sql
-- Script de migración aplicado
ALTER TABLE journal_entry_lines 
ADD COLUMN third_party_id UUID REFERENCES third_parties(id);

ALTER TABLE journal_entry_lines 
ADD COLUMN cost_center_id UUID REFERENCES cost_centers(id);

-- Índices para performance
CREATE INDEX idx_journal_lines_third_party ON journal_entry_lines(third_party_id);
CREATE INDEX idx_journal_lines_cost_center ON journal_entry_lines(cost_center_id);
```

## Conclusión

La integración de centros de costo y terceros en los asientos contables proporciona:

- **Mayor Control**: Trazabilidad completa de transacciones
- **Mejor Análisis**: Reportes multidimensionales detallados  
- **Automatización**: Procesos simplificados con reglas de negocio
- **Cumplimiento**: Estándares contables y auditoría mejorada

Esta integración establece la base para funcionalidades avanzadas como análisis de rentabilidad, presupuestación por centros de costo y gestión automatizada de cuentas por cobrar/pagar.
