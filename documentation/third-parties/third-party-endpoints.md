# Endpoints de Terceros

Este documento describe todos los endpoints disponibles para la gestión de terceros (clientes, proveedores, empleados), incluyendo operaciones CRUD, estados de cuenta y análisis de balances.

## Base URL
```
/api/v1/third-parties
```

## Autenticación
Todos los endpoints requieren autenticación JWT válida:
```http
Authorization: Bearer <jwt_token>
```

---

## Endpoints CRUD

### **GET** `/api/v1/third-parties`
Listar terceros con filtros avanzados y paginación.

#### Parámetros de Query
```typescript
interface ThirdPartyFilters {
  type?: 'CLIENTE' | 'PROVEEDOR' | 'EMPLEADO'; // Tipo de tercero
  document_type?: string;    // Tipo de documento (RUT, CI, etc.)
  document_number?: string;  // Número de documento (búsqueda parcial)
  business_name?: string;    // Razón social (búsqueda parcial)
  commercial_name?: string;  // Nombre comercial (búsqueda parcial)
  email?: string;           // Email (búsqueda parcial)
  is_active?: boolean;      // Estado activo
  has_balance?: boolean;    // Tiene saldo pendiente
  
  // Filtros de fecha
  created_after?: date;     // Creados después de fecha
  created_before?: date;    // Creados antes de fecha
  
  // Filtros financieros
  credit_limit_min?: number; // Límite de crédito mínimo
  credit_limit_max?: number; // Límite de crédito máximo
  
  // Ordenamiento
  order_by?: 'document_number' | 'business_name' | 'created_at' | 'credit_limit';
  order_desc?: boolean;
  
  // Paginación
  skip?: number;            // Elementos a omitir (default: 0)
  limit?: number;           // Elementos por página (default: 100, max: 1000)
}
```

#### Ejemplo de Solicitud
```http
GET /api/v1/third-parties?type=CLIENTE&is_active=true&has_balance=true&limit=50
```

#### Respuesta Exitosa
```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "type": "CLIENTE",
      "document_type": "RUT",
      "document_number": "12345678-9",
      "business_name": "Empresa Cliente S.A.",
      "commercial_name": "Cliente Corp",
      "first_name": null,
      "last_name": null,
      "email": "contacto@cliente.com",
      "phone": "+56912345678",
      "address": "Av. Principal 123",
      "city": "Santiago",
      "country": "Chile",
      "payment_terms": 30,
      "credit_limit": 500000.00,
      "discount_percentage": 5.0,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "current_balance": 150000.00,
      "overdue_balance": 45000.00,
      "last_transaction_date": "2024-12-10"
    }
  ],
  "total": 125,
  "skip": 0,
  "limit": 50
}
```

### **POST** `/api/v1/third-parties`
Crear nuevo tercero con validaciones automáticas.

#### Cuerpo de la Solicitud
```json
{
  "type": "CLIENTE",
  "document_type": "RUT",
  "document_number": "12345678-9",
  "business_name": "Nueva Empresa S.A.",
  "commercial_name": "Nueva Empresa",
  "email": "contacto@nuevaempresa.com",
  "phone": "+56987654321",
  "address": "Calle Nueva 456",
  "city": "Valparaíso",
  "country": "Chile",
  "payment_terms": 45,
  "credit_limit": 750000.00,
  "discount_percentage": 3.0,
  "is_active": true,
  "contact_person": "Juan Pérez",
  "tax_id": "12345678-9",
  "website": "https://nuevaempresa.com"
}
```

#### Respuesta Exitosa (201)
```json
{
  "id": "789e0123-e89b-12d3-a456-426614174000",
  "type": "CLIENTE",
  "document_type": "RUT",
  "document_number": "12345678-9",
  "business_name": "Nueva Empresa S.A.",
  "commercial_name": "Nueva Empresa",
  "first_name": null,
  "last_name": null,
  "email": "contacto@nuevaempresa.com",
  "phone": "+56987654321",
  "address": "Calle Nueva 456",
  "city": "Valparaíso",
  "country": "Chile",
  "payment_terms": 45,
  "credit_limit": 750000.00,
  "discount_percentage": 3.0,
  "is_active": true,
  "created_at": "2024-12-11T10:30:00Z",
  "updated_at": "2024-12-11T10:30:00Z",
  "current_balance": 0.00,
  "overdue_balance": 0.00,
  "last_transaction_date": null
}
```

