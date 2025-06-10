# Endpoints de Cuentas

## Descripción General

Los endpoints del módulo de cuentas proporcionan una API REST completa para la gestión de cuentas contables, incluyendo operaciones CRUD, consultas jerárquicas, manejo de saldos, y reportes específicos. Estos endpoints están protegidos según el sistema de roles implementado en el API Contable.

## Base URL

```
Base URL: /api/v1/accounts
```

## Endpoints Disponibles

### 🏦 POST /

Crea una nueva cuenta contable.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
POST /api/v1/accounts/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "code": "1.1.02.03",
  "name": "Banco XYZ Cuenta Corriente",
  "description": "Cuenta bancaria principal para operaciones",
  "account_type": "ACTIVO",
  "category": "ACTIVO_CORRIENTE",
  "parent_id": "12345678-1234-1234-1234-123456789012",
  "is_active": true,
  "allows_movements": true,
  "requires_third_party": false,
  "requires_cost_center": false,
  "notes": "Cuenta abierta en junio 2025"
}
```

#### Schema de Request
```python
class AccountCreate(AccountBase):
    """Schema para crear cuentas contables"""
    parent_id: Optional[uuid.UUID] = Field(None, description="ID de la cuenta padre")
```

#### Response Exitosa (201)
```json
{
  "id": "87654321-4321-4321-4321-987654321098",
  "code": "1.1.02.03",
  "name": "Banco XYZ Cuenta Corriente",
  "description": "Cuenta bancaria principal para operaciones",
  "account_type": "ACTIVO",
  "category": "ACTIVO_CORRIENTE",
  "parent_id": "12345678-1234-1234-1234-123456789012",
  "level": 4,
  "is_active": true,
  "allows_movements": true,
  "requires_third_party": false,
  "requires_cost_center": false,
  "balance": "0.00",
  "debit_balance": "0.00",
  "credit_balance": "0.00",
  "notes": "Cuenta abierta en junio 2025",
  "created_by_id": "99999999-9999-9999-9999-999999999999",
  "created_at": "2025-06-10T14:30:00Z",
  "updated_at": "2025-06-10T14:30:00Z"
}
```

#### Códigos de Error
- **400 Bad Request**: Código ya existe o datos inválidos
- **403 Forbidden**: Permisos insuficientes
- **422 Unprocessable Entity**: Datos de entrada inválidos

---

### 📋 GET /

Obtiene una lista de cuentas con filtros opcionales.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/?skip=0&limit=50&account_type=ACTIVO&is_active=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `skip` (int, opcional): Número de registros a omitir (default: 0)
- `limit` (int, opcional): Máximo número de registros (default: 100)
- `account_type` (AccountType, opcional): Filtrar por tipo de cuenta
- `category` (AccountCategory, opcional): Filtrar por categoría
- `is_active` (bool, opcional): Filtrar por estado activo/inactivo
- `parent_id` (UUID, opcional): Filtrar por cuenta padre
- `search` (string, opcional): Texto a buscar en código, nombre o descripción

#### Response Exitosa (200)
```json
[
  {
    "id": "12345678-1234-1234-1234-123456789012",
    "code": "1.1",
    "name": "Activo Corriente",
    "description": "Activos a corto plazo",
    "account_type": "ACTIVO",
    "category": "ACTIVO_CORRIENTE",
    "parent_id": "11111111-1111-1111-1111-111111111111",
    "level": 2,
    "is_active": true,
    "allows_movements": false,
    "requires_third_party": false,
    "requires_cost_center": false,
    "balance": "15000.00",
    "debit_balance": "15000.00",
    "credit_balance": "0.00",
    "notes": null,
    "created_by_id": "99999999-9999-9999-9999-999999999999",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  },
  {
    "id": "87654321-4321-4321-4321-987654321098",
    "code": "1.1.02.03",
    "name": "Banco XYZ Cuenta Corriente",
    "description": "Cuenta bancaria principal para operaciones",
    "account_type": "ACTIVO",
    "category": "ACTIVO_CORRIENTE",
    "parent_id": "12345678-1234-1234-1234-123456789012",
    "level": 4,
    "is_active": true,
    "allows_movements": true,
    "requires_third_party": false,
    "requires_cost_center": false,
    "balance": "5000.00",
    "debit_balance": "10000.00",
    "credit_balance": "5000.00",
    "notes": "Cuenta abierta en junio 2025",
    "created_by_id": "99999999-9999-9999-9999-999999999999",
    "created_at": "2025-06-10T14:30:00Z",
    "updated_at": "2025-06-10T14:30:00Z"
  }
]
```

---

### 🌳 GET /tree

Obtiene la estructura jerárquica de cuentas como árbol.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/tree?account_type=ACTIVO&active_only=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `account_type` (AccountType, opcional): Filtrar por tipo de cuenta
- `active_only` (bool, opcional): Mostrar solo cuentas activas (default: true)

#### Response Exitosa (200)
```json
[
  {
    "id": "11111111-1111-1111-1111-111111111111",
    "code": "1",
    "name": "Activos",
    "account_type": "ACTIVO",
    "level": 1,
    "balance": "30000.00",
    "is_active": true,
    "allows_movements": false,
    "children": [
      {
        "id": "12345678-1234-1234-1234-123456789012",
        "code": "1.1",
        "name": "Activo Corriente",
        "account_type": "ACTIVO",
        "level": 2,
        "balance": "15000.00",
        "is_active": true,
        "allows_movements": false,
        "children": [
          {
            "id": "22222222-2222-2222-2222-222222222222",
            "code": "1.1.02",
            "name": "Bancos",
            "account_type": "ACTIVO",
            "level": 3,
            "balance": "5000.00",
            "is_active": true,
            "allows_movements": false,
            "children": [
              {
                "id": "87654321-4321-4321-4321-987654321098",
                "code": "1.1.02.03",
                "name": "Banco XYZ Cuenta Corriente",
                "account_type": "ACTIVO",
                "level": 4,
                "balance": "5000.00",
                "is_active": true,
                "allows_movements": true,
                "children": []
              }
            ]
          }
        ]
      }
    ]
  }
]
```

---

### 📊 GET /chart

Obtiene el plan de cuentas completo organizado por tipo.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/chart
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "by_type": [
    {
      "account_type": "ACTIVO",
      "accounts": [
        {
          "id": "11111111-1111-1111-1111-111111111111",
          "code": "1",
          "name": "Activos",
          "account_type": "ACTIVO",
          "balance": "30000.00",
          "is_active": true,
          "allows_movements": false
        },
        {
          "id": "12345678-1234-1234-1234-123456789012",
          "code": "1.1",
          "name": "Activo Corriente", 
          "account_type": "ACTIVO",
          "balance": "15000.00",
          "is_active": true,
          "allows_movements": false
        }
      ],
      "total_balance": "30000.00"
    },
    {
      "account_type": "PASIVO",
      "accounts": [
        {
          "id": "33333333-3333-3333-3333-333333333333",
          "code": "2",
          "name": "Pasivos",
          "account_type": "PASIVO",
          "balance": "10000.00",
          "is_active": true,
          "allows_movements": false
        }
      ],
      "total_balance": "10000.00"
    }
  ],
  "total_accounts": 50,
  "active_accounts": 48,
  "leaf_accounts": 30
}
```

