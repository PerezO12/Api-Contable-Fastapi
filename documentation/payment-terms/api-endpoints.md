# Endpoints del API - Condiciones de Pago

## Descripción General

El módulo de condiciones de pago proporciona un conjunto completo de endpoints REST para gestionar condiciones de pago, cronogramas y cálculos relacionados.

## Base URL
```
/api/v1/payment-terms
```

## Endpoints Disponibles

### 1. Crear Condiciones de Pago
```http
POST /api/v1/payment-terms/
```

#### Request Body
```json
{
  "code": "30-60",
  "name": "30-60 días",
  "description": "Pago fraccionado: 50% a 30 días, 50% a 60 días",
  "is_active": true,
  "notes": "Condiciones especiales para clientes premium",
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 30,
      "percentage": 50.00,
      "description": "Primer pago - 50%"
    },
    {
      "sequence": 2,
      "days": 60,
      "percentage": 50.00,
      "description": "Segundo pago - 50%"
    }
  ]
}
```

#### Response (201 Created)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "30-60",
  "name": "30-60 días",
  "description": "Pago fraccionado: 50% a 30 días, 50% a 60 días",
  "is_active": true,
  "notes": "Condiciones especiales para clientes premium",
  "total_percentage": 100.00,
  "max_days": 60,
  "is_valid": true,
  "created_at": "2025-06-14T10:00:00Z",
  "updated_at": "2025-06-14T10:00:00Z",
  "payment_schedules": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "sequence": 1,
      "days": 30,
      "percentage": 50.00,
      "description": "Primer pago - 50%",
      "created_at": "2025-06-14T10:00:00Z",
      "updated_at": "2025-06-14T10:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "sequence": 2,
      "days": 60,
      "percentage": 50.00,
      "description": "Segundo pago - 50%",
      "created_at": "2025-06-14T10:00:00Z",
      "updated_at": "2025-06-14T10:00:00Z"
    }
  ]
}
```

### 2. Listar Condiciones de Pago
```http
GET /api/v1/payment-terms/?skip=0&limit=10&is_active=true&search=30
```

#### Query Parameters
- `skip` (int): Número de registros a omitir (default: 0)
- `limit` (int): Número máximo de registros (default: 10, max: 100)
- `is_active` (bool): Filtrar por estado activo/inactivo
- `search` (str): Búsqueda en código, nombre o descripción

#### Response (200 OK)
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "code": "30D",
      "name": "30 días",
      "description": "Pago a 30 días fecha factura",
      "is_active": true,
      "total_percentage": 100.00,
      "max_days": 30,
      "is_valid": true,
      "payment_schedules_count": 1
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

### 3. Obtener Condiciones Activas
```http
GET /api/v1/payment-terms/active
```

#### Response (200 OK)
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "CONTADO",
    "name": "Contado",
    "max_days": 0
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "code": "30D",
    "name": "30 días",
    "max_days": 30
  }
]
```

### 4. Obtener por ID
```http
GET /api/v1/payment-terms/{id}
```

#### Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "30-60",
  "name": "30-60 días",
  "description": "Pago fraccionado: 50% a 30 días, 50% a 60 días",
  "is_active": true,
  "total_percentage": 100.00,
  "max_days": 60,
  "is_valid": true,
  "payment_schedules": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "sequence": 1,
      "days": 30,
      "percentage": 50.00,
      "description": "Primer pago - 50%"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "sequence": 2,
      "days": 60,
      "percentage": 50.00,
      "description": "Segundo pago - 50%"
    }
  ]
}
```

### 5. Obtener por Código
```http
GET /api/v1/payment-terms/code/{code}
```

#### Ejemplo
```http
GET /api/v1/payment-terms/code/30D
```

#### Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "30D",
  "name": "30 días",
  "description": "Pago a 30 días fecha factura",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 30,
      "percentage": 100.00,
      "description": "Pago único a 30 días"
    }
  ]
}
```

### 6. Actualizar Condiciones de Pago
```http
PUT /api/v1/payment-terms/{id}
```

#### Request Body
```json
{
  "code": "30-60-MODIFIED",
  "name": "30-60 días modificado",
  "description": "Versión actualizada de condiciones 30-60",
  "is_active": true,
  "payment_schedules": [
    {
      "sequence": 1,
      "days": 30,
      "percentage": 60.00,
      "description": "Primer pago - 60%"
    },
    {
      "sequence": 2,
      "days": 60,
      "percentage": 40.00,
      "description": "Segundo pago - 40%"
    }
  ]
}
```

#### Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "30-60-MODIFIED",
  "name": "30-60 días modificado",
  "updated_at": "2025-06-14T11:00:00Z",
  "payment_schedules": [...]
}
```

### 7. Activar/Desactivar
```http
PATCH /api/v1/payment-terms/{id}/toggle-active
```

#### Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "30D",
  "name": "30 días",
  "is_active": false,
  "updated_at": "2025-06-14T11:30:00Z"
}
```

