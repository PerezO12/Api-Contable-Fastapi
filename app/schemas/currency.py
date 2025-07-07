"""
Schemas for Currency and Exchange Rate management
"""
import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


# === CURRENCY SCHEMAS ===

class CurrencyBase(BaseModel):
    """Schema base para monedas"""
    code: str = Field(
        ..., 
        min_length=3, 
        max_length=3, 
        pattern="^[A-Z]{3}$",
        description="Código ISO 4217 de la moneda (USD, EUR, etc.)"
    )
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Nombre completo de la moneda"
    )
    symbol: Optional[str] = Field(
        None, 
        max_length=10,
        description="Símbolo de la moneda ($, €, etc.)"
    )
    decimal_places: int = Field(
        default=2, 
        ge=0, 
        le=8,
        description="Número de decimales para esta moneda"
    )
    country_code: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=2, 
        pattern="^[A-Z]{2}$",
        description="Código ISO del país principal (opcional)"
    )
    notes: Optional[str] = Field(
        None, 
        max_length=500,
        description="Notas adicionales sobre la moneda"
    )
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """Valida y convierte el código a mayúsculas"""
        return v.upper().strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Valida y limpia el nombre"""
        return v.strip().title()
    
    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v):
        """Valida el código de país"""
        if v:
            return v.upper().strip()
        return v


class CurrencyCreate(CurrencyBase):
    """Schema para crear monedas"""
    is_active: bool = Field(default=True, description="Si la moneda está activa")


class CurrencyUpdate(BaseModel):
    """Schema para actualizar monedas"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    symbol: Optional[str] = Field(None, max_length=10)
    decimal_places: Optional[int] = Field(None, ge=0, le=8)
    is_active: Optional[bool] = None
    country_code: Optional[str] = Field(None, min_length=2, max_length=2, pattern="^[A-Z]{2}$")
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v:
            return v.strip().title()
        return v
    
    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v):
        if v:
            return v.upper().strip()
        return v


class CurrencyRead(CurrencyBase):
    """Schema para leer monedas"""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CurrencyList(BaseModel):
    """Schema para lista paginada de monedas"""
    currencies: List[CurrencyRead]
    total: int
    page: int
    size: int
    pages: int