---

### 📉 GET /stats

Obtener estadísticas generales de las cuentas.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/stats
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "total_accounts": 50,
  "active_accounts": 48,
  "inactive_accounts": 2,
  "by_type": {
    "ACTIVO": 20,
    "PASIVO": 12,
    "PATRIMONIO": 5,
    "INGRESO": 5,
    "GASTO": 6,
    "COSTOS": 2
  },
  "by_category": {
    "ACTIVO_CORRIENTE": 12,
    "ACTIVO_NO_CORRIENTE": 8,
    "PASIVO_CORRIENTE": 8,
    "PASIVO_NO_CORRIENTE": 4,
    "CAPITAL": 2,
    "RESULTADOS": 3
  },
  "accounts_with_movements": 30,
  "accounts_without_movements": 20
}
```

---

### 🔍 GET /{account_id}

Obtiene una cuenta específica por su ID.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/87654321-4321-4321-4321-987654321098
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "87654321-4321-4321-4321-987654321098",
  "code": "1.1.02.03",
  "name": "Banco XYZ Cuenta Corriente",
  "description": "Cuenta bancaria principal para operaciones",
  "account_type": "ACTIVO",
  "category": "ACTIVO_CORRIENTE",
  "parent_id": "22222222-2222-2222-2222-222222222222",
  "level": 4,
  "is_active": true,
  "allows_movements": true,
  "requires_third_party": false,
  "requires_cost_center": false,
  "balance": "5000.00",
  "debit_balance": "10000.00",
  "credit_balance": "5000.00",
  "notes": "Cuenta abierta en junio 2025",
  "created_by_id": "99999999-9999-9999-9999-999999999999",
  "created_at": "2025-06-10T14:30:00Z",
  "updated_at": "2025-06-10T14:30:00Z"
}
```

