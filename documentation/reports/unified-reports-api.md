# 🔄 API de Reportes Unificados

## Descripción General

La API de Reportes Unificados proporciona una interfaz moderna y consistente para generar reportes financieros con formato tabular estandarizado. Esta API está diseñada para aplicaciones modernas que requieren flexibilidad y consistencia en el formato de respuesta, incluyendo narrativa automática y análisis inteligente.

## Base URL

```
Base URL: /api/v1/reports
```

## Características Principales

### 🎯 **Formato Unificado**
- Respuesta consistente para todos los tipos de reporte
- Formato tabular estandarizado
- Narrativa automática con análisis y recomendaciones
- Metadatos completos de generación

### 🧠 **Inteligencia Incorporada**
- Análisis automático de tendencias
- Generación de recomendaciones
- Detección de anomalías contables
- Interpretación de ratios financieros

### 🔧 **Flexibilidad Avanzada**
- Niveles de detalle configurables
- Contexto de proyecto personalizable
- Filtros dinámicos
- Agregaciones automáticas

## Autenticación

Todos los endpoints requieren autenticación mediante Bearer Token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints Disponibles

### 📊 GET /balance-general

Genera Balance General con formato tabular unificado y narrativa automática.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/balance-general?project_context=Mi%20Empresa&from_date=2025-01-01&to_date=2025-06-10&detail_level=medio&include_subaccounts=false
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `project_context` (string, opcional): Contexto o nombre del proyecto (usa nombre de empresa si se omite)
- `from_date` (date, requerido): Fecha de inicio del período
- `to_date` (date, requerido): Fecha de fin del período
- `detail_level` (DetailLevel, opcional): Nivel de detalle del reporte (bajo, medio, alto) - default: medio
- `include_subaccounts` (bool, opcional): Incluir subcuentas en el detalle - default: false

#### Response Exitosa (200)
```json
{
  "success": true,
  "report_type": "balance_general",
  "generated_at": "2025-06-10",
  "period": {
    "from_date": "2025-01-01",
    "to_date": "2025-06-10"
  },
  "project_context": "Mi Empresa S.A.",
  "table": {
    "sections": [
      {
        "section_name": "ACTIVOS",
        "items": [
          {
            "account_group": "ACTIVOS",
            "account_code": "1001",
            "account_name": "Caja",
            "opening_balance": "0.00",
            "movements": "50000.00",
            "closing_balance": "50000.00",
            "level": 1
          },
          {
            "account_group": "ACTIVOS",
            "account_code": "1002",
            "account_name": "Bancos",
            "opening_balance": "0.00",
            "movements": "120000.00",
            "closing_balance": "120000.00",
            "level": 1
          }
        ],
        "total": "170000.00"
      },
      {
        "section_name": "PASIVOS",
        "items": [
          {
            "account_group": "PASIVOS",
            "account_code": "2001",
            "account_name": "Proveedores",
            "opening_balance": "0.00",
            "movements": "45000.00",
            "closing_balance": "45000.00",
            "level": 1
          }
        ],
        "total": "45000.00"
      },
      {
        "section_name": "PATRIMONIO",
        "items": [
          {
            "account_group": "PATRIMONIO",
            "account_code": "3001",
            "account_name": "Capital",
            "opening_balance": "0.00",
            "movements": "125000.00",
            "closing_balance": "125000.00",
            "level": 1
          }
        ],
        "total": "125000.00"
      }
    ],
    "totals": {
      "total_activos": "170000.00",
      "total_pasivos": "45000.00",
      "total_patrimonio": "125000.00",
      "total_pasivos_patrimonio": "170000.00"
    },
    "summary": {
      "is_balanced": true,
      "report_date": "2025-06-10",
      "company_name": "Mi Empresa S.A."
    }
  },
  "narrative": {
    "executive_summary": "El Balance General muestra una situación financiera sólida con activos por $170,000 respaldados completamente por patrimonio y pasivos.",
    "key_insights": [
      "La empresa mantiene una posición de liquidez saludable con $170,000 en activos corrientes",
      "El ratio de deuda sobre patrimonio es del 36%, indicando un nivel conservador de apalancamiento",
      "Los activos están balanceados correctamente con los pasivos y patrimonio"
    ],
    "recommendations": [
      "Considerar inversiones adicionales para optimizar la rentabilidad del efectivo",
      "Evaluar oportunidades de crecimiento dado el sólido patrimonio",
      "Mantener el nivel conservador de deuda para preservar la estabilidad financiera"
    ],
    "financial_highlights": {
      "total_assets": "170000.00",
      "debt_to_equity_ratio": "0.36",
      "liquidity_position": "Excelente"
    }
  }
}
```

