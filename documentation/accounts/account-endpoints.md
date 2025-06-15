# Endpoints de Cuentas Contables - ACTUALIZADO

## Descripción General

Los endpoints de cuentas contables proporcionan funcionalidades completas para la gestión del plan de cuentas, incluyendo operaciones CRUD, consultas jerárquicas, balances, movimientos y operaciones masivas. Estos endpoints son fundamentales para el funcionamiento del sistema contable.

## Base URL

```
Base URL: /api/v1/accounts
```

## Autenticación

Todos los endpoints requieren autenticación mediante Bearer Token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints Disponibles

### ➕ POST /
Crear una nueva cuenta contable.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
POST /api/v1/accounts/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "code": "1101001",
  "name": "Caja General",
  "account_type": "ACTIVO",
  "category": "CORRIENTE",
  "parent_id": null,
  "description": "Cuenta para el manejo de efectivo en caja general",
  "is_active": true,
  "allow_transactions": true
}
```

#### Response Exitosa (201)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "1101001",
  "name": "Caja General",
  "account_type": "ACTIVO",
  "category": "CORRIENTE",
  "parent_id": null,
  "description": "Cuenta para el manejo de efectivo en caja general",
  "is_active": true,
  "allow_transactions": true,
  "level": 1,
  "full_code": "1101001",
  "full_name": "1101001 - Caja General",
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### 📋 GET /
Obtener lista de cuentas con filtros opcionales.

#### Parámetros de Query
- `skip`: int = 0 - Número de registros a omitir
- `limit`: int = 100 - Máximo número de registros a retornar
- `account_type`: Optional[AccountType] - Filtrar por tipo de cuenta
- `category`: Optional[AccountCategory] - Filtrar por categoría
- `is_active`: Optional[bool] - Filtrar por estado activo
- `parent_id`: Optional[UUID] - Filtrar por cuenta padre
- `search`: Optional[str] - Búsqueda en código o nombre

#### Request
```http
GET /api/v1/accounts/?account_type=ACTIVO&is_active=true&limit=50
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "1101001",
    "name": "Caja General",
    "account_type": "ACTIVO",
    "category": "CORRIENTE",
    "parent_id": null,
    "description": "Cuenta para el manejo de efectivo en caja general",
    "is_active": true,
    "allow_transactions": true,
    "level": 1,
    "full_code": "1101001",
    "full_name": "1101001 - Caja General",
    "created_at": "2024-06-15T10:30:00Z",
    "updated_at": "2024-06-15T10:30:00Z"
  }
]
```

---

### 🌳 GET /tree
Obtener la estructura jerárquica de cuentas como árbol.

#### Parámetros de Query
- `account_type`: Optional[AccountType] - Filtrar por tipo de cuenta
- `active_only`: bool = true - Solo cuentas activas

#### Request
```http
GET /api/v1/accounts/tree?account_type=ACTIVO&active_only=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "1100000",
    "name": "ACTIVOS CORRIENTES",
    "account_type": "ACTIVO",
    "level": 1,
    "children": [
      {
        "id": "456e7890-e89b-12d3-a456-426614174000",
        "code": "1101000",
        "name": "EFECTIVO Y EQUIVALENTES",
        "account_type": "ACTIVO",
        "level": 2,
        "children": [
          {
            "id": "789e0123-e89b-12d3-a456-426614174000",
            "code": "1101001",
            "name": "Caja General",
            "account_type": "ACTIVO",
            "level": 3,
            "children": []
          }
        ]
      }
    ]
  }
]
```

---

### 📊 GET /chart
Obtener el plan de cuentas completo organizado.

#### Request
```http
GET /api/v1/accounts/chart
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "ACTIVO": {
    "CORRIENTE": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "code": "1101001",
        "name": "Caja General",
        "full_name": "1101001 - Caja General",
        "level": 3,
        "is_active": true,
        "allow_transactions": true
      }
    ],
    "NO_CORRIENTE": []
  },
  "PASIVO": {
    "CORRIENTE": [],
    "NO_CORRIENTE": []
  },
  "PATRIMONIO": {},
  "INGRESOS": {},
  "GASTOS": {}
}
```

---

### 📈 GET /stats
Obtener estadísticas del plan de cuentas.

#### Request
```http
GET /api/v1/accounts/stats
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "total_accounts": 150,
  "active_accounts": 142,
  "inactive_accounts": 8,
  "accounts_by_type": {
    "ACTIVO": 45,
    "PASIVO": 32,
    "PATRIMONIO": 8,
    "INGRESOS": 35,
    "GASTOS": 30
  },
  "accounts_by_category": {
    "CORRIENTE": 85,
    "NO_CORRIENTE": 65
  },
  "accounts_with_children": 25,
  "transaction_enabled_accounts": 120
}
```

---

### 🔍 GET /{account_id}
Obtener cuenta específica por ID.

#### Request
```http
GET /api/v1/accounts/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "1101001",
  "name": "Caja General",
  "account_type": "ACTIVO",
  "category": "CORRIENTE",
  "parent_id": null,
  "description": "Cuenta para el manejo de efectivo en caja general",
  "is_active": true,
  "allow_transactions": true,
  "level": 1,
  "full_code": "1101001",
  "full_name": "1101001 - Caja General",
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### 🔍 GET /code/{account_code}
Obtener cuenta específica por código.

