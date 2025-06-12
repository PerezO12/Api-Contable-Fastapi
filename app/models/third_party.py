"""
Third Party model for customers, suppliers, employees and other business partners.
Enables customer/supplier accounting and relationship management.
"""
import uuid
from typing import Optional, List
from enum import Enum

from sqlalchemy import String, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ThirdPartyType(str, Enum):
    """Tipos de terceros"""
    CUSTOMER = "customer"       # Cliente
    SUPPLIER = "supplier"       # Proveedor
    EMPLOYEE = "employee"       # Empleado
    SHAREHOLDER = "shareholder" # Accionista
    BANK = "bank"              # Banco
    GOVERNMENT = "government"   # Entidades gubernamentales
    OTHER = "other"            # Otros


class DocumentType(str, Enum):
    """Tipos de documento de identidad"""
    RUT = "rut"                # RUT (Chile)
    NIT = "nit"                # NIT (Colombia)
    CUIT = "cuit"              # CUIT (Argentina)
    RFC = "rfc"                # RFC (México)
    PASSPORT = "passport"       # Pasaporte
    DNI = "dni"                # DNI/Cédula
    OTHER = "other"            # Otro


class ThirdParty(Base):
    """
    Modelo para terceros (clientes, proveedores, empleados, etc.)
    Centraliza la información de contactos comerciales para reporting y CRM básico
    """
    __tablename__ = "third_parties"
    
    # Información básica
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    commercial_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Clasificación
    third_party_type: Mapped[ThirdPartyType] = mapped_column(
        SQLEnum(ThirdPartyType),
        nullable=False,
        index=True
    )
    
    # Identificación
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
        nullable=False
    )
    document_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # RUT, NIT, etc.
    
    # Información de contacto
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Dirección
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Información comercial
    credit_limit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Límite de crédito
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Términos de pago
    discount_percentage: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # % descuento
    
    # Información bancaria
    bank_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Estado y configuración
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_tax_withholding_agent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Código interno adicional
    
    def __repr__(self) -> str:
        return f"<ThirdParty(code='{self.code}', name='{self.name}', type='{self.third_party_type}')>"
    
    @property
    def display_name(self) -> str:
        """Retorna el nombre a mostrar (comercial si existe, sino el legal)"""
        return self.commercial_name if self.commercial_name else self.name
    
    @property
    def full_address(self) -> str:
        """Retorna la dirección completa concatenada"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts)
    
    @property
    def is_customer(self) -> bool:
        """Verifica si es cliente"""
        return self.third_party_type == ThirdPartyType.CUSTOMER
    
    @property
    def is_supplier(self) -> bool:
        """Verifica si es proveedor"""
        return self.third_party_type == ThirdPartyType.SUPPLIER
    
    @property
    def is_employee(self) -> bool:
        """Verifica si es empleado"""
        return self.third_party_type == ThirdPartyType.EMPLOYEE
    
    def validate_third_party(self) -> List[str]:
        """Valida el tercero y retorna lista de errores"""
        errors = []
        
        # Validar código único
        if not self.code or len(self.code.strip()) == 0:
            errors.append("El código del tercero es requerido")
        
        # Validar nombre
        if not self.name or len(self.name.strip()) == 0:
            errors.append("El nombre del tercero es requerido")
        
        # Validar número de documento
        if not self.document_number or len(self.document_number.strip()) == 0:
            errors.append("El número de documento es requerido")
        
        # Validar email si está presente
        if self.email and "@" not in self.email:
            errors.append("El formato del email es inválido")
        
        # Validaciones específicas por tipo de documento
        if self.document_type == DocumentType.RUT and self.document_number:
            # Validación básica de RUT chileno (formato: 12345678-9)
            if "-" not in self.document_number and "." not in self.document_number:
                errors.append("El RUT debe tener formato válido (ej: 12345678-9)")
        
        return errors
