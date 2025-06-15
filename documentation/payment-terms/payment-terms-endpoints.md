# API de Términos de Pago - Documentación Actualizada

## Descripción General

La API de términos de pago proporciona funcionalidades para gestionar condiciones de pago con cronogramas personalizables, cálculos automáticos de fechas de vencimiento y validaciones empresariales.

### Características Principales

- **CRUD completo** de términos de pago
- **Cronogramas de pago** configurables
- **Cálculo automático** de fechas de vencimiento
- **Validaciones empresariales** 
- **Estado activo/inactivo** para control
- **Búsqueda y filtros** avanzados
- **Integración** con asientos contables y terceros

## Autenticación

Todos los endpoints requieren autenticación Bearer Token:

```
Authorization: Bearer <jwt_token>
```

## Permisos Requeridos

- **Acceso básico**: Usuarios autenticados pueden consultar términos de pago
- **Modificación**: Roles ADMIN y CONTADOR pueden crear/actualizar/eliminar

## Conceptos Clave

### Términos de Pago

Los términos de pago definen:
- **Código único**: Identificador del término (ej: "30D", "45D", "CONTADO")
- **Nombre descriptivo**: Descripción del término
- **Cronograma**: Lista de cuotas con días y porcentajes
- **Estado**: Activo/Inactivo para control de uso

### Cronograma de Pagos

Cada término puede tener múltiples cuotas:
- **Días**: Días desde la fecha base para el vencimiento
- **Porcentaje**: Porcentaje del total a pagar en esa cuota
- **Orden**: Secuencia de las cuotas

## Endpoints

### 1. Crear Términos de Pago

**POST** `/payment-terms/`

Crea nuevos términos de pago con su cronograma.

**Request Body:**
```json
{
  "code": "30D",
  "name": "30 días",
  "description": "Pago a 30 días fecha factura",
  "is_active": true,
  "payment_schedule": [
    {
      "days": 30,
      "percentage": 100.0,
      "sequence_order": 1
    }
  ]
}
```

**Ejemplo cronograma múltiple:**
```json
{
  "code": "30-60D",
  "name": "30-60 días",
  "description": "50% a 30 días, 50% a 60 días",
  "is_active": true,
  "payment_schedule": [
    {
      "days": 30,
      "percentage": 50.0,
      "sequence_order": 1
    },
    {
      "days": 60,
      "percentage": 50.0,
      "sequence_order": 2
    }
  ]
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "30D",
  "name": "30 días",
  "description": "Pago a 30 días fecha factura",
  "is_active": true,
  "created_at": "2024-12-01T10:00:00Z",
  "updated_at": "2024-12-01T10:00:00Z",
  "payment_schedule": [
    {
      "id": "schedule-id-1",
      "days": 30,
      "percentage": 100.0,
      "sequence_order": 1,
      "payment_terms_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "total_days": 30,
  "installments_count": 1,
  "is_immediate": false
}
```

### 2. Listar Términos de Pago

**GET** `/payment-terms/`

Obtiene una lista paginada de términos de pago con filtros opcionales.

**Query Parameters:**
- `skip` (int): Registros a omitir (default: 0)
- `limit` (int): Registros por página (default: 100, max: 1000)
- `is_active` (bool): Filtrar por estado activo
- `search_text` (string): Buscar en código, nombre o descripción
- `min_days` (int): Días mínimos del primer pago
- `max_days` (int): Días máximos del último pago

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "CONTADO",
    "name": "Contado",
    "description": "Pago inmediato",
    "is_active": true,
    "total_days": 0,
    "installments_count": 1,
    "is_immediate": true
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "code": "30D",
    "name": "30 días",
    "description": "Pago a 30 días fecha factura",
    "is_active": true,
    "total_days": 30,
    "installments_count": 1,
    "is_immediate": false
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "code": "30-60D",
    "name": "30-60 días",
    "description": "50% a 30 días, 50% a 60 días",
    "is_active": true,
    "total_days": 60,
    "installments_count": 2,
    "is_immediate": false
  }
]
```

### 3. Obtener Términos Activos

**GET** `/payment-terms/active`

Obtiene todos los términos de pago activos para uso en formularios.

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "CONTADO",
    "name": "Contado",
    "description": "Pago inmediato",
    "is_active": true
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "code": "30D",
    "name": "30 días",
    "description": "Pago a 30 días fecha factura",
    "is_active": true
  }
]
```

