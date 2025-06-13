# Nuevas Funcionalidades para Centros de Costo

## Resumen
Se han agregado funcionalidades de operaciones en lote (bulk) y importación/exportación masiva para los centros de costo, siguiendo el mismo patrón implementado en otros endpoints como `accounts`.

## Funcionalidades Agregadas

### 1. Eliminación en Lote (Bulk Delete)

**Endpoint:** `POST /api/v1/cost-centers/bulk-delete`

**Descripción:** Permite eliminar múltiples centros de costo con validaciones exhaustivas.

**Request Body:**
```json
{
  "cost_center_ids": ["uuid1", "uuid2", "uuid3"],
  "force_delete": false,
  "delete_reason": "Reestructuración departamental"
}
```

**Response:**
```json
{
  "total_requested": 3,
  "successfully_deleted": ["uuid1", "uuid2"],
  "failed_to_delete": [
    {
      "cost_center_id": "uuid3",
      "reason": "Tiene 2 centros de costo hijos",
      "details": {"children_count": 2}
    }
  ],
  "validation_errors": [],
  "warnings": ["Centro de costo uuid1: El centro de costo está activo"],
  "success_count": 2,
  "failure_count": 1,
  "success_rate": 66.67
}
```

**Validaciones realizadas:**
- Verifica que no tengan asientos contables asociados
- Verifica que no tengan centros de costo hijos
- Verifica que no estén siendo utilizados en otras partes del sistema
- Permite forzar eliminación con `force_delete=true`

### 2. Validación Previa de Eliminación

**Endpoint:** `POST /api/v1/cost-centers/validate-deletion`

**Descripción:** Valida si múltiples centros de costo pueden ser eliminados sin proceder con la eliminación.

**Request Body:**
```json
["uuid1", "uuid2", "uuid3"]
```

**Response:**
```json
[
  {
    "cost_center_id": "uuid1",
    "can_delete": true,
    "blocking_reasons": [],
    "warnings": ["El centro de costo está activo"],
    "dependencies": {}
  },
  {
    "cost_center_id": "uuid2",
    "can_delete": false,
    "blocking_reasons": ["Tiene 5 movimientos contables asociados"],
    "warnings": [],
    "dependencies": {"movements_count": 5}
  }
]
```

### 3. Importación Masiva desde CSV

**Endpoint:** `POST /api/v1/cost-centers/import`

**Descripción:** Importa centros de costo desde un archivo CSV/Excel.

**Formato CSV esperado:**
```csv
code,name,description,parent_code,is_active,allows_direct_assignment,manager_name,budget_code,notes
ADM,Administración,Departamento de Administración,,true,true,Juan Pérez,ADM001,Centro administrativo
VEN,Ventas,Departamento de Ventas,,true,true,María García,VEN001,Centro de ventas
VEN-01,Ventas Norte,Zona Norte,VEN,true,true,Ana Torres,VEN-N01,Ventas región norte
```

**Columnas:**
- `code` (requerido): Código único del centro de costo
- `name` (requerido): Nombre del centro de costo
- `description` (opcional): Descripción detallada
- `parent_code` (opcional): Código del centro de costo padre
- `is_active` (opcional): Si está activo (por defecto true)
- `allows_direct_assignment` (opcional): Si permite asignación directa (por defecto true)
- `manager_name` (opcional): Nombre del responsable
- `budget_code` (opcional): Código presupuestario
- `notes` (opcional): Notas adicionales

**Response:**
```json
{
  "total_rows": 5,
  "successfully_imported": 4,
  "updated_existing": 1,
  "failed_imports": [
    {
      "row": 3,
      "error": "Código y nombre son requeridos",
      "data": {"code": "", "name": ""}
    }
  ],
  "validation_errors": [],
  "warnings": [
    "Fila 4: Centro de costo padre 'INVALID' no encontrado, se creará sin padre"
  ],
  "created_cost_centers": ["uuid1", "uuid2"],
  "success_rate": 80.0
}
```

**Funcionalidades:**
- Crea nuevos centros de costo si no existen
- Actualiza centros de costo existentes (basado en el código)
- Maneja relaciones jerárquicas mediante `parent_code`
- Valida todos los datos antes de crear/actualizar
- Proporciona reporte detallado de errores y advertencias

### 4. Exportación a CSV

**Endpoint:** `GET /api/v1/cost-centers/export/csv`

**Descripción:** Exporta centros de costo a formato CSV.

**Parámetros de consulta:**
- `is_active` (opcional): Filtrar por estado activo
- `parent_id` (opcional): Filtrar por centro de costo padre

**Response:** Contenido CSV con todas las propiedades de los centros de costo.

**Ejemplo de uso:**
```
GET /api/v1/cost-centers/export/csv?is_active=true
```

## Archivos Modificados

### 1. Schemas (`app/schemas/cost_center.py`)
- **`BulkCostCenterDelete`**: Schema para solicitudes de eliminación múltiple
- **`BulkCostCenterDeleteResult`**: Schema para resultados de eliminación múltiple
- **`CostCenterDeleteValidation`**: Schema para validación de eliminación
- **`CostCenterImportResult`**: Schema para resultados de importación

### 2. Endpoints (`app/api/v1/cost_centers.py`)
- **`bulk_delete_cost_centers`**: Endpoint para eliminación múltiple
- **`validate_cost_centers_for_deletion`**: Endpoint para validación previa
- **`import_cost_centers`**: Endpoint para importación CSV
- **`export_cost_centers_csv`**: Endpoint para exportación CSV

### 3. Servicios (`app/services/cost_center_service.py`)
- **`bulk_delete_cost_centers`**: Lógica de eliminación múltiple
- **`validate_cost_center_for_deletion`**: Lógica de validación
- **`import_cost_centers_from_csv`**: Lógica de importación CSV
- **`export_cost_centers_to_csv`**: Lógica de exportación CSV

## Permisos y Seguridad

- **Bulk Delete**: Requiere permisos de `can_create_entries`
- **Import**: Requiere permisos de `can_create_entries`
- **Export**: Requiere ser usuario activo
- **Validate**: Requiere permisos de `can_create_entries`

## Compatibilidad

Las nuevas funcionalidades siguen el mismo patrón implementado en `accounts`, garantizando:
- Consistencia en la API
- Manejo de errores estandarizado
- Validaciones exhaustivas
- Respuestas estructuradas
- Documentación automática con OpenAPI

## Casos de Uso

1. **Reestructuración Organizacional**: Eliminar múltiples centros de costo obsoletos
2. **Migración de Datos**: Importar centros de costo desde sistemas externos
3. **Respaldo**: Exportar todos los centros de costo para respaldo
4. **Validación Masiva**: Verificar qué centros de costo pueden eliminarse antes de proceder

## Ejemplo de Flujo Completo

1. **Exportar datos actuales** para respaldo:
   ```
   GET /api/v1/cost-centers/export/csv
   ```

2. **Validar qué se puede eliminar**:
   ```
   POST /api/v1/cost-centers/validate-deletion
   ["uuid1", "uuid2", "uuid3"]
   ```

3. **Eliminar en lote** los que pasan validación:
   ```
   POST /api/v1/cost-centers/bulk-delete
   {
     "cost_center_ids": ["uuid1", "uuid2"],
     "force_delete": false,
     "delete_reason": "Reestructuración"
   }
   ```

4. **Importar nueva estructura**:
   ```
   POST /api/v1/cost-centers/import
   [CSV con nueva estructura]
   ```
