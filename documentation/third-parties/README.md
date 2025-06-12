# Sistema de Terceros

El módulo de Terceros es una funcionalidad integral del sistema contable que permite gestionar la información de clientes, proveedores, empleados y otros terceros. Implementado en el Sprint 2, ofrece capacidades completas de gestión, seguimiento y análisis de relaciones comerciales.

## Índice de Documentación

### Documentos Principales
- [Gestión de Terceros](./third-party-management.md) - CRUD y administración básica
- [Estados de Cuenta](./third-party-statements.md) - Generación de estados de cuenta
- [Balances y Antigüedad](./third-party-balances.md) - Análisis de saldos y vencimientos
- [Operaciones Masivas](./third-party-operations.md) - Importación y actualización masiva
- [Endpoints de Terceros](./third-party-endpoints.md) - Documentación completa de APIs

## Características Principales

### ✅ **Gestión Integral de Terceros**
- Clientes, proveedores y empleados
- Información comercial completa
- Datos de contacto y ubicación
- Configuración de términos de pago

### ✅ **Estados de Cuenta Automáticos**
- Generación en tiempo real
- Filtrado por fechas y tipos
- Cálculo automático de saldos
- Formato profesional para envío

### ✅ **Análisis de Balances**
- Saldos actuales por tercero
- Análisis de antigüedad de saldos
- Identificación de vencimientos
- Alertas de cobranza/pago

### ✅ **Operaciones Masivas**
- Importación desde archivos
- Actualización masiva de datos
- Sincronización con sistemas externos
- Validaciones automáticas

## Arquitectura del Módulo

```
app/
├── models/
│   └── third_party.py              # Modelo de datos principal
├── schemas/
│   └── third_party.py              # Esquemas Pydantic y validaciones
├── services/
│   └── third_party_service.py      # Lógica de negocio y servicios
└── api/v1/
    └── third_parties.py            # Endpoints completos de API
```

## Integración con el Sistema

### **Conexión con Asientos Contables**
Los terceros se integran directamente con el sistema contable:

```python
# En JournalEntryLine
third_party_id: Optional[UUID] = mapped_column(ForeignKey("third_parties.id"))
third_party: Optional["ThirdParty"] = relationship("ThirdParty")
```

### **Análisis Automático**
- Cálculo automático de saldos basado en movimientos contables
- Generación de estados de cuenta en tiempo real
- Análisis de antigüedad de saldos
- Alertas automáticas de vencimientos

## Tipos de Terceros

### 1. **Clientes**
```python
# Ejemplo: Cliente comercial
{
    "type": "CLIENTE",
    "document_type": "RUT",
    "document_number": "12345678-9",
    "business_name": "Empresa Cliente S.A.",
    "commercial_name": "Cliente Corp",
    "payment_terms": 30,  # días
    "credit_limit": 500000.00,
    "is_active": true
}
```

### 2. **Proveedores**
```python
# Ejemplo: Proveedor de servicios
{
    "type": "PROVEEDOR",
    "document_type": "RUT",
    "document_number": "98765432-1",
    "business_name": "Servicios XYZ Ltda.",
    "contact_person": "Juan Pérez",
    "payment_terms": 15,  # días
    "is_active": true
}
```

### 3. **Empleados**
```python
# Ejemplo: Empleado
{
    "type": "EMPLEADO",
    "document_type": "CI",
    "document_number": "12345678",
    "first_name": "María",
    "last_name": "González",
    "position": "Contadora",
    "department": "Finanzas",
    "is_active": true
}
```

## Casos de Uso Principales

### 1. **Gestión de Clientes**
```python
# Registro completo de cliente
cliente = {
    "document_type": "RUT",
    "document_number": "76543210-K",
    "business_name": "Distribuidora ABC S.A.",
    "commercial_name": "ABC Distribución",
    "email": "facturacion@abc.com",
    "phone": "+56912345678",
    "address": "Av. Principal 123",
    "city": "Santiago",
    "country": "Chile",
    "payment_terms": 30,
    "credit_limit": 1000000.00,
    "discount_percentage": 5.0
}
```

### 2. **Estados de Cuenta**
```python
# Generación de estado de cuenta
estado_cuenta = await third_party_service.generate_statement(
    third_party_id=cliente_id,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    include_details=True
)

# Resultado:
{
    "third_party": cliente_info,
    "period": {"start": "2024-01-01", "end": "2024-12-31"},
    "opening_balance": 0.00,
    "movements": [
        {
            "date": "2024-01-15",
            "reference": "FAC-001",
            "description": "Venta de productos",
            "debit": 150000.00,
            "credit": 0.00,
            "balance": 150000.00
        }
    ],
    "closing_balance": 150000.00,
    "summary": {
        "total_debits": 500000.00,
        "total_credits": 350000.00,
        "net_balance": 150000.00
    }
}
```

### 3. **Análisis de Antigüedad**
```python
# Análisis de antigüedad de saldos
analisis = await third_party_service.get_aging_analysis(
    third_party_id=cliente_id,
    as_of_date=date.today()
)

# Resultado:
{
    "third_party": cliente_info,
    "as_of_date": "2024-12-11",
    "current_balance": 150000.00,
    "aging_buckets": {
        "current": 50000.00,      # 0-30 días
        "30_days": 30000.00,      # 31-60 días
        "60_days": 40000.00,      # 61-90 días
        "90_days": 20000.00,      # 91-120 días
        "over_120": 10000.00      # Más de 120 días
    },
    "overdue_amount": 100000.00,
    "overdue_percentage": 66.67
}
```

## APIs Disponibles

### **Endpoints CRUD** (`/api/v1/third-parties`)
- `GET /` - Listar terceros con filtros avanzados
- `POST /` - Crear nuevo tercero con validaciones
- `GET /{id}` - Obtener tercero específico
- `PUT /{id}` - Actualizar información de tercero
- `DELETE /{id}` - Desactivar tercero (soft delete)

