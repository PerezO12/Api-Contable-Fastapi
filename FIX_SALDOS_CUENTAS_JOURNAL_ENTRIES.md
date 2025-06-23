# Fix de Saldos de Cuentas en Journal Entries

## Problema Identificado

Las facturas estaban creando journal entries correctamente con débitos y créditos, pero **los saldos de las cuentas contables no se estaban actualizando** cuando se contabilizaban los asientos.

### Causa Raíz

En los servicios `journal_entry_service.py` e `invoice_service.py`, los journal entries se estaban marcando como `POSTED` directamente sin llamar al método `post()` del modelo que es responsable de actualizar los saldos de las cuentas.

### Ubicaciones del Problema

1. **JournalEntryService.post_journal_entry()** - Líneas 798-801
   - Actualizaba status a POSTED directamente
   - No llamaba `update_balance()` en las cuentas

2. **JournalEntryService._create_reversal_entry()** - Líneas 937-940  
   - Mismo problema en asientos de reversión

3. **InvoiceService._create_journal_entry_for_invoice()** - Línea 587
   - Creaba journal entries con status POSTED directamente
   - No actualizaba saldos de cuentas

4. **InvoiceService._create_reversal_journal_entry()** - Línea 724
   - Mismo problema en reversiones de facturas

## Solución Implementada

### 1. Actualización de JournalEntryService

**Archivo:** `app/services/journal_entry_service.py`

#### En método `post_journal_entry()`:
```python
# CRÍTICO: Actualizar saldos de las cuentas
for line in journal_entry.lines:
    # Cargar la cuenta si no está ya cargada
    if not line.account:
        account_result = await self.db.execute(
            select(Account).where(Account.id == line.account_id)
        )
        account = account_result.scalar_one_or_none()
        if account:
            line.account = account
    
    # Actualizar saldos de la cuenta
    if line.account:
        line.account.update_balance(line.debit_amount, line.credit_amount)
```

#### En método `_create_reversal_entry()`:
```python
# CRÍTICO: Actualizar saldos de las cuentas para la reversión
for line in reversal_lines:
    # Cargar la cuenta si no está ya cargada
    if not line.account:
        account_result = await self.db.execute(
            select(Account).where(Account.id == line.account_id)
        )
        account = account_result.scalar_one_or_none()
        if account:
            line.account = account
    
    # Actualizar saldos de la cuenta
    if line.account:
        line.account.update_balance(line.debit_amount, line.credit_amount)
```

### 2. Actualización de InvoiceService

**Archivo:** `app/services/invoice_service.py`

#### En método `_create_journal_entry_for_invoice()`:
```python
# CRÍTICO: Actualizar saldos de las cuentas ya que se creó con status POSTED
for line in journal_entry.lines:
    if line.account:
        line.account.update_balance(line.debit_amount, line.credit_amount)
```

#### En método `_create_reversal_journal_entry()`:
```python
# CRÍTICO: Actualizar saldos de las cuentas ya que se creó con status POSTED
self.db.flush()  # Asegurar que las líneas estén persistidas

# Cargar las líneas con sus cuentas para actualizar saldos
reversal_lines = self.db.query(JournalEntryLine).filter(
    JournalEntryLine.journal_entry_id == reversal_entry.id
).all()

for line in reversal_lines:
    if line.account:
        line.account.update_balance(line.debit_amount, line.credit_amount)
```

### 3. Script de Validación

**Archivo:** `validate_account_balances.py`

Script para:
- Validar que los saldos actuales coincidan con los journal entries
- Identificar discrepancias
- Corregir automáticamente los saldos si es necesario

## Funcionamiento del Método update_balance()

**Archivo:** `app/models/account.py`

```python
def update_balance(self, debit_amount: Decimal = Decimal('0'), credit_amount: Decimal = Decimal('0')) -> None:
    """
    Actualiza los saldos de la cuenta
    """
    self.debit_balance += Decimal(str(debit_amount))
    self.credit_balance += Decimal(str(credit_amount))
    self.balance = self.get_balance_display()
```

## Impacto de la Solución

✅ **Solucionado:** Los journal entries ahora actualizan correctamente los saldos de las cuentas
✅ **Solucionado:** Las facturas contabilizadas afectan los saldos de las cuentas
✅ **Solucionado:** Los asientos de reversión también actualizan saldos correctamente
✅ **Agregado:** Script de validación para detectar futuros problemas

## Verificación Post-Fix

Para verificar que la solución funciona, hay dos scripts disponibles:

### 1. Script Completo de Validación (`validate_account_balances.py`)

**Uso:**
```bash
cd "e:\trabajo\Aplicacion\API Contable"
python validate_account_balances.py
```

**Características:**
- ✅ Validación completa de saldos vs journal entries
- ✅ Corrección automática de discrepancias
- ✅ Reporte detallado de diferencias
- ✅ Estadísticas completas del sistema

### 2. Script Rápido de Verificación (`quick_balance_check.py`)

**Uso:**
```bash
cd "e:\trabajo\Aplicacion\API Contable"
# Configurar DATABASE_URL si no está en el entorno
set DATABASE_URL=postgresql://user:pass@localhost/dbname
python quick_balance_check.py
```

**Características:**
- ⚡ Verificación rápida sin importar modelos de la app
- 📊 Consultas SQL directas
- 🔍 Solo muestra discrepancias encontradas

### 3. Prueba Manual

1. **Crear una nueva factura y contabilizarla**
2. **Verificar que los saldos de las cuentas se actualicen**
3. **Comprobar en la base de datos:**

```sql
-- Verificar saldos de una cuenta específica
SELECT 
    a.code, 
    a.name,
    a.debit_balance,
    a.credit_balance,
    a.balance
FROM accounts a 
WHERE a.code = 'CODIGO_CUENTA';

-- Verificar movimientos contabilizados de la cuenta
SELECT 
    je.number,
    je.description,
    jel.debit_amount,
    jel.credit_amount,
    je.entry_date
FROM journal_entry_lines jel
JOIN journal_entries je ON jel.journal_entry_id = je.id
JOIN accounts a ON jel.account_id = a.id
WHERE a.code = 'CODIGO_CUENTA' 
AND je.status = 'POSTED'
ORDER BY je.entry_date DESC;
```

## Facturas Históricas

Las facturas creadas antes de este fix pueden tener journal entries contabilizados pero sin saldos actualizados en las cuentas. El script `validate_account_balances.py` puede corregir estos casos automáticamente.

---

**Fecha:** 23 de Junio, 2025  
**Severidad:** Crítico - Integridad de datos contables  
**Status:** ✅ Resuelto
