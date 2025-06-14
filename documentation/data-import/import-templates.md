# Plantillas y Formatos de Importación

Este documento describe las plantillas y formatos disponibles para importar datos en el sistema API Contable.

> **Nota**: Para información sobre cómo exportar plantillas y ejemplos mediante la API, consulte el documento [Exportación de Plantillas de Datos](export-templates.md).

## Plantillas Disponibles

El sistema proporciona plantillas predefinidas para facilitar la importación de datos. Estas plantillas sirven como guía para estructurar correctamente los datos y garantizar una importación exitosa.

### Plantillas de Cuentas Contables

Las plantillas de cuentas contables facilitan la importación del plan de cuentas al sistema.

#### Columnas Requeridas

| Columna       | Descripción                                      | Ejemplo       |
|---------------|--------------------------------------------------|---------------|
| code          | Código único de la cuenta (máx. 20 caracteres)   | 1001          |
| name          | Nombre de la cuenta (máx. 200 caracteres)        | Caja          |
| account_type  | Tipo de cuenta (ACTIVO, PASIVO, etc.)            | ACTIVO        |

#### Columnas Opcionales

| Columna               | Descripción                                      | Ejemplo           |
|-----------------------|--------------------------------------------------|-------------------|
| category              | Categoría específica según el tipo               | ACTIVO_CORRIENTE  |
| cash_flow_category    | Categoría flujo efectivo (operating, investing, financing, cash) | operating |
| parent_code           | Código de cuenta padre para jerarquía            | 1000              |
| description           | Descripción detallada de la cuenta               | Dinero en efectivo|
| is_active             | Si la cuenta está activa (true/false)            | true              |
| allows_movements      | Si permite registrar movimientos (true/false)    | true              |
| requires_third_party  | Si requiere especificar tercero (true/false)     | false             |
| requires_cost_center  | Si requiere centro de costo (true/false)         | false             |
| notes                 | Notas adicionales sobre la cuenta                | Notas de ejemplo  |

#### Datos de Ejemplo

```csv
code,name,account_type,category,cash_flow_category,parent_code,description,is_active,allows_movements,requires_third_party,requires_cost_center,notes
1105,Caja General,ACTIVO,ACTIVO_CORRIENTE,cash,1100,Dinero en efectivo en caja principal,true,true,false,false,Cuenta para manejo de efectivo - Efectivo y equivalentes para flujo de efectivo
1110,Bancos Moneda Nacional,ACTIVO,ACTIVO_CORRIENTE,cash,1100,Depósitos en bancos en moneda nacional,true,true,true,false,Requiere especificar el banco como tercero - Efectivo y equivalentes
1120,Clientes Nacionales,ACTIVO,ACTIVO_CORRIENTE,operating,1100,Cuentas por cobrar a clientes nacionales,true,true,true,false,Requiere especificar el cliente - Actividades operativas
1201,Equipos de Oficina,ACTIVO,ACTIVO_NO_CORRIENTE,investing,1200,Mobiliario y equipos para oficina,true,true,false,true,Activos fijos - Actividades de inversión
2105,Proveedores Nacionales,PASIVO,PASIVO_CORRIENTE,operating,2100,Cuentas por pagar a proveedores nacionales,true,true,true,false,Requiere especificar el proveedor - Actividades operativas
2201,Préstamos Bancarios LP,PASIVO,PASIVO_NO_CORRIENTE,financing,2200,Préstamos bancarios a largo plazo,true,true,true,false,Requiere especificar el banco - Actividades de financiamiento
3001,Capital Social,PATRIMONIO,CAPITAL,financing,3000,Aportes de capital de los socios,true,true,false,false,Capital inicial de la empresa - Actividades de financiamiento
4001,Ventas de Productos,INGRESO,INGRESOS_OPERACIONALES,operating,4000,Ingresos por venta de productos,true,true,false,true,Ingresos principales del negocio - Actividades operativas
5001,Sueldos y Salarios,GASTO,GASTOS_OPERACIONALES,operating,5000,Remuneraciones del personal,true,true,false,true,Gastos de personal - Actividades operativas
6001,Costo de Mercadería Vendida,COSTOS,COSTO_VENTAS,operating,6000,Costo directo de productos vendidos,true,true,false,true,Costo directo de ventas - Actividades operativas
```

#### Categorías de Flujo de Efectivo

El campo `cash_flow_category` es fundamental para la clasificación de las cuentas en los estados de flujo de efectivo. A continuación se detallan las categorías disponibles:

| Categoría    | Descripción                                      | Ejemplos de Cuentas |
|--------------|--------------------------------------------------|---------------------|
| **operating**   | Actividades de Operación - Ingresos, gastos, costos y cuentas corrientes relacionadas con la operación principal del negocio | Clientes, Proveedores, Ventas, Gastos operativos, Costos de venta |
| **investing**   | Actividades de Inversión - Activos fijos, equipos, propiedades y otras inversiones de capital | Equipos, Maquinaria, Propiedades, Inversiones en instrumentos financieros |
| **financing**   | Actividades de Financiamiento - Préstamos, capital, dividendos y operaciones relacionadas con la estructura financiera | Préstamos bancarios, Capital social, Dividendos, Aportes de socios |
| **cash**        | Efectivo y Equivalentes - Caja, bancos e inversiones temporales de alta liquidez | Caja, Bancos, Inversiones temporales, Fondos de inversión líquidos |

> **Importante**: La correcta clasificación de las cuentas en estas categorías es esencial para generar estados de flujo de efectivo precisos y cumplir con las normas contables aplicables.

### Plantillas de Asientos Contables

Las plantillas de asientos contables facilitan la importación de transacciones al sistema.

#### Estructura de la Plantilla

Para asientos contables, la plantilla tiene una estructura más compleja que combina información de cabecera del asiento con sus líneas detalladas.

#### Columnas del Asiento (Cabecera)

| Columna       | Descripción                                      | Ejemplo           |
|---------------|--------------------------------------------------|-------------------|
| entry_date    | Fecha del asiento (YYYY-MM-DD)                   | 2024-01-15        |
| reference     | Referencia externa (opcional)                    | FAC-001           |
| description   | Descripción del asiento                          | Venta de mercadería|
| entry_type    | Tipo de asiento                                  | MANUAL            |
| notes         | Notas adicionales (opcional)                     | Pago al contado   |

#### Columnas de Líneas de Asiento

| Columna       | Descripción                                      | Ejemplo           |
|---------------|--------------------------------------------------|-------------------|
| account_code  | Código de la cuenta contable                     | 1001              |
| description   | Descripción del movimiento                       | Ingreso por venta |
| debit_amount  | Monto débito (usar 0 si es crédito)              | 1000.00           |
| credit_amount | Monto crédito (usar 0 si es débito)              | 0.00              |
| third_party   | Tercero (opcional)                               | Cliente ABC       |
| cost_center   | Centro de costo (opcional)                       | Ventas            |
| reference     | Referencia específica de línea (opcional)        | FAC-001-1         |

#### Datos de Ejemplo (Formato JSON)

```json
[
  {
    "entry_date": "2024-01-15",
    "reference": "FAC-001",
    "description": "Venta de mercadería",
    "entry_type": "MANUAL",
    "notes": "Venta al contado",
    "lines": [
      {
        "account_code": "1001",
        "description": "Ingreso en caja",
        "debit_amount": 1180.00,
        "credit_amount": 0.00,
        "reference": "FAC-001"
      },
      {
        "account_code": "4001",
        "description": "Ingreso por venta",
        "debit_amount": 0.00,
        "credit_amount": 1000.00,
        "reference": "FAC-001"
      },
      {
        "account_code": "2401",
        "description": "IVA cobrado",
        "debit_amount": 0.00,
        "credit_amount": 180.00,
        "reference": "FAC-001"
      }
    ]
  },
  {
    "entry_date": "2024-01-16",
    "reference": "COMP-001",
    "description": "Compra de suministros",
    "entry_type": "MANUAL",
    "notes": "Pago a 30 días",
    "lines": [
      {
        "account_code": "1501",
        "description": "Suministros de oficina",
        "debit_amount": 500.00,
        "credit_amount": 0.00,
        "reference": "COMP-001"
      },
      {
        "account_code": "1402",
        "description": "IVA pagado",
        "debit_amount": 90.00,
        "credit_amount": 0.00,
        "reference": "COMP-001"
      },
      {
        "account_code": "2105",
        "description": "Proveedor por pagar",
        "debit_amount": 0.00,
        "credit_amount": 590.00,
        "reference": "COMP-001",
        "third_party": "Proveedor XYZ"
      }
    ]
  }
]
```

## Formatos Soportados

### CSV (Valores Separados por Comas)

El CSV es un formato simple y ampliamente soportado para intercambio de datos tabulares.

#### Especificaciones para CSV:

- Delimitador: Coma (,)
- Codificación: UTF-8
- Primera fila debe contener los nombres de columnas
- Los valores pueden estar opcionalmente encerrados en comillas dobles
- Las fechas deben estar en formato YYYY-MM-DD

#### Formato CSV para Cuentas:

