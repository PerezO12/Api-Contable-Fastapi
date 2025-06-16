# Documentación Técnica - Integración con Asientos Contables

## Resumen

La integración entre productos y asientos contables permite trazabilidad completa de las transacciones, control de inventario en tiempo real y clasificación de los orígenes de las operaciones contables.

## Cambios en JournalEntry

### Nuevo Campo: transaction_origin

```python
transaction_origin: Mapped[Optional[TransactionOrigin]] = mapped_column(
    nullable=True,
    comment="Origen de la transacción contable"
)
```

#### Enum TransactionOrigin
```python
class TransactionOrigin(str, Enum):
    SALE = "sale"               # Venta
    PURCHASE = "purchase"       # Compra
    ADJUSTMENT = "adjustment"   # Ajuste
    TRANSFER = "transfer"       # Transferencia
    PAYMENT = "payment"         # Pago
    COLLECTION = "collection"   # Cobro
    OPENING = "opening"         # Apertura
    CLOSING = "closing"         # Cierre
    OTHER = "other"             # Otro
```

## Cambios en JournalEntryLine

### Nuevos Campos de Producto

```python
# Referencia al producto
product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    ForeignKey("products.id"), 
    nullable=True,
    comment="ID del producto asociado"
)

# Campos de cantidad y precio
quantity: Mapped[Optional[Decimal]] = mapped_column(
    Numeric(15, 4), 
    nullable=True,
    comment="Cantidad del producto"
)

unit_price: Mapped[Optional[Decimal]] = mapped_column(
    Numeric(15, 4), 
    nullable=True,
    comment="Precio unitario del producto"
)

# Campos de descuentos
discount_percentage: Mapped[Optional[Decimal]] = mapped_column(
    Numeric(5, 2), 
    nullable=True,
    comment="Porcentaje de descuento aplicado"
)

discount_amount: Mapped[Optional[Decimal]] = mapped_column(
    Numeric(15, 4), 
    nullable=True,
    comment="Monto de descuento aplicado"
)

# Campos de impuestos
tax_percentage: Mapped[Optional[Decimal]] = mapped_column(
    Numeric(5, 2), 
    nullable=True,
    comment="Porcentaje de impuesto aplicado"
)

tax_amount: Mapped[Optional[Decimal]] = mapped_column(
    Numeric(15, 4), 
    nullable=True,
    comment="Monto de impuesto aplicado"
)
```

### Relación con Producto

```python
product: Mapped[Optional["Product"]] = relationship(
    "Product", 
    back_populates="journal_entry_lines",
    lazy="select"
)
```

## Validaciones Implementadas

### En JournalEntryService.create_journal_entry()

#### 1. Validación de Productos en Batch
```python
# Validación de existencia de productos
product_ids = [line.product_id for line in entry_data.lines if line.product_id]
if product_ids:
    products_result = await self.db.execute(
        select(Product).where(Product.id.in_(product_ids))
    )
    products_dict = {product.id: product for product in products_result.scalars().all()}
    
    # Verificar productos faltantes
    missing_products = set(product_ids) - set(products_dict.keys())
    if missing_products:
        raise JournalEntryError(f"Productos no encontrados: {list(missing_products)}")
```

#### 2. Validación de Estado de Productos
```python
# Verificar que productos estén activos
inactive_products = [
    f"{product.code} - {product.name}" 
    for product in products_dict.values() 
    if product.status != ProductStatus.ACTIVE
]
if inactive_products:
    raise JournalEntryError(f"Los siguientes productos no están activos: {', '.join(inactive_products)}")
```

#### 3. Validación de Coherencia de Precios
```python
if line_data.product_id:
    # Validar cantidad para productos físicos
    if product.product_type in [ProductType.PRODUCT, ProductType.BOTH]:
        if not line_data.quantity or line_data.quantity <= 0:
            raise JournalEntryError(f"La cantidad debe ser mayor a 0 para productos físicos en línea {line_number}")
    
    # Validar coherencia de precios
    if line_data.unit_price and line_data.quantity:
        calculated_total = line_data.unit_price * line_data.quantity
        # Aplicar descuentos
        if line_data.discount_amount:
            calculated_total -= line_data.discount_amount
        elif line_data.discount_percentage:
            calculated_total *= (1 - line_data.discount_percentage / 100)
        
        # Verificar coherencia con monto de la línea
        line_amount = line_data.debit_amount or line_data.credit_amount
        if abs(calculated_total - line_amount) > Decimal('0.01'):
            raise JournalEntryError(f"El monto calculado no coincide con el monto de la línea en línea {line_number}")
```

#### 4. Validación de Origen de Transacción
```python
if entry_data.transaction_origin:
    sales_origins = [TransactionOrigin.SALE, TransactionOrigin.COLLECTION]
    purchase_origins = [TransactionOrigin.PURCHASE, TransactionOrigin.PAYMENT]
    
    if entry_data.transaction_origin in sales_origins:
        # Para ventas, verificar línea de ingreso
        has_revenue_line = any(line.credit_amount > 0 for line in entry_data.lines)
        if not has_revenue_line:
            raise JournalEntryError("Los asientos de ventas deben incluir al menos una línea de crédito (ingreso)")
    
    elif entry_data.transaction_origin in purchase_origins:
        # Para compras, verificar línea de gasto
        has_expense_line = any(line.debit_amount > 0 for line in entry_data.lines)
        if not has_expense_line:
            raise JournalEntryError("Los asientos de compras deben incluir al menos una línea de débito (gasto o activo)")
```