#### Códigos de Error
- **400 Bad Request**: Parámetros inválidos o período incorrecto
- **401 Unauthorized**: Token inválido o expirado
- **500 Internal Server Error**: Error interno del servidor

---

### 📈 GET /perdidas-ganancias

Genera Estado de Pérdidas y Ganancias con análisis de rentabilidad.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/perdidas-ganancias?project_context=Mi%20Empresa&from_date=2025-01-01&to_date=2025-06-10&detail_level=medio&include_subaccounts=false
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `project_context` (string, opcional): Contexto o nombre del proyecto
- `from_date` (date, requerido): Fecha de inicio del período
- `to_date` (date, requerido): Fecha de fin del período
- `detail_level` (DetailLevel, opcional): Nivel de detalle (bajo, medio, alto) - default: medio
- `include_subaccounts` (bool, opcional): Incluir subcuentas - default: false

#### Response Exitosa (200)
```json
{
  "success": true,
  "report_type": "p_g",
  "generated_at": "2025-06-10",
  "period": {
    "from_date": "2025-01-01",
    "to_date": "2025-06-10"
  },
  "project_context": "Mi Empresa S.A.",
  "table": {
    "sections": [
      {
        "section_name": "INGRESOS",
        "items": [
          {
            "account_group": "INGRESOS",
            "account_code": "4001",
            "account_name": "Ventas",
            "opening_balance": "0.00",
            "movements": "250000.00",
            "closing_balance": "250000.00",
            "level": 1
          },
          {
            "account_group": "INGRESOS",
            "account_code": "4002",
            "account_name": "Ingresos por Servicios",
            "opening_balance": "0.00",
            "movements": "75000.00",
            "closing_balance": "75000.00",
            "level": 1
          }
        ],
        "total": "325000.00"
      },
      {
        "section_name": "GASTOS",
        "items": [
          {
            "account_group": "GASTOS",
            "account_code": "5001",
            "account_name": "Gastos de Administración",
            "opening_balance": "0.00",
            "movements": "45000.00",
            "closing_balance": "45000.00",
            "level": 1
          },
          {
            "account_group": "GASTOS",
            "account_code": "5002",
            "account_name": "Gastos de Ventas",
            "opening_balance": "0.00",
            "movements": "30000.00",
            "closing_balance": "30000.00",
            "level": 1
          }
        ],
        "total": "75000.00"
      }
    ],
    "totals": {
      "total_ingresos": "325000.00",
      "total_gastos": "75000.00",
      "utilidad_bruta": "325000.00",
      "utilidad_operacional": "250000.00",
      "utilidad_neta": "250000.00"
    },
    "summary": {
      "start_date": "2025-01-01",
      "end_date": "2025-06-10",
      "company_name": "Mi Empresa S.A."
    }
  },
  "narrative": {
    "executive_summary": "El período muestra excelente rentabilidad con ingresos de $325,000 y una utilidad neta de $250,000, representando un margen del 77%.",
    "key_insights": [
      "Los ingresos por ventas representan el 77% del total, mostrando un modelo de negocio diversificado",
      "Los gastos operativos se mantienen en un nivel eficiente del 23% sobre ingresos",
      "El margen de utilidad neta del 77% indica una excelente gestión operativa"
    ],
    "recommendations": [
      "Considerar expandir los servicios que muestran alta rentabilidad",
      "Evaluar oportunidades de crecimiento manteniendo la eficiencia operativa",
      "Invertir en marketing para incrementar las ventas"
    ],
    "financial_highlights": {
      "revenue_growth": "N/A (primer período)",
      "net_margin": "76.92%",
      "operational_efficiency": "Excelente"
    }
  }
}
```

