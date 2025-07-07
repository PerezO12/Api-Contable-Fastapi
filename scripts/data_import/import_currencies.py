#!/usr/bin/env python3
"""
Script para importar todas las monedas del mundo a la base de datos
Solo se ejecuta la primera vez que se inicia el servidor o cuando MAP_CURRENCY=true
"""
import asyncio
import os
import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import List, Tuple, Optional
from sqlalchemy import select, func

from app.database import get_async_db
from app.models.currency import Currency, ExchangeRate
from app.schemas.currency import CurrencyCreate, ExchangeRateCreate
from app.services.currency_service import CurrencyService
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Datos de todas las monedas del mundo
WORLD_CURRENCIES = [
    ("BRL", "R$", "Brazilian real"),
    ("AED", "د.إ", "United Arab Emirates dirham"),
    ("AFN", "Afs", "Afghan afghani"),
    ("ALL", "L", "Albanian lek"),
    ("AMD", "դր.", "Armenian dram"),
    ("ANG", "ƒ", "Netherlands Antillean guilder"),
    ("AOA", "Kz", "Angolan kwanza"),
    ("ARS", "$", "Argentine peso"),
    ("AUD", "$", "Australian dollar"),
    ("AWG", "Afl.", "Aruban florin"),
    ("AZN", "m", "Azerbaijani manat"),
    ("BAM", "KM", "Bosnia and Herzegovina convertible mark"),
    ("BBD", "Bds$", "Barbados dollar"),
    ("BDT", "৳", "Bangladeshi taka"),
    ("BGN", "лв", "Bulgarian lev"),
    ("BHD", "BD", "Bahraini dinar"),
    ("BIF", "FBu", "Burundian franc"),
    ("BMD", "BD$", "Bermudian dollar"),
    ("BND", "$", "Brunei dollar"),
    ("BOB", "Bs.", "Boliviano"),
    ("BSD", "B$", "Bahamian dollar"),
    ("BTN", "Nu.", "Bhutanese ngultrum"),
    ("BWP", "P", "Botswana pula"),
    ("BYN", "Br", "Belarusian ruble"),
    ("BYR", "BR", "Belarusian ruble"),
    ("BZD", "BZ$", "Belize dollar"),
    ("CAD", "$", "Canadian dollar"),
    ("CDF", "Fr", "Congolese franc"),
    ("CHF", "CHF", "Swiss franc"),
    ("CLF", "$", "Unidad de Fomento"),
    ("CLP", "$", "Chilean peso"),
    ("CNH", "¥", "Chinese yuan - Offshore"),
    ("CNY", "¥", "Chinese yuan"),
    ("COP", "$", "Colombian peso"),
    ("COU", "$", "Unidad de Valor Real"),
    ("CRC", "₡", "Costa Rican colón"),
    ("CUC", "$", "Cuban convertible peso"),
    ("CUP", "$", "Cuban peso"),
    ("CVE", "$", "Cape Verdean escudo"),
    ("CZK", "Kč", "Czech koruna"),
    ("DJF", "Fdj", "Djiboutian franc"),
    ("DKK", "kr", "Danish krone"),
    ("DOP", "RD$", "Dominican peso"),
    ("DZD", "DA", "Algerian dinar"),
    ("EGP", "LE", "Egyptian pound"),
    ("ERN", "Nfk", "Eritrean nakfa"),
    ("ETB", "Br", "Ethiopian birr"),
    ("EUR", "€", "Euro"),
    ("FJD", "FJ$", "Fiji dollar"),
    ("FKP", "£", "Falkland Islands pound"),
    ("GBP", "£", "Pound sterling"),
    ("GEL", "ლ", "Georgian lari"),
    ("GHS", "GH¢", "Ghanaian cedi"),
    ("GIP", "£", "Gibraltar pound"),
    ("GMD", "D", "Gambian dalasi"),
    ("GNF", "FG", "Guinean franc"),
    ("GTQ", "Q", "Guatemalan Quetzal"),
    ("GYD", "$", "Guyanese dollar"),
    ("HKD", "$", "Hong Kong dollar"),
    ("HNL", "L", "Honduran lempira"),
    ("HRK", "kn", "Croatian kuna"),
    ("HTG", "G", "Haitian gourde"),
    ("HUF", "Ft", "Hungarian forint"),
    ("IDR", "Rp", "Indonesian rupiah"),
    ("ILS", "₪", "Israeli new shekel"),
    ("INR", "₹", "Indian rupee"),
    ("IQD", " ع.د", "Iraqi dinar"),
    ("IRR", "﷼", "Iranian rial"),
    ("ISK", "kr", "Icelandic króna"),
    ("JMD", "$", "Jamaican dollar"),
    ("JOD", " د.ا ", "Jordanian dinar"),
    ("JPY", "¥", "Japanese yen"),
    ("KES", "KSh", "Kenyan shilling"),
    ("KGS", "лв", "Kyrgyzstani som"),
    ("KHR", "៛", "Cambodian riel"),
    ("KMF", "CF", "Comorian franc"),
    ("KPW", "₩", "North Korean won"),
    ("KRW", "₩", "South Korean won"),
    ("KWD", " د.ك ", "Kuwaiti dinar"),
    ("KYD", "$", "Cayman Islands dollar"),
    ("KZT", "₸", "Kazakhstani tenge"),
    ("LAK", "₭", "Lao kip"),
    ("LBP", "ل.ل", "Lebanese pound"),
    ("LKR", "Rs", "Sri Lankan rupee"),
    ("LRD", "L$", "Liberian dollar"),
    ("LSL", "M", "Lesotho loti"),
    ("LTL", "Lt", "Lithuanian litas"),
    ("LVL", "Ls", "Latvian lats"),
    ("LYD", " ل.د ", "Libyan dinar"),
    ("MAD", "DH", "Moroccan dirham"),
    ("MDL", "L", "Moldovan leu"),
    ("MGA", "Ar", "Malagasy ariary"),
    ("MKD", "ден", "Macedonian denar"),
    ("MMK", "K", "Myanmar kyat"),
    ("MNT", "₮", "Mongolian tögrög"),
    ("MOP", "MOP$", "Macanese pataca"),
    ("MRO", "UM", "Mauritanian ouguiya (old)"),
    ("MRU", "UM", "Mauritanian ouguiya"),
    ("MUR", "Rs", "Mauritian rupee"),
    ("MVR", "Rf", "Maldivian rufiyaa"),
    ("MWK", "MK", "Malawian kwacha"),
    ("MXN", "$", "Mexican peso"),
    ("MYR", "RM", "Malaysian ringgit"),
    ("MZN", "MT", "Mozambican metical"),
    ("NAD", "$", "Namibian dollar"),
    ("NGN", "₦", "Nigerian naira"),
    ("NIO", "C$", "Nicaraguan córdoba"),
    ("NOK", "kr", "Norwegian krone"),
    ("NPR", "₨", "Nepalese rupee"),
    ("NZD", "$", "New Zealand dollar"),
    ("OMR", "ر.ع.", "Omani rial"),
    ("PAB", "B/.", "Panamanian balboa"),
    ("PEN", "S/", "Peruvian sol"),
    ("PGK", "K", "Papua New Guinean kina"),
    ("PHP", "₱", "Philippine peso"),
    ("PKR", "Rs.", "Pakistani rupee"),
    ("PLN", "zł", "Polish złoty"),
    ("PYG", "₲", "Paraguayan guaraní"),
    ("QAR", "QR", "Qatari riyal"),
    ("RON", "lei", "Romanian leu"),
    ("RSD", "din.", "Serbian dinar"),
    ("RUB", "руб", "Russian ruble"),
    ("RWF", "RF", "Rwandan franc"),
    ("SAR", "SR", "Saudi riyal"),
    ("SBD", "SI$", "Solomon Islands dollar"),
    ("SCR", "SR", "Seychellois rupee"),
    ("SDG", "ج.س.", "Sudanese pound"),
    ("SEK", "kr", "Swedish krona"),
    ("SGD", "S$", "Singapore dollar"),
    ("SHP", "£", "Saint Helena pound"),
    ("SLE", "Le", "Sierra Leonean leone"),
    ("SLL", "Le", "Sierra Leonean leone"),
    ("SOS", "Sh.", "Somali shilling"),
    ("SRD", "$", "Surinamese dollar"),
    ("SSP", "£", "South Sudanese pound"),
    ("STD", "Db", "São Tomé and Príncipe dobra"),
    ("STN", "Db", "São Tomé and Príncipe dobra"),
    ("SVC", "¢", "Salvadoran Colon"),
    ("SYP", "£", "Syrian pound"),
    ("SZL", "E", "Swazi lilangeni"),
    ("THB", "฿", "Thai baht"),
    ("TJS", "TJS", "Tajikistani somoni"),
    ("TMT", "T", "Turkmenistan manat"),
    ("TND", "DT", "Tunisian dinar"),
    ("TOP", "T$", "Tongan paʻanga"),
    ("TRY", "₺", "Turkish lira"),
    ("TTD", "$", "Trinidad and Tobago dollar"),
    ("TWD", "NT$", "New Taiwan dollar"),
    ("TZS", "TSh", "Tanzanian shilling"),
    ("UAH", "₴", "Ukraine Hryvnia"),
    ("UGX", "USh", "Ugandan shilling"),
    ("USD", "$", "United States dollar"),
    ("UYI", "$", "Uruguay Peso en Unidades Indexadas"),
    ("UYU", "$", "Uruguayan peso"),
    ("UYW", "$", "Unidad previsional"),
    ("UZS", "лв", "Uzbekistan som"),
    ("VEF", "Bs.F", "Venezuelan bolívar fuerte"),
    ("VES", "Bs", "Venezuelan bolívar soberano"),
    ("VND", "₫", "Vietnamese đồng"),
    ("VUV", "VT", "Vanuatu vatu"),
    ("WST", "WS$", "Samoan tālā"),
    ("XAF", "FCFA", "CFA franc BEAC"),
    ("XCD", "$", "East Caribbean dollar"),
    ("XOF", "CFA", "CFA franc BCEAO"),
    ("XPF", "XPF", "CFP franc"),
    ("YER", "﷼", "Yemeni rial"),
    ("ZAR", "R", "South African rand"),
    ("ZIG", "ZiG", "Zimbabwe Gold"),
    ("ZMW", "ZK", "Zambian kwacha"),
]


