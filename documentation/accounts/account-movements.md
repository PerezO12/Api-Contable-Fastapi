# Movimientos de Cuentas

## Descripción General

Los movimientos de cuentas representan los cambios en los saldos de las cuentas contables generados por las transacciones financieras. Cada movimiento está vinculado a una cuenta contable y forma parte de un asiento contable (journal entry). El sistema registra, valida y permite consultar estos movimientos para mantener la integridad del estado financiero de la organización.

## Registro de Movimientos Contables

Los movimientos contables se registran en la tabla `journal_entry_lines` y están asociados tanto a un asiento contable como a una cuenta específica:

```python
# Modelo conceptual simplificado
class JournalEntryLine:
    id: UUID
    journal_entry_id: UUID  # Vínculo con el asiento contable
    account_id: UUID        # Vínculo con la cuenta
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    
    # Relaciones
    journal_entry: JournalEntry
    account: Account
```

### Validaciones para Movimientos

Antes de registrar un movimiento en una cuenta, se realizan varias validaciones:

```python
def validate_movement_allowed(self) -> bool:
    """
    Valida si se pueden crear movimientos en esta cuenta
    """
    if not self.is_active:
        raise ValueError(f"La cuenta {self.code} - {self.name} está inactiva")
    
    if not self.allows_movements:
        raise ValueError(f"La cuenta {self.code} - {self.name} no permite movimientos")
    
    if not self.is_leaf_account:
        raise ValueError(f"La cuenta {self.code} - {self.name} es una cuenta padre y no puede recibir movimientos")
    
    return True
```

Las validaciones principales incluyen:

1. **Cuenta Activa**: Solo cuentas activas pueden recibir movimientos
2. **Permite Movimientos**: La configuración `allows_movements` debe ser verdadera
3. **Cuenta Hoja**: Solo cuentas sin hijos pueden recibir movimientos directos
4. **Terceros y Centro de Costos**: Si está configurado `requires_third_party` o `requires_cost_center`, estos datos deben proporcionarse

## Cálculo de Saldos y Balances

El sistema mantiene actualizados tres tipos de saldos para cada cuenta:

1. **Débito Acumulado** (`debit_balance`): Total de movimientos de débito
2. **Crédito Acumulado** (`credit_balance`): Total de movimientos de crédito
3. **Saldo Neto** (`balance`): Saldo ajustado según la naturaleza de la cuenta

```python
def update_balance(self, debit_amount: Decimal = Decimal('0'), credit_amount: Decimal = Decimal('0')) -> None:
    """
    Actualiza los saldos de la cuenta
    """
    self.debit_balance += Decimal(str(debit_amount))
    self.credit_balance += Decimal(str(credit_amount))
    self.balance = self.get_balance_display()

def get_balance_display(self) -> Decimal:
    """
    Retorna el balance con el signo correcto según la naturaleza de la cuenta
    """
    if self.normal_balance_side == "debit":
        return self.debit_balance - self.credit_balance
    else:
        return self.credit_balance - self.debit_balance
```

### Balance por Naturaleza de Cuenta

El cálculo del saldo neto varía según el tipo de cuenta:

- **Cuentas de Naturaleza Deudora** (ACTIVO, GASTO, COSTOS):
  - Saldo = Débitos - Créditos
  - Saldo normal es positivo

- **Cuentas de Naturaleza Acreedora** (PASIVO, PATRIMONIO, INGRESO):
  - Saldo = Créditos - Débitos
  - Saldo normal es positivo

## Historial de Movimientos

El sistema proporciona un endpoint para consultar el historial de movimientos de una cuenta específica:

```python
@router.get("/{account_id}/movements", response_model=AccountMovementHistory)
async def get_account_movements(
    account_id: uuid.UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountMovementHistory:
    """
    Obtener el historial de movimientos de una cuenta en un período.
    """
    account_service = AccountService(db)
    return await account_service.get_account_movements(account_id, start_date, end_date)
```

### Esquema de Historial

```python
class AccountMovementHistory(BaseModel):
    """Schema para historial de movimientos"""
    account: AccountSummary
    movements: List[AccountMovement]
    period_start: date
    period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal

class AccountMovement(BaseModel):
    """Schema para movimientos de cuenta"""
    date: date
    journal_entry_number: str
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    balance: Decimal
    reference: Optional[str] = None
```

