# Tipos y Categorías de Cuentas

## Descripción General

El sistema de cuentas contables utiliza una clasificación estructurada para organizar las cuentas según su naturaleza contable. Esta clasificación se basa en dos niveles principales: **Tipos de Cuenta** y **Categorías**, que permiten organizar el plan contable de manera coherente y facilitar la generación de estados financieros.

## Tipos Fundamentales de Cuentas

Los tipos de cuenta están definidos como un enum `AccountType` y representan las clasificaciones fundamentales en contabilidad:

```python
class AccountType(str, Enum):
    """Tipos de cuentas contables según la naturaleza contable"""
    ACTIVO = "activo"
    PASIVO = "pasivo"
    PATRIMONIO = "patrimonio"
    INGRESO = "ingreso"
    GASTO = "gasto"
    COSTOS = "costos"
```

### Características por Tipo de Cuenta

#### ACTIVO
- **Naturaleza**: Deudora (aumenta con débito)
- **Representa**: Recursos controlados por la entidad
- **Ubicación**: Balance General (lado izquierdo)
- **Saldo normal**: Deudor (débito > crédito)
- **Ejemplos**: Efectivo, Bancos, Inventarios, Activos Fijos

#### PASIVO
- **Naturaleza**: Acreedora (aumenta con crédito)
- **Representa**: Obligaciones de la entidad
- **Ubicación**: Balance General (lado derecho)
- **Saldo normal**: Acreedor (crédito > débito)
- **Ejemplos**: Préstamos, Proveedores, Impuestos por Pagar

#### PATRIMONIO
- **Naturaleza**: Acreedora (aumenta con crédito)
- **Representa**: Capital y resultados acumulados
- **Ubicación**: Balance General (lado derecho)
- **Saldo normal**: Acreedor (crédito > débito)
- **Ejemplos**: Capital Social, Utilidades Retenidas, Reservas

#### INGRESO
- **Naturaleza**: Acreedora (aumenta con crédito)
- **Representa**: Incrementos en el patrimonio por operaciones
- **Ubicación**: Estado de Resultados
- **Saldo normal**: Acreedor (crédito > débito)
- **Ejemplos**: Ventas, Servicios Prestados, Intereses Ganados

#### GASTO
- **Naturaleza**: Deudora (aumenta con débito)
- **Representa**: Disminuciones en el patrimonio por operaciones
- **Ubicación**: Estado de Resultados
- **Saldo normal**: Deudor (débito > crédito)
- **Ejemplos**: Sueldos, Arriendos, Servicios, Depreciación

#### COSTOS
- **Naturaleza**: Deudora (aumenta con débito)
- **Representa**: Inversión para producir bienes/servicios
- **Ubicación**: Estado de Resultados
- **Saldo normal**: Deudor (débito > crédito)
- **Ejemplos**: Materia Prima, Mano de Obra Directa

## Categorías de Cuentas

Las categorías proporcionan una clasificación más específica dentro de cada tipo de cuenta, facilitando la organización y reportes:

```python
class AccountCategory(str, Enum):
    """Categorías principales para clasificación de cuentas"""
    # Activos
    ACTIVO_CORRIENTE = "activo_corriente"
    ACTIVO_NO_CORRIENTE = "activo_no_corriente"
    
    # Pasivos
    PASIVO_CORRIENTE = "pasivo_corriente"
    PASIVO_NO_CORRIENTE = "pasivo_no_corriente"
    
    # Patrimonio
    CAPITAL = "capital"
    RESERVAS = "reservas"
    RESULTADOS = "resultados"
    
    # Ingresos
    INGRESOS_OPERACIONALES = "ingresos_operacionales"
    INGRESOS_NO_OPERACIONALES = "ingresos_no_operacionales"
    
    # Gastos
    GASTOS_OPERACIONALES = "gastos_operacionales"
    GASTOS_NO_OPERACIONALES = "gastos_no_operacionales"
    
    # Costos
    COSTO_VENTAS = "costo_ventas"
    COSTOS_PRODUCCION = "costos_produccion"
```

### Detalle de Categorías

#### Categorías de Activo
- **ACTIVO_CORRIENTE**: Activos que se esperan convertir en efectivo o consumirse en un plazo menor a un año
  - Ejemplos: Efectivo, Cuentas por Cobrar, Inventarios
  - Plazo: Corto plazo (< 12 meses)

- **ACTIVO_NO_CORRIENTE**: Activos de larga duración destinados al uso de la entidad
  - Ejemplos: Propiedades, Planta y Equipo, Intangibles
  - Plazo: Largo plazo (> 12 meses)

#### Categorías de Pasivo
- **PASIVO_CORRIENTE**: Obligaciones que se espera liquidar en el ciclo normal de operación
  - Ejemplos: Cuentas por Pagar, Impuestos por Pagar
  - Plazo: Corto plazo (< 12 meses)

