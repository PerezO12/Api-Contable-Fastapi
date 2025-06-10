# Tipos de Asientos Contables

Este documento describe los diferentes tipos y estados de asientos contables disponibles en el sistema API Contable.

## 📋 Tipos de Asiento

El sistema soporta diferentes tipos de asientos contables para satisfacer diversas necesidades de registro contable:

```python
class JournalEntryType(str, Enum):
    """Tipos de asiento contable"""
    MANUAL = "manual"        # Asiento manual
    AUTOMATIC = "automatic"  # Asiento automático
    ADJUSTMENT = "adjustment"# Asiento de ajuste
    OPENING = "opening"      # Asiento de apertura
    CLOSING = "closing"      # Asiento de cierre
    REVERSAL = "reversal"    # Asiento de reversión
```

### 🖋️ Asientos Manuales (MANUAL)

- **Descripción**: Asientos creados directamente por usuarios del sistema
- **Características**:
  - Requieren aprobación explícita antes de ser contabilizados
  - Totalmente flexibles en términos de cuentas y montos
  - Son los más comunes en operaciones diarias
  - Pueden representar cualquier tipo de transacción
- **Validaciones específicas**:
  - Requieren documentación adecuada (descripción, referencias)
  - Verificación estándar de partida doble

### 🤖 Asientos Automáticos (AUTOMATIC)

- **Descripción**: Asientos generados automáticamente por el sistema
- **Características**:
  - Generados por procesos automáticos
  - No requieren aprobación manual (pre-aprobados)
  - Pueden ser generados en lotes
  - Se utilizan para operaciones recurrentes o programadas
- **Validaciones específicas**:
  - Se verifican automáticamente
  - Deben contener referencia al proceso que los generó
  - No pueden ser modificados manualmente una vez creados

### ⚙️ Asientos de Ajuste (ADJUSTMENT)

- **Descripción**: Asientos para corregir errores o realizar ajustes contables
- **Características**:
  - Usados para correcciones o reclasificaciones
  - Requieren mayor nivel de autorización
  - Deben contener referencia a la razón del ajuste
  - Generalmente afectan periodos ya cerrados
- **Validaciones específicas**:
  - Requieren nota explicativa detallada
  - Requieren aprobación de nivel jerárquico superior
  - Verificación adicional de permisos

### 📅 Asientos de Apertura (OPENING)

- **Descripción**: Asientos para iniciar un nuevo periodo contable
- **Características**:
  - Realizados al inicio de un periodo fiscal
  - Transfieren saldos del periodo anterior
  - Solo pueden existir uno por periodo fiscal
  - Afectan principalmente cuentas de balance
- **Validaciones específicas**:
  - Solo pueden ser creados al inicio de periodo
  - Verificación de consistencia con saldos finales anteriores
  - Requieren permisos especiales

### 📚 Asientos de Cierre (CLOSING)

- **Descripción**: Asientos para cerrar un periodo contable
- **Características**:
  - Realizados al final de un periodo fiscal
  - Cierran cuentas temporales (ingresos/gastos)
  - Solo pueden existir uno por periodo fiscal
  - Afectan cuentas de resultados y utilidades retenidas
- **Validaciones específicas**:
  - Solo pueden ser creados al final de periodo
  - Requieren que todos los demás asientos estén contabilizados
  - Verificación de cierre de cuentas temporales
  - Requieren permisos especiales

### ↩️ Asientos de Reversión (REVERSAL)

- **Descripción**: Asientos para revertir efectos de otros asientos
- **Características**:
  - Invierten los débitos y créditos del asiento original
  - Mantienen referencia al asiento original
  - Pueden ser generados automáticamente
  - Se usan para anular transacciones sin eliminar registros
- **Validaciones específicas**:
  - Verificación de correspondencia con asiento original
  - Razón obligatoria para la reversión
  - No pueden ser revertidos (para evitar ciclos)

## 🚦 Estados de Asientos Contables

Los asientos contables pueden tener diferentes estados a lo largo de su ciclo de vida:

