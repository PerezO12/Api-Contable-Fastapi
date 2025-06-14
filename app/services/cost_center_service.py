"""
Cost Center Service for cost accounting operations.
Handles CRUD operations, hierarchical structure validation and reporting.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from math import ceil

from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.cost_center import CostCenter
from app.models.journal_entry import JournalEntryLine, JournalEntry
from app.models.account import Account
from app.schemas.cost_center import (
    CostCenterCreate, CostCenterUpdate, CostCenterSummary, CostCenterList,
    CostCenterFilter, CostCenterReport, CostCenterMovement, CostCenterValidation,
    BulkCostCenterOperation, CostCenterStats, CostCenterImport, CostCenterRead,
    BulkCostCenterDelete, BulkCostCenterDeleteResult, CostCenterDeleteValidation,
    CostCenterImportResult, CostCenterTree
)
from app.utils.exceptions import (
    ValidationError, NotFoundError, ConflictError, BusinessLogicError
)


class CostCenterService:
    """Servicio para operaciones de centros de costo"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_cost_center(self, cost_center_data: CostCenterCreate) -> CostCenter:
        """Crear un nuevo centro de costo"""
        
        # Validar que no exista un centro de costo con el mismo código
        existing_result = await self.db.execute(
            select(CostCenter).where(CostCenter.code == cost_center_data.code)
        )
        existing_cost_center = existing_result.scalar_one_or_none()
        
        if existing_cost_center:
            raise ConflictError(f"Ya existe un centro de costo con el código {cost_center_data.code}")
        
        # Validar centro de costo padre si se especifica
        parent_cost_center = None
        if cost_center_data.parent_id:
            parent_result = await self.db.execute(
                select(CostCenter).where(CostCenter.id == cost_center_data.parent_id)
            )
            parent_cost_center = parent_result.scalar_one_or_none()
            
            if not parent_cost_center:
                raise ValidationError("El centro de costo padre especificado no existe")
            
            if not parent_cost_center.is_active:
                raise ValidationError("El centro de costo padre debe estar activo")
          # Crear el centro de costo
        cost_center = CostCenter(**cost_center_data.model_dump())
        
        # Validar el modelo
        validation_errors = cost_center.validate_cost_center()
        if validation_errors:
            raise ValidationError(f"Errores de validación: {'; '.join(validation_errors)}")
        
        self.db.add(cost_center)
        await self.db.commit()
        await self.db.refresh(cost_center)
        
        # Calcular propiedades dinámicas sin activar lazy loading
        await self._calculate_cost_center_properties_safe(cost_center)
        
        return cost_center

    async def get_cost_center_by_id(self, cost_center_id: uuid.UUID) -> Optional[CostCenter]:
        """Obtener centro de costo por ID"""
        result = await self.db.execute(
            select(CostCenter)
            .options(
                selectinload(CostCenter.parent),
                selectinload(CostCenter.children)
            )
            .where(CostCenter.id == cost_center_id)        )
        cost_center = result.scalar_one_or_none()
        
        if cost_center:
            # Calcular propiedades dinámicas de forma segura para el objeto principal
            await self._calculate_cost_center_properties_safe(cost_center)
            
            # Si tiene padre, también calcular sus propiedades
            if cost_center.parent:
                await self._calculate_cost_center_properties_safe(cost_center.parent)
            
            # Calcular propiedades para los hijos también
            for child in cost_center.children:
                await self._calculate_cost_center_properties_safe(child)
        
        return cost_center

    async def get_cost_center_by_code(self, code: str) -> Optional[CostCenter]:
        """Obtener centro de costo por código"""
        result = await self.db.execute(
            select(CostCenter)
            .options(
                selectinload(CostCenter.parent),
                selectinload(CostCenter.children)
            )
            .where(CostCenter.code == code)
        )
        cost_center = result.scalar_one_or_none()
        
        if cost_center:
            # Calcular propiedades dinámicas de forma segura para el objeto principal
            await self._calculate_cost_center_properties_safe(cost_center)
            
            # Si tiene padre, también calcular sus propiedades
            if cost_center.parent:
                await self._calculate_cost_center_properties_safe(cost_center.parent)
            
            # Calcular propiedades para los hijos también
            for child in cost_center.children:
                await self._calculate_cost_center_properties_safe(child)
        
        return cost_center

    async def update_cost_center(
        self, 
        cost_center_id: uuid.UUID, 
        cost_center_data: CostCenterUpdate
    ) -> CostCenter:
        """Actualizar centro de costo"""
        
        cost_center = await self.get_cost_center_by_id(cost_center_id)
        if not cost_center:
            raise NotFoundError("Centro de costo no encontrado")
        
        # Validar centro de costo padre si se especifica
        if cost_center_data.parent_id is not None:
            if cost_center_data.parent_id == cost_center_id:
                raise ValidationError("Un centro de costo no puede ser su propio padre")
            
            if cost_center_data.parent_id:
                parent_result = await self.db.execute(
                    select(CostCenter).where(CostCenter.id == cost_center_data.parent_id)
                )
                parent_cost_center = parent_result.scalar_one_or_none()
                
                if not parent_cost_center:
                    raise ValidationError("El centro de costo padre especificado no existe")
                
                # Verificar que no se cree un ciclo
                if await self._would_create_cycle(cost_center_id, cost_center_data.parent_id):
                    raise ValidationError("La asignación crearía una referencia circular")
        
        # Actualizar campos
        for field, value in cost_center_data.model_dump(exclude_unset=True).items():
            setattr(cost_center, field, value)
        
        # Validar el modelo actualizado
        validation_errors = cost_center.validate_cost_center()
        if validation_errors:
            raise ValidationError(f"Errores de validación: {'; '.join(validation_errors)}")
        
        await self.db.commit()
        await self.db.refresh(cost_center)
        
        return cost_center

    async def delete_cost_center(self, cost_center_id: uuid.UUID) -> bool:
        """Eliminar centro de costo"""
        
        cost_center = await self.get_cost_center_by_id(cost_center_id)
        if not cost_center:
            raise NotFoundError("Centro de costo no encontrado")
        
        # Verificar que no tenga hijos activos
        if cost_center.children:
            active_children = [child for child in cost_center.children if child.is_active]
            if active_children:
                raise BusinessLogicError(
                    "No se puede eliminar un centro de costo que tiene centros hijo activos"
                )
          # Verificar que no tenga movimientos asociados
        movements_result = await self.db.execute(
            select(func.count(JournalEntryLine.id))
            .where(JournalEntryLine.cost_center_id == cost_center_id)
        )
        movements_count = movements_result.scalar() or 0
        
        if movements_count > 0:
            raise BusinessLogicError(
                f"No se puede eliminar el centro de costo porque tiene {movements_count} movimientos asociados"
            )
        
        await self.db.delete(cost_center)
        await self.db.commit()
        
        return True

    async def get_cost_centers_list(
        self, 
        filter_params: CostCenterFilter,
        skip: int = 0,
        limit: int = 100
    ) -> CostCenterList:
        """Obtener lista paginada de centros de costo"""
        
        # Construir query base con eager loading de las relaciones necesarias
        query = select(CostCenter).options(
            selectinload(CostCenter.parent),
            selectinload(CostCenter.children)
        )
          # Aplicar filtros
        conditions = []
        
        if filter_params.search:
            search_term = f"%{filter_params.search}%"
            conditions.append(
                or_(
                    CostCenter.code.ilike(search_term),
                    CostCenter.name.ilike(search_term),
                    CostCenter.description.ilike(search_term)
                )
            )
        
        if filter_params.is_active is not None:
            conditions.append(CostCenter.is_active == filter_params.is_active)
        
        if filter_params.parent_id is not None:
            conditions.append(CostCenter.parent_id == filter_params.parent_id)
        
        if filter_params.allows_direct_assignment is not None:
            conditions.append(
                CostCenter.allows_direct_assignment == filter_params.allows_direct_assignment
            )
        
        # Filtros de jerarquía
        if filter_params.level is not None:
            # Para filtrar por nivel, necesitamos usar subconsultas o calcular el nivel
            # Por simplicidad, filtraremos los resultados después de la consulta
            pass  # Se manejará en el post-procesamiento
        
        if filter_params.has_children is not None:
            if filter_params.has_children:
                # Centros de costo que tienen hijos
                subquery = select(CostCenter.parent_id).where(CostCenter.parent_id.is_not(None)).distinct()
                conditions.append(CostCenter.id.in_(subquery))
            else:
                # Centros de costo que NO tienen hijos
                subquery = select(CostCenter.parent_id).where(CostCenter.parent_id.is_not(None)).distinct()
                conditions.append(~CostCenter.id.in_(subquery))
        
        if filter_params.is_leaf is not None:
            if filter_params.is_leaf:
                # Nodos hoja (sin hijos)
                subquery = select(CostCenter.parent_id).where(CostCenter.parent_id.is_not(None)).distinct()
                conditions.append(~CostCenter.id.in_(subquery))
            else:
                # Nodos que NO son hoja (tienen hijos)
                subquery = select(CostCenter.parent_id).where(CostCenter.parent_id.is_not(None)).distinct()
                conditions.append(CostCenter.id.in_(subquery))
        
        if filter_params.is_root is not None:
            if filter_params.is_root:
                # Nodos raíz (sin padre)
                conditions.append(CostCenter.parent_id.is_(None))
            else:
                # Nodos que NO son raíz (tienen padre)
                conditions.append(CostCenter.parent_id.is_not(None))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Contar total
        count_query = select(func.count(CostCenter.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
          # Aplicar paginación y ordenamiento
        query = query.order_by(CostCenter.code).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        cost_centers = result.scalars().all()
        
        # Aplicar filtros post-procesamiento (como level)
        if filter_params.level is not None:
            # Calcular propiedades dinámicas para todos los centros de costo
            for cc in cost_centers:
                await self._calculate_cost_center_properties_safe(cc)
            # Filtrar por nivel
            cost_centers = [cc for cc in cost_centers if cc.level == filter_params.level]
        else:
            # Calcular propiedades dinámicas solo si no se filtró por nivel
            for cc in cost_centers:
                await self._calculate_cost_center_properties_safe(cc)
          # Convertir a summaries
        cost_center_summaries = []
        for cc in cost_centers:
            summary = CostCenterSummary(
                id=cc.id,
                code=cc.code,
                name=cc.name,
                is_active=cc.is_active,
                level=cc.level,
                parent_name=cc.parent.name if cc.parent else None,
                children_count=len(cc.children),
                created_at=cc.created_at
            )
            cost_center_summaries.append(summary)
        
        # Calcular paginación
        pages = ceil(total / limit) if limit > 0 else 1
        page = (skip // limit) + 1 if limit > 0 else 1
        
        return CostCenterList(
            cost_centers=cost_center_summaries,
            total=total,
            page=page,
            size=len(cost_center_summaries),
            pages=pages
        )

    async def get_cost_center_hierarchy(self, parent_id: Optional[uuid.UUID] = None) -> List[CostCenter]:
        """Obtener jerarquía de centros de costo"""
        
        query = select(CostCenter).options(
            selectinload(CostCenter.children),
            selectinload(CostCenter.parent)
        ).where(CostCenter.parent_id == parent_id)
        
        if parent_id is None:
            query = query.where(CostCenter.parent_id.is_(None))
        
        query = query.order_by(CostCenter.code)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_cost_center_movements(
        self, 
        cost_center_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CostCenterMovement]:
        """Obtener movimientos de un centro de costo"""
        
        query = (
            select(
                JournalEntryLine.journal_entry_id,
                JournalEntry.number,
                JournalEntry.entry_date,
                Account.code,
                Account.name,
                JournalEntryLine.description,
                JournalEntryLine.debit_amount,
                JournalEntryLine.credit_amount,
                JournalEntryLine.reference
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(Account, JournalEntryLine.account_id == Account.id)
            .where(JournalEntryLine.cost_center_id == cost_center_id)
            .order_by(desc(JournalEntry.entry_date), JournalEntry.number)
        )
        
        # Aplicar filtros de fecha
        if start_date:
            query = query.where(JournalEntry.entry_date >= start_date)
        if end_date:
            query = query.where(JournalEntry.entry_date <= end_date)
        
        result = await self.db.execute(query)
        movements = []
        
        for row in result:
            movement = CostCenterMovement(
                journal_entry_id=row.journal_entry_id,
                journal_entry_number=row.number,
                entry_date=row.entry_date,
                account_code=row.code,
                account_name=row.name,
                description=row.description,
                debit_amount=row.debit_amount,
                credit_amount=row.credit_amount,
                reference=row.reference
            )
            movements.append(movement)
        
        return movements

    async def get_cost_center_report(
        self, 
        cost_center_id: uuid.UUID,
        start_date: date,
        end_date: date
    ) -> CostCenterReport:
        """Generar reporte de centro de costo"""
        
        cost_center = await self.get_cost_center_by_id(cost_center_id)
        if not cost_center:
            raise NotFoundError("Centro de costo no encontrado")
        
        movements = await self.get_cost_center_movements(
            cost_center_id, start_date, end_date
        )
          # Calcular totales
        total_debits = Decimal(str(sum(m.debit_amount for m in movements))) if movements else Decimal('0')
        total_credits = Decimal(str(sum(m.credit_amount for m in movements))) if movements else Decimal('0')
        net_amount = Decimal(str(total_debits - total_credits))
        
        return CostCenterReport(
            cost_center=CostCenterRead.model_validate(cost_center),
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            movements=movements,
            total_debits=total_debits,
            total_credits=total_credits,
            net_amount=net_amount,
            movement_count=len(movements)
        )

    async def validate_cost_center(self, cost_center_id: uuid.UUID) -> CostCenterValidation:
        """Validar un centro de costo"""
        
        cost_center = await self.get_cost_center_by_id(cost_center_id)
        if not cost_center:
            return CostCenterValidation(
                is_valid=False,
                errors=["Centro de costo no encontrado"],
                warnings=[],
                hierarchy_valid=False,
                code_unique=False
            )
        
        errors = cost_center.validate_cost_center()
        warnings = []
        
        # Validar unicidad del código
        code_query = select(func.count(CostCenter.id)).where(
            and_(
                CostCenter.code == cost_center.code,
                CostCenter.id != cost_center_id
            )
        )
        code_result = await self.db.execute(code_query)
        code_unique = (code_result.scalar() or 0) == 0
        
        if not code_unique:
            errors.append("El código del centro de costo ya existe")
        
        # Validar jerarquía
        hierarchy_valid = True
        if cost_center.parent_id:
            if await self._would_create_cycle(cost_center_id, cost_center.parent_id):
                hierarchy_valid = False
                errors.append("La jerarquía contiene referencias circulares")
        
        # Warnings
        if not cost_center.allows_direct_assignment and cost_center.is_leaf:
            warnings.append("Centro de costo hoja que no permite asignación directa")
        
        return CostCenterValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            hierarchy_valid=hierarchy_valid,
            code_unique=code_unique
        )

    async def get_cost_center_stats(self) -> CostCenterStats:
        """Obtener estadísticas de centros de costo"""
        
        # Contar totales
        total_query = select(func.count(CostCenter.id))
        total_result = await self.db.execute(total_query)
        total_cost_centers = total_result.scalar() or 0
        
        # Contar activos
        active_query = select(func.count(CostCenter.id)).where(CostCenter.is_active == True)
        active_result = await self.db.execute(active_query)
        active_cost_centers = active_result.scalar() or 0
        
        # Contar raíz (sin padre)
        root_query = select(func.count(CostCenter.id)).where(CostCenter.parent_id.is_(None))
        root_result = await self.db.execute(root_query)
        root_cost_centers = root_result.scalar() or 0
        
        # Contar hojas (sin hijos)
        leaf_query = select(func.count(CostCenter.id)).where(
            ~CostCenter.id.in_(
                select(CostCenter.parent_id).where(CostCenter.parent_id.is_not(None))
            )
        )
        leaf_result = await self.db.execute(leaf_query)
        leaf_cost_centers = leaf_result.scalar() or 0
        
        # Nivel máximo de jerarquía
        max_level = 0
        all_cost_centers = await self.db.execute(
            select(CostCenter).options(selectinload(CostCenter.parent))
        )
        for cc in all_cost_centers.scalars():
            max_level = max(max_level, cc.level)
        
        # Centros con movimientos
        movements_query = select(func.count(func.distinct(JournalEntryLine.cost_center_id))).where(
            JournalEntryLine.cost_center_id.is_not(None)
        )
        movements_result = await self.db.execute(movements_query)
        cost_centers_with_movements = movements_result.scalar() or 0
        
        return CostCenterStats(
            total_cost_centers=total_cost_centers,
            active_cost_centers=active_cost_centers,
            inactive_cost_centers=total_cost_centers - active_cost_centers,
            root_cost_centers=root_cost_centers,
            leaf_cost_centers=leaf_cost_centers,
            max_hierarchy_level=max_level,
            cost_centers_with_movements=cost_centers_with_movements
        )

    async def bulk_operation(self, operation_data: BulkCostCenterOperation) -> Dict[str, Any]:
        """Operación masiva en centros de costo"""
        
        results = {
            "success": [],
            "errors": [],
            "total_processed": len(operation_data.cost_center_ids)
        }
        
        for cost_center_id in operation_data.cost_center_ids:
            try:
                cost_center = await self.get_cost_center_by_id(cost_center_id)
                if not cost_center:
                    results["errors"].append({
                        "id": str(cost_center_id),
                        "error": "Centro de costo no encontrado"
                    })
                    continue
                
                if operation_data.operation == "activate":
                    cost_center.is_active = True
                elif operation_data.operation == "deactivate":
                    cost_center.is_active = False
                elif operation_data.operation == "delete":
                    await self.delete_cost_center(cost_center_id)
                    results["success"].append(str(cost_center_id))
                    continue
                
                await self.db.commit()
                results["success"].append(str(cost_center_id))
                
            except Exception as e:
                results["errors"].append({
                    "id": str(cost_center_id),
                    "error": str(e)
                })
        
        return results

    async def _would_create_cycle(self, cost_center_id: uuid.UUID, parent_id: uuid.UUID) -> bool:
        """Verificar si asignar un padre crearía un ciclo"""
        
        current_id = parent_id
        visited = set()
        
        while current_id and current_id not in visited:
            if current_id == cost_center_id:
                return True
            
            visited.add(current_id)
            
            # Obtener el padre del padre
            result = await self.db.execute(
                select(CostCenter.parent_id).where(CostCenter.id == current_id)
            )
            current_id = result.scalar()
        return False

    async def _calculate_cost_center_properties_safe(self, cost_center: CostCenter) -> None:
        """Calcular propiedades dinámicas del centro de costo de forma segura"""
        # Calcular full_code
        if cost_center.parent_id:
            parent_result = await self.db.execute(
                select(CostCenter).where(CostCenter.id == cost_center.parent_id)
            )
            parent = parent_result.scalar_one_or_none()
            if parent:
                # Recursivamente obtener el código completo del padre
                parent_full_code = await self._get_parent_full_code(parent)
                cost_center.full_code = f"{parent_full_code}.{cost_center.code}"
            else:
                cost_center.full_code = cost_center.code
        else:
            cost_center.full_code = cost_center.code
        
        # Calcular level
        cost_center.level = await self._calculate_level(cost_center)
        
        # Calcular is_leaf (contar hijos directamente en la BD)
        children_count_result = await self.db.execute(
            select(func.count(CostCenter.id))
            .where(CostCenter.parent_id == cost_center.id)
        )
        children_count = children_count_result.scalar() or 0
        cost_center.is_leaf = children_count == 0
    
    async def _get_parent_full_code(self, cost_center: CostCenter) -> str:
        """Obtener el código completo de un centro de costo recursivamente"""
        if cost_center.parent_id:
            parent_result = await self.db.execute(
                select(CostCenter).where(CostCenter.id == cost_center.parent_id)
            )
            parent = parent_result.scalar_one_or_none()
            if parent:
                parent_full_code = await self._get_parent_full_code(parent)
                return f"{parent_full_code}.{cost_center.code}"
        return cost_center.code
    
    async def _calculate_level(self, cost_center: CostCenter) -> int:
        """Calcular el nivel de jerarquía de un centro de costo"""
        level = 0
        current_parent_id = cost_center.parent_id
        
        while current_parent_id:
            level += 1
            parent_result = await self.db.execute(
                select(CostCenter.parent_id).where(CostCenter.id == current_parent_id)
            )
            current_parent_id = parent_result.scalar_one_or_none()
        
        return level

    async def bulk_delete_cost_centers(self, delete_request: 'BulkCostCenterDelete', user_id: uuid.UUID) -> 'BulkCostCenterDeleteResult':
        """Borrar múltiples centros de costo con validaciones exhaustivas"""
        from app.schemas.cost_center import BulkCostCenterDeleteResult
        
        result = BulkCostCenterDeleteResult(
            total_requested=len(delete_request.cost_center_ids),
            successfully_deleted=[],
            failed_to_delete=[],
            validation_errors=[],
            warnings=[]
        )
        
        # Validar primero todos los centros de costo
        validations = {}
        for cost_center_id in delete_request.cost_center_ids:
            validation = await self.validate_cost_center_for_deletion(cost_center_id)
            validations[cost_center_id] = validation
            
            if not validation.can_delete and not delete_request.force_delete:
                result.failed_to_delete.append({
                    "cost_center_id": str(cost_center_id),
                    "reason": "; ".join(validation.blocking_reasons),
                    "details": validation.dependencies
                })
            elif validation.warnings:
                result.warnings.extend([
                    f"Centro de costo {cost_center_id}: {warning}" for warning in validation.warnings
                ])
        
        # Si force_delete es False y hay errores, no proceder
        if not delete_request.force_delete and result.failed_to_delete:
            result.validation_errors.append({
                "error": "Hay centros de costo que no pueden eliminarse. Use force_delete=true para forzar la eliminación de los que sí pueden eliminarse."
            })
            return result
        
        # Proceder con la eliminación
        cost_centers_to_delete = []
        for cost_center_id in delete_request.cost_center_ids:
            validation = validations[cost_center_id]
            
            if validation.can_delete or (delete_request.force_delete and not any("no encontrado" in reason for reason in validation.blocking_reasons)):
                if validation.can_delete:
                    cost_centers_to_delete.append(cost_center_id)
                elif delete_request.force_delete:
                    # Con force_delete, solo eliminar si no tiene movimientos ni hijos
                    has_critical_blocks = any(
                        "movimientos" in reason or "hijos" in reason 
                        for reason in validation.blocking_reasons
                    )
                    if not has_critical_blocks:
                        cost_centers_to_delete.append(cost_center_id)
                    else:
                        result.failed_to_delete.append({
                            "cost_center_id": str(cost_center_id),
                            "reason": f"Eliminación forzada bloqueada: {'; '.join(validation.blocking_reasons)}",
                            "force_delete_blocked": True
                        })
        
        # Eliminar los centros de costo validados
        for cost_center_id in cost_centers_to_delete:
            try:
                # Obtener el centro de costo
                cost_center_result = await self.db.execute(
                    select(CostCenter).where(CostCenter.id == cost_center_id)
                )
                cost_center = cost_center_result.scalar_one_or_none()
                
                if cost_center:
                    await self.db.delete(cost_center)
                    result.successfully_deleted.append(cost_center_id)
                else:
                    result.failed_to_delete.append({
                        "cost_center_id": str(cost_center_id),
                        "reason": "Centro de costo no encontrado al momento de eliminar"
                    })
            except Exception as e:
                result.failed_to_delete.append({
                    "cost_center_id": str(cost_center_id),
                    "reason": f"Error durante eliminación: {str(e)}"
                })
        
        if result.successfully_deleted:
            await self.db.commit()
            result.warnings.append(f"Se eliminaron {len(result.successfully_deleted)} centros de costo exitosamente")
        
        return result
    
    async def validate_cost_center_for_deletion(self, cost_center_id: uuid.UUID) -> 'CostCenterDeleteValidation':
        """Validar si un centro de costo puede ser eliminado"""
        from app.schemas.cost_center import CostCenterDeleteValidation
        
        validation = CostCenterDeleteValidation(
            cost_center_id=cost_center_id,
            can_delete=True,
            blocking_reasons=[],
            warnings=[],
            dependencies={}
        )
        
        # Verificar que el centro de costo exista
        cost_center_result = await self.db.execute(
            select(CostCenter).where(CostCenter.id == cost_center_id)
        )
        cost_center = cost_center_result.scalar_one_or_none()
        
        if not cost_center:
            validation.can_delete = False
            validation.blocking_reasons.append("Centro de costo no encontrado")
            return validation
        
        # Verificar si tiene centros de costo hijos
        children_result = await self.db.execute(
            select(func.count(CostCenter.id))
            .where(CostCenter.parent_id == cost_center_id)
        )
        children_count = children_result.scalar() or 0
        
        if children_count > 0:
            validation.can_delete = False
            validation.blocking_reasons.append(f"Tiene {children_count} centros de costo hijos")
            validation.dependencies["children_count"] = children_count
        
        # Verificar si tiene movimientos contables (asientos)
        movements_result = await self.db.execute(
            select(func.count(JournalEntryLine.id))
            .where(JournalEntryLine.cost_center_id == cost_center_id)
        )
        movements_count = movements_result.scalar() or 0
        
        if movements_count > 0:
            validation.can_delete = False
            validation.blocking_reasons.append(f"Tiene {movements_count} movimientos contables asociados")
            validation.dependencies["movements_count"] = movements_count
        
        # Agregar información adicional como advertencias
        if cost_center.is_active:
            validation.warnings.append("El centro de costo está activo")
        
        if cost_center.allows_direct_assignment:
            validation.warnings.append("El centro de costo permite asignación directa")
        
        return validation
    
    async def import_cost_centers_from_csv(self, file_content: str, user_id: uuid.UUID) -> 'CostCenterImportResult':
        """Importar centros de costo desde CSV"""
        from app.schemas.cost_center import CostCenterImportResult
        import csv
        import io
        
        result = CostCenterImportResult(
            total_rows=0,
            successfully_imported=0,
            updated_existing=0,
            failed_imports=[],
            validation_errors=[],
            warnings=[],
            created_cost_centers=[]
        )
        
        try:
            # Procesar el contenido CSV
            csv_reader = csv.DictReader(io.StringIO(file_content))
            rows = list(csv_reader)
            result.total_rows = len(rows)
              # Validar headers requeridos
            required_headers = ['code', 'name']
            fieldnames = csv_reader.fieldnames or []
            missing_headers = [h for h in required_headers if h not in fieldnames]
            
            if missing_headers:
                result.validation_errors.append({
                    "error": f"Faltan columnas requeridas: {', '.join(missing_headers)}"
                })
                return result
            
            # Procesar cada fila
            for row_num, row in enumerate(rows, start=2):  # +2 porque la primera es header
                try:
                    # Limpiar y validar datos
                    code = row.get('code', '').strip().upper()
                    name = row.get('name', '').strip()
                    
                    if not code or not name:
                        result.failed_imports.append({
                            "row": row_num,
                            "error": "Código y nombre son requeridos",
                            "data": row
                        })
                        continue
                    
                    # Verificar si ya existe
                    existing_result = await self.db.execute(
                        select(CostCenter).where(CostCenter.code == code)
                    )
                    existing_cost_center = existing_result.scalar_one_or_none()
                    
                    # Preparar datos para crear/actualizar
                    cost_center_data = {
                        'code': code,
                        'name': name,
                        'description': row.get('description', '').strip() or None,
                        'is_active': row.get('is_active', 'true').lower() in ['true', '1', 'yes', 'sí'],
                        'allows_direct_assignment': row.get('allows_direct_assignment', 'true').lower() in ['true', '1', 'yes', 'sí'],
                        'manager_name': row.get('manager_name', '').strip() or None,
                        'budget_code': row.get('budget_code', '').strip() or None,
                        'notes': row.get('notes', '').strip() or None
                    }
                    
                    # Manejar parent_id si existe parent_code
                    parent_code = row.get('parent_code', '').strip()
                    if parent_code:
                        parent_result = await self.db.execute(
                            select(CostCenter.id).where(CostCenter.code == parent_code)
                        )
                        parent_id = parent_result.scalar_one_or_none()
                        if parent_id:
                            cost_center_data['parent_id'] = parent_id
                        else:
                            result.warnings.append(f"Fila {row_num}: Centro de costo padre '{parent_code}' no encontrado, se creará sin padre")
                    
                    if existing_cost_center:
                        # Actualizar existente
                        for key, value in cost_center_data.items():
                            if key != 'code':  # No actualizar el código
                                setattr(existing_cost_center, key, value)
                        
                        existing_cost_center.updated_at = datetime.utcnow()
                        await self._calculate_cost_center_properties_safe(existing_cost_center)
                        result.updated_existing += 1
                        
                    else:
                        # Crear nuevo
                        cost_center_data['id'] = uuid.uuid4()
                        cost_center_data['created_at'] = datetime.utcnow()
                        cost_center_data['updated_at'] = datetime.utcnow()
                        
                        new_cost_center = CostCenter(**cost_center_data)
                        await self._calculate_cost_center_properties_safe(new_cost_center)
                        
                        self.db.add(new_cost_center)
                        result.successfully_imported += 1
                        result.created_cost_centers.append(new_cost_center.id)
                
                except Exception as e:
                    result.failed_imports.append({
                        "row": row_num,
                        "error": str(e),
                        "data": row
                    })
            
            # Confirmar cambios si hay éxitos
            if result.successfully_imported > 0 or result.updated_existing > 0:
                await self.db.commit()
                result.warnings.append(f"Importación completada: {result.successfully_imported} creados, {result.updated_existing} actualizados")
            
        except Exception as e:
            result.validation_errors.append({
                "error": f"Error general de importación: {str(e)}"
            })
        
        return result
    
    async def export_cost_centers_to_csv(self, is_active: Optional[bool] = None, parent_id: Optional[uuid.UUID] = None) -> str:
        """Exportar centros de costo a CSV"""
        import csv
        import io
          # Construir consulta con eager loading para evitar lazy loading
        query = select(CostCenter).options(
            selectinload(CostCenter.parent),
            selectinload(CostCenter.children)
        )
        
        if is_active is not None:
            query = query.where(CostCenter.is_active == is_active)
        
        if parent_id is not None:
            query = query.where(CostCenter.parent_id == parent_id)
        
        query = query.order_by(CostCenter.code)
        
        result = await self.db.execute(query)
        cost_centers = list(result.scalars().all())
        
        # Calcular propiedades dinámicas para todos los centros de costo
        for cc in cost_centers:
            await self._calculate_cost_center_properties_safe(cc)
        
        # Crear CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            'code', 'name', 'description', 'parent_code', 'is_active',
            'allows_direct_assignment', 'manager_name', 'budget_code', 'notes',
            'full_code', 'level', 'is_leaf', 'created_at', 'updated_at'
        ]
        writer.writerow(headers)
        
        # Datos
        for cc in cost_centers:
            parent_code = cc.parent.code if cc.parent else ''
            
            row = [
                cc.code,
                cc.name,
                cc.description or '',
                parent_code,
                cc.is_active,
                cc.allows_direct_assignment,
                cc.manager_name or '',
                cc.budget_code or '',
                cc.notes or '',
                cc.full_code or '',
                cc.level or 0,
                cc.is_leaf,                
                cc.created_at.isoformat() if cc.created_at else '',
                cc.updated_at.isoformat() if cc.updated_at else ''
            ]
            writer.writerow(row)
        
        return output.getvalue()

    async def get_cost_center_tree(self, active_only: bool = True) -> List[CostCenterTree]:
        """Obtener estructura jerárquica de centros de costo como árbol"""
        
        # Obtener todos los centros de costo de una vez para evitar lazy loading
        query = select(CostCenter)
        
        if active_only:
            query = query.where(CostCenter.is_active == True)
        
        query = query.order_by(CostCenter.code)
        
        result = await self.db.execute(query)
        all_cost_centers = list(result.scalars().all())
        
        # Calcular propiedades dinámicas para todos los centros de costo
        for cc in all_cost_centers:
            await self._calculate_cost_center_properties_safe(cc)
        
        # Crear un diccionario para acceso rápido por ID
        cost_centers_dict = {cc.id: cc for cc in all_cost_centers}
        
        # Construir la estructura de hijos para cada centro de costo
        children_dict = {}
        for cc in all_cost_centers:
            children_dict[cc.id] = []
        
        for cc in all_cost_centers:
            if cc.parent_id and cc.parent_id in children_dict:
                children_dict[cc.parent_id].append(cc)
        
        def build_tree(cost_center: CostCenter) -> CostCenterTree:
            # Obtener hijos desde nuestro diccionario en lugar de la relación lazy
            children_cost_centers = sorted(children_dict.get(cost_center.id, []), key=lambda x: x.code)
            children = []
            
            for child in children_cost_centers:
                if not active_only or child.is_active:
                    children.append(build_tree(child))
            
            return CostCenterTree(
                id=cost_center.id,
                code=cost_center.code,
                name=cost_center.name,
                description=cost_center.description,
                is_active=cost_center.is_active,
                allows_direct_assignment=cost_center.allows_direct_assignment,
                manager_name=cost_center.manager_name,
                level=cost_center.level,
                is_leaf=cost_center.is_leaf,
                children=children
            )
        
        # Solo procesar centros de costo raíz (sin parent_id)
        root_cost_centers = [cc for cc in all_cost_centers if cc.parent_id is None]
        return [build_tree(cc) for cc in sorted(root_cost_centers, key=lambda x: x.code)]