#### Códigos de Error
- **404 Not Found**: Cuenta no encontrada

---

### 🔢 GET /code/{account_code}

Obtiene una cuenta específica por su código.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/code/1.1.02.03
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "87654321-4321-4321-4321-987654321098",
  "code": "1.1.02.03",
  "name": "Banco XYZ Cuenta Corriente",
  "description": "Cuenta bancaria principal para operaciones",
  "account_type": "ACTIVO",
  "category": "ACTIVO_CORRIENTE",
  "parent_id": "22222222-2222-2222-2222-222222222222",
  "level": 4,
  "is_active": true,
  "allows_movements": true,
  "requires_third_party": false,
  "requires_cost_center": false,
  "balance": "5000.00",
  "debit_balance": "10000.00",
  "credit_balance": "5000.00",
  "notes": "Cuenta abierta en junio 2025",
  "created_by_id": "99999999-9999-9999-9999-999999999999",
  "created_at": "2025-06-10T14:30:00Z",
  "updated_at": "2025-06-10T14:30:00Z"
}
```

#### Códigos de Error
- **404 Not Found**: Cuenta no encontrada

---

### ✏️ PUT /{account_id}

Actualiza una cuenta existente.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
PUT /api/v1/accounts/87654321-4321-4321-4321-987654321098
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Banco XYZ Cuenta Principal",
  "description": "Cuenta bancaria principal para operaciones diarias",
  "is_active": true,
  "notes": "Cuenta actualizada junio 2025"
}
```

#### Schema de Request
```python
class AccountUpdate(BaseModel):
    """Schema para actualizar cuentas contables"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[AccountCategory] = None
    is_active: Optional[bool] = None
    allows_movements: Optional[bool] = None
    requires_third_party: Optional[bool] = None
    requires_cost_center: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)
```

#### Response Exitosa (200)
```json
{
  "id": "87654321-4321-4321-4321-987654321098",
  "code": "1.1.02.03",
  "name": "Banco XYZ Cuenta Principal",
  "description": "Cuenta bancaria principal para operaciones diarias",
  "account_type": "ACTIVO",
  "category": "ACTIVO_CORRIENTE",
  "parent_id": "22222222-2222-2222-2222-222222222222",
  "level": 4,
  "is_active": true,
  "allows_movements": true,
  "requires_third_party": false,
  "requires_cost_center": false,
  "balance": "5000.00",
  "debit_balance": "10000.00",
  "credit_balance": "5000.00",
  "notes": "Cuenta actualizada junio 2025",
  "created_by_id": "99999999-9999-9999-9999-999999999999",
  "created_at": "2025-06-10T14:30:00Z",
  "updated_at": "2025-06-10T15:00:00Z"
}
```

#### Códigos de Error
- **403 Forbidden**: Permisos insuficientes
- **404 Not Found**: Cuenta no encontrada
- **422 Unprocessable Entity**: Datos de entrada inválidos

---

### 🗑️ DELETE /{account_id}

Elimina una cuenta existente.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
DELETE /api/v1/accounts/87654321-4321-4321-4321-987654321098
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (204)
```
No Content
```

#### Códigos de Error
- **403 Forbidden**: Permisos insuficientes
- **404 Not Found**: Cuenta no encontrada
- **409 Conflict**: No se puede eliminar (tiene movimientos o hijos)

---

### 💰 GET /{account_id}/balance

Obtiene el saldo de una cuenta a una fecha específica.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/87654321-4321-4321-4321-987654321098/balance?as_of_date=2025-06-15
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `as_of_date` (date, opcional): Fecha para el cálculo del balance (default: fecha actual)

