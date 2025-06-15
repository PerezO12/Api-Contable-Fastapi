# Ejemplos y Casos de Uso - Condiciones de Pago

## Descripción General

Esta guía presenta ejemplos prácticos y casos de uso reales para la implementación del módulo de condiciones de pago, cubriendo desde configuraciones básicas hasta escenarios complejos de facturación.

## Ejemplos de Condiciones de Pago

### 1. Condiciones Básicas

#### Pago Contado
```json
{
  "code": "CONTADO",
  "name": "Contado",
  "description": "Pago inmediato al recibir la factura",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 0,
      "percentage": 100.00,
      "description": "Pago inmediato"
    }
  ]
}
```

#### Pago a 30 Días
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

#### Pago a 60 Días
```json
{
  "code": "60D",
  "name": "60 días",
  "description": "Pago a 60 días fecha factura",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 60,
      "percentage": 100.00,
      "description": "Pago único a 60 días"
    }
  ]
}
```

### 2. Condiciones Fraccionadas

#### Pago 30-60 Días (50%-50%)
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

#### Pago 15-30-45 Días (40%-30%-30%)
```json
{
  "code": "15-30-45",
  "name": "15-30-45 días",
  "description": "Pago escalonado en tres cuotas",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 15,
      "percentage": 40.00,
      "description": "Primera cuota - 40%"
    },
    {
      "sequence": 2,
      "days": 30,
      "percentage": 30.00,
      "description": "Segunda cuota - 30%"
    },
    {
      "sequence": 3,
      "days": 45,
      "percentage": 30.00,
      "description": "Tercera cuota - 30%"
    }
  ]
}
```

### 3. Condiciones Especializadas

#### Anticipo + Saldo (20%-80%)
```json
{
  "code": "ANTICIPO-80",
  "name": "Anticipo 20% + Saldo 80%",
  "description": "20% anticipo, 80% a 30 días",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 0,
      "percentage": 20.00,
      "description": "Anticipo - 20%"
    },
    {
      "sequence": 2,
      "days": 30,
      "percentage": 80.00,
      "description": "Saldo - 80%"
    }
  ]
}
```

#### Pago Trimestral (25%-25%-25%-25%)
```json
{
  "code": "TRIMESTRAL",
  "name": "Pago trimestral",
  "description": "Cuatro pagos trimestrales iguales",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 0,
      "percentage": 25.00,
      "description": "Primer trimestre"
    },
    {
      "sequence": 2,
      "days": 90,
      "percentage": 25.00,
      "description": "Segundo trimestre"
    },
    {
      "sequence": 3,
      "days": 180,
      "percentage": 25.00,
      "description": "Tercer trimestre"
    },
    {
      "sequence": 4,
      "days": 270,
      "percentage": 25.00,
      "description": "Cuarto trimestre"
    }
  ]
}
```

## Casos de Uso por Industria

### 1. Industria Manufacturera

#### Caso: Fabricación de Maquinaria
```json
{
  "code": "MANUFACTURA",
  "name": "Fabricación por fases",
  "description": "Pagos escalonados según avance de producción",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 0,
      "percentage": 30.00,
      "description": "Anticipo - Inicio producción"
    },
    {
      "sequence": 2,
      "days": 45,
      "percentage": 40.00,
      "description": "Avance 50% - Pruebas iniciales"
    },
    {
      "sequence": 3,
      "days": 90,
      "percentage": 30.00,
      "description": "Entrega final - Instalación"
    }
  ]
}
```

**Uso en Asiento Contable:**
```json
{
  "entry_date": "2025-06-14",
  "description": "Venta maquinaria industrial - Cliente ABC",
  "lines": [
    {
      "account_id": "uuid-cuenta-clientes",
      "debit_amount": 100000.00,
      "invoice_date": "2025-06-14",
      "payment_terms_id": "uuid-manufactura",
      "third_party_id": "uuid-cliente-abc",
      "description": "Factura #MFG-001"
    },
    {
      "account_id": "uuid-cuenta-ventas",
      "credit_amount": 100000.00,
      "description": "Venta maquinaria industrial"
    }
  ]
}
```

