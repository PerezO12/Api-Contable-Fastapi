# Reportes de Rentabilidad y KPIs

El sistema de reportes de centros de costo proporciona análisis avanzado de rentabilidad, KPIs y métricas de rendimiento para facilitar la toma de decisiones gerenciales. Estos reportes se generan en tiempo real utilizando los datos de asientos contables asociados a cada centro de costo.

## Tipos de Reportes

### ✅ **Análisis de Rentabilidad**
- Cálculo automático de márgenes y ROI
- Desglose de ingresos y costos por categoría
- Comparación con períodos anteriores
- Proyecciones y tendencias

### ✅ **KPIs de Rendimiento**
- Métricas financieras automatizadas
- Indicadores de eficiencia operativa
- Alertas de rendimiento
- Benchmarking interno

### ✅ **Dashboard Ejecutivo**
- Vista consolidada de métricas clave
- Gráficos interactivos
- Alertas y notificaciones
- Datos en tiempo real

### ✅ **Análisis Comparativo**
- Comparación entre centros de costo
- Rankings de rendimiento
- Análisis de variaciones
- Identificación de mejores prácticas

## Métricas Calculadas

### **Métricas de Rentabilidad**

#### **1. Margen Bruto**
```python
margen_bruto = (ingresos - costo_directo) / ingresos * 100
```
- **Descripción**: Porcentaje de ganancia después de costos directos
- **Interpretación**: Eficiencia en la producción/prestación de servicios
- **Rango Óptimo**: Varía por industria (típicamente 20-60%)

#### **2. Margen Operativo**
```python
margen_operativo = (ingresos - costo_total) / ingresos * 100
```
- **Descripción**: Ganancia después de todos los costos operativos
- **Interpretación**: Eficiencia operativa general
- **Rango Óptimo**: Positivo, idealmente >10%

#### **3. ROI (Return on Investment)**
```python
roi = (utilidad_neta / inversion_total) * 100
```
- **Descripción**: Retorno sobre la inversión
- **Interpretación**: Eficiencia en el uso de recursos
- **Rango Óptimo**: >15% anual

#### **4. EBITDA**
```python
ebitda = utilidad_operativa + depreciacion + amortizacion
```
- **Descripción**: Ganancia antes de intereses, impuestos, depreciación y amortización
- **Interpretación**: Generación de efectivo operativo
- **Uso**: Comparación entre centros y períodos

### **Métricas de Eficiencia**

#### **1. Costo por Unidad Producida**
```python
costo_unitario = costo_total / unidades_producidas
```
- **Descripción**: Costo promedio por unidad
- **Interpretación**: Eficiencia en la producción
- **Objetivo**: Minimizar manteniendo calidad

#### **2. Productividad**
```python
productividad = ingresos / numero_empleados
```
- **Descripción**: Ingresos generados por empleado
- **Interpretación**: Eficiencia del recurso humano
- **Benchmark**: Comparar con promedios del sector

#### **3. Rotación de Activos**
```python
rotacion_activos = ingresos / activos_promedio
```
- **Descripción**: Eficiencia en el uso de activos
- **Interpretación**: Cuántos ingresos genera cada peso invertido
- **Objetivo**: Maximizar sin sacrificar capacidad

### **Métricas de Crecimiento**

#### **1. Crecimiento de Ingresos**
```python
crecimiento_ingresos = ((ingresos_actuales - ingresos_anteriores) / ingresos_anteriores) * 100
```
- **Descripción**: Tasa de crecimiento periodo a periodo
- **Interpretación**: Expansión del negocio
- **Benchmark**: Comparar con objetivos y mercado

#### **2. Variación de Costos**
```python
variacion_costos = ((costos_actuales - costos_anteriores) / costos_anteriores) * 100
```
- **Descripción**: Cambio en estructura de costos
- **Interpretación**: Control de gastos
- **Objetivo**: Mantener por debajo del crecimiento de ingresos

## Reportes Específicos

### **1. Reporte de Rentabilidad Detallado**

#### **Contenido**
- Ingresos por categoría y línea de negocio
- Costos directos e indirectos desglosados
- Cálculo de márgenes por nivel
- Comparación con períodos anteriores
- Análisis de variaciones

#### **Periodicidad**
- Mensual para análisis táctico
- Trimestral para revisión estratégica
- Anual para planificación

#### **Usuarios Objetivo**
- Gerentes de centros de costo
- Directores financieros
- Alta dirección

### **2. Dashboard de KPIs Ejecutivos**

#### **Métricas Principales**
- Ingresos del período
- Margen bruto y operativo
- ROI acumulado
- Ranking vs otros centros
- Tendencia trimestral

#### **Visualizaciones**
- Gráficos de tendencias
- Indicadores semafóricos
- Comparativos con metas
- Heat maps de rendimiento

#### **Alertas Automáticas**
- Márgen por debajo del mínimo
- Costos que superan presupuesto
- Tendencias negativas sostenidas
- Oportunidades de mejora

### **3. Análisis Comparativo de Centros**

#### **Métricas de Comparación**
- Rentabilidad relativa
- Eficiencia operativa
- Crecimiento sostenido
- Consistencia en resultados