#### Response Exitosa (200)
```json
{
  "account_id": "87654321-4321-4321-4321-987654321098",
  "account_code": "1.1.02.03",
  "account_name": "Banco XYZ Cuenta Principal",
  "debit_balance": "10000.00",
  "credit_balance": "5000.00",
  "net_balance": "5000.00",
  "normal_balance_side": "debit",
  "as_of_date": "2025-06-15"
}
```

---

### 📝 GET /{account_id}/movements

Obtiene el historial de movimientos de una cuenta en un período.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/87654321-4321-4321-4321-987654321098/movements?start_date=2025-06-01&end_date=2025-06-15
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `start_date` (date, opcional): Fecha inicial (default: primer día del mes actual)
- `end_date` (date, opcional): Fecha final (default: fecha actual)

#### Response Exitosa (200)
```json
{
  "account": {
    "id": "87654321-4321-4321-4321-987654321098",
    "code": "1.1.02.03",
    "name": "Banco XYZ Cuenta Principal",
    "account_type": "ACTIVO",
    "balance": "5000.00",
    "is_active": true,
    "allows_movements": true
  },
  "movements": [
    {
      "date": "2025-06-05",
      "journal_entry_number": "JE-2025-000123",
      "description": "Depósito inicial",
      "debit_amount": "10000.00",
      "credit_amount": "0.00",
      "balance": "10000.00",
      "reference": "Transferencia #9876"
    },
    {
      "date": "2025-06-10",
      "journal_entry_number": "JE-2025-000145",
      "description": "Pago a proveedor",
      "debit_amount": "0.00",
      "credit_amount": "5000.00",
      "balance": "5000.00",
      "reference": "Cheque #1001"
    }
  ],
  "period_start": "2025-06-01",
  "period_end": "2025-06-15",
  "opening_balance": "0.00",
  "closing_balance": "5000.00",
  "total_debits": "10000.00",
  "total_credits": "5000.00"
}
```

---

### ✅ POST /{account_id}/validate

Valida una cuenta específica y retorna errores/advertencias.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
POST /api/v1/accounts/87654321-4321-4321-4321-987654321098/validate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    "Esta cuenta no ha tenido movimientos en los últimos 30 días"
  ]
}
```

---

### 🔄 POST /bulk-operation

Realiza operaciones masivas en cuentas.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/accounts/bulk-operation
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "account_ids": [
    "87654321-4321-4321-4321-987654321098",
    "12345678-5678-5678-5678-123456789012"
  ],
  "operation": "deactivate",
  "reason": "Cuentas obsoletas que serán reemplazadas"
}
```

#### Schema de Request
```python
class BulkAccountOperation(BaseModel):
    """Schema para operaciones masivas"""
    account_ids: List[uuid.UUID]
    operation: str  # "activate", "deactivate", "delete"
    reason: Optional[str] = None
```

#### Response Exitosa (200)
```json
{
  "success": true,
  "operation": "deactivate",
  "affected_accounts": 2,
  "failed_operations": 0,
  "details": "2 cuentas desactivadas correctamente"
}
```

#### Códigos de Error
- **400 Bad Request**: Operación no válida
- **403 Forbidden**: Permisos insuficientes
- **422 Unprocessable Entity**: Datos de entrada inválidos

---

### 🏷️ GET /type/{account_type}

Obtiene todas las cuentas de un tipo específico.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/type/ACTIVO
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `active_only` (bool, opcional): Mostrar solo cuentas activas (default: true)

#### Response Exitosa (200)
```json
{
  "account_type": "ACTIVO",
  "accounts": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "code": "1",
      "name": "Activos",
      "account_type": "ACTIVO",
      "balance": "30000.00",
      "is_active": true,
      "allows_movements": false
    },
    {
      "id": "12345678-1234-1234-1234-123456789012",
      "code": "1.1",
      "name": "Activo Corriente",
      "account_type": "ACTIVO",
      "balance": "15000.00",
      "is_active": true,
      "allows_movements": false
    }
  ],
  "total_balance": "30000.00"
}
```

---

### 📤 GET /export/csv

