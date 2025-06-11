# Documentación del Sistema Contable

Este directorio contiene toda la documentación técnica del sistema contable, organizada por módulos y funcionalidades.

## Estructura de la Documentación

### Sistema de Usuario y Autenticación
- [Autenticación y Seguridad](./auth/authentication.md) - Sistema completo de autenticación
- [Gestión de Usuarios](./auth/user-management.md) - CRUD y administración de usuarios
- [Roles y Permisos](./auth/roles-permissions.md) - Sistema de roles y control de acceso
- [Sesiones y Tokens](./auth/sessions-tokens.md) - Gestión de sesiones JWT
- [Endpoints de Autenticación](./auth/auth-endpoints.md) - API de autenticación
- [Endpoints de Usuarios](./auth/user-endpoints.md) - API de gestión de usuarios

### Sistema de Cuentas Contables
- [Plan de Cuentas](./accounts/README.md) - Índice del módulo de cuentas
- [Gestión de Cuentas](./accounts/account-management.md) - CRUD y administración de cuentas
- [Tipos de Cuentas](./accounts/account-types.md) - Tipos y categorías de cuentas
- [Estructura del Plan](./accounts/chart-of-accounts.md) - Estructura jerárquica de cuentas
- [Movimientos](./accounts/account-movements.md) - Gestión de movimientos y saldos
- [Endpoints de Cuentas](./accounts/account-endpoints.md) - API de gestión de cuentas

### Sistema de Asientos Contables
- [Índice de Asientos Contables](./journal-entries/README.md) - Índice del módulo de asientos contables
- [Gestión de Asientos](./journal-entries/journal-entry-management.md) - Modelo y estructura de asientos
- [Tipos de Asientos](./journal-entries/journal-entry-types.md) - Tipos y estados de asientos
- [Operaciones de Asientos](./journal-entries/journal-entry-operations.md) - Operaciones y lógica de asientos
- [Endpoints de Asientos](./journal-entries/journal-entry-endpoints.md) - API de gestión de asientos

### Sistema de Importación de Datos
- [Índice de Importación](./data-import/README.md) - Visión general del sistema de importación
- [Estructuras de Datos](./data-import/import-data-structures.md) - Modelos y esquemas para importación
- [Procesos de Importación](./data-import/import-processes.md) - Flujos de trabajo y procesos
- [Plantillas y Formatos](./data-import/import-templates.md) - Plantillas y formatos soportados
- [Exportación de Plantillas](./data-import/export-templates.md) - Funcionalidades de exportación de ejemplos y plantillas
- [API de Importación](./data-import/import-api-endpoints.md) - Endpoints para importación

### Sistema de Exportación de Datos
- [Índice de Exportación](./export/README.md) - Visión general del sistema de exportación
- [Servicio de Exportación](./export/export-service.md) - Documentación técnica del servicio principal
- [API de Exportación](./export/export-endpoints.md) - Endpoints y especificaciones de la API
- [Esquemas de Datos](./export/export-schemas.md) - Modelos y validaciones de datos
- [Seguridad y Filtros](./export/export-security.md) - Manejo de datos sensibles y protección

### Otros Módulos (Para futuras expansiones)
- [Reportes](./reports/) - Sistema de reportes financieros
- [Auditoría](./audit/) - Sistema de auditoría y logs

## Convenciones de Documentación

### Formato
- Todos los archivos están en formato Markdown (.md)
- Uso de títulos jerárquicos (H1, H2, H3...)
- Ejemplos de código con sintaxis destacada
- Enlaces entre documentos relacionados

### Estructura de Cada Documento
1. **Descripción General** - Qué hace el módulo
2. **Características Principales** - Funcionalidades clave
3. **Arquitectura** - Cómo está organizado el código
4. **Schemas/Modelos** - Estructuras de datos
5. **Servicios** - Lógica de negocio
6. **Endpoints** - APIs disponibles
7. **Ejemplos de Uso** - Casos prácticos
8. **Configuración** - Parámetros y settings
9. **Seguridad** - Consideraciones de seguridad
10. **Troubleshooting** - Problemas comunes

## Tecnologías Documentadas

- **FastAPI** - Framework web principal
- **SQLAlchemy 2.0** - ORM y gestión de base de datos
- **PostgreSQL** - Base de datos
- **JWT** - Tokens de autenticación
- **bcrypt** - Hashing de contraseñas
- **Pydantic** - Validación y serialización
- **Alembic** - Migraciones de base de datos

## Cómo Contribuir

1. Mantener la estructura establecida
2. Incluir ejemplos prácticos
3. Documentar cambios en la API
4. Actualizar diagramas cuando sea necesario
5. Revisar enlaces y referencias cruzadas

## Últimas Actualizaciones

- **Junio 2025** - Documentación inicial del sistema de autenticación
  - Sistema de usuarios y roles completamente funcional
  - Endpoints de autenticación documentados
  - Ejemplos de integración incluidos
- **Junio 2025** - Documentación completa del módulo de asientos contables
  - Modelos, tipos y estados de asientos documentados
  - Operaciones de asientos (creación, aprobación, contabilización, cancelación, reversión)
  - Endpoints de API e integración con otros módulos
- **Junio 2025** - Documentación del sistema de importación de datos
  - Procesos de importación para cuentas y asientos contables
  - Plantillas de importación en CSV, XLSX y JSON
  - API para importación, validación y gestión de datos
  - Funcionalidad de exportación de plantillas y ejemplos
