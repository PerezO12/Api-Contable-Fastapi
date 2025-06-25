# Guía de Uso del Asistente de Importación Genérico

## 🎯 Descripción General

El Asistente de Importación Genérico es un sistema completo similar al de Odoo que permite a los usuarios importar datos desde archivos CSV/XLSX de manera intuitiva y segura. El sistema incluye mapeo automático de columnas, validación de datos, vista previa y ejecución con feedback detallado.

## 🔧 Endpoints Disponibles

### 1. Obtener Modelos Disponibles
```http
GET /api/v1/generic-import/models
```
**Respuesta:**
```json
["third_party", "product", "account", "invoice"]
```

### 2. Obtener Metadatos de Modelo
```http
GET /api/v1/generic-import/models/third_party/metadata
```
**Respuesta:**
```json
{
  "model_name": "third_party",
  "display_name": "Tercero",
  "fields": [
    {
      "internal_name": "code",
      "display_label": "Código",
      "field_type": "text",
      "is_required": true,
      "is_unique": true,
      "max_length": 20
    },
    {
      "internal_name": "name",
      "display_label": "Nombre",
      "field_type": "text", 
      "is_required": true,
      "max_length": 100
    }
  ]
}
```

### 3. Subir Archivo y Crear Sesión
```http
POST /api/v1/generic-import/sessions
Content-Type: multipart/form-data

model_name: third_party
file: terceros.csv
```
**Respuesta:**
```json
{
  "import_session_token": "uuid-session-token",
  "model": "third_party",
  "model_display_name": "Tercero",
  "file_info": {
    "name": "terceros.csv",
    "size": 1024,
    "total_rows": 50
  },
  "detected_columns": [
    {
      "name": "codigo",
      "sample_values": ["C001", "C002", "C003"]
    },
    {
      "name": "nombre_completo", 
      "sample_values": ["Juan Pérez", "María García"]
    }
  ],
  "sample_rows": [
    {"codigo": "C001", "nombre_completo": "Juan Pérez"},
    {"codigo": "C002", "nombre_completo": "María García"}
  ]
}
```

### 4. Obtener Sugerencias de Mapeo
```http
GET /api/v1/generic-import/sessions/{session_id}/mapping-suggestions
```
**Respuesta:**
```json
{
  "session_id": "uuid-session-token",
  "model": "third_party",
  "suggestions": [
    {
      "column_name": "codigo",
      "suggested_field": "code",
      "confidence": 1.0,
      "reason": "Name similarity: 1.00"
    },
    {
      "column_name": "nombre_completo",
      "suggested_field": "name", 
      "confidence": 0.7,
      "reason": "Name similarity: 0.70"
    }
  ],
  "available_fields": [
    {
      "internal_name": "code",
      "display_label": "Código",
      "field_type": "text",
      "is_required": true
    }
  ],
  "auto_mappable_count": 2
}
```

### 5. Configurar Mapeo de Columnas
```http
POST /api/v1/generic-import/sessions/{session_id}/mapping
Content-Type: application/json

[
  {
    "column_name": "codigo",
    "field_name": "code"
  },
  {
    "column_name": "nombre_completo", 
    "field_name": "name"
  },
  {
    "column_name": "columna_ignorada",
    "field_name": null
  }
]
```

### 6. Vista Previa con Validación
```http
POST /api/v1/generic-import/sessions/{session_id}/preview
Content-Type: application/json

{
  "import_session_token": "uuid-session-token",
  "column_mappings": [
    {"column_name": "codigo", "field_name": "code"},
    {"column_name": "nombre_completo", "field_name": "name"}
  ],
  "preview_rows": 10
}
```
**Respuesta:**
```json
{
  "import_session_token": "uuid-session-token",
  "model": "third_party",
  "total_rows": 50,
  "preview_data": [
    {
      "row_number": 1,
      "original_data": {"codigo": "C001", "nombre_completo": "Juan Pérez"},
      "transformed_data": {"code": "C001", "name": "Juan Pérez"},
      "validation_status": "valid",
      "errors": [],
      "warnings": []
    },
    {
      "row_number": 2,
      "original_data": {"codigo": "", "nombre_completo": "María García"},
      "transformed_data": {"name": "María García"},
      "validation_status": "error",
      "errors": [
        {
          "field_name": "code",
          "error_type": "required_field_missing",
          "message": "Required field 'code' is missing or empty"
        }
      ]
    }
  ],
  "validation_summary": {
    "total_rows_analyzed": 10,
    "valid_rows": 8,
    "rows_with_errors": 2,
    "rows_with_warnings": 0
  },
  "can_proceed": false,
  "blocking_issues": ["2 rows have validation errors"]
}
```

