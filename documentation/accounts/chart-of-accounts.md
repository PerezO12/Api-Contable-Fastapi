# Plan de Cuentas

## Descripción General

El Plan de Cuentas es una estructura organizada y codificada que representa todas las cuentas utilizadas en el sistema contable. Proporciona un marco para clasificar, registrar y reportar las transacciones financieras de manera coherente y sistemática. En el API Contable, el plan de cuentas implementa una estructura jerárquica que permite una organización lógica y facilita la consolidación de información financiera.

## Estructura Jerárquica

El sistema implementa un modelo jerárquico donde:

1. **Cuentas de Nivel 1**: Representan las grandes clasificaciones (Activos, Pasivos, etc.)
2. **Cuentas Intermedias**: Organizan subcategorías (Activo Corriente, Activo No Corriente)
3. **Cuentas Operativas**: Cuentas de nivel inferior que reciben los movimientos contables

Esta estructura se implementa en el modelo `Account` con las siguientes relaciones:

```python
class Account(Base):
    # ...
    
    # Jerarquía
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relaciones
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side="Account.id")
    children: Mapped[List["Account"]] = relationship("Account", back_populates="parent")
```

### Propiedades de la Estructura

- **Relación Padre-Hijo**: Cada cuenta puede tener una cuenta padre y múltiples cuentas hijas
- **Nivel Jerárquico**: El nivel se incrementa automáticamente (nivel padre + 1)
- **Código Compuesto**: Los códigos reflejan la jerarquía (ej: 1.1.01)
- **Nombre Completo**: Incluye la ruta jerárquica completa (ej: "Activo > Activo Corriente > Bancos")

## Representación en Árbol

El sistema provee una función para obtener la estructura completa en formato de árbol:

```python
@router.get("/tree", response_model=List[AccountTree])
async def get_account_tree(
    account_type: Optional[AccountType] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AccountTree]:
    """
    Obtener la estructura jerárquica de cuentas como árbol.
    """
    account_service = AccountService(db)
    return await account_service.get_account_tree_fixed(account_type=account_type, active_only=active_only)
```

### Esquema de Árbol

```python
class AccountTree(BaseModel):
    """Schema para representar la jerarquía de cuentas"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    code: str
    name: str
    account_type: AccountType
    level: int
    balance: Decimal
    is_active: bool
    allows_movements: bool
    children: List['AccountTree'] = Field(default_factory=list)
```

Esta estructura permite visualizar el plan completo con sus relaciones jerárquicas y saldos consolidados.

## Códigos y Nomenclatura

El sistema implementa una convención de codificación para las cuentas:

- **Formato**: Alfanumérico con puntos como separadores jerárquicos
- **Longitud**: Hasta 20 caracteres, típicamente en formato X.Y.ZZ
- **Unicidad**: Cada código debe ser único en todo el sistema
- **Validación**: Se aplican validaciones para garantizar la coherencia

```python
@field_validator('code')
@classmethod
def validate_code_format(cls, v):
    """Valida el formato del código de cuenta"""
    # Solo permitir letras, números, puntos y guiones
    if not v.replace('.', '').replace('-', '').replace('_', '').isalnum():
        raise ValueError("El código solo puede contener letras, números, puntos, guiones y guiones bajos")
    return v.upper()  # Convertir a mayúsculas
```

### Ejemplos de Codificación

| Nivel | Ejemplo de Código | Descripción |
|-------|------------------|-------------|
| 1     | 1                | Activos (cuenta principal) |
| 2     | 1.1              | Activo Corriente (subcategoría) |
| 3     | 1.1.01           | Efectivo y Equivalentes (grupo) |
| 4     | 1.1.01.01        | Caja General (cuenta operativa) |

## Importación y Exportación

El sistema proporciona funciones para la importación y exportación del plan de cuentas:

### Importación

```python
@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_accounts(
    file_content: str,  # En producción usar UploadFile de FastAPI
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> dict:
    """
    Importar cuentas desde archivo CSV/Excel.
    Solo disponible para administradores.
    """
    account_service = AccountService(db)
    return await account_service.import_accounts_from_csv(file_content, current_user.id)
```

#### Esquema de Importación

```python
class AccountImport(BaseModel):
    """Schema para importar cuentas desde archivos"""
    code: str
    name: str
    account_type: str
    category: Optional[str] = None
    parent_code: Optional[str] = None
    description: Optional[str] = None
```

### Exportación

```python
@router.get("/export/csv")
async def export_accounts_csv(
    account_type: Optional[AccountType] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exportar cuentas a formato CSV.
    """
    account_service = AccountService(db)
    return await account_service.export_accounts_to_csv(account_type, active_only)
```

#### Esquema de Exportación

```python
class AccountExport(BaseModel):
    """Schema para exportar cuentas"""
    code: str
    name: str
    full_name: str
    account_type: str
    category: Optional[str]
    parent_code: Optional[str]
    level: int
    balance: Decimal
    is_active: bool
    allows_movements: bool
```

## Consulta de Estructura

El sistema proporciona endpoints específicos para consultar la estructura del plan:

### Plan de Cuentas Completo

