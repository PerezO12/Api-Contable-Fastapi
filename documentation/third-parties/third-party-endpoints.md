# Endpoints de Terceros - ACTUALIZADO

## Descripción General

Los endpoints de terceros proporcionan funcionalidades completas para la gestión de clientes, proveedores, empleados y otros terceros comerciales. Incluyen operaciones CRUD, estados de cuenta, balances, validaciones y operaciones masivas. Estos endpoints son esenciales para el manejo de relaciones comerciales en el sistema contable.

## Base URL

```
Base URL: /api/v1/third-parties
```

## Autenticación

Todos los endpoints requieren autenticación mediante Bearer Token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints Disponibles

### ➕ POST /
Crear un nuevo tercero con validaciones automáticas.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
POST /api/v1/third-parties/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "type": "CLIENTE",
  "document_type": "RUT",
  "document_number": "12345678-9",
  "business_name": "Empresa Cliente S.A.",
  "commercial_name": "Cliente Corp",
  "email": "contacto@cliente.com",
  "phone": "+56912345678",
  "address": "Av. Principal 123",
  "city": "Santiago",
  "country": "Chile",
  "payment_terms": 30,
  "credit_limit": 500000.00,
  "discount_percentage": 5.0,
  "is_active": true
}
```

#### Response Exitosa (201)
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
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### 📋 GET /
Listar terceros con filtros avanzados y paginación.

#### Parámetros de Query
- `search`: Optional[str] - Búsqueda en código, nombre, número de documento
- `third_party_type`: Optional[ThirdPartyType] - Filtrar por tipo de tercero
- `document_type`: Optional[DocumentType] - Filtrar por tipo de documento
- `is_active`: Optional[bool] - Filtrar por estado activo
- `city`: Optional[str] - Filtrar por ciudad
- `country`: Optional[str] - Filtrar por país
- `skip`: int = 0 - Registros a omitir
- `limit`: int = 100 - Máximo registros a retornar (máx. 1000)

#### Request
```http
GET /api/v1/third-parties/?third_party_type=CLIENTE&is_active=true&city=Santiago&limit=50
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "items": [
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
      "created_at": "2024-06-15T10:30:00Z",
      "updated_at": "2024-06-15T10:30:00Z"
    }
  ],
  "total": 125,
  "skip": 0,
  "limit": 50
}
```

---

### 🔍 GET /{third_party_id}
Obtener tercero específico por ID con información detallada.

#### Request
```http
GET /api/v1/third-parties/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
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
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z",
  "additional_info": {
    "current_balance": 150000.00,
    "overdue_balance": 45000.00,
    "last_transaction_date": "2024-06-14",
    "transaction_count": 25,
    "credit_utilization": 30.0
  }
}
```

---

### 🔍 GET /code/{code}
Obtener tercero por código único.

#### Request
```http
GET /api/v1/third-parties/code/CLI001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "CLIENTE",
  "document_type": "RUT",
  "document_number": "12345678-9",
  "business_name": "Empresa Cliente S.A.",
  "commercial_name": "Cliente Corp",
  "code": "CLI001",
  "email": "contacto@cliente.com",
  "phone": "+56912345678",
  "is_active": true,
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### 📄 GET /document/{document_type}/{document_number}
Obtener tercero por tipo y número de documento.

#### Request
```http
GET /api/v1/third-parties/document/RUT/12345678-9
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "CLIENTE",
  "document_type": "RUT",
  "document_number": "12345678-9",
  "business_name": "Empresa Cliente S.A.",
  "commercial_name": "Cliente Corp",
  "email": "contacto@cliente.com",
  "phone": "+56912345678",
  "is_active": true,
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### ✏️ PUT /{third_party_id}
Actualizar tercero existente.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
PUT /api/v1/third-parties/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "business_name": "Empresa Cliente S.A. - Actualizada",
  "email": "nuevo@cliente.com",
  "phone": "+56999888777",
  "credit_limit": 750000.00,
  "payment_terms": 45,
  "is_active": true
}
```

