import uuid
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, ForeignKey, Numeric, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.journal_entry import JournalEntryLine
    from app.models.account import Account


class ProductType(str, Enum):
    """Tipos de producto"""
    PRODUCT = "product"  # Producto físico
    SERVICE = "service"  # Servicio
    BOTH = "both"  # Puede ser producto o servicio


class ProductStatus(str, Enum):
    """Estados del producto"""
    ACTIVE = "active"  # Activo
    INACTIVE = "inactive"  # Inactivo
    DISCONTINUED = "discontinued"  # Descontinuado


class MeasurementUnit(str, Enum):
    """Unidades de medida"""
    UNIT = "unit"  # Unidad
    KG = "kg"  # Kilogramo
    GRAM = "gram"  # Gramo
    LITER = "liter"  # Litro
    METER = "meter"  # Metro
    CM = "cm"  # Centímetro
    M2 = "m2"  # Metro cuadrado
    M3 = "m3"  # Metro cúbico
    HOUR = "hour"  # Hora
    DAY = "day"  # Día
    MONTH = "month"  # Mes
    YEAR = "year"  # Año
    DOZEN = "dozen"  # Docena
    PACK = "pack"  # Paquete
    BOX = "box"  # Caja


class TaxCategory(str, Enum):
    """Categorías de impuestos"""
    EXEMPT = "EXEMPT"  # Exento
    ZERO_RATE = "ZERO_RATE"  # Tasa cero
    REDUCED_RATE = "REDUCED_RATE"  # Tasa reducida
    STANDARD_RATE = "STANDARD_RATE"  # Tasa estándar
    SUPER_REDUCED_RATE = "SUPER_REDUCED_RATE"  # Tasa súper reducida


