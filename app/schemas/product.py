import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.product import ProductType, ProductStatus, MeasurementUnit, TaxCategory
from app.utils.enum_validators import create_enum_validator


# Esquemas base para productos
class ProductBase(BaseModel):
    """Esquema base para productos"""
    code: str = Field(..., min_length=1, max_length=50, description="Código único del producto")
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del producto")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción detallada")
    product_type: ProductType = Field(default=ProductType.PRODUCT, description="Tipo de producto")
    category: Optional[str] = Field(None, max_length=100, description="Categoría del producto")
    subcategory: Optional[str] = Field(None, max_length=100, description="Subcategoría del producto")
    brand: Optional[str] = Field(None, max_length=100, description="Marca del producto")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="Estado del producto")
    measurement_unit: MeasurementUnit = Field(default=MeasurementUnit.UNIT, description="Unidad de medida")
    weight: Optional[Decimal] = Field(None, ge=0, description="Peso en kilogramos")
    dimensions: Optional[str] = Field(None, max_length=100, description="Dimensiones (LxAxA)")    # Precios y costos
    purchase_price: Decimal = Field(default=Decimal("0"), ge=0, description="Precio de compra")
    sale_price: Decimal = Field(default=Decimal("0"), ge=0, description="Precio de venta")
    min_sale_price: Decimal = Field(default=Decimal("0"), ge=0, description="Precio mínimo de venta")
    suggested_price: Decimal = Field(default=Decimal("0"), ge=0, description="Precio sugerido")
    
    # Información fiscal
    tax_category: TaxCategory = Field(default=TaxCategory.EXEMPT, description="Categoría fiscal")
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100, description="Tasa de impuesto (%)")
    
    # Cuentas contables
    sales_account_id: Optional[uuid.UUID] = Field(None, description="Cuenta contable para ventas")
    purchase_account_id: Optional[uuid.UUID] = Field(None, description="Cuenta contable para compras")
    inventory_account_id: Optional[uuid.UUID] = Field(None, description="Cuenta contable para inventario")
    cogs_account_id: Optional[uuid.UUID] = Field(None, description="Cuenta contable para costo de ventas")
      # Control de inventario
    manage_inventory: bool = Field(default=False, description="Maneja inventario")
    current_stock: Decimal = Field(default=Decimal("0"), ge=0, description="Stock actual")
    min_stock: Decimal = Field(default=Decimal("0"), ge=0, description="Stock mínimo")
    max_stock: Decimal = Field(default=Decimal("0"), ge=0, description="Stock máximo")
    reorder_point: Decimal = Field(default=Decimal("0"), ge=0, description="Punto de reorden")
    
    # Información adicional
    barcode: Optional[str] = Field(None, max_length=50, description="Código de barras")
    sku: Optional[str] = Field(None, max_length=50, description="SKU")
    internal_reference: Optional[str] = Field(None, max_length=50, description="Referencia interna")
    supplier_reference: Optional[str] = Field(None, max_length=50, description="Referencia del proveedor")
    notes: Optional[str] = Field(None, description="Notas adicionales")
    external_reference: Optional[str] = Field(None, max_length=100, description="Referencia externa")
      # Fechas de control
    launch_date: Optional[datetime] = Field(None, description="Fecha de lanzamiento")
    discontinuation_date: Optional[datetime] = Field(None, description="Fecha de descontinuación")

    @field_validator('product_type', mode='before')
    @classmethod
    def validate_product_type(cls, v):
        """Valida el tipo de producto de forma case-insensitive"""
        return create_enum_validator(ProductType)(v)

    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Valida el estado del producto de forma case-insensitive"""
        return create_enum_validator(ProductStatus)(v)

    @field_validator('measurement_unit', mode='before')
    @classmethod
    def validate_measurement_unit(cls, v):
        """Valida la unidad de medida de forma case-insensitive"""
        return create_enum_validator(MeasurementUnit)(v)

    @field_validator('tax_category', mode='before')
    @classmethod
    def validate_tax_category(cls, v):
        """Valida la categoría fiscal de forma case-insensitive"""
        return create_enum_validator(TaxCategory)(v)

    @field_validator('sale_price', 'min_sale_price')
    @classmethod
    def validate_sale_prices(cls, v, info):
        """Valida coherencia de precios de venta"""
        if v is not None and v < 0:
            raise ValueError("Los precios no pueden ser negativos")
        return v

    @field_validator('min_stock', 'max_stock')
    @classmethod
    def validate_stock_levels(cls, v, info):
        """Valida niveles de stock"""
        values = info.data
        if v is not None:
            if v < 0:
                raise ValueError("Los niveles de stock no pueden ser negativos")
            if 'min_stock' in values and 'max_stock' in values:
                min_stock = values.get('min_stock')
                max_stock = values.get('max_stock')
                if min_stock and max_stock and min_stock > max_stock:
                    raise ValueError("El stock mínimo no puede ser mayor al stock máximo")
        return v


class ProductCreate(ProductBase):
    """Esquema para crear productos"""
    pass


class ProductUpdate(BaseModel):
    """Esquema para actualizar productos"""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    product_type: Optional[ProductType] = None
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    status: Optional[ProductStatus] = None
    measurement_unit: Optional[MeasurementUnit] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[str] = Field(None, max_length=100)
    
    # Precios y costos
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    sale_price: Optional[Decimal] = Field(None, ge=0)
    min_sale_price: Optional[Decimal] = Field(None, ge=0)
    suggested_price: Optional[Decimal] = Field(None, ge=0)
    
    # Información fiscal
    tax_category: Optional[TaxCategory] = None
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Cuentas contables
    sales_account_id: Optional[uuid.UUID] = None
    purchase_account_id: Optional[uuid.UUID] = None
    inventory_account_id: Optional[uuid.UUID] = None
    cogs_account_id: Optional[uuid.UUID] = None
    
    # Control de inventario
    manage_inventory: Optional[bool] = None
    current_stock: Optional[Decimal] = Field(None, ge=0)
    min_stock: Optional[Decimal] = Field(None, ge=0)
    max_stock: Optional[Decimal] = Field(None, ge=0)
    reorder_point: Optional[Decimal] = Field(None, ge=0)
    
    # Información adicional
    barcode: Optional[str] = Field(None, max_length=50)
    sku: Optional[str] = Field(None, max_length=50)
    internal_reference: Optional[str] = Field(None, max_length=50)
    supplier_reference: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    external_reference: Optional[str] = Field(None, max_length=100)
    
    # Fechas de control
    launch_date: Optional[datetime] = None
    discontinuation_date: Optional[datetime] = None


class ProductRead(ProductBase):
    """Esquema para leer productos"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Campos calculados
    display_name: Optional[str] = None
    is_physical_product: Optional[bool] = None
    is_service: Optional[bool] = None
    requires_inventory_control: Optional[bool] = None
    is_low_stock: Optional[bool] = None
    needs_reorder: Optional[bool] = None
    profit_margin: Optional[Decimal] = None
    profit_amount: Optional[Decimal] = None
    stock_value: Optional[Decimal] = None
    has_valid_accounting_setup: Optional[bool] = None


