# Sistema de Importación de Datos

El sistema API Contable ofrece una funcionalidad robusta y profesional para importar datos contables desde diversos formatos, permitiendo la incorporación masiva de información al sistema de manera eficiente y controlada.

## Contenido

- [Visión General](#visión-general)
- [Formatos Soportados](#formatos-soportados)
- [Tipos de Datos para Importación](#tipos-de-datos-para-importación)
- [Niveles de Validación](#niveles-de-validación)
- [Proceso de Importación](#proceso-de-importación)
- [Endpoints de Importación](#endpoints-de-importación)
- [Plantillas de Importación](#plantillas-de-importación)
- [Exportación de Plantillas](#exportación-de-plantillas)
- [Estructura de las Plantillas](#estructura-de-las-plantillas)
- [Manejo de Errores](#manejo-de-errores)
- [Optimización de Rendimiento](#optimización-de-rendimiento)

## Visión General

El sistema de importación permite a los usuarios cargar datos contables desde archivos en diferentes formatos, validarlos según reglas de negocio y procesarlos por lotes, con características avanzadas como:

- Preview y validación previa sin importar
- Procesamiento por lotes para archivos grandes
- Manejo configurable de duplicados y errores
- Seguimiento detallado del proceso
- Plantillas de ejemplo para facilitar la preparación de datos
- Validaciones empresariales específicas para cada tipo de datos

## Formatos Soportados

El sistema soporta los siguientes formatos de archivo:

- **CSV** (Valores Separados por Comas)
- **XLSX** (Microsoft Excel)
- **JSON** (JavaScript Object Notation)

El sistema detecta automáticamente el formato basado en la extensión del archivo o la configuración proporcionada.

## Tipos de Datos para Importación

Actualmente se soportan los siguientes tipos de datos para importación:

1. **Cuentas Contables** (`accounts`):
   - Permite importar el plan de cuentas completo
   - Soporta jerarquías de cuentas (padres e hijos)
   - Incluye todas las propiedades de las cuentas (tipo, categoría, estado, etc.)

2. **Asientos Contables** (`journal_entries`):
   - Permite importar asientos completos con múltiples líneas
   - Validación automática de balance (débitos = créditos)
   - Referencias a cuentas existentes en el sistema

## Niveles de Validación

El sistema ofrece diferentes niveles de validación para adaptarse a distintas necesidades:

1. **Estricto** (`strict`):
   - Detiene el proceso ante cualquier error
   - Garantiza la integridad total de los datos
   - Ideal para importaciones iniciales críticas

2. **Tolerante** (`tolerant`):
   - Continúa el proceso a pesar de errores no críticos
   - Registra todos los errores para revisión posterior
   - Útil para importaciones masivas donde algunos errores son aceptables

3. **Vista Previa** (`preview`):
   - Solo valida sin importar realmente
   - Muestra todos los posibles errores y advertencias
   - Permite ajustar los datos antes de realizar la importación real

## Proceso de Importación

El flujo típico de importación consta de los siguientes pasos:

1. **Preparación de Datos**:
   - Descargar plantilla en el formato deseado usando los endpoints de exportación
   - Completar los datos siguiendo la estructura de la plantilla
   - Guardar el archivo en formato compatible

2. **Vista Previa y Validación**:
   - Cargar el archivo para vista previa
   - Revisar los datos detectados y posibles errores
   - Ajustar la configuración de importación según necesidades

3. **Importación**:
   - Ejecutar la importación con las opciones configuradas
   - Monitorear el progreso de la importación
   - Revisar el reporte de resultados

4. **Verificación Post-Importación**:
   - Revisar el historial de importaciones
   - Verificar los datos importados en el sistema
   - Realizar ajustes manuales si es necesario

## Exportación de Plantillas

El sistema proporciona endpoints especializados para exportar plantillas que facilitan la preparación de datos para importación:

- Plantillas disponibles para todos los tipos de datos soportados
- Múltiples formatos (CSV, XLSX, JSON) con características específicas
- Documentación incorporada y ejemplos prácticos
- Estructura adaptada a las reglas del negocio

Para más detalles sobre las plantillas disponibles y cómo utilizarlas, consulte el documento [Exportación de Plantillas de Datos](export-templates.md).
