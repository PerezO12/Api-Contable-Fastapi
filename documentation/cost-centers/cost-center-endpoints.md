# Endpoints de Centros de Costo - ACTUALIZADO

## Descripción General

Los endpoints de centros de costo proporcionan funcionalidades completas para la gestión de centros de costo, incluyendo operaciones CRUD, manejo jerárquico, reportes, validaciones y operaciones masivas. Los centros de costo permiten una distribución y seguimiento detallado de costos por departamentos, proyectos o actividades.

## Base URL

```
Base URL: /api/v1/cost-centers
```

## Autenticación

Todos los endpoints requieren autenticación mediante Bearer Token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints Disponibles

### ➕ POST /
Crear un nuevo centro de costo con soporte jerárquico.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
POST /api/v1/cost-centers/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "code": "CC001",
  "name": "Administración General",
  "description": "Centro de costo para gastos administrativos generales",
  "parent_id": null,
  "allows_direct_assignment": true,
  "is_active": true
}
```

#### Response Exitosa (201)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "CC001",
  "name": "Administración General",
  "description": "Centro de costo para gastos administrativos generales",
  "parent_id": null,
  "allows_direct_assignment": true,
  "is_active": true,
  "level": 0,
  "full_code": "CC001",
  "full_name": "CC001 - Administración General",
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### 📋 GET /
Obtener lista paginada de centros de costo con filtros.

#### Parámetros de Query
- `search`: Optional[str] - Búsqueda en código, nombre o descripción
- `is_active`: Optional[bool] - Filtrar por estado activo
- `parent_id`: Optional[UUID] - Filtrar por centro de costo padre
- `allows_direct_assignment`: Optional[bool] - Filtrar por capacidad de asignación
- `level`: Optional[int] - Filtrar por nivel jerárquico (0=raíz, 1=primer nivel, etc.)
- `has_children`: Optional[bool] - Filtrar si tiene centros hijos
- `is_leaf`: Optional[bool] - Filtrar nodos hoja (sin hijos)
- `is_root`: Optional[bool] - Filtrar nodos raíz (sin padre)
- `skip`: int = 0 - Registros a omitir
- `limit`: int = 100 - Máximo registros a retornar

#### Request
```http
GET /api/v1/cost-centers/?search=admin&is_active=true&level=0&limit=50
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "code": "CC001",
      "name": "Administración General",
      "description": "Centro de costo para gastos administrativos generales",
      "parent_id": null,
      "allows_direct_assignment": true,
      "is_active": true,
      "level": 0,
      "full_code": "CC001",
      "full_name": "CC001 - Administración General",
      "created_at": "2024-06-15T10:30:00Z",
      "updated_at": "2024-06-15T10:30:00Z"
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 50
}
```

---

### 🌳 GET /tree
Obtener estructura jerárquica completa de centros de costo como árbol.

#### Parámetros de Query
- `active_only`: bool = true - Incluir solo centros de costo activos

#### Request
```http
GET /api/v1/cost-centers/tree?active_only=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "CC001",
    "name": "Administración General",
    "level": 0,
    "allows_direct_assignment": false,
    "children": [
      {
        "id": "456e7890-e89b-12d3-a456-426614174000",
        "code": "CC001001",
        "name": "Recursos Humanos",
        "level": 1,
        "allows_direct_assignment": true,
        "children": []
      },
      {
        "id": "789e0123-e89b-12d3-a456-426614174000",
        "code": "CC001002",
        "name": "Contabilidad",
        "level": 1,
        "allows_direct_assignment": true,
        "children": []
      }
    ]
  }
]
```

---

### 🔍 GET /{cost_center_id}
Obtener centro de costo específico por ID con información de jerarquía.

#### Request
```http
GET /api/v1/cost-centers/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "CC001",
  "name": "Administración General",
  "description": "Centro de costo para gastos administrativos generales",
  "parent_id": null,
  "allows_direct_assignment": true,
  "is_active": true,
  "level": 0,
  "full_code": "CC001",
  "full_name": "CC001 - Administración General",
  "hierarchy_info": {
    "has_children": true,
    "children_count": 2,
    "is_root": true,
    "depth": 2
  },
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### 🔍 GET /code/{code}
Obtener centro de costo por código único.

