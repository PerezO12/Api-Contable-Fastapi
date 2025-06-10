# Exportación de Plantillas de Datos

Este documento describe las funcionalidades de exportación de plantillas y ejemplos que facilitan la preparación de datos para su importación en el sistema API Contable.

> **Nota**: Para información detallada sobre la estructura de las plantillas y los formatos soportados, consulte el documento [Plantillas y Formatos de Importación](import-templates.md).

## Visión General

El sistema ofrece la capacidad de descargar plantillas predefinidas para los diferentes tipos de datos que se pueden importar. Estas plantillas sirven como ejemplos y guías que ayudan a los usuarios a estructurar correctamente sus datos antes de importarlos, reduciendo errores y agilizando el proceso.

Las plantillas están disponibles en múltiples formatos (CSV, XLSX, JSON) para adaptarse a las preferencias y necesidades de los usuarios:

- **CSV**: Formato simple basado en texto plano, compatible con la mayoría de herramientas
- **XLSX**: Formato Excel con documentación adicional y validaciones
- **JSON**: Formato estructurado ideal para representar datos jerárquicos

## Endpoints de Exportación de Plantillas

> **Nota**: Todos los endpoints descritos a continuación usan la ruta base `/api/v1/templates/`.

### Listado de Plantillas Disponibles

```http
GET /api/v1/templates/
```

Obtiene información sobre todas las plantillas disponibles, sus formatos y contenido.

**Permisos Requeridos:**
- Usuario autenticado (cualquier rol)

**Respuesta Exitosa (200):**
```json
{
  "available_templates": {
    "accounts": {
      "description": "Plantilla para importación de cuentas contables",
      "formats": ["csv", "xlsx", "json"],
      "endpoints": {
        "csv": "/api/v1/templates/accounts/csv",
        "xlsx": "/api/v1/templates/accounts/xlsx", 
        "json": "/api/v1/templates/accounts/json"
      },
      "required_fields": ["code", "name", "account_type"],
      "optional_fields": ["category", "parent_code", "description", "is_active", "allows_movements", "requires_third_party", "requires_cost_center", "notes"],
      "example_data": {
        "code": "1105",
        "name": "Caja General",
        "account_type": "ACTIVO",
        "category": "ACTIVO_CORRIENTE",
        "parent_code": "1100"
      }
    },
    "journal_entries": {
      "description": "Plantilla para importación de asientos contables",
      "formats": ["csv", "xlsx", "json"], 
      "endpoints": {
        "csv": "/api/v1/templates/journal-entries/csv",
        "xlsx": "/api/v1/templates/journal-entries/xlsx",
        "json": "/api/v1/templates/journal-entries/json"
      },
      "required_fields": ["entry_number", "entry_date", "description", "account_code", "line_description"],
      "conditional_fields": ["debit_amount", "credit_amount"],
      "optional_fields": ["reference", "entry_type", "third_party", "cost_center", "line_reference"],
      "example_data": {
        "entry_number": "AST-2024-001",
        "entry_date": "2024-01-15",
        "description": "Compra de material de oficina",
        "account_code": "5105",
        "line_description": "Material de oficina - papelería",
        "debit_amount": 150000
      }
    }
  },
  "formats_supported": ["csv", "xlsx", "json"],
  "notes": [
    "Las plantillas incluyen datos de ejemplo y documentación",
    "Los archivos XLSX incluyen hojas adicionales con documentación de campos",
    "Para asientos contables, agrupe las líneas por entry_number",
    "Respete los nombres de columnas exactos mostrados en las plantillas",
    "Para importar cuentas use los tipos: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS",
    "Para asientos contables, solo un monto (débito o crédito) debe tener valor por línea"
  ]
}
```

### Exportar Plantilla de Cuentas Contables

```http
GET /api/v1/templates/accounts/{format}
```

Descarga una plantilla con estructura y ejemplos para la importación de cuentas contables.

**Parámetros de Ruta:**
- `format`: Formato de la plantilla (`csv`, `xlsx`, `json`)

**Permisos Requeridos:**
- Usuario autenticado con permisos para modificar cuentas (`can_modify_accounts`)

**Respuesta:**
- Archivo de plantilla en el formato solicitado

#### Contenido Específico por Formato

**JSON:**
- Incluye metadatos detallados sobre la estructura de los datos
- Documentación de campos y tipos válidos
- Ejemplos completos de cuentas

Ejemplo (parcial):
```json
{
  "template_info": {
    "data_type": "accounts",
    "format": "json",
    "description": "Plantilla de ejemplo para importación de cuentas contables",
    "required_fields": ["code", "name", "account_type"],
    "optional_fields": ["category", "parent_code", "description", "is_active", ...]
  },
  "field_descriptions": {
    "code": "Código único de la cuenta (máximo 20 caracteres)",
    "name": "Nombre de la cuenta (máximo 200 caracteres)",
    "account_type": "Tipo de cuenta: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS",
    ...
  },
  "valid_account_types": ["ACTIVO", "PASIVO", "PATRIMONIO", "INGRESO", "GASTO", "COSTOS"],
  "example_data": [...]
}
```

