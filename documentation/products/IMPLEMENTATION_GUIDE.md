# Guía de Implementación - Sistema de Productos

## Introducción

Esta guía proporciona instrucciones paso a paso para desarrolladores que necesiten entender, mantener o extender el sistema de gestión de productos implementado en la API Contable.

## Arquitectura del Sistema

### Patrón de Diseño

El sistema sigue el patrón **Repository-Service-Controller** con las siguientes capas:

```
┌─────────────────────────────────────────────────────────────┐
│                    Capa de Presentación                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   FastAPI       │  │   Pydantic      │  │   OpenAPI   │  │
│  │   Controllers   │  │   Schemas       │  │   Docs      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Capa de Negocio                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Product       │  │   Validation    │  │   Business  │  │
│  │   Service       │  │   Logic         │  │   Rules     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Capa de Datos                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   SQLAlchemy    │  │   PostgreSQL    │  │   Alembic   │  │
│  │   Models        │  │   Database      │  │   Migrations│  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principales

1. **Modelos (Models)**: Definición de la estructura de datos
2. **Esquemas (Schemas)**: Validación y serialización de datos
3. **Servicios (Services)**: Lógica de negocio
4. **Controladores (Controllers)**: Endpoints de la API
5. **Migraciones (Migrations)**: Evolución de la base de datos

## Estructura de Archivos

```
app/
├── models/
│   ├── __init__.py
│   ├── product.py              # Modelo de datos del producto
│   └── journal_entry.py        # Modelo actualizado con productos
├── schemas/
│   ├── __init__.py
│   ├── product.py              # Esquemas Pydantic de productos
│   └── journal_entry.py        # Esquemas actualizados
├── services/
│   ├── product_service.py      # Lógica de negocio de productos
│   └── journal_entry_service.py # Servicio actualizado
├── api/
│   └── v1/
│       ├── __init__.py
│       └── products.py         # Endpoints REST de productos
└── db/
    └── session.py              # Configuración de base de datos

alembic/
└── versions/
    └── [timestamp]_add_products.py  # Migración de productos

tests/
├── test_product_model.py       # Tests del modelo
├── test_product_service.py     # Tests del servicio
├── test_product_api.py         # Tests de la API
└── test_journal_entry_with_products.py  # Tests de integración
```

## Implementación Detallada

### 1. Modelo de Datos (Product)

#### Archivo: `app/models/product.py`

```python
from sqlalchemy import Column, String, Decimal, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from .base import Base

class ProductType(str, enum.Enum):
    PRODUCT = "product"
    SERVICE = "service"
    BOTH = "both"

class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"

