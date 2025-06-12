# Sistema de Centros de Costo

El módulo de Centros de Costo es una funcionalidad avanzada del sistema contable que permite la gestión y análisis de la rentabilidad por unidades organizacionales, proyectos o departamentos. Implementado en el Sprint 2, ofrece capacidades completas de seguimiento, análisis y reporte de costos.

## Índice de Documentación

### Documentos Principales
- [Gestión de Centros de Costo](./cost-center-management.md) - CRUD y administración básica
- [Estructura Jerárquica](./cost-center-hierarchy.md) - Sistema jerárquico y validaciones
- [Reportes de Rentabilidad](./cost-center-reports.md) - Análisis de rentabilidad y KPIs
- [Análisis Comparativo](./cost-center-analysis.md) - Comparaciones y benchmarking
- [Endpoints de Centros de Costo](./cost-center-endpoints.md) - Documentación completa de APIs

## Características Principales

### ✅ **Gestión Jerárquica**
- Estructura de árbol multinivel
- Códigos automáticos con jerarquía
- Validaciones de integridad
- Propagación de cambios

### ✅ **Análisis de Rentabilidad**
- Cálculo automático de métricas financieras
- Análisis de márgenes y eficiencia
- Comparación con períodos anteriores
- Desglose de ingresos y costos

### ✅ **Reportes Ejecutivos**
- KPIs de rendimiento
- Dashboard ejecutivo
- Rankings por métricas
- Alertas automáticas

### ✅ **Seguimiento Presupuestario**
- Comparación vs presupuesto
- Análisis de variaciones
- Proyecciones y forecasting
- Recomendaciones automáticas

## Arquitectura del Módulo

```
app/
├── models/
│   └── cost_center.py           # Modelo de datos principal
├── schemas/
│   └── cost_center.py           # Esquemas Pydantic y validaciones
├── services/
│   ├── cost_center_service.py           # Lógica de negocio CRUD
│   └── cost_center_reporting_service.py # Servicios de reportes
└── api/v1/
    ├── cost_centers.py          # Endpoints CRUD y consultas
    └── cost_center_reports.py   # Endpoints de reportes avanzados
```

## Integración con el Sistema

### **Conexión con Asientos Contables**
Los centros de costo se integran directamente con el sistema de asientos contables:

```python
# En JournalEntryLine
cost_center_id: Optional[UUID] = mapped_column(ForeignKey("cost_centers.id"))
cost_center: Optional["CostCenter"] = relationship("CostCenter")
```

### **Análisis Automático**
- Cálculo automático de rentabilidad basado en movimientos contables
- Clasificación de ingresos y gastos por centro de costo
- Generación de reportes en tiempo real

## Casos de Uso Principales

### 1. **Gestión Departamental**
```python
# Ejemplo: Estructura por departamentos
Empresa (Nivel 0)
├── Ventas (Nivel 1) - CC001
│   ├── Ventas Norte (Nivel 2) - CC001.001
│   └── Ventas Sur (Nivel 2) - CC001.002
└── Operaciones (Nivel 1) - CC002
    ├── Producción (Nivel 2) - CC002.001
    └── Logística (Nivel 2) - CC002.002
```

### 2. **Análisis de Proyectos**
```python
# Ejemplo: Seguimiento de rentabilidad por proyecto
Proyecto A - Rentabilidad: 15.2%
├── Ingresos: $150,000
├── Costos Directos: $90,000
├── Costos Indirectos: $37,500
└── Utilidad Neta: $22,500
```

### 3. **Control Presupuestario**
```python
# Ejemplo: Variaciones presupuestarias
Centro de Costo: Marketing Digital
├── Presupuesto: $50,000
├── Real: $48,500
├── Variación: -$1,500 (3% favorable)
└── Status: ✅ Dentro del presupuesto
```

## APIs Disponibles