### 8. Eliminar Condiciones de Pago
```http
DELETE /api/v1/payment-terms/{id}
```

#### Response (204 No Content)
```
(Sin contenido)
```

### 9. Calcular Cronograma de Pagos
```http
POST /api/v1/payment-terms/calculate
```

#### Request Body
```json
{
  "payment_terms_id": "550e8400-e29b-41d4-a716-446655440000",
  "invoice_date": "2025-06-14",
  "amount": 10000.00
}
```

#### Response (200 OK)
```json
{
  "payment_terms": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "30-60",
    "name": "30-60 días"
  },
  "invoice_date": "2025-06-14",
  "total_amount": 10000.00,
  "schedule": [
    {
      "sequence": 1,
      "days": 30,
      "percentage": 50.00,
      "amount": 5000.00,
      "payment_date": "2025-07-14",
      "description": "Primer pago - 50%"
    },
    {
      "sequence": 2,
      "days": 60,
      "percentage": 50.00,
      "amount": 5000.00,
      "payment_date": "2025-08-13",
      "description": "Segundo pago - 50%"
    }
  ],
  "final_due_date": "2025-08-13"
}
```

### 10. Validar Condiciones de Pago
```http
GET /api/v1/payment-terms/{id}/validate
```

#### Response (200 OK)
```json
{
  "is_valid": true,
  "total_percentage": 100.00,
  "schedules_count": 2,
  "max_days": 60,
  "validation_errors": []
}
```

#### Response con Errores (200 OK)
```json
{
  "is_valid": false,
  "total_percentage": 90.00,
  "schedules_count": 2,
  "max_days": 60,
  "validation_errors": [
    "Los porcentajes deben sumar 100%, suma actual: 90%",
    "Faltan cronogramas para completar el 100%"
  ]
}
```

## Códigos de Error Comunes

### 400 Bad Request
```json
{
  "detail": "Los porcentajes deben sumar 100%, suma actual: 90%"
}
```

### 404 Not Found
```json
{
  "detail": "Condiciones de pago no encontradas"
}
```

### 409 Conflict
```json
{
  "detail": "Ya existe una condición de pago con el código '30D'"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "payment_schedules", 0, "percentage"],
      "msg": "El porcentaje debe ser mayor a 0",
      "input": 0
    }
  ]
}
```

## Filtros y Búsquedas Avanzadas

### Búsqueda por Texto
```http
GET /api/v1/payment-terms/?search=fraccionado
```
Busca en campos: `code`, `name`, `description`

### Filtros Combinados
```http
GET /api/v1/payment-terms/?is_active=true&search=30&limit=5
```

### Ordenamiento
```http
GET /api/v1/payment-terms/?sort_by=code&sort_order=asc
```

Campos ordenables:
- `code`
- `name`
- `created_at`
- `updated_at`
- `max_days`

## Ejemplos de Integración

### JavaScript/TypeScript
```typescript
// Crear condiciones de pago
const createPaymentTerms = async (data: PaymentTermsCreate) => {
  const response = await fetch('/api/v1/payment-terms/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });
  
  if (!response.ok) {
    throw new Error('Error al crear condiciones de pago');
  }
  
  return response.json();
};

// Calcular cronograma
const calculateSchedule = async (
  paymentTermsId: string, 
  invoiceDate: string, 
  amount: number
) => {
  const response = await fetch('/api/v1/payment-terms/calculate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      payment_terms_id: paymentTermsId,
      invoice_date: invoiceDate,
      amount: amount
    })
  });
  
  return response.json();
};
```

### Python
```python
import requests
from datetime import date
from decimal import Decimal

class PaymentTermsAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_payment_terms(self, data: dict) -> dict:
        response = requests.post(
            f'{self.base_url}/api/v1/payment-terms/',
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def calculate_schedule(
        self, 
        payment_terms_id: str, 
        invoice_date: date, 
        amount: Decimal
    ) -> dict:
        data = {
            'payment_terms_id': payment_terms_id,
            'invoice_date': invoice_date.isoformat(),
            'amount': float(amount)
        }
        
        response = requests.post(
            f'{self.base_url}/api/v1/payment-terms/calculate',
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

## Rate Limiting y Performance

### Límites de Tasa
- 100 requests por minuto por usuario
- 1000 requests por hora por usuario
- Límites especiales para endpoints de cálculo

### Optimizaciones
- Caché de condiciones activas (5 minutos)
- Paginación obligatoria en listados
- Índices optimizados para búsquedas

### Headers de Rate Limiting
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1625097600
```