#### Request
```http
GET /api/v1/cost-centers/code/CC001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "CC001",
  "name": "Administración General",
  "description": "Centro de costo para gastos administrativos generales",
  "parent_id": null,
  "allows_direct_assignment": true,
  "is_active": true,
  "level": 0,
  "full_code": "CC001",
  "full_name": "CC001 - Administración General",
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T10:30:00Z"
}
```

---

### ✏️ PUT /{cost_center_id}
Actualizar información de centro de costo.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
PUT /api/v1/cost-centers/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Administración General Actualizada",
  "description": "Descripción actualizada del centro de costo",
  "allows_direct_assignment": false,
  "is_active": true
}
```

#### Response Exitosa (200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "CC001",
  "name": "Administración General Actualizada",
  "description": "Descripción actualizada del centro de costo",
  "parent_id": null,
  "allows_direct_assignment": false,
  "is_active": true,
  "level": 0,
  "full_code": "CC001",
  "full_name": "CC001 - Administración General Actualizada",
  "created_at": "2024-06-15T10:30:00Z",
  "updated_at": "2024-06-15T15:45:00Z"
}
```

---

### 🗑️ DELETE /{cost_center_id}
Eliminar centro de costo si no tiene movimientos.

#### Permisos Requeridos
- **ADMIN** o **CONTADOR**

#### Request
```http
DELETE /api/v1/cost-centers/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (204)
```
No Content
```

#### Códigos de Error
- **400 Bad Request**: Centro de costo tiene movimientos asociados
- **409 Conflict**: Centro de costo tiene centros hijos

---

### 🏗️ GET /hierarchy/tree
Obtener jerarquía de centros de costo.

#### Parámetros de Query
- `parent_id`: Optional[UUID] - ID del centro de costo padre (null para raíz)

#### Request
```http
GET /api/v1/cost-centers/hierarchy/tree?parent_id=null
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "CC001",
    "name": "Administración General",
    "description": "Centro de costo para gastos administrativos generales",
    "parent_id": null,
    "allows_direct_assignment": true,
    "is_active": true,
    "level": 0,
    "full_code": "CC001",
    "full_name": "CC001 - Administración General",
    "hierarchy_info": {
      "has_children": true,
      "children_count": 2,
      "is_root": true,
      "depth": 2
    },
    "created_at": "2024-06-15T10:30:00Z",
    "updated_at": "2024-06-15T10:30:00Z"
  }
]
```

---

### 📊 GET /{cost_center_id}/report
Generar reporte de actividad del centro de costo para un período.

#### Parámetros de Query
- `start_date`: date (requerido) - Fecha de inicio del reporte
- `end_date`: date (requerido) - Fecha de fin del reporte

#### Request
```http
GET /api/v1/cost-centers/123e4567-e89b-12d3-a456-426614174000/report?start_date=2024-06-01&end_date=2024-06-30
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
  "cost_center_code": "CC001",
  "cost_center_name": "Administración General",
  "period": {
    "start_date": "2024-06-01",
    "end_date": "2024-06-30"
  },
  "summary": {
    "total_movements": 45,
    "total_amount": 2500000.00,
    "debits": 1800000.00,
    "credits": 700000.00,
    "net_amount": 1100000.00
  },
  "movements_by_account": [
    {
      "account_code": "5101001",
      "account_name": "Sueldos y Salarios",
      "total_amount": 1500000.00,
      "movement_count": 15
    }
  ],
  "movements_by_month": [
    {
      "month": "2024-06",
      "total_amount": 2500000.00,
      "movement_count": 45
    }
  ]
}
```

---

### ✅ GET /{cost_center_id}/validate
Validar datos del centro de costo y jerarquía.

#### Request
```http
GET /api/v1/cost-centers/123e4567-e89b-12d3-a456-426614174000/validate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
  "is_valid": true,
  "can_be_deleted": false,
  "can_modify_hierarchy": true,
  "has_movements": true,
  "has_children": true,
  "movement_count": 125,
  "children_count": 3,
  "warnings": [
    "Centro de costo tiene movimientos, considere cuidadosamente antes de eliminar"
  ],
  "restrictions": [
    "No se puede eliminar centro de costo con movimientos asociados",
    "No se puede eliminar centro de costo con centros hijos"
  ]
}
```

---

### 📈 GET /statistics/summary
Obtener estadísticas de uso y distribución de centros de costo.

#### Request
```http
GET /api/v1/cost-centers/statistics/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```json
{
  "total_cost_centers": 50,
  "active_cost_centers": 45,
  "inactive_cost_centers": 5,
  "root_cost_centers": 8,
  "cost_centers_with_children": 15,
  "cost_centers_allowing_assignment": 35,
  "cost_centers_with_movements": 28,
  "average_depth": 2.5,
  "max_depth": 4,
  "distribution_by_level": {
    "0": 8,
    "1": 20,
    "2": 15,
    "3": 7
  }
}
```

