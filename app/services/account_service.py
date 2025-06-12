import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account, AccountType, AccountCategory
from app.models.journal_entry import JournalEntryLine
from app.schemas.account import (
    AccountCreate, AccountUpdate, AccountTree, AccountSummary,
    AccountBalance, AccountMovementHistory, AccountsByType, ChartOfAccounts,
    AccountValidation, BulkAccountOperation, AccountStats, BulkAccountDelete,
    BulkAccountDeleteResult, AccountDeleteValidation
)
from app.utils.exceptions import AccountNotFoundError, AccountValidationError


class AccountService:
    """Servicio para operaciones de cuentas contables"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_account(self, account_data: AccountCreate, created_by_id: uuid.UUID) -> Account:
        """Crear una nueva cuenta contable"""
        
        # Validar que no exista una cuenta con el mismo código
        existing_result = await self.db.execute(
            select(Account).where(Account.code == account_data.code)
        )
        existing_account = existing_result.scalar_one_or_none()
        
        if existing_account:
            raise AccountValidationError(f"Ya existe una cuenta con el código {account_data.code}")
        
        # Validar cuenta padre si se especifica
        parent_account = None
        if account_data.parent_id:
            parent_result = await self.db.execute(
                select(Account).where(Account.id == account_data.parent_id)
            )
            parent_account = parent_result.scalar_one_or_none()
            
            if not parent_account:
                raise AccountValidationError("La cuenta padre especificada no existe")
            
            if parent_account.account_type != account_data.account_type:
                raise AccountValidationError("La cuenta debe ser del mismo tipo que su cuenta padre")
        
        # Crear la cuenta
        account = Account(
            code=account_data.code,
            name=account_data.name,
            description=account_data.description,
            account_type=account_data.account_type,
            category=account_data.category,
            parent_id=account_data.parent_id,
            level=parent_account.level + 1 if parent_account else 1,
            is_active=account_data.is_active,
            allows_movements=account_data.allows_movements,
            requires_third_party=account_data.requires_third_party,
            requires_cost_center=account_data.requires_cost_center,
            notes=account_data.notes,
            created_by_id=created_by_id
        )
        
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        
        return account

    async def get_accounts(
        self,
        skip: int = 0,
        limit: int = 100,
        account_type: Optional[AccountType] = None,
        category: Optional[AccountCategory] = None,
        is_active: Optional[bool] = None,
        parent_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None
    ) -> List[Account]:
        """Obtener lista de cuentas con filtros"""
        
        query = select(Account)
        
        # Aplicar filtros
        if account_type:
            query = query.where(Account.account_type == account_type)
        
        if category:
            query = query.where(Account.category == category)
        
        if is_active is not None:
            query = query.where(Account.is_active == is_active)
        
        if parent_id:
            query = query.where(Account.parent_id == parent_id)
        
        if search:
            search_filter = or_(
                Account.code.ilike(f"%{search}%"),
                Account.name.ilike(f"%{search}%"),
                Account.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        # Ordenar por código
        query = query.order_by(Account.code).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_account_by_id(self, account_id: uuid.UUID) -> Optional[Account]:
        """Obtener una cuenta por ID"""
        result = await self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_account_by_code(self, code: str) -> Optional[Account]:
        """Obtener una cuenta por código"""
        result = await self.db.execute(
            select(Account).where(Account.code == code)
        )
        return result.scalar_one_or_none()

    async def update_account(self, account_id: uuid.UUID, account_data: AccountUpdate) -> Optional[Account]:
        """Actualizar una cuenta"""
        account = await self.get_account_by_id(account_id)
        
        if not account:
            return None
        
        # Actualizar campos
        update_data = account_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)
        
        account.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(account)
        
        return account

    async def delete_account(self, account_id: uuid.UUID) -> bool:
        """Eliminar una cuenta"""
        account = await self.get_account_by_id(account_id)
        
        if not account:
            raise AccountNotFoundError("Cuenta no encontrada")
        
        # Verificar que no tenga movimientos
        movements_result = await self.db.execute(
            select(func.count(JournalEntryLine.id))
            .where(JournalEntryLine.account_id == account_id)
        )
        movements_count = movements_result.scalar()
        
        if movements_count and movements_count > 0:
            raise AccountValidationError("No se puede eliminar una cuenta con movimientos")
        
        # Verificar que no tenga cuentas hijas        if account.children:
            raise AccountValidationError("No se puede eliminar una cuenta que tiene cuentas hijas")
        
        await self.db.delete(account)
        await self.db.commit()
        
        return True
    
    async def get_account_tree(
        self, 
        account_type: Optional[AccountType] = None, 
        active_only: bool = True
    ) -> List[AccountTree]:
        """Obtener estructura jerárquica de cuentas"""
        
        # Obtener todas las cuentas de una vez para evitar lazy loading
        query = select(Account)
        
        if account_type:
            query = query.where(Account.account_type == account_type)
        
        if active_only:
            query = query.where(Account.is_active == True)
        
        query = query.order_by(Account.code)
        
        result = await self.db.execute(query)
        all_accounts = list(result.scalars().all())
        
        # Crear un diccionario para acceso rápido por ID
        accounts_dict = {account.id: account for account in all_accounts}
        
        # Construir la estructura de hijos para cada cuenta
        children_dict = {}
        for account in all_accounts:
            children_dict[account.id] = []
        
        for account in all_accounts:
            if account.parent_id and account.parent_id in children_dict:
                children_dict[account.parent_id].append(account)
        
        def build_tree(account: Account) -> AccountTree:
            # Obtener hijos desde nuestro diccionario en lugar de la relación lazy
            children_accounts = sorted(children_dict.get(account.id, []), key=lambda x: x.code)
            children = []
            
            for child in children_accounts:
                if not active_only or child.is_active:
                    children.append(build_tree(child))
            
            return AccountTree(
                id=account.id,
                code=account.code,
                name=account.name,
                account_type=account.account_type,
                level=account.level,
                balance=account.balance,
                is_active=account.is_active,
                allows_movements=account.allows_movements,
                children=children
            )
        
        # Solo procesar cuentas raíz (sin parent_id)
        root_accounts = [account for account in all_accounts if account.parent_id is None]
        return [build_tree(account) for account in sorted(root_accounts, key=lambda x: x.code)]

    async def get_chart_of_accounts(self) -> ChartOfAccounts:
        """Obtener plan de cuentas organizado por tipo"""
        
        # Obtener estadísticas básicas
        total_result = await self.db.execute(select(func.count(Account.id)))
        total_accounts = total_result.scalar() or 0
        
        active_result = await self.db.execute(
            select(func.count(Account.id)).where(Account.is_active == True)
        )
        active_accounts = active_result.scalar() or 0
        
        # Contar cuentas hoja (sin hijos)
        leaf_result = await self.db.execute(
            select(func.count(Account.id)).where(~Account.children.any())        
        )
        leaf_accounts = leaf_result.scalar() or 0
        
        # Obtener cuentas por tipo
        by_type = []
        
        for account_type in AccountType:
            accounts = await self.get_accounts(account_type=account_type, is_active=True)
            account_summaries = [
                AccountSummary(
                    id=acc.id,
                    code=acc.code,
                    name=acc.name,
                    account_type=acc.account_type,
                    balance=acc.balance,
                    is_active=acc.is_active,
                    allows_movements=acc.allows_movements
                ) for acc in accounts
            ]
            total_balance = sum((acc.balance for acc in accounts), Decimal('0'))
            
            by_type.append(AccountsByType(
                account_type=account_type,
                accounts=account_summaries,
                total_balance=total_balance
            ))
        
        return ChartOfAccounts(
            by_type=by_type,
            total_accounts=total_accounts,
            active_accounts=active_accounts,
            leaf_accounts=leaf_accounts
        )

    async def get_account_balance(
        self, 
        account_id: uuid.UUID, 
        as_of_date: Optional[date] = None
    ) -> AccountBalance:
        """Obtener saldo de una cuenta a una fecha específica"""
        
        account = await self.get_account_by_id(account_id)
        if not account:
            raise AccountNotFoundError("Cuenta no encontrada")
        
        # Query base para movimientos
        query = select(
            func.sum(JournalEntryLine.debit_amount).label('total_debits'),
            func.sum(JournalEntryLine.credit_amount).label('total_credits')
        ).where(JournalEntryLine.account_id == account_id)
        
        # Filtrar por fecha si se especifica
        if as_of_date:
            from app.models.journal_entry import JournalEntry
            query = query.join(JournalEntry).where(
                JournalEntry.entry_date <= as_of_date
            )
        
        result = await self.db.execute(query)
        balance_data = result.one()
        
        total_debits = balance_data.total_debits or Decimal('0')
        total_credits = balance_data.total_credits or Decimal('0')
        
        # Calcular saldo según naturaleza de la cuenta
        if account.normal_balance_side == "debit":
            net_balance = total_debits - total_credits
        else:
            net_balance = total_credits - total_debits
        return AccountBalance(
            account_id=account.id,
            account_code=account.code,
            account_name=account.name,
            debit_balance=total_debits,
            credit_balance=total_credits,
            net_balance=net_balance,
            normal_balance_side=account.normal_balance_side,
            as_of_date=as_of_date or date.today()
        )

    async def get_account_movements(
        self,
        account_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> AccountMovementHistory:
        """Obtener historial de movimientos de una cuenta"""
        
        account = await self.get_account_by_id(account_id)
        if not account:
            raise AccountNotFoundError("Cuenta no encontrada")
        
        # Query para movimientos
        from app.models.journal_entry import JournalEntry
        
        query = select(JournalEntryLine).join(JournalEntry).where(
            JournalEntryLine.account_id == account_id
        )
        
        if start_date:
            query = query.where(JournalEntry.entry_date >= start_date)
        
        if end_date:
            query = query.where(JournalEntry.entry_date <= end_date)
            query = query.order_by(desc(JournalEntry.entry_date), JournalEntryLine.line_number)
        
        result = await self.db.execute(query)
        movements = list(result.scalars().all())
        
        # Calcular saldos de apertura y cierre
        opening_balance = Decimal('0')  # TODO: Calcular balance de apertura
        closing_balance = Decimal('0')   # TODO: Calcular balance de cierre
        total_debits = sum((mov.debit_amount for mov in movements), Decimal('0'))
        total_credits = sum((mov.credit_amount for mov in movements), Decimal('0'))
        
        return AccountMovementHistory(
            account=AccountSummary(
                id=account.id,
                code=account.code,
                name=account.name,
                account_type=account.account_type,
                balance=account.balance,
                is_active=account.is_active,
                allows_movements=account.allows_movements
            ),
            movements=[],  # TODO: Mapear a AccountMovement schema
            period_start=start_date or date.today(),
            period_end=end_date or date.today(),
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            total_debits=total_debits,
            total_credits=total_credits
        )

    async def validate_account(self, account_id: uuid.UUID) -> AccountValidation:
        """Validar una cuenta específica"""
        
        account = await self.get_account_by_id(account_id)
        if not account:
            raise AccountNotFoundError("Cuenta no encontrada")
        
        errors = []
        warnings = []
        
        # Validaciones
        if not account.is_active and account.balance != 0:
            warnings.append("Cuenta inactiva con saldo pendiente")
        
        if account.is_parent_account and account.allows_movements:
            errors.append("Las cuentas padre no deberían permitir movimientos")
        
        if account.is_leaf_account and not account.allows_movements:
            warnings.append("Cuenta hoja que no permite movimientos")
        
        return AccountValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def get_account_stats(self) -> AccountStats:
        """Obtener estadísticas de cuentas"""
        
        total_result = await self.db.execute(select(func.count(Account.id)))
        total_accounts = total_result.scalar() or 0
        
        active_result = await self.db.execute(
            select(func.count(Account.id)).where(Account.is_active == True)
        )
        active_accounts = active_result.scalar() or 0
        
        by_type = {}
        for account_type in AccountType:
            type_result = await self.db.execute(
                select(func.count(Account.id))
                .where(Account.account_type == account_type)
            )
            by_type[account_type.value] = type_result.scalar() or 0
        
        by_category = {}
        for category in AccountCategory:
            cat_result = await self.db.execute(
                select(func.count(Account.id))
                .where(Account.category == category)
            )
            by_category[category.value] = cat_result.scalar() or 0
        
        return AccountStats(
            total_accounts=total_accounts,            active_accounts=active_accounts,
            inactive_accounts=total_accounts - active_accounts,
            by_type=by_type,
            by_category=by_category,
            accounts_with_movements=0,  # TODO: Implementar
            accounts_without_movements=0  # TODO: Implementar
        )

    async def bulk_operation(self, operation: BulkAccountOperation, user_id: uuid.UUID) -> dict:
        """Realizar operaciones masivas en cuentas"""
        
        results = {
            "success": [],
            "errors": [],
            "total_processed": 0
        }
        
        # Si la operación es delete, usar el método mejorado
        if operation.operation == "delete":
            from app.schemas.account import BulkAccountDelete
            
            delete_request = BulkAccountDelete(
                account_ids=operation.account_ids,
                force_delete=False,
                delete_reason=operation.reason
            )
            
            delete_result = await self.bulk_delete_accounts(delete_request, user_id)
            
            return {
                "success": [str(account_id) for account_id in delete_result.successfully_deleted],
                "errors": [
                    f"Cuenta {item['account_id']}: {item['reason']}"
                    for item in delete_result.failed_to_delete
                ],
                "total_processed": delete_result.total_requested,
                "delete_summary": {
                    "success_count": delete_result.success_count,
                    "failure_count": delete_result.failure_count,
                    "success_rate": f"{delete_result.success_rate:.1f}%",
                    "warnings": delete_result.warnings
                }
            }
        
        # Para otras operaciones, usar la lógica existente
        for account_id in operation.account_ids:
            try:
                account = await self.get_account_by_id(account_id)
                if not account:
                    results["errors"].append(f"Cuenta {account_id} no encontrada")
                    continue
                
                if operation.operation == "activate":
                    account.is_active = True
                elif operation.operation == "deactivate":
                    account.is_active = False
                
                results["success"].append(account_id)
                results["total_processed"] += 1
                
            except Exception as e:                
                results["errors"].append(f"Error en cuenta {account_id}: {str(e)}")
        
        if results["success"]:
            await self.db.commit()
        
        return results
    
    async def validate_account_for_deletion(self, account_id: uuid.UUID) -> 'AccountDeleteValidation':
        """Validar si una cuenta puede ser eliminada"""
        from app.schemas.account import AccountDeleteValidation
        
        account = await self.get_account_by_id(account_id)
        if not account:
            return AccountDeleteValidation(
                account_id=account_id,
                can_delete=False,
                blocking_reasons=["Cuenta no encontrada"],
                warnings=[],
                dependencies={}
            )
        
        blocking_reasons = []
        warnings = []
        dependencies = {}
        
        # Verificar que no tenga movimientos
        movements_result = await self.db.execute(
            select(func.count(JournalEntryLine.id))
            .where(JournalEntryLine.account_id == account_id)
        )
        movements_count = movements_result.scalar() or 0
        
        if movements_count > 0:
            blocking_reasons.append(f"La cuenta tiene {movements_count} movimientos contables")
            dependencies["movements_count"] = movements_count
        
        # Verificar que no tenga cuentas hijas
        children_result = await self.db.execute(
            select(func.count(Account.id))
            .where(Account.parent_id == account_id)
        )
        children_count = children_result.scalar() or 0
        
        if children_count > 0:
            blocking_reasons.append(f"La cuenta tiene {children_count} cuentas hijas")
            dependencies["children_count"] = children_count
        
        # Verificar si es una cuenta de sistema (códigos básicos)
        system_codes = ["1", "2", "3", "4", "5", "6"]
        if account.code in system_codes:
            blocking_reasons.append("No se puede eliminar una cuenta de sistema")
        
        # Advertencias
        if account.balance != 0:
            warnings.append(f"La cuenta tiene un saldo pendiente de {account.balance}")
            dependencies["balance"] = str(account.balance)
        
        if not account.is_active:
            warnings.append("La cuenta ya está inactiva")
        
        can_delete = len(blocking_reasons) == 0
        
        return AccountDeleteValidation(
            account_id=account_id,
            can_delete=can_delete,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            dependencies=dependencies
        )
    
    async def bulk_delete_accounts(self, delete_request: 'BulkAccountDelete', user_id: uuid.UUID) -> 'BulkAccountDeleteResult':
        """Borrar múltiples cuentas con validaciones exhaustivas"""
        from app.schemas.account import BulkAccountDeleteResult
        
        result = BulkAccountDeleteResult(
            total_requested=len(delete_request.account_ids),
            successfully_deleted=[],
            failed_to_delete=[],
            validation_errors=[],
            warnings=[]
        )
        
        # Validar primero todas las cuentas
        validations = {}
        for account_id in delete_request.account_ids:
            validation = await self.validate_account_for_deletion(account_id)
            validations[account_id] = validation
            
            if not validation.can_delete and not delete_request.force_delete:
                result.failed_to_delete.append({
                    "account_id": str(account_id),
                    "reason": "; ".join(validation.blocking_reasons),
                    "details": validation.dependencies
                })
            elif validation.warnings:
                result.warnings.extend([
                    f"Cuenta {account_id}: {warning}" for warning in validation.warnings
                ])
        
        # Si force_delete es False y hay errores, no proceder
        if not delete_request.force_delete and result.failed_to_delete:
            result.validation_errors.append({
                "error": "Hay cuentas que no pueden eliminarse. Use force_delete=true para forzar la eliminación de las que sí pueden eliminarse."
            })
            return result
        
        # Proceder con la eliminación
        accounts_to_delete = []
        for account_id in delete_request.account_ids:
            validation = validations[account_id]
            
            if validation.can_delete or (delete_request.force_delete and not any("no encontrada" in reason for reason in validation.blocking_reasons)):
                if validation.can_delete:
                    accounts_to_delete.append(account_id)
                elif delete_request.force_delete:
                    # Con force_delete, solo eliminar si no tiene movimientos ni hijos
                    has_critical_blocks = any(
                        "movimientos" in reason or "hijas" in reason or "sistema" in reason 
                        for reason in validation.blocking_reasons
                    )
                    if not has_critical_blocks:
                        accounts_to_delete.append(account_id)
                    else:
                        result.failed_to_delete.append({
                            "account_id": str(account_id),
                            "reason": "No se puede forzar la eliminación: " + "; ".join(validation.blocking_reasons),
                            "details": validation.dependencies
                        })
        
        # Eliminar las cuentas validadas
        for account_id in accounts_to_delete:
            try:
                success = await self.delete_account(account_id)
                if success:
                    result.successfully_deleted.append(account_id)
                else:
                    result.failed_to_delete.append({
                        "account_id": str(account_id),
                        "reason": "Error desconocido durante la eliminación",
                        "details": {}
                    })
            except Exception as e:
                result.failed_to_delete.append({
                    "account_id": str(account_id),
                    "reason": str(e),
                    "details": {}
                })
        
        # Añadir información sobre la razón de eliminación si se proporcionó
        if delete_request.delete_reason and result.successfully_deleted:
            result.warnings.append(f"Razón de eliminación: {delete_request.delete_reason}")
        
        return result
    
    async def get_accounts_by_type(self, account_type: AccountType, active_only: bool = True) -> AccountsByType:
        """Obtener cuentas por tipo"""
        
        accounts = await self.get_accounts(account_type=account_type, is_active=active_only)
        
        return AccountsByType(
            account_type=account_type,
            accounts=[                AccountSummary(
                    id=acc.id,
                    code=acc.code,
                    name=acc.name,
                    account_type=acc.account_type,
                    balance=acc.balance,
                    is_active=acc.is_active,
                    allows_movements=acc.allows_movements
                ) for acc in accounts
            ],
            total_balance=sum((acc.balance for acc in accounts), Decimal('0'))
        )

    async def import_accounts_from_csv(self, file_content: str, user_id: uuid.UUID) -> dict:
        """Importar cuentas desde CSV"""
        # Implementación básica - en producción sería más robusta
        return {            "imported": 0,
            "errors": [],
            "message": "Funcionalidad de importación pendiente de implementación completa"
        }
    
    async def export_accounts_to_csv(self, account_type: Optional[AccountType] = None, active_only: bool = True) -> str:
        """Exportar cuentas a CSV"""
        # Implementación básica - en producción retornaría CSV real
        return "CSV export functionality pending"
    
    async def get_account_tree_fixed(
        self, 
        account_type: Optional[AccountType] = None, 
        active_only: bool = True
    ) -> List[AccountTree]:
        """Obtener estructura jerárquica de cuentas - versión corregida para evitar MissingGreenlet"""
        
        # Obtener todas las cuentas de una vez para evitar lazy loading
        query = select(Account)
        
        if account_type:
            query = query.where(Account.account_type == account_type)
        
        if active_only:
            query = query.where(Account.is_active == True)
        
        query = query.order_by(Account.code)
        
        result = await self.db.execute(query)
        all_accounts = list(result.scalars().all())
        
        # Crear un diccionario para acceso rápido por ID
        accounts_dict = {account.id: account for account in all_accounts}
        
        # Construir la estructura de hijos para cada cuenta
        children_dict = {}
        for account in all_accounts:
            children_dict[account.id] = []
        
        for account in all_accounts:
            if account.parent_id and account.parent_id in children_dict:
                children_dict[account.parent_id].append(account)
        
        def build_tree(account: Account) -> AccountTree:
            # Obtener hijos desde nuestro diccionario en lugar de la relación lazy
            children_accounts = sorted(children_dict.get(account.id, []), key=lambda x: x.code)
            children = []
            
            for child in children_accounts:
                if not active_only or child.is_active:
                    children.append(build_tree(child))
            
            return AccountTree(
                id=account.id,
                code=account.code,
                name=account.name,
                account_type=account.account_type,
                level=account.level,
                balance=account.balance,
                is_active=account.is_active,
                allows_movements=account.allows_movements,
                children=children
            )
        
        # Solo procesar cuentas raíz (sin parent_id)
        root_accounts = [account for account in all_accounts if account.parent_id is None]
        return [build_tree(account) for account in sorted(root_accounts, key=lambda x: x.code)]
