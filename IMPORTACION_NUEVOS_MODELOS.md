# Importación Genérica - Centros de Costo, Diarios y Términos de Pago

## 📋 Resumen

Se han agregado tres nuevos modelos al sistema de importación genérica:
- **Centros de Costo**: Para análisis de rentabilidad por departamento/proyecto
- **Diarios Contables**: Para organización de asientos contables
- **Términos de Pago**: Para definir condiciones de pago con cronogramas

## 🚀 Modelos Disponibles

### 1. Centros de Costo (`cost_center`)

**Campos disponibles:**
- `code` *(requerido, único)*: Código único del centro de costo
- `name` *(requerido, único)*: Nombre del centro de costo
- `description`: Descripción detallada
- `parent_code`: Código del centro padre (para jerarquías)
- `manager_name`: Nombre del responsable
- `budget_code`: Código presupuestario
- `is_active`: Activo (por defecto: true)
- `allows_direct_assignment`: Permite asignación directa (por defecto: true)
- `notes`: Notas adicionales

**Validaciones específicas:**
- El código debe ser único en todo el sistema
- El nombre debe ser único
- Si se especifica `parent_code`, el centro padre debe existir
- No se permiten referencias circulares en la jerarquía

**Ejemplo CSV:**
```csv
code,name,description,parent_code,manager_name,is_active
ADM,Administración,Centro administrativo,,Juan Pérez,true
VEN,Ventas,Centro de ventas,,María García,true
VEN-NAC,Ventas Nacionales,Ventas nacionales,VEN,Carlos López,true
```

### 2. Diarios Contables (`journal`)

**Campos disponibles:**
- `name` *(requerido)*: Nombre descriptivo del diario
- `code` *(requerido, único)*: Código único del diario
- `type` *(requerido)*: Tipo de diario (sale, purchase, cash, bank, miscellaneous)
- `sequence_prefix` *(requerido, único)*: Prefijo único para numeración
- `sequence_padding`: Dígitos para relleno (por defecto: 4)
- `include_year_in_sequence`: Incluir año en secuencia (por defecto: true)
- `reset_sequence_yearly`: Resetear secuencia anualmente (por defecto: true)
- `requires_validation`: Requiere validación (por defecto: false)
- `allow_manual_entries`: Permite asientos manuales (por defecto: true)
- `is_active`: Activo (por defecto: true)
- `description`: Descripción del propósito

**Validaciones específicas:**
- El código debe ser único
- El prefijo de secuencia debe ser único
- El tipo debe ser uno de los valores válidos
- El relleno de secuencia debe estar entre 1 y 10

**Ejemplo CSV:**
```csv
name,code,type,sequence_prefix,description
Diario de Ventas,VEN,sale,VEN,Para registrar ventas
Diario de Compras,COM,purchase,COM,Para registrar compras
Diario de Caja,CAJ,cash,CAJ,Para movimientos de efectivo
```

### 3. Términos de Pago (`payment_terms`)

**Campos disponibles:**
- `code` *(requerido, único)*: Código único de los términos
- `name` *(requerido)*: Nombre descriptivo
- `description`: Descripción detallada
- `is_active`: Activo (por defecto: true)
- `notes`: Notas adicionales
- `payment_schedule_days` *(requerido)*: Días separados por comas (ej: "0,30,60")
- `payment_schedule_percentages` *(requerido)*: Porcentajes separados por comas (ej: "50.0,30.0,20.0")
- `payment_schedule_descriptions`: Descripciones separadas por | (ej: "Anticipo|Intermedio|Final")

**Validaciones específicas:**
- El código debe ser único
- Los días deben ser números no negativos en orden ascendente
- Los porcentajes deben sumar exactamente 100.0%
- El número de días y porcentajes debe coincidir
- Los porcentajes deben estar entre 0.000001 y 100

**Ejemplo CSV:**
```csv
code,name,payment_schedule_days,payment_schedule_percentages,payment_schedule_descriptions
CONT,Contado,0,100.0,Pago inmediato
30D,30 Días,30,100.0,Pago a 30 días
30-60,30/60 Días,"30,60","50.0,50.0",Primera cuota|Segunda cuota
```

## 🔧 Uso de la API

### 1. Listar modelos disponibles
```http
GET /api/v1/generic-import/models
```

**Respuesta incluirá:**
```json
[
  "third_party",
  "product", 
  "account",
  "invoice",
  "cost_center",
  "journal",
  "payment_terms"
]
```