class Product(Base):
    """
    Modelo de productos y servicios
    Maneja el catálogo de productos/servicios de la empresa
    """
    __tablename__ = "products"    # Información básica
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False,
                                     comment="Código único del producto")
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True,
                                     comment="Nombre único del producto (case-sensitive)")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True,
                                                      comment="Descripción detallada del producto")
    
    # Clasificación
    product_type: Mapped[ProductType] = mapped_column(default=ProductType.PRODUCT, nullable=False,
                                                     comment="Tipo de producto: físico, servicio o ambos")
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True,
                                                   comment="Categoría del producto")
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True,
                                                      comment="Subcategoría del producto")
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True,
                                                comment="Marca del producto")
    
    # Estado
    status: Mapped[ProductStatus] = mapped_column(default=ProductStatus.ACTIVE, nullable=False,
                                                 comment="Estado actual del producto")
    
    # Unidades y medidas
    measurement_unit: Mapped[MeasurementUnit] = mapped_column(default=MeasurementUnit.UNIT, nullable=False,
                                                             comment="Unidad de medida principal")
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=3), nullable=True,
                                                     comment="Peso en kilogramos")
    dimensions: Mapped[Optional[str]] = mapped_column(String(100), nullable=True,
                                                     comment="Dimensiones (LxAxA)")
      # Precios y costos
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=0, nullable=False,
                                                    comment="Precio de compra")
    sale_price: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=0, nullable=False,
                                               comment="Precio de venta")
    min_sale_price: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=0, nullable=False,
                                                   comment="Precio mínimo de venta")
    suggested_price: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=0, nullable=False,
                                                    comment="Precio sugerido")
      # Información fiscal
    tax_category: Mapped[TaxCategory] = mapped_column(default=TaxCategory.EXEMPT, nullable=False,
                                                     comment="Categoría fiscal del producto")
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), default=0, nullable=False,
                                             comment="Tasa de impuesto aplicable (%)")
    
    # Cuentas contables asociadas
    sales_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True,
                                                                 comment="Cuenta contable para ventas")
    purchase_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True,
                                                                    comment="Cuenta contable para compras")
    inventory_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True,
                                                                     comment="Cuenta contable para inventario")
    cogs_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True,
                                                               comment="Cuenta contable para costo de ventas")
      # Control de inventario (para productos físicos)
    manage_inventory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False,
                                                  comment="Indica si se maneja inventario")
    current_stock: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=0, nullable=False,
                                                  comment="Stock actual")
    min_stock: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=0, nullable=False,
                                              comment="Stock mínimo")
    max_stock: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=0, nullable=False,
                                              comment="Stock máximo")
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), default=0, nullable=False,
                                                  comment="Punto de reorden")
    
    # Información adicional
    barcode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True,
                                                  comment="Código de barras")
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True,
                                              comment="Stock Keeping Unit")
    internal_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True,
                                                             comment="Referencia interna")
    supplier_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True,
                                                             comment="Referencia del proveedor")
    
    # Metadatos
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True,
                                               comment="Notas adicionales")
    external_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True,
                                                             comment="Referencia externa")
    
    # Fechas de control
    launch_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                           comment="Fecha de lanzamiento")
    discontinuation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                                    comment="Fecha de descontinuación")
    
    # Relationships
    sales_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[sales_account_id], lazy="select")
    purchase_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[purchase_account_id], lazy="select")
    inventory_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[inventory_account_id], lazy="select")
    cogs_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[cogs_account_id], lazy="select")
    
    # Relación con líneas de asientos contables
    journal_entry_lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine",
        back_populates="product",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Product(code='{self.code}', name='{self.name}', type='{self.product_type}')>"

    @property
    def display_name(self) -> str:
        """Nombre para mostrar que incluye código y nombre"""
        return f"{self.code} - {self.name}"

    @property
    def is_physical_product(self) -> bool:
        """Verifica si es un producto físico"""
        return self.product_type in [ProductType.PRODUCT, ProductType.BOTH]

    @property
    def is_service(self) -> bool:
        """Verifica si es un servicio"""
        return self.product_type in [ProductType.SERVICE, ProductType.BOTH]

    @property
    def requires_inventory_control(self) -> bool:
        """Verifica si requiere control de inventario"""
        return self.is_physical_product and self.manage_inventory

    @property
    def is_low_stock(self) -> bool:
        """Verifica si el stock está bajo"""
        if not self.requires_inventory_control or self.current_stock is None or self.min_stock is None:
            return False
        return self.current_stock <= self.min_stock

    @property
    def needs_reorder(self) -> bool:
        """Verifica si necesita reabastecimiento"""
        if not self.requires_inventory_control or self.current_stock is None or self.reorder_point is None:
            return False
        return self.current_stock <= self.reorder_point

    @property
    def profit_margin(self) -> Optional[Decimal]:
        """Calcula el margen de ganancia"""
        if self.purchase_price and self.sale_price and self.purchase_price > 0:
            return ((self.sale_price - self.purchase_price) / self.purchase_price) * 100
        return None

    @property
    def profit_amount(self) -> Optional[Decimal]:
        """Calcula la ganancia por unidad"""
        if self.purchase_price and self.sale_price:
            return self.sale_price - self.purchase_price
        return None

    @property
    def stock_value(self) -> Optional[Decimal]:
        """Calcula el valor del stock actual"""
        if self.current_stock and self.purchase_price:
            return self.current_stock * self.purchase_price
        return None

    @property
    def has_valid_accounting_setup(self) -> bool:
        """Verifica si tiene configuración contable válida"""
        if self.is_service:
            return self.sales_account_id is not None
        else:  # Producto físico
            return (
                self.sales_account_id is not None and
                self.purchase_account_id is not None and
                (not self.manage_inventory or self.inventory_account_id is not None)
            )

    def activate(self) -> None:
        """Activa el producto"""
        self.status = ProductStatus.ACTIVE
        self.discontinuation_date = None

    def deactivate(self) -> None:
        """Desactiva el producto"""
        self.status = ProductStatus.INACTIVE

    def discontinue(self) -> None:
        """Descontinúa el producto"""
        self.status = ProductStatus.DISCONTINUED
        self.discontinuation_date = datetime.now(timezone.utc)

    def update_stock(self, quantity: Decimal, operation: str = "add") -> bool:
        """
        Actualiza el stock del producto
        
        Args:
            quantity: Cantidad a sumar o restar
            operation: "add" para sumar, "subtract" para restar
            
        Returns:
            True si la operación fue exitosa, False si no
        """
        if not self.requires_inventory_control:
            return False
            
        if self.current_stock is None:
            self.current_stock = Decimal('0')
            
        if operation == "add":
            self.current_stock += quantity
        elif operation == "subtract":
            if self.current_stock >= quantity:
                self.current_stock -= quantity
            else:
                return False  # No se puede reducir por debajo de 0
        else:
            return False
            
        return True

    def validate_product(self) -> List[str]:
        """
        Valida el producto y retorna lista de errores
        """
        errors = []
        
        # Validar código único
        if not self.code or len(self.code.strip()) == 0:
            errors.append("El código del producto es requerido")
            
        # Validar nombre
        if not self.name or len(self.name.strip()) == 0:
            errors.append("El nombre del producto es requerido")
            
        # Validar precios
        if self.purchase_price and self.purchase_price < 0:
            errors.append("El precio de compra no puede ser negativo")
            
        if self.sale_price and self.sale_price < 0:
            errors.append("El precio de venta no puede ser negativo")
            
        if self.min_sale_price and self.min_sale_price < 0:
            errors.append("El precio mínimo de venta no puede ser negativo")
            
        # Validar coherencia de precios
        if self.sale_price and self.min_sale_price and self.sale_price < self.min_sale_price:
            errors.append("El precio de venta no puede ser menor al precio mínimo")
            
        # Validar inventario
        if self.manage_inventory:
            if self.current_stock and self.current_stock < 0:
                errors.append("El stock actual no puede ser negativo")
                
            if self.min_stock and self.min_stock < 0:
                errors.append("El stock mínimo no puede ser negativo")
                
            if self.max_stock and self.max_stock < 0:
                errors.append("El stock máximo no puede ser negativo")
                
            if self.min_stock and self.max_stock and self.min_stock > self.max_stock:
                errors.append("El stock mínimo no puede ser mayor al stock máximo")
                
        # Validar configuración contable
        if not self.has_valid_accounting_setup:
            if self.is_service:
                errors.append("Los servicios deben tener cuenta de ventas configurada")
            else:
                errors.append("Los productos deben tener cuentas contables configuradas")
                
        return errors

    @classmethod
    def get_by_code(cls, db_session, code: str) -> Optional["Product"]:
        """Busca un producto por código"""
        return db_session.query(cls).filter(cls.code == code).first()

    @classmethod
    def get_active_products(cls, db_session) -> List["Product"]:
        """Obtiene todos los productos activos"""
        return db_session.query(cls).filter(cls.status == ProductStatus.ACTIVE).all()

    @classmethod
    def get_low_stock_products(cls, db_session) -> List["Product"]:
        """Obtiene productos con stock bajo"""
        return db_session.query(cls).filter(
            cls.manage_inventory == True,
            cls.current_stock <= cls.min_stock
        ).all()

    @classmethod
    def search_products(cls, db_session, search_term: str) -> List["Product"]:
        """Busca productos por código, nombre o descripción"""
        search_pattern = f"%{search_term}%"
        return db_session.query(cls).filter(
            cls.code.ilike(search_pattern) |
            cls.name.ilike(search_pattern) |
            cls.description.ilike(search_pattern)
        ).all()