---

### 🔄 POST /bulk-operation
Operaciones masivas en múltiples centros de costo.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/cost-centers/bulk-operation
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "operation": "toggle_active",
  "cost_center_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ],
  "parameters": {
    "reason": "Reorganización departamental"
  }
}
```

#### Response Exitosa (200)
```json
{
  "operation": "toggle_active",
  "total_cost_centers": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
      "success": true,
      "message": "Estado actualizado correctamente"
    }
  ]
}
```

---

### 🗑️ POST /bulk-delete
Eliminación masiva de centros de costo con validaciones.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/cost-centers/bulk-delete
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "cost_center_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ],
  "force": false
}
```

#### Response Exitosa (200)
```json
{
  "total_requested": 2,
  "successful_deletions": 1,
  "failed_deletions": 1,
  "results": [
    {
      "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
      "success": false,
      "error": "Centro de costo tiene movimientos asociados"
    },
    {
      "cost_center_id": "456e7890-e89b-12d3-a456-426614174000",
      "success": true,
      "message": "Centro de costo eliminado correctamente"
    }
  ]
}
```

---

### ⚠️ POST /validate-deletion
Validar eliminación de centros de costo antes de ejecutar.

#### Request
```http
POST /api/v1/cost-centers/validate-deletion
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "cost_center_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174000"
  ]
}
```

#### Response Exitosa (200)
```json
[
  {
    "cost_center_id": "123e4567-e89b-12d3-a456-426614174000",
    "cost_center_code": "CC001",
    "cost_center_name": "Administración General",
    "can_delete": false,
    "blocking_reasons": [
      "Centro de costo tiene 125 movimientos asociados",
      "Centro de costo tiene 3 centros hijos"
    ],
    "warnings": [
      "Eliminar este centro afectará la jerarquía existente"
    ],
    "requires_confirmation": true
  }
]
```

---

### 📥 POST /import
Importar centros de costo masivamente desde archivo.

#### Permisos Requeridos
- **ADMIN** únicamente

#### Request
```http
POST /api/v1/cost-centers/import
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data

file: [archivo CSV/Excel con centros de costo]
validate_only: false
```

#### Response Exitosa (201)
```json
{
  "import_id": "import-uuid-here",
  "status": "processing",
  "total_rows": 50,
  "processed_rows": 0,
  "successful_imports": 0,
  "failed_imports": 0,
  "validation_errors": [],
  "estimated_completion": "2024-06-15T10:35:00Z",
  "started_at": "2024-06-15T10:30:00Z"
}
```

---

### 📤 GET /export/csv
Exportar centros de costo a archivo CSV.

#### Request
```http
GET /api/v1/cost-centers/export/csv
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Exitosa (200)
```
Content-Type: text/csv
Content-Disposition: attachment; filename="cost_centers_export_2024-06-15.csv"

code,name,description,parent_code,allows_direct_assignment,is_active,level
CC001,Administración General,Centro de gastos administrativos,,false,true,0
CC001001,Recursos Humanos,Departamento de RRHH,CC001,true,true,1
CC001002,Contabilidad,Departamento contable,CC001,true,true,1
...
```

---

## Flujos de Integración

### Creación de Jerarquía de Centros de Costo

```javascript
// 1. Crear centro de costo padre
const parentCenter = await fetch('/api/v1/cost-centers/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    code: 'CC001',
    name: 'Administración General',
    description: 'Centro de gastos administrativos',
    allows_direct_assignment: false,
    is_active: true
  })
});

