# 📊 Sistema de Reportes Financieros

## Descripción General

El sistema de reportes financieros del API Contable proporciona una solución completa y profesional para la generación de reportes contables fundamentales. Está diseñado siguiendo principios contables internacionales y mejores prácticas de desarrollo, ofreciendo dos APIs especializadas:

1. **API de Reportes Clásicos** (`/api/v1/reports`) - Reportes tradicionales con esquemas estructurados
2. **API de Reportes Unificados** (`/api/v1/reports`) - API moderna con formato tabular unificado

## Características Principales

### 🏗️ **Arquitectura Robusta**
- **Servicios Separados**: Lógica de negocio separada en `ReportService`
- **Validaciones Contables**: Verificación automática de ecuaciones fundamentales
- **Manejo de Errores**: Sistema robusto de captura y manejo de excepciones
- **Cacheo Inteligente**: Optimización de consultas para mejor rendimiento

### 📈 **Reportes Fundamentales**
- **Balance General**: Estado de situación financiera
- **Estado de Resultados**: Análisis de pérdidas y ganancias
- **Balance de Comprobación**: Verificación de integridad contable
- **Libro Mayor**: Detalle de movimientos por cuenta
- **Análisis Financiero**: Ratios y indicadores clave

### 🔧 **Funcionalidades Avanzadas**
- **Filtros Flexibles**: Por fecha, tipo de cuenta, cuentas específicas
- **Niveles de Detalle**: Configurables según necesidades
- **Exportación**: Soporte para múltiples formatos (PDF, Excel, CSV)
- **Validación de Integridad**: Verificación automática de ecuaciones contables
- **Narrativa Automática**: Generación de análisis y recomendaciones

## Principios Contables Implementados

### Ecuación Fundamental del Balance
```
Activos = Pasivos + Patrimonio
```

### Balance de Comprobación
```
Σ Débitos = Σ Créditos
```

### Estado de Resultados
```
Utilidad Neta = Ingresos - Gastos
```

## Arquitectura del Sistema

```
📁 Sistema de Reportes
├── 📄 ReportService          # Servicio principal de lógica de negocio
├── 📄 ReportAPIService       # Adaptador para API unificada
├── 🌐 Reports Router         # Endpoints clásicos
├── 🌐 Report API Router      # Endpoints unificados
├── 📊 Schemas Clásicos       # Estructuras tradicionales
├── 📊 Schemas API            # Formato tabular unificado
└── 🔧 Utilidades            # Validadores y helpers
```

## Casos de Uso Principales

### 📋 **Para Contadores**
- Generación de estados financieros mensuales
- Verificación de integridad contable
- Análisis de ratios financieros
- Preparación de reportes regulatorios

### 👥 **Para Gerencia**
- Dashboards ejecutivos
- Análisis de rentabilidad
- Seguimiento de KPIs financieros
- Reportes de situación financiera

### 🔍 **Para Auditores**
- Verificación de balances
- Análisis de movimientos contables
- Validación de integridad de datos
- Reportes de cumplimiento

## Tecnologías Utilizadas

- **FastAPI**: Framework web moderno
- **SQLAlchemy**: ORM para base de datos
- **Pydantic**: Validación de datos
- **Decimal**: Precisión contable garantizada
- **AsyncIO**: Procesamiento asíncrono
- **PostgreSQL**: Base de datos empresarial

## Estructura de Documentación

- [🔗 **Endpoints de Reportes Clásicos**](./classic-reports-endpoints.md)
- [🔗 **Endpoints de API Unificada**](./unified-reports-api.md)
- [🔗 **Esquemas y Modelos**](./schemas-reference.md)
- [🔗 **Casos de Uso y Ejemplos**](./use-cases-examples.md)
- [🔗 **Configuración y Administración**](./configuration-admin.md)

## Cumplimiento y Estándares

### ✅ **Estándares Contables**
- NIIF (Normas Internacionales de Información Financiera)
- Principios de Contabilidad Generalmente Aceptados
- Ecuaciones contables fundamentales

### ✅ **Estándares Técnicos**
- REST API Guidelines
- OpenAPI 3.0 Specification
- Async/Await Patterns
- Error Handling Best Practices

## Próximas Funcionalidades

- 📊 **Reportes Personalizados**: Constructor de reportes dinámicos
- 📈 **Dashboards Interactivos**: Visualizaciones en tiempo real
- 🔄 **Sincronización**: Integración con sistemas externos
- 🤖 **IA Financiera**: Análisis predictivo y recomendaciones automáticas
