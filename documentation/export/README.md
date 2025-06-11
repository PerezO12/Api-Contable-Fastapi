# Sistema de Exportación de Datos

## Índice del Módulo de Exportación

Este módulo proporciona capacidades avanzadas de exportación de datos para todas las tablas del sistema contable con múltiples formatos de salida y filtrado de datos sensibles.

### Documentación Disponible

#### Documentación Principal
- [**Sistema de Exportación Genérica**](./export-system.md) - Arquitectura y funcionalidades principales
- [**Servicio de Exportación**](./export-service.md) - Documentación técnica del servicio
- [**API de Exportación**](./export-endpoints.md) - Endpoints y especificaciones de la API
- [**Esquemas de Datos**](./export-schemas.md) - Modelos y validaciones de datos

#### Guías de Implementación
- [**Guía de Uso**](./export-usage.md) - Cómo usar el sistema de exportación
- [**Seguridad y Filtros**](./export-security.md) - Manejo de datos sensibles
- [**Formatos de Exportación**](./export-formats.md) - Detalles de formatos soportados

#### Referencias Técnicas
- [**Configuración**](./export-configuration.md) - Configuración y personalización
- [**Ejemplos de Código**](./export-examples.md) - Ejemplos prácticos de implementación

## Características Principales

### 🔄 Exportación Flexible
- **Múltiples tablas**: Soporte para todas las tablas del sistema
- **Formatos variados**: CSV, JSON, XLSX
- **Filtrado avanzado**: Por IDs, fechas, estado activo y filtros personalizados

### 🔒 Seguridad Integrada
- **Filtrado de datos sensibles**: Omisión automática de campos confidenciales
- **Control de acceso**: Validación de permisos por usuario
- **Auditoría**: Registro de todas las exportaciones realizadas

### ⚡ Rendimiento Optimizado
- **Consultas eficientes**: Uso de filtros para reducir carga de datos
- **Generación en memoria**: Procesamiento optimizado de archivos
- **Metadatos detallados**: Información completa de cada exportación

### 🎯 Funcionalidades Avanzadas
- **API simplificada**: Endpoints intuitivos y fáciles de usar
- **Exportación por lotes**: Selección específica de registros por ID
- **Información de esquemas**: Consulta de estructura de tablas disponibles

## Tablas Soportadas

| Tabla | Nombre de Esquema | Descripción |
|-------|------------------|-------------|
| `users` | Usuarios | Gestión de usuarios del sistema |
| `accounts` | Plan de Cuentas | Cuentas contables |
| `journal_entries` | Asientos Contables | Asientos del diario |
| `journal_entry_lines` | Líneas de Asientos | Líneas de detalle de asientos |
| `audit_logs` | Logs de Auditoría | Registro de auditoría |
| `user_sessions` | Sesiones de Usuario | Sesiones activas |
| `change_tracking` | Tracking de Cambios | Seguimiento de modificaciones |
| `system_configuration` | Configuración del Sistema | Configuraciones |
| `company_info` | Información de la Empresa | Datos de la empresa |
| `number_sequences` | Secuencias de Numeración | Secuencias automáticas |

## Formatos de Exportación

### CSV (Comma-Separated Values)
- Ideal para importación en hojas de cálculo
- Compatible con Excel y otras herramientas
- Encoding UTF-8 con encabezados

### JSON (JavaScript Object Notation)
- Formato estructurado para APIs
- Ideal para integraciones
- Soporte para tipos de datos complejos

### XLSX (Excel)
- Formato nativo de Microsoft Excel
- Formateado automático
- Compatible con Office 365

## Arquitectura del Sistema

```
app/
├── schemas/
│   └── export_generic.py    # Esquemas de exportación
├── services/
│   └── export_service.py    # Servicio principal de exportación
├── api/v1/
│   └── export.py           # Endpoints de la API
└── models/
    └── [all_models].py     # Modelos de datos soportados
```

## Flujo de Exportación

```
1. Solicitud → Validación de parámetros
2. Autenticación → Verificación de permisos
3. Consulta → Aplicación de filtros
4. Procesamiento → Filtrado de datos sensibles
5. Generación → Creación del archivo
6. Respuesta → Entrega del archivo + metadatos
```

## Casos de Uso Comunes

### Exportación Simple
```bash
POST /api/v1/export/
{
  "table": "users",
  "format": "csv",
  "ids": [1, 2, 3]
}
```

### Exportación Avanzada
```bash
POST /api/v1/export/advanced
{
  "table_name": "journal_entries",
  "export_format": "xlsx",
  "filters": {
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "active_only": true
  }
}
```

### Consulta de Esquemas
```bash
GET /api/v1/export/tables/users
```

## Consideraciones de Seguridad

- **Datos sensibles**: Automáticamente filtrados según la tabla
- **Autenticación requerida**: Todos los endpoints requieren autenticación
- **Auditoría completa**: Registro de todas las exportaciones
- **Validación de entrada**: Validación estricta de parámetros

## Próximos Pasos

1. Consultar la [documentación del servicio](./export-service.md) para detalles técnicos
2. Revisar los [endpoints disponibles](./export-endpoints.md) para implementación
3. Explorar los [ejemplos de código](./export-examples.md) para casos prácticos