#### Request
```http
GET /api/v1/accounts/code/1101001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "1101001",
  "name": "Caja General",
  "account_type": "ACTIVO",
  "category": "CORRIENTE",
  "parent_id": null,
  "description": "Cuenta para el manejo de efectivo en caja general",
  "is_active": true,
  "allow_transactions": true,
  "level": 1,
  "full_code": "1101001",
  "full_name": "1101001 - Caja General",
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### ✏️ PUT /{account_id}
Actualizar cuenta existente.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
PUT /api/v1/accounts/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Caja General Actualizada",
  "description": "Descripción actualizada de la cuenta",
  "is_active": true
}
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "1101001",
  "name": "Caja General Actualizada",
  "account_type": "ACTIVO",
  "category": "CORRIENTE",
  "parent_id": null,
  "description": "Descripción actualizada de la cuenta",
  "is_active": true,
  "allow_transactions": true,
  "level": 1,
  "full_code": "1101001",
  "full_name": "1101001 - Caja General Actualizada",
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T15:45:00Z"
}
```

---

### 🗑️ DELETE /{account_id}
Eliminar cuenta contable.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
DELETE /api/v1/accounts/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (204)
```
No Content
```

#### Códigos de Error
- **400 Bad Request**: Cuenta tiene transacciones asociadas
- **409 Conflict**: Cuenta tiene cuentas hijas

---

### 💰 GET /{account_id}/balance
Obtener balance actual de una cuenta.

#### Parámetros de Query
- `as_of_date`: Optional[date] - Fecha de corte (default: hoy)

#### Request
```http
GET /api/v1/accounts/123e4567-e89b-12d3-a456-426614174000/balance?as_of_date=2024-06-15
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "account_code": "1101001",
  "account_name": "Caja General",
  "debit_balance": 1500000.00,
  "credit_balance": 850000.00,
  "net_balance": 650000.00,
  "as_of_date": "2024-06-15",
  "currency": "CLP",
  "last_movement_date": "2024-06-14T16:30:00Z"
}
```

---

### 📊 GET /{account_id}/movements
Obtener historial de movimientos de una cuenta.

#### Parámetros de Query
- `start_date`: Optional[date] - Fecha de inicio
- `end_date`: Optional[date] - Fecha de fin
- `skip`: int = 0 - Registros a omitir
- `limit`: int = 100 - Máximo registros a retornar