### 4. Obtener Término por ID

**GET** `/payment-terms/{payment_terms_id}`

Obtiene los detalles completos de un término de pago incluyendo su cronograma.

**Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "code": "30-60D",
  "name": "30-60 días",
  "description": "50% a 30 días, 50% a 60 días",
  "is_active": true,
  "created_at": "2024-12-01T10:00:00Z",
  "updated_at": "2024-12-01T10:00:00Z",
  "payment_schedule": [
    {
      "id": "schedule-id-1",
      "days": 30,
      "percentage": 50.0,
      "sequence_order": 1,
      "payment_terms_id": "770e8400-e29b-41d4-a716-446655440002"
    },
    {
      "id": "schedule-id-2",
      "days": 60,
      "percentage": 50.0,
      "sequence_order": 2,
      "payment_terms_id": "770e8400-e29b-41d4-a716-446655440002"
    }
  ],
  "total_days": 60,
  "installments_count": 2,
  "is_immediate": false
}
```

### 5. Obtener Término por Código

**GET** `/payment-terms/code/{code}`

Obtiene un término de pago usando su código único.

**Path Parameters:**
- `code` (string): Código del término de pago

**Response (200):** Igual que obtener por ID

### 6. Actualizar Términos de Pago

**PUT** `/payment-terms/{payment_terms_id}`

Actualiza un término de pago y opcionalmente su cronograma.

**Request Body:**
```json
{
  "name": "30 días neto",
  "description": "Pago neto a 30 días fecha factura",
  "is_active": true,
  "payment_schedule": [
    {
      "days": 30,
      "percentage": 100.0,
      "sequence_order": 1
    }
  ]
}
```

**Response (200):** Término actualizado con detalles completos

### 7. Alternar Estado Activo

**PATCH** `/payment-terms/{payment_terms_id}/toggle-active`

Alterna el estado activo/inactivo del término de pago.

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "30D",
  "name": "30 días",
  "description": "Pago a 30 días fecha factura",
  "is_active": false
}
```

### 8. Eliminar Términos de Pago

**DELETE** `/payment-terms/{payment_terms_id}`

Elimina un término de pago si no está en uso.

**Response (204):** Sin contenido

### 9. Calcular Cronograma de Pagos

**POST** `/payment-terms/calculate`

Calcula fechas y montos de pago basados en términos específicos.

**Request Body:**
```json
{
  "payment_terms_id": "770e8400-e29b-41d4-a716-446655440002",
  "base_date": "2024-12-01",
  "total_amount": 1000.00,
  "currency": "COP"
}
```

**Response (200):**
```json
{
  "payment_terms": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "code": "30-60D",
    "name": "30-60 días"
  },
  "base_date": "2024-12-01",
  "total_amount": 1000.00,
  "currency": "COP",
  "calculated_schedule": [
    {
      "installment_number": 1,
      "due_date": "2024-12-31",
      "days_from_base": 30,
      "amount": 500.00,
      "percentage": 50.0,
      "is_overdue": false
    },
    {
      "installment_number": 2,
      "due_date": "2025-01-30",
      "days_from_base": 60,
      "amount": 500.00,
      "percentage": 50.0,
      "is_overdue": false
    }
  ],
  "summary": {
    "total_installments": 2,
    "first_due_date": "2024-12-31",
    "last_due_date": "2025-01-30",
    "total_days": 60,
    "average_days": 45
  }
}
```

### 10. Validar Términos de Pago

**GET** `/payment-terms/{payment_terms_id}/validate`

Valida un término de pago y retorna detalles de la validación.