async def should_import_currencies():
    """
    Verificar si se debe ejecutar la importación de monedas
    """
    # Verificar variable de entorno
    map_currency = os.getenv('MAP_CURRENCY', 'false').lower() == 'true'
    if not map_currency:
        return False, "Importación de monedas deshabilitada (MAP_CURRENCY=false)"
    
    # Verificar archivo de control
    control_file = "scripts/.currencies_imported"
    if os.path.exists(control_file):
        return False, f"Las monedas ya fueron importadas anteriormente (archivo de control existe: {control_file})"
    
    # Verificar si ya hay suficientes monedas en la base de datos
    async for db in get_async_db():
        try:
            count_result = await db.scalar(
                select(func.count()).select_from(Currency)
            )
            total_currencies = count_result if count_result is not None else 0
            
            # Si ya hay más de 50 monedas, probablemente ya se importaron
            if total_currencies >= 50:
                # Crear archivo de control para evitar futuras verificaciones
                os.makedirs(os.path.dirname(control_file), exist_ok=True)
                with open(control_file, 'w') as f:
                    f.write(f"Currencies imported automatically on {datetime.now().isoformat()}\n")
                    f.write(f"Total currencies found: {total_currencies}\n")
                
                return False, f"Ya existen {total_currencies} monedas en la base de datos"
            
            return True, f"Solo hay {total_currencies} monedas, se procederá con la importación"
            
        except Exception as e:
            logger.error(f"Error verificando estado de monedas: {str(e)}")
            return False, f"Error verificando base de datos: {str(e)}"
        finally:
            await db.close()