Exporta cuentas a formato CSV.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/accounts/export/csv?account_type=ACTIVO&active_only=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `account_type` (AccountType, opcional): Filtrar por tipo de cuenta
- `active_only` (bool, opcional): Mostrar solo cuentas activas (default: true)

#### Response Exitosa (200)
```
Content-Type: text/csv
Content-Disposition: attachment; filename="accounts_export.csv"

code,name,full_name,account_type,category,parent_code,level,balance,is_active,allows_movements
1,Activos,Activos,ACTIVO,,null,1,30000.00,true,false
1.1,Activo Corriente,"Activos > Activo Corriente",ACTIVO,ACTIVO_CORRIENTE,1,2,15000.00,true,false
```

---

### 📥 POST /import

Importa cuentas desde archivo CSV/Excel.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/accounts/import
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: text/plain

code,name,account_type,category,parent_code,description
1.1.03,Inventarios,ACTIVO,ACTIVO_CORRIENTE,1.1,"Inventarios y mercancías"
1.1.03.01,Inventario de Mercaderías,ACTIVO,ACTIVO_CORRIENTE,1.1.03,"Productos para la venta"
```

#### Response Exitosa (201)
```json
{
  "success": true,
  "accounts_created": 2,
  "accounts_failed": 0,
  "details": "2 cuentas importadas correctamente"
}
```

## Códigos de Error Comunes

### 400 Bad Request
```json
{
  "detail": "Código de cuenta ya existe en el sistema",
  "error_code": "ACCOUNT_CODE_EXISTS"
}
```

### 403 Forbidden  
```json
{
  "detail": "Permisos insuficientes para esta operación",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

### 404 Not Found
```json
{
  "detail": "Cuenta no encontrada",
  "error_code": "ACCOUNT_NOT_FOUND"
}
```

### 409 Conflict
```json
{
  "detail": "No se puede eliminar una cuenta con movimientos",
  "error_code": "ACCOUNT_HAS_MOVEMENTS"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "code"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Flujos de Integración

### Gestión Completa del Plan de Cuentas

1. **Creación del Plan**: 
   - Crear cuentas principales (nivel 1)
   - Crear subcuentas (nivel 2, 3, etc.)
   - Verificar estructura con `/tree`

2. **Operatividad**:
   - Consultar saldos con `/{account_id}/balance`
   - Consultar movimientos con `/{account_id}/movements`
   - Verificar estadísticas con `/stats`

3. **Mantenimiento**:
   - Actualizar cuentas con `PUT /{account_id}`
   - Desactivar cuentas obsoletas con `/bulk-operation`
   - Exportar plan para respaldo con `/export/csv`

## Testing de Endpoints

### Tests para Usuarios Regulares

```python
def test_user_can_view_accounts(client, regular_user_token):
    response = client.get(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {regular_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_user_cannot_create_account(client, regular_user_token):
    account_data = {
        "code": "1.1.99",
        "name": "Cuenta Test",
        "account_type": "ACTIVO"
    }
    
    response = client.post(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {regular_user_token}"},
        json=account_data
    )
    
    assert response.status_code == 403
```

### Tests para Contadores

```python
def test_contador_can_create_account(client, contador_token):
    account_data = {
        "code": "1.1.99",
        "name": "Cuenta Test Contador",
        "account_type": "ACTIVO",
        "category": "ACTIVO_CORRIENTE"
    }
    
    response = client.post(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {contador_token}"},
        json=account_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "1.1.99"
    assert data["name"] == "Cuenta Test Contador"
```

### Tests para Administradores

```python
def test_admin_can_delete_account(client, admin_token, account_without_movements):
    response = client.delete(
        f"/api/v1/accounts/{account_without_movements.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 204

def test_admin_cannot_delete_account_with_movements(client, admin_token, account_with_movements):
    response = client.delete(
        f"/api/v1/accounts/{account_with_movements.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 409
    assert "movimientos" in response.json()["detail"]
```

## Referencias

- [Modelo de Cuenta](../account-management.md): Documentación detallada del modelo de datos
- [Tipos de Cuenta](../account-types.md): Descripción de tipos y categorías de cuentas
- [Plan de Cuentas](../chart-of-accounts.md): Estructura y organización jerárquica
- [Movimientos de Cuentas](../account-movements.md): Gestión de movimientos y saldos