class Product(Base):
    __tablename__ = "products"
    
    # Campos principales
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(String(1000))
    
    # Tipo y estado
    product_type = Column(Enum(ProductType), nullable=False, default=ProductType.PRODUCT)
    status = Column(Enum(ProductStatus), nullable=False, default=ProductStatus.ACTIVE)
    
    # Inventario
    current_stock = Column(Decimal(15, 4), nullable=False, default=0)
    min_stock = Column(Decimal(15, 4), nullable=False, default=0)
    max_stock = Column(Decimal(15, 4), nullable=False, default=0)
    
    # Precios
    cost_price = Column(Decimal(15, 4), nullable=False, default=0)
    sale_price = Column(Decimal(15, 4), nullable=False, default=0)
    
    # Relaciones con cuentas contables
    income_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    expense_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    inventory_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    
    # Relaciones
    income_account = relationship("Account", foreign_keys=[income_account_id])
    expense_account = relationship("Account", foreign_keys=[expense_account_id])
    inventory_account = relationship("Account", foreign_keys=[inventory_account_id])
    
    # Campos de auditoría
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
```

#### Puntos Clave del Modelo:

1. **Identificación única**: UUID como clave primaria
2. **Código único**: Índice único para búsquedas rápidas
3. **Enums tipados**: Para tipos y estados del producto
4. **Precisión decimal**: Para precios y cantidades
5. **Relaciones FK**: Con cuentas contables y usuarios
6. **Auditoría completa**: Timestamps y usuarios de creación/modificación

### 2. Esquemas Pydantic

#### Archivo: `app/schemas/product.py`

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid
from .product_enums import ProductType, ProductStatus, MeasurementUnit

class ProductBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    product_type: ProductType = ProductType.PRODUCT
    status: ProductStatus = ProductStatus.ACTIVE
    
    # Validaciones personalizadas
    @validator('code')
    def code_must_be_alphanumeric(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must be alphanumeric with optional hyphens or underscores')
        return v.upper()

class ProductCreate(ProductBase):
    current_stock: Decimal = Field(default=0, ge=0)
    min_stock: Decimal = Field(default=0, ge=0)
    max_stock: Decimal = Field(default=0, ge=0)
    cost_price: Decimal = Field(..., gt=0)
    sale_price: Decimal = Field(..., gt=0)
    
    # Validación de coherencia de precios
    @validator('max_stock')
    def max_stock_greater_than_min(cls, v, values):
        if 'min_stock' in values and v < values['min_stock']:
            raise ValueError('Max stock must be greater than or equal to min stock')
        return v

class ProductRead(ProductBase):
    id: uuid.UUID
    profit_margin: Optional[Decimal]  # Campo calculado
    stock_status: str  # Campo calculado
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
```

#### Validaciones Implementadas:

1. **Longitud de campos**: Límites realistas
2. **Valores positivos**: Para precios y stocks
3. **Coherencia de datos**: Stock mínimo vs máximo
4. **Formato de código**: Alfanumérico con guiones/guiones bajos
5. **Campos calculados**: Margen de ganancia, estado de stock

### 3. Servicio de Negocio

#### Archivo: `app/services/product_service.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from ..models.product import Product, ProductStatus
from ..schemas.product import ProductCreate, ProductUpdate, ProductFilter
from .base_service import BaseService

class ProductService(BaseService[Product, ProductCreate, ProductUpdate]):
    
    def __init__(self, db: Session):
        super().__init__(Product, db)
    
    def get_by_code(self, code: str) -> Optional[Product]:
        """Obtener producto por código único"""
        return self.db.query(Product).filter(
            Product.code == code.upper(),
            Product.is_active == True
        ).first()
    
    def filter_products(self, filters: ProductFilter) -> List[Product]:
        """Filtrar productos con criterios múltiples"""
        query = self.db.query(Product).filter(Product.is_active == True)
        
        # Aplicar filtros dinámicamente
        if filters.product_type:
            query = query.filter(Product.product_type == filters.product_type)
        
        if filters.status:
            query = query.filter(Product.status == filters.status)
        
        if filters.low_stock:
            query = query.filter(Product.current_stock <= Product.min_stock)
        
        if filters.search_term:
            search = f"%{filters.search_term}%"
            query = query.filter(
                or_(
                    Product.code.ilike(search),
                    Product.name.ilike(search),
                    Product.description.ilike(search)
                )
            )
        
        # Ordenamiento dinámico
        if filters.sort_by:
            order_field = getattr(Product, filters.sort_by, None)
            if order_field:
                if filters.sort_order == "desc":
                    query = query.order_by(order_field.desc())
                else:
                    query = query.order_by(order_field.asc())
        
        return query.offset(filters.skip).limit(filters.limit).all()
    
    def adjust_stock(self, product_id: uuid.UUID, adjustment: StockAdjustment) -> Product:
        """Ajustar stock del producto"""
        product = self.get(product_id)
        if not product:
            raise ValueError("Product not found")
        
        # Calcular nuevo stock
        if adjustment.adjustment_type == "increase":
            new_stock = product.current_stock + adjustment.quantity
        elif adjustment.adjustment_type == "decrease":
            new_stock = product.current_stock - adjustment.quantity
            if new_stock < 0:
                raise ValueError("Insufficient stock")
        elif adjustment.adjustment_type == "set":
            new_stock = adjustment.quantity
        
        # Actualizar stock
        product.current_stock = new_stock
        product.updated_at = datetime.utcnow()
        
        # Crear movimiento de inventario
        movement = self._create_stock_movement(product, adjustment)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def validate_for_transaction(self, product_id: uuid.UUID, quantity: Decimal) -> bool:
        """Validar producto para uso en transacciones"""
        product = self.get(product_id)
        
        if not product:
            raise ValueError("Product not found")
        
        if product.status != ProductStatus.ACTIVE:
            raise ValueError("Product is not active")
        
        if product.current_stock < quantity:
            raise ValueError("Insufficient stock")
        
        return True
