# Estructura Jerárquica de Centros de Costo

El sistema de centros de costo implementa una estructura jerárquica que permite organizar los centros de costo en múltiples niveles, similar a un árbol organizacional. Esta estructura facilita el análisis consolidado y la administración eficiente de los costos.

## Características de la Jerarquía

### ✅ **Estructura de Árbol Multinivel**
- Soporte para niveles ilimitados de anidación
- Relación padre-hijo claramente definida
- Códigos automáticos que reflejan la jerarquía
- Navegación intuitiva en la estructura

### ✅ **Validaciones de Integridad**
- Prevención de referencias circulares
- Validación de consistencia en movimientos
- Control de eliminación en cascada
- Verificación de códigos únicos

### ✅ **Propagación Automática**
- Cálculo de totales consolidados
- Propagación de cambios de estado
- Actualizaciones en tiempo real
- Mantenimiento de coherencia

## Modelo de Datos Jerárquico

### **Campos de Jerarquía**
```python
class CostCenter(Base):
    # Campos jerárquicos
    parent_id: Optional[uuid.UUID] = mapped_column(ForeignKey("cost_centers.id"))
    level: int = 0  # Calculado automáticamente
    path: str = ""  # Ruta jerárquica completa
    
    # Relaciones
    parent: Optional["CostCenter"] = relationship("CostCenter", remote_side=[id])
    children: List["CostCenter"] = relationship("CostCenter", back_populates="parent")
```

### **Propiedades Calculadas**
- `is_leaf`: Indica si es un nodo hoja (sin hijos)
- `descendants_count`: Número total de descendientes
- `depth`: Profundidad en el árbol
- `hierarchical_code`: Código que incluye la jerarquía

## Operaciones Jerárquicas

### **1. Creación de Centros de Costo**
- Validación automática del padre
- Cálculo del nivel jerárquico
- Generación del código jerárquico
- Actualización de estadísticas

### **2. Modificación de Estructura**
- Cambio de padre con validaciones
- Recálculo de niveles afectados
- Actualización de códigos dependientes
- Notificación de cambios

### **3. Eliminación Controlada**
- Verificación de centros hijos
- Reasignación o eliminación en cascada
- Validación de movimientos asociados
- Limpieza de referencias

### **4. Consultas Jerárquicas**
- Obtención de ancestros
- Consulta de descendientes
- Análisis de ramas completas
- Agregaciones por nivel

## Casos de Uso Comunes

### **Estructura Corporativa**
```
Empresa (ROOT)
├── Ventas (VEN)
│   ├── Ventas Nacionales (VEN-NAC)
│   │   ├── Zona Norte (VEN-NAC-NOR)
│   │   ├── Zona Centro (VEN-NAC-CEN)
│   │   └── Zona Sur (VEN-NAC-SUR)
│   └── Ventas Internacionales (VEN-INT)
│       ├── América (VEN-INT-AME)
│       └── Europa (VEN-INT-EUR)
├── Producción (PROD)
│   ├── Planta A (PROD-A)
│   └── Planta B (PROD-B)
└── Administración (ADM)
    ├── Recursos Humanos (ADM-RH)
    ├── Finanzas (ADM-FIN)
    └── Sistemas (ADM-SIS)
```

### **Estructura por Proyectos**
```
Proyectos (ROOT)
├── Proyecto Alpha (PROJ-ALPHA)
│   ├── Desarrollo (PROJ-ALPHA-DEV)
│   ├── Testing (PROJ-ALPHA-TEST)
│   └── Deployment (PROJ-ALPHA-DEPLOY)
├── Proyecto Beta (PROJ-BETA)
│   ├── Investigación (PROJ-BETA-RND)
│   └── Prototipo (PROJ-BETA-PROTO)
└── Mantenimiento (MANT)
    ├── Correctivo (MANT-CORR)
    └── Preventivo (MANT-PREV)
```

## Validaciones Implementadas