### 2. Obtener metadatos del modelo
```http
GET /api/v1/generic-import/models/cost_center/metadata
```

### 3. Crear sesión de importación
```http
POST /api/v1/generic-import/sessions
Content-Type: multipart/form-data

model_name: cost_center
file: [archivo CSV]
```

### 4. Vista previa con validación
```http
POST /api/v1/generic-import/preview
```

### 5. Ejecutar importación
```http
POST /api/v1/generic-import/execute
```

## 📝 Plantillas CSV

Se han creado plantillas de ejemplo en:
- `/examples/import_templates/cost_centers_template.csv`
- `/examples/import_templates/journals_template.csv`
- `/examples/import_templates/payment_terms_template.csv`

## ✅ Validaciones Implementadas

### Centros de Costo
- ✅ Unicidad de código y nombre
- ✅ Validación de existencia del centro padre
- ✅ Prevención de referencias circulares
- ✅ Valores por defecto para campos booleanos

### Diarios
- ✅ Unicidad de código y prefijo de secuencia
- ✅ Validación de tipos de diario válidos
- ✅ Validación de rango para relleno de secuencia
- ✅ Valores por defecto para configuración

### Términos de Pago
- ✅ Unicidad de código
- ✅ Validación de cronograma de pagos
- ✅ Verificación de suma de porcentajes = 100%
- ✅ Validación de orden ascendente de días
- ✅ Creación automática de PaymentSchedule

## 🚨 Manejo de Errores

### Errores Comunes

**Centro de Costo:**
- "Ya existe un centro de costo con código 'XXX'"
- "No se encontró centro de costo padre con código 'XXX'"

**Diario:**
- "Ya existe un diario con código 'XXX'"
- "Ya existe un diario con prefijo de secuencia 'XXX'"
- "Tipo de diario inválido"

**Términos de Pago:**
- "Los porcentajes deben sumar exactamente 100%"
- "Los días de pago deben estar en orden ascendente"
- "El número de días y porcentajes debe ser igual"

## 📊 Ejemplos de Uso

### Importar Centros de Costo con Jerarquía
```csv
code,name,parent_code,manager_name
EMPRESA,Empresa General,,CEO
ADM,Administración,EMPRESA,Dir. Admin
FIN,Finanzas,ADM,CFO
CONT,Contabilidad,FIN,Contador
```

### Importar Diarios por Módulo
```csv
name,code,type,sequence_prefix
Ventas Módulo 1,VEN1,sale,V1
Ventas Módulo 2,VEN2,sale,V2
Compras Proveedores,CPR,purchase,CPR
Caja General,CG,cash,CG
```

### Importar Términos con Cronogramas Complejos
```csv
code,name,payment_schedule_days,payment_schedule_percentages
NET15,Neto 15 días,15,100.0
2-10-NET30,2/10 neto 30,"10,30","98.0,2.0"
QUARTERLY,Trimestral,"30,60,90","33.33,33.33,33.34"
```

## 🔄 Flujo Recomendado

1. **Preparar datos:** Usar plantillas CSV como base
2. **Validar estructura:** Revisar campos requeridos y formatos
3. **Subir archivo:** Crear sesión de importación
4. **Revisar mapeo:** Verificar sugerencias automáticas
5. **Vista previa:** Validar datos antes de importar
6. **Ejecutar:** Procesar importación en lotes
7. **Verificar resultados:** Revisar errores y advertencias

## 🎯 Mejores Prácticas

### Centros de Costo
- Usar códigos jerárquicos (ej: VEN, VEN-NAC, VEN-INT)
- Definir estructura antes de importar (padres antes que hijos)
- Mantener códigos cortos pero descriptivos

### Diarios
- Usar prefijos únicos y descriptivos
- Configurar tipos apropiados según uso
- Considerar secuencias anuales para mejor organización

### Términos de Pago
- Verificar que porcentajes sumen exactamente 100%
- Usar días en orden ascendente
- Incluir descripciones claras para cada período

---

## 📞 Soporte

Para problemas específicos:
1. Revisar logs de validación en la respuesta
2. Verificar plantillas de ejemplo
3. Consultar documentación de modelos individuales
4. Usar vista previa para identificar errores antes de importar

**Última actualización:** Junio 2025  
**Versión:** 2.1.0 - Nuevos Modelos de Importación
