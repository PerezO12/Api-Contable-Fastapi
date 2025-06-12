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
    BulkCostCenterOperation, CostCenterStats, CostCenterImport, CostCenterRead
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
            select(CostCenter).where(CostCenter.id == cost_center_id)
        )
        cost_center = result.scalar_one_or_none()
        
        if cost_center:
            # Calcular propiedades dinámicas de forma segura
            await self._calculate_cost_center_properties_safe(cost_center)
        
        return cost_center

    async def get_cost_center_by_code(self, code: str) -> Optional[CostCenter]:
        """Obtener centro de costo por código"""
        result = await self.db.execute(
            select(CostCenter).where(CostCenter.code == code)
        )
        return result.scalar_one_or_none()

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
                children_count=len(cc.children)            )
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
