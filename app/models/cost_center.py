"""
Cost Center model for cost accounting functionality.
Implements hierarchical cost centers with parent-child relationships.
"""
import uuid
from typing import Optional, List

from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CostCenter(Base):
    """
    Modelo para centros de costo
    Permite análisis de rentabilidad y control presupuestario por departamento/área
    """
    __tablename__ = "cost_centers"
    
    # Información básica
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Jerarquía (estructura padre-hijo)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("cost_centers.id"), 
        nullable=True
    )
    
    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Configuración
    allows_direct_assignment: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Si permite asignación directa de transacciones o solo es agrupador"
    )
    
    # Metadata adicional
    manager_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    budget_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    parent: Mapped[Optional["CostCenter"]] = relationship(
        "CostCenter", 
        remote_side="CostCenter.id",
        back_populates="children"
    )
    children: Mapped[List["CostCenter"]] = relationship(
        "CostCenter",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<CostCenter(code='{self.code}', name='{self.name}', active={self.is_active})>"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Propiedades calculadas temporales para la respuesta
        self._full_code: Optional[str] = None
        self._level: Optional[int] = None
        self._is_leaf: Optional[bool] = None
    
    # Propiedades calculadas que pueden ser asignadas temporalmente
    @property
    def full_code(self) -> str:
        """Retorna el código completo - usar versión calculada si está disponible"""
        if hasattr(self, '_full_code') and self._full_code is not None:
            return self._full_code
        return self.get_full_code()
    
    @full_code.setter
    def full_code(self, value: str):
        self._full_code = value
    
    @property
    def level(self) -> int:
        """Retorna el nivel - usar versión calculada si está disponible"""
        if hasattr(self, '_level') and self._level is not None:
            return self._level
        return self.get_level()
    
    @level.setter
    def level(self, value: int):
        self._level = value
    
    @property
    def is_leaf(self) -> bool:
        """Verifica si es un nodo hoja - usar versión calculada si está disponible"""
        if hasattr(self, '_is_leaf') and self._is_leaf is not None:
            return self._is_leaf
        return self.get_is_leaf()
    
    @is_leaf.setter
    def is_leaf(self, value: bool):
        self._is_leaf = value

    def get_full_code(self) -> str:
        """Retorna el código completo incluyendo jerarquía"""
        if self.parent:
            return f"{self.parent.get_full_code()}.{self.code}"
        return self.code
    
    def get_level(self) -> int:
        """Retorna el nivel en la jerarquía (0 = raíz)"""
        if self.parent:
            return self.parent.get_level() + 1
        return 0
    
    def get_is_leaf(self) -> bool:
        """Verifica si es un nodo hoja (sin hijos)"""
        return len(self.children) == 0
    
    def get_ancestors(self) -> List["CostCenter"]:
        """Retorna lista de centros de costo ancestros"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self) -> List["CostCenter"]:
        """Retorna lista de todos los descendientes"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    def validate_cost_center(self) -> List[str]:
        """Valida el centro de costo y retorna lista de errores"""
        errors = []
        
        # Validar código único
        if not self.code or len(self.code.strip()) == 0:
            errors.append("El código del centro de costo es requerido")
        
        # Validar nombre
        if not self.name or len(self.name.strip()) == 0:
            errors.append("El nombre del centro de costo es requerido")
        
        # Validar que no se referencie a sí mismo como padre
        # Solo validar si ambos valores no son None (el ID se asigna después del commit)
        if self.parent_id is not None and self.id is not None and self.parent_id == self.id:
            errors.append("Un centro de costo no puede ser su propio padre")
        
        # Validar jerarquía circular (evitar ciclos)
        if self.parent:
            ancestors = self.get_ancestors()
            if self in ancestors:
                errors.append("Se detectó una referencia circular en la jerarquía")
        
        return errors
