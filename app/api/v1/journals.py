from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.journal import JournalType
from app.schemas.journal import (
    JournalCreate, JournalUpdate, JournalRead, JournalDetail, 
    JournalListItem, JournalFilter, JournalStats, 
    JournalSequenceInfo, JournalResetSequence
)
from app.services.journal_service import (
    JournalService, JournalNotFoundError, JournalValidationError, 
    JournalDuplicateError
)
from app.utils.pagination import PagedResponse, create_paged_response

router = APIRouter()


@router.post("/", response_model=JournalDetail, status_code=status.HTTP_201_CREATED)
async def create_journal(
    journal_data: JournalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crear un nuevo diario contable
    
    - **name**: Nombre descriptivo del diario
    - **code**: Código único del diario
    - **type**: Tipo de diario (sale, purchase, cash, bank, miscellaneous)
    - **sequence_prefix**: Prefijo único para la secuencia (ej: VEN, COM, CAJ)
    - **default_account_id**: Cuenta contable por defecto (opcional)
    """
    try:
        journal_service = JournalService(db)
        journal = await journal_service.create_journal(journal_data, current_user.id)
        
        # Recargar con relaciones para la respuesta
        journal = await journal_service.get_journal_by_id(journal.id)
        return journal
        
    except JournalDuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except JournalValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/", response_model=PagedResponse[JournalListItem])
async def get_journals(
    type: Optional[JournalType] = Query(None, description="Filtrar por tipo de diario"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    search: Optional[str] = Query(None, description="Buscar en nombre, código o descripción"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    order_by: str = Query("name", description="Campo para ordenar"),
    order_dir: str = Query("asc", regex="^(asc|desc)$", description="Dirección del ordenamiento"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener lista de diarios con filtros y paginación
    """
    try:
        journal_service = JournalService(db)
        
        filters = JournalFilter(
            type=type,
            is_active=is_active,
            search=search
        )
        
        journals = await journal_service.get_journals(
            filters=filters,
            skip=skip,
            limit=limit,
            order_by=order_by,
            order_dir=order_dir
        )
        
        total = await journal_service.count_journals(filters)
        
        return create_paged_response(
            items=journals,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener diarios: {str(e)}"
        )


@router.get("/{journal_id}", response_model=JournalDetail)
async def get_journal(
    journal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener un diario por ID
    """
    try:
        journal_service = JournalService(db)
        journal = await journal_service.get_journal_by_id(journal_id)
        
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diario con ID {journal_id} no encontrado"
            )
        
        return journal
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener diario: {str(e)}"
        )


@router.put("/{journal_id}", response_model=JournalDetail)
async def update_journal(
    journal_id: uuid.UUID,
    journal_data: JournalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualizar un diario existente
    """
    try:
        journal_service = JournalService(db)
        journal = await journal_service.update_journal(journal_id, journal_data)
        
        return journal
        
    except JournalNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except JournalValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete("/{journal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal(
    journal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Eliminar un diario
    
    Solo se puede eliminar si no tiene asientos contables asociados
    """
    try:
        journal_service = JournalService(db)
        await journal_service.delete_journal(journal_id)
        
    except JournalNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except JournalValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/{journal_id}/stats", response_model=JournalStats)
async def get_journal_stats(
    journal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener estadísticas de un diario
    """
    try:
        journal_service = JournalService(db)
        stats = await journal_service.get_journal_stats(journal_id)
        
        return stats
        
    except JournalNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{journal_id}/sequence", response_model=JournalSequenceInfo)
async def get_journal_sequence_info(
    journal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener información de la secuencia de numeración de un diario
    """
    try:
        journal_service = JournalService(db)
        sequence_info = await journal_service.get_sequence_info(journal_id)
        
        return sequence_info
        
    except JournalNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{journal_id}/sequence/reset", response_model=JournalDetail)
async def reset_journal_sequence(
    journal_id: uuid.UUID,
    reset_data: JournalResetSequence,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Resetear la secuencia de numeración de un diario
    
    **¡Cuidado!** Esta operación reinicia el contador de secuencia a 0
    """
    try:
        journal_service = JournalService(db)
        journal = await journal_service.reset_sequence(journal_id, reset_data.reason)
        
        return journal
        
    except JournalNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/by-type/{journal_type}", response_model=List[JournalListItem])
async def get_journals_by_type(
    journal_type: JournalType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener todos los diarios activos de un tipo específico
    """
    try:
        journal_service = JournalService(db)
        journals = await journal_service.get_journals_by_type(journal_type)
        
        return journals
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener diarios por tipo: {str(e)}"
        )


@router.get("/default/{journal_type}", response_model=Optional[JournalDetail])
async def get_default_journal_for_type(
    journal_type: JournalType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener el diario por defecto para un tipo específico
    """
    try:
        journal_service = JournalService(db)
        journal = await journal_service.get_default_journal_for_type(journal_type)
        
        return journal
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener diario por defecto: {str(e)}"
        )
