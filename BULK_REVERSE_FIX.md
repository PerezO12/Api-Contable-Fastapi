# Fix para Error de Reversión Masiva - Bulk Reverse

## Problema Identificado

El error 422 "UUID parsing error" ocurre porque el frontend está enviando la cadena `'bulk'` como parámetro UUID en lugar de usar la URL correcta.

### Error Actual:
```
AxiosError: Request failed with status code 422
detail: [
  {
    "type": "uuid_parsing", 
    "loc": ["path", "journal_entry_id"], 
    "msg": "Input should be a valid UUID, invalid character: ...", 
    "input": "bulk"
  },
  {
    "type": "missing", 
    "loc": ["body"], 
    "msg": "Field required", 
    "input": null
  }
]
```

## Causa Raíz

El frontend está construyendo incorrectamente la URL para la reversión masiva. Está usando:
```
/api/v1/journal-entries/bulk/reverse  ❌ INCORRECTO
```

En lugar de:
```
/api/v1/journal-entries/bulk-reverse  ✅ CORRECTO
```

## Solución

### 1. Verificar la URL en el Frontend

El servicio de frontend debe usar la URL correcta:

```typescript
// INCORRECTO ❌
async bulkReverseEntries(entryIds: string[], reason: string) {
  return await this.apiClient.post(`/journal-entries/bulk/reverse`, {
    journal_entry_ids: entryIds,
    reason: reason
  });
}

// CORRECTO ✅
async bulkReverseEntries(entryIds: string[], reason: string) {
  return await this.apiClient.post(`/journal-entries/bulk-reverse`, {
    journal_entry_ids: entryIds,
    reason: reason,
    force_reverse: false
  });
}
```

### 2. Verificar el Schema de Datos

El backend espera este formato:

```json
{
  "journal_entry_ids": ["uuid1", "uuid2", "uuid3"],
  "force_reverse": false,
  "reason": "Razón para la reversión masiva"
}
```

### 3. Endpoints Correctos

**Backend Definido:**
- `POST /api/v1/journal-entries/bulk-reverse` - Reversión masiva
- `POST /api/v1/journal-entries/validate-reverse` - Validación previa

**No existe:**
- `POST /api/v1/journal-entries/bulk/reverse` ❌
- `POST /api/v1/journal-entries/{id}/bulk/reverse` ❌

## Código de Ejemplo Corregido

### Frontend (TypeScript)
```typescript
export class JournalEntryService {
  async bulkReverseEntries(
    entryIds: string[], 
    reason: string, 
    forceReverse: boolean = false
  ) {
    const response = await this.apiClient.post(
      '/api/v1/journal-entries/bulk-reverse',  // URL CORRECTA
      {
        journal_entry_ids: entryIds,
        reason: reason,
        force_reverse: forceReverse
      }
    );
    return response.data;
  }

  async validateBulkReverse(entryIds: string[]) {
    const response = await this.apiClient.post(
      '/api/v1/journal-entries/validate-reverse',
      entryIds
    );
    return response.data;
  }
}
```

### Validación Previa Recomendada
```typescript
async bulkReverseOperation(entryIds: string[], reason: string) {
  try {
    // 1. Validar primero
    const validations = await this.validateBulkReverse(entryIds);
    
    // 2. Verificar si hay errores críticos
    const hasErrors = validations.some(v => v.errors.length > 0);
    if (hasErrors && !confirm('Hay errores. ¿Continuar?')) {
      return;
    }
    
    // 3. Ejecutar reversión
    const result = await this.bulkReverseEntries(entryIds, reason);
    return result;
    
  } catch (error) {
    console.error('Error en reversión masiva:', error);
    throw error;
  }
}
```

## Verificación

Para verificar que el fix funciona:

1. **Verificar URL**: Asegurar que se usa `/bulk-reverse` no `/bulk/reverse`
2. **Verificar Payload**: Incluir todos los campos requeridos
3. **Verificar Permisos**: Usuario debe tener `can_create_entries`
4. **Verificar Estados**: Solo asientos en estado `POSTED` pueden revertirse

## Testing

```bash
# Test con curl
curl -X POST "http://localhost:8000/api/v1/journal-entries/bulk-reverse" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "journal_entry_ids": ["uuid1", "uuid2"],
    "reason": "Test reversión",
    "force_reverse": false
  }'
```
