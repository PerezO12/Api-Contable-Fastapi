# Eliminación Masiva de Asientos Contables

## 📋 Resumen

Este documento describe el sistema de eliminación masiva de asientos contables, que permite eliminar múltiples asientos de forma segura y eficiente con validaciones exhaustivas y control de errores.

## 🎯 Características Principales

- **Eliminación masiva**: Hasta 100 asientos por operación
- **Validaciones estrictas**: Solo asientos en estado DRAFT pueden ser eliminados
- **Verificación previa**: Endpoint de validación antes de eliminación
- **Control granular**: Validación individual de cada asiento
- **Auditoría completa**: Registro de todas las operaciones
- **Manejo de errores**: Control detallado de errores y advertencias
- **Operaciones en lote**: Sistema unificado para múltiples operaciones

## 🔄 Flujo de Trabajo

### 1. Validación Previa (Recomendado)
```
POST /journal-entries/validate-deletion
```
- Verificar qué asientos pueden ser eliminados
- Identificar errores y advertencias
- Revisar impacto antes de proceder

### 2. Eliminación Masiva
```
POST /journal-entries/bulk-delete
```
- Eliminar múltiples asientos validados
- Opción de forzar eliminación (solo para advertencias)
- Resultado detallado de la operación

### 3. Operaciones Unificadas (Alternativo)
```
POST /journal-entries/bulk-operation?operation=delete
```
- Parte del sistema de operaciones masivas
- Integrado con otras operaciones (aprobar, cancelar)

## 📊 Esquemas de Datos

### JournalEntryDeleteValidation
```typescript
{
  journal_entry_id: UUID;           // ID del asiento
  journal_entry_number: string;     // Número del asiento
  journal_entry_description: string; // Descripción del asiento
  status: JournalEntryStatus;       // Estado actual
  can_delete: boolean;              // Si puede ser eliminado
  errors: string[];                 // Errores que impiden eliminación
  warnings: string[];               // Advertencias importantes
}
```

### BulkJournalEntryDelete
```typescript
{
  journal_entry_ids: UUID[];        // Lista de IDs (1-100)
  force_delete: boolean;            // Forzar eliminación ignorando advertencias
  reason?: string;                  // Razón para la eliminación (opcional)
}
```

### BulkJournalEntryDeleteResult
```typescript
{
  total_requested: number;          // Total de asientos solicitados
  total_deleted: number;            // Total eliminados exitosamente
  total_failed: number;             // Total que falló la eliminación
  deleted_entries: JournalEntryDeleteValidation[]; // Asientos eliminados
  failed_entries: JournalEntryDeleteValidation[];  // Asientos que fallaron
  errors: string[];                 // Errores globales
  warnings: string[];               // Advertencias globales
}
```

## 🚦 Reglas de Validación

### Reglas Críticas (Impiden Eliminación)
1. **Estado del asiento**: Solo asientos en estado `DRAFT` pueden ser eliminados
2. **Existencia**: El asiento debe existir en la base de datos
3. **Integridad**: No debe estar referenciado en otras entidades

### Advertencias (No Impiden Eliminación con force_delete)
1. **Asientos de apertura**: Pueden afectar saldos iniciales
2. **Asientos de cierre**: Pueden afectar balance del período
3. **Montos significativos**: Asientos con importes > $10,000
4. **Fecha antigua**: Asientos de períodos anteriores

## 🛡️ Seguridad y Permisos

### Permisos Requeridos
- Usuario debe tener permiso `can_create_entries`
- Mismo permiso que para creación/edición de asientos

### Auditoría
- Registro de usuario que ejecuta la eliminación
- Timestamp de la operación
- Razón proporcionada (si aplica)
- Lista de asientos eliminados

### Transacciones
- Operación atómica: todo o nada
- Rollback automático en caso de error
- Validación antes de commit

## 📚 Casos de Uso

### 1. Limpieza de Borradores
```json
{
  "journal_entry_ids": ["uuid1", "uuid2", "uuid3"],
  "force_delete": false,
  "reason": "Limpieza de asientos de prueba"
}
```

