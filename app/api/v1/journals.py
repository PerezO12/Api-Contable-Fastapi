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
    JournalSequenceInfo, JournalResetSequence, JournalDeleteValidation,
    BankJournalConfigCreate, BankJournalConfigUpdate, BankJournalConfigRead,
    BankJournalConfigValidation, JournalWithBankConfig
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
    
    - **name**: Nombre descriptivo del diario    - **code**: Código único del diario
    - **type**: Tipo de diario (sale, purchase, cash, bank, miscellaneous)
    - **sequence_prefix**: Prefijo único para la secuencia (ej: VEN, COM, CAJ)
    - **default_account_id**: Cuenta contable por defecto (opcional)
    """
    try:
        journal_service = JournalService(db)
        journal = await journal_service.create_journal(journal_data, current_user.id)
        
        # Recargar con conteo correcto para la respuesta
        journal_data_with_count = await journal_service.get_journal_by_id_with_count(journal.id)
        if not journal_data_with_count:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al recargar journal creado"
            )
        return JournalDetail.from_journal_with_count(
            journal_data_with_count['journal'],
            journal_data_with_count['total_journal_entries']
        )
        
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
            search=search        )
        
        journals_data = await journal_service.get_journals_list(
            filters=filters,
            skip=skip,
            limit=limit,
            order_by=order_by,
            order_dir=order_dir
        )
          # Convertir a JournalListItem manejando la serialización correctamente
        journals = []
        for data in journals_data:
            # Crear copia del diccionario para manipular
            journal_dict = data.copy()
            
            # Serializar default_account si existe
            if journal_dict.get('default_account'):
                account = journal_dict['default_account']
                journal_dict['default_account'] = {
                    'id': str(account.id),
                    'code': account.code,
                    'name': account.name,
                    'account_type': account.account_type
                }
            
            journals.append(JournalListItem(**journal_dict))
        
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
        print(f"🔍 Obteniendo journal {journal_id}")
        
        journal_data = await journal_service.get_journal_by_id_with_count(journal_id)
        print(f"📊 Journal data obtenido: {journal_data is not None}")
        
        if not journal_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diario con ID {journal_id} no encontrado"
            )
        
        print(f"📊 Journal: {journal_data['journal']}")
        print(f"📊 Count: {journal_data['total_journal_entries']}")
        print(f"📊 Default account: {journal_data['journal'].default_account}")
        print(f"📊 Created by: {journal_data['journal'].created_by}")
        
        # Crear JournalDetail usando el método from_journal_with_count
        journal_detail = JournalDetail.from_journal_with_count(
            journal_data['journal'],
            journal_data['total_journal_entries']
        )
        print(f"✅ JournalDetail creado exitosamente")
        
        return journal_detail
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en get_journal: {e}")
        print(f"❌ Tipo de error: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
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
        
        # Recargar con conteo correcto para la respuesta
        journal_data_with_count = await journal_service.get_journal_by_id_with_count(journal_id)
        if not journal_data_with_count:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al recargar journal actualizado"
            )
        return JournalDetail.from_journal_with_count(
            journal_data_with_count['journal'],
            journal_data_with_count['total_journal_entries']
        )
        
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


@router.post("/validate-deletion", response_model=List[JournalDeleteValidation])
async def validate_journals_deletion(
    journal_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validar si los diarios especificados pueden ser eliminados
    
    Verifica dependencias como:
    - Asientos contables asociados
    - Si es diario por defecto para algún tipo
    - Facturas asociadas
    """
    from sqlalchemy import text
    
    validations = []
    
    for journal_id in journal_ids:
        try:
            # Validar que el journal existe
            journal_service = JournalService(db)
            journal = await journal_service.get_journal_by_id(journal_id)
            
            if not journal:
                validations.append(JournalDeleteValidation(
                    journal_id=str(journal_id),
                    can_delete=False,
                    blocking_reasons=["Diario no encontrado"],
                    warnings=[],
                    dependencies={}
                ))
                continue
                
            can_delete = True
            blocking_reasons = []
            warnings = []
            dependencies = {
                "journal_name": journal.name,
                "journal_code": journal.code,
                "journal_type": journal.type.value if journal.type else ""
            }
            
            # Verificar asientos contables
            result = await db.execute(text("""
                SELECT COUNT(*) 
                FROM journal_entries 
                WHERE journal_id = :journal_id
            """), {"journal_id": str(journal_id)})
            journal_entries_count = result.scalar() or 0
            
            if journal_entries_count > 0:
                can_delete = False
                blocking_reasons.append(f"Diario tiene {journal_entries_count} asientos contables asociados")
                dependencies["journal_entries_count"] = str(journal_entries_count)
            
            # Verificar si es diario por defecto en otros journals
            result = await db.execute(text("""
                SELECT COUNT(*) 
                FROM journals 
                WHERE default_account_id IN (
                    SELECT default_account_id 
                    FROM journals 
                    WHERE id = :journal_id
                )
                AND id != :journal_id
            """), {"journal_id": str(journal_id)})
            references_count = result.scalar() or 0
            
            if references_count > 0:
                warnings.append(f"Diario es usado como referencia por {references_count} otros diarios")
                dependencies["references_count"] = str(references_count)
            
            # Verificar facturas asociadas (si el diario se usa en facturas)
            result = await db.execute(text("""
                SELECT COUNT(*) 
                FROM invoices 
                WHERE journal_id = :journal_id
            """), {"journal_id": str(journal_id)})
            invoices_count = result.scalar() or 0
            
            if invoices_count > 0:
                can_delete = False
                blocking_reasons.append(f"Diario tiene {invoices_count} facturas asociadas")
                dependencies["invoices_count"] = str(invoices_count)
            
            validations.append(JournalDeleteValidation(
                journal_id=str(journal_id),
                can_delete=can_delete,
                blocking_reasons=blocking_reasons,
                warnings=warnings,
                dependencies=dependencies
            ))
            
        except Exception as e:
            validations.append(JournalDeleteValidation(
                journal_id=str(journal_id),
                can_delete=False,
                blocking_reasons=[f"Error al validar: {str(e)}"],
                warnings=[],
                dependencies={}
            ))
    
    return validations