### En JournalEntryService.post_journal_entry()

#### Validación de Stock Disponible
```python
for line in journal_entry.lines:
    if line.product_id:
        # Validar stock para productos de inventario (solo ventas)
        if (line.product.product_type in [ProductType.PRODUCT, ProductType.BOTH] and 
            journal_entry.transaction_origin == TransactionOrigin.SALE and
            line.quantity and line.quantity > 0):
            
            if line.product.manage_inventory and line.product.current_stock is not None:
                if line.product.current_stock < line.quantity:
                    raise JournalEntryError(
                        f"Stock insuficiente para producto {line.product.code}. "
                        f"Stock actual: {line.product.current_stock}, Cantidad requerida: {line.quantity}"
                    )
```

## Esquemas Actualizados

### JournalEntryLineBase Schema
```python
class JournalEntryLineBase(BaseModel):
    # Campos existentes...
    
    # Nuevos campos para productos
    product_id: Optional[uuid.UUID] = Field(None, description="ID del producto")
    quantity: Optional[Decimal] = Field(None, gt=0, description="Cantidad del producto")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Precio unitario")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Porcentaje de descuento")
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Monto de descuento")
    tax_percentage: Optional[Decimal] = Field(None, ge=0, description="Porcentaje de impuesto")
    tax_amount: Optional[Decimal] = Field(None, ge=0, description="Monto de impuesto")
    
    @model_validator(mode='after')
    def validate_product_fields(self):
        """Valida coherencia de campos relacionados con productos"""
        if self.product_id:
            if self.quantity and self.quantity <= 0:
                raise ValueError("La cantidad debe ser mayor a cero")
                
            # No permitir ambos tipos de descuento
            if self.discount_percentage is not None and self.discount_amount is not None:
                raise ValueError("No se puede especificar porcentaje y monto de descuento al mismo tiempo")
        
        return self
```

### JournalEntryBase Schema
```python
class JournalEntryBase(BaseModel):
    # Campos existentes...
    
    # Nuevo campo
    transaction_origin: Optional[TransactionOrigin] = Field(None, description="Origen de la transacción")
```

## Casos de Uso Típicos

### 1. Asiento de Venta con Productos

```python
sale_entry = JournalEntryCreate(
    entry_date=date.today(),
    description="Venta de productos",
    entry_type=JournalEntryType.AUTOMATIC,
    transaction_origin=TransactionOrigin.SALE,
    lines=[
        # Línea de efectivo (débito)
        JournalEntryLineCreate(
            account_id=cash_account_id,
            debit_amount=Decimal("1000.00"),
            credit_amount=Decimal("0"),
            description="Efectivo recibido",
            product_id=laptop_id,
            quantity=Decimal("2"),
            unit_price=Decimal("500.00")
        ),
        # Línea de ingresos (crédito)
        JournalEntryLineCreate(
            account_id=revenue_account_id,
            debit_amount=Decimal("0"),
            credit_amount=Decimal("1000.00"),
            description="Ingresos por venta",
            product_id=laptop_id,
            quantity=Decimal("2"),
            unit_price=Decimal("500.00")
        )
    ]
)
```

### 2. Asiento de Compra con Productos

```python
purchase_entry = JournalEntryCreate(
    entry_date=date.today(),
    description="Compra de inventario",
    entry_type=JournalEntryType.AUTOMATIC,
    transaction_origin=TransactionOrigin.PURCHASE,
    lines=[
        # Línea de inventario (débito)
        JournalEntryLineCreate(
            account_id=inventory_account_id,
            debit_amount=Decimal("800.00"),
            credit_amount=Decimal("0"),
            description="Compra de inventario",
            product_id=laptop_id,
            quantity=Decimal("2"),
            unit_price=Decimal("400.00")
        ),
        # Línea de efectivo (crédito)
        JournalEntryLineCreate(
            account_id=cash_account_id,
            debit_amount=Decimal("0"),
            credit_amount=Decimal("800.00"),
            description="Efectivo pagado"
        )
    ]
)
```

## Beneficios de la Integración

### 1. Trazabilidad Completa
- Cada línea de asiento puede rastrearse a un producto específico
- Historial completo de transacciones por producto
- Análisis de rentabilidad por producto

### 2. Control de Inventario
- Validación de stock disponible en tiempo real
- Prevención de sobreventa
- Alertas automáticas de stock bajo

### 3. Coherencia de Datos
- Validación automática de precios y cantidades
- Consistencia entre documentos comerciales y contables
- Reducción de errores manuales

### 4. Reportes Avanzados
- Análisis de ventas por producto
- Cálculo automático de costos de ventas
- Estadísticas de movimiento de inventario

## Consideraciones de Rendimiento

### 1. Consultas Optimizadas
- Validaciones en batch para múltiples productos
- Uso de selectinload para evitar lazy loading
- Índices en campos de consulta frecuente

### 2. Validaciones Eficientes
- Validaciones a nivel de aplicación para lógica compleja
- Restricciones de base de datos para integridad básica
- Validaciones async para no bloquear la aplicación

### 3. Manejo de Memoria
- Carga selectiva de relaciones según necesidad
- Paginación en consultas de grandes volúmenes
- Limpieza de objetos después de operaciones masivas