### **GET** `/api/v1/third-parties/{id}`
Obtener tercero específico por ID.

#### Parámetros de Ruta
- `id`: UUID del tercero

#### Parámetros de Query
```typescript
interface DetailParams {
  include_balance?: boolean;     // Incluir balance actual
  include_statistics?: boolean;  // Incluir estadísticas
}
```

#### Respuesta Exitosa
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "CLIENTE",
  "document_type": "RUT",
  "document_number": "12345678-9",
  "business_name": "Empresa Cliente S.A.",
  "commercial_name": "Cliente Corp",
  "first_name": null,
  "last_name": null,
  "email": "contacto@cliente.com",
  "phone": "+56912345678",
  "address": "Av. Principal 123",
  "city": "Santiago",
  "country": "Chile",
  "payment_terms": 30,
  "credit_limit": 500000.00,
  "discount_percentage": 5.0,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "current_balance": 150000.00,
  "overdue_balance": 45000.00,
  "last_transaction_date": "2024-12-10",
  "statistics": {
    "total_transactions": 45,
    "average_payment_days": 28,
    "credit_utilization": 30.0,
    "payment_score": 85
  }
}
```

### **PUT** `/api/v1/third-parties/{id}`
Actualizar tercero existente.

#### Cuerpo de la Solicitud
```json
{
  "business_name": "Empresa Cliente S.A. - Actualizada",
  "email": "nuevo@cliente.com",
  "phone": "+56999888777",
  "credit_limit": 750000.00,
  "payment_terms": 45,
  "is_active": true
}
```

#### Respuesta Exitosa
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "CLIENTE",
  "document_type": "RUT",
  "document_number": "12345678-9",
  "business_name": "Empresa Cliente S.A. - Actualizada",
  "email": "nuevo@cliente.com",
  "phone": "+56999888777",
  "credit_limit": 750000.00,
  "payment_terms": 45,
  "updated_at": "2024-12-11T14:30:00Z"
}
```

### **DELETE** `/api/v1/third-parties/{id}`
Desactivar tercero (soft delete).

#### Respuesta Exitosa (204)
```
No Content
```

---

## Endpoints de Consulta

### **GET** `/api/v1/third-parties/search`
Búsqueda avanzada multi-criterio.

#### Parámetros de Query
```typescript
interface SearchParams {
  q: string;               // Término de búsqueda (requerido)
  type?: ThirdPartyType;   // Filtrar por tipo
  limit?: number;          // Límite de resultados (default: 10)
  include_inactive?: boolean; // Incluir terceros inactivos
  search_fields?: string[]; // Campos a buscar: document_number, business_name, email
}
```

#### Ejemplo de Solicitud
```http
GET /api/v1/third-parties/search?q=cliente&type=CLIENTE&limit=5
```

#### Respuesta Exitosa
```json
{
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "type": "CLIENTE",
      "document_number": "12345678-9",
      "business_name": "Empresa Cliente S.A.",
      "commercial_name": "Cliente Corp",
      "email": "contacto@cliente.com",
      "current_balance": 150000.00,
      "match_score": 0.95
    }
  ],
  "total": 8,
  "search_term": "cliente"
}
```

### **GET** `/api/v1/third-parties/{id}/statement`
Estado de cuenta detallado del tercero.

#### Parámetros de Query
```typescript
interface StatementParams {
  start_date?: date;       // Fecha inicio (default: inicio del año)
  end_date?: date;         // Fecha fin (default: hoy)
  include_details?: boolean; // Incluir detalle de movimientos
  format?: 'json' | 'pdf'; // Formato de respuesta
  currency?: string;       // Moneda (default: sistema)
}
```

