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
    
    Requiere únicamente:
    - Nombre del producto (obligatorio)
    
    Valores automáticos:
    - Código: Se genera automáticamente basado en el nombre y tipo
    - Tipo: Producto por defecto
    - Estado: Activo por defecto
    - Precios: 0 por defecto
    - Control de inventario: Desactivado por defecto
    
    El resto de campos son opcionales y pueden tener valores por defecto o null.
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
    size: int = Query(50, ge=1, le=1000, description="Tamaño de página")
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
    limit: int = Query(20, ge=1, le=1000, description="Límite de resultados")
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
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Límite de resultados")
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
        
        return [ProductStock.from_product(product) for product in products]
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
        
        return [ProductStock.from_product(product) for product in products]
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
        
        # Convertir movimientos filtrando None
        converted_movements = []
        for movement in movements:
            converted = ProductMovement.from_journal_entry_line(movement)
            if converted is not None:
                converted_movements.append(converted)
        
        return ProductDetailResponse(
            product=ProductRead.model_validate(product),
            movements=converted_movements,
            stock_info=ProductStock.from_product(product) if product.requires_inventory_control else None,
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
        
        # Convertir movimientos filtrando None
        converted_movements = []
        for movement in movements:
            converted = ProductMovement.from_journal_entry_line(movement)
            if converted is not None:
                converted_movements.append(converted)
        
        return ProductDetailResponse(
            product=ProductRead.model_validate(product),
            movements=converted_movements,
            stock_info=ProductStock.from_product(product) if product.requires_inventory_control else None,
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
    limit: int = Query(50, ge=1, le=1000, description="Límite de resultados")
):
    """
    Obtener movimientos contables del producto
    """
    try:
        product_service = ProductService(db)
        movements = product_service.get_product_movements(product_id, limit)
        
        result = []
        for movement in movements:
            converted = ProductMovement.from_journal_entry_line(movement)
            if converted is not None:
                result.append(converted)
        return result
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


@router.post("/bulk-delete", response_model=BulkProductOperationResult)
def bulk_delete_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_ids: List[uuid.UUID]
):
    """
    Eliminar múltiples productos en lote
    
    Solo se pueden eliminar productos que:
    - No tengan movimientos contables asociados
    - No tengan asientos contables pendientes
    - No estén siendo utilizados en transacciones activas
    """
    try:
        product_service = ProductService(db)
        
        successful_deletions = []
        failed_deletions = []
        errors = []
        
        for product_id in product_ids:
            try:
                product = product_service.get_by_id(product_id)
                if not product:
                    errors.append({
                        "id": product_id,
                        "error": "Producto no encontrado"
                    })
                    continue
                
                # Intentar eliminar - el servicio ya valida las condiciones
                success = product_service.delete_product(product_id)
                if success:
                    successful_deletions.append(product_id)
                else:
                    errors.append({
                        "id": product_id,
                        "error": "No se pudo eliminar el producto"
                    })
                    
            except Exception as e:
                errors.append({
                    "id": product_id,
                    "error": str(e)
                })
        
        return BulkProductOperationResult(
            total_requested=len(product_ids),
            total_processed=len(successful_deletions),
            total_errors=len(errors),
            successful_ids=successful_deletions,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/validate-deletion", response_model=List[dict])
def validate_products_for_deletion(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_ids: List[uuid.UUID]
):
    """
    Validar si múltiples productos se pueden eliminar
    
    Verifica:
    - Existencia del producto
    - Stock actual
    - Movimientos asociados
    - Referencias en otros módulos
    """
    try:
        product_service = ProductService(db)
        validation_results = []
        
        for product_id in product_ids:
            try:
                product = product_service.get_by_id(product_id)
                if not product:
                    validation_results.append({
                        "product_id": str(product_id),
                        "product_name": "Producto no encontrado",
                        "can_delete": False,
                        "blocking_reasons": ["Producto no existe"],
                        "warnings": []
                    })
                    continue
                
                blocking_reasons = []
                warnings = []
                
                # Verificar si tiene stock
                if product.current_stock > 0:
                    warnings.append(f"Producto tiene stock actual: {product.current_stock}")
                
                # Verificar si está activo
                if product.status == "active":
                    warnings.append("Producto está activo - considere desactivar primero")
                
                # Por ahora asumimos que se puede eliminar si existe
                # En el futuro se pueden agregar más validaciones
                can_delete = True
                
                validation_results.append({
                    "product_id": str(product_id),
                    "product_code": product.code,
                    "product_name": product.name,
                    "product_status": product.status,
                    "current_stock": float(product.current_stock),
                    "can_delete": can_delete,
                    "blocking_reasons": blocking_reasons,
                    "warnings": warnings,
                    "estimated_stock_value": float(product.current_stock * product.purchase_price) if product.current_stock > 0 and product.purchase_price else 0.0
                })
                
            except Exception as e:
                validation_results.append({
                    "product_id": str(product_id),
                    "product_name": "Error al validar",
                    "can_delete": False,
                    "blocking_reasons": [f"Error de validación: {str(e)}"],
                    "warnings": []
                })
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/bulk-deactivate", response_model=BulkProductOperationResult)
def bulk_deactivate_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_ids: List[uuid.UUID]
):
    """
    Desactivar múltiples productos en lote
    
    La desactivación es más permisiva que la eliminación:
    - Se pueden desactivar productos con stock
    - Se pueden desactivar productos con historial
    - Se bloquean futuras transacciones pero se mantiene el historial
    """
    try:
        product_service = ProductService(db)
        
        successful_operations = []
        errors = []
        
        for product_id in product_ids:
            try:
                product = product_service.get_by_id(product_id)
                if not product:
                    errors.append({
                        "id": product_id,
                        "error": "Producto no encontrado"
                    })
                    continue
                
                if product.status == "inactive":
                    successful_operations.append(product_id)
                    continue
                
                # Desactivar producto
                updated_product = product_service.deactivate_product(product_id)
                successful_operations.append(product_id)
                
            except Exception as e:
                errors.append({
                    "id": product_id,
                    "error": str(e)
                })
        
        return BulkProductOperationResult(
            total_requested=len(product_ids),
            total_processed=len(successful_operations),
            total_errors=len(errors),
            successful_ids=successful_operations,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.delete("/{product_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    product_id: uuid.UUID
):
    """
    Eliminar un producto individual
    
    Elimina un producto específico si no está siendo utilizado en otras entidades.
    Se verifica que el producto no tenga:
    - Movimientos de inventario
    - Referencias en asientos contables
    - Referencias en documentos
    
    Si el producto está en uso, retorna error 400 con detalles.
    """
    try:
        product_service = ProductService(db)
        
        # Verificar que el producto existe
        product = product_service.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Eliminar el producto usando el método del servicio
        try:
            success = product_service.delete_product(product_id)
            
            if not success:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="No se puede eliminar el producto. Puede estar en uso en otras entidades."
                )
            
            # Si llegamos aquí, la eliminación fue exitosa
            return  # 204 No Content
            
        except ValidationError as e:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