async def create_exchange_rate_for_currency(db, currency: Currency, base_currency_code: str = "USD"):
    """
    Crear exchange rate por defecto para una moneda
    """
    # No crear exchange rate para la moneda base
    if currency.code == base_currency_code:
        return
    
    # Verificar si ya tiene exchange rate
    existing = await db.scalar(
        select(ExchangeRate).where(ExchangeRate.currency_id == currency.id)
    )
    
    if existing:
        return  # Ya tiene exchange rate
    
    # Crear exchange rate con valor 1.0
    exchange_rate = ExchangeRate(
        id=uuid.uuid4(),
        currency_id=currency.id,
        rate=Decimal('1.0'),
        rate_date=date.today(),
        source="system",
        provider="import_script",
        notes=f"Tipo de cambio inicial para {currency.code} (importación automática)"
    )
    
    db.add(exchange_rate)
    logger.debug(f"Exchange rate creado para {currency.code}: 1.0")


async def import_currencies_from_data():
    """
    Importar monedas desde los datos definidos en el script
    """
    # Verificar si se debe ejecutar la importación
    should_import, reason = await should_import_currencies()
    if not should_import:
        logger.info(f"Saltando importación de monedas: {reason}")
        return
    
    logger.info(f"Iniciando importación de monedas: {reason}")
    
    async for db in get_async_db():
        try:
            service = CurrencyService(db)
            
            # Obtener moneda base configurada
            base_currency_code = os.getenv('DEFAULT_BASE_CURRENCY', 'USD')
            
            created_count = 0
            updated_count = 0
            error_count = 0
            exchange_rates_created = 0
            
            for code, symbol, name in WORLD_CURRENCIES:
                try:
                    # Verificar si la moneda ya existe
                    existing = await db.scalar(
                        select(Currency).where(Currency.code == code.upper())
                    )
                    
                    if existing:
                        # Actualizar si es necesario
                        if existing.symbol != symbol or existing.name != name:
                            existing.symbol = symbol
                            existing.name = name
                            updated_count += 1
                            logger.debug(f"Moneda actualizada: {code}")
                        
                        # Asegurar que tenga exchange rate
                        await create_exchange_rate_for_currency(db, existing, base_currency_code)
                        if existing.code != base_currency_code:
                            exchange_rates_created += 1
                        
                    else:
                        # Crear nueva moneda
                        currency_data = CurrencyCreate(
                            code=code.upper(),
                            name=name,
                            symbol=symbol,
                            decimal_places=2,
                            is_active=False,  # Por defecto inactivas como establecimos
                            notes=f"Importada automáticamente desde script de inicialización"
                        )
                        
                        currency = Currency(**currency_data.model_dump())
                        db.add(currency)
                        await db.flush()  # Para obtener el ID
                        
                        created_count += 1
                        logger.debug(f"Moneda creada: {code} - {name}")
                        
                        # Crear exchange rate
                        await create_exchange_rate_for_currency(db, currency, base_currency_code)
                        if currency.code != base_currency_code:
                            exchange_rates_created += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error procesando moneda {code}: {str(e)}")
                    continue
            
            # Confirmar todas las transacciones
            await db.commit()
            
            # Crear archivo de control
            control_file = "scripts/.currencies_imported"
            os.makedirs(os.path.dirname(control_file), exist_ok=True)
            with open(control_file, 'w') as f:
                f.write(f"Currencies imported on {datetime.now().isoformat()}\n")
                f.write(f"Total currencies created: {created_count}\n")
                f.write(f"Total currencies updated: {updated_count}\n")
                f.write(f"Total exchange rates created: {exchange_rates_created}\n")
                f.write(f"Total errors: {error_count}\n")
                f.write(f"Base currency: {base_currency_code}\n")
            
            logger.info(
                f"Importación completada: {created_count} creadas, {updated_count} actualizadas, "
                f"{exchange_rates_created} exchange rates creados, {error_count} errores"
            )
            
        except Exception as e:
            logger.error(f"Error en importación de monedas: {str(e)}")
            await db.rollback()
            raise
        finally:
            await db.close()


async def main():
    """
    Función principal para ejecutar la importación
    """
    try:
        await import_currencies_from_data()
    except Exception as e:
        logger.error(f"Error ejecutando importación de monedas: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
