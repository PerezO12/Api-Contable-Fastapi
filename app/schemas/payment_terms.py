import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Esquemas para cronograma de pagos
class PaymentScheduleBase(BaseModel):
    """Schema base para cronograma de pagos"""
    sequence: int = Field(..., ge=1, description="Orden del pago")
    days: int = Field(..., ge=0, description="Días desde la fecha de factura")
    percentage: Decimal = Field(..., gt=0, le=100, description="Porcentaje a pagar")
    description: Optional[str] = Field(None, max_length=200, description="Descripción del período")


class PaymentScheduleCreate(PaymentScheduleBase):
    """Schema para crear cronograma de pagos"""
    pass


class PaymentScheduleUpdate(BaseModel):
    """Schema para actualizar cronograma de pagos"""
    sequence: Optional[int] = Field(None, ge=1)
    days: Optional[int] = Field(None, ge=0)
    percentage: Optional[Decimal] = Field(None, gt=0, le=100)
    description: Optional[str] = Field(None, max_length=200)


class PaymentScheduleRead(PaymentScheduleBase):
    """Schema para leer cronograma de pagos"""
    id: uuid.UUID
    payment_terms_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Esquemas para condiciones de pago
class PaymentTermsBase(BaseModel):
    """Schema base para condiciones de pago"""
    code: str = Field(..., min_length=1, max_length=20, description="Código único")
    name: str = Field(..., min_length=1, max_length=100, description="Nombre descriptivo")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción detallada")
    is_active: bool = Field(True, description="Estado activo/inactivo")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas adicionales")


class PaymentTermsCreate(PaymentTermsBase):
    """Schema para crear condiciones de pago"""
    payment_schedules: List[PaymentScheduleCreate] = Field(..., min_length=1, description="Cronograma de pagos")
    
    @field_validator('payment_schedules')
    @classmethod
    def validate_payment_schedules(cls, v):
        """Valida que el cronograma de pagos sea correcto"""
        if not v:
            raise ValueError("Debe tener al menos un período de pago")
        
        # Validar que las secuencias sean únicas y consecutivas
        sequences = [schedule.sequence for schedule in v]
        if len(set(sequences)) != len(sequences):
            raise ValueError("Las secuencias deben ser únicas")
        
        if sorted(sequences) != list(range(1, len(sequences) + 1)):
            raise ValueError("Las secuencias deben ser consecutivas empezando en 1")
        
        # Validar que el total de porcentajes sea 100%
        total_percentage = sum(schedule.percentage for schedule in v)
        if abs(total_percentage - Decimal('100.00')) > Decimal('0.01'):
            raise ValueError(f"El total de porcentajes debe ser 100%. Actual: {total_percentage}%")
        
        # Validar que los días estén en orden ascendente
        days_list = [schedule.days for schedule in sorted(v, key=lambda x: x.sequence)]
        if days_list != sorted(days_list):
            raise ValueError("Los días deben estar en orden ascendente según la secuencia")
        
        return v


class PaymentTermsUpdate(BaseModel):
    """Schema para actualizar condiciones de pago"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)
    payment_schedules: Optional[List[PaymentScheduleCreate]] = None
    
    @field_validator('payment_schedules')
    @classmethod
    def validate_payment_schedules(cls, v):
        """Valida que el cronograma de pagos sea correcto si se proporciona"""
        if v is None:
            return v
        
        # Aplicar las mismas validaciones que en PaymentTermsCreate
        if not v:
            raise ValueError("Debe tener al menos un período de pago")
        
        sequences = [schedule.sequence for schedule in v]
        if len(set(sequences)) != len(sequences):
            raise ValueError("Las secuencias deben ser únicas")
        
        if sorted(sequences) != list(range(1, len(sequences) + 1)):
            raise ValueError("Las secuencias deben ser consecutivas empezando en 1")
        
        total_percentage = sum(schedule.percentage for schedule in v)
        if abs(total_percentage - Decimal('100.00')) > Decimal('0.01'):
            raise ValueError(f"El total de porcentajes debe ser 100%. Actual: {total_percentage}%")
        
        days_list = [schedule.days for schedule in sorted(v, key=lambda x: x.sequence)]
        if days_list != sorted(days_list):
            raise ValueError("Los días deben estar en orden ascendente según la secuencia")
        
        return v


class PaymentTermsRead(PaymentTermsBase):
    """Schema para leer condiciones de pago"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    total_percentage: Decimal = Decimal('0.00')
    is_valid: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class PaymentTermsDetail(PaymentTermsRead):
    """Schema para detalles completos de condiciones de pago"""
    payment_schedules: List[PaymentScheduleRead] = []


class PaymentTermsSummary(BaseModel):
    """Schema para resumen de condiciones de pago"""
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    total_percentage: Decimal
    schedule_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# Esquemas para cálculos de pago
class PaymentCalculation(BaseModel):
    """Schema para cálculo de fechas y montos de pago"""
    sequence: int
    days: int
    percentage: Decimal
    amount: Decimal
    payment_date: date
    description: Optional[str] = None


class PaymentCalculationRequest(BaseModel):
    """Schema para solicitar cálculo de pagos"""
    payment_terms_id: uuid.UUID
    invoice_date: date
    total_amount: Decimal = Field(..., gt=0)


class PaymentCalculationResponse(BaseModel):
    """Schema para respuesta de cálculo de pagos"""
    payment_terms_code: str
    payment_terms_name: str
    invoice_date: date
    total_amount: Decimal
    payments: List[PaymentCalculation]
    final_due_date: date


# Esquemas para filtros
class PaymentTermsFilter(BaseModel):
    """Schema para filtros de búsqueda de condiciones de pago"""
    is_active: Optional[bool] = None
    search_text: Optional[str] = Field(None, description="Texto a buscar en código, nombre o descripción")
    min_days: Optional[int] = Field(None, ge=0, description="Días mínimos del primer pago")
    max_days: Optional[int] = Field(None, ge=0, description="Días máximos del último pago")
