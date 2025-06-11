# Importación Jerárquica de Cuentas

## Descripción General

La funcionalidad de importación de cuentas ha sido mejorada para soportar la importación de cuentas con relaciones padre-hijo en un solo archivo. Esto significa que puedes importar tanto cuentas padre como cuentas hijas en la misma operación, sin necesidad de importarlas por separado.

## Características Principales

### 1. Ordenamiento Automático por Jerarquía
- El sistema automáticamente reordena las cuentas para procesar las cuentas padre antes que las cuentas hijas
- No importa el orden en que aparezcan en el archivo CSV/Excel
- Se respetan las dependencias jerárquicas

### 2. Referencia por Código
- Las cuentas hijas pueden referenciar a sus padres usando el campo `parent_code`
- El `parent_code` puede referenciar tanto:
  - Cuentas existentes en la base de datos
  - Cuentas que están siendo importadas en el mismo archivo

### 3. Caché de Importación
- Se mantiene un caché interno durante la importación
- Las cuentas recién creadas están inmediatamente disponibles para ser referenciadas por otras cuentas en el mismo archivo

## Ejemplo de Uso

### Estructura del Archivo CSV

```csv
code,name,account_type,category,parent_code,description,is_active,allows_movements
1000,ACTIVOS,ACTIVO,ACTIVO_CORRIENTE,,Grupo principal de activos,true,false
1100,ACTIVOS CORRIENTES,ACTIVO,ACTIVO_CORRIENTE,1000,Activos de corto plazo,true,false
1110,DISPONIBLE,ACTIVO,ACTIVO_CORRIENTE,1100,Efectivo y equivalentes,true,false
1111,CAJA GENERAL,ACTIVO,ACTIVO_CORRIENTE,1110,Dinero en efectivo,true,true
```

### Notas Importantes

1. **Cuentas Padre**: Deben tener `allows_movements=false` ya que son cuentas de agrupación
2. **Cuentas Hoja**: Son las únicas que pueden tener `allows_movements=true`
3. **Códigos Únicos**: Cada código de cuenta debe ser único en todo el plan contable
4. **Tipos Coherentes**: Las cuentas hijas deben ser del mismo tipo que su cuenta padre

## Orden de Procesamiento

El sistema procesa las cuentas en el siguiente orden:

1. **Análisis de Dependencias**: Se identifican las relaciones padre-hijo
2. **Ordenamiento Topológico**: Se reordenan las cuentas para respetar las dependencias
3. **Procesamiento Secuencial**: Se procesan las cuentas en orden, creando primero los padres
4. **Actualización de Caché**: Cada cuenta creada se agrega al caché para futuras referencias

## Ejemplo de Flujo

```
Archivo Original:
- 1111,CAJA GENERAL,ACTIVO,ACTIVO_CORRIENTE,1110,...
- 1000,ACTIVOS,ACTIVO,ACTIVO_CORRIENTE,,...
- 1110,DISPONIBLE,ACTIVO,ACTIVO_CORRIENTE,1100,...
- 1100,ACTIVOS CORRIENTES,ACTIVO,ACTIVO_CORRIENTE,1000,...

Orden de Procesamiento Automático:
1. 1000,ACTIVOS (sin padre)
2. 1100,ACTIVOS CORRIENTES (padre: 1000)
3. 1110,DISPONIBLE (padre: 1100) 
4. 1111,CAJA GENERAL (padre: 1110)
```

## Validaciones

### Validaciones Automáticas

1. **Cuenta Padre Existente**: Verifica que el `parent_code` exista o esté en el archivo a importar
2. **Coherencia de Tipos**: La cuenta hija debe ser del mismo tipo que el padre
3. **Códigos Únicos**: No puede haber códigos duplicados
4. **Estructura Válida**: No se permiten referencias circulares

### Mensajes de Error Mejorados

- `PARENT_NOT_FOUND`: "Cuenta padre {código} no encontrada ni en BD ni en la importación actual"
- `CIRCULAR_REFERENCE`: "Referencia circular detectada en la jerarquía"
- `TYPE_MISMATCH`: "La cuenta hija debe ser del mismo tipo que la cuenta padre"

## Formatos Soportados

- **CSV**: Separado por comas con codificación UTF-8
- **XLSX**: Archivos de Excel con la primera fila como encabezados
- **JSON**: Estructura de objetos con los mismos campos

## Campos Requeridos

- `code`: Código único de la cuenta
- `name`: Nombre de la cuenta
- `account_type`: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS

## Campos Opcionales

- `parent_code`: Código de la cuenta padre (para jerarquía)
- `category`: Categoría específica del tipo de cuenta
- `description`: Descripción detallada
- `is_active`: Si la cuenta está activa (default: true)
- `allows_movements`: Si permite movimientos contables (default: true)
- `requires_third_party`: Si requiere tercero en los movimientos
- `requires_cost_center`: Si requiere centro de costo
- `notes`: Notas adicionales

## Ejemplo Completo

Ver el archivo `accounts_hierarchical_import_example.csv` en esta misma carpeta para un ejemplo completo que incluye:

- Estructura jerárquica de activos con 4 niveles
- Cuentas de pasivos con proveedores
- Patrimonio con capital social
- Ingresos operacionales
- Gastos administrativos con diferentes configuraciones

## Beneficios

1. **Eficiencia**: Importa toda la estructura contable en una sola operación
2. **Flexibilidad**: No requiere orden específico en el archivo
3. **Robustez**: Validaciones automáticas y manejo de errores
4. **Trazabilidad**: Logs detallados del proceso de importación
5. **Consistencia**: Garantiza la integridad de la estructura jerárquica