class CurrencySummary(BaseModel):
    """Schema resumido para monedas en dropdowns"""
    id: uuid.UUID
    code: str
    name: str
    symbol: Optional[str] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI"""
        if self.symbol:
            return f"{self.code} ({self.symbol}) - {self.name}"
        return f"{self.code} - {self.name}"


# === EXCHANGE RATE SCHEMAS ===

class ExchangeRateBase(BaseModel):
    """Schema base para tipos de cambio"""
    currency_id: uuid.UUID = Field(..., description="ID de la moneda")
    rate: Decimal = Field(
        ..., 
        gt=0, 
        decimal_places=6,
        description="Tasa de cambio: 1 unidad de esta moneda = rate unidades de moneda base"
    )
    rate_date: date = Field(..., description="Fecha de vigencia del tipo de cambio")
    source: str = Field(
        default="manual", 
        max_length=50,
        description="Origen del tipo de cambio (manual, api_import, etc.)"
    )
    provider: Optional[str] = Field(
        None, 
        max_length=100,
        description="Proveedor de la tasa (si es automática)"
    )
    notes: Optional[str] = Field(
        None, 
        max_length=500,
        description="Notas adicionales sobre este tipo de cambio"
    )
    
    @field_validator('rate_date')
    @classmethod
    def validate_rate_date(cls, v):
        """Valida que la fecha no sea futura"""
        if v > date.today():
            raise ValueError("La fecha del tipo de cambio no puede ser futura")
        return v


class ExchangeRateCreate(ExchangeRateBase):
    """Schema para crear tipos de cambio"""
    pass


class ExchangeRateUpdate(BaseModel):
    """Schema para actualizar tipos de cambio"""
    rate: Optional[Decimal] = Field(None, gt=0, decimal_places=6)
    source: Optional[str] = Field(None, max_length=50)
    provider: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class ExchangeRateRead(ExchangeRateBase):
    """Schema para leer tipos de cambio"""
    id: uuid.UUID
    currency: CurrencySummary
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExchangeRateList(BaseModel):
    """Schema para lista paginada de tipos de cambio"""
    exchange_rates: List[ExchangeRateRead]
    total: int
    page: int
    size: int
    pages: int


class ExchangeRateSummary(BaseModel):
    """Schema resumido para tipos de cambio"""
    id: uuid.UUID
    currency_code: str
    rate: Decimal
    rate_date: date
    source: str
    
    model_config = ConfigDict(from_attributes=True)


# === CONVERSION SCHEMAS ===

class CurrencyConversionRequest(BaseModel):
    """Schema para solicitud de conversión de moneda"""
    amount: Decimal = Field(..., gt=0, description="Importe a convertir")
    from_currency_code: str = Field(..., min_length=3, max_length=3, description="Código de moneda origen")
    to_currency_code: str = Field(..., min_length=3, max_length=3, description="Código de moneda destino")
    conversion_date: Optional[date] = Field(None, description="Fecha para la conversión (por defecto hoy)")
    
    @field_validator('from_currency_code', 'to_currency_code')
    @classmethod
    def validate_currency_codes(cls, v):
        return v.upper().strip()


class CurrencyConversionResponse(BaseModel):
    """Schema para respuesta de conversión de moneda"""
    original_amount: Decimal
    converted_amount: Decimal
    from_currency_code: str
    to_currency_code: str
    exchange_rate: Decimal
    conversion_date: date
    rate_source: str


# === IMPORT/EXPORT SCHEMAS ===

class ExchangeRateImportRequest(BaseModel):
    """Schema para importación masiva de tipos de cambio"""
    provider: str = Field(default="manual", description="Proveedor de las tasas")
    import_date: date = Field(default_factory=date.today, description="Fecha de importación")
    currency_codes: Optional[List[str]] = Field(None, description="Códigos de moneda específicos (opcional)")
    overwrite_existing: bool = Field(default=False, description="Sobrescribir tasas existentes")


class ExchangeRateImportResult(BaseModel):
    """Schema para resultado de importación"""
    imported_count: int
    updated_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# === FILTERING SCHEMAS ===

class CurrencyFilter(BaseModel):
    """Schema para filtros de búsqueda de monedas"""
    code: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    country_code: Optional[str] = None


class ExchangeRateFilter(BaseModel):
    """Schema para filtros de búsqueda de tipos de cambio"""
    currency_code: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    source: Optional[str] = None
    provider: Optional[str] = None


# === MULTI-CURRENCY JOURNAL ENTRY SCHEMAS ===

class JournalEntryLineCurrency(BaseModel):
    """Schema para información de moneda en líneas de asiento"""
    currency_id: Optional[uuid.UUID] = Field(None, description="ID de la moneda original")
    amount_currency: Optional[Decimal] = Field(None, description="Importe en moneda original")
    exchange_rate_id: Optional[uuid.UUID] = Field(None, description="ID del tipo de cambio utilizado")
    
    @field_validator('amount_currency')
    @classmethod
    def validate_currency_amount(cls, v, info):
        """Validar que si hay amount_currency, también hay currency_id"""
        values = info.data if hasattr(info, 'data') else {}
        if v is not None and values.get('currency_id') is None:
            raise ValueError('currency_id es requerido cuando se especifica amount_currency')
        return v


class JournalEntryLineWithCurrency(BaseModel):
    """Schema extendido para líneas de asiento con información de moneda"""
    # Campos base de la línea
    account_id: uuid.UUID
    debit_amount: Decimal
    credit_amount: Decimal
    description: Optional[str] = None
    
    # Campos multi-currency
    currency_info: Optional[JournalEntryLineCurrency] = None
    
    # Propiedades calculadas
    currency_code: Optional[str] = None
    exchange_rate_value: Optional[Decimal] = None
    amount_in_base_currency: Optional[Decimal] = None
    
    model_config = ConfigDict(from_attributes=True)