#### Códigos de Error
- **400 Bad Request**: Parámetros inválidos
- **401 Unauthorized**: Token inválido o expirado
- **500 Internal Server Error**: Error de generación

---

### 💧 GET /flujo-efectivo

Genera Estado de Flujo de Efectivo con soporte para métodos directo e indirecto, categorización automática de actividades y análisis de liquidez.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/flujo-efectivo?project_context=Mi%20Empresa&from_date=2025-01-01&to_date=2025-06-10&detail_level=alto&include_subaccounts=false
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters
- `project_context` (string, opcional): Contexto o nombre del proyecto
- `from_date` (date, requerido): Fecha de inicio del período
- `to_date` (date, requerido): Fecha de fin del período
- `detail_level` (DetailLevel, opcional): 
  - **alto**: Método directo - muestra entradas y salidas brutas de efectivo
  - **medio/bajo**: Método indirecto - ajustes a la utilidad neta
  - default: medio
- `include_subaccounts` (bool, opcional): Incluir subcuentas - default: false

#### Características Especiales
- **Categorización Automática**: Las cuentas se categorizan automáticamente según su `cash_flow_category`
- **Método Dinámico**: El nivel de detalle determina si se usa método directo o indirecto
- **Validación**: Verifica que los flujos calculados coincidan con el cambio en efectivo
- **Análisis Inteligente**: Narrativa específica para flujos de efectivo con recomendaciones de liquidez

#### Response Exitosa (200) - Método Indirecto
```json
{
  "success": true,
  "report_type": "flujo_efectivo",
  "generated_at": "2025-06-10",
  "period": {
    "from_date": "2025-01-01",
    "to_date": "2025-06-10"
  },
  "project_context": "Mi Empresa S.A.",
  "table": {
    "sections": [
      {
        "section_name": "Actividades Operativas",
        "items": [
          {
            "account_group": "OPERATIVO",
            "account_code": "",
            "account_name": "Utilidad neta del período",
            "opening_balance": "0.00",
            "movements": "15000.00",
            "closing_balance": "15000.00",
            "level": 1
          },
          {
            "account_group": "OPERATIVO",
            "account_code": "",
            "account_name": "Ajustes para conciliar utilidad neta:",
            "opening_balance": "0.00",
            "movements": "0.00",
            "closing_balance": "0.00",
            "level": 1
          },
          {
            "account_group": "OPERATIVO",
            "account_code": "5010",
            "account_name": "  Depreciación",
            "opening_balance": "0.00",
            "movements": "2000.00",
            "closing_balance": "2000.00",
            "level": 2
          }
        ],
        "total": "17000.00"
      },
      {
        "section_name": "Actividades de Inversión",
        "items": [
          {
            "account_group": "INVERSION",
            "account_code": "1201",
            "account_name": "Compra de equipos",
            "opening_balance": "0.00",
            "movements": "-10000.00",
            "closing_balance": "-10000.00",
            "level": 1
          }
        ],
        "total": "-10000.00"
      },
      {
        "section_name": "Actividades de Financiamiento",
        "items": [
          {
            "account_group": "FINANCIAMIENTO",
            "account_code": "3001",
            "account_name": "Aporte de capital",
            "opening_balance": "0.00",
            "movements": "50000.00",
            "closing_balance": "50000.00",
            "level": 1
          }
        ],
        "total": "50000.00"
      },
      {
        "section_name": "Resumen de Efectivo",
        "items": [
          {
            "account_group": "RESUMEN",
            "account_code": "",
            "account_name": "Aumento neto en efectivo",
            "opening_balance": "0.00",
            "movements": "57000.00",
            "closing_balance": "57000.00",
            "level": 1
          },
          {
            "account_group": "RESUMEN",
            "account_code": "",
            "account_name": "Efectivo al inicio del período",
            "opening_balance": "0.00",
            "movements": "0.00",
            "closing_balance": "0.00",
            "level": 1
          },
          {
            "account_group": "RESUMEN",
            "account_code": "",
            "account_name": "Efectivo al final del período",
            "opening_balance": "0.00",
            "movements": "57000.00",
            "closing_balance": "57000.00",
            "level": 1
          }
        ],
        "total": "57000.00"
      }
    ],
    "totals": {
      "flujo_operativo": "17000.00",
      "flujo_inversion": "-10000.00",
      "flujo_financiamiento": "50000.00",
      "flujo_neto": "57000.00"
    },
    "summary": {
      "start_date": "2025-01-01",
      "end_date": "2025-06-10",
      "company_name": "Mi Empresa S.A.",
      "method": "indirect",
      "is_reconciled": true
    }
  },
  "narrative": {
    "executive_summary": "El flujo de efectivo muestra una generación sólida de $57,000 con contribuciones positivas de actividades operativas y de financiamiento, parcialmente compensadas por inversiones en equipos.",
    "key_insights": [
      "Las actividades operativas generaron $17,000, indicando capacidad de generación de efectivo desde operaciones",
      "La inversión de $10,000 en equipos representa una expansión de capacidades productivas",
      "El aporte de capital de $50,000 fortalece significativamente la posición financiera",
      "El flujo neto positivo de $57,000 mejora sustancialmente la liquidez"
    ],
    "recommendations": [
      "Continuar optimizando las actividades operativas para incrementar la generación de efectivo",
      "Evaluar el retorno de la inversión en equipos y planificar futuras inversiones estratégicas",
      "Considerar el establecimiento de una reserva de efectivo para oportunidades futuras",
      "Monitorear la eficiencia en el uso del capital recién aportado"
    ],
    "financial_highlights": {
      "operating_cash_flow": "17000.00",
      "investing_cash_flow": "-10000.00",
      "financing_cash_flow": "50000.00",
      "net_cash_flow": "57000.00",
      "cash_position_strength": "Muy fuerte",
      "liquidity_trend": "Mejorando significativamente",
      "method_used": "Método Indirecto"
    }
  }
}
```