#### Ejemplo de Solicitud
```http
GET /api/v1/third-parties/123e4567-e89b-12d3-a456-426614174000/statement?start_date=2024-01-01&end_date=2024-12-31&include_details=true
```

#### Respuesta Exitosa
```json
{
  "third_party": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "document_number": "12345678-9",
    "business_name": "Empresa Cliente S.A.",
    "commercial_name": "Cliente Corp",
    "type": "CLIENTE"
  },
  "statement_date": "2024-12-11",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "opening_balance": 0.00,
  "movements": [
    {
      "date": "2024-01-15",
      "journal_entry_id": "JE001",
      "reference": "FAC-001",
      "description": "Venta de productos",
      "document_type": "Factura",
      "debit_amount": 150000.00,
      "credit_amount": 0.00,
      "running_balance": 150000.00,
      "due_date": "2024-02-14",
      "days_overdue": 0
    },
    {
      "date": "2024-02-10",
      "journal_entry_id": "JE015",
      "reference": "PAG-001",
      "description": "Pago recibido",
      "document_type": "Pago",
      "debit_amount": 0.00,
      "credit_amount": 100000.00,
      "running_balance": 50000.00,
      "due_date": null,
      "days_overdue": 0
    }
  ],
  "closing_balance": 150000.00,
  "summary": {
    "total_debits": 800000.00,
    "total_credits": 650000.00,
    "net_movement": 150000.00,
    "transaction_count": 25
  },
  "aging_analysis": {
    "current": 105000.00,
    "30_days": 25000.00,
    "60_days": 15000.00,
    "90_days": 5000.00,
    "over_120": 0.00
  },
  "generated_at": "2024-12-11T15:30:00Z"
}
```

### **GET** `/api/v1/third-parties/{id}/balance`
Balance actual y análisis de antigüedad.

#### Parámetros de Query
```typescript
interface BalanceParams {
  as_of_date?: date;       // Fecha de corte (default: hoy)
  include_aging?: boolean; // Incluir análisis de antigüedad
  currency?: string;       // Moneda
}
```

#### Respuesta Exitosa
```json
{
  "third_party": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "document_number": "12345678-9",
    "business_name": "Empresa Cliente S.A.",
    "type": "CLIENTE"
  },
  "as_of_date": "2024-12-11",
  "current_balance": 150000.00,
  "credit_limit": 500000.00,
  "available_credit": 350000.00,
  "credit_utilization": 30.0,
  "overdue_balance": 45000.00,
  "overdue_percentage": 30.0,
  "aging_buckets": {
    "current": 105000.00,     // 0-30 días
    "30_days": 25000.00,      // 31-60 días
    "60_days": 15000.00,      // 61-90 días
    "90_days": 5000.00,       // 91-120 días
    "over_120": 0.00          // Más de 120 días
  },
  "oldest_transaction": {
    "date": "2024-10-15",
    "amount": 25000.00,
    "days_old": 57,
    "reference": "FAC-087"
  },
  "payment_behavior": {
    "average_payment_days": 28,
    "payment_score": 85,
    "last_payment_date": "2024-12-05",
    "payment_frequency": "regular"
  }
}
```

---

## Endpoints de Operaciones

### **POST** `/api/v1/third-parties/bulk-operations`
Operaciones masivas sobre múltiples terceros.

#### Cuerpo de la Solicitud
```json
{
  "operation": "update",
  "filters": {
    "type": "CLIENTE",
    "city": "Santiago"
  },
  "updates": {
    "discount_percentage": 7.0,
    "payment_terms": 45
  }
}
```

#### Respuesta Exitosa
```json
{
  "operation": "update",
  "affected_count": 15,
  "success_count": 14,
  "error_count": 1,
  "results": [
    {
      "third_party_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "success",
      "message": "Actualizado correctamente"
    },
    {
      "third_party_id": "456e7890-e89b-12d3-a456-426614174000",
      "status": "error",
      "message": "Tercero inactivo, no se puede actualizar"
    }
  ],
  "execution_time": "2.5s"
}
```