**Cronograma Generado:**
- **2025-06-14**: $30,000 (Anticipo)
- **2025-07-29**: $40,000 (Avance 50%)
- **2025-09-12**: $30,000 (Entrega final)

### 2. Construcción

#### Caso: Proyecto de Construcción
```json
{
  "code": "CONSTRUCCION",
  "name": "Construcción por hitos",
  "description": "Pagos según hitos de construcción",
  "is_active": true,
  "payment_schedules": [
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
      "description": "Cimientos y estructura"
    },
    {
      "sequence": 3,
      "days": 60,
      "percentage": 35.00,
      "description": "Obra gris completa"
    },
    {
      "sequence": 4,
      "days": 90,
      "percentage": 25.00,
      "description": "Acabados y entrega"
    }
  ]
}
```

### 3. Servicios Profesionales

#### Caso: Consultoría de Sistemas
```json
{
  "code": "CONSULTORIA",
  "name": "Consultoría mensual",
  "description": "Pagos mensuales por servicios de consultoría",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 0,
      "percentage": 33.33,
      "description": "Mes 1 - Análisis"
    },
    {
      "sequence": 2,
      "days": 30,
      "percentage": 33.33,
      "description": "Mes 2 - Desarrollo"
    },
    {
      "sequence": 3,
      "days": 60,
      "percentage": 33.34,
      "description": "Mes 3 - Implementación"
    }
  ]
}
```

### 4. Comercio Mayorista

#### Caso: Distribución con Descuento por Pronto Pago
```json
{
  "code": "MAYORISTA-DESCUENTO",
  "name": "Mayorista con descuento",
  "description": "Descuento por pago anticipado o plazo normal",
  "is_active": true,
  "notes": "Aplicar descuento 2% si paga en primeros 10 días",
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 45,
      "percentage": 100.00,
      "description": "Pago neto a 45 días"
    }
  ]
}
```

## Escenarios de Integración Práctica

### Escenario 1: Factura Simple con Condiciones

```python
# Crear asiento con condiciones de pago
journal_entry_data = {
    "entry_date": "2025-06-14",
    "description": "Venta a cliente con términos 30-60",
    "lines": [
        {
            "account_id": "client_account_id",
            "debit_amount": 15000.00,
            "invoice_date": "2025-06-14",
            "payment_terms_id": "30-60_terms_id",
            "third_party_id": "client_id",
            "description": "Factura #FAC-001"
        },
        {
            "account_id": "sales_account_id",
            "credit_amount": 15000.00,
            "description": "Venta productos"
        }
    ]
}

# El sistema automáticamente calculará:
# - effective_invoice_date: 2025-06-14
# - Cronograma de pagos:
#   * 2025-07-14: $7,500 (50%)
#   * 2025-08-13: $7,500 (50%)
# - effective_due_date: 2025-08-13 (último pago)
```

### Escenario 2: Factura con Fecha de Factura Diferente

```python
# Factura emitida antes, asiento creado después
journal_entry_data = {
    "entry_date": "2025-06-20",  # Fecha del asiento
    "description": "Registro de factura emitida anteriormente",
    "lines": [
        {
            "account_id": "client_account_id",
            "debit_amount": 8000.00,
            "invoice_date": "2025-06-10",  # Fecha real de la factura
            "payment_terms_id": "30d_terms_id",
            "description": "Factura #FAC-002"
        }
    ]
}

# Cálculos basados en invoice_date (2025-06-10):
# - effective_due_date: 2025-07-10 (30 días desde factura)
```

### Escenario 3: Vencimiento Manual (Sin Condiciones)

```python
# Cliente con términos especiales no estándar
journal_entry_data = {
    "entry_date": "2025-06-14",
    "description": "Cliente con términos especiales",
    "lines": [
        {
            "account_id": "client_account_id",
            "debit_amount": 12000.00,
            "invoice_date": "2025-06-14",
            "due_date": "2025-08-15",  # Fecha manual específica
            "description": "Factura especial #ESP-001"
        }
    ]
}

# La fecha manual tiene prioridad:
# - effective_due_date: 2025-08-15
```

## Reportes y Análisis

### Reporte de Vencimientos Próximos