**Response (200):**
```json
{
  "payment_terms_id": "770e8400-e29b-41d4-a716-446655440002",
  "is_valid": true,
  "validation_details": {
    "code_unique": true,
    "schedule_complete": true,
    "percentages_sum_100": true,
    "days_ascending": true,
    "no_duplicate_days": true
  },
  "errors": [],
  "warnings": [],
  "usage_info": {
    "used_in_journal_entries": 15,
    "used_in_third_parties": 3,
    "can_be_deleted": false,
    "can_be_deactivated": true
  },
  "schedule_analysis": {
    "total_installments": 2,
    "days_range": {
      "min": 30,
      "max": 60,
      "average": 45
    },
    "percentage_distribution": [
      {
        "installment": 1,
        "percentage": 50.0,
        "days": 30
      },
      {
        "installment": 2,
        "percentage": 50.0,
        "days": 60
      }
    ]
  }
}
```

## Validaciones de Negocio

### Validaciones del Código

- **Único**: No puede repetirse
- **Formato**: Alfanumérico, máximo 20 caracteres
- **Requerido**: No puede estar vacío

### Validaciones del Cronograma

- **Porcentajes**: La suma debe ser exactamente 100%
- **Días únicos**: No puede haber días duplicados
- **Orden ascendente**: Los días deben estar en orden creciente
- **Valores positivos**: Días y porcentajes deben ser positivos
- **Al menos una cuota**: Debe tener mínimo una cuota

### Validaciones de Eliminación

- **No en uso**: No puede eliminarse si está siendo usado en:
  - Asientos contables
  - Terceros como término por defecto
  - Facturas o documentos

## Ejemplos de Términos Comunes

### Contado
```json
{
  "code": "CONTADO",
  "name": "Contado",
  "description": "Pago inmediato",
  "payment_schedule": [
    {
      "days": 0,
      "percentage": 100.0,
      "sequence_order": 1
    }
  ]
}
```

### 30 días
```json
{
  "code": "30D",
  "name": "30 días",
  "description": "Pago a 30 días fecha factura",
  "payment_schedule": [
    {
      "days": 30,
      "percentage": 100.0,
      "sequence_order": 1
    }
  ]
}
```

### 30-60-90 días (3 cuotas iguales)
```json
{
  "code": "30-60-90D",
  "name": "30-60-90 días",
  "description": "3 cuotas iguales: 30, 60 y 90 días",
  "payment_schedule": [
    {
      "days": 30,
      "percentage": 33.33,
      "sequence_order": 1
    },
    {
      "days": 60,
      "percentage": 33.33,
      "sequence_order": 2
    },
    {
      "days": 90,
      "percentage": 33.34,
      "sequence_order": 3
    }
  ]
}
```

### Anticipo + Saldo
```json
{
  "code": "20-80-30D",
  "name": "20% anticipo + 80% a 30 días",
  "description": "20% inmediato, 80% a 30 días",
  "payment_schedule": [
    {
      "days": 0,
      "percentage": 20.0,
      "sequence_order": 1
    },
    {
      "days": 30,
      "percentage": 80.0,
      "sequence_order": 2
    }
  ]
}
```

## Ejemplos de Integración

### Crear Término Completo

```python
import requests

# Crear término de pago con cronograma
response = requests.post(
    "https://api.contable.com/v1/payment-terms/",
    headers={"Authorization": "Bearer <token>"},
    json={
        "code": "15-30D",
        "name": "15-30 días",
        "description": "50% a 15 días, 50% a 30 días",
        "is_active": True,
        "payment_schedule": [
            {
                "days": 15,
                "percentage": 50.0,
                "sequence_order": 1
            },
            {
                "days": 30,
                "percentage": 50.0,
                "sequence_order": 2
            }
        ]
    }
)

term = response.json()
print(f"Término creado: {term['code']}")
```

### Calcular Fechas de Pago

```python
import requests
from datetime import date

# Calcular cronograma para una factura
response = requests.post(
    "https://api.contable.com/v1/payment-terms/calculate",
    headers={"Authorization": "Bearer <token>"},
    json={
        "payment_terms_id": "term-id",
        "base_date": "2024-12-01",
        "total_amount": 1500000.00,
        "currency": "COP"
    }
)

schedule = response.json()
for installment in schedule['calculated_schedule']:
    print(f"Cuota {installment['installment_number']}: "
          f"${installment['amount']:,.2f} "
          f"vence {installment['due_date']}")
```