### **POST** `/api/v1/third-parties/import`
Importación masiva desde archivos.

#### Parámetros de Form
- `file`: Archivo CSV, XLSX o JSON
- `format`: Formato del archivo
- `dry_run`: true/false - Solo validar sin importar

#### Respuesta Exitosa
```json
{
  "import_id": "imp_123456",
  "status": "completed",
  "summary": {
    "total_records": 100,
    "successful_imports": 95,
    "failed_imports": 5,
    "duplicates_found": 3,
    "validation_errors": 2
  },
  "errors": [
    {
      "row": 15,
      "field": "document_number",
      "error": "Formato de RUT inválido",
      "value": "12345678"
    }
  ],
  "warnings": [
    {
      "row": 23,
      "message": "Tercero ya existe, se actualizaron los datos"
    }
  ]
}
```

### **GET** `/api/v1/third-parties/export`
Exportación de datos de terceros.

#### Parámetros de Query
```typescript
interface ExportParams {
  format: 'csv' | 'xlsx' | 'json'; // Formato de exportación
  filters?: ThirdPartyFilters;     // Filtros a aplicar
  fields?: string[];               // Campos específicos a exportar
  include_balance?: boolean;       // Incluir saldos actuales
}
```

#### Respuesta Exitosa
```json
{
  "export_id": "exp_789012",
  "status": "ready",
  "download_url": "/api/v1/downloads/exp_789012.xlsx",
  "file_size": "2.5MB",
  "record_count": 500,
  "expires_at": "2024-12-12T15:30:00Z"
}
```

---

## Endpoints de Análisis

### **GET** `/api/v1/third-parties/analytics/summary`
Resumen analítico de terceros.

#### Parámetros de Query
```typescript
interface AnalyticsParams {
  type?: ThirdPartyType;   // Filtrar por tipo
  period?: string;         // Período de análisis
  group_by?: string;       // Agrupar por: type, city, country
}
```

#### Respuesta Exitosa
```json
{
  "summary": {
    "total_third_parties": 450,
    "active_third_parties": 425,
    "by_type": {
      "CLIENTE": 300,
      "PROVEEDOR": 120,
      "EMPLEADO": 30
    },
    "by_country": {
      "Chile": 380,
      "Argentina": 45,
      "Colombia": 25
    }
  },
  "financial_summary": {
    "total_receivables": 2500000.00,
    "total_payables": 850000.00,
    "overdue_receivables": 380000.00,
    "overdue_payables": 125000.00,
    "average_credit_limit": 650000.00,
    "credit_utilization": 35.2
  },
  "top_customers": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "business_name": "Cliente Principal S.A.",
      "current_balance": 450000.00,
      "credit_limit": 1000000.00
    }
  ],
  "aging_summary": {
    "current": 1750000.00,
    "30_days": 450000.00,
    "60_days": 200000.00,
    "90_days": 75000.00,
    "over_120": 25000.00
  }
}
```

### **GET** `/api/v1/third-parties/analytics/aging-report`
Reporte consolidado de antigüedad de saldos.

#### Respuesta Exitosa
```json
{
  "report_date": "2024-12-11",
  "currency": "CLP",
  "aging_buckets": {
    "current": {
      "amount": 1750000.00,
      "count": 120,
      "percentage": 70.0
    },
    "30_days": {
      "amount": 450000.00,
      "count": 35,
      "percentage": 18.0
    },
    "60_days": {
      "amount": 200000.00,
      "count": 15,
      "percentage": 8.0
    },
    "90_days": {
      "amount": 75000.00,
      "count": 8,
      "percentage": 3.0
    },
    "over_120": {
      "amount": 25000.00,
      "count": 3,
      "percentage": 1.0
    }
  },
  "total_outstanding": 2500000.00,
  "total_customers": 181,
  "overdue_amount": 750000.00,
  "overdue_percentage": 30.0,
  "by_customer": [
    {
      "third_party": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "business_name": "Cliente Moroso S.A.",
        "document_number": "87654321-0"
      },
      "total_balance": 125000.00,
      "overdue_balance": 95000.00,
      "aging": {
        "current": 30000.00,
        "30_days": 45000.00,
        "60_days": 35000.00,
        "90_days": 15000.00,
        "over_120": 0.00
      },
      "oldest_invoice_days": 75
    }
  ]
}
```

