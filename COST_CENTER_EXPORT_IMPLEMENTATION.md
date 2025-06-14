# Implementación del Endpoint de Exportación de Centros de Costo

## Resumen de Cambios para Exportación CSV

Se ha mejorado y completado el endpoint de exportación de centros de costo a formato CSV.

### 1. Endpoint Mejorado

En `app/api/v1/cost_centers.py`:
```python
@router.get(
    "/export/csv",
    summary="Export cost centers to CSV",
    description="Export cost centers data to CSV format with optional filtering"
)
async def export_cost_centers_csv(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_id: Optional[uuid.UUID] = Query(None, description="Filter by parent cost center"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> StreamingResponse:
    """Export cost centers to CSV format."""
    
    service = CostCenterService(db)
    csv_content = await service.export_cost_centers_to_csv(is_active=is_active, parent_id=parent_id)
    
    # Crear nombre de archivo con timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"centros_costo_{timestamp}.csv"
    
    # Crear respuesta de streaming para descarga
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### 2. Método del Servicio Mejorado

En `app/services/cost_center_service.py`:
- Se mejoró `export_cost_centers_to_csv()` para usar `selectinload` y evitar lazy loading
- Se calculan las propiedades dinámicas (`level`, `is_leaf`, `full_code`) antes de exportar
- Se incluyen todos los campos relevantes en el CSV

### 3. Campos Incluidos en la Exportación CSV

El archivo CSV incluye las siguientes columnas:
1. **Código** - Código único del centro de costo
2. **Nombre** - Nombre del centro de costo
3. **Descripción** - Descripción opcional
4. **Padre** - Código del centro de costo padre
5. **Activo** - Estado activo/inactivo
6. **Permite Asignación Directa** - Si permite movimientos directos
7. **Responsable** - Nombre del responsable/manager
8. **Código Presupuesto** - Código presupuestario
9. **Notas** - Notas adicionales
10. **Código Completo** - Código jerárquico completo
11. **Nivel** - Nivel en la jerarquía
12. **Es Hoja** - Si es un nodo terminal
13. **Fecha Creación** - Fecha de creación
14. **Fecha Actualización** - Fecha de última actualización

### 4. Parámetros de Filtrado

El endpoint soporta filtrado opcional:
- `is_active`: Filtrar por estado activo/inactivo
- `parent_id`: Filtrar por centro de costo padre específico

### 5. Características del Archivo CSV

- **Encoding**: UTF-8 con BOM para compatibilidad con Excel
- **Separador**: Coma (`,`)
- **Nombre del archivo**: `centros_costo_YYYYMMDD_HHMMSS.csv`
- **Descarga automática**: El navegador descarga el archivo automáticamente
- **Headers apropiados**: Content-Disposition para descarga

## Uso del Endpoint

### Exportar todos los centros de costo:
```
GET /api/v1/cost-centers/export/csv
```

### Exportar solo centros de costo activos:
```
GET /api/v1/cost-centers/export/csv?is_active=true
```

### Exportar solo centros de costo inactivos:
```
GET /api/v1/cost-centers/export/csv?is_active=false
```

### Exportar centros de costo de un padre específico:
```
GET /api/v1/cost-centers/export/csv?parent_id=123e4567-e89b-12d3-a456-426614174000
```

### Combinar filtros:
```
GET /api/v1/cost-centers/export/csv?is_active=true&parent_id=123e4567-e89b-12d3-a456-426614174000
```

## Archivos Modificados

1. `app/api/v1/cost_centers.py` - Mejorado endpoint de exportación
2. `app/services/cost_center_service.py` - Mejorado método de exportación CSV
3. Se creó archivo de prueba: `test_cost_center_export.py`

## Mejoras Implementadas

- ✅ **Lazy Loading Fijo**: Usa `selectinload` para cargar relaciones
- ✅ **Propiedades Calculadas**: Calcula `level`, `is_leaf`, `full_code` antes de exportar
- ✅ **Filtrado Opcional**: Permite filtrar por estado y padre
- ✅ **Descarga Automática**: Respuesta como archivo descargable
- ✅ **Nombre de Archivo con Timestamp**: Evita conflictos de nombres
- ✅ **Documentación Completa**: Endpoint documentado con OpenAPI
- ✅ **Manejo de Errores**: Gestión apropiada de excepciones

El endpoint de exportación está ahora completamente funcional y listo para uso en producción.
