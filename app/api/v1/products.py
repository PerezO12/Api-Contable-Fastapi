import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.product import ProductType, ProductStatus, MeasurementUnit, TaxCategory
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductRead, ProductSummary, ProductList,
    ProductFilter, ProductMovement, ProductStock, BulkProductOperation,
    BulkProductOperationResult, ProductStats, ProductResponse,
    ProductDetailResponse, ProductListResponse
)
from app.services.product_service import ProductService
from app.utils.exceptions import ValidationError

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=http_status.HTTP_201_CREATED)
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Crear un nuevo producto
    
    Requiere:
    - Código único del producto
    - Nombre del producto
    - Configuración contable adecuada según el tipo
    """
    try:
        product_service = ProductService(db)
        product = product_service.create_product(product_in, current_user.id)
        
        return ProductResponse(
            success=True,
            message="Producto creado exitosamente",
            product=ProductRead.model_validate(product)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/", response_model=ProductListResponse)
def list_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Buscar en código, nombre o descripción"),
    product_type: Optional[ProductType] = Query(None, description="Filtrar por tipo de producto"),
    product_status: Optional[ProductStatus] = Query(None, description="Filtrar por estado"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    brand: Optional[str] = Query(None, description="Filtrar por marca"),
    manage_inventory: Optional[bool] = Query(None, description="Filtrar por manejo de inventario"),
    low_stock: Optional[bool] = Query(None, description="Solo productos con stock bajo"),
    needs_reorder: Optional[bool] = Query(None, description="Solo productos que necesitan reorden"),
    min_price: Optional[Decimal] = Query(None, description="Precio mínimo"),
    max_price: Optional[Decimal] = Query(None, description="Precio máximo"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=100, description="Tamaño de página")
):
    """
    Listar productos con filtros y paginación
    """
    try:
        product_service = ProductService(db)
        
        # Crear filtros
        filters = ProductFilter(
            search=search,
            product_type=product_type,
            status=product_status,
            category=category,
            brand=brand,
            manage_inventory=manage_inventory,
            low_stock=low_stock,
            needs_reorder=needs_reorder,
            min_price=min_price,
            max_price=max_price
        )
        
        # Obtener productos filtrados
        result = product_service.filter_products(filters, page, size)
        
        # Convertir a ProductSummary
        product_summaries = [
            ProductSummary.model_validate(product) 
            for product in result["products"]
        ]
        
        product_list = ProductList(
            products=product_summaries,
            total=result["total"],
            page=result["page"],
            size=result["size"],
            pages=result["pages"]
        )
        
        return ProductListResponse(
            success=True,
            message="Productos obtenidos exitosamente",
            data=product_list,
            filters_applied=filters
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/search", response_model=List[ProductSummary])
def search_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    Buscar productos por término
    """
    try:
        product_service = ProductService(db)
        products = product_service.search_products(q, limit)
        
        return [ProductSummary.model_validate(product) for product in products]
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/active", response_model=List[ProductSummary])
def get_active_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Límite de resultados")
):
    """
    Obtener productos activos
    """
    try:
        product_service = ProductService(db)
        products = product_service.get_active_products(limit)
        
        return [ProductSummary.model_validate(product) for product in products]
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/low-stock", response_model=List[ProductStock])
def get_low_stock_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener productos con stock bajo
    """
    try:
        product_service = ProductService(db)
        products = product_service.get_low_stock_products()
        
        return [ProductStock.model_validate(product) for product in products]
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/need-reorder", response_model=List[ProductStock])
def get_products_need_reorder(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener productos que necesitan reabastecimiento
    """
    try:
        product_service = ProductService(db)
        products = product_service.get_products_need_reorder()
        
        return [ProductStock.model_validate(product) for product in products]
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/stats", response_model=ProductStats)
def get_product_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas de productos
    """
    try:
        product_service = ProductService(db)
        return product_service.get_product_stats()
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/code/{code}", response_model=ProductDetailResponse)
def get_product_by_code(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    code: str
):
    """
    Obtener producto por código
    """
    try:
        product_service = ProductService(db)
        product = product_service.get_product_by_code(code)
        
        if not product:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Producto con código '{code}' no encontrado"
            )
        
        # Obtener movimientos recientes
        movements = product_service.get_product_movements(product.id, limit=10)
        
        return ProductDetailResponse(
            product=ProductRead.model_validate(product),
            movements=[ProductMovement.model_validate(movement) for movement in movements],
            stock_info=ProductStock.model_validate(product) if product.requires_inventory_control else None,
            accounting_setup={
                "sales_account": product.sales_account.code if product.sales_account else None,
                "purchase_account": product.purchase_account.code if product.purchase_account else None,
                "inventory_account": product.inventory_account.code if product.inventory_account else None,
                "cogs_account": product.cogs_account.code if product.cogs_account else None,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID
):
    """
    Obtener producto por ID
    """
    try:
        product_service = ProductService(db)
        product = product_service.get_by_id(product_id)
        
        if not product:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {product_id} no encontrado"
            )
        
        # Obtener movimientos recientes
        movements = product_service.get_product_movements(product_id, limit=10)
        
        return ProductDetailResponse(
            product=ProductRead.model_validate(product),
            movements=[ProductMovement.model_validate(movement) for movement in movements],
            stock_info=ProductStock.model_validate(product) if product.requires_inventory_control else None,
            accounting_setup={
                "sales_account": product.sales_account.code if product.sales_account else None,
                "purchase_account": product.purchase_account.code if product.purchase_account else None,
                "inventory_account": product.inventory_account.code if product.inventory_account else None,
                "cogs_account": product.cogs_account.code if product.cogs_account else None,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID,
    product_in: ProductUpdate
):
    """
    Actualizar producto
    """
    try:
        product_service = ProductService(db)
        product = product_service.update_product(product_id, product_in, current_user.id)
        
        return ProductResponse(
            success=True,
            message="Producto actualizado exitosamente",
            product=ProductRead.model_validate(product)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/{product_id}/activate", response_model=ProductResponse)
def activate_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID
):
    """
    Activar producto
    """
    try:
        product_service = ProductService(db)
        product = product_service.activate_product(product_id)
        
        return ProductResponse(
            success=True,
            message="Producto activado exitosamente",
            product=ProductRead.model_validate(product)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/{product_id}/deactivate", response_model=ProductResponse)
def deactivate_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID
):
    """
    Desactivar producto
    """
    try:
        product_service = ProductService(db)
        product = product_service.deactivate_product(product_id)
        
        return ProductResponse(
            success=True,
            message="Producto desactivado exitosamente",
            product=ProductRead.model_validate(product)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/{product_id}/discontinue", response_model=ProductResponse)
def discontinue_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID
):
    """
    Descontinuar producto
    """
    try:
        product_service = ProductService(db)
        product = product_service.discontinue_product(product_id)
        
        return ProductResponse(
            success=True,
            message="Producto descontinuado exitosamente",
            product=ProductRead.model_validate(product)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/{product_id}/stock/add", response_model=ProductResponse)
def add_stock(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID,
    quantity: float = Query(..., gt=0, description="Cantidad a agregar")
):
    """
    Agregar stock al producto
    """
    try:
        product_service = ProductService(db)
        product = product_service.update_stock(product_id, Decimal(str(quantity)), "add")
        
        return ProductResponse(
            success=True,
            message=f"Stock agregado exitosamente. Nuevo stock: {product.current_stock}",
            product=ProductRead.model_validate(product)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/{product_id}/stock/subtract", response_model=ProductResponse)
def subtract_stock(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID,
    quantity: float = Query(..., gt=0, description="Cantidad a restar")
):
    """
    Restar stock del producto
    """
    try:
        product_service = ProductService(db)
        product = product_service.update_stock(product_id, Decimal(str(quantity)), "subtract")
        
        return ProductResponse(
            success=True,
            message=f"Stock restado exitosamente. Nuevo stock: {product.current_stock}",
            product=ProductRead.model_validate(product)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/{product_id}/movements", response_model=List[ProductMovement])
def get_product_movements(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200, description="Límite de resultados")
):
    """
    Obtener movimientos contables del producto
    """
    try:
        product_service = ProductService(db)
        movements = product_service.get_product_movements(product_id, limit)
        
        return [ProductMovement.model_validate(movement) for movement in movements]
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/bulk-operation", response_model=BulkProductOperationResult)
def bulk_product_operation(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    operation_data: BulkProductOperation
):
    """
    Ejecutar operación masiva en productos
    
    Operaciones disponibles:
    - activate: Activar productos
    - deactivate: Desactivar productos
    - discontinue: Descontinuar productos
    """
    try:
        product_service = ProductService(db)
        result = product_service.bulk_operation(operation_data)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.delete("/{product_id}", response_model=ProductResponse)
def delete_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID
):
    """
    Eliminar producto
    
    Solo se puede eliminar si no tiene movimientos contables asociados
    """
    try:
        product_service = ProductService(db)
        success = product_service.delete_product(product_id)
        
        if success:
            return ProductResponse(
                success=True,
                message="Producto eliminado exitosamente"
            )
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="No se pudo eliminar el producto"
            )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
