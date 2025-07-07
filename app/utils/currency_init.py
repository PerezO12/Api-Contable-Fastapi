"""
Currency initialization script
Crea monedas por defecto al inicializar la base de datos
"""
import asyncio
import os
from decimal import Decimal
from datetime import date
from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.currency import Currency, ExchangeRate
from app.models.company_settings import CompanySettings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Monedas comunes con información completa
DEFAULT_CURRENCIES = [
    {
        "code": "USD",
        "name": "United States Dollar",
        "symbol": "$",
        "decimal_places": 2,
        "country_code": "US",
        "notes": "Moneda base por defecto del sistema"
    },
    {
        "code": "EUR", 
        "name": "Euro",
        "symbol": "€",
        "decimal_places": 2,
        "country_code": "DE",
        "notes": "Moneda común europea"
    },
    {
        "code": "GBP",
        "name": "British Pound Sterling", 
        "symbol": "£",
        "decimal_places": 2,
        "country_code": "GB",
        "notes": "Libra esterlina británica"
    },
    {
        "code": "JPY",
        "name": "Japanese Yen",
        "symbol": "¥",
        "decimal_places": 0,
        "country_code": "JP", 
        "notes": "Yen japonés - sin decimales"
    },
    {
        "code": "CAD",
        "name": "Canadian Dollar",
        "symbol": "C$",
        "decimal_places": 2,
        "country_code": "CA",
        "notes": "Dólar canadiense"
    },
    {
        "code": "AUD",
        "name": "Australian Dollar",
        "symbol": "A$",
        "decimal_places": 2,
        "country_code": "AU",
        "notes": "Dólar australiano"
    },
    {
        "code": "CHF",
        "name": "Swiss Franc",
        "symbol": "CHF",
        "decimal_places": 2,
        "country_code": "CH",
        "notes": "Franco suizo"
    },
    {
        "code": "SEK",
        "name": "Swedish Krona",
        "symbol": "kr",
        "decimal_places": 2,
        "country_code": "SE",
        "notes": "Corona sueca"
    },
    {
        "code": "NOK",
        "name": "Norwegian Krone",
        "symbol": "kr",
        "decimal_places": 2,
        "country_code": "NO",
        "notes": "Corona noruega"
    },
    {
        "code": "DKK",
        "name": "Danish Krone",
        "symbol": "kr",
        "decimal_places": 2,
        "country_code": "DK",
        "notes": "Corona danesa"
    },
    {
        "code": "COP",
        "name": "Colombian Peso",
        "symbol": "$",
        "decimal_places": 2,
        "country_code": "CO",
        "notes": "Peso colombiano"
    },
    {
        "code": "MXN",
        "name": "Mexican Peso",
        "symbol": "$",
        "decimal_places": 2,
        "country_code": "MX",
        "notes": "Peso mexicano"
    },
    {
        "code": "BRL",
        "name": "Brazilian Real",
        "symbol": "R$",
        "decimal_places": 2,
        "country_code": "BR",
        "notes": "Real brasileño"
    },
    {
        "code": "ARS",
        "name": "Argentine Peso",
        "symbol": "$",
        "decimal_places": 2,
        "country_code": "AR",
        "notes": "Peso argentino"
    },
    {
        "code": "CLP",
        "name": "Chilean Peso",
        "symbol": "$",
        "decimal_places": 0,
        "country_code": "CL",
        "notes": "Peso chileno - sin decimales"
    }
]


