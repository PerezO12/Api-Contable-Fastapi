# Gestión de Cuentas Contables

## Descripción General

El sistema de gestión de cuentas contables constituye el núcleo del API Contable, permitiendo la definición, organización y administración de todas las cuentas que conforman el plan contable de la organización. Este componente implementa una estructura jerárquica que permite representar la relación padre-hijo entre cuentas, facilitando la organización por niveles y la consolidación de saldos.

## Modelo de Datos

### Estructura Principal

El modelo `Account` es la entidad principal y tiene las siguientes características:

- **Campos de Identificación**:
  - `id`: Identificador único UUID
  - `code`: Código alfanumérico único (hasta 20 caracteres)
  - `name`: Nombre descriptivo (hasta 200 caracteres)
  - `description`: Descripción opcional detallada

- **Clasificación Contable**:
  - `account_type`: Tipo fundamental (ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS)
  - `category`: Categoría específica dentro del tipo (ej: ACTIVO_CORRIENTE, PASIVO_NO_CORRIENTE)
  
- **Estructura Jerárquica**:
  - `parent_id`: Referencia a la cuenta padre (opcional)
  - `level`: Nivel en la jerarquía (1 para cuentas raíz, incrementa por nivel)
  - `children`: Relación con cuentas hijas

- **Control y Configuración**:
  - `is_active`: Estado activo/inactivo de la cuenta
  - `allows_movements`: Indica si la cuenta puede recibir movimientos directos
  - `requires_third_party`: Indica si los movimientos requieren asociación con terceros
  - `requires_cost_center`: Indica si los movimientos requieren centro de costo

- **Saldos y Balances**:
  - `balance`: Saldo neto actual (considerando la naturaleza de la cuenta)
  - `debit_balance`: Acumulado de débitos
  - `credit_balance`: Acumulado de créditos

- **Metadatos y Auditoría**:
  - `notes`: Notas adicionales sobre la cuenta
  - `created_by_id`: Usuario que creó la cuenta
  - `created_at`: Fecha de creación
  - `updated_at`: Fecha de última actualización

## Propiedades Calculadas

El modelo incluye varias propiedades calculadas que facilitan su uso:

- **`full_code`**: Código completo incluyendo la jerarquía (ej: "1.1.02")
- **`full_name`**: Nombre completo con la ruta jerárquica (ej: "Activo > Activo Corriente > Bancos")
- **`is_parent_account`**: Determina si la cuenta tiene cuentas hijas
- **`is_leaf_account`**: Determina si es una cuenta hoja (sin hijos)
- **`can_receive_movements`**: Verifica si la cuenta puede recibir asientos contables
- **`normal_balance_side`**: Lado normal del balance ("debit" o "credit" según el tipo)
- **`increases_with`**: Operación que aumenta el saldo
- **`decreases_with`**: Operación que disminuye el saldo

## Operaciones CRUD

### Creación de Cuentas

La creación de cuentas implementa varias validaciones para mantener la integridad del plan contable:

```python
async def create_account(account_data: AccountCreate, created_by_id: uuid.UUID) -> Account:
    # Validaciones
    # 1. Código único
    # 2. Verificación de cuenta padre
    # 3. Compatibilidad de tipo con la cuenta padre
    # 4. Formato de código válido
    # ...
    
    # Crear cuenta con nivel adecuado
    account = Account(
        code=account_data.code,
        name=account_data.name,
        # ...otros campos
        level=parent_account.level + 1 if parent_account else 1,
    )
    
    # Guardar y retornar
    # ...
```

### Consulta de Cuentas

El sistema permite consultar cuentas con diversos filtros:

- Por ID o código específico
- Por tipo de cuenta o categoría
- Por estado activo/inactivo
- Por cuenta padre (estructura jerárquica)
- Por texto de búsqueda (en código, nombre o descripción)

### Actualización de Cuentas

La actualización de cuentas permite modificar atributos manteniendo la integridad:

- No se permite cambiar el código (identificador de negocio)
- No se permite cambiar el tipo de cuenta
- No se permite cambiar la relación jerárquica (padre-hijo)
- Se actualizan metadatos y configuraciones
- Se registra la fecha de actualización

### Eliminación de Cuentas

La eliminación de cuentas está restringida para mantener la integridad histórica:

- Solo administradores pueden eliminar cuentas
- Solo se pueden eliminar cuentas sin movimientos
- No se pueden eliminar cuentas que tienen hijos
- Se recomienda inactivar en lugar de eliminar

## Validaciones de Negocio

Las principales validaciones implementadas incluyen:

1. **Unicidad de Código**: Cada cuenta debe tener un código único en todo el plan
2. **Coherencia Jerárquica**: Las cuentas hijas deben ser del mismo tipo que su cuenta padre
3. **Formato de Código**: Se valida el formato permitido (letras, números, puntos, guiones)
4. **Movimientos**: Solo cuentas hoja pueden recibir movimientos directos
5. **Integridad Referencial**: No se pueden eliminar cuentas con movimientos o relaciones
6. **Validaciones de Nombre**: Normalizados automáticamente (primera letra mayúscula, espacios)

## Ejemplos de Uso

### Ejemplo 1: Crear una estructura jerárquica de cuentas

```python
# 1. Crear cuenta padre
cuenta_activo = {
    "code": "1",
    "name": "Activos",
    "account_type": "ACTIVO",
    "category": "ACTIVO_CORRIENTE",
    "allows_movements": False  # Cuenta padre, no permite movimientos directos
}

# 2. Crear subcuenta
cuenta_banco = {
    "code": "1.1",
    "name": "Bancos",
    "account_type": "ACTIVO",
    "category": "ACTIVO_CORRIENTE", 
    "parent_id": "id-de-cuenta-activo",
    "allows_movements": True  # Cuenta hoja, permite movimientos
}
```

### Ejemplo 2: Consultar saldo de una cuenta

```python
# Obtener saldo con fecha específica
saldo = await account_service.get_account_balance(
    account_id=uuid.UUID("cuenta-id"),
    as_of_date=date(2025, 6, 10)
)

# El resultado incluye:
# - Saldo deudor
# - Saldo acreedor
# - Saldo neto según naturaleza
# - Lado normal del balance
```

## Integración con Otros Módulos

El sistema de cuentas se integra con:

- **Asientos Contables**: Para registrar movimientos y actualizar saldos
- **Usuarios**: Para control de acceso y auditoría
- **Reportes**: Para generar estados financieros y análisis

## Buenas Prácticas

1. **Estructura Coherente**: Mantener una estructura jerárquica lógica y ordenada
2. **Códigos Significativos**: Utilizar un sistema de codificación que refleje la jerarquía
3. **Cuentas Específicas**: Crear cuentas suficientemente específicas para el análisis
4. **Inactivar vs Eliminar**: Preferir inactivar cuentas en lugar de eliminarlas
5. **Documentación**: Utilizar los campos de descripción y notas para documentar el propósito