class ProductSummary(BaseModel):
    """Esquema resumido para productos"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    code: str
    name: str
    product_type: ProductType
    status: ProductStatus
    sale_price: Optional[Decimal] = None
    current_stock: Optional[Decimal] = None
    measurement_unit: MeasurementUnit


class ProductList(BaseModel):
    """Esquema para lista paginada de productos"""
    products: List[ProductSummary]
    total: int
    page: int
    size: int
    pages: int


class ProductFilter(BaseModel):
    """Esquema para filtros de productos"""
    search: Optional[str] = Field(None, description="Buscar en código, nombre o descripción")
    product_type: Optional[ProductType] = None
    status: Optional[ProductStatus] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    tax_category: Optional[TaxCategory] = None
    manage_inventory: Optional[bool] = None
    low_stock: Optional[bool] = Field(None, description="Productos con stock bajo")
    needs_reorder: Optional[bool] = Field(None, description="Productos que necesitan reorden")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Precio mínimo")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Precio máximo")


class ProductMovement(BaseModel):
    """Esquema para movimientos de productos"""
    model_config = ConfigDict(from_attributes=True)
    
    product_id: uuid.UUID
    product_code: str
    product_name: str
    journal_entry_id: uuid.UUID
    journal_entry_number: str
    entry_date: datetime
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    amount: Decimal
    movement_type: str  # "debit" o "credit"
    account_code: str
    account_name: str
    third_party_code: Optional[str] = None
    third_party_name: Optional[str] = None
    reference: Optional[str] = None


class ProductStock(BaseModel):
    """Esquema para información de stock"""
    model_config = ConfigDict(from_attributes=True)
    
    product_id: uuid.UUID
    product_code: str
    product_name: str
    current_stock: Optional[Decimal] = None
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    measurement_unit: MeasurementUnit
    is_low_stock: bool
    needs_reorder: bool
    stock_value: Optional[Decimal] = None


class ProductImport(BaseModel):
    """Esquema para importación de productos"""
    products: List[ProductCreate]
    update_existing: bool = Field(default=False, description="Actualizar productos existentes")
    skip_errors: bool = Field(default=True, description="Omitir productos con errores")


class ProductExport(BaseModel):
    """Esquema para exportación de productos"""
    format: str = Field(default="xlsx", description="Formato de exportación")
    include_inactive: bool = Field(default=False, description="Incluir productos inactivos")
    include_discontinued: bool = Field(default=False, description="Incluir productos descontinuados")
    filters: Optional[ProductFilter] = None


class ProductValidation(BaseModel):
    """Esquema para validación de productos"""
    is_valid: bool
    errors: List[str]
    warnings: List[str] = Field(default_factory=list)


class BulkProductOperation(BaseModel):
    """Esquema para operaciones masivas en productos"""
    product_ids: List[uuid.UUID]
    operation: str = Field(..., description="Tipo de operación: activate, deactivate, discontinue")
    reason: Optional[str] = Field(None, description="Razón de la operación")


class BulkProductOperationResult(BaseModel):
    """Esquema para resultado de operaciones masivas"""
    total_requested: int
    total_processed: int
    total_errors: int
    successful_ids: List[uuid.UUID]
    errors: List[dict]  # {"id": uuid, "error": str}


class ProductStats(BaseModel):
    """Esquema para estadísticas de productos"""
    total_products: int
    active_products: int
    inactive_products: int
    discontinued_products: int
    products_with_inventory: int
    low_stock_products: int
    products_need_reorder: int
    total_stock_value: Optional[Decimal] = None
    categories: List[dict] = Field(default_factory=list)  # {"category": str, "count": int}
    brands: List[dict] = Field(default_factory=list)  # {"brand": str, "count": int}


class ProductResponse(BaseModel):
    """Esquema para respuesta de operaciones con productos"""
    success: bool
    message: str
    product: Optional[ProductRead] = None
    errors: List[str] = Field(default_factory=list)


class ProductDetailResponse(BaseModel):
    """Esquema para respuesta detallada de productos"""
    product: ProductRead
    movements: List[ProductMovement] = Field(default_factory=list)
    stock_info: Optional[ProductStock] = None
    accounting_setup: dict = Field(default_factory=dict)


class ProductListResponse(BaseModel):
    """Esquema para respuesta de lista de productos"""
    success: bool
    message: str
    data: ProductList
    filters_applied: Optional[ProductFilter] = None


# Esquemas para líneas de asientos con productos
class JournalEntryLineProduct(BaseModel):
    """Esquema para información de producto en líneas de asiento"""
    product_id: Optional[uuid.UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0, description="Cantidad del producto")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Precio unitario")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="% descuento")
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Monto descuento")
    tax_percentage: Optional[Decimal] = Field(None, ge=0, description="% impuesto")
    tax_amount: Optional[Decimal] = Field(None, ge=0, description="Monto impuesto")
    
    # Campos calculados
    subtotal_before_discount: Optional[Decimal] = None
    effective_unit_price: Optional[Decimal] = None
    total_discount: Optional[Decimal] = None
    subtotal_after_discount: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None

    @field_validator('discount_percentage', 'discount_amount')
    @classmethod
    def validate_discount(cls, v, info):
        """Valida que no se especifiquen ambos tipos de descuento"""
        values = info.data
        if v is not None:
            discount_percentage = values.get('discount_percentage')
            discount_amount = values.get('discount_amount')
            if discount_percentage is not None and discount_amount is not None:
                raise ValueError("No se puede especificar porcentaje y monto de descuento al mismo tiempo")
        return v
