# Actualización de Precisión en Condiciones de Pago

## Problema Resuelto

Se ha corregido el problema donde no se podían crear términos de pago que sumaran exactamente 100% debido a limitaciones de precisión decimal.

### Error Original
```
"Payment terms '10-20-30' are invalid. Total percentage: 99.99% (Code: BUSINESS_RULE_ERROR)"
```

## Cambios Implementados

### 1. Base de Datos
- **Columna `percentage` en `payment_schedules`**: 
  - Antes: `Numeric(5, 2)` - Solo 2 decimales (ej: 33.33%)
  - Ahora: `Numeric(11, 6)` - Hasta 6 decimales (ej: 33.333334%)

### 2. Backend (API)
- **Modelos**: Actualizada definición de columna en `PaymentSchedule`
- **Validaciones**: Nueva precisión de 0.000001 (1 millonésima) en lugar de 0.01
- **Schemas**: Soporte para hasta 6 decimales en validación Pydantic

### 3. Frontend
- **Validaciones TypeScript**: Actualizada precisión en Zod schemas
- **Formularios**: Nuevas validaciones y mensajes de error más precisos
- **Utilidades**: Nueva biblioteca de utilidades para manejo de porcentajes

## Ejemplos de Uso

### Términos Válidos Ahora Soportados

```typescript
// Tres cuotas iguales - antes imposible, ahora válido
const threeEqual = [
  { percentage: 33.333334, days: 30 },
  { percentage: 33.333333, days: 60 },
  { percentage: 33.333333, days: 90 }
]; // Total: 100.000000%

// Términos complejos con alta precisión
const complexTerms = [
  { percentage: 12.500000, days: 15 },
  { percentage: 25.000000, days: 30 },
  { percentage: 37.500000, days: 45 },
  { percentage: 25.000000, days: 60 }
]; // Total: 100.000000%
```

## Migración

### Ejecutar Migración de Base de Datos
```bash
cd "API Contable"
alembic upgrade head
```

### Verificar Migración
```sql
-- Verificar nueva precisión
SELECT 
    pt.code,
    pt.name,
    ps.percentage,
    pg_typeof(ps.percentage) as type
FROM payment_terms pt
JOIN payment_schedules ps ON pt.id = ps.payment_terms_id
LIMIT 5;
```

## Validaciones Actualizadas

### Backend
- **Precisión**: 0.000001 (6 decimales)
- **Mensaje**: "El total de porcentajes debe ser exactamente 100.000000%"
- **Validación**: `abs(total - Decimal('100.000000')) <= Decimal('0.000001')`

### Frontend
- **Precisión**: 0.000001 (6 decimales)
- **Validación individual**: Máximo 6 decimales por porcentaje
- **Auto-corrección**: Utilidades para distribuir diferencias automáticamente

## Utilidades Nuevas

### Validación y Auto-corrección
```typescript
import { usePaymentTermsValidation } from '@/features/payment-terms/utils/validationUtils';

const { validateAndFixPercentages, createEqualInstallments } = usePaymentTermsValidation();

// Crear cuotas iguales automáticamente
const threeEqualInstallments = createEqualInstallments(3);
// Resultado: [33.333334, 33.333333, 33.333333]

// Validar y corregir porcentajes existentes
const result = validateAndFixPercentages([33.33, 33.33, 33.33]);
if (!result.isValid) {
  console.log(result.suggestion);
  const correctedPercentages = result.adjusted;
}
```

### Ejemplos Predefinidos
```typescript
import { commonPaymentTermsExamples } from '@/features/payment-terms/utils/validationUtils';

// Términos comunes listos para usar
const contado = commonPaymentTermsExamples.immediate;
const treintaDias = commonPaymentTermsExamples.thirtyDays;
const tresIguales = commonPaymentTermsExamples.threeEqual;
```

## Impacto

### ✅ Beneficios
- ✅ Se pueden crear términos de pago que sumen exactamente 100%
- ✅ Mayor flexibilidad para términos complejos
- ✅ Compatibilidad completa con cálculos de alta precisión
- ✅ Herramientas de auto-corrección para usuarios

### ⚠️ Consideraciones
- Los términos existentes mantienen su funcionalidad
- Los nuevos términos pueden usar la mayor precisión
- La validación es más estricta pero más precisa

## Testing

### Casos de Prueba
1. **Crear términos 33.333334/33.333333/33.333333** ✅
2. **Validar suma exacta de 100.000000%** ✅
3. **Rechazar términos con más de 6 decimales** ✅
4. **Auto-corrección de pequeñas diferencias** ✅

### Comando de Validación
```bash
cd "API Contable"
python validate_account_balances.py
```