```
code,name,account_type,category,cash_flow_category,parent_code,description,is_active,allows_movements,requires_third_party,requires_cost_center,notes
1105,Caja General,ACTIVO,ACTIVO_CORRIENTE,cash,1100,Dinero en efectivo en caja principal,true,true,false,false,Cuenta para manejo de efectivo
1110,Bancos Moneda Nacional,ACTIVO,ACTIVO_CORRIENTE,cash,1100,Depósitos en bancos en moneda nacional,true,true,true,false,Requiere especificar el banco como tercero
2105,Proveedores Nacionales,PASIVO,PASIVO_CORRIENTE,operating,2100,Cuentas por pagar a proveedores nacionales,true,true,true,false,Requiere especificar el proveedor
```

#### Formato CSV para Asientos:

Para asientos contables en CSV, debido a su estructura jerárquica, cada línea de asiento es una fila independiente que se relaciona con la cabecera mediante un identificador o número de asiento:

```
entry_date,reference,description,entry_type,account_code,debit_amount,credit_amount,third_party
2024-01-15,FAC-001,Venta de mercadería,MANUAL,1001,1000.00,0.00,
2024-01-15,FAC-001,Venta de mercadería,MANUAL,4001,0.00,1000.00,
```

### XLSX (Excel)

El formato XLSX permite importación desde hojas de cálculo de Microsoft Excel.

#### Especificaciones para XLSX:

- Primera fila debe contener los nombres de columnas
- Se puede especificar la hoja a importar (default: primera hoja)
- Se puede especificar la fila de inicio para los encabezados (default: fila 1)
- Soporta múltiples hojas para datos relacionados

#### Características especiales de XLSX:

- **Documentación integrada**: La plantilla XLSX incluye una hoja adicional con documentación detallada sobre cada campo.
- **Validación de datos**: Las plantillas XLSX incluyen validaciones de datos integradas para ayudar en la captura correcta de información.
- **Formateo condicional**: Se incluye formateo visual para identificar campos requeridos y opcionales.

### JSON (JavaScript Object Notation)

El formato JSON es ideal para estructuras de datos jerárquicas y complejas.

#### Especificaciones para JSON:

- Debe ser un JSON válido
- Puede ser un array de objetos o un objeto con un array anidado
- Codificación: UTF-8
- Soporta estructura natural jerárquica para asientos contables

#### Formato JSON para Cuentas:

```json
[
  {
    "code": "1105",
    "name": "Caja General",
    "account_type": "ACTIVO",
    "category": "ACTIVO_CORRIENTE",
    "cash_flow_category": "cash",
    "parent_code": "1100",
    "description": "Dinero en efectivo en caja principal",
    "is_active": true,
    "allows_movements": true,
    "requires_third_party": false,
    "requires_cost_center": false,
    "notes": "Cuenta para manejo de efectivo - Efectivo y equivalentes"
  },
  {
    "code": "2105",
    "name": "Proveedores Nacionales",
    "account_type": "PASIVO",
    "category": "PASIVO_CORRIENTE",
    "cash_flow_category": "operating",
    "parent_code": "2100",
    "description": "Cuentas por pagar a proveedores nacionales",
    "is_active": true,
    "allows_movements": true,
    "requires_third_party": true,
    "requires_cost_center": false,
    "notes": "Requiere especificar el proveedor - Actividades operativas"
  }
]
```

#### Formato JSON para Asientos:

El formato JSON es particularmente adecuado para asientos contables debido a su capacidad para representar naturalmente la estructura jerárquica de cabecera y líneas:

```json
[
  {
    "entry_date": "2024-01-15",
    "reference": "FAC-001",
    "description": "Venta de mercadería",
    "entry_type": "MANUAL",
    "lines": [
      {
        "account_code": "1001",
        "description": "Ingreso en caja",
        "debit_amount": 1000.00,
        "credit_amount": 0.00
      },
      {
        "account_code": "4001",
        "description": "Ingreso por venta",
        "debit_amount": 0.00,
        "credit_amount": 1000.00
      }
    ]
  }
]
```

## Valores y Tipos Aceptados

### Tipos de Cuenta (account_type)

Los valores aceptados para el campo `account_type` son:

- `ACTIVO`: Representa los bienes y derechos de la empresa.
- `PASIVO`: Representa las obligaciones de la empresa.
- `PATRIMONIO`: Representa el capital y resultados de la empresa.
- `INGRESO`: Representa los ingresos o ventas.
- `GASTO`: Representa los gastos operativos y administrativos.
- `COSTOS`: Representa los costos de ventas o producción.

### Categorías de Cuenta (category)

Cada tipo de cuenta tiene categorías específicas aceptadas:

- Categorías para ACTIVO:
  - `ACTIVO_CORRIENTE`: Activos que se convertirán en efectivo en menos de un año.
  - `ACTIVO_NO_CORRIENTE`: Activos de largo plazo.

- Categorías para PASIVO:
  - `PASIVO_CORRIENTE`: Obligaciones a pagar en menos de un año.
  - `PASIVO_NO_CORRIENTE`: Obligaciones a largo plazo.

- Categorías para PATRIMONIO:
  - `CAPITAL`: Capital social aportado.
  - `RESERVAS`: Reservas legales y estatutarias.
  - `RESULTADOS`: Resultados acumulados y del ejercicio.

- Categorías para INGRESO:
  - `INGRESOS_OPERACIONALES`: Ingresos por actividades principales.
  - `INGRESOS_NO_OPERACIONALES`: Ingresos por actividades secundarias.

- Categorías para GASTO:
  - `GASTOS_OPERACIONALES`: Gastos relacionados a la operación principal.
  - `GASTOS_NO_OPERACIONALES`: Gastos no relacionados a la operación principal.

- Categorías para COSTOS:
  - `COSTO_VENTAS`: Costos directamente relacionados a las ventas.
  - `COSTOS_PRODUCCION`: Costos directamente relacionados a la producción.

### Categorías de Flujo de Efectivo (cash_flow_category)

Los valores aceptados para el campo `cash_flow_category` son:

- `operating`: Actividades de Operación - Incluye ingresos, gastos, costos y cuentas corrientes relacionadas con la operación principal del negocio.
- `investing`: Actividades de Inversión - Incluye activos fijos, equipos, propiedades y otras inversiones de capital.
- `financing`: Actividades de Financiamiento - Incluye préstamos, capital, dividendos y operaciones relacionadas con la estructura financiera.
- `cash`: Efectivo y Equivalentes - Incluye caja, bancos e inversiones temporales de alta liquidez.

> **Nota**: Esta clasificación es esencial para la generación automática de estados de flujo de efectivo conforme a las normas contables.

### Tipos de Asiento (entry_type)

Los valores aceptados para el campo `entry_type` son:

- `MANUAL`: Asiento ingresado manualmente por un usuario.
- `AUTOMATIC`: Asiento generado automáticamente por el sistema.
- `ADJUSTMENT`: Asiento de ajuste contable.
- `OPENING`: Asiento de apertura de ejercicio.
- `CLOSING`: Asiento de cierre de ejercicio.
- `REVERSAL`: Asiento de reversión de otro asiento.

## Reglas de Validación

### Validaciones para Cuentas

1. El código de cuenta debe ser único en el sistema.
2. El tipo de cuenta debe ser uno de los valores aceptados.
3. La categoría debe corresponder al tipo de cuenta.
4. Si se especifica `cash_flow_category`, debe ser uno de los valores válidos: operating, investing, financing, cash.
5. Si se especifica un código de cuenta padre, ésta debe existir previamente.
6. Una cuenta con `allows_movements` = false no puede tener movimientos directamente.

### Validaciones para Asientos

1. La fecha del asiento debe ser válida.
2. La descripción del asiento es obligatoria.
3. Cada asiento debe tener al menos 2 líneas.
4. El asiento debe estar balanceado (total débitos = total créditos).
5. Las cuentas referenciadas deben existir previamente en el sistema.
6. Una línea debe tener valor en débito O crédito, no ambos o ninguno.
7. Las cuentas que requieren tercero deben tener el campo tercero especificado.
8. Las cuentas que requieren centro de costo deben tener el campo centro de costo especificado.

## Recomendaciones para Preparación de Datos

1. **Utilizar las plantillas proporcionadas** como punto de partida para garantizar la estructura correcta.
2. **Verificar la integridad de los datos** antes de intentar importarlos:
   - Códigos de cuenta válidos y existentes
   - Asientos balanceados (débito = crédito)
   - Fechas en formato correcto

3. **Dividir archivos grandes** en múltiples archivos más pequeños para mejor rendimiento y facilidad de diagnóstico en caso de errores.

4. **Revisar la codificación de caracteres** especialmente al trabajar con CSV, asegurando que se use UTF-8.

5. **Realizar importaciones de prueba** con un conjunto pequeño de datos antes de proceder con el conjunto completo.

## Descarga de Plantillas

Las plantillas pueden descargarse a través de los siguientes endpoints de la API:

- Plantillas generales: `GET /api/v1/import/templates/{data_type}/download?format={format}`
- Plantilla de cuentas: `GET /api/v1/import/templates/accounts/{format}`

Donde:
- `{data_type}` puede ser `accounts` o `journal_entries`
- `{format}` puede ser `csv`, `xlsx` o `json`