### 7. Ejecutar Importación
```http
POST /api/v1/generic-import/sessions/{session_id}/execute
Content-Type: application/json

{
  "mappings": [
    {"column_name": "codigo", "field_name": "code"},
    {"column_name": "nombre_completo", "field_name": "name"}
  ],
  "import_policy": "create_only"
}
```
**Respuesta:**
```json
{
  "session_id": "uuid-session-token",
  "model": "third_party", 
  "import_policy": "create_only",
  "status": "completed",
  "total_rows": 50,
  "successful_rows": 48,
  "error_rows": 2,
  "errors": [
    "Row 15: Required field 'code' is missing or empty",
    "Row 23: Invalid email format: not-an-email"
  ],
  "message": "Import completed: 48 successful, 2 errors"
}
```

### 8. Obtener Plantillas
```http
GET /api/v1/generic-import/templates?model_name=third_party
```

### 9. Crear Plantilla
```http
POST /api/v1/generic-import/templates
Content-Type: application/json

{
  "name": "Terceros Básico",
  "model": "third_party",
  "description": "Mapeo básico para terceros",
  "mappings": [
    {"column_name": "codigo", "field_name": "code"},
    {"column_name": "nombre", "field_name": "name"}
  ]
}
```

### 10. Descargar Plantilla CSV
```http
GET /api/v1/generic-import/models/third_party/template
```
Devuelve un archivo CSV con las columnas correctas y datos de ejemplo.

## 🔄 Flujo de Trabajo Completo

### Paso 1: Preparación
1. **Obtener modelos disponibles** para saber qué se puede importar
2. **Consultar metadatos del modelo** para entender la estructura de campos
3. **Descargar plantilla CSV** (opcional) para preparar el archivo

### Paso 2: Subida y Análisis
1. **Subir archivo** con el modelo seleccionado
2. El sistema **detecta columnas automáticamente** y extrae muestra
3. **Obtener sugerencias de mapeo** para acelerar la configuración

### Paso 3: Configuración de Mapeo
1. **Configurar mapeo** de columnas a campos del modelo
2. Usar sugerencias automáticas o mapear manualmente
3. Ignorar columnas que no se necesiten

### Paso 4: Validación y Vista Previa
1. **Ejecutar vista previa** con validación completa
2. **Revisar errores** y problemas detectados
3. **Corregir datos** en el archivo original si es necesario
4. Repetir hasta que `can_proceed: true`

### Paso 5: Ejecución
1. **Ejecutar importación** con política seleccionada:
   - `create_only`: Solo crear registros nuevos
   - `update_only`: Solo actualizar existentes  
   - `upsert`: Crear o actualizar según corresponda
2. **Revisar resultados** y manejar errores si los hay

### Paso 6: Gestión de Plantillas (Opcional)
1. **Guardar configuración** como plantilla para reutilizar
2. **Usar plantillas existentes** en futuras importaciones

## 📋 Tipos de Validación

### Validaciones por Tipo de Campo:
- **text**: Longitud máxima, caracteres permitidos
- **number**: Rango de valores, formato numérico
- **date**: Formatos de fecha válidos
- **boolean**: Valores true/false reconocidos
- **email**: Formato de email válido
- **phone**: Formato de teléfono básico
- **many_to_one**: Existencia del registro relacionado

### Validaciones Generales:
- **Campos obligatorios**: No pueden estar vacíos
- **Campos únicos**: No pueden repetirse
- **Relaciones**: Los registros relacionados deben existir

## 🎨 Políticas de Importación

### create_only
- Solo crea registros nuevos
- Falla si encuentra duplicados
- Más seguro para datos maestros

### update_only  
- Solo actualiza registros existentes
- Requiere criterios de búsqueda únicos
- Útil para actualizar información

### upsert
- Crea si no existe, actualiza si existe
- Más flexible pero requiere más cuidado
- Ideal para sincronización de datos

## 🛡️ Consideraciones de Seguridad

- **Autenticación requerida** en todos los endpoints
- **Validación de permisos** por modelo (implementar según necesidades)
- **Limpieza automática** de archivos temporales
- **Sesiones con expiración** para evitar acumulación
- **Límites de tamaño** de archivo (configurar según necesidades)

## 🧪 Ejemplos de Uso

### Importar Terceros Básico
```bash
# 1. Subir archivo
curl -X POST "/api/v1/generic-import/sessions" \
  -F "model_name=third_party" \
  -F "file=@terceros.csv"

# 2. Obtener sugerencias  
curl "/api/v1/generic-import/sessions/{session_id}/mapping-suggestions"

# 3. Vista previa
curl -X POST "/api/v1/generic-import/sessions/{session_id}/preview" \
  -H "Content-Type: application/json" \
  -d '{"column_mappings": [{"column_name": "codigo", "field_name": "code"}]}'

# 4. Ejecutar
curl -X POST "/api/v1/generic-import/sessions/{session_id}/execute" \
  -H "Content-Type: application/json" \
  -d '{"mappings": [{"column_name": "codigo", "field_name": "code"}]}'
```

El sistema está diseñado para ser intuitivo y proporcionar feedback claro en cada paso, permitiendo a los usuarios importar datos de manera segura y eficiente.