```python
@router.get("/chart", response_model=ChartOfAccounts)
async def get_chart_of_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChartOfAccounts:
    """
    Obtener el plan de cuentas completo organizado por tipo.
    """
    account_service = AccountService(db)
    return await account_service.get_chart_of_accounts()
```

#### Esquema de Respuesta

```python
class ChartOfAccounts(BaseModel):
    """Schema para plan de cuentas completo"""
    by_type: List[AccountsByType]
    total_accounts: int
    active_accounts: int
    leaf_accounts: int
```

### Cuentas por Tipo

```python
@router.get("/type/{account_type}", response_model=AccountsByType)
async def get_accounts_by_type(
    account_type: AccountType,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountsByType:
    """
    Obtener todas las cuentas de un tipo específico.
    """
    account_service = AccountService(db)
    return await account_service.get_accounts_by_type(account_type, active_only)
```

## Manejo de Saldos Consolidados

El sistema permite calcular saldos consolidados para cuentas padre, sumando los saldos de todas sus cuentas hijas:

```python
def calculate_total_balance(self) -> Decimal:
    """
    Calcula el balance total incluyendo todas las cuentas hijas
    """
    total = Decimal(str(self.balance))
    for child in self.children:
        total += child.calculate_total_balance()
    return total
```

Este cálculo recursivo permite obtener el saldo de una cuenta incluyendo la suma de todas sus subcuentas.

### Validación de Integridad

El sistema implementa validaciones para mantener la integridad del plan de cuentas:

1. **Coherencia de Tipos**: Las cuentas hijas deben ser del mismo tipo que la cuenta padre
2. **Validación de Movimientos**: Solo las cuentas hoja (sin hijos) pueden recibir movimientos directos
3. **Unicidad de Códigos**: No puede haber dos cuentas con el mismo código
4. **Estructura Jerárquica**: La cuenta padre debe existir antes de crear una cuenta hija
5. **Saldo Coherente**: Los saldos consolidados deben reflejar la suma de los movimientos
6. **Categorización de Flujo de Efectivo**: Las cuentas deben tener una categoría de flujo asignada para reportes automáticos

## Configuración para Flujo de Efectivo

El plan de cuentas incluye configuración especial para la generación automática del Estado de Flujo de Efectivo:

### Categorización Automática

```python
# Reglas de categorización por patrones de código
categorization_rules = {
    CashFlowCategory.CASH_EQUIVALENTS: [
        "1.1.01",  # Efectivo y equivalentes
        "caja", "banco", "inversiones temporales"
    ],
    CashFlowCategory.OPERATING: [
        "tipo:INGRESO",     # Todos los ingresos
        "tipo:GASTO",       # Todos los gastos
        "tipo:COSTOS",      # Todos los costos
        "1.1.02",           # Cuentas por cobrar
        "2.1"               # Pasivos corrientes
    ],
    CashFlowCategory.INVESTING: [
        "1.2",              # Activos no corrientes
        "equipos", "propiedades", "inversiones"
    ],
    CashFlowCategory.FINANCING: [
        "2.2",              # Pasivos no corrientes
        "3.",               # Patrimonio
        "prestamos", "capital", "dividendos"
    ]
}
```

### Validación de Configuración

```python
async def validate_cash_flow_configuration():
    """Validar que el plan de cuentas esté configurado correctamente para flujo de efectivo"""
    
    # Verificar cuentas de efectivo
    cash_accounts = await get_accounts_by_cash_flow_category(CashFlowCategory.CASH_EQUIVALENTS)
    if not cash_accounts:
        raise ValidationError("No hay cuentas configuradas como efectivo y equivalentes")
    
    # Verificar categorización por tipo
    for account_type in [AccountType.INGRESO, AccountType.GASTO]:
        uncategorized = await get_uncategorized_accounts_by_type(account_type)
        if uncategorized:
            logger.warning(f"Cuentas {account_type} sin categoría de flujo: {len(uncategorized)}")
    
    return True
```

### Migración y Actualización

```sql
-- Script SQL para categorizar cuentas existentes
UPDATE accounts SET cash_flow_category = 'cash' 
WHERE code LIKE '1.1.01%' OR LOWER(name) LIKE '%caja%' OR LOWER(name) LIKE '%banco%';

UPDATE accounts SET cash_flow_category = 'operating' 
WHERE account_type IN ('INGRESO', 'GASTO', 'COSTOS');

UPDATE accounts SET cash_flow_category = 'investing' 
WHERE code LIKE '1.2%' AND account_type = 'ACTIVO';

UPDATE accounts SET cash_flow_category = 'financing' 
WHERE code LIKE '2.2%' OR code LIKE '3.%';
```

## Reportes por Tipo de Cuenta

El sistema permite generar reportes agrupados por tipo de cuenta:

```python
@router.get("/stats", response_model=AccountStats)
async def get_account_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountStats:
    """
    Obtener estadísticas generales de las cuentas.
    """
    account_service = AccountService(db)
    return await account_service.get_account_stats()
```

### Esquema de Estadísticas

