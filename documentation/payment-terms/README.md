# Índice de Documentación - Módulo de Condiciones de Pago

Este directorio contiene la documentación completa del módulo de Condiciones de Pago (Payment Terms) del API Contable.

## 📚 Documentos Disponibles

### 📝 [payment-terms-management.md](./payment-terms-management.md)
**Gestión de Condiciones de Pago**
- Descripción general del sistema de condiciones de pago
- Modelo de datos y estructura
- CRUD completo de condiciones de pago
- Cronogramas de pago múltiples
- Validaciones de negocio
- Integración con asientos contables
- Cálculos automáticos de fechas de vencimiento

### 🗓️ [payment-schedules.md](./payment-schedules.md)
**Cronogramas de Pago**
- Gestión de cronogramas de pago múltiples
- Cálculo de fechas de vencimiento
- Distribución de porcentajes
- Validaciones de cronogramas
- Ejemplos de configuración

### 🔗 [journal-entry-integration.md](./journal-entry-integration.md)
**Integración con Asientos Contables**
- Nuevos campos en líneas de asiento
- Fechas de factura independientes
- Fechas de vencimiento automáticas y manuales
- Propiedades calculadas
- Casos de uso prácticos

### ⚡ [api-endpoints.md](./api-endpoints.md)
**Endpoints del API**
- Listado completo de endpoints disponibles
- Ejemplos de requests y responses
- Validaciones y errores
- Casos de uso específicos
- Filtros y búsquedas

### 📊 [examples-and-use-cases.md](./examples-and-use-cases.md)
**Ejemplos y Casos de Uso**
- Condiciones de pago comunes
- Escenarios de facturación
- Cronogramas de pago típicos
- Integración práctica con asientos
- Casos de prueba

## 🎯 Funcionalidades Principales

### ✅ Gestión de Condiciones de Pago
- Creación y mantenimiento de condiciones de pago
- Códigos únicos y nombres descriptivos
- Estados activo/inactivo
- Validaciones de integridad

### ✅ Cronogramas de Pago Múltiples
- Soporte para pagos fraccionados
- Diferentes días de vencimiento
- Porcentajes personalizables
- Validación automática (suma 100%)

### ✅ Integración con Asientos Contables
- Fechas de factura independientes
- Cálculo automático de vencimientos
- Fechas manuales opcionales
- Cronogramas detallados por línea

### ✅ APIs Completas
- CRUD completo de condiciones de pago
- Búsquedas y filtros avanzados
- Cálculo de cronogramas
- Validaciones en tiempo real

## 🔧 Arquitectura Técnica

### Tablas Principales
- `payment_terms`: Condiciones de pago principales
- `payment_schedules`: Cronogramas de pago detallados
- `journal_entry_lines`: Líneas de asiento con campos de pago

### Modelos SQLAlchemy
- `PaymentTerms`: Condiciones de pago
- `PaymentSchedule`: Cronogramas individuales
- `JournalEntryLine`: Líneas de asiento actualizadas

### Servicios
- `PaymentTermsService`: Lógica de negocio principal
- Integración con `JournalEntryService`

## 📈 Estado de Implementación

- ✅ Modelos de datos completados
- ✅ Migración de base de datos
- ✅ APIs REST implementadas
- ✅ Servicios de negocio
- ✅ Validaciones y pruebas
- ✅ Integración con asientos contables
- ✅ Documentación técnica

## 🚀 Próximos Pasos

- Implementación de reportes de vencimientos
- Alertas automáticas de pagos próximos
- Integración con módulo de cuentas por cobrar/pagar
- Dashboard de seguimiento de pagos
