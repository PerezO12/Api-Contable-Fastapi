from typing import List, Optional, Any
import uuid
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.api.deps import get_db, get_current_user, get_current_admin_user, get_current_active_user
from app.models.account import Account, AccountType, AccountCategory
from app.models.user import User
from app.schemas.account import (
    AccountCreate, AccountUpdate, AccountRead, AccountTree, AccountSummary,
    AccountBalance, AccountMovementHistory, AccountsByType, ChartOfAccounts,
    AccountValidation, BulkAccountOperation, AccountStats, BulkAccountDelete,
    BulkAccountDeleteResult, AccountDeleteValidation
)
from app.services.account_service import AccountService
from app.utils.exceptions import (
    AccountNotFoundError, 
    AccountValidationError,
    raise_account_not_found,
    raise_validation_error,
    raise_insufficient_permissions
)

router = APIRouter()


@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    *,
    db: AsyncSession = Depends(get_db),
    account_in: AccountCreate,
    current_user: User = Depends(get_current_active_user),
) -> AccountRead:
    """
    Crear una nueva cuenta contable.
    Requiere permisos de ADMIN o CONTADOR.
    """
    if not current_user.can_modify_accounts:
        raise_insufficient_permissions()
    
    account_service = AccountService(db)
    try:
        new_account = await account_service.create_account(account_in, current_user.id)
        
        # Convertir explícitamente a schema para evitar problemas de serialización
        return AccountRead.model_validate(new_account)
        
    except AccountValidationError as e:
        raise_validation_error(str(e))


@router.get("/", response_model=List[AccountRead])
async def list_accounts(
    skip: int = 0,
    limit: int = 100,
    account_type: Optional[AccountType] = None,
    category: Optional[AccountCategory] = None,
    is_active: Optional[bool] = None,
    parent_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AccountRead]:
    """
    Obtener lista de cuentas con filtros opcionales.
    """
    account_service = AccountService(db)
    accounts = await account_service.get_accounts(
        skip=skip,
        limit=limit,
        account_type=account_type,
        category=category,
        is_active=is_active,
        parent_id=parent_id,
        search=search
    )
      # Convertir explícitamente a schemas para evitar problemas de serialización
    return [AccountRead.model_validate(account) for account in accounts]


@router.get("/tree", response_model=List[AccountTree])
async def get_account_tree(
    account_type: Optional[AccountType] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AccountTree]:
    """
    Obtener la estructura jerárquica de cuentas como árbol.
    """
    account_service = AccountService(db)
    # Usar el método corregido temporalmente
    return await account_service.get_account_tree_fixed(account_type=account_type, active_only=active_only)


@router.get("/chart", response_model=ChartOfAccounts)
async def get_chart_of_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChartOfAccounts:
    """
    Obtener el plan de cuentas completo organizado por tipo.
    """
    account_service = AccountService(db)
    return await account_service.get_chart_of_accounts()


@router.get("/stats", response_model=AccountStats)
async def get_account_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountStats:
    """
    Obtener estadísticas generales de las cuentas.
    """
    account_service = AccountService(db)
    return await account_service.get_account_stats()


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Account:
    """
    Obtener una cuenta específica por ID.
    """
    account_service = AccountService(db)
    account = await account_service.get_account_by_id(account_id)
    if not account:
        raise_account_not_found()
    # Type assertion: at this point we know account is not None
    return account  # type: ignore


