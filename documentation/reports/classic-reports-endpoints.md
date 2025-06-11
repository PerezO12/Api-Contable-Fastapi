# 📊 Endpoints de Reportes Clásicos

## Descripción General

Los endpoints de reportes clásicos proporcionan acceso a los reportes financieros fundamentales con esquemas estructurados específicos para cada tipo de reporte. Estos endpoints están optimizados para aplicaciones contables tradicionales que requieren formatos específicos y detallados.

## Base URL

```
Base URL: /api/v1/reports
```

## Autenticación

Todos los endpoints requieren autenticación mediante Bearer Token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints Disponibles

### 📊 GET /balance-sheet

Genera el Balance General (Estado de Situación Financiera) a una fecha específica.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/balance-sheet?as_of_date=2025-06-10&include_zero_balances=false&company_name=Mi%20Empresa
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `as_of_date` (date, opcional): Fecha del balance (default: hoy)
- `include_zero_balances` (bool, opcional): Incluir cuentas con saldo cero (default: false)
- `company_name` (string, opcional): Nombre de la empresa para el reporte

#### Response Exitosa (200)
```json
{
  "report_date": "2025-06-10",
  "company_name": "Mi Empresa S.A.",
  "assets": {
    "section_name": "ACTIVOS",
    "account_type": "ACTIVO",
    "items": [
      {
        "account_id": "11111111-1111-1111-1111-111111111111",
        "account_code": "1001",
        "account_name": "Caja",
        "balance": "50000.00",
        "level": 1,
        "children": []
      },
      {
        "account_id": "22222222-2222-2222-2222-222222222222",
        "account_code": "1002",
        "account_name": "Bancos",
        "balance": "120000.00",
        "level": 1,
        "children": []
      }
    ],
    "total": "170000.00"
  },
  "liabilities": {
    "section_name": "PASIVOS",
    "account_type": "PASIVO",
    "items": [
      {
        "account_id": "33333333-3333-3333-3333-333333333333",
        "account_code": "2001",
        "account_name": "Proveedores",
        "balance": "45000.00",
        "level": 1,
        "children": []
      }
    ],
    "total": "45000.00"
  },
  "equity": {
    "section_name": "PATRIMONIO",
    "account_type": "PATRIMONIO",
    "items": [
      {
        "account_id": "44444444-4444-4444-4444-444444444444",
        "account_code": "3001",
        "account_name": "Capital",
        "balance": "125000.00",
        "level": 1,
        "children": []
      }
    ],
    "total": "125000.00"
  },
  "total_assets": "170000.00",
  "total_liabilities_equity": "170000.00",
  "is_balanced": true
}
```

#### Códigos de Error
- **400 Bad Request**: Parámetros inválidos
- **401 Unauthorized**: Token inválido o expirado
- **500 Internal Server Error**: Error interno del servidor

---

### 📈 GET /income-statement

Genera el Estado de Resultados (Estado de Pérdidas y Ganancias) para un período específico.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/income-statement?start_date=2025-01-01&end_date=2025-06-10&include_zero_balances=false&company_name=Mi%20Empresa
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `start_date` (date, requerido): Fecha de inicio del período
- `end_date` (date, requerido): Fecha de fin del período
- `include_zero_balances` (bool, opcional): Incluir cuentas con saldo cero (default: false)
- `company_name` (string, opcional): Nombre de la empresa para el reporte