# Endpoints para configuración bancaria

@router.post("/{journal_id}/bank-config", response_model=JournalWithBankConfig)
async def create_bank_config(
    journal_id: uuid.UUID,
    config_data: BankJournalConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crear configuración bancaria para un diario
    
    Solo válido para diarios tipo BANK
    """
    try:
        journal_service = JournalService(db)
        journal = await journal_service.create_bank_config(journal_id, config_data)
        return journal
        
    except JournalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diario no encontrado"
        )
    except JournalValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/{journal_id}/bank-config", response_model=BankJournalConfigRead)
async def get_bank_config(
    journal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener configuración bancaria de un diario
    """
    try:
        journal_service = JournalService(db)
        config = await journal_service.get_bank_config(journal_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuración bancaria no encontrada"
            )
        return config
        
    except JournalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diario no encontrado"
        )


@router.put("/{journal_id}/bank-config", response_model=BankJournalConfigRead)
async def update_bank_config(
    journal_id: uuid.UUID,
    config_data: BankJournalConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualizar configuración bancaria de un diario
    """
    try:
        journal_service = JournalService(db)
        config = await journal_service.update_bank_config(journal_id, config_data)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuración bancaria no encontrada"
            )
        return config
        
    except JournalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diario o configuración bancaria no encontrada"
        )
    except JournalValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete("/{journal_id}/bank-config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_config(
    journal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Eliminar configuración bancaria de un diario
    """
    try:
        journal_service = JournalService(db)
        await journal_service.delete_bank_config(journal_id)
        
    except JournalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diario o configuración bancaria no encontrada"
        )


@router.post("/{journal_id}/bank-config/validate", response_model=BankJournalConfigValidation)
async def validate_bank_config(
    journal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validar configuración bancaria de un diario
    """
    try:
        journal_service = JournalService(db)
        validation = await journal_service.validate_bank_config(journal_id)
        return validation
        
    except JournalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diario no encontrado"
        )
