from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field
from math import ceil

T = TypeVar('T')


class PagedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica"""
    items: List[T] = Field(..., description="Lista de elementos")
    total: int = Field(..., description="Total de elementos")
    page: int = Field(..., description="Página actual (basada en 1)")
    per_page: int = Field(..., description="Elementos por página")
    total_pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Si hay página siguiente")
    has_prev: bool = Field(..., description="Si hay página anterior")
    next_page: Optional[int] = Field(None, description="Número de página siguiente")
    prev_page: Optional[int] = Field(None, description="Número de página anterior")


def create_paged_response(
    items: List[T],
    total: int,
    skip: int,
    limit: int
) -> PagedResponse[T]:
    """
    Crea una respuesta paginada
    
    Args:
        items: Lista de elementos
        total: Total de elementos
        skip: Número de elementos omitidos
        limit: Límite de elementos por página
        
    Returns:
        PagedResponse con metadatos de paginación
    """
    # Calcular página actual (basada en 1)
    page = (skip // limit) + 1 if limit > 0 else 1
    
    # Calcular total de páginas
    total_pages = ceil(total / limit) if limit > 0 and total > 0 else 1
    
    # Calcular si hay páginas siguiente y anterior
    has_next = page < total_pages
    has_prev = page > 1
    
    # Calcular números de página siguiente y anterior
    next_page = page + 1 if has_next else None
    prev_page = page - 1 if has_prev else None
    
    return PagedResponse(
        items=items,
        total=total,
        page=page,
        per_page=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        next_page=next_page,
        prev_page=prev_page
    )