#### Request
```http
GET /api/v1/accounts/123e4567-e89b-12d3-a456-426614174000/movements?start_date=2024-06-01&end_date=2024-06-15&limit=50
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "account_code": "1101001",
  "account_name": "Caja General",
  "period": {
    "start_date": "2024-06-01",
    "end_date": "2024-06-15"
  },
  "opening_balance": 500000.00,
  "closing_balance": 650000.00,
  "total_debits": 1000000.00,
  "total_credits": 850000.00,
  "movements": [
    {
      "date": "2024-06-14T16:30:00Z",
      "journal_entry_id": "je-uuid-here",
      "journal_entry_number": "AST-2024-0001",
      "description": "Registro de ventas del día",
      "debit_amount": 150000.00,
      "credit_amount": 0.00,
      "balance_after": 650000.00,
      "reference": "Venta-001"
    }
  ],
  "total_movements": 25
}
```

---

### ✅ POST /{account_id}/validate
Validar cuenta antes de operaciones críticas.

#### Request
```http
POST /api/v1/accounts/123e4567-e89b-12d3-a456-426614174000/validate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "is_valid": true,
  "can_be_deleted": false,
  "can_modify_type": false,
  "has_transactions": true,
  "has_children": false,
  "transaction_count": 25,
  "warnings": [],
  "restrictions": [
    "Cuenta tiene transacciones, no se puede eliminar",
    "Tipo de cuenta no se puede modificar por tener movimientos"
  ]
}
```

---

### 🔄 POST /bulk-operation
Operaciones masivas sobre múltiples cuentas.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/accounts/bulk-operation
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "operation": "toggle_active",
  "account_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ]
}
```

#### Response Exitosa (200)
```json
{
  "operation": "toggle_active",
  "total_accounts": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "account_id": "123e4567-e89b-12d3-a456-426614174000",
      "success": true,
      "message": "Estado actualizado correctamente"
    }
  ]
}
```

---

### 🗑️ POST /bulk-delete
Eliminación masiva de cuentas con validaciones.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/accounts/bulk-delete
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "account_ids": [
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
      "account_id": "123e4567-e89b-12d3-a456-426614174000",
      "success": false,
      "error": "Cuenta tiene transacciones asociadas"
    },
    {
      "account_id": "456e7890-e89b-12d3-a456-426614174000",
      "success": true,
      "message": "Cuenta eliminada correctamente"
    }
  ]
}
```

---

### ⚠️ POST /validate-deletion
Validar eliminación de cuentas antes de ejecutar.

#### Request
```http
POST /api/v1/accounts/validate-deletion
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "account_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ]
}
```

#### Response Exitosa (200)
```json
[
  {
    "account_id": "123e4567-e89b-12d3-a456-426614174000",
    "account_code": "1101001",
    "account_name": "Caja General",
    "can_delete": false,
    "blocking_reasons": [
      "Cuenta tiene 25 transacciones asociadas",
      "Cuenta tiene saldo pendiente de $650,000"
    ],
    "warnings": [],
    "requires_confirmation": true
  }
]
```

---

### 🏷️ GET /type/{account_type}
Obtener cuentas agrupadas por tipo específico.

#### Request
```http
GET /api/v1/accounts/type/ACTIVO
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "account_type": "ACTIVO",
  "total_accounts": 45,
  "categories": {
    "CORRIENTE": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "code": "1101001",
        "name": "Caja General",
        "full_name": "1101001 - Caja General",
        "is_active": true,
        "current_balance": 650000.00
      }
    ],
    "NO_CORRIENTE": []
  }
}
```

---

### 📥 POST /import
Importar cuentas masivamente desde archivo.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/accounts/import
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data

file: [archivo CSV/Excel con cuentas]
```

#### Response Exitosa (201)
```json
{
  "message": "Importación iniciada",
  "import_id": "import-uuid-here",
  "total_rows": 150,
  "status": "processing",
  "estimated_completion": "2024-06-15T10:35:00Z"
}
```

---

### 📤 GET /export/csv
Exportar cuentas a archivo CSV.

#### Request
```http
GET /api/v1/accounts/export/csv
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```
Content-Type: text/csv
Content-Disposition: attachment; filename="accounts_export_2024-06-15.csv"

code,name,account_type,category,is_active,balance
1101001,Caja General,ACTIVO,CORRIENTE,true,650000.00
1101002,Banco Estado,ACTIVO,CORRIENTE,true,2500000.00
...
```

---

## Flujos de Integración