### **Endpoints CRUD** (`/api/v1/cost-centers`)
- `GET /` - Listar centros de costo con filtros
- `POST /` - Crear nuevo centro de costo
- `GET /{id}` - Obtener centro específico
- `PUT /{id}` - Actualizar centro de costo
- `DELETE /{id}` - Eliminar centro de costo

### **Endpoints de Consulta** (`/api/v1/cost-centers`)
- `GET /hierarchy` - Vista jerárquica completa
- `GET /search` - Búsqueda avanzada
- `GET /{id}/children` - Obtener centros hijos
- `GET /{id}/movements` - Movimientos contables

### **Endpoints de Reportes** (`/api/v1/cost-center-reports`)
- `GET /{id}/profitability` - Análisis de rentabilidad
- `GET /comparison` - Comparación entre centros
- `GET /{id}/budget-tracking` - Seguimiento presupuestario
- `GET /ranking` - Ranking por métricas
- `GET /executive-dashboard` - Dashboard ejecutivo

## Métricas y KPIs

### **Métricas Financieras**
- **Ingresos Totales**: Suma de todos los ingresos asignados
- **Costos Directos**: Costos directamente atribuibles
- **Costos Indirectos**: Costos distribuidos según reglas
- **Utilidad Bruta**: Ingresos - Costos Directos
- **Utilidad Neta**: Ingresos - Costos Totales

### **Indicadores de Eficiencia**
- **Margen Bruto**: (Utilidad Bruta / Ingresos) × 100
- **Margen Neto**: (Utilidad Neta / Ingresos) × 100
- **Eficiencia de Costos**: Ingresos / Costos Totales
- **ROI**: (Utilidad Neta / Inversión) × 100

### **Clasificación de Rendimiento**
- **Excelente**: Margen neto ≥ 20%
- **Bueno**: Margen neto ≥ 15%
- **Promedio**: Margen neto ≥ 10%
- **Bajo**: Margen neto < 10%

## Seguridad y Validaciones

### **Validaciones de Integridad**
- Códigos únicos por nivel jerárquico
- Prevención de referencias circulares
- Validación de estados activo/inactivo
- Control de eliminación con dependencias

### **Seguridad de Acceso**
- Autenticación JWT requerida
- Control de permisos por rol
- Auditoría de cambios
- Protección de datos sensibles

## Configuración y Personalización

### **Parámetros Configurables**
```python
# Configuración de costos indirectos
INDIRECT_COST_PERCENTAGE = 15  # Por defecto 15%

# Umbrales de rendimiento
PERFORMANCE_THRESHOLDS = {
    'excellent': 20,
    'good': 15,
    'average': 10,
    'poor': 5
}

# Configuración de reportes
DEFAULT_REPORT_PERIOD = 'current_month'
MAX_COMPARISON_ITEMS = 10
```

## Troubleshooting

### **Problemas Comunes**

**1. Error de código duplicado**
```
Error: "Código de centro de costo ya existe"
Solución: Verificar unicidad en el nivel jerárquico correspondiente
```

**2. Referencias circulares**
```
Error: "No se puede asignar como padre - crearía referencia circular"
Solución: Verificar la estructura jerárquica antes de asignar padres
```

**3. Cálculos incorrectos**
```
Problema: Métricas no coinciden con expectativas
Solución: Verificar asignación correcta de movimientos contables
```

## Próximas Mejoras

### **Roadmap de Funcionalidades**
- [ ] **Budget Management**: Sistema completo de presupuestos
- [ ] **Cost Allocation**: Reglas avanzadas de distribución de costos
- [ ] **Performance Analytics**: Machine learning para predicciones
- [ ] **Mobile Dashboard**: Dashboard móvil para ejecutivos
- [ ] **Integration APIs**: APIs para sistemas externos

---

## Enlaces Relacionados

- [Sistema de Asientos Contables](../journal-entries/README.md)
- [Sistema de Terceros](../third-parties/README.md)
- [API Principal](../../README.md)

---
**Última actualización**: Diciembre 2024  
**Sprint**: 2 - Centros de Costo y Terceros  
**Estado**: ✅ Completado
