# Gestión de Centros de Costo

Este documento describe la funcionalidad de gestión básica de centros de costo, incluyendo operaciones CRUD, validaciones y estructura de datos.

## Descripción General

El sistema de gestión de centros de costo permite organizar la empresa en unidades lógicas para el seguimiento y análisis de costos. Cada centro de costo puede tener centros hijos, formando una estructura jerárquica flexible.

## Modelo de Datos

### **CostCenter** - Modelo Principal

```python
class CostCenter(BaseModel):
    id: UUID                    # Identificador único
    code: str                   # Código del centro de costo
    name: str                   # Nombre descriptivo
    description: Optional[str]  # Descripción detallada
    parent_id: Optional[UUID]   # ID del centro padre
    is_active: bool            # Estado activo/inactivo
    created_at: datetime       # Fecha de creación
    updated_at: datetime       # Fecha de actualización
    
    # Propiedades calculadas
    level: int                 # Nivel en la jerarquía (0 = raíz)
    full_code: str            # Código completo jerárquico
    is_leaf: bool             # True si no tiene hijos
    
    # Relaciones
    parent: Optional["CostCenter"]     # Centro padre
    children: List["CostCenter"]       # Centros hijos
    journal_entries: List["JournalEntryLine"]  # Movimientos contables
```

### **Propiedades Calculadas**

#### **Nivel Jerárquico**
```python
@hybrid_property
def level(self) -> int:
    """Calcula el nivel en la jerarquía"""
    if not self.parent_id:
        return 0
    # Se calcula recursivamente desde la raíz
    return self.parent.level + 1 if self.parent else 0
```

#### **Código Completo**
```python
@hybrid_property
def full_code(self) -> str:
    """Genera código jerárquico completo"""
    if not self.parent_id:
        return self.code
    return f"{self.parent.full_code}.{self.code}"
```

#### **Es Hoja**
```python
@hybrid_property
def is_leaf(self) -> bool:
    """Determina si es un nodo hoja (sin hijos)"""
    return len(self.children) == 0
```

## Esquemas Pydantic

### **Esquemas de Entrada**

#### **CostCenterCreate**
```python
class CostCenterCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20, 
                     description="Código único del centro de costo")
    name: str = Field(..., min_length=1, max_length=100,
                     description="Nombre descriptivo")
    description: Optional[str] = Field(None, max_length=500,
                                      description="Descripción detallada")
    parent_id: Optional[UUID] = Field(None, 
                                     description="ID del centro padre")
    is_active: bool = Field(True, description="Estado activo")

    @validator('code')
    def validate_code(cls, v):
        """Validar formato del código"""
        if not re.match(r'^[A-Z0-9][A-Z0-9_-]*$', v):
            raise ValueError('Código debe contener solo letras, números, guiones y guiones bajos')
        return v.upper()
```

#### **CostCenterUpdate**
```python
class CostCenterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    
    # Nota: El código no se puede cambiar una vez creado
```

### **Esquemas de Salida**

#### **CostCenterRead**
```python
class CostCenterRead(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    parent_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Propiedades calculadas
    level: int
    full_code: str
    is_leaf: bool
    
    # Información del padre
    parent_name: Optional[str] = None
    
    # Estadísticas básicas
    children_count: int = 0
    movements_count: int = 0
    
    class Config:
        from_attributes = True
```

### **Esquemas Especializados**

#### **CostCenterHierarchy**
```python
class CostCenterHierarchy(BaseModel):
    """Representación jerárquica de centros de costo"""
    id: UUID
    code: str
    name: str
    level: int
    is_active: bool
    children: List["CostCenterHierarchy"] = []
    
    # Métricas básicas
    total_revenue: Decimal = Decimal('0')
    total_costs: Decimal = Decimal('0')
    net_margin: Decimal = Decimal('0')
```

#### **CostCenterFilter**
```python
class CostCenterFilter(BaseModel):
    """Filtros para búsqueda de centros de costo"""
    code: Optional[str] = None
    name: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    level: Optional[int] = None
    has_children: Optional[bool] = None
    
    # Filtros de fecha
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    
    # Ordenamiento
    order_by: str = Field('code', regex='^(code|name|created_at|level)$')
    order_desc: bool = False
    
    # Paginación
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
```

## Servicio de Negocio

### **CostCenterService** - Operaciones CRUD