Este esquema proporciona información completa sobre los movimientos, incluyendo:

- Resumen de la cuenta
- Lista detallada de movimientos
- Saldos de apertura y cierre del período
- Totales de débitos y créditos
- Información de seguimiento (número de asiento, referencia)

## Validaciones de Integridad

El sistema implementa múltiples validaciones para mantener la integridad de los movimientos y saldos:

### 1. Partida Doble

Cada asiento contable debe cumplir con el principio de partida doble:

```python
# Validación simplificada
total_debits = sum(line.debit_amount for line in journal_entry.lines)
total_credits = sum(line.credit_amount for line in journal_entry.lines)

if total_debits != total_credits:
    raise ValueError("El asiento no está balanceado: débitos != créditos")
```

### 2. Coherencia de Movimientos

Cada línea de asiento debe tener un monto de débito o crédito, pero no ambos:

```python
if line.debit_amount > 0 and line.credit_amount > 0:
    raise ValueError("Una línea no puede tener débito y crédito simultáneamente")
    
if line.debit_amount == 0 and line.credit_amount == 0:
    raise ValueError("Una línea debe tener un valor de débito o crédito")
```

### 3. Validación de Cuenta

Se valida que la cuenta pueda recibir movimientos:

```python
account = await get_account_by_id(line.account_id)
if not account:
    raise ValueError(f"La cuenta con ID {line.account_id} no existe")

account.validate_movement_allowed()  # Lanza excepción si no se permite
```

## Consulta de Movimientos por Período

El sistema permite consultar movimientos por períodos específicos:

```python
async def get_account_movements(
    self, 
    account_id: uuid.UUID, 
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> AccountMovementHistory:
    """Obtener historial de movimientos de una cuenta"""
    
    # Obtener la cuenta
    account = await self.get_account_by_id(account_id)
    if not account:
        raise AccountNotFoundError()
        
    # Establecer fechas por defecto si no se proporcionan
    if not start_date:
        # Primer día del mes actual
        today = date.today()
        start_date = date(today.year, today.month, 1)
        
    if not end_date:
        # Fecha actual
        end_date = date.today()
    
    # Consulta para obtener los movimientos
    query = (
        select(JournalEntryLine)
        .join(JournalEntry)
        .where(
            JournalEntryLine.account_id == account_id,
            JournalEntry.entry_date.between(start_date, end_date),
            JournalEntry.status == "POSTED"  # Solo movimientos contabilizados
        )
        .order_by(JournalEntry.entry_date, JournalEntry.number)
    )
    
    result = await self.db.execute(query)
    lines = result.scalars().all()
    
    # Calcular saldo de apertura
    opening_balance = await self._get_account_balance_at_date(account_id, start_date - timedelta(days=1))
    
    # Construir lista de movimientos
    movements = []
    running_balance = opening_balance
    total_debits = Decimal("0")
    total_credits = Decimal("0")
    
    for line in lines:
        # Actualizar balance
        if line.debit_amount > 0:
            if account.normal_balance_side == "debit":
                running_balance += line.debit_amount
            else:
                running_balance -= line.debit_amount
            total_debits += line.debit_amount
        else:
            if account.normal_balance_side == "debit":
                running_balance -= line.credit_amount
            else:
                running_balance += line.credit_amount
            total_credits += line.credit_amount
        
        # Crear movimiento
        movement = AccountMovement(
            date=line.journal_entry.entry_date,
            journal_entry_number=line.journal_entry.number,
            description=line.description or line.journal_entry.description,
            debit_amount=line.debit_amount,
            credit_amount=line.credit_amount,
            balance=running_balance,
            reference=line.journal_entry.reference
        )
        movements.append(movement)
    
    # Construir respuesta
    return AccountMovementHistory(
        account=AccountSummary.model_validate(account),
        movements=movements,
        period_start=start_date,
        period_end=end_date,
        opening_balance=opening_balance,
        closing_balance=running_balance,
        total_debits=total_debits,
        total_credits=total_credits
    )
```

## Relación con Asientos Contables

Los movimientos de cuentas están siempre vinculados a asientos contables:

1. **Asiento Contable** (`JournalEntry`): Representa una transacción contable completa
2. **Línea de Asiento** (`JournalEntryLine`): Representa un movimiento individual en una cuenta

```python
# Relación desde la cuenta hacia los movimientos
class Account(Base):
    # ...
    journal_entry_lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine", 
        back_populates="account"
    )

# Relación desde el movimiento hacia la cuenta
class JournalEntryLine(Base):
    # ...
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"))
    account: Mapped["Account"] = relationship("Account", back_populates="journal_entry_lines")
```

### Estados de los Movimientos

Los movimientos heredan el estado del asiento contable al que pertenecen:

- **DRAFT**: Borrador, no afecta los saldos reales
- **POSTED**: Contabilizado, afecta los saldos
- **CANCELLED**: Cancelado, reversado de los saldos

Solo los movimientos en estado `POSTED` afectan los saldos de las cuentas y aparecen en los reportes oficiales.

## Reportes de Cuenta

El sistema proporciona varios reportes relacionados con los movimientos de cuentas:

### Saldo de Cuenta

```python
@router.get("/{account_id}/balance", response_model=AccountBalance)
async def get_account_balance(
    account_id: uuid.UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountBalance:
    """
    Obtener el saldo de una cuenta a una fecha específica.
    """
    account_service = AccountService(db)
    return await account_service.get_account_balance(account_id, as_of_date)
```

### Balance de Comprobación

El balance de comprobación muestra los saldos de todas las cuentas:

```python
class TrialBalanceItem(BaseModel):
    """Schema para items del balance de comprobación"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    opening_balance: Decimal
    debit_movements: Decimal
    credit_movements: Decimal
    closing_balance: Decimal
    normal_balance_side: str
```

### Libro Mayor

El libro mayor muestra todos los movimientos agrupados por cuenta:

```python
class LedgerAccount(BaseModel):
    """Schema para cuenta en libro mayor"""
    account_id: uuid.UUID
    account_code: str
    account_name: str
    opening_balance: Decimal
    movements: List[LedgerMovement]
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
```

## Ejemplos de Uso

### Ejemplo 1: Registrar un Asiento Contable con Movimientos

```python
# Asiento contable con movimientos en cuentas
journal_entry = {
    "entry_date": "2023-06-10",
    "description": "Compra de equipos de oficina",
    "reference": "Factura #1234",
    "lines": [
        {
            "account_id": "id-cuenta-equipos-oficina",  # Cuenta de ACTIVO
            "description": "Compra de computadoras",
            "debit_amount": 1500.00,
            "credit_amount": 0
        },
        {
            "account_id": "id-cuenta-iva-credito",  # Cuenta de ACTIVO
            "description": "IVA Crédito Fiscal",
            "debit_amount": 180.00,
            "credit_amount": 0
        },
        {
            "account_id": "id-cuenta-bancos",  # Cuenta de ACTIVO
            "description": "Pago desde cuenta bancaria",
            "debit_amount": 0,
            "credit_amount": 1680.00
        }
    ]
}
```

### Ejemplo 2: Consultar Movimientos de una Cuenta

```python
# Solicitud para obtener movimientos de la cuenta bancaria
response = client.get(
    "/api/v1/accounts/id-cuenta-bancos/movements?start_date=2023-06-01&end_date=2023-06-30",
    headers={"Authorization": f"Bearer {token}"}
)

# Respuesta con el historial de movimientos
```

### Ejemplo 3: Obtener Saldo de una Cuenta

```python
# Consultar saldo a fecha específica
response = client.get(
    "/api/v1/accounts/id-cuenta-bancos/balance?as_of_date=2023-06-30",
    headers={"Authorization": f"Bearer {token}"}
)

# La respuesta incluye debit_balance, credit_balance, net_balance
```

## Buenas Prácticas

1. **Descripción Clara**: Proporcionar descripciones claras para cada movimiento
2. **Referencias**: Incluir referencias a documentos externos (facturas, recibos)
3. **Partida Doble**: Verificar que cada asiento cumple con el principio de partida doble
4. **Validación Previa**: Validar las cuentas y montos antes de crear movimientos
5. **Auditoría**: Mantener información completa para fines de auditoría
6. **Conciliación Regular**: Verificar periódicamente la exactitud de los saldos