#### Response Exitosa (200)
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-06-10",
  "company_name": "Mi Empresa S.A.",
  "revenues": {
    "section_name": "INGRESOS",
    "items": [
      {
        "account_id": "55555555-5555-5555-5555-555555555555",
        "account_code": "4001",
        "account_name": "Ventas",
        "amount": "250000.00",
        "level": 1
      },
      {
        "account_id": "66666666-6666-6666-6666-666666666666",
        "account_code": "4002",
        "account_name": "Ingresos por Servicios",
        "amount": "75000.00",
        "level": 1
      }
    ],
    "total": "325000.00"
  },
  "expenses": {
    "section_name": "GASTOS",
    "items": [
      {
        "account_id": "77777777-7777-7777-7777-777777777777",
        "account_code": "5001",
        "account_name": "Gastos de Administración",
        "amount": "45000.00",
        "level": 1
      },
      {
        "account_id": "88888888-8888-8888-8888-888888888888",
        "account_code": "5002",
        "account_name": "Gastos de Ventas",
        "amount": "30000.00",
        "level": 1
      }
    ],
    "total": "75000.00"
  },
  "gross_profit": "325000.00",
  "operating_profit": "250000.00",
  "net_profit": "250000.00"
}
```

#### Códigos de Error
- **400 Bad Request**: Fechas inválidas o período incorrecto
- **401 Unauthorized**: Token inválido o expirado
- **422 Unprocessable Entity**: Fecha de fin anterior a fecha de inicio

---

### ⚖️ GET /trial-balance

Genera el Balance de Comprobación para verificar que débitos igualen créditos.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/trial-balance?as_of_date=2025-06-10&include_zero_balances=false&company_name=Mi%20Empresa
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `as_of_date` (date, opcional): Fecha del balance (default: hoy)
- `include_zero_balances` (bool, opcional): Incluir cuentas con saldo cero (default: false)
- `company_name` (string, opcional): Nombre de la empresa para el reporte

#### Response Exitosa (200)
```json
{
  "report_date": "2025-06-10",
  "company_name": "Mi Empresa S.A.",
  "accounts": [
    {
      "account_id": "11111111-1111-1111-1111-111111111111",
      "account_code": "1001",
      "account_name": "Caja",
      "opening_balance": "0.00",
      "debit_movements": "75000.00",
      "credit_movements": "25000.00",
      "closing_balance": "50000.00",
      "normal_balance_side": "debit"
    },
    {
      "account_id": "22222222-2222-2222-2222-222222222222",
      "account_code": "2001",
      "account_name": "Proveedores",
      "opening_balance": "0.00",
      "debit_movements": "5000.00",
      "credit_movements": "50000.00",
      "closing_balance": "45000.00",
      "normal_balance_side": "credit"
    }
  ],
  "total_debits": "450000.00",
  "total_credits": "450000.00",
  "is_balanced": true
}
```

#### Códigos de Error
- **400 Bad Request**: Parámetros inválidos
- **401 Unauthorized**: Token inválido o expirado

---

### 📚 GET /general-ledger

Genera el Libro Mayor mostrando todos los movimientos por cuenta.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/general-ledger?start_date=2025-01-01&end_date=2025-06-10&account_id=11111111-1111-1111-1111-111111111111&account_type=ACTIVO&company_name=Mi%20Empresa
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `start_date` (date, requerido): Fecha de inicio del período
- `end_date` (date, requerido): Fecha de fin del período
- `account_id` (UUID, opcional): Filtrar por cuenta específica
- `account_type` (AccountType, opcional): Filtrar por tipo de cuenta
- `company_name` (string, opcional): Nombre de la empresa para el reporte

#### Response Exitosa (200)
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-06-10",
  "company_name": "Mi Empresa S.A.",
  "accounts": [
    {
      "account_id": "11111111-1111-1111-1111-111111111111",
      "account_code": "1001",
      "account_name": "Caja",
      "opening_balance": "0.00",
      "movements": [
        {
          "date": "2025-01-15",
          "journal_entry_number": "001",
          "description": "Venta de mercadería",
          "debit_amount": "15000.00",
          "credit_amount": "0.00",
          "running_balance": "15000.00",
          "reference": "FAC-001"
        },
        {
          "date": "2025-01-20",
          "journal_entry_number": "002",
          "description": "Pago a proveedor",
          "debit_amount": "0.00",
          "credit_amount": "5000.00",
          "running_balance": "10000.00",
          "reference": "PAG-001"
        }
      ],
      "closing_balance": "50000.00",
      "total_debits": "75000.00",
      "total_credits": "25000.00"
    }
  ]
}
```

#### Códigos de Error
- **400 Bad Request**: Parámetros inválidos o período incorrecto
- **401 Unauthorized**: Token inválido o expirado
- **422 Unprocessable Entity**: Filtros incompatibles

---

### 💼 POST /export