#### **Rankings Automáticos**
- Por rentabilidad
- Por eficiencia
- Por crecimiento
- Por estabilidad

#### **Identificación de Buenas Prácticas**
- Centros de mejor rendimiento
- Factores de éxito identificados
- Recomendaciones de transferencia
- Planes de mejora sugeridos

## Configuración de Reportes

### **Parámetros Configurables**

#### **1. Períodos de Análisis**
- Rango de fechas personalizable
- Comparación con período anterior
- Análisis de tendencias históricas
- Proyecciones futuras

#### **2. Agrupaciones**
- Por centro de costo individual
- Por rama jerárquica
- Por categoría de negocio
- Por ubicación geográfica

#### **3. Métricas Incluidas**
- Selección de KPIs relevantes
- Ponderación de métricas
- Umbrales de alerta
- Metas y objetivos

### **Automatización**
- Generación programada
- Envío automático por email
- Notificaciones de alertas
- Actualización en tiempo real

## Casos de Uso Prácticos

### **Caso 1: Análisis de Rentabilidad Mensual**
```
Objetivo: Evaluar rendimiento mensual de centros de costo
Métricas: Margen bruto, margen operativo, ROI
Comparación: vs mes anterior, vs mismo mes año anterior
Salida: Dashboard ejecutivo + reporte detallado
```

### **Caso 2: Identificación de Centros Problemáticos**
```
Objetivo: Detectar centros con bajo rendimiento
Métricas: Todas las métricas vs benchmarks
Alertas: Automáticas cuando métricas están fuera de rango
Acción: Plan de mejora automático generado
```

### **Caso 3: Planificación Presupuestaria**
```
Objetivo: Establecer metas para siguiente período
Datos: Tendencias históricas + proyecciones
Análisis: Capacidad vs demanda proyectada
Salida: Recomendaciones presupuestarias
```

### **Caso 4: Benchmarking Interno**
```
Objetivo: Comparar rendimiento entre centros similares
Agrupación: Por tipo de negocio o tamaño
Métricas: Eficiencia y rentabilidad normalizada
Resultado: Best practices identificadas
```

## API de Reportes

### **Endpoints Principales**

#### **Reporte de Rentabilidad**
```http
GET /api/v1/cost-center-reports/{id}/profitability
Parameters:
  - start_date: fecha inicio
  - end_date: fecha fin
  - comparison_period: incluir comparación
  - include_breakdown: desglose detallado
```

#### **Dashboard Ejecutivo**
```http
GET /api/v1/cost-center-reports/executive-dashboard
Parameters:
  - cost_center_ids: lista de centros
  - period: período de análisis
  - metrics: métricas a incluir
```

#### **Análisis Comparativo**
```http
GET /api/v1/cost-center-reports/comparison
Parameters:
  - cost_center_ids: centros a comparar
  - metrics: métricas de comparación
  - ranking_criteria: criterio de ranking
```

#### **Seguimiento Presupuestario**
```http
GET /api/v1/cost-center-reports/{id}/budget-tracking
Parameters:
  - budget_year: año presupuestario
  - include_variance: incluir análisis de variaciones
  - alert_threshold: umbral de alertas
```

### **Formatos de Exportación**
- **JSON**: Para integración con sistemas
- **PDF**: Para presentaciones ejecutivas
- **Excel**: Para análisis detallado
- **CSV**: Para procesamiento adicional

## Interpretación de Resultados

### **Rangos de Interpretación**

#### **Margen Bruto**
- **Excelente**: >50%
- **Bueno**: 30-50%
- **Aceptable**: 15-30%
- **Problemático**: <15%

#### **ROI Anual**
- **Excelente**: >25%
- **Bueno**: 15-25%
- **Aceptable**: 8-15%
- **Problemático**: <8%

#### **Crecimiento de Ingresos**
- **Excelente**: >20% anual
- **Bueno**: 10-20% anual
- **Estable**: 0-10% anual
- **Problemático**: <0% anual

### **Alertas Automáticas**
- **Crítica**: Métricas por debajo del 80% del objetivo
- **Advertencia**: Métricas entre 80-90% del objetivo
- **Información**: Tendencias negativas detectadas
- **Oportunidad**: Rendimiento superior al benchmark

## Mejores Prácticas

### **Para Administradores**
1. **Configurar alertas apropiadas** para cada tipo de centro
2. **Revisar métricas regularmente** para detectar tendencias
3. **Establecer benchmarks realistas** basados en datos históricos
4. **Usar comparaciones** para identificar mejores prácticas

### **Para Analistas**
1. **Analizar variaciones** para entender causas raíz
2. **Correlacionar métricas** para obtener insights profundos
3. **Usar períodos apropiados** para cada tipo de análisis
4. **Documentar hallazgos** para seguimiento futuro

### **Para Gerentes**
1. **Enfocarse en métricas clave** para su centro específico
2. **Entender el contexto** de las comparaciones
3. **Actuar sobre alertas** de manera oportuna
4. **Usar insights** para mejorar operaciones

---

*Documentación de reportes de rentabilidad y KPIs - Sprint 2*