### Creación de Plan de Cuentas Jerárquico

```javascript
// 1. Crear cuenta padre
const parentAccount = await fetch('/api/v1/accounts/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    code: '1100000',
    name: 'ACTIVOS CORRIENTES',
    account_type: 'ACTIVO',
    category: 'CORRIENTE',
    allow_transactions: false
  })
});

// 2. Crear cuenta hija
const childAccount = await fetch('/api/v1/accounts/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    code: '1101001',
    name: 'Caja General',
    account_type: 'ACTIVO',
    category: 'CORRIENTE',
    parent_id: parentAccount.id,
    allow_transactions: true
  })
});
```

### Consulta de Balances y Movimientos

```javascript
// Obtener balance actual
const balance = await fetch(`/api/v1/accounts/${accountId}/balance`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Obtener movimientos del mes
const movements = await fetch(
  `/api/v1/accounts/${accountId}/movements?start_date=2024-06-01&end_date=2024-06-30`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);

// Verificar estructura jerárquica
const accountTree = await fetch('/api/v1/accounts/tree', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

## Validaciones y Reglas de Negocio

### Estructura de Códigos
- **Primer dígito**: Tipo de cuenta (1=Activo, 2=Pasivo, 3=Patrimonio, 4=Ingresos, 5=Gastos)
- **Códigos únicos**: No pueden existir códigos duplicados
- **Jerarquía**: Las cuentas padre no pueden tener transacciones directas

### Tipos de Cuenta
- **ACTIVO**: Recursos controlados por la entidad
- **PASIVO**: Obligaciones presentes de la entidad
- **PATRIMONIO**: Interés residual en los activos
- **INGRESOS**: Incrementos en beneficios económicos
- **GASTOS**: Decrementos en beneficios económicos

### Restricciones de Eliminación
- No se puede eliminar cuenta con transacciones
- No se puede eliminar cuenta con cuentas hijas
- Solo administradores pueden eliminar cuentas

## Códigos de Error Comunes

### 400 Bad Request
- Código de cuenta inválido
- Tipo de cuenta incompatible con padre
- Datos de entrada malformados

### 401 Unauthorized
- Token de autenticación inválido
- Token expirado

### 403 Forbidden
- Permisos insuficientes para la operación
- Usuario no puede modificar cuentas

### 404 Not Found
- Cuenta no encontrada
- Cuenta padre no existe

### 409 Conflict
- Código de cuenta ya existe
- Cuenta tiene transacciones (al eliminar)
- Cuenta tiene cuentas hijas (al eliminar)

### 422 Unprocessable Entity
- Validación de datos falló
- Estructura jerárquica inválida

## Testing de Endpoints

### Casos de Prueba Críticos
1. **Jerarquía**: Crear estructura padre-hijo correcta
2. **Unicidad**: Verificar códigos únicos
3. **Balances**: Validar cálculos correctos
4. **Restricciones**: Probar eliminación con restricciones
5. **Permisos**: Verificar control de acceso por roles

### Ejemplo con pytest
```python
@pytest.mark.asyncio
async def test_create_account_hierarchy(client: AsyncClient, admin_token: str):
    # Crear cuenta padre
    parent_response = await client.post(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": "1100000",
            "name": "ACTIVOS CORRIENTES",
            "account_type": "ACTIVO",
            "category": "CORRIENTE",
            "allow_transactions": False
        }
    )
    assert parent_response.status_code == 201
    parent_data = parent_response.json()
    
    # Crear cuenta hija
    child_response = await client.post(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": "1101001",
            "name": "Caja General",
            "account_type": "ACTIVO",
            "category": "CORRIENTE",
            "parent_id": parent_data["id"],
            "allow_transactions": True
        }
    )
    assert child_response.status_code == 201
```

## Referencias

- [Esquemas de Cuentas](../schemas/account-schemas.md)
- [Asientos Contables](../journal-entries/journal-entry-endpoints.md)
- [Reportes Financieros](../reports/financial-reports.md)
- [Plan de Cuentas Estándar](../guides/chart-of-accounts.md)