class CurrencyInitializer:
    """
    Servicio para inicializar monedas por defecto
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def initialize_default_currencies(self, force: bool = False) -> List[Currency]:
        """
        Inicializar monedas por defecto
        """
        logger.info("Inicializando monedas por defecto...")
        
        # Obtener lista de monedas a crear desde env
        env_currencies = os.getenv("DEFAULT_CURRENCIES", "USD,EUR,GBP,JPY,CAD")
        currency_codes = [code.strip().upper() for code in env_currencies.split(",")]
        
        created_currencies = []
        
        for currency_data in DEFAULT_CURRENCIES:
            code = currency_data["code"]
            
            # Solo crear si está en la lista de env
            if code not in currency_codes:
                continue
            
            # Verificar si ya existe
            existing = await self.db.scalar(
                select(Currency).where(Currency.code == code)
            )
            
            if existing and not force:
                logger.info(f"Moneda {code} ya existe, omitiendo...")
                continue
            
            if existing and force:
                logger.info(f"Actualizando moneda existente {code}...")
                for field, value in currency_data.items():
                    if field != "code":  # No cambiar el código
                        setattr(existing, field, value)
                await self.db.commit()
                await self.db.refresh(existing)
                created_currencies.append(existing)
            else:
                # Crear nueva moneda
                logger.info(f"Creando moneda {code}...")
                currency = Currency(**currency_data)
                self.db.add(currency)
                await self.db.commit()
                await self.db.refresh(currency)
                created_currencies.append(currency)
        
        logger.info(f"Inicializadas {len(created_currencies)} monedas")
        return created_currencies
    
    async def set_base_currency_from_env(self) -> Currency:
        """
        Establecer la moneda base desde variable de entorno
        """
        base_currency_code = os.getenv("DEFAULT_BASE_CURRENCY", "USD").upper()
        
        logger.info(f"Configurando moneda base: {base_currency_code}")
        
        # Buscar la moneda
        currency = await self.db.scalar(
            select(Currency).where(Currency.code == base_currency_code)
        )
        
        if not currency:
            logger.warning(f"Moneda base {base_currency_code} no existe, creándola...")
            # Buscar en defaults
            currency_data = next(
                (c for c in DEFAULT_CURRENCIES if c["code"] == base_currency_code),
                {
                    "code": base_currency_code,
                    "name": f"{base_currency_code} Currency",
                    "symbol": base_currency_code,
                    "decimal_places": 2,
                    "notes": "Moneda base creada automáticamente"
                }
            )
            currency = Currency(**currency_data)
            self.db.add(currency)
            await self.db.commit()
            await self.db.refresh(currency)
        
        # Actualizar configuración de empresa
        settings = await self.db.scalar(
            select(CompanySettings).where(CompanySettings.is_active == True)
        )
        
        if settings:
            settings.base_currency_id = currency.id
            settings.currency_code = currency.code  # Mantener compatibilidad
            await self.db.commit()
            logger.info(f"Moneda base configurada en CompanySettings: {currency.code}")
        else:
            logger.warning("No se encontró configuración de empresa activa")
        
        return currency
    
    async def create_sample_exchange_rates(self, base_currency_code: str = "USD") -> List[ExchangeRate]:
        """
        Crear tipos de cambio de ejemplo (solo para desarrollo)
        """
        if os.getenv("ENVIRONMENT") != "development":
            logger.info("No creando tipos de cambio de ejemplo en entorno no-desarrollo")
            return []
        
        logger.info("Creando tipos de cambio de ejemplo para desarrollo...")
        
        # Tasas de ejemplo (NO usar en producción)
        sample_rates = {
            "EUR": Decimal("0.85"),
            "GBP": Decimal("0.73"),
            "JPY": Decimal("110.0"),
            "CAD": Decimal("1.25"),
            "AUD": Decimal("1.35"),
            "CHF": Decimal("0.92"),
            "COP": Decimal("4000.0"),
            "MXN": Decimal("18.5"),
            "BRL": Decimal("5.2")
        }
        
        created_rates = []
        today = date.today()
        
        for currency_code, rate_value in sample_rates.items():
            if currency_code == base_currency_code:
                continue
            
            # Buscar la moneda
            currency = await self.db.scalar(
                select(Currency).where(Currency.code == currency_code)
            )
            
            if not currency:
                continue
            
            # Verificar si ya existe tipo de cambio para hoy
            existing_rate = await self.db.scalar(
                select(ExchangeRate).where(
                    ExchangeRate.currency_id == currency.id,
                    ExchangeRate.rate_date == today
                )
            )
            
            if existing_rate:
                logger.info(f"Ya existe tipo de cambio para {currency_code} hoy")
                continue
            
            # Crear tipo de cambio
            exchange_rate = ExchangeRate(
                currency_id=currency.id,
                rate=rate_value,
                rate_date=today,
                source="sample_data",
                provider="development",
                notes="Tipo de cambio de ejemplo para desarrollo"
            )
            
            self.db.add(exchange_rate)
            created_rates.append(exchange_rate)
            logger.info(f"Creado tipo de cambio: 1 {currency_code} = {rate_value} {base_currency_code}")
        
        if created_rates:
            await self.db.commit()
            
            # Refresh all created rates
            for rate in created_rates:
                await self.db.refresh(rate)
        
        logger.info(f"Creados {len(created_rates)} tipos de cambio de ejemplo")
        return created_rates


async def initialize_currencies():
    """
    Función principal para inicializar monedas
    """
    logger.info("=== INICIANDO INICIALIZACIÓN DE MONEDAS ===")
    
    try:
        async for db in get_async_db():
            initializer = CurrencyInitializer(db)
            
            # 1. Crear monedas por defecto
            currencies = await initializer.initialize_default_currencies()
            
            # 2. Configurar moneda base
            base_currency = await initializer.set_base_currency_from_env()
            
            # 3. Crear tipos de cambio de ejemplo (solo desarrollo)
            if os.getenv("ENVIRONMENT") == "development":
                exchange_rates = await initializer.create_sample_exchange_rates(base_currency.code)
            
            logger.info("=== INICIALIZACIÓN DE MONEDAS COMPLETADA ===")
            break
            
    except Exception as e:
        logger.error(f"Error inicializando monedas: {str(e)}")
        raise


if __name__ == "__main__":
    # Ejecutar directamente si se llama el script
    asyncio.run(initialize_currencies())
