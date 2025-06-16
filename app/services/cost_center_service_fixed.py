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
        
        # Validar que no exista un centro de costo con el mismo nombre (case sensitive)
        existing_name_result = await self.db.execute(
            select(CostCenter).where(CostCenter.name == cost_center_data.name)
        )
        existing_name_center = existing_name_result.scalar_one_or_none()
        
        if existing_name_center:
            raise ConflictError(f"Ya existe un centro de costo con el nombre '{cost_center_data.name}'")
        
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

    async def _calculate_cost_center_properties_safe(self, cost_center: CostCenter) -> None:
        """Calcular propiedades dinámicas del centro de costo de forma segura"""
        # Calcular full_code
        if cost_center.parent_id:
            parent_full_code = await self._get_parent_full_code_by_id(cost_center.parent_id)
            cost_center.full_code = f"{parent_full_code}.{cost_center.code}"
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
    
    async def _get_parent_full_code_by_id(self, parent_id: uuid.UUID) -> str:
        """Obtener el código completo de un centro de costo por ID"""
        result = await self.db.execute(
            select(CostCenter).where(CostCenter.id == parent_id)
        )
        parent = result.scalar_one_or_none()
        
        if not parent:
            return ""
        
        if parent.parent_id:
            parent_full_code = await self._get_parent_full_code_by_id(parent.parent_id)
            return f"{parent_full_code}.{parent.code}"
        
        return parent.code
    
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