#### Response Exitosa (200)
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
  "is_active": true,
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T15:45:00Z"
}
```

---

### 🗑️ DELETE /{third_party_id}
Eliminar tercero si no tiene movimientos.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
DELETE /api/v1/third-parties/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (204)
```
No Content
```

#### Códigos de Error
- **400 Bad Request**: Tercero tiene transacciones asociadas
- **404 Not Found**: Tercero no encontrado

---

### 🏷️ GET /type/{third_party_type}
Obtener todos los terceros activos de un tipo específico.

#### Request
```http
GET /api/v1/third-parties/type/CLIENTE
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "type": "CLIENTE",
    "document_type": "RUT",
    "document_number": "12345678-9",
    "business_name": "Empresa Cliente S.A.",
    "commercial_name": "Cliente Corp",
    "email": "contacto@cliente.com",
    "is_active": true,
    "created_at": "2024-06-15T10:30:00Z"
  }
]
```

---

### 📊 GET /{third_party_id}/statement
Generar estado de cuenta del tercero para un período.

#### Parámetros de Query
- `start_date`: date (requerido) - Fecha de inicio del estado
- `end_date`: date (requerido) - Fecha de fin del estado

#### Request
```http
GET /api/v1/third-parties/123e4567-e89b-12d3-a456-426614174000/statement?start_date=2024-06-01&end_date=2024-06-30
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "third_party_id": "123e4567-e89b-12d3-a456-426614174000",
  "third_party_name": "Empresa Cliente S.A.",
  "document_number": "12345678-9",
  "period": {
    "start_date": "2024-06-01",
    "end_date": "2024-06-30"
  },
  "opening_balance": 100000.00,
  "closing_balance": 150000.00,
  "total_debits": 250000.00,
  "total_credits": 200000.00,
  "transactions": [
    {
      "date": "2024-06-15T10:30:00Z",
      "reference": "FAC-001",
      "description": "Venta de productos",
      "debit_amount": 100000.00,
      "credit_amount": 0.00,
      "balance": 150000.00,
      "journal_entry_id": "je-uuid-here"
    }
  ],
  "summary": {
    "transaction_count": 15,
    "average_payment_days": 28,
    "largest_transaction": 100000.00,
    "payment_behavior": "GOOD"
  }
}
```

---

### 💰 GET /{third_party_id}/balance
Obtener balance actual e información de crédito del tercero.

#### Request
```http
GET /api/v1/third-parties/123e4567-e89b-12d3-a456-426614174000/balance
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "third_party_id": "123e4567-e89b-12d3-a456-426614174000",
  "third_party_name": "Empresa Cliente S.A.",
  "current_balance": 150000.00,
  "credit_limit": 500000.00,
  "available_credit": 350000.00,
  "credit_utilization": 30.0,
  "overdue_balance": 45000.00,
  "current_balance_detail": {
    "0_30_days": 105000.00,
    "31_60_days": 25000.00,
    "61_90_days": 15000.00,
    "over_90_days": 5000.00
  },
  "last_payment_date": "2024-06-10T14:30:00Z",
  "last_payment_amount": 50000.00,
  "payment_score": 85,
  "risk_level": "LOW"
}
```

---

### ✅ GET /{third_party_id}/validate
Validar datos del tercero y restricciones de unicidad.

#### Request
```http
GET /api/v1/third-parties/123e4567-e89b-12d3-a456-426614174000/validate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "third_party_id": "123e4567-e89b-12d3-a456-426614174000",
  "is_valid": true,
  "can_be_deleted": false,
  "has_transactions": true,
  "transaction_count": 25,
  "duplicate_document": false,
  "duplicate_email": false,
  "credit_limit_exceeded": false,
  "warnings": [
    "Tercero tiene saldo vencido mayor a 90 días"
  ],
  "restrictions": [
    "No se puede eliminar tercero con transacciones asociadas"
  ],
  "validation_details": {
    "document_format_valid": true,
    "email_format_valid": true,
    "phone_format_valid": true,
    "required_fields_complete": true
  }
}
```

---

### 📈 GET /statistics/summary
Obtener estadísticas generales de terceros.

#### Request
```http
GET /api/v1/third-parties/statistics/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "total_third_parties": 450,
  "active_third_parties": 425,
  "inactive_third_parties": 25,
  "by_type": {
    "CLIENTE": 200,
    "PROVEEDOR": 180,
    "EMPLEADO": 45,
    "OTRO": 25
  },
  "by_country": {
    "Chile": 350,
    "Argentina": 50,
    "Perú": 30,
    "Colombia": 20
  },
  "with_transactions": 320,
  "with_overdue_balance": 45,
  "total_credit_limit": 25000000.00,
  "total_current_balance": 8500000.00,
  "average_payment_days": 32,
  "top_customers_by_balance": [
    {
      "id": "top-customer-uuid",
      "name": "Cliente Principal S.A.",
      "balance": 500000.00
    }
  ]
}
```

---

### 🔄 POST /bulk-operation
Operaciones masivas sobre múltiples terceros.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/third-parties/bulk-operation
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "operation": "toggle_active",
  "third_party_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ],
  "parameters": {
    "reason": "Revisión anual de clientes"
  }
}
```

#### Response Exitosa (200)
```json
{
  "operation": "toggle_active",
  "total_third_parties": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "third_party_id": "123e4567-e89b-12d3-a456-426614174000",
      "success": true,
      "message": "Estado actualizado correctamente"
    }
  ]
}
```

---