```python
class AccountStats(BaseModel):
    """Schema para estadísticas de cuentas"""
    total_accounts: int
    active_accounts: int
    inactive_accounts: int
    by_type: dict[str, int]
    by_category: dict[str, int]
    accounts_with_movements: int
    accounts_without_movements: int
```

## Ejemplos y Casos de Uso

### Ejemplo 1: Plan de Cuentas Básico

```
1. ACTIVOS
   1.1 Activo Corriente
       1.1.01 Efectivo y Equivalentes
           1.1.01.01 Caja General
           1.1.01.02 Banco ABC Cuenta Corriente
       1.1.02 Cuentas por Cobrar
           1.1.02.01 Clientes Nacionales
   1.2 Activo No Corriente
       1.2.01 Propiedad, Planta y Equipo
           1.2.01.01 Edificios
           1.2.01.02 (-) Depreciación Acumulada Edificios

2. PASIVOS
   2.1 Pasivo Corriente
       2.1.01 Cuentas por Pagar
           2.1.01.01 Proveedores Nacionales
   2.2 Pasivo No Corriente
       2.2.01 Préstamos Bancarios LP

3. PATRIMONIO
   3.1 Capital
       3.1.01 Capital Social
   3.2 Resultados
       3.2.01 Utilidad del Ejercicio

4. INGRESOS
   4.1 Ingresos Operacionales
       4.1.01 Ventas de Mercadería

5. GASTOS
   5.1 Gastos Operacionales
       5.1.01 Sueldos y Salarios

6. COSTOS
   6.1 Costo de Ventas
       6.1.01 Costo de Mercadería Vendida
```

### Ejemplo 2: Plan de Cuentas con Categorías de Flujo de Efectivo

```json
{
  "accounts": [
    {
      "code": "1.1.01.01",
      "name": "Caja General",
      "account_type": "ACTIVO",
      "category": "ACTIVO_CORRIENTE",
      "cash_flow_category": "cash",
      "description": "Efectivo en caja para operaciones diarias"
    },
    {
      "code": "1.1.01.02", 
      "name": "Banco Cuenta Corriente",
      "account_type": "ACTIVO",
      "category": "ACTIVO_CORRIENTE",
      "cash_flow_category": "cash",
      "description": "Depósitos bancarios de disponibilidad inmediata"
    },
    {
      "code": "1.1.02.01",
      "name": "Clientes Nacionales",
      "account_type": "ACTIVO",
      "category": "ACTIVO_CORRIENTE", 
      "cash_flow_category": "operating",
      "description": "Cuentas por cobrar de ventas a crédito"
    },
    {
      "code": "1.2.01.01",
      "name": "Equipos de Oficina",
      "account_type": "ACTIVO",
      "category": "ACTIVO_NO_CORRIENTE",
      "cash_flow_category": "investing",
      "description": "Mobiliario y equipos para uso operativo"
    },
    {
      "code": "2.1.01.01",
      "name": "Proveedores Nacionales",
      "account_type": "PASIVO",
      "category": "PASIVO_CORRIENTE",
      "cash_flow_category": "operating",
      "description": "Obligaciones por compras a crédito"
    },
    {
      "code": "2.2.01.01",
      "name": "Préstamo Bancario LP",
      "account_type": "PASIVO", 
      "category": "PASIVO_NO_CORRIENTE",
      "cash_flow_category": "financing",
      "description": "Financiamiento bancario a largo plazo"
    },
    {
      "code": "3.1.01.01",
      "name": "Capital Social",
      "account_type": "PATRIMONIO",
      "category": "CAPITAL",
      "cash_flow_category": "financing",
      "description": "Aportes de los socios"
    },
    {
      "code": "4.1.01.01",
      "name": "Ventas de Productos",
      "account_type": "INGRESO",
      "category": "INGRESOS_OPERACIONALES",
      "cash_flow_category": "operating",
      "description": "Ingresos por venta de mercaderías"
    },
    {
      "code": "5.1.01.01",
      "name": "Sueldos y Salarios",
      "account_type": "GASTO",
      "category": "GASTOS_OPERACIONALES", 
      "cash_flow_category": "operating",
      "description": "Remuneraciones del personal"
    }
  ]
}
```

### Ejemplo 3: Consultar Estructura Jerárquica

```python
# Solicitud para obtener el árbol de cuentas de tipo ACTIVO
response = client.get(
    "/api/v1/accounts/tree?account_type=ACTIVO&active_only=true",
    headers={"Authorization": f"Bearer {token}"}
)

# El resultado es una estructura anidada que refleja la jerarquía
```

## Buenas Prácticas

1. **Codificación Coherente**: Utilizar un sistema de codificación consistente
2. **Nivel de Detalle**: Equilibrar entre demasiado detalle y poca especificidad
3. **Homogeneidad**: Mantener el mismo nivel de detalle para cuentas similares
4. **Nomenclatura Clara**: Usar nombres descriptivos y consistentes
5. **Mantenimiento**: Revisar periódicamente la estructura para adaptarla a nuevas necesidades
6. **Documentación**: Mantener descripciones claras de cada cuenta
7. **Validación**: Implementar controles para mantener la integridad del plan