Vea el ejemplo completo en [accounts_template.json](examples/accounts_template.json)
```

**XLSX:**
- Múltiples hojas de trabajo:
  - `Accounts_Template`: Datos de ejemplo para importar
  - `Field_Documentation`: Documentación detallada de cada campo
  - `Valid_Types`: Valores permitidos para tipos y categorías

**CSV:**
- Formato simple con encabezados y ejemplos de datos
- Estructura plana sin metadatos adicionales

### Exportar Plantilla de Asientos Contables

```http
GET /api/v1/templates/journal-entries/{format}
```

Descarga una plantilla con estructura y ejemplos para la importación de asientos contables.

**Parámetros de Ruta:**
- `format`: Formato de la plantilla (`csv`, `xlsx`, `json`)

**Permisos Requeridos:**
- Usuario autenticado con permisos para crear asientos (`can_create_entries`)

**Respuesta:**
- Archivo de plantilla en el formato solicitado

#### Contenido Específico por Formato

**JSON:**
- Incluye metadatos detallados sobre la estructura de los asientos
- Documentación de reglas de negocio para asientos válidos
- Ejemplos completos de asientos con múltiples líneas

Ejemplo (parcial):
```json
{
  "template_info": {
    "data_type": "journal_entries",
    "format": "json",
    "description": "Plantilla de ejemplo para importación de asientos contables",
    "required_fields": ["entry_number", "entry_date", "description", "account_code", "line_description"],
    "optional_fields": ["reference", "entry_type", "debit_amount", "credit_amount", ...],
    "important_notes": [
      "Cada línea del asiento debe tener entry_number idéntico para agruparse",
      "Solo uno de debit_amount o credit_amount debe tener valor por línea",
      ...
    ]
  },
  "field_descriptions": {
    "entry_number": "Número único del asiento contable",
    "entry_date": "Fecha del asiento (formato: YYYY-MM-DD)",
    ...
  },
  "valid_entry_types": ["MANUAL", "AUTOMATIC", "ADJUSTMENT", "OPENING", "CLOSING", "REVERSAL"],
  "example_data": [...]
}
```

Vea el ejemplo completo en [journal_entries_template.json](examples/journal_entries_template.json)
```

**XLSX:**
- Múltiples hojas de trabajo:
  - `Journal_Entries_Template`: Datos de ejemplo para importar
  - `Field_Documentation`: Documentación detallada de cada campo
  - `Business_Rules`: Reglas de negocio para asientos válidos

**CSV:**
- Formato simple con encabezados y ejemplos de datos
- Estructura plana donde las líneas de un mismo asiento comparten entry_number

## Características Especiales de las Plantillas

### Plantilla de Cuentas Contables

Las plantillas de cuentas contables se caracterizan por:

1. **Estructura jerárquica**: Demostración del uso de parent_code para crear relaciones jerárquicas
2. **Campos booleanos**: Ejemplos de uso de is_active, allows_movements y otros campos de tipo true/false
3. **Tipos de cuenta**: Incluye todos los tipos de cuenta válidos con sus respectivas categorías
4. **Campos requeridos vs opcionales**: Clara distinción entre campos obligatorios y opcionales

### Plantilla de Asientos Contables

Las plantillas de asientos contables se caracterizan por:

1. **Estructura de doble partida**: Demostración del balance entre débitos y créditos
2. **Agrupación de líneas**: Ejemplos de cómo las líneas se agrupan en un asiento mediante el entry_number
3. **Montos condicionales**: Ejemplos de uso correcto de debit_amount y credit_amount (solo uno con valor)
4. **Referencias externas**: Uso de campos reference para documentos externos
5. **Tipos de asiento**: Ejemplos de los diferentes tipos de asiento (MANUAL, AUTOMATIC, etc.)

## Recomendaciones de Uso

- **Documentación integrada**: Los formatos XLSX y JSON incluyen documentación detallada que debe ser consultada
- **Mantener estructura**: Respetar las estructuras y nombres de campos exactamente como aparecen en las plantillas
- **Validación previa**: Usar el endpoint `/api/v1/import/preview` para validar los datos antes de importarlos
- **Datos de ejemplo**: Utilizar los datos de ejemplo como guía para entender las relaciones y restricciones

## Consideraciones Técnicas

- Las plantillas JSON son especialmente útiles para importaciones programáticas mediante API
- Las plantillas XLSX contienen validaciones y son ideales para la preparación manual de datos
- Las plantillas CSV son las más universales pero carecen de metadatos y documentación integrada

## Limitaciones

- El formato de fecha debe ser estrictamente YYYY-MM-DD
- Los valores booleanos deben ser true/false en JSON, y "true"/"false" en CSV/XLSX
- Las columnas con nombres incorrectos serán ignoradas durante la importación
- Los códigos de cuenta referenciados deben existir o estar incluidos en el mismo lote de importación

## Tabla de Compatibilidad de Formatos

| Característica | CSV | XLSX | JSON |
|---------------|-----|------|------|
| Facilidad de edición manual | ★★★★☆ | ★★★★★ | ★★☆☆☆ |
| Integración con sistemas | ★★★★☆ | ★★☆☆☆ | ★★★★★ |
| Documentación integrada | ☆☆☆☆☆ | ★★★★☆ | ★★★★★ |
| Representación de jerarquías | ★☆☆☆☆ | ★★☆☆☆ | ★★★★★ |
| Validación de datos | ★☆☆☆☆ | ★★★☆☆ | ★★★★☆ |
| Capacidad de metadatos | ☆☆☆☆☆ | ★★★☆☆ | ★★★★★ |