```python
class JournalEntryStatus(str, Enum):
    """Estados del asiento contable"""
    DRAFT = "draft"        # Borrador
    PENDING = "pending"    # Pendiente de aprobación
    APPROVED = "approved"  # Aprobado
    POSTED = "posted"      # Contabilizado
    CANCELLED = "cancelled"# Anulado
```

### 📝 Borrador (DRAFT)

- **Descripción**: Estado inicial de un asiento recién creado
- **Características**:
  - Puede ser modificado libremente
  - No afecta saldos contables
  - Puede contener errores o estar incompleto
  - Puede ser eliminado del sistema
- **Transiciones posibles**:
  - → PENDING (al enviarse para aprobación)
  - → APPROVED (si no requiere flujo de aprobación)
  - → Eliminación (no deja registro)

### ⏳ Pendiente (PENDING)

- **Descripción**: Asiento en espera de aprobación
- **Características**:
  - Validado sintácticamente pero pendiente de revisión
  - No puede ser modificado sin volver a borrador
  - No afecta saldos contables
  - Visible en bandeja de aprobaciones
- **Transiciones posibles**:
  - → DRAFT (si se rechaza o requiere cambios)
  - → APPROVED (si se aprueba)

### ✅ Aprobado (APPROVED)

- **Descripción**: Asiento revisado y aprobado
- **Características**:
  - Validado tanto sintáctica como conceptualmente
  - No puede ser modificado (solo cancelado)
  - Listo para ser contabilizado
  - Conserva información de quién lo aprobó
- **Transiciones posibles**:
  - → POSTED (al contabilizarse)
  - → CANCELLED (si se cancela antes de contabilizar)

### 📊 Contabilizado (POSTED)

- **Descripción**: Asiento registrado en los libros contables
- **Características**:
  - Afecta los saldos de las cuentas involucradas
  - Absolutamente inmutable
  - Registra fecha efectiva de contabilización
  - Forma parte de los reportes financieros
- **Transiciones posibles**:
  - → CANCELLED (mediante proceso formal de cancelación)

### ❌ Cancelado (CANCELLED)

- **Descripción**: Asiento anulado o invalidado
- **Características**:
  - Requiere razón explícita de cancelación
  - Si estaba contabilizado, requiere asiento de reversión
  - No puede ser restaurado o modificado
  - Se conserva por razones de auditoría
- **Transiciones posibles**:
  - Estado terminal (no permite más cambios)

## 🔄 Transiciones de Estado

El siguiente diagrama muestra las transiciones válidas entre estados:

```
DRAFT ──────┐
  │         │
  ▼         │
PENDING     │
  │         │
  ▼         │
APPROVED ───┤
  │         │
  ▼         │
POSTED ─────┤
  │         │
  ▼         │
CANCELLED ◀─┘
```

## 🔍 Consideraciones por Tipo y Estado

| Tipo \ Estado | DRAFT | PENDING | APPROVED | POSTED | CANCELLED |
|---------------|-------|---------|----------|--------|-----------|
| MANUAL        | ✓     | ✓       | ✓        | ✓      | ✓         |
| AUTOMATIC     | ✓     | ✗       | ✓        | ✓      | ✓         |
| ADJUSTMENT    | ✓     | ✓       | ✓        | ✓      | ✓         |
| OPENING       | ✓     | ✓       | ✓        | ✓      | ✓         |
| CLOSING       | ✓     | ✓       | ✓        | ✓      | ✓         |
| REVERSAL      | ✓     | ✗       | ✓        | ✓      | ✗         |

**Leyenda**:
- ✓: Estado permitido para el tipo
- ✗: Estado no aplicable o prohibido para el tipo

## 🛠️ Implicaciones Técnicas

- Los asientos de tipo AUTOMATIC pueden omitir el estado PENDING
- Los asientos de tipo REVERSAL no pueden ser cancelados (ya son cancelaciones)
- Los asientos OPENING y CLOSING requieren validaciones adicionales de fechas
- Los asientos ADJUSTMENT requieren permisos especiales en todos sus estados