#### Response Exitosa (200) - Método Directo (detail_level=alto)
El método directo muestra entradas y salidas brutas de efectivo en lugar de ajustes a la utilidad neta:

```json
{
  "table": {
    "sections": [
      {
        "section_name": "Actividades Operativas",
        "items": [
          {
            "account_group": "OPERATIVO",
            "account_code": "4001",
            "account_name": "Cobros por ventas",
            "opening_balance": "0.00",
            "movements": "100000.00",
            "closing_balance": "100000.00",
            "level": 1
          },
          {
            "account_group": "OPERATIVO",
            "account_code": "5001",
            "account_name": "Pagos a proveedores",
            "opening_balance": "0.00",
            "movements": "-65000.00",
            "closing_balance": "-65000.00",
            "level": 1
          },
          {
            "account_group": "OPERATIVO",
            "account_code": "5002",
            "account_name": "Pagos por sueldos",
            "opening_balance": "0.00",
            "movements": "-18000.00",
            "closing_balance": "-18000.00",
            "level": 1
          }
        ],
        "total": "17000.00"
      }
    ],
    "summary": {
      "method": "direct"
    }
  }
}
```

#### Códigos de Error
- **400 Bad Request**: Parámetros inválidos
- **401 Unauthorized**: Token inválido o expirado
- **500 Internal Server Error**: Error de generación

---

### 📋 GET /tipos

Lista todos los tipos de reportes financieros disponibles.

#### Permisos Requeridos
- Usuario autenticado (cualquier rol)

#### Request
```http
GET /api/v1/reports/tipos
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "type": "balance_general",
    "name": "Balance General",
    "description": "Estado de la situación financiera a una fecha específica",
    "endpoint": "/reports/balance-general"
  },
  {
    "type": "flujo_efectivo",
    "name": "Estado de Flujo de Efectivo",
    "description": "Movimientos de efectivo en un período específico",
    "endpoint": "/reports/flujo-efectivo"
  },
  {
    "type": "perdidas_ganancias",
    "name": "Estado de Pérdidas y Ganancias",
    "description": "Ingresos y gastos en un período específico",
    "endpoint": "/reports/perdidas-ganancias"
  }
]
```

#### Códigos de Error
- **401 Unauthorized**: Token inválido o expirado

---

## Esquemas de Datos

### ReportType (Enum)
```typescript
enum ReportType {
  BALANCE_GENERAL = "balance_general",
  FLUJO_EFECTIVO = "flujo_efectivo", 
  P_G = "p_g"  // Pérdidas y Ganancias
}
```