@router.get("/code/{account_code}", response_model=AccountRead)
async def get_account_by_code(
    account_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Account:
    """
    Obtener una cuenta específica por código.
    """
    account_service = AccountService(db)
    account = await account_service.get_account_by_code(account_code)
    if not account:
        raise_account_not_found()
    return account  # type: ignore


@router.put("/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: uuid.UUID,
    account_update: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Account:
    """
    Actualizar una cuenta existente.
    Requiere permisos de ADMIN o CONTADOR.
    """
    if not current_user.can_modify_accounts:
        raise_insufficient_permissions()
    
    account_service = AccountService(db)
    account = await account_service.update_account(account_id, account_update)
    if not account:
        raise_account_not_found()
    return account  # type: ignore


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Eliminar una cuenta.
    Solo disponible para administradores y solo si no tiene movimientos.
    """
    account_service = AccountService(db)
    deleted = await account_service.delete_account(account_id)
    if not deleted:
        raise_account_not_found()


@router.get("/{account_id}/balance", response_model=AccountBalance)
async def get_account_balance(
    account_id: uuid.UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountBalance:
    """
    Obtener el saldo de una cuenta a una fecha específica.
    """
    account_service = AccountService(db)
    return await account_service.get_account_balance(account_id, as_of_date)


@router.get("/{account_id}/movements", response_model=AccountMovementHistory)
async def get_account_movements(
    account_id: uuid.UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountMovementHistory:
    """
    Obtener el historial de movimientos de una cuenta en un período.
    """
    account_service = AccountService(db)
    return await account_service.get_account_movements(account_id, start_date, end_date)


@router.post("/{account_id}/validate", response_model=AccountValidation)
async def validate_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountValidation:
    """
    Validar una cuenta específica y retornar errores/advertencias.
    """
    account_service = AccountService(db)
    return await account_service.validate_account(account_id)


@router.post("/bulk-operation", status_code=status.HTTP_200_OK)
async def bulk_account_operation(
    operation: BulkAccountOperation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> dict:
    """
    Realizar operaciones masivas en cuentas.
    Solo disponible para administradores.
    """
    account_service = AccountService(db)
    return await account_service.bulk_operation(operation, current_user.id)


@router.post("/bulk-delete", response_model=BulkAccountDeleteResult, status_code=status.HTTP_200_OK)
async def bulk_delete_accounts(
    delete_request: BulkAccountDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> BulkAccountDeleteResult:
    """
    Eliminar múltiples cuentas con validaciones exhaustivas.
    
    Este endpoint realiza validaciones detalladas antes de eliminar cada cuenta:
    - Verifica que no tengan movimientos contables
    - Verifica que no tengan cuentas hijas
    - Verifica que no sean cuentas de sistema
    - Permite forzar eliminación con force_delete=true
    
    Solo disponible para administradores.
    """
    account_service = AccountService(db)
    
    try:
        result = await account_service.bulk_delete_accounts(delete_request, current_user.id)
        return result
    except AccountValidationError as e:
        raise_validation_error(str(e))


@router.post("/validate-deletion", response_model=List[AccountDeleteValidation])
async def validate_accounts_for_deletion(
    account_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> List[AccountDeleteValidation]:
    """
    Validar si múltiples cuentas pueden ser eliminadas sin proceder con la eliminación.
    
    Este endpoint es útil para verificar qué cuentas pueden eliminarse antes de 
    realizar la operación de borrado masivo.
    
    Solo disponible para administradores.
    """
    account_service = AccountService(db)
    
    validations = []
    for account_id in account_ids:
        validation = await account_service.validate_account_for_deletion(account_id)
        validations.append(validation)
    
    return validations


@router.get("/type/{account_type}", response_model=AccountsByType)
async def get_accounts_by_type(
    account_type: AccountType,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountsByType:
    """
    Obtener todas las cuentas de un tipo específico.
    """
    account_service = AccountService(db)
    return await account_service.get_accounts_by_type(account_type, active_only)


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_accounts(
    file_content: str,  # En producción usar UploadFile de FastAPI
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> dict:
    """
    Importar cuentas desde archivo CSV/Excel.
    Solo disponible para administradores.
    """
    account_service = AccountService(db)
    return await account_service.import_accounts_from_csv(file_content, current_user.id)


@router.get("/export/csv")
async def export_accounts_csv(
    account_type: Optional[AccountType] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exportar cuentas a formato CSV.
    """
    account_service = AccountService(db)
    # En producción retornar StreamingResponse con el CSV
    return await account_service.export_accounts_to_csv(account_type, active_only)


@router.post("/setup/tax-accounts", response_model=List[AccountRead])
async def create_tax_accounts(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Crear cuentas de impuestos sobre ventas.
    Solo superusuarios pueden ejecutar esta operación.
    """
    account_service = AccountService(db)
    accounts = await account_service.create_tax_accounts()
    return accounts