- **PASIVO_NO_CORRIENTE**: Obligaciones con vencimiento superior a un año
  - Ejemplos: Préstamos a Largo Plazo, Provisiones
  - Plazo: Largo plazo (> 12 meses)

#### Categorías de Patrimonio
- **CAPITAL**: Aportes directos de los propietarios
  - Ejemplos: Capital Social, Acciones Preferentes

- **RESERVAS**: Ganancias retenidas para fines específicos
  - Ejemplos: Reserva Legal, Reserva Estatutaria

- **RESULTADOS**: Ganancias o pérdidas acumuladas
  - Ejemplos: Utilidades Retenidas, Resultados del Ejercicio

#### Categorías de Ingresos
- **INGRESOS_OPERACIONALES**: Derivados de la actividad principal
  - Ejemplos: Ventas de Mercaderías, Prestación de Servicios

- **INGRESOS_NO_OPERACIONALES**: No relacionados con la actividad principal
  - Ejemplos: Intereses Financieros, Ganancia en Venta de Activos

#### Categorías de Gastos
- **GASTOS_OPERACIONALES**: Relacionados con la operación normal
  - Ejemplos: Sueldos, Arriendos, Servicios

- **GASTOS_NO_OPERACIONALES**: No relacionados con la operación normal
  - Ejemplos: Intereses Pagados, Pérdidas por Venta de Activos

#### Categorías de Costos
- **COSTO_VENTAS**: Costo de productos vendidos o servicios prestados
  - Ejemplos: Costo de Mercaderías Vendidas

- **COSTOS_PRODUCCION**: Costos incurridos en el proceso productivo
  - Ejemplos: Materias Primas, Mano de Obra, CIF

## Comportamiento del Saldo

El sistema incluye lógica para determinar el comportamiento del saldo según el tipo de cuenta:

```python
@property
def normal_balance_side(self) -> str:
    """Retorna el lado normal del balance para esta cuenta"""
    if self.account_type in [AccountType.ACTIVO, AccountType.GASTO, AccountType.COSTOS]:
        return "debit"
    else:  # PASIVO, PATRIMONIO, INGRESO
        return "credit"

@property
def increases_with(self) -> str:
    """Retorna con qué lado aumenta el saldo de la cuenta"""
    return self.normal_balance_side
    
@property
def decreases_with(self) -> str:
    """Retorna con qué lado disminuye el saldo de la cuenta"""
    return "credit" if self.normal_balance_side == "debit" else "debit"
```

### Tabla de Comportamiento de Saldos

| Tipo de Cuenta | Saldo Normal | Aumenta Con | Disminuye Con | Presentación de Saldo |
|----------------|--------------|-------------|---------------|----------------------|
| ACTIVO         | Deudor       | Débito      | Crédito       | Débito - Crédito     |
| PASIVO         | Acreedor     | Crédito     | Débito        | Crédito - Débito     |
| PATRIMONIO     | Acreedor     | Crédito     | Débito        | Crédito - Débito     |
| INGRESO        | Acreedor     | Crédito     | Débito        | Crédito - Débito     |
| GASTO          | Deudor       | Débito      | Crédito       | Débito - Crédito     |
| COSTOS         | Deudor       | Débito      | Crédito       | Débito - Crédito     |

## Validaciones por Tipo de Cuenta

El sistema implementa validaciones específicas según el tipo de cuenta:

1. **Coherencia Jerárquica**: Una cuenta solo puede tener hijos del mismo tipo
   ```python
   if parent_account.account_type != account_data.account_type:
       raise AccountValidationError("La cuenta debe ser del mismo tipo que su cuenta padre")
   ```

2. **Validaciones de Categoría**: La categoría debe ser coherente con el tipo de cuenta
   ```python
   if account_data.category and not account_data.category.name.startswith(account_data.account_type.name):
       raise AccountValidationError("La categoría debe corresponder al tipo de cuenta")
   ```

3. **Restricciones de Movimiento**: Validaciones específicas para permitir movimientos
   ```python
   def validate_movement_allowed(self) -> bool:
       if not self.is_active:
           raise ValueError(f"La cuenta {self.code} - {self.name} está inactiva")
       
       if not self.allows_movements:
           raise ValueError(f"La cuenta {self.code} - {self.name} no permite movimientos")
       
       if not self.is_leaf_account:
           raise ValueError(f"La cuenta {self.code} - {self.name} es una cuenta padre y no puede recibir movimientos")
       
       return True
   ```

## Estructura Jerárquica

El sistema permite organizar las cuentas en una estructura jerárquica, donde:

- Cada tipo de cuenta tiene sus propias cuentas padre (nivel 1)
- Las cuentas padre pueden tener subcuentas (niveles 2, 3, etc.)
- Las cuentas hoja son las que reciben movimientos contables
- La jerarquía se refleja en los códigos (ej: "1" → "1.1" → "1.1.01")

