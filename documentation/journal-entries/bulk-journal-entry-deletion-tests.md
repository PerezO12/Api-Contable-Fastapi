# Pruebas de Eliminación Masiva de Asientos Contables

## 📋 Plan de Pruebas

Este documento detalla las pruebas para validar el funcionamiento correcto del sistema de eliminación masiva de asientos contables.

## 🎯 Objetivos de las Pruebas

1. **Validar funcionalidad básica** de eliminación masiva
2. **Verificar reglas de negocio** y validaciones
3. **Confirmar manejo de errores** y casos límite
4. **Asegurar integridad de datos** y transacciones
5. **Validar seguridad** y permisos

## 🧪 Casos de Prueba

### TC001: Eliminación Exitosa de Múltiples Asientos DRAFT

**Objetivo**: Verificar eliminación correcta de asientos en estado borrador

**Precondiciones**:
- Usuario con permisos `can_create_entries`
- 3 asientos en estado DRAFT creados

**Pasos**:
1. Crear 3 asientos en estado DRAFT
2. Llamar `POST /journal-entries/bulk-delete`
3. Verificar respuesta exitosa
4. Confirmar eliminación en base de datos

**Datos de Prueba**:
```json
{
  "journal_entry_ids": ["draft-uuid-1", "draft-uuid-2", "draft-uuid-3"],
  "force_delete": false,
  "reason": "Prueba de eliminación masiva"
}
```

**Resultado Esperado**:
```json
{
  "total_requested": 3,
  "total_deleted": 3,
  "total_failed": 0,
  "deleted_entries": [/* 3 entradas */],
  "failed_entries": [],
  "errors": [],
  "warnings": [/* mensajes de auditoría */]
}
```

**Código de Estado**: `200 OK`

---

### TC002: Validación de Estados No Eliminables

**Objetivo**: Verificar que asientos en estados distintos a DRAFT no se pueden eliminar

**Precondiciones**:
- Asientos en estados: APPROVED, POSTED, CANCELLED

**Pasos**:
1. Crear asientos en diferentes estados
2. Intentar eliminarlos masivamente
3. Verificar que fallan con errores apropiados

**Datos de Prueba**:
```json
{
  "journal_entry_ids": ["approved-uuid", "posted-uuid", "cancelled-uuid"],
  "force_delete": false,
  "reason": "Prueba de validación de estados"
}
```

**Resultado Esperado**:
```json
{
  "total_requested": 3,
  "total_deleted": 0,
  "total_failed": 3,
  "deleted_entries": [],
  "failed_entries": [
    {
      "journal_entry_id": "approved-uuid",
      "status": "approved",
      "can_delete": false,
      "errors": ["Solo se pueden eliminar asientos en estado borrador. Estado actual: approved"]
    }
    /* ... otros asientos con errores similares */
  ]
}
```

---

### TC003: Validación Previa de Eliminación

**Objetivo**: Verificar endpoint de validación antes de eliminación

**Precondiciones**:
- Mix de asientos eliminables y no eliminables

**Pasos**:
1. Llamar `POST /journal-entries/validate-deletion`
2. Revisar validaciones individuales
3. Confirmar que no se elimina nada

**Datos de Prueba**:
```json
["draft-uuid", "posted-uuid", "opening-draft-uuid"]
```

**Resultado Esperado**:
```json
[
  {
    "journal_entry_id": "draft-uuid",
    "can_delete": true,
    "errors": [],
    "warnings": []
  },
  {
    "journal_entry_id": "posted-uuid",
    "can_delete": false,
    "errors": ["Solo se pueden eliminar asientos en estado borrador"]
  },
  {
    "journal_entry_id": "opening-draft-uuid",
    "can_delete": true,
    "warnings": ["Eliminar asientos de apertura puede afectar los saldos iniciales"]
  }
]
```

---

### TC004: Eliminación Forzada con Advertencias

**Objetivo**: Verificar eliminación con `force_delete=true`

**Precondiciones**:
- Asiento DRAFT con advertencias (ej: monto alto, tipo OPENING)

**Pasos**:
1. Crear asiento DRAFT con características que generen advertencias
2. Llamar eliminación con `force_delete=true`
3. Verificar eliminación exitosa

**Datos de Prueba**:
```json
{
  "journal_entry_ids": ["high-amount-draft-uuid"],
  "force_delete": true,
  "reason": "Eliminación forzada autorizada"
}
```

**Resultado Esperado**:
- Eliminación exitosa a pesar de advertencias
- Advertencias incluidas en la respuesta

---

### TC005: Límites de Operación

**Objetivo**: Verificar límites del sistema

**Subcasos**:

#### TC005a: Límite Máximo (101 asientos)
```json
{
  "journal_entry_ids": [/* 101 UUIDs */],
  "force_delete": false
}
```
**Resultado**: `422 Unprocessable Entity` con error de validación

#### TC005b: Lista Vacía
```json
{
  "journal_entry_ids": [],
  "force_delete": false
}
```
**Resultado**: `422 Unprocessable Entity` con error de validación

#### TC005c: IDs Duplicados
```json
{
  "journal_entry_ids": ["uuid-1", "uuid-1", "uuid-2"],
  "force_delete": false
}
```
**Resultado**: `422 Unprocessable Entity` con error de validación

---

### TC006: Manejo de Asientos No Existentes

**Objetivo**: Verificar manejo de UUIDs que no existen

**Pasos**:
1. Incluir UUIDs válidos y no existentes
2. Verificar manejo correcto de cada caso

**Datos de Prueba**:
```json
{
  "journal_entry_ids": ["valid-uuid", "non-existent-uuid"],
  "force_delete": false
}
```