### Buscar Términos Activos

```python
import requests

# Obtener términos para formulario
response = requests.get(
    "https://api.contable.com/v1/payment-terms/active",
    headers={"Authorization": "Bearer <token>"}
)

terms = response.json()
for term in terms:
    print(f"{term['code']}: {term['name']}")
```

### Validar Término

```python
import requests

# Validar término antes de usar
response = requests.get(
    "https://api.contable.com/v1/payment-terms/term-id/validate",
    headers={"Authorization": "Bearer <token>"}
)

validation = response.json()
if validation['is_valid']:
    print("Término válido")
else:
    print("Errores encontrados:")
    for error in validation['errors']:
        print(f"- {error}")
```

## Casos de Uso Comunes

### 1. Configuración Inicial

Crear términos básicos para la empresa:

```python
basic_terms = [
    {
        "code": "CONTADO",
        "name": "Contado",
        "description": "Pago inmediato",
        "payment_schedule": [{"days": 0, "percentage": 100.0, "sequence_order": 1}]
    },
    {
        "code": "30D",
        "name": "30 días",
        "description": "Pago a 30 días",
        "payment_schedule": [{"days": 30, "percentage": 100.0, "sequence_order": 1}]
    },
    {
        "code": "60D",
        "name": "60 días",
        "description": "Pago a 60 días",
        "payment_schedule": [{"days": 60, "percentage": 100.0, "sequence_order": 1}]
    }
]

for term in basic_terms:
    response = requests.post(
        "https://api.contable.com/v1/payment-terms/",
        headers={"Authorization": "Bearer <token>"},
        json=term
    )
```

### 2. Cálculo de Vencimientos

```python
def calculate_due_dates(payment_terms_id, invoice_date, invoice_amount):
    response = requests.post(
        "https://api.contable.com/v1/payment-terms/calculate",
        headers={"Authorization": "Bearer <token>"},
        json={
            "payment_terms_id": payment_terms_id,
            "base_date": invoice_date,
            "total_amount": invoice_amount,
            "currency": "COP"
        }
    )
    
    return response.json()['calculated_schedule']
```

### 3. Validación Masiva

```python
def validate_all_terms():
    # Obtener todos los términos
    response = requests.get(
        "https://api.contable.com/v1/payment-terms/",
        headers={"Authorization": "Bearer <token>"}
    )
    
    invalid_terms = []
    for term in response.json():
        validation = requests.get(
            f"https://api.contable.com/v1/payment-terms/{term['id']}/validate",
            headers={"Authorization": "Bearer <token>"}
        ).json()
        
        if not validation['is_valid']:
            invalid_terms.append({
                'term': term,
                'errors': validation['errors']
            })
    
    return invalid_terms
```

## Códigos de Error Comunes

| Código | Descripción |
|--------|-------------|
| 400 | Error de validación (cronograma inválido, porcentajes incorrectos) |
| 404 | Término de pago no encontrado |
| 409 | Código duplicado |
| 422 | No se puede eliminar (término en uso) |
| 500 | Error interno del servidor |

## Mejores Prácticas

1. **Códigos descriptivos**: Usar códigos que reflejen el cronograma (ej: "30D", "30-60D")
2. **Validar porcentajes**: Verificar que sumen exactamente 100%
3. **Orden lógico**: Mantener días en orden ascendente
4. **Términos estándar**: Crear términos comunes para toda la empresa
5. **Estado activo**: Usar el estado activo para controlar disponibilidad
6. **Documentación**: Incluir descripciones claras en cada término
7. **Validación previa**: Validar términos antes de eliminar o modificar
8. **Backup**: Exportar configuración de términos periódicamente

## Integración con Otros Módulos

### Asientos Contables
Los términos de pago se pueden asociar a líneas de asientos contables para calcular vencimientos automáticamente.

### Terceros
Los terceros pueden tener términos de pago por defecto que se aplican automáticamente.

### Reportes
Los términos de pago se utilizan en reportes de cartera y flujo de caja para proyecciones.

### Facturación
Sistema de facturación puede usar términos para calcular fechas de vencimiento automáticamente.