### Ejemplo de Estructura

```
ACTIVO (1)
├── ACTIVO CORRIENTE (1.1)
│   ├── EFECTIVO Y EQUIVALENTES (1.1.01)
│   │   ├── CAJA GENERAL (1.1.01.01)
│   │   ├── BANCO CUENTA CORRIENTE (1.1.01.02)
│   ├── CUENTAS POR COBRAR (1.1.02)
│       ├── CLIENTES NACIONALES (1.1.02.01)
│       ├── CLIENTES EXTRANJEROS (1.1.02.02)
├── ACTIVO NO CORRIENTE (1.2)
    ├── PROPIEDAD PLANTA Y EQUIPO (1.2.01)
        ├── EDIFICIOS (1.2.01.01)
        ├── EQUIPOS DE CÓMPUTO (1.2.01.02)
```

## Categorías de Flujo de Efectivo

Además de la clasificación tradicional por tipo y categoría, el sistema incluye una clasificación especial para el Estado de Flujo de Efectivo:

### CashFlowCategory

```python
class CashFlowCategory(str, Enum):
    """Categorías para clasificar cuentas según actividades del flujo de efectivo"""
    OPERATING = "operating"        # Actividades de Operación
    INVESTING = "investing"        # Actividades de Inversión  
    FINANCING = "financing"        # Actividades de Financiamiento
    CASH_EQUIVALENTS = "cash"      # Efectivo y Equivalentes de Efectivo
```

### Relación con Tipos de Cuenta

| Tipo de Cuenta | Categoría Típica de Flujo | Ejemplos |
|----------------|---------------------------|----------|
| ACTIVO (Corriente) | CASH_EQUIVALENTS o OPERATING | Caja, Bancos, Cuentas por Cobrar |
| ACTIVO (No Corriente) | INVESTING | Equipos, Propiedades, Inversiones |
| PASIVO (Corriente) | OPERATING | Proveedores, Gastos Acumulados |
| PASIVO (No Corriente) | FINANCING | Préstamos a Largo Plazo |
| PATRIMONIO | FINANCING | Capital Social, Utilidades Retenidas |
| INGRESO | OPERATING | Ventas, Servicios |
| GASTO | OPERATING | Sueldos, Arriendos, Servicios |
| COSTOS | OPERATING | Costo de Ventas |

### Configuración Recomendada

```python
# Ejemplos de configuración por actividad

# ACTIVIDADES OPERATIVAS
cuentas_operativas = [
    {"code": "4001", "name": "Ventas", "type": "INGRESO", "cash_flow": "operating"},
    {"code": "5001", "name": "Sueldos", "type": "GASTO", "cash_flow": "operating"},
    {"code": "1102", "name": "Clientes", "type": "ACTIVO", "cash_flow": "operating"},
    {"code": "2101", "name": "Proveedores", "type": "PASIVO", "cash_flow": "operating"}
]

# ACTIVIDADES DE INVERSIÓN
cuentas_inversion = [
    {"code": "1201", "name": "Equipos", "type": "ACTIVO", "cash_flow": "investing"},
    {"code": "1202", "name": "Propiedades", "type": "ACTIVO", "cash_flow": "investing"},
    {"code": "1301", "name": "Inversiones LP", "type": "ACTIVO", "cash_flow": "investing"}
]

# ACTIVIDADES DE FINANCIAMIENTO
cuentas_financiamiento = [
    {"code": "2201", "name": "Préstamos LP", "type": "PASIVO", "cash_flow": "financing"},
    {"code": "3001", "name": "Capital Social", "type": "PATRIMONIO", "cash_flow": "financing"},
    {"code": "3002", "name": "Utilidades Retenidas", "type": "PATRIMONIO", "cash_flow": "financing"}
]

# EFECTIVO Y EQUIVALENTES
cuentas_efectivo = [
    {"code": "1101", "name": "Caja", "type": "ACTIVO", "cash_flow": "cash"},
    {"code": "1102", "name": "Bancos", "type": "ACTIVO", "cash_flow": "cash"},
    {"code": "1103", "name": "Inversiones Temporales", "type": "ACTIVO", "cash_flow": "cash"}
]
```

## Buenas Prácticas

1. **Consistencia en Codificación**: Mantener un sistema coherente de codificación por tipo
2. **Niveles Adecuados**: No crear jerarquías excesivamente profundas (3-4 niveles suele ser suficiente)
3. **Categorización Correcta**: Asignar la categoría adecuada para facilitar reportes
4. **Cuentas Hoja**: Solo las cuentas hoja deben recibir movimientos directos
5. **Nombres Descriptivos**: Usar nombres claros que indiquen el propósito de la cuenta
6. **Categorización de Flujo de Efectivo**: Asignar la categoría `cash_flow_category` apropiada para facilitar la generación automática del Estado de Flujo de Efectivo