```python
class CostCenterService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_cost_center(self, data: CostCenterCreate) -> CostCenter:
        """Crear nuevo centro de costo con validaciones"""
        
    async def get_cost_center(self, cost_center_id: UUID) -> Optional[CostCenter]:
        """Obtener centro de costo por ID"""
        
    async def update_cost_center(self, cost_center_id: UUID, data: CostCenterUpdate) -> CostCenter:
        """Actualizar centro de costo con validaciones"""
        
    async def delete_cost_center(self, cost_center_id: UUID) -> bool:
        """Eliminar centro de costo (soft delete)"""
        
    async def list_cost_centers(self, filters: CostCenterFilter) -> List[CostCenter]:
        """Listar centros de costo con filtros"""
```

### **Validaciones de Negocio**

#### **Validación de Código Único**
```python
async def _validate_unique_code(self, code: str, parent_id: Optional[UUID], exclude_id: Optional[UUID] = None):
    """Validar que el código sea único en el nivel jerárquico"""
    query = select(CostCenter).where(
        CostCenter.code == code,
        CostCenter.parent_id == parent_id
    )
    
    if exclude_id:
        query = query.where(CostCenter.id != exclude_id)
    
    result = await self.db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise ConflictError(f"Ya existe un centro de costo con código '{code}' en este nivel")
```

#### **Validación de Referencias Circulares**
```python
async def _validate_no_circular_reference(self, cost_center_id: UUID, new_parent_id: UUID):
    """Validar que no se cree una referencia circular"""
    current_parent = new_parent_id
    
    while current_parent:
        if current_parent == cost_center_id:
            raise ValidationError("No se puede asignar como padre - crearía referencia circular")
        
        parent = await self.get_cost_center(current_parent)
        current_parent = parent.parent_id if parent else None
```

#### **Validación de Eliminación**
```python
async def _can_delete_cost_center(self, cost_center_id: UUID) -> bool:
    """Verificar si se puede eliminar el centro de costo"""
    # Verificar si tiene hijos activos
    children_count = await self._count_active_children(cost_center_id)
    if children_count > 0:
        raise ValidationError("No se puede eliminar: tiene centros de costo hijos activos")
    
    # Verificar si tiene movimientos contables
    movements_count = await self._count_journal_entries(cost_center_id)
    if movements_count > 0:
        raise ValidationError("No se puede eliminar: tiene movimientos contables asociados")
    
    return True
```

## Operaciones Principales

### **Crear Centro de Costo**

```python
async def create_cost_center(self, data: CostCenterCreate) -> CostCenter:
    """Crear nuevo centro de costo"""
    
    # Validar código único
    await self._validate_unique_code(data.code, data.parent_id)
    
    # Validar padre existe y está activo
    if data.parent_id:
        parent = await self.get_cost_center(data.parent_id)
        if not parent:
            raise NotFoundError("Centro de costo padre no encontrado")
        if not parent.is_active:
            raise ValidationError("No se puede asignar un padre inactivo")
    
    # Crear centro de costo
    cost_center = CostCenter(
        id=uuid.uuid4(),
        code=data.code.upper(),
        name=data.name,
        description=data.description,
        parent_id=data.parent_id,
        is_active=data.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    self.db.add(cost_center)
    await self.db.commit()
    await self.db.refresh(cost_center)
    
    return cost_center
```

### **Actualizar Centro de Costo**

```python
async def update_cost_center(self, cost_center_id: UUID, data: CostCenterUpdate) -> CostCenter:
    """Actualizar centro de costo"""
    
    cost_center = await self.get_cost_center(cost_center_id)
    if not cost_center:
        raise NotFoundError("Centro de costo no encontrado")
    
    # Validar cambio de padre
    if data.parent_id is not None and data.parent_id != cost_center.parent_id:
        if data.parent_id:
            await self._validate_no_circular_reference(cost_center_id, data.parent_id)
            parent = await self.get_cost_center(data.parent_id)
            if not parent or not parent.is_active:
                raise ValidationError("Padre no válido")
    
    # Aplicar cambios
    for field, value in data.dict(exclude_unset=True).items():
        setattr(cost_center, field, value)
    
    cost_center.updated_at = datetime.utcnow()
    
    await self.db.commit()
    await self.db.refresh(cost_center)
    
    return cost_center
```

### **Obtener Jerarquía**