### 🗑️ POST /bulk-delete
Eliminación masiva de terceros con validaciones.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/third-parties/bulk-delete
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "third_party_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ],
  "force": false
}
```

#### Response Exitosa (200)
```json
{
  "total_requested": 2,
  "successful_deletions": 1,
  "failed_deletions": 1,
  "results": [
    {
      "third_party_id": "123e4567-e89b-12d3-a456-426614174000",
      "success": false,
      "error": "Tercero tiene transacciones asociadas"
    },
    {
      "third_party_id": "456e7890-e89b-12d3-a456-426614174000",
      "success": true,
      "message": "Tercero eliminado correctamente"
    }
  ]
}
```

---

### ⚠️ POST /validate-deletion
Validar eliminación de terceros antes de ejecutar.

#### Request
```http
POST /api/v1/third-parties/validate-deletion
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "third_party_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ]
}
```

#### Response Exitosa (200)
```json
[
  {
    "third_party_id": "123e4567-e89b-12d3-a456-426614174000",
    "third_party_name": "Empresa Cliente S.A.",
    "document_number": "12345678-9",
    "can_delete": false,
    "blocking_reasons": [
      "Tercero tiene 25 transacciones asociadas",
      "Tercero tiene saldo pendiente de $150,000"
    ],
    "warnings": [
      "Eliminar este tercero afectará reportes históricos"
    ],
    "requires_confirmation": true
  }
]
```

---

## Flujos de Integración

### Creación y Gestión de Cliente Completa

```javascript
// 1. Crear nuevo cliente
const clientResponse = await fetch('/api/v1/third-parties/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
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

const client = await clientResponse.json();

// 2. Obtener estado de cuenta
const statementResponse = await fetch(
  `/api/v1/third-parties/${client.id}/statement?start_date=2024-01-01&end_date=2024-12-31`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);

// 3. Verificar balance actual
const balanceResponse = await fetch(
  `/api/v1/third-parties/${client.id}/balance`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
```

### Búsqueda y Filtrado de Terceros

```javascript
// Buscar clientes activos en Santiago
const clientsResponse = await fetch(
  '/api/v1/third-parties/?third_party_type=CLIENTE&is_active=true&city=Santiago&limit=100',
  { headers: { 'Authorization': `Bearer ${token}` } }
);

// Buscar por documento específico
const thirdPartyResponse = await fetch(
  '/api/v1/third-parties/document/RUT/12345678-9',
  { headers: { 'Authorization': `Bearer ${token}` } }
);

// Obtener todos los proveedores
const suppliersResponse = await fetch(
  '/api/v1/third-parties/type/PROVEEDOR',
  { headers: { 'Authorization': `Bearer ${token}` } }
);
```

## Validaciones y Reglas de Negocio

### Tipos de Terceros
- **CLIENTE**: Personas o empresas que compran productos/servicios
- **PROVEEDOR**: Personas o empresas que suministran productos/servicios
- **EMPLEADO**: Personal de la empresa
- **OTRO**: Otros terceros (entidades gubernamentales, bancos, etc.)

### Tipos de Documento
- **RUT**: Rol Único Tributario (Chile)
- **CI**: Cédula de Identidad
- **PASSPORT**: Pasaporte
- **FOREIGN_ID**: Identificación extranjera

### Validaciones de Datos
- **Documento único**: No pueden existir dos terceros con el mismo documento
- **Email único**: Solo un tercero puede tener un email específico
- **Formato de documento**: Validación según tipo de documento
- **Límite de crédito**: Debe ser mayor a 0 si se especifica

### Restricciones de Eliminación
- No se puede eliminar tercero con transacciones asociadas
- No se puede eliminar tercero con saldo pendiente
- Solo administradores y contadores pueden eliminar terceros

## Códigos de Error Comunes

### 400 Bad Request
- Formato de documento inválido
- Tipo de tercero incompatible
- Datos de entrada malformados

### 401 Unauthorized
- Token de autenticación inválido
- Token expirado

### 403 Forbidden
- Permisos insuficientes para la operación
- Usuario no puede modificar terceros

### 404 Not Found
- Tercero no encontrado
- Documento no existe

### 409 Conflict
- Documento ya existe en el sistema
- Email ya está en uso
- Tercero tiene transacciones (al eliminar)

### 422 Unprocessable Entity
- Validación de datos falló
- Formato de email inválido
- Tipo de documento no válido

## Testing de Endpoints

### Casos de Prueba Críticos
1. **Unicidad**: Verificar documentos y emails únicos
2. **Validaciones**: Probar formatos de documento
3. **Estados de cuenta**: Validar cálculos de balances
4. **Restricciones**: Probar eliminación con restricciones
5. **Búsquedas**: Verificar filtros y paginación
6. **Permisos**: Verificar control de acceso por roles

### Ejemplo con pytest
```python
@pytest.mark.asyncio
async def test_create_third_party_unique_document(client: AsyncClient, admin_token: str):
    # Crear primer tercero
    response1 = await client.post(
        "/api/v1/third-parties/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "type": "CLIENTE",
            "document_type": "RUT",
            "document_number": "12345678-9",
            "business_name": "Cliente Test S.A.",
            "email": "test@cliente.com"
        }
    )
    assert response1.status_code == 201
    
    # Intentar crear segundo tercero con mismo documento
    response2 = await client.post(
        "/api/v1/third-parties/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "type": "PROVEEDOR",
            "document_type": "RUT",
            "document_number": "12345678-9",
            "business_name": "Proveedor Test S.A.",
            "email": "test@proveedor.com"
        }
    )
    assert response2.status_code == 409  # Conflict
```

## Referencias

- [Esquemas de Terceros](../schemas/third-party-schemas.md)
- [Asientos Contables](../journal-entries/journal-entry-endpoints.md)
- [Reportes de Terceros](../reports/third-party-reports.md)
- [Gestión de Pagos](../payments/payment-endpoints.md)