### 2. Eliminación Forzada (con Advertencias)
```json
{
  "journal_entry_ids": ["uuid1", "uuid2"],
  "force_delete": true,
  "reason": "Eliminación autorizada por supervisor"
}
```

### 3. Validación Previa
```json
["uuid1", "uuid2", "uuid3", "uuid4"]
```

## ⚠️ Consideraciones Importantes

### Limitaciones
- Máximo 100 asientos por operación
- Solo asientos en estado DRAFT
- Operación irreversible
- No se pueden eliminar asientos contabilizados

### Mejores Prácticas
1. **Siempre validar primero**: Usar endpoint de validación
2. **Revisar advertencias**: Evaluar impacto antes de forzar
3. **Proporcionar razón**: Incluir motivo para auditoría
4. **Operaciones pequeñas**: Preferir lotes de 10-50 asientos
5. **Horarios apropiados**: Evitar operaciones en horarios pico

### Manejo de Errores
- Errores individuales no detienen el proceso completo
- Resultado detallado para identificar problemas
- Logs automáticos para troubleshooting
- Rollback automático en errores críticos

## 🔗 Referencias

- [Documentación de Endpoints](./journal-entry-endpoints.md)
- [Gestión de Asientos](./journal-entry-management.md)
- [Operaciones de Asientos](./journal-entry-operations.md)
- [Pruebas de Eliminación Masiva](./bulk-journal-entry-deletion-tests.md)

## 📝 Ejemplos Completos

### Ejemplo 1: Flujo Completo de Validación y Eliminación

#### Paso 1: Validar asientos
```http
POST /journal-entries/validate-deletion
Content-Type: application/json

["550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440002"]
```

#### Respuesta:
```json
[
  {
    "journal_entry_id": "550e8400-e29b-41d4-a716-446655440001",
    "journal_entry_number": "MAN-2025-000123",
    "journal_entry_description": "Asiento de prueba",
    "status": "draft",
    "can_delete": true,
    "errors": [],
    "warnings": ["El asiento tiene un monto significativo: 15000.00"]
  },
  {
    "journal_entry_id": "550e8400-e29b-41d4-a716-446655440002",
    "journal_entry_number": "MAN-2025-000124",
    "journal_entry_description": "Otro asiento de prueba",
    "status": "posted",
    "can_delete": false,
    "errors": ["Solo se pueden eliminar asientos en estado borrador. Estado actual: posted"],
    "warnings": []
  }
]
```

#### Paso 2: Eliminar solo los válidos
```http
POST /journal-entries/bulk-delete
Content-Type: application/json

{
  "journal_entry_ids": ["550e8400-e29b-41d4-a716-446655440001"],
  "force_delete": true,
  "reason": "Eliminación de asientos de prueba autorizada"
}
```

#### Respuesta:
```json
{
  "total_requested": 1,
  "total_deleted": 1,
  "total_failed": 0,
  "deleted_entries": [
    {
      "journal_entry_id": "550e8400-e29b-41d4-a716-446655440001",
      "journal_entry_number": "MAN-2025-000123",
      "journal_entry_description": "Asiento de prueba",
      "status": "draft",
      "can_delete": true,
      "errors": [],
      "warnings": ["El asiento tiene un monto significativo: 15000.00"]
    }
  ],
  "failed_entries": [],
  "errors": [],
  "warnings": ["Asiento MAN-2025-000123 eliminado: Eliminación de asientos de prueba autorizada"]
}
```

### Ejemplo 2: Uso del Endpoint de Operaciones Masivas

```http
POST /journal-entries/bulk-operation?operation=delete&force_operation=false&reason=Limpieza%20de%20borradores
Content-Type: application/json

["550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440002"]
```

## 🏁 Conclusión

El sistema de eliminación masiva de asientos contables proporciona una solución robusta y segura para la gestión eficiente de múltiples asientos, con controles exhaustivos y transparencia completa en el proceso.