### DetailLevel (Enum)
```typescript
enum DetailLevel {
  BAJO = "bajo",
  MEDIO = "medio",
  ALTO = "alto"
}
```

### DateRange
```typescript
interface DateRange {
  from_date: Date;  // Fecha de inicio
  to_date: Date;    // Fecha de fin
}
```

### ReportResponse
```typescript
interface ReportResponse {
  success: boolean;
  report_type: ReportType;
  generated_at: Date;
  period: DateRange;
  project_context: string;
  table: ReportTable;
  narrative: ReportNarrative;
}
```

### ReportTable
```typescript
interface ReportTable {
  sections: ReportSection[];
  totals: Record<string, Decimal>;
  summary: Record<string, any>;
}
```

### ReportSection
```typescript
interface ReportSection {
  section_name: string;
  items: AccountReportItem[];
  total: Decimal;
}
```

### AccountReportItem
```typescript
interface AccountReportItem {
  account_group: string;
  account_code: string;
  account_name: string;
  opening_balance: Decimal;
  movements: Decimal;
  closing_balance: Decimal;
  level: number;
}
```

### ReportNarrative
```typescript
interface ReportNarrative {
  executive_summary: string;
  key_insights: string[];
  recommendations: string[];
  financial_highlights: Record<string, any>;
}
```

## Características Avanzadas

### 🎯 **Narrativa Automática**
La API genera automáticamente:
- **Resumen Ejecutivo**: Análisis condensado de la situación
- **Insights Clave**: Descubrimientos importantes de los datos
- **Recomendaciones**: Sugerencias basadas en análisis
- **Destacados Financieros**: Métricas y ratios relevantes

### 📊 **Niveles de Detalle**
- **Bajo**: Solo totales por sección
- **Medio**: Cuentas principales y subtotales
- **Alto**: Todas las cuentas incluidas, incluso con saldo cero

### 🏢 **Contexto de Proyecto**
- Permite personalizar el nombre del contexto
- Usa nombre de empresa por defecto si no se especifica
- Facilita reportes para múltiples entidades o proyectos

## Análisis Inteligente

### 🧮 **Cálculos Automáticos**
- Verificación de ecuaciones contables
- Cálculo de ratios financieros
- Detección de inconsistencias
- Tendencias y variaciones

### 🔍 **Detección de Anomalías**
- Balances inconsistentes
- Variaciones atípicas
- Cuentas con movimientos inusuales
- Alertas de integridad

### 💡 **Recomendaciones Inteligentes**
- Sugerencias de mejora financiera
- Oportunidades de optimización
- Alertas de riesgo
- Mejores prácticas contables

## Ejemplos de Uso

### Dashboard Ejecutivo
```http
GET /api/v1/reports/balance-general?detail_level=bajo&project_context=Dashboard%20Ejecutivo
```

### Análisis Detallado Mensual
```http
GET /api/v1/reports/perdidas-ganancias?from_date=2025-05-01&to_date=2025-05-31&detail_level=alto&include_subaccounts=true
```

### Monitoreo de Liquidez
```http
GET /api/v1/reports/flujo-efectivo?from_date=2025-06-01&to_date=2025-06-10&detail_level=medio
```

## Consideraciones de Rendimiento

- **Caching Inteligente**: Los reportes se cachean por parámetros
- **Procesamiento Asíncrono**: Generación no bloqueante
- **Optimización de Consultas**: Consultas SQL optimizadas
- **Agregación Eficiente**: Cálculos precomputados cuando es posible

## Límites y Restricciones

- **Período máximo**: 2 años para reportes detallados
- **Rate limiting**: 20 solicitudes por minuto por usuario
- **Tamaño de respuesta**: Máximo 10MB por reporte
- **Tiempo de generación**: Timeout de 30 segundos

## Integración con Sistemas Externos

La API está diseñada para facilitar la integración con:
- **Dashboards de BI**: Formato compatible con herramientas de visualización
- **Sistemas ERP**: Exportación de datos estructurados
- **Aplicaciones Móviles**: Formato JSON optimizado
- **Herramientas de Análisis**: Datos preparados para análisis avanzado