```python
async def get_hierarchy(self, root_id: Optional[UUID] = None) -> List[CostCenterHierarchy]:
    """Obtener estructura jerárquica de centros de costo"""
    
    # Consulta base para centros raíz o hijos de un padre específico
    query = select(CostCenter).where(
        CostCenter.is_active == True,
        CostCenter.parent_id == root_id
    ).order_by(CostCenter.code)
    
    result = await self.db.execute(query)
    root_centers = result.scalars().all()
    
    hierarchy = []
    for center in root_centers:
        hierarchy_item = await self._build_hierarchy_item(center)
        hierarchy.append(hierarchy_item)
    
    return hierarchy

async def _build_hierarchy_item(self, center: CostCenter) -> CostCenterHierarchy:
    """Construir item de jerarquía recursivamente"""
    
    # Obtener hijos
    children = await self.get_children(center.id)
    children_hierarchy = []
    
    for child in children:
        child_item = await self._build_hierarchy_item(child)
        children_hierarchy.append(child_item)
    
    # Calcular métricas básicas
    metrics = await self._calculate_basic_metrics(center.id)
    
    return CostCenterHierarchy(
        id=center.id,
        code=center.code,
        name=center.name,
        level=center.level,
        is_active=center.is_active,
        children=children_hierarchy,
        total_revenue=metrics.get('revenue', Decimal('0')),
        total_costs=metrics.get('costs', Decimal('0')),
        net_margin=metrics.get('margin', Decimal('0'))
    )
```

## Búsqueda y Filtrado

### **Búsqueda Avanzada**

```python
async def search_cost_centers(self, search_term: str, limit: int = 10) -> List[CostCenterRead]:
    """Búsqueda avanzada de centros de costo"""
    
    # Búsqueda por código, nombre o descripción
    query = select(CostCenter).where(
        or_(
            CostCenter.code.ilike(f'%{search_term}%'),
            CostCenter.name.ilike(f'%{search_term}%'),
            CostCenter.description.ilike(f'%{search_term}%')
        ),
        CostCenter.is_active == True
    ).limit(limit)
    
    result = await self.db.execute(query)
    cost_centers = result.scalars().all()
    
    # Convertir a schema de salida
    return [
        CostCenterRead.model_validate(cc) 
        for cc in cost_centers
    ]
```

### **Filtros Aplicados**

```python
async def list_cost_centers(self, filters: CostCenterFilter) -> List[CostCenterRead]:
    """Listar centros de costo con filtros aplicados"""
    
    query = select(CostCenter)
    
    # Aplicar filtros
    if filters.code:
        query = query.where(CostCenter.code.ilike(f'%{filters.code}%'))
    
    if filters.name:
        query = query.where(CostCenter.name.ilike(f'%{filters.name}%'))
    
    if filters.parent_id is not None:
        query = query.where(CostCenter.parent_id == filters.parent_id)
    
    if filters.is_active is not None:
        query = query.where(CostCenter.is_active == filters.is_active)
    
    if filters.level is not None:
        # Filtro por nivel requiere cálculo
        query = query.where(CostCenter.level == filters.level)
    
    # Aplicar ordenamiento
    order_column = getattr(CostCenter, filters.order_by)
    if filters.order_desc:
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))
    
    # Aplicar paginación
    query = query.offset(filters.skip).limit(filters.limit)
    
    result = await self.db.execute(query)
    cost_centers = result.scalars().all()
    
    return [CostCenterRead.model_validate(cc) for cc in cost_centers]
```

## Estadísticas y Métricas

### **Estadísticas Básicas**

```python
async def get_cost_center_stats(self, cost_center_id: UUID) -> Dict[str, Any]:
    """Obtener estadísticas básicas del centro de costo"""
    
    # Contar hijos
    children_count = await self._count_children(cost_center_id)
    
    # Contar movimientos
    movements_count = await self._count_journal_entries(cost_center_id)
    
    # Calcular totales del período actual
    current_month_totals = await self._calculate_current_month_totals(cost_center_id)
    
    return {
        'children_count': children_count,
        'movements_count': movements_count,
        'current_month_revenue': current_month_totals.get('revenue', Decimal('0')),
        'current_month_costs': current_month_totals.get('costs', Decimal('0')),
        'current_month_profit': current_month_totals.get('profit', Decimal('0')),
        'is_profitable': current_month_totals.get('profit', Decimal('0')) > 0
    }
```

## Consideraciones de Rendimiento

### **Optimizaciones Implementadas**

1. **Consultas Lazy/Eager**: Relaciones configuradas según el contexto de uso
2. **Índices de Base de Datos**: En campos de búsqueda frecuente
3. **Caching de Jerarquía**: Para estructuras que no cambian frecuentemente
4. **Paginación**: En todas las listas para manejar grandes volúmenes

### **Recomendaciones de Uso**

- Limitar la profundidad de jerarquía a 5 niveles máximo
- Usar filtros específicos en consultas de gran volumen
- Implementar cache para jerarquías estáticas
- Considerar desnormalización para reportes frecuentes

---

## Enlaces Relacionados

- [Estructura Jerárquica](./cost-center-hierarchy.md)
- [Reportes de Rentabilidad](./cost-center-reports.md)
- [Endpoints de API](./cost-center-endpoints.md)

---
**Última actualización**: Diciembre 2024  
**Versión**: 1.0.0