---

## Códigos de Error

### Errores Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| 400 | Datos de entrada inválidos | Verificar formato de campos |
| 404 | Tercero no encontrado | Verificar ID existe |
| 409 | Documento duplicado | Usar documento único |
| 422 | Error de validación | Revisar reglas de negocio |

### Ejemplos de Respuestas de Error

#### Error de Validación (422)
```json
{
  "detail": [
    {
      "loc": ["body", "document_number"],
      "msg": "Formato de RUT inválido",
      "type": "value_error"
    },
    {
      "loc": ["body", "email"],
      "msg": "Formato de email inválido",
      "type": "value_error"
    }
  ]
}
```

#### Error de Documento Duplicado (409)
```json
{
  "detail": "Ya existe un tercero con documento '12345678-9'"
}
```

---

## Ejemplos de Uso

### Flujo Completo de Gestión de Cliente

```javascript
// 1. Crear nuevo cliente
const clientResponse = await fetch('/api/v1/third-parties', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    type: 'CLIENTE',
    document_type: 'RUT',
    document_number: '12345678-9',
    business_name: 'Nuevo Cliente S.A.',
    email: 'contacto@nuevocliente.com',
    payment_terms: 30,
    credit_limit: 500000.00
  })
});

// 2. Obtener estado de cuenta
const statementResponse = await fetch(
  `/api/v1/third-parties/${clientResponse.data.id}/statement?start_date=2024-01-01&end_date=2024-12-31`,
  {
    headers: { 'Authorization': 'Bearer ' + token }
  }
);

// 3. Verificar balance actual
const balanceResponse = await fetch(
  `/api/v1/third-parties/${clientResponse.data.id}/balance?include_aging=true`,
  {
    headers: { 'Authorization': 'Bearer ' + token }
  }
);

// 4. Búsqueda de clientes
const searchResponse = await fetch(
  '/api/v1/third-parties/search?q=cliente&type=CLIENTE&limit=10',
  {
    headers: { 'Authorization': 'Bearer ' + token }
  }
);
```

### Operaciones Masivas

```javascript
// Actualización masiva de términos de pago
const bulkUpdateResponse = await fetch('/api/v1/third-parties/bulk-operations', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    operation: 'update',
    filters: {
      type: 'CLIENTE',
      city: 'Santiago'
    },
    updates: {
      payment_terms: 45,
      discount_percentage: 5.0
    }
  })
});

// Importación desde archivo
const formData = new FormData();
formData.append('file', csvFile);
formData.append('format', 'csv');
formData.append('dry_run', 'false');

const importResponse = await fetch('/api/v1/third-parties/import', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  body: formData
});
```

---

## Rate Limiting

- **Endpoints de Consulta**: 1000 requests/hour
- **Endpoints de Modificación**: 200 requests/hour
- **Endpoints de Operaciones Masivas**: 10 requests/hour
- **Endpoints de Reportes**: 50 requests/hour

---

## Webhooks

### Eventos Disponibles
- `third_party.created` - Tercero creado
- `third_party.updated` - Tercero actualizado
- `third_party.balance_changed` - Cambio de saldo
- `third_party.overdue_detected` - Saldo vencido detectado

### Configuración de Webhook
```json
{
  "url": "https://mi-sistema.com/webhooks/third-parties",
  "events": ["third_party.balance_changed", "third_party.overdue_detected"],
  "secret": "webhook_secret_key"
}
```

---
**Última actualización**: Diciembre 2024  
**Versión API**: 1.0.0