Exporta reportes financieros a varios formatos (PDF, Excel, CSV).

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
POST /api/v1/reports/export
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "report_type": "balance_sheet",
  "format": "pdf",
  "parameters": {
    "as_of_date": "2025-06-10",
    "include_zero_balances": false,
    "company_name": "Mi Empresa S.A."
  },
  "template": "standard"
}
```

#### Schema de Request
```json
{
  "report_type": "balance_sheet | income_statement | trial_balance | general_ledger",
  "format": "pdf | excel | csv",
  "parameters": {
    "as_of_date": "2025-06-10",
    "start_date": "2025-01-01",
    "end_date": "2025-06-10",
    "include_zero_balances": false,
    "company_name": "string",
    "account_id": "uuid",
    "account_type": "ACTIVO | PASIVO | PATRIMONIO | INGRESO | GASTO"
  },
  "template": "standard | detailed | summary"
}
```

#### Response Exitosa (200)
```json
{
  "file_url": "/reports/downloads/balance_sheet_20250610_143022.pdf",
  "file_name": "balance_sheet_20250610_143022.pdf",
  "file_size": 234567,
  "format": "pdf",
  "generated_at": "2025-06-10T14:30:22Z",
  "expires_at": "2025-06-17T14:30:22Z"
}
```

#### Códigos de Error
- **400 Bad Request**: Parámetros de exportación inválidos
- **401 Unauthorized**: Token inválido o expirado
- **422 Unprocessable Entity**: Combinación inválida de parámetros

---

### 📊 GET /accounts-summary/{account_type}

Obtiene resumen de cuentas por tipo con saldos actuales.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/accounts-summary/ACTIVO?as_of_date=2025-06-10&include_zero_balances=false
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Path Parameters
- `account_type` (AccountType, requerido): Tipo de cuenta a resumir

#### Query Parameters
- `as_of_date` (date, opcional): Fecha del resumen (default: hoy)
- `include_zero_balances` (bool, opcional): Incluir cuentas con saldo cero (default: false)

#### Response Exitosa (200)
```json
[
  {
    "account_id": "11111111-1111-1111-1111-111111111111",
    "account_code": "1001",
    "account_name": "Caja",
    "account_type": "ACTIVO",
    "opening_balance": 0.0,
    "total_debits": 75000.0,
    "total_credits": 25000.0,
    "closing_balance": 50000.0,
    "movement_count": 15
  },
  {
    "account_id": "22222222-2222-2222-2222-222222222222",
    "account_code": "1002",
    "account_name": "Bancos",
    "account_type": "ACTIVO",
    "opening_balance": 0.0,
    "total_debits": 200000.0,
    "total_credits": 80000.0,
    "closing_balance": 120000.0,
    "movement_count": 28
  }
]
```

#### Códigos de Error
- **400 Bad Request**: Tipo de cuenta inválido
- **401 Unauthorized**: Token inválido o expirado

---

### 🔍 GET /accounting-integrity

Verifica la integridad contable y validación de balances.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/accounting-integrity?as_of_date=2025-06-10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `as_of_date` (date, opcional): Fecha de verificación (default: hoy)

#### Response Exitosa (200)
```json
{
  "as_of_date": "2025-06-10",
  "balance_sheet_balanced": true,
  "balance_sheet_equation": {
    "assets": 170000.0,
    "liabilities_equity": 170000.0,
    "difference": 0.0
  },
  "trial_balance_balanced": true,
  "trial_balance_totals": {
    "total_debits": 450000.0,
    "total_credits": 450000.0,
    "difference": 0.0
  },
  "overall_integrity": true,
  "timestamp": "2025-06-10T14:30:22Z"
}
```

#### Códigos de Error
- **400 Bad Request**: Parámetros inválidos
- **401 Unauthorized**: Token inválido o expirado
- **500 Internal Server Error**: Error al verificar integridad

---

## Tipos de Datos

### AccountType (Enum)
```
ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS
```

### Formatos de Exportación
```
pdf, excel, csv
```

### Plantillas de Exportación
```
standard, detailed, summary
```

## Consideraciones de Rendimiento

- Los reportes se generan de forma asíncrona para mejor rendimiento
- Se implementa caching inteligente para consultas frecuentes
- Los archivos exportados tienen un tiempo de vida limitado (7 días)
- Las consultas complejas pueden tomar varios segundos

## Límites y Restricciones

- **Período máximo**: 1 año para reportes detallados
- **Tamaño de archivo**: Máximo 50MB para exportaciones
- **Rate limiting**: 10 solicitudes por minuto por usuario
- **Retención**: Los archivos exportados se eliminan automáticamente después de 7 días

## Ejemplos de Uso

### Verificación Diaria de Balances
```http
GET /api/v1/reports/accounting-integrity
```

### Reporte Mensual para Gerencia
```http
POST /api/v1/reports/export
{
  "report_type": "income_statement",
  "format": "pdf",
  "parameters": {
    "start_date": "2025-05-01",
    "end_date": "2025-05-31",
    "template": "summary"
  }
}
```

### Análisis de Cuentas de Activo
```http
GET /api/v1/reports/accounts-summary/ACTIVO?include_zero_balances=false
```