### **Endpoints de Consulta** (`/api/v1/third-parties`)
- `GET /search` - Búsqueda avanzada multi-criterio
- `GET /{id}/statement` - Estado de cuenta detallado
- `GET /{id}/balance` - Balance y saldos actuales
- `GET /{id}/aging` - Análisis de antigüedad

### **Endpoints de Operaciones** (`/api/v1/third-parties`)
- `POST /bulk-operations` - Operaciones masivas
- `POST /import` - Importación desde archivos
- `GET /export` - Exportación de datos
- `POST /{id}/sync` - Sincronización con sistemas externos

## Métricas y Análisis

### **Métricas de Clientes**
- **Saldo Pendiente**: Total adeudado por el cliente
- **Días Promedio de Pago**: Tiempo promedio de cobro
- **Límite de Crédito Utilizado**: Porcentaje del límite usado
- **Historial de Pagos**: Comportamiento de pago histórico

### **Métricas de Proveedores**
- **Saldo a Pagar**: Total pendiente de pago
- **Días Promedio de Pago**: Tiempo promedio de pago a proveedor
- **Descuentos Obtenidos**: Descuentos por pronto pago
- **Evaluación de Proveedor**: Calificación de desempeño

### **Indicadores de Gestión**
- **Rotación de Cartera**: Velocidad de cobro
- **Índice de Morosidad**: Porcentaje de cartera vencida
- **Concentración de Clientes**: Dependencia de clientes principales
- **Plazo Promedio de Cobro/Pago**: Indicadores de liquidez

## Validaciones y Reglas de Negocio

### **Validaciones de Documento**
```python
# Validación de RUT chileno
def validate_rut(rut: str) -> bool:
    """Validar formato y dígito verificador de RUT"""
    # Implementación del algoritmo de validación

# Validación por país
DOCUMENT_VALIDATIONS = {
    "Chile": {"RUT": validate_rut, "CI": validate_ci},
    "Argentina": {"CUIT": validate_cuit, "DNI": validate_dni},
    "Colombia": {"NIT": validate_nit, "CC": validate_cc}
}
```

### **Reglas de Negocio**
- **Unicidad**: Un documento no puede estar duplicado por tipo
- **Integridad**: Terceros con movimientos no pueden eliminarse
- **Consistencia**: Tipos de documento deben coincidir con el país
- **Validación**: Datos de contacto deben tener formato válido

## Seguridad y Auditoría

### **Control de Acceso**
- Autenticación JWT requerida para todos los endpoints
- Roles específicos para gestión de terceros
- Auditoría completa de cambios
- Protección de datos sensibles (GDPR compliance)

### **Logs de Auditoría**
```python
# Ejemplo de log de auditoría
{
    "action": "UPDATE_THIRD_PARTY",
    "user_id": "user_123",
    "third_party_id": "tp_456",
    "timestamp": "2024-12-11T10:30:00Z",
    "changes": {
        "phone": {"old": "+56911111111", "new": "+56922222222"},
        "credit_limit": {"old": 500000.00, "new": 750000.00}
    },
    "ip_address": "192.168.1.100"
}
```

## Configuración y Personalización

### **Parámetros Configurables**
```python
# Configuración del módulo de terceros
THIRD_PARTY_CONFIG = {
    "default_payment_terms": 30,  # días
    "default_credit_limit": 100000.00,
    "aging_buckets": [30, 60, 90, 120],  # días
    "auto_credit_check": True,
    "send_statements_email": True,
    "statement_format": "PDF",
    "currency": "CLP"
}

# Tipos de documento por país
DOCUMENT_TYPES_BY_COUNTRY = {
    "Chile": ["RUT", "Pasaporte", "CI"],
    "Argentina": ["CUIT", "CUIL", "DNI"],
    "Colombia": ["NIT", "CC", "CE"]
}
```

## Integraciones Externas

### **Sistemas de Facturación**
- Sincronización automática con sistemas de facturación
- Actualización de saldos en tiempo real
- Generación de documentos tributarios

### **Sistemas de CRM**
- Integración con sistemas de gestión de clientes
- Sincronización de datos comerciales
- Seguimiento de oportunidades de venta

### **Sistemas de Pago**
- Integración con pasarelas de pago
- Actualización automática de pagos recibidos
- Conciliación bancaria automática

## Troubleshooting

### **Problemas Comunes**

**1. Error de documento duplicado**
```
Error: "Ya existe un tercero con este documento"
Solución: Verificar que el documento no esté registrado o reactivar tercero existente
```

**2. Problemas de validación de documento**
```
Error: "Formato de documento inválido"
Solución: Verificar que el formato coincida con el país seleccionado
```

**3. Saldos inconsistentes**
```
Problema: Saldos no coinciden con movimientos contables
Solución: Ejecutar recálculo de saldos y verificar integridad de datos
```

## Próximas Mejoras

### **Roadmap de Funcionalidades**
- [ ] **Credit Scoring**: Evaluación automática de riesgo crediticio
- [ ] **Payment Predictions**: Machine learning para predicción de pagos
- [ ] **Mobile App**: Aplicación móvil para gestión de campo
- [ ] **API Integrations**: Conectores para sistemas populares
- [ ] **Advanced Analytics**: Dashboards ejecutivos y reportes avanzados

---

## Enlaces Relacionados

- [Sistema de Asientos Contables](../journal-entries/README.md)
- [Sistema de Centros de Costo](../cost-centers/README.md)
- [API Principal](../../README.md)

---
**Última actualización**: Diciembre 2024  
**Sprint**: 2 - Centros de Costo y Terceros  
**Estado**: ✅ Completado