```

#### Características del Servicio:

1. **Herencia de BaseService**: Reutilización de CRUD básico
2. **Métodos especializados**: Búsqueda por código, filtros avanzados
3. **Gestión de stock**: Ajustes con validaciones
4. **Validaciones de negocio**: Para uso en transacciones
5. **Transacciones de DB**: Commits explícitos para operaciones críticas

### 4. Controlador API

#### Archivo: `app/api/v1/products.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...database import get_db
from ...services.product_service import ProductService
from ...schemas.product import ProductCreate, ProductRead, ProductUpdate
from ...core.auth import get_current_user

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Crear un nuevo producto"""
    service = ProductService(db)
    
    # Verificar código único
    existing = service.get_by_code(product.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with code '{product.code}' already exists"
        )
    
    try:
        return service.create(product, created_by=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    product_type: Optional[str] = None,
    status: Optional[str] = None,
    is_active: bool = True,
    low_stock: bool = False,
    search_term: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Listar productos con filtros"""
    service = ProductService(db)
    
    filters = ProductFilter(
        skip=skip,
        limit=limit,
        product_type=product_type,
        status=status,
        is_active=is_active,
        low_stock=low_stock,
        search_term=search_term,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return service.filter_products(filters)

@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener producto por ID"""
    service = ProductService(db)
    product = service.get(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualizar producto existente"""
    service = ProductService(db)
    
    try:
        return service.update(product_id, product_update, updated_by=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{product_id}")
async def delete_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Eliminar producto (soft delete)"""
    service = ProductService(db)
    
    if not service.delete(product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {"message": "Product deleted successfully"}
```

#### Características del Controlador:

1. **Documentación automática**: Con OpenAPI/Swagger
2. **Validación de entrada**: Query parameters con límites
3. **Manejo de errores**: HTTPException con códigos apropiados
4. **Autenticación**: Middleware de usuario actual
5. **Responses tipadas**: Con Pydantic models

### 5. Migración de Base de Datos

#### Archivo: `alembic/versions/[timestamp]_add_products.py`

```python
"""Add products table and journal entry product integration

Revision ID: 123abc456def
Revises: 789ghi012jkl
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '123abc456def'
down_revision = '789ghi012jkl'
branch_labels = None
depends_on = None

def upgrade():
    # Create product_type enum
    product_type_enum = postgresql.ENUM(
        'product', 'service', 'both',
        name='producttype'
    )
    product_type_enum.create(op.get_bind())
    
    # Create product_status enum
    product_status_enum = postgresql.ENUM(
        'active', 'inactive', 'discontinued',
        name='productstatus'
    )
    product_status_enum.create(op.get_bind())
    
    # Create measurement_unit enum
    measurement_unit_enum = postgresql.ENUM(
        'unit', 'kg', 'g', 'l', 'ml', 'm', 'cm', 'inch', 'foot',
        'm2', 'm3', 'hour', 'minute', 'piece', 'package', 'box',
        name='measurementunit'
    )
    measurement_unit_enum.create(op.get_bind())
    
    # Create products table
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('product_type', product_type_enum, nullable=False),
        sa.Column('status', product_status_enum, nullable=False),
        sa.Column('current_stock', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('min_stock', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('max_stock', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('cost_price', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('sale_price', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('tax_category', sa.String(length=50), nullable=True),
        sa.Column('income_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expense_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('inventory_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('measurement_unit', measurement_unit_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['expense_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['income_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['inventory_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Create indexes
    op.create_index(op.f('ix_products_code'), 'products', ['code'], unique=False)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    
    # Add transaction_origin to journal_entries
    transaction_origin_enum = postgresql.ENUM(
        'sale', 'purchase', 'adjustment', 'transfer', 'payment',
        'collection', 'opening', 'closing', 'other',
        name='transactionorigin'
    )
    transaction_origin_enum.create(op.get_bind())
    
    op.add_column('journal_entries', 
        sa.Column('transaction_origin', transaction_origin_enum, nullable=True)
    )
    
    # Add product fields to journal_entry_lines
    op.add_column('journal_entry_lines',
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('journal_entry_lines',
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=True)
    )
    op.add_column('journal_entry_lines',
        sa.Column('unit_price', sa.Numeric(precision=15, scale=4), nullable=True)
    )
    op.add_column('journal_entry_lines',
        sa.Column('discount_percentage', sa.Numeric(precision=5, scale=2), nullable=True)
    )
    op.add_column('journal_entry_lines',
        sa.Column('discount_amount', sa.Numeric(precision=15, scale=4), nullable=True)
    )
    op.add_column('journal_entry_lines',
        sa.Column('tax_percentage', sa.Numeric(precision=5, scale=2), nullable=True)
    )
    op.add_column('journal_entry_lines',
        sa.Column('tax_amount', sa.Numeric(precision=15, scale=4), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(None, 'journal_entry_lines', 'products', ['product_id'], ['id'])

def downgrade():
    # Remove foreign key and columns from journal_entry_lines
    op.drop_constraint(None, 'journal_entry_lines', type_='foreignkey')
    op.drop_column('journal_entry_lines', 'tax_amount')
    op.drop_column('journal_entry_lines', 'tax_percentage')
    op.drop_column('journal_entry_lines', 'discount_amount')
    op.drop_column('journal_entry_lines', 'discount_percentage')
    op.drop_column('journal_entry_lines', 'unit_price')
    op.drop_column('journal_entry_lines', 'quantity')
    op.drop_column('journal_entry_lines', 'product_id')
    
    # Remove transaction_origin from journal_entries
    op.drop_column('journal_entries', 'transaction_origin')
    
    # Drop products table
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_index(op.f('ix_products_code'), table_name='products')
    op.drop_table('products')
    
    # Drop enums
    sa.Enum(name='transactionorigin').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='measurementunit').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='productstatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='producttype').drop(op.get_bind(), checkfirst=False)
```

## Testing

### Estructura de Tests

```python
# tests/test_product_service.py
import pytest
from sqlalchemy.orm import Session
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate
from tests.conftest import db_session, sample_product

def test_create_product(db_session: Session):
    """Test crear producto"""
    service = ProductService(db_session)
    
    product_data = ProductCreate(
        code="TEST001",
        name="Test Product",
        cost_price=50.00,
        sale_price=75.00
    )
    
    product = service.create(product_data)
    
    assert product.id is not None
    assert product.code == "TEST001"
    assert product.profit_margin == 50.0

def test_get_by_code(db_session: Session, sample_product):
    """Test buscar por código"""
    service = ProductService(db_session)
    
    found = service.get_by_code("TEST001")
    
    assert found is not None
    assert found.name == sample_product.name

def test_adjust_stock(db_session: Session, sample_product):
    """Test ajuste de stock"""
    service = ProductService(db_session)
    
    adjustment = StockAdjustment(
        adjustment_type="increase",
        quantity=50,
        reason="Test adjustment"
    )
    
    updated = service.adjust_stock(sample_product.id, adjustment)
    
    assert updated.current_stock == sample_product.current_stock + 50
```

### Tests de Integración

```python
# tests/test_product_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_product_api():
    """Test endpoint crear producto"""
    product_data = {
        "code": "API001",
        "name": "API Test Product",
        "cost_price": 25.00,
        "sale_price": 40.00
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "API001"
    assert data["profit_margin"] == 60.0

def test_list_products_with_filters():
    """Test listar productos con filtros"""
    response = client.get("/api/v1/products/?product_type=product&status=active")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for product in data:
        assert product["product_type"] == "product"
        assert product["status"] == "active"
```

## Mejores Prácticas

### 1. Validación de Datos

```python
# Siempre validar en múltiples capas
@validator('sale_price')
def sale_price_greater_than_cost(cls, v, values):
    if 'cost_price' in values and v <= values['cost_price']:
        raise ValueError('Sale price must be greater than cost price')
    return v
```

### 2. Manejo de Errores

```python
# Usar excepciones específicas
try:
    product = service.create(product_data)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except IntegrityError as e:
    raise HTTPException(status_code=409, detail="Product code already exists")
```

### 3. Transacciones de Base de Datos

```python
# Usar transacciones explícitas para operaciones críticas
def adjust_stock(self, product_id: uuid.UUID, adjustment: StockAdjustment):
    try:
        # Operaciones múltiples
        product = self.update_stock(product_id, adjustment.quantity)
        movement = self.create_movement(product, adjustment)
        
        self.db.commit()
        return product
    except Exception:
        self.db.rollback()
        raise
```

### 4. Logging y Auditoría

```python
import logging

logger = logging.getLogger(__name__)

def create_product(self, product_data: ProductCreate):
    logger.info(f"Creating product with code: {product_data.code}")
    
    product = Product(**product_data.dict())
    self.db.add(product)
    self.db.commit()
    
    logger.info(f"Product created successfully: {product.id}")
    return product
```

### 5. Optimización de Consultas

```python
# Usar joins para evitar consultas N+1
def get_products_with_accounts(self):
    return self.db.query(Product)\
        .join(Product.income_account)\
        .join(Product.expense_account)\
        .options(
            joinedload(Product.income_account),
            joinedload(Product.expense_account)
        )\
        .all()
```

## Extensiones Futuras

### 1. Categorías de Productos

```python
class ProductCategory(Base):
    __tablename__ = "product_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"))
    
    # Relación jerárquica
    children = relationship("ProductCategory", backref=backref('parent', remote_side=[id]))

# Agregar a Product
category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"))
category = relationship("ProductCategory")
```

### 2. Historial de Precios

```python
class ProductPriceHistory(Base):
    __tablename__ = "product_price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    cost_price = Column(Decimal(15, 4))
    sale_price = Column(Decimal(15, 4))
    effective_date = Column(DateTime)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
```

### 3. Multi-almacén

```python
class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200))

class ProductStock(Base):
    __tablename__ = "product_stocks"
    
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), primary_key=True)
    current_stock = Column(Decimal(15, 4), default=0)
    min_stock = Column(Decimal(15, 4), default=0)
    max_stock = Column(Decimal(15, 4), default=0)
```

## Conclusión

Esta guía proporciona una base sólida para entender y extender el sistema de productos. El diseño modular y las mejores prácticas implementadas facilitan el mantenimiento y la evolución del sistema.

Para nuevas funcionalidades:

1. **Seguir el patrón establecido**: Model → Schema → Service → Controller
2. **Agregar tests completos**: Unitarios e integración
3. **Documentar cambios**: README y docstrings
4. **Crear migraciones**: Para cambios de base de datos
5. **Validar rendimiento**: Para consultas complejas

El sistema está preparado para crecer y adaptarse a nuevos requerimientos manteniendo la calidad y consistencia del código.
