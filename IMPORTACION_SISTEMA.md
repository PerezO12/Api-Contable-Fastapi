# Sistema de Importación de Datos Contables

## Descripción General

El sistema de importación de la API Contable proporciona una solución empresarial robusta para importar datos contables desde archivos CSV, XLSX y JSON. Está diseñado con validaciones estrictas, procesamiento por lotes eficiente y manejo comprehensivo de errores.

## Características Principales

### ✅ Formatos Soportados
- **CSV** (Comma Separated Values)
- **XLSX** (Microsoft Excel)
- **JSON** (JavaScript Object Notation)

### ✅ Tipos de Datos
- **Cuentas Contables** (`accounts`)
- **Asientos Contables** (`journal_entries`)

### ✅ Niveles de Validación
- **STRICT**: Falla si hay cualquier error de validación
- **TOLERANT**: Procesa registros válidos, reporta errores
- **PREVIEW**: Solo valida sin importar datos

### ✅ Funcionalidades Empresariales
- Procesamiento por lotes configurable
- Validaciones de integridad de datos
- Manejo de duplicados
- Actualización de registros existentes
- Reportes detallados de errores
- Templates de importación
- Preview de datos antes de importar

## Endpoints Disponibles

### 1. Preview de Importación
```http
POST /api/v1/import/preview
```
Analiza el archivo y muestra una vista previa sin importar datos.

**Request Body:**
```json
{
  "file_content": "base64_encoded_content",
  "filename": "accounts.csv",
  "configuration": {
    "data_type": "accounts",
    "format": "csv",
    "validation_level": "preview",
    "batch_size": 100,
    "skip_duplicates": true,
    "update_existing": false,
    "continue_on_error": false
  },
  "preview_rows": 10
}
```

**Response:**
```json
{
  "detected_format": "csv",
  "detected_data_type": "accounts",
  "total_rows": 5,
  "preview_data": [...],
  "column_mapping": {...},
  "validation_errors": [],
  "recommendations": [...]
}
```

### 2. Importación de Datos
```http
POST /api/v1/import/import
```
Importa datos con validaciones completas y procesamiento por lotes.

### 3. Subida y Preview de Archivo
```http
POST /api/v1/import/upload-file
```
Sube un archivo y obtiene preview automático.

### 4. Importación Directa desde Archivo
```http
POST /api/v1/import/import-file
```
Importación directa con configuración automática.

### 5. Templates de Importación
```http
GET /api/v1/import/templates
```
Obtiene templates disponibles con columnas requeridas y datos de ejemplo.

### 6. Descarga de Templates
```http
GET /api/v1/import/templates/{data_type}/download?format={format}
```
Descarga templates específicos para cada tipo de datos.

### 7. Formatos Soportados
```http
GET /api/v1/import/formats
```
Lista formatos, tipos de datos y límites del sistema.

## Estructura de Datos

### Cuentas Contables

#### Columnas Requeridas:
- `code`: Código único de la cuenta
- `name`: Nombre de la cuenta
- `account_type`: Tipo (ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS)

#### Columnas Opcionales:
- `category`: Categoría específica del tipo
- `parent_code`: Código de cuenta padre
- `description`: Descripción detallada
- `is_active`: Si la cuenta está activa (default: true)
- `allows_movements`: Si permite movimientos (default: true)
- `requires_third_party`: Si requiere terceros (default: false)
- `requires_cost_center`: Si requiere centro de costo (default: false)
- `notes`: Notas adicionales

#### Ejemplo CSV:
```csv
code,name,account_type,category,parent_code,description,is_active,allows_movements
1001,Caja,ACTIVO,ACTIVO_CORRIENTE,,Dinero en efectivo,true,true
1002,Bancos,ACTIVO,ACTIVO_CORRIENTE,,Cuentas bancarias,true,true
2001,Proveedores,PASIVO,PASIVO_CORRIENTE,,Cuentas por pagar,true,true
3001,Capital,PATRIMONIO,PATRIMONIO_NETO,,Capital social,true,false
```

### Asientos Contables

#### Estructura para CSV:
Cada línea representa una línea del asiento. Las líneas del mismo asiento deben tener la misma fecha y referencia.

#### Columnas Requeridas:
- `entry_date`: Fecha del asiento (YYYY-MM-DD)
- `description`: Descripción del asiento
- `account_code`: Código de la cuenta
- `debit_amount`: Monto débito (usar 0 si es crédito)
- `credit_amount`: Monto crédito (usar 0 si es débito)

#### Columnas Opcionales:
- `reference`: Referencia externa
- `entry_type`: Tipo de asiento (default: MANUAL)
- `third_party`: Tercero asociado
- `cost_center`: Centro de costo
- `notes`: Notas del asiento

#### Ejemplo CSV:
```csv
entry_date,description,account_code,debit_amount,credit_amount,reference
2024-01-15,Venta de mercadería,1001,1000.00,0.00,FAC-001
2024-01-15,Venta de mercadería,4001,0.00,1000.00,FAC-001
2024-01-16,Compra de suministros,5001,500.00,0.00,COMP-002
2024-01-16,Compra de suministros,1001,0.00,500.00,COMP-002
```

## Validaciones Implementadas

### Validaciones de Cuentas:
- ✅ Código único y obligatorio
- ✅ Nombre obligatorio
- ✅ Tipo de cuenta válido
- ✅ Categoría válida (si se especifica)
- ✅ Cuenta padre debe existir (si se especifica)
- ✅ Cuenta padre debe ser del mismo tipo
- ✅ Validación de jerarquía circular

### Validaciones de Asientos:
- ✅ Fecha válida
- ✅ Descripción obligatoria
- ✅ Al menos 2 líneas por asiento
- ✅ Balance cuadrado (débitos = créditos)
- ✅ Cuentas deben existir
- ✅ Línea debe tener débito O crédito (no ambos)
- ✅ Montos no negativos
- ✅ Cuentas deben permitir movimientos

