import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, asc, func

from app.models.product import Product, ProductStatus, ProductType, MeasurementUnit, TaxCategory
from app.models.journal_entry import JournalEntryLine
from app.models.account import Account
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductFilter, BulkProductOperation,
    BulkProductOperationResult, ProductStats
)
from app.utils.exceptions import (
    AccountingSystemException, ValidationError, DuplicateError
)


import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, asc, func

from app.models.product import Product, ProductStatus, ProductType, MeasurementUnit, TaxCategory
from app.models.journal_entry import JournalEntryLine
from app.models.account import Account
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductFilter, BulkProductOperation,
    BulkProductOperationResult, ProductStats
)
from app.utils.exceptions import (
    AccountingSystemException, ValidationError
)


class ProductService:
    """
    Servicio para gestión de productos y servicios
    """
    
    def __init__(self, db: Session):
        self.db = db

    def _generate_product_code(self, name: str, product_type: Optional[ProductType] = None) -> str:
        """
        Genera un código único para el producto basado en el nombre y tipo
        
        Args:
            name: Nombre del producto
            product_type: Tipo de producto
            
        Returns:
            Código único generado
        """
        # Obtener prefijo basado en el tipo de producto
        if product_type == ProductType.SERVICE:
            prefix = "SRV"
        elif product_type == ProductType.BOTH:
            prefix = "MIX"
        else:  # PRODUCT o None
            prefix = "PRD"
        
        # Limpiar el nombre para crear una base del código
        # Tomar las primeras letras significativas del nombre
        clean_name = ''.join(c.upper() for c in name if c.isalnum())[:6]
        if len(clean_name) < 3:
            clean_name = clean_name.ljust(3, 'X')
        
        # Buscar el siguiente número disponible
        base_code = f"{prefix}-{clean_name}"
        counter = 1
        
        while True:
            if counter == 1:
                candidate_code = base_code
            else:
                candidate_code = f"{base_code}-{counter:02d}"
            
            # Verificar si el código ya existe
            existing = self.db.query(Product).filter(Product.code == candidate_code).first()
            if not existing:
                return candidate_code
            
            counter += 1
            # Evitar bucle infinito
            if counter > 999:
                # Usar timestamp como fallback
                import time
                timestamp = str(int(time.time()))[-6:]
                return f"{prefix}-{timestamp}"

    def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        """Obtiene un producto por ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def create_product(self, product_data: ProductCreate, created_by_id: uuid.UUID) -> Product:
        """
        Crea un nuevo producto
        
        Args:
            product_data: Datos del producto a crear
            created_by_id: ID del usuario que crea el producto
            
        Returns:
            Producto creado
            
        Raises:
            ValidationError: Si los datos no son válidos o ya existe un producto con el mismo nombre
        """
        # Verificar que no exista un producto con el mismo nombre (case-sensitive)
        existing_name = self.db.query(Product).filter(Product.name == product_data.name).first()
        if existing_name:
            raise ValidationError(f"Ya existe un producto con nombre '{product_data.name}' (los nombres son case-sensitive)")
        
        # Verificar que no exista un producto con el mismo código de barras (si se especifica)
        if product_data.barcode:
            existing_barcode = self.db.query(Product).filter(Product.barcode == product_data.barcode).first()
            if existing_barcode:
                raise ValidationError(f"Ya existe un producto con código de barras '{product_data.barcode}'")
        
        # Verificar que no exista un producto con el mismo SKU (si se especifica)
        if product_data.sku:
            existing_sku = self.db.query(Product).filter(Product.sku == product_data.sku).first()
            if existing_sku:
                raise ValidationError(f"Ya existe un producto con SKU '{product_data.sku}'")
        
        # Validar cuentas contables si se especifican
        self._validate_accounting_accounts(product_data)
        
        # Crear diccionario con datos del producto
        product_dict = product_data.model_dump(exclude_unset=True)
        
        # Generar código automáticamente
        product_type = product_dict.get('product_type', ProductType.PRODUCT)
        generated_code = self._generate_product_code(product_data.name, product_type)
        product_dict['code'] = generated_code
        
        # Aplicar valores por defecto
        defaults = {
            'product_type': ProductType.PRODUCT,
            'status': ProductStatus.ACTIVE,
            'measurement_unit': MeasurementUnit.UNIT,
            'purchase_price': Decimal("0"),
            'sale_price': Decimal("0"),
            'min_sale_price': Decimal("0"),
            'suggested_price': Decimal("0"),
            'tax_category': TaxCategory.EXEMPT,
            'tax_rate': Decimal("0"),
            'manage_inventory': False,
            'current_stock': Decimal("0"),
            'min_stock': Decimal("0"),
            'max_stock': Decimal("0"),
            'reorder_point': Decimal("0")
        }
        
        # Aplicar valores por defecto solo para campos no especificados
        for key, default_value in defaults.items():
            if key not in product_dict or product_dict[key] is None:
                product_dict[key] = default_value
        
        # Crear el producto
        product = Product(**product_dict)
        
        # Validar el producto
        errors = product.validate_product()
        if errors:
            raise ValidationError(f"Error de validación: {'; '.join(errors)}")
        
        try:
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Error de integridad al crear producto: {str(e)}")

    def update_product(self, product_id: uuid.UUID, product_data: ProductUpdate, 
                      updated_by_id: uuid.UUID) -> Product:
        """
        Actualiza un producto existente
        
        Args:
            product_id: ID del producto a actualizar
            product_data: Datos de actualización
            updated_by_id: ID del usuario que actualiza
            
        Returns:
            Producto actualizado
            
        Raises:
            ValidationError: Si el producto no existe o los datos no son válidos
        """
        product = self.get_by_id(product_id)
        if not product:
            raise ValidationError(f"Producto con ID {product_id} no encontrado")
        
        update_data = product_data.model_dump(exclude_unset=True)
          # Verificar códigos únicos solo si se están actualizando
        if "code" in update_data and update_data["code"] != product.code:
            existing_code = self.db.query(Product).filter(
                and_(Product.code == update_data["code"], Product.id != product_id)
            ).first()
            if existing_code:
                raise ValidationError(f"Ya existe un producto con código '{update_data['code']}'")
        
        # Verificar nombre único solo si se está actualizando (case-sensitive)
        if "name" in update_data and update_data["name"] != product.name:
            existing_name = self.db.query(Product).filter(
                and_(Product.name == update_data["name"], Product.id != product_id)
            ).first()
            if existing_name:
                raise ValidationError(f"Ya existe un producto con nombre '{update_data['name']}' (los nombres son case-sensitive)")
        
        if "barcode" in update_data and update_data["barcode"] and update_data["barcode"] != product.barcode:
            existing_barcode = self.db.query(Product).filter(
                and_(Product.barcode == update_data["barcode"], Product.id != product_id)
            ).first()
            if existing_barcode:
                raise ValidationError(f"Ya existe un producto con código de barras '{update_data['barcode']}'")
        
        if "sku" in update_data and update_data["sku"] and update_data["sku"] != product.sku:
            existing_sku = self.db.query(Product).filter(
                and_(Product.sku == update_data["sku"], Product.id != product_id)
            ).first()
            if existing_sku:
                raise ValidationError(f"Ya existe un producto con SKU '{update_data['sku']}'")
        
        # Validar cuentas contables si se están actualizando
        if any(key in update_data for key in ["sales_account_id", "purchase_account_id", 
                                             "inventory_account_id", "cogs_account_id"]):
            # Crear un objeto temporal para validación
            temp_data = ProductUpdate(**{**product.__dict__, **update_data})
            self._validate_accounting_accounts(temp_data)
        
        # Aplicar actualizaciones
        for field, value in update_data.items():
            setattr(product, field, value)
        
        # Validar el producto actualizado
        errors = product.validate_product()
        if errors:
            raise ValidationError(f"Error de validación: {'; '.join(errors)}")
        
        try:
            self.db.commit()
            self.db.refresh(product)
            return product
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Error de integridad al actualizar producto: {str(e)}")

    def get_product_by_code(self, code: str) -> Optional[Product]:
        """Obtiene un producto por su código"""
        return self.db.query(Product).filter(Product.code == code).first()

    def get_active_products(self, limit: Optional[int] = None) -> List[Product]:
        """Obtiene productos activos"""
        query = self.db.query(Product).filter(Product.status == ProductStatus.ACTIVE)
        if limit:
            query = query.limit(limit)
        return query.all()

    def search_products(self, search_term: str, limit: Optional[int] = 100) -> List[Product]:
        """
        Busca productos por código, nombre o descripción
        
        Args:
            search_term: Término de búsqueda
            limit: Límite de resultados
            
        Returns:
            Lista de productos que coinciden con la búsqueda
        """
        search_pattern = f"%{search_term}%"
        query = self.db.query(Product).filter(
            or_(
                Product.code.ilike(search_pattern),
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
                Product.barcode.ilike(search_pattern),
                Product.sku.ilike(search_pattern)
            )
        )
        
        if limit:
            query = query.limit(limit)
            
        return query.all()

    def filter_products(self, filters: ProductFilter, page: int = 1, 
                       size: int = 50) -> Dict[str, Any]:
        """
        Filtra productos según criterios especificados
        
        Args:
            filters: Criterios de filtrado
            page: Número de página
            size: Tamaño de página
            
        Returns:
            Diccionario con productos filtrados y metadatos de paginación
        """
        query = self.db.query(Product)
        
        # Aplicar filtros
        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Product.code.ilike(search_pattern),
                    Product.name.ilike(search_pattern),
                    Product.description.ilike(search_pattern)
                )
            )
        
        if filters.product_type:
            query = query.filter(Product.product_type == filters.product_type)
        
        if filters.status:
            query = query.filter(Product.status == filters.status)
        
        if filters.category:
            query = query.filter(Product.category.ilike(f"%{filters.category}%"))
        
        if filters.subcategory:
            query = query.filter(Product.subcategory.ilike(f"%{filters.subcategory}%"))
        
        if filters.brand:
            query = query.filter(Product.brand.ilike(f"%{filters.brand}%"))
        
        if filters.tax_category:
            query = query.filter(Product.tax_category == filters.tax_category)
        
        if filters.manage_inventory is not None:
            query = query.filter(Product.manage_inventory == filters.manage_inventory)
        
        if filters.low_stock:
            query = query.filter(
                and_(
                    Product.manage_inventory == True,
                    Product.current_stock <= Product.min_stock
                )
            )
        
        if filters.needs_reorder:
            query = query.filter(
                and_(
                    Product.manage_inventory == True,
                    Product.current_stock <= Product.reorder_point
                )
            )
        
        if filters.min_price:
            query = query.filter(Product.sale_price >= filters.min_price)
        
        if filters.max_price:
            query = query.filter(Product.sale_price <= filters.max_price)
        
        # Obtener total
        total = query.count()
        
        # Aplicar paginación
        offset = (page - 1) * size
        products = query.offset(offset).limit(size).all()
        
        # Calcular número de páginas
        pages = (total + size - 1) // size
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }

    def activate_product(self, product_id: uuid.UUID) -> Product:
        """Activa un producto"""
        product = self.get_by_id(product_id)
        if not product:
            raise ValidationError(f"Producto con ID {product_id} no encontrado")
        
        product.activate()
        self.db.commit()
        self.db.refresh(product)
        return product

    def deactivate_product(self, product_id: uuid.UUID) -> Product:
        """Desactiva un producto"""
        product = self.get_by_id(product_id)
        if not product:
            raise ValidationError(f"Producto con ID {product_id} no encontrado")
        
        product.deactivate()
        self.db.commit()
        self.db.refresh(product)
        return product

    def discontinue_product(self, product_id: uuid.UUID) -> Product:
        """Descontinúa un producto"""
        product = self.get_by_id(product_id)
        if not product:
            raise ValidationError(f"Producto con ID {product_id} no encontrado")
        
        product.discontinue()
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_stock(self, product_id: uuid.UUID, quantity: Decimal, 
                    operation: str = "add") -> Product:
        """
        Actualiza el stock de un producto
        
        Args:
            product_id: ID del producto
            quantity: Cantidad a sumar o restar
            operation: "add" para sumar, "subtract" para restar
            
        Returns:
            Producto con stock actualizado
            
        Raises:
            ValidationError: Si el producto no existe o la operación no es válida
        """
        product = self.get_by_id(product_id)
        if not product:
            raise ValidationError(f"Producto con ID {product_id} no encontrado")
        
        if not product.requires_inventory_control:
            raise ValidationError("El producto no maneja control de inventario")
        
        success = product.update_stock(quantity, operation)
        if not success:
            if operation == "subtract":
                raise ValidationError(f"Stock insuficiente. Stock actual: {product.current_stock}, cantidad solicitada: {quantity}")
            else:
                raise ValidationError("Error al actualizar stock")
        
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_low_stock_products(self) -> List[Product]:
        """Obtiene productos con stock bajo"""
        return self.db.query(Product).filter(
            and_(
                Product.manage_inventory == True,
                Product.current_stock <= Product.min_stock,
                Product.status == ProductStatus.ACTIVE
            )
        ).all()

    def get_products_need_reorder(self) -> List[Product]:
        """Obtiene productos que necesitan reabastecimiento"""
        return self.db.query(Product).filter(
            and_(
                Product.manage_inventory == True,
                Product.current_stock <= Product.reorder_point,
                Product.status == ProductStatus.ACTIVE
            )
        ).all()

    def get_product_movements(self, product_id: uuid.UUID, 
                            limit: Optional[int] = None) -> List[JournalEntryLine]:
        """
        Obtiene los movimientos contables de un producto
        
        Args:
            product_id: ID del producto
            limit: Límite de resultados
            
        Returns:
            Lista de líneas de asientos contables relacionadas con el producto
        """
        from sqlalchemy.orm import joinedload
        
        query = self.db.query(JournalEntryLine).options(
            joinedload(JournalEntryLine.journal_entry),
            joinedload(JournalEntryLine.account),
            joinedload(JournalEntryLine.product),
            joinedload(JournalEntryLine.third_party)
        ).filter(
            JournalEntryLine.product_id == product_id
        ).order_by(desc(JournalEntryLine.created_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()

    def bulk_operation(self, operation_data: BulkProductOperation) -> BulkProductOperationResult:
        """
        Ejecuta operaciones masivas en productos
        
        Args:
            operation_data: Datos de la operación masiva
            
        Returns:
            Resultado de la operación masiva
        """
        successful_ids = []
        errors = []
        
        for product_id in operation_data.product_ids:
            try:
                if operation_data.operation == "activate":
                    self.activate_product(product_id)
                elif operation_data.operation == "deactivate":
                    self.deactivate_product(product_id)
                elif operation_data.operation == "discontinue":
                    self.discontinue_product(product_id)
                else:
                    errors.append({
                        "id": str(product_id),
                        "error": f"Operación '{operation_data.operation}' no válida"
                    })
                    continue
                
                successful_ids.append(product_id)
                
            except Exception as e:
                errors.append({
                    "id": str(product_id),
                    "error": str(e)
                })
        
        return BulkProductOperationResult(
            total_requested=len(operation_data.product_ids),
            total_processed=len(successful_ids),
            total_errors=len(errors),
            successful_ids=successful_ids,
            errors=errors
        )

    def get_product_stats(self) -> ProductStats:
        """
        Obtiene estadísticas generales de productos
        
        Returns:
            Estadísticas de productos
        """
        # Contar productos por estado
        total_products = self.db.query(Product).count()
        active_products = self.db.query(Product).filter(Product.status == ProductStatus.ACTIVE).count()
        inactive_products = self.db.query(Product).filter(Product.status == ProductStatus.INACTIVE).count()
        discontinued_products = self.db.query(Product).filter(Product.status == ProductStatus.DISCONTINUED).count()
        
        # Productos con inventario
        products_with_inventory = self.db.query(Product).filter(Product.manage_inventory == True).count()
        
        # Productos con stock bajo
        low_stock_products = self.db.query(Product).filter(
            and_(
                Product.manage_inventory == True,
                Product.current_stock <= Product.min_stock
            )
        ).count()
        
        # Productos que necesitan reorden
        products_need_reorder = self.db.query(Product).filter(
            and_(
                Product.manage_inventory == True,
                Product.current_stock <= Product.reorder_point
            )
        ).count()
        
        # Valor total del stock
        total_stock_value = self.db.query(
            func.sum(Product.current_stock * Product.purchase_price)
        ).filter(
            and_(
                Product.manage_inventory == True,
                Product.current_stock.isnot(None),
                Product.purchase_price.isnot(None)
            )
        ).scalar() or Decimal('0')
        
        # Categorías
        categories = self.db.query(
            Product.category, func.count(Product.id)
        ).filter(
            Product.category.isnot(None)
        ).group_by(Product.category).all()
        
        category_stats = [{"category": cat[0], "count": cat[1]} for cat in categories]
        
        # Marcas
        brands = self.db.query(
            Product.brand, func.count(Product.id)
        ).filter(
            Product.brand.isnot(None)
        ).group_by(Product.brand).all()
        
        brand_stats = [{"brand": brand[0], "count": brand[1]} for brand in brands]
        
        return ProductStats(
            total_products=total_products,
            active_products=active_products,
            inactive_products=inactive_products,
            discontinued_products=discontinued_products,
            products_with_inventory=products_with_inventory,
            low_stock_products=low_stock_products,
            products_need_reorder=products_need_reorder,
            total_stock_value=total_stock_value,
            categories=category_stats,
            brands=brand_stats
        )

    def delete_product(self, product_id: uuid.UUID) -> bool:
        """
        Elimina un producto (solo si no tiene movimientos contables)
        
        Args:
            product_id: ID del producto a eliminar
            
        Returns:
            True si se eliminó exitosamente
            
        Raises:
            ValidationError: Si el producto no existe o tiene movimientos contables
        """
        product = self.get_by_id(product_id)
        if not product:
            raise ValidationError(f"Producto con ID {product_id} no encontrado")
        
        # Verificar que no tenga movimientos contables
        movements = self.db.query(JournalEntryLine).filter(
            JournalEntryLine.product_id == product_id
        ).count()
        
        if movements > 0:
            raise ValidationError("No se puede eliminar un producto que tiene movimientos contables asociados")
        
        self.db.delete(product)
        self.db.commit()
        return True

    def _validate_accounting_accounts(self, product_data) -> None:
        """
        Valida que las cuentas contables especificadas existan y sean válidas
        
        Args:
            product_data: Datos del producto con cuentas contables
            
        Raises:
            ValidationError: Si alguna cuenta no es válida
        """
        account_fields = {
            "sales_account_id": "ventas",
            "purchase_account_id": "compras",
            "inventory_account_id": "inventario",
            "cogs_account_id": "costo de ventas"
        }
        
        for field, description in account_fields.items():
            account_id = getattr(product_data, field, None)
            if account_id:
                account = self.db.query(Account).filter(Account.id == account_id).first()
                if not account:
                    raise ValidationError(f"La cuenta de {description} especificada no existe")
                
                if not account.can_receive_movements:
                    raise ValidationError(f"La cuenta de {description} no puede recibir movimientos")

    def get_products_by_category(self, category: str) -> List[Product]:
        """Obtiene productos por categoría"""
        return self.db.query(Product).filter(
            and_(
                Product.category.ilike(f"%{category}%"),
                Product.status == ProductStatus.ACTIVE
            )
        ).all()

    def get_products_by_brand(self, brand: str) -> List[Product]:
        """Obtiene productos por marca"""
        return self.db.query(Product).filter(
            and_(
                Product.brand.ilike(f"%{brand}%"),
                Product.status == ProductStatus.ACTIVE
            )
        ).all()

    def validate_product_for_transaction(self, product_id: uuid.UUID, 
                                       transaction_type: str) -> bool:
        """
        Valida que un producto pueda ser usado en una transacción específica
        
        Args:
            product_id: ID del producto
            transaction_type: Tipo de transacción ("sale" o "purchase")
            
        Returns:
            True si el producto es válido para la transacción
            
        Raises:
            ValidationError: Si el producto no existe, no está activo o no tiene configuración contable adecuada
        """
        product = self.get_by_id(product_id)
        if not product:
            raise ValidationError(f"Producto con ID {product_id} no encontrado")
        
        if product.status != ProductStatus.ACTIVE:
            raise ValidationError(f"El producto '{product.code}' no está activo")
        
        # Validar configuración contable según el tipo de transacción
        if transaction_type == "sale":
            if not product.sales_account_id:
                raise ValidationError(f"El producto '{product.code}' no tiene cuenta de ventas configurada")
        elif transaction_type == "purchase":
            if not product.purchase_account_id:
                raise ValidationError(f"El producto '{product.code}' no tiene cuenta de compras configurada")
        
        return True