// 2. Crear centros de costo hijos
const childCenter = await fetch('/api/v1/cost-centers/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    code: 'CC001001',
    name: 'Recursos Humanos',
    description: 'Departamento de RRHH',
    parent_id: parentCenter.id,
    allows_direct_assignment: true,
    is_active: true
  })
});
```

### Consulta de Reportes y Análisis

```javascript
// Obtener estructura jerárquica
const tree = await fetch('/api/v1/cost-centers/tree', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Generar reporte de centro de costo
const report = await fetch(
  `/api/v1/cost-centers/${costCenterId}/report?start_date=2024-06-01&end_date=2024-06-30`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);

// Obtener estadísticas generales
const stats = await fetch('/api/v1/cost-centers/statistics/summary', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

## Validaciones y Reglas de Negocio

### Estructura Jerárquica
- **Códigos únicos**: No pueden existir códigos duplicados
- **Jerarquía válida**: Un centro no puede ser padre de sí mismo
- **Niveles**: La profundidad máxima recomendada es 5 niveles
- **Asignación directa**: Solo centros con `allows_direct_assignment=true` pueden recibir movimientos

### Restricciones de Eliminación
- No se puede eliminar centro con movimientos asociados
- No se puede eliminar centro con centros hijos
- Solo administradores y contadores pueden eliminar centros

### Códigos de Centros de Costo
- **Formato recomendado**: CC + número secuencial (CC001, CC002, etc.)
- **Jerarquía en código**: Los hijos pueden usar el código padre como prefijo
- **Longitud**: Máximo 20 caracteres

## Códigos de Error Comunes

### 400 Bad Request
- Código de centro de costo inválido
- Jerarquía circular detectada
- Datos de entrada malformados

### 401 Unauthorized
- Token de autenticación inválido
- Token expirado

### 403 Forbidden
- Permisos insuficientes para la operación
- Usuario no puede modificar centros de costo

### 404 Not Found
- Centro de costo no encontrado
- Centro de costo padre no existe

### 409 Conflict
- Código de centro de costo ya existe
- Centro de costo tiene movimientos (al eliminar)
- Centro de costo tiene centros hijos (al eliminar)

### 422 Unprocessable Entity
- Validación de datos falló
- Estructura jerárquica inválida
- Parámetros de reporte inválidos

## Testing de Endpoints

### Casos de Prueba Críticos
1. **Jerarquía**: Crear estructura padre-hijo correcta
2. **Unicidad**: Verificar códigos únicos
3. **Asignación**: Validar restricciones de asignación directa
4. **Reportes**: Verificar cálculos de reportes
5. **Restricciones**: Probar eliminación con restricciones
6. **Permisos**: Verificar control de acceso por roles

### Ejemplo con pytest
```python
@pytest.mark.asyncio
async def test_create_cost_center_hierarchy(client: AsyncClient, admin_token: str):
    # Crear centro padre
    parent_response = await client.post(
        "/api/v1/cost-centers/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": "CC001",
            "name": "Administración General",
            "allows_direct_assignment": False
        }
    )
    assert parent_response.status_code == 201
    parent_data = parent_response.json()
    
    # Crear centro hijo
    child_response = await client.post(
        "/api/v1/cost-centers/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": "CC001001",
            "name": "Recursos Humanos",
            "parent_id": parent_data["id"],
            "allows_direct_assignment": True
        }
    )
    assert child_response.status_code == 201
    
    # Verificar jerarquía
    tree_response = await client.get(
        "/api/v1/cost-centers/tree",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert tree_response.status_code == 200
    tree_data = tree_response.json()
    assert len(tree_data) == 1
    assert len(tree_data[0]["children"]) == 1
```

## Referencias

- [Esquemas de Centros de Costo](../schemas/cost-center-schemas.md)
- [Reportes de Centros de Costo](../reports/cost-center-reports.md)
- [Asientos Contables](../journal-entries/journal-entry-endpoints.md)
- [Guía de Implementación](../guides/cost-center-setup.md)