## Configuración de Importación

### Parámetros Principales:

```json
{
  "data_type": "accounts|journal_entries",
  "format": "csv|xlsx|json",
  "validation_level": "strict|tolerant|preview",
  "batch_size": 100,
  "skip_duplicates": true,
  "update_existing": false,
  "continue_on_error": false,
  "csv_delimiter": ",",
  "csv_encoding": "utf-8",
  "xlsx_sheet_name": null,
  "xlsx_header_row": 1
}
```

### Límites del Sistema:
- **Tamaño máximo de archivo**: 10MB
- **Filas máximas por importación**: 10,000
- **Tamaño máximo de lote**: 1,000
- **Filas máximas en preview**: 100

## Manejo de Errores

### Tipos de Errores:
- **validation**: Errores de validación de datos
- **business**: Errores de lógica de negocio
- **system**: Errores del sistema

### Estructura de Error:
```json
{
  "row_number": 5,
  "field_name": "account_type",
  "error_code": "INVALID_ACCOUNT_TYPE",
  "error_message": "Tipo de cuenta inválido",
  "error_type": "validation",
  "severity": "error"
}
```

### Resultados por Fila:
```json
{
  "row_number": 1,
  "status": "success|error|warning|skipped",
  "entity_id": "uuid",
  "entity_code": "1001",
  "errors": [],
  "warnings": []
}
```

## Permisos Requeridos

### Para Importar Cuentas:
- Usuario debe tener `can_modify_accounts = true`
- Roles permitidos: ADMIN

### Para Importar Asientos:
- Usuario debe tener `can_create_entries = true`
- Roles permitidos: ADMIN, CONTADOR

## Ejemplos de Uso

### 1. Preview de Cuentas CSV
```python
import requests
import base64

# Leer archivo CSV
with open('cuentas.csv', 'rb') as f:
    file_content = base64.b64encode(f.read()).decode('utf-8')

# Preview request
response = requests.post(
    'http://api.example.com/api/v1/import/preview',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'file_content': file_content,
        'filename': 'cuentas.csv',
        'configuration': {
            'data_type': 'accounts',
            'format': 'csv',
            'validation_level': 'preview',
            'batch_size': 100
        },
        'preview_rows': 5
    }
)

print(response.json())
```

### 2. Importación Real de Asientos
```python
# Importación con validación estricta
response = requests.post(
    'http://api.example.com/api/v1/import/import',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'file_content': file_content,
        'filename': 'asientos.csv',
        'configuration': {
            'data_type': 'journal_entries',
            'format': 'csv',
            'validation_level': 'strict',
            'batch_size': 50,
            'skip_duplicates': false,
            'continue_on_error': false
        }
    }
)

result = response.json()
print(f"Procesadas: {result['summary']['processed_rows']}")
print(f"Exitosas: {result['summary']['successful_rows']}")
print(f"Errores: {result['summary']['error_rows']}")
```

## Optimizaciones de Rendimiento

### 1. Procesamiento por Lotes
El sistema procesa datos en lotes configurables para optimizar memoria y rendimiento.

### 2. Caché de Cuentas
Durante la importación, las cuentas se cargan en caché para acelerar las validaciones.

### 3. Transacciones por Lote
Se usa una transacción por lote para evitar transacciones muy largas.

### 4. Validación Temprana
Se validan los datos antes de iniciar la importación para fallar rápido.

## Monitoreo y Logging

### Logs Generados:
- Inicio y fin de importaciones
- Errores de procesamiento
- Estadísticas de rendimiento
- Uso de caché

### Métricas Importantes:
- Tiempo de procesamiento
- Filas procesadas por segundo
- Tasa de errores
- Uso de memoria

## Extensibilidad

### Agregar Nuevos Formatos:
1. Implementar parser en `ImportDataService`
2. Agregar formato al enum `ImportFormat`
3. Actualizar templates y documentación

### Agregar Nuevos Tipos de Datos:
1. Crear schemas de importación
2. Implementar procesamiento en el servicio
3. Agregar validaciones específicas
4. Crear templates

## Mejores Prácticas

### Para Archivos CSV:
- Usar encoding UTF-8
- Incluir headers en la primera fila
- Escapar comillas internas con comillas dobles
- Usar formato de fecha YYYY-MM-DD

### Para Archivos Excel:
- Usar extensión .xlsx
- Headers en la primera fila
- Una hoja por tipo de datos
- Formatear fechas correctamente

### Para Importación de Asientos:
- Agrupar líneas del mismo asiento consecutivamente
- Usar la misma referencia para líneas del mismo asiento
- Verificar balance antes de importar
- Importar cuentas antes que asientos

### Para Manejo de Errores:
- Usar modo preview primero
- Configurar batch_size apropiado según tamaño
- Usar validation_level=tolerant para importaciones grandes
- Revisar logs de errores detalladamente

## Soporte y Troubleshooting

### Errores Comunes:

1. **"Account not found"**
   - Verificar que las cuentas existan antes de importar asientos
   - Revisar códigos de cuenta en el archivo

2. **"Unbalanced entry"**
   - Verificar que débitos = créditos en cada asiento
   - Revisar formatos numéricos

3. **"Invalid account type"**
   - Usar tipos válidos: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS

4. **"File too large"**
   - Dividir archivo en partes más pequeñas (< 10MB)
   - Usar batch_size más pequeño

5. **"Permission denied"**
   - Verificar permisos del usuario
   - Contactar administrador para asignar roles apropiados

Para soporte adicional, revisar logs del servidor y usar modo preview para diagnosticar problemas.