**Resultado Esperado**:
- Asiento válido eliminado
- Asiento no existente en `failed_entries` con error apropiado

---

### TC007: Operaciones Masivas Unificadas

**Objetivo**: Verificar endpoint de operaciones masivas

**Subcasos**:

#### TC007a: Operación Delete
```http
POST /journal-entries/bulk-operation?operation=delete&force_operation=false&reason=Prueba
```

#### TC007b: Operación Inválida
```http
POST /journal-entries/bulk-operation?operation=invalid
```
**Resultado**: `422 Unprocessable Entity`

---

### TC008: Permisos y Seguridad

**Objetivo**: Verificar control de acceso

**Subcasos**:

#### TC008a: Usuario Sin Permisos
- Usuario sin `can_create_entries`
- **Resultado**: `403 Forbidden`

#### TC008b: Usuario No Autenticado
- Sin token de autenticación
- **Resultado**: `401 Unauthorized`

---

### TC009: Integridad Transaccional

**Objetivo**: Verificar comportamiento de transacciones

**Pasos**:
1. Crear escenario donde algunos asientos pueden eliminarse y otros no
2. Simular error durante eliminación
3. Verificar rollback correcto

**Configuración**:
- 5 asientos DRAFT válidos
- 1 asiento con error simulado durante eliminación

**Resultado Esperado**:
- Solo asientos exitosos confirmados
- Error no afecta otros asientos válidos

---

### TC010: Rendimiento y Estrés

**Objetivo**: Verificar rendimiento con cargas altas

**Subcasos**:

#### TC010a: Máximo Permitido (100 asientos)
- Tiempo de respuesta < 10 segundos
- Memoria estable

#### TC010b: Operaciones Concurrentes
- Múltiples usuarios ejecutando eliminaciones simultáneas
- Sin deadlocks o corruption de datos

---

## 🔧 Configuración de Pruebas

### Datos de Prueba Requeridos

```sql
-- Asientos en diferentes estados
INSERT INTO journal_entries (status, entry_type, total_debit, total_credit) VALUES
('draft', 'manual', 1000.00, 1000.00),
('approved', 'manual', 2000.00, 2000.00),
('posted', 'manual', 3000.00, 3000.00),
('cancelled', 'manual', 4000.00, 4000.00),
('draft', 'opening', 15000.00, 15000.00),
('draft', 'closing', 5000.00, 5000.00);
```

### Variables de Entorno
```bash
TEST_API_BASE_URL=http://localhost:8000/api/v1
TEST_USER_TOKEN=<token-with-permissions>
TEST_ADMIN_TOKEN=<admin-token>
TEST_NO_PERMISSIONS_TOKEN=<token-without-permissions>
```

### Utilidades de Prueba

```python
async def create_test_journal_entry(status: str, entry_type: str, amount: Decimal) -> UUID:
    """Helper para crear asientos de prueba"""
    pass

async def cleanup_test_data():
    """Limpiar datos de prueba después de cada test"""
    pass

def assert_bulk_delete_result(result: dict, expected_deleted: int, expected_failed: int):
    """Helper para validar resultados de eliminación masiva"""
    assert result["total_deleted"] == expected_deleted
    assert result["total_failed"] == expected_failed
    assert len(result["deleted_entries"]) == expected_deleted
    assert len(result["failed_entries"]) == expected_failed
```

## 📊 Métricas de Calidad

### Cobertura de Código
- **Objetivo**: >95% en funcionalidades de eliminación masiva
- **Incluir**: Validaciones, manejo de errores, casos límite

### Tiempo de Respuesta
- **Eliminación de 10 asientos**: <2 segundos
- **Eliminación de 50 asientos**: <5 segundos
- **Eliminación de 100 asientos**: <10 segundos

### Robustez
- **Sin memory leaks** en operaciones repetidas
- **Transacciones consistentes** bajo carga
- **Manejo graceful** de errores de BD

## 🚀 Automatización

### CI/CD Pipeline
```yaml
test_bulk_deletion:
  runs-on: ubuntu-latest
  steps:
    - name: Setup test database
      run: |
        python create_test_data.py
    
    - name: Run bulk deletion tests
      run: |
        pytest tests/test_bulk_journal_deletion.py -v
    
    - name: Cleanup
      run: |
        python cleanup_test_data.py
```

### Test Suites

#### Suite 1: Smoke Tests (Rápidos)
- TC001, TC002, TC008a
- Ejecutar en cada commit

#### Suite 2: Integration Tests (Completos)
- Todos los casos de prueba
- Ejecutar antes de releases

#### Suite 3: Performance Tests
- TC010a, TC010b
- Ejecutar semanalmente

## 📝 Reporte de Resultados

### Template de Reporte
```markdown
# Resultados de Pruebas - Eliminación Masiva Journal Entries

## Resumen
- **Fecha**: YYYY-MM-DD
- **Versión**: v1.0.0
- **Total de Pruebas**: 25
- **Exitosas**: 24
- **Fallidas**: 1

## Detalles
| Test ID | Descripción | Estado | Tiempo | Notas |
|---------|-------------|--------|--------|-------|
| TC001   | Eliminación exitosa | ✅ PASS | 1.2s | - |
| TC002   | Validación estados | ✅ PASS | 0.8s | - |
| TC010a  | Performance 100 items | ❌ FAIL | 12s | Excede límite |

## Acciones Requeridas
1. Optimizar query de eliminación masiva
2. Revisar índices de base de datos
```

## 🏁 Conclusión

Este plan de pruebas asegura la calidad y confiabilidad del sistema de eliminación masiva de asientos contables, cubriendo funcionalidad, seguridad, rendimiento y casos límite.
