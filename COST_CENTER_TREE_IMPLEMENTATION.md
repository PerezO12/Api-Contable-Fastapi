# Implementación del Endpoint de Árbol de Centros de Costo

## Resumen de Cambios

Se ha implementado un nuevo endpoint para obtener los centros de costo en forma de árbol jerárquico, similar al endpoint de cuentas.

### 1. Schema Agregado

En `app/schemas/cost_center.py`:
```python
class CostCenterTree(BaseModel):
    """Schema para representar la jerarquía de centros de costo como árbol"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    allows_direct_assignment: bool
    manager_name: Optional[str] = None
    level: int
    is_leaf: bool
    children: List['CostCenterTree'] = Field(default_factory=list)
```

### 2. Endpoint Agregado

En `app/api/v1/cost_centers.py`:
```python
@router.get(
    "/tree",
    response_model=List[CostCenterTree],
    summary="Get cost center tree",
    description="Get complete hierarchical tree structure of cost centers"
)
async def get_cost_center_tree(
    active_only: bool = Query(True, description="Include only active cost centers"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[CostCenterTree]:
    """Get cost center tree structure."""
    
    service = CostCenterService(db)
    return await service.get_cost_center_tree(active_only=active_only)
```

### 3. Método del Servicio

En `app/services/cost_center_service.py`:
- Se agregó el método `get_cost_center_tree()`
- Evita problemas de lazy loading obteniendo todos los centros de costo de una vez
- Construye la estructura de árbol manualmente usando diccionarios
- Calcula propiedades dinámicas (level, is_leaf) de forma segura

### 4. Filtros Adicionales Implementados

También se agregaron nuevos filtros al endpoint de lista de centros de costo:
- `level`: Filtrar por nivel jerárquico (0=raíz, 1=primer nivel, etc.)
- `has_children`: Filtrar por si tiene hijos
- `is_leaf`: Filtrar por nodos hoja (sin hijos)
- `is_root`: Filtrar por nodos raíz (sin padre)

### 5. Corrección del Problema de Greenlet

Se corrigió el error original de "MissingGreenlet" asegurando que:
- Todas las relaciones necesarias se cargan con `selectinload()`
- Las propiedades calculadas se asignan antes de la validación de Pydantic
- Se calculan propiedades para objetos padre e hijos también

## Uso del Endpoint

### Obtener árbol completo (solo activos):
```
GET /api/v1/cost-centers/tree?active_only=true
```

### Obtener árbol completo (incluyendo inactivos):
```
GET /api/v1/cost-centers/tree?active_only=false
```

### Ejemplos de filtros en lista:
```
GET /api/v1/cost-centers/?level=0  # Solo centros raíz
GET /api/v1/cost-centers/?is_active=true&level=1&has_children=true  # Activos de nivel 1 con hijos
GET /api/v1/cost-centers/?is_leaf=true  # Solo nodos hoja
GET /api/v1/cost-centers/?is_root=true  # Solo nodos raíz
```

## Archivos Modificados

1. `app/schemas/cost_center.py` - Agregado `CostCenterTree` y nuevos filtros
2. `app/api/v1/cost_centers.py` - Agregado endpoint `/tree` y nuevos parámetros de consulta
3. `app/services/cost_center_service.py` - Agregado método `get_cost_center_tree()` y lógica de filtros
4. Se crearon archivos de prueba: `test_cost_center_tree.py` y `test_cost_center_filters.py`

La implementación sigue el mismo patrón que el endpoint de cuentas, evitando problemas de lazy loading y proporcionando una estructura de árbol eficiente.
