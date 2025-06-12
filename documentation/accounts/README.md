# Índice de Documentación - Módulo de Cuentas Contables

Este directorio contiene la documentación completa del módulo de Cuentas Contables del API Contable.

## 📚 Documentos Disponibles

### 🏦 [account-management.md](./account-management.md)
**Gestión de Cuentas Contables**
- Descripción general del sistema de cuentas
- Modelo de datos y estructura
- CRUD completo de cuentas
- Validaciones de negocio
- Relaciones entre cuentas
- Manejo de saldos
- **Categorías de flujo de efectivo**
- Integración con el sistema contable

### 📊 [account-types.md](./account-types.md)
**Tipos y Categorías de Cuentas**
- Tipos fundamentales (ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS)
- Categorías por tipo de cuenta
- **Categorías de flujo de efectivo (OPERATING, INVESTING, FINANCING, CASH_EQUIVALENTS)**
- Propiedades específicas según tipo
- Reglas de balance y movimientos
- Comportamiento normal del saldo
- Validaciones específicas por tipo
- Estructura jerárquica

### 📈 [chart-of-accounts.md](./chart-of-accounts.md)
**Plan de Cuentas**
- Estructura jerárquica de cuentas
- Representación en árbol
- Códigos y nomenclatura
- Importación y exportación
- Consulta de estructura
- **Configuración para flujo de efectivo**
- **Categorización automática de cuentas**
- Manejo de saldos consolidados
- Reportes por tipo de cuenta

### 📝 [account-movements.md](./account-movements.md)
**Movimientos de Cuentas**
- Registro de movimientos contables
- Cálculo de saldos y balances
- Historial de movimientos
- Validaciones de integridad
- Consulta de movimientos por período
- Relación con asientos contables
- Reportes de cuenta

### 🌐 [account-endpoints.md](./account-endpoints.md)
**Endpoints de Cuentas**
- Detalle completo de todos los endpoints
- Parámetros y formatos de solicitud
- **Filtros por categoría de flujo de efectivo**
- **Endpoint de categorización automática**
- **Nuevos endpoints de eliminación múltiple**
- **Validación previa de eliminaciones**
- Ejemplos de respuestas
- Códigos de estado y errores
- Permisos requeridos
- Casos de uso y ejemplos
- Integración con frontend

### 🗑️ [bulk-account-deletion.md](./bulk-account-deletion.md) **[NUEVO]**
**Eliminación Múltiple de Cuentas**
- Sistema avanzado de eliminación masiva
- Validaciones exhaustivas y controles de seguridad
- Endpoints `/bulk-delete` y `/validate-deletion`
- Parámetros de control (`force_delete`, `delete_reason`)
- Casos de uso: limpieza, migración, correcciones
- Flujos de trabajo recomendados
- Manejo de errores y recuperación
- Mejores prácticas de seguridad y auditoría

### 🧪 [bulk-deletion-tests.md](./bulk-deletion-tests.md) **[NUEVO]**
**Tests para Eliminación Múltiple**
- Casos de prueba completos
- Tests de validación y eliminación
- Manejo de errores y límites
- Tests de performance e integración
- Utilidades de testing y fixtures
- Checklist de testing completo

## 🔄 Integración con Otros Módulos

El sistema de cuentas contables se integra estrechamente con:

- **Asientos Contables**: Para registro de movimientos
- **Reportes Financieros**: Balance general, estado de resultados, etc.
- **Sistema de Usuarios**: Para permisos y auditoría
- **Importación/Exportación**: Para manejo masivo de cuentas