### **Validaciones de Creación**
1. **Padre Válido**: El centro de costo padre debe existir y estar activo
2. **No Circularidad**: No se permite que un centro sea padre de sí mismo (directa o indirectamente)
3. **Código Único**: Los códigos deben ser únicos en todo el sistema
4. **Profundidad Máxima**: Límite configurable de niveles de anidación

### **Validaciones de Modificación**
1. **Cambio de Padre**: Verificación de que el nuevo padre no genere circularidad
2. **Estado Consistente**: Los hijos no pueden estar activos si el padre está inactivo
3. **Movimientos Existentes**: Restricciones para cambios que afecten movimientos contables
4. **Integridad Referencial**: Mantenimiento de todas las referencias

### **Validaciones de Eliminación**
1. **Sin Hijos Activos**: No se puede eliminar un centro con hijos activos
2. **Sin Movimientos**: Verificación de movimientos contables asociados
3. **Reasignación**: Opción de reasignar movimientos antes de eliminar
4. **Confirmación**: Proceso de confirmación para eliminaciones complejas

## API de Operaciones Jerárquicas

### **Consulta de Estructura**
```http
GET /api/v1/cost-centers/hierarchy
GET /api/v1/cost-centers/{id}/children
GET /api/v1/cost-centers/{id}/ancestors
GET /api/v1/cost-centers/{id}/descendants
```

### **Análisis Jerárquico**
```http
GET /api/v1/cost-centers/{id}/consolidation
GET /api/v1/cost-centers/tree-analysis
POST /api/v1/cost-centers/bulk-operations
```

### **Modificación de Estructura**
```http
PUT /api/v1/cost-centers/{id}/move-to-parent
POST /api/v1/cost-centers/reorganize
DELETE /api/v1/cost-centers/{id}/cascade
```

## Beneficios de la Estructura Jerárquica

### **Para Administradores**
- **Organización Clara**: Estructura visual y lógica de la organización
- **Flexibilidad**: Capacidad de reorganizar según necesidades
- **Control Granular**: Administración a cualquier nivel de la jerarquía
- **Escalabilidad**: Soporte para organizaciones complejas

### **Para Analistas**
- **Análisis Multinivel**: Reportes desde el detalle hasta el consolidado
- **Drill-down/Roll-up**: Navegación intuitiva entre niveles
- **Comparaciones**: Análisis entre ramas de la organización
- **Tendencias**: Seguimiento de tendencias por niveles

### **Para Reportes**
- **Consolidación Automática**: Totales automáticos por rama
- **Segmentación**: Análisis por cualquier nivel de la jerarquía
- **Visualización**: Representación gráfica de la estructura
- **Exportación**: Datos estructurados para análisis externos

## Consideraciones de Rendimiento

### **Optimizaciones Implementadas**
- **Índices Específicos**: Índices optimizados para consultas jerárquicas
- **Caché de Estructura**: Almacenamiento en caché de la estructura completa
- **Consultas Eficientes**: Uso de CTEs recursivas para consultas complejas
- **Lazy Loading**: Carga bajo demanda de ramas específicas

### **Mejores Prácticas**
- **Profundidad Moderada**: Evitar jerarquías excesivamente profundas
- **Códigos Descriptivos**: Usar códigos que reflejen la estructura
- **Planificación**: Diseñar la estructura antes de implementar
- **Mantenimiento**: Revisión periódica de la estructura

## Troubleshooting

### **Problemas Comunes**
1. **Referencias Circulares**: Error al intentar crear ciclos en la jerarquía
2. **Códigos Duplicados**: Conflictos con códigos existentes
3. **Eliminación Bloqueada**: Centros con hijos o movimientos activos
4. **Inconsistencias**: Datos no sincronizados después de cambios

### **Soluciones**
1. **Validación Previa**: Verificar estructura antes de cambios
2. **Códigos Únicos**: Usar generadores automáticos de códigos
3. **Reasignación**: Proceso de reasignación antes de eliminar
4. **Sincronización**: Ejecutar procesos de sincronización periódicos

---

*Documentación técnica del sistema jerárquico de centros de costo - Sprint 2*