```sql
-- Líneas que vencen en los próximos 30 días
SELECT 
    je.number as asiento,
    jel.description as concepto,
    jel.amount as importe,
    jel.effective_due_date as vencimiento,
    tp.name as tercero,
    pt.name as condiciones
FROM journal_entry_lines jel
JOIN journal_entries je ON jel.journal_entry_id = je.id
LEFT JOIN third_parties tp ON jel.third_party_id = tp.id
LEFT JOIN payment_terms pt ON jel.payment_terms_id = pt.id
WHERE jel.effective_due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
ORDER BY jel.effective_due_date;
```

### Análisis de Condiciones de Pago por Cliente

```sql
-- Condiciones más utilizadas por cliente
SELECT 
    tp.name as cliente,
    pt.code as condicion,
    pt.name as descripcion,
    COUNT(*) as veces_utilizada,
    SUM(jel.debit_amount + jel.credit_amount) as importe_total
FROM journal_entry_lines jel
JOIN third_parties tp ON jel.third_party_id = tp.id
JOIN payment_terms pt ON jel.payment_terms_id = pt.id
WHERE jel.payment_terms_id IS NOT NULL
GROUP BY tp.id, tp.name, pt.code, pt.name
ORDER BY tp.name, veces_utilizada DESC;
```

## Validaciones y Casos de Error

### Caso 1: Condiciones Inválidas (Porcentajes No Suman 100%)

```python
# Intento de crear condiciones inválidas
invalid_terms = {
    "code": "INVALID",
    "name": "Condiciones inválidas",
    "payment_schedules": [
        {
            "sequence": 1,
            "days": 30,
            "percentage": 50.00
        },
        {
            "sequence": 2,
            "days": 60,
            "percentage": 40.00  # Solo suma 90%
        }
    ]
}

# Error esperado:
# "Los porcentajes deben sumar 100%, suma actual: 90%"
```

### Caso 2: Conflicto en Línea de Asiento

```python
# Intento de usar condiciones Y fecha manual
conflicted_line = {
    "account_id": "client_account_id",
    "debit_amount": 10000.00,
    "payment_terms_id": "30d_terms_id",
    "due_date": "2025-07-20"  # Conflicto
}

# Error esperado:
# "No se puede especificar condiciones de pago y fecha de vencimiento manual simultáneamente"
```

## Migración de Datos Existentes

### Script para Migrar Facturas Existentes

```python
# Migración de facturas con vencimientos fijos a condiciones de pago
def migrate_existing_invoices():
    # Buscar facturas con vencimiento a 30 días
    lines_30d = session.query(JournalEntryLine).filter(
        JournalEntryLine.due_date.isnot(None),
        # Calcular si son aproximadamente 30 días
    ).all()
    
    # Obtener condiciones de pago "30D"
    terms_30d = session.query(PaymentTerms).filter_by(code="30D").first()
    
    for line in lines_30d:
        # Calcular diferencia en días
        if line.invoice_date and line.due_date:
            days_diff = (line.due_date - line.invoice_date).days
            
            if 28 <= days_diff <= 32:  # Aproximadamente 30 días
                line.payment_terms_id = terms_30d.id
                line.due_date = None  # Limpiar fecha manual
                print(f"Migrated line {line.id} to 30D terms")
    
    session.commit()
```

## Mejores Prácticas

### 1. Nomenclatura de Códigos
- **Simples**: "30D", "60D", "90D"
- **Fraccionados**: "30-60", "15-30-45"
- **Especiales**: "CONTADO", "ANTICIPO", "TRIMESTRAL"

### 2. Descripciones Claras
- Incluir información sobre días y porcentajes
- Especificar casos especiales o condiciones
- Mantener consistencia en el formato

### 3. Gestión de Estados
- Mantener condiciones históricas inactivas
- No eliminar condiciones con uso histórico
- Crear nuevas versiones en lugar de modificar existentes

### 4. Validaciones Robustas
- Verificar suma de porcentajes en frontend y backend
- Validar secuencias lógicas
- Prevenir conflictos entre fechas manuales y automáticas

### 5. Performance
- Indexar campos de búsqueda frecuente
- Caché de condiciones activas
- Lazy loading apropiado en relaciones
