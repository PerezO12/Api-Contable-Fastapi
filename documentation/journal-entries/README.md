# Índice de Documentación - Módulo de Asientos Contables

Este directorio contiene la documentación completa del módulo de Asientos Contables (Journal Entries) del API Contable.

## 📚 Documentos Disponibles

### 📝 [journal-entry-management.md](./journal-entry-management.md)
**Gestión de Asientos Contables**
- Descripción general del sistema de asientos contables
- Modelo de datos y estructura
- CRUD completo de asientos contables
- Validaciones de negocio
- Ciclo de vida de los asientos
- Manejo de estados (borrador, aprobado, contabilizado, cancelado)
- Integración con el sistema contable

### 🔄 [journal-entry-types.md](./journal-entry-types.md)
**Tipos de Asientos Contables**
- Tipos fundamentales (MANUAL, AUTOMÁTICO, AJUSTE, etc.)
- Estados de los asientos contables
- Propiedades específicas según tipo
- Reglas para cada tipo de asiento
- Validaciones específicas por tipo
- Ciclo de vida según tipo de asiento
- Casos de uso específicos

### 🔗 [journal-entry-integration.md](./journal-entry-integration.md)
**Integración con Centros de Costo y Terceros - Sprint 2**
- Cambios en el modelo de datos para soporte de terceros y centros de costo
- Validaciones mejoradas con entidades relacionadas
- Nuevos endpoints para reportes integrados
- Casos de uso con distribución por centros de costo
- Estados de cuenta por tercero
- Análisis multidimensional y reportes cruzados
- Mejores prácticas para asignación de terceros y centros

### 📊 [journal-entry-operations.md](./journal-entry-operations.md)
**Operaciones de Asientos Contables**
- Creación y validación de asientos
- Aprobación de asientos
- Contabilización y efecto en cuentas
- Reversión de asientos
- Cancelación de asientos
- Importación y exportación
- Operaciones masivas
- Control de balance (partida doble)

### 🌐 [journal-entry-endpoints.md](./journal-entry-endpoints.md)
**Endpoints de Asientos Contables**
- Detalle completo de todos los endpoints
- Parámetros y formatos de solicitud
- Ejemplos de respuestas
- Códigos de estado y errores
- Permisos requeridos
- Casos de uso y ejemplos
- Integración con frontend

## 🔄 Integración con Otros Módulos

El sistema de asientos contables se integra estrechamente con:

- **Cuentas Contables**: Para afectar saldos y registrar movimientos
- **Reportes Financieros**: Para generación de libro diario, balance general, etc.
- **Sistema de Usuarios**: Para permisos, aprobaciones y auditoría
- **Importación/Exportación**: Para manejo masivo de asientos contables
