#!/usr/bin/env python3
"""
Script para importar todas las monedas mundiales a la base de datos
Solo se ejecuta la primera vez o si se fuerza la reimportación
"""
import asyncio
import os
import sys
import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy import select, func

# Agregar el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_async_db
from app.models.currency import Currency, ExchangeRate
from app.core.settings import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Datos completos de todas las monedas mundiales
WORLD_CURRENCIES = [
    {"code": "BRL", "symbol": "R$", "name": "Brazilian real"},
    {"code": "AED", "symbol": "د.إ", "name": "United Arab Emirates dirham"},
    {"code": "AFN", "symbol": "Afs", "name": "Afghan afghani"},
    {"code": "ALL", "symbol": "L", "name": "Albanian lek"},
    {"code": "AMD", "symbol": "դր.", "name": "Armenian dram"},
    {"code": "ANG", "symbol": "ƒ", "name": "Netherlands Antillean guilder"},
    {"code": "AOA", "symbol": "Kz", "name": "Angolan kwanza"},
    {"code": "ARS", "symbol": "$", "name": "Argentine peso"},
    {"code": "AUD", "symbol": "$", "name": "Australian dollar"},
    {"code": "AWG", "symbol": "Afl.", "name": "Aruban florin"},
    {"code": "AZN", "symbol": "m", "name": "Azerbaijani manat"},
    {"code": "BAM", "symbol": "KM", "name": "Bosnia and Herzegovina convertible mark"},
    {"code": "BBD", "symbol": "Bds$", "name": "Barbados dollar"},
    {"code": "BDT", "symbol": "৳", "name": "Bangladeshi taka"},
    {"code": "BGN", "symbol": "лв", "name": "Bulgarian lev"},
    {"code": "BHD", "symbol": "BD", "name": "Bahraini dinar"},
    {"code": "BIF", "symbol": "FBu", "name": "Burundian franc"},
    {"code": "BMD", "symbol": "BD$", "name": "Bermudian dollar"},
    {"code": "BND", "symbol": "$", "name": "Brunei dollar"},
    {"code": "BOB", "symbol": "Bs.", "name": "Boliviano"},
    {"code": "BSD", "symbol": "B$", "name": "Bahamian dollar"},
    {"code": "BTN", "symbol": "Nu.", "name": "Bhutanese ngultrum"},
    {"code": "BWP", "symbol": "P", "name": "Botswana pula"},
    {"code": "BYN", "symbol": "Br", "name": "Belarusian ruble"},
    {"code": "BYR", "symbol": "BR", "name": "Belarusian ruble"},
    {"code": "BZD", "symbol": "BZ$", "name": "Belize dollar"},
    {"code": "CAD", "symbol": "$", "name": "Canadian dollar"},
    {"code": "CDF", "symbol": "Fr", "name": "Congolese franc"},
    {"code": "CHF", "symbol": "CHF", "name": "Swiss franc"},
    {"code": "CLF", "symbol": "$", "name": "Unidad de Fomento"},
    {"code": "CLP", "symbol": "$", "name": "Chilean peso"},
    {"code": "CNH", "symbol": "¥", "name": "Chinese yuan - Offshore"},
    {"code": "CNY", "symbol": "¥", "name": "Chinese yuan"},
    {"code": "COP", "symbol": "$", "name": "Colombian peso"},
    {"code": "COU", "symbol": "$", "name": "Unidad de Valor Real"},
    {"code": "CRC", "symbol": "₡", "name": "Costa Rican colón"},
    {"code": "CUC", "symbol": "$", "name": "Cuban convertible peso"},
    {"code": "CUP", "symbol": "$", "name": "Cuban peso"},
    {"code": "CVE", "symbol": "$", "name": "Cape Verdean escudo"},
    {"code": "CZK", "symbol": "Kč", "name": "Czech koruna"},
    {"code": "DJF", "symbol": "Fdj", "name": "Djiboutian franc"},
    {"code": "DKK", "symbol": "kr", "name": "Danish krone"},
    {"code": "DOP", "symbol": "RD$", "name": "Dominican peso"},
    {"code": "DZD", "symbol": "DA", "name": "Algerian dinar"},
    {"code": "EGP", "symbol": "LE", "name": "Egyptian pound"},
    {"code": "ERN", "symbol": "Nfk", "name": "Eritrean nakfa"},
    {"code": "ETB", "symbol": "Br", "name": "Ethiopian birr"},
    {"code": "EUR", "symbol": "€", "name": "Euro"},
    {"code": "FJD", "symbol": "FJ$", "name": "Fiji dollar"},
    {"code": "FKP", "symbol": "£", "name": "Falkland Islands pound"},
    {"code": "GBP", "symbol": "£", "name": "Pound sterling"},
    {"code": "GEL", "symbol": "ლ", "name": "Georgian lari"},
    {"code": "GHS", "symbol": "GH¢", "name": "Ghanaian cedi"},
    {"code": "GIP", "symbol": "£", "name": "Gibraltar pound"},
    {"code": "GMD", "symbol": "D", "name": "Gambian dalasi"},
    {"code": "GNF", "symbol": "FG", "name": "Guinean franc"},
    {"code": "GTQ", "symbol": "Q", "name": "Guatemalan Quetzal"},
    {"code": "GYD", "symbol": "$", "name": "Guyanese dollar"},
    {"code": "HKD", "symbol": "$", "name": "Hong Kong dollar"},
    {"code": "HNL", "symbol": "L", "name": "Honduran lempira"},
    {"code": "HRK", "symbol": "kn", "name": "Croatian kuna"},
    {"code": "HTG", "symbol": "G", "name": "Haitian gourde"},
    {"code": "HUF", "symbol": "Ft", "name": "Hungarian forint"},
    {"code": "IDR", "symbol": "Rp", "name": "Indonesian rupiah"},
    {"code": "ILS", "symbol": "₪", "name": "Israeli new shekel"},
    {"code": "INR", "symbol": "₹", "name": "Indian rupee"},
    {"code": "IQD", "symbol": " ع.د", "name": "Iraqi dinar"},
    {"code": "IRR", "symbol": "﷼", "name": "Iranian rial"},
    {"code": "ISK", "symbol": "kr", "name": "Icelandic króna"},
    {"code": "JMD", "symbol": "$", "name": "Jamaican dollar"},
    {"code": "JOD", "symbol": " د.ا ", "name": "Jordanian dinar"},
    {"code": "JPY", "symbol": "¥", "name": "Japanese yen"},
    {"code": "KES", "symbol": "KSh", "name": "Kenyan shilling"},
    {"code": "KGS", "symbol": "лв", "name": "Kyrgyzstani som"},
    {"code": "KHR", "symbol": "៛", "name": "Cambodian riel"},
    {"code": "KMF", "symbol": "CF", "name": "Comorian franc"},
    {"code": "KPW", "symbol": "₩", "name": "North Korean won"},
    {"code": "KRW", "symbol": "₩", "name": "South Korean won"},
    {"code": "KWD", "symbol": " د.ك ", "name": "Kuwaiti dinar"},
    {"code": "KYD", "symbol": "$", "name": "Cayman Islands dollar"},
    {"code": "KZT", "symbol": "₸", "name": "Kazakhstani tenge"},
    {"code": "LAK", "symbol": "₭", "name": "Lao kip"},
    {"code": "LBP", "symbol": "ل.ل", "name": "Lebanese pound"},
    {"code": "LKR", "symbol": "Rs", "name": "Sri Lankan rupee"},
    {"code": "LRD", "symbol": "L$", "name": "Liberian dollar"},
    {"code": "LSL", "symbol": "M", "name": "Lesotho loti"},
    {"code": "LTL", "symbol": "Lt", "name": "Lithuanian litas"},
    {"code": "LVL", "symbol": "Ls", "name": "Latvian lats"},
    {"code": "LYD", "symbol": " ل.د ", "name": "Libyan dinar"},
    {"code": "MAD", "symbol": "DH", "name": "Moroccan dirham"},
    {"code": "MDL", "symbol": "L", "name": "Moldovan leu"},
    {"code": "MGA", "symbol": "Ar", "name": "Malagasy ariary"},
    {"code": "MKD", "symbol": "ден", "name": "Macedonian denar"},
    {"code": "MMK", "symbol": "K", "name": "Myanmar kyat"},
    {"code": "MNT", "symbol": "₮", "name": "Mongolian tögrög"},
    {"code": "MOP", "symbol": "MOP$", "name": "Macanese pataca"},
    {"code": "MRO", "symbol": "UM", "name": "Mauritanian ouguiya (old)"},
    {"code": "MRU", "symbol": "UM", "name": "Mauritanian ouguiya"},
    {"code": "MUR", "symbol": "Rs", "name": "Mauritian rupee"},
    {"code": "MVR", "symbol": "Rf", "name": "Maldivian rufiyaa"},
    {"code": "MWK", "symbol": "MK", "name": "Malawian kwacha"},
    {"code": "MXN", "symbol": "$", "name": "Mexican peso"},
    {"code": "MYR", "symbol": "RM", "name": "Malaysian ringgit"},
    {"code": "MZN", "symbol": "MT", "name": "Mozambican metical"},
    {"code": "NAD", "symbol": "$", "name": "Namibian dollar"},
    {"code": "NGN", "symbol": "₦", "name": "Nigerian naira"},
    {"code": "NIO", "symbol": "C$", "name": "Nicaraguan córdoba"},
    {"code": "NOK", "symbol": "kr", "name": "Norwegian krone"},
    {"code": "NPR", "symbol": "₨", "name": "Nepalese rupee"},
    {"code": "NZD", "symbol": "$", "name": "New Zealand dollar"},
    {"code": "OMR", "symbol": "ر.ع.", "name": "Omani rial"},
    {"code": "PAB", "symbol": "B/.", "name": "Panamanian balboa"},
    {"code": "PEN", "symbol": "S/", "name": "Peruvian sol"},
    {"code": "PGK", "symbol": "K", "name": "Papua New Guinean kina"},
    {"code": "PHP", "symbol": "₱", "name": "Philippine peso"},
    {"code": "PKR", "symbol": "Rs.", "name": "Pakistani rupee"},
    {"code": "PLN", "symbol": "zł", "name": "Polish złoty"},
    {"code": "PYG", "symbol": "₲", "name": "Paraguayan guaraní"},
    {"code": "QAR", "symbol": "QR", "name": "Qatari riyal"},
    {"code": "RON", "symbol": "lei", "name": "Romanian leu"},
    {"code": "RSD", "symbol": "din.", "name": "Serbian dinar"},
    {"code": "RUB", "symbol": "руб", "name": "Russian ruble"},
    {"code": "RWF", "symbol": "RF", "name": "Rwandan franc"},
    {"code": "SAR", "symbol": "SR", "name": "Saudi riyal"},
    {"code": "SBD", "symbol": "SI$", "name": "Solomon Islands dollar"},
    {"code": "SCR", "symbol": "SR", "name": "Seychellois rupee"},
    {"code": "SDG", "symbol": "ج.س.", "name": "Sudanese pound"},
    {"code": "SEK", "symbol": "kr", "name": "Swedish krona"},
    {"code": "SGD", "symbol": "S$", "name": "Singapore dollar"},
    {"code": "SHP", "symbol": "£", "name": "Saint Helena pound"},
    {"code": "SLE", "symbol": "Le", "name": "Sierra Leonean leone"},
    {"code": "SLL", "symbol": "Le", "name": "Sierra Leonean leone"},
    {"code": "SOS", "symbol": "Sh.", "name": "Somali shilling"},
    {"code": "SRD", "symbol": "$", "name": "Surinamese dollar"},
    {"code": "SSP", "symbol": "£", "name": "South Sudanese pound"},
    {"code": "STD", "symbol": "Db", "name": "São Tomé and Príncipe dobra"},
    {"code": "STN", "symbol": "Db", "name": "São Tomé and Príncipe dobra"},
    {"code": "SVC", "symbol": "¢", "name": "Salvadoran Colon"},
    {"code": "SYP", "symbol": "£", "name": "Syrian pound"},
    {"code": "SZL", "symbol": "E", "name": "Swazi lilangeni"},
    {"code": "THB", "symbol": "฿", "name": "Thai baht"},
    {"code": "TJS", "symbol": "TJS", "name": "Tajikistani somoni"},
    {"code": "TMT", "symbol": "T", "name": "Turkmenistan manat"},
    {"code": "TND", "symbol": "DT", "name": "Tunisian dinar"},
    {"code": "TOP", "symbol": "T$", "name": "Tongan paʻanga"},
    {"code": "TRY", "symbol": "₺", "name": "Turkish lira"},
    {"code": "TTD", "symbol": "$", "name": "Trinidad and Tobago dollar"},
    {"code": "TWD", "symbol": "NT$", "name": "New Taiwan dollar"},
    {"code": "TZS", "symbol": "TSh", "name": "Tanzanian shilling"},
    {"code": "UAH", "symbol": "₴", "name": "Ukraine Hryvnia"},
    {"code": "UGX", "symbol": "USh", "name": "Ugandan shilling"},
    {"code": "USD", "symbol": "$", "name": "United States dollar"},
    {"code": "UYI", "symbol": "$", "name": "Uruguay Peso en Unidades Indexadas"},
    {"code": "UYU", "symbol": "$", "name": "Uruguayan peso"},
    {"code": "UYW", "symbol": "$", "name": "Unidad previsional"},
    {"code": "UZS", "symbol": "лв", "name": "Uzbekistan som"},
    {"code": "VEF", "symbol": "Bs.F", "name": "Venezuelan bolívar fuerte"},
    {"code": "VES", "symbol": "Bs", "name": "Venezuelan bolívar soberano"},
    {"code": "VND", "symbol": "₫", "name": "Vietnamese đồng"},
    {"code": "VUV", "symbol": "VT", "name": "Vanuatu vatu"},
    {"code": "WST", "symbol": "WS$", "name": "Samoan tālā"},
    {"code": "XAF", "symbol": "FCFA", "name": "CFA franc BEAC"},
    {"code": "XCD", "symbol": "$", "name": "East Caribbean dollar"},
    {"code": "XOF", "symbol": "CFA", "name": "CFA franc BCEAO"},
    {"code": "XPF", "symbol": "XPF", "name": "CFP franc"},
    {"code": "YER", "symbol": "﷼", "name": "Yemeni rial"},
    {"code": "ZAR", "symbol": "R", "name": "South African rand"},
    {"code": "ZIG", "symbol": "ZiG", "name": "Zimbabwe Gold"},
    {"code": "ZMW", "symbol": "ZK", "name": "Zambian kwacha"},
]

# Archivo de control para evitar reimportaciones
CONTROL_FILE = "scripts/.currencies_imported"
MIN_CURRENCIES_THRESHOLD = 50  # Si hay menos de 50 monedas, reimportar


async def check_map_currency_setting() -> bool:
    """
    Verificar si la variable MAP_CURRENCY está habilitada
    """
    map_currency = os.getenv("MAP_CURRENCY", "false").lower()
    return map_currency in ("true", "1", "yes", "on")


async def check_control_file() -> bool:
    """
    Verificar si existe el archivo de control que indica importación previa
    """
    return os.path.exists(CONTROL_FILE)


async def count_existing_currencies(db) -> int:
    """
    Contar cuántas monedas ya existen en la base de datos
    """
    result = await db.scalar(select(func.count(Currency.id)))
    return result if result is not None else 0


async def should_import_currencies(db, force: bool = False) -> Tuple[bool, str]:
    """
    Determinar si se debe ejecutar la importación de monedas
    """
    # Si se fuerza, siempre importar
    if force:
        return True, "Importación forzada por parámetro"
    
    # Verificar variable de entorno
    if not await check_map_currency_setting():
        return False, "MAP_CURRENCY no está habilitado en variables de entorno"
    
    # Verificar archivo de control
    if await check_control_file():
        # Verificar también que haya suficientes monedas en BD
        currency_count = await count_existing_currencies(db)
        if currency_count >= MIN_CURRENCIES_THRESHOLD:
            return False, f"Ya importado anteriormente ({currency_count} monedas en BD)"
        else:
            logger.warning(f"Archivo de control existe pero solo hay {currency_count} monedas. Reimportando...")
    
    # Verificar si ya hay muchas monedas importadas
    currency_count = await count_existing_currencies(db)
    if currency_count >= MIN_CURRENCIES_THRESHOLD:
        return False, f"Ya existen {currency_count} monedas en la base de datos"
    
    return True, f"Proceder con importación (solo {currency_count} monedas actuales)"


async def create_control_file():
    """
    Crear archivo de control para indicar que la importación se completó
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(CONTROL_FILE), exist_ok=True)
        
        with open(CONTROL_FILE, 'w', encoding='utf-8') as f:
            f.write(f"Currencies imported on: {datetime.now().isoformat()}\n")
            f.write(f"Total currencies: {len(WORLD_CURRENCIES)}\n")
            f.write(f"Script: import_world_currencies.py\n")
        
        logger.info(f"Archivo de control creado: {CONTROL_FILE}")
    except Exception as e:
        logger.warning(f"No se pudo crear archivo de control: {str(e)}")


async def get_base_currency_code() -> str:
    """
    Obtener el código de la moneda base del sistema
    """
    settings = get_settings()
    return getattr(settings, 'DEFAULT_BASE_CURRENCY', 'USD')


async def currency_exists(db, currency_code: str) -> bool:
    """
    Verificar si una moneda ya existe en la base de datos
    """
    result = await db.execute(
        select(Currency).where(Currency.code == currency_code.upper())
    )
    return result.scalar_one_or_none() is not None


async def create_currency_with_exchange_rate(
    db, 
    currency_data: Dict[str, Any], 
    base_currency_code: str,
    is_base_currency: bool = False
) -> Currency:
    """
    Crear una moneda y su exchange rate automático
    """
    # Crear la moneda (inactiva por defecto según nuestra nueva lógica)
    currency = Currency(
        id=uuid.uuid4(),
        code=currency_data["code"].upper(),
        name=currency_data["name"],
        symbol=currency_data["symbol"],
        decimal_places=2,  # Por defecto 2 decimales
        is_active=is_base_currency,  # Solo la moneda base estará activa
        country_code=None,  # No tenemos datos de país en esta importación
        notes=f"Importada automáticamente - {currency_data['name']}"
    )
    
    db.add(currency)
    await db.flush()  # Para obtener el ID generado
    
    # Crear exchange rate automático (excepto para la moneda base)
    if not is_base_currency:
        exchange_rate = ExchangeRate(
            id=uuid.uuid4(),
            currency_id=currency.id,
            rate=Decimal('1.0'),
            rate_date=date.today(),
            source="system",
            provider="auto_import",
            notes=f"Tipo de cambio inicial para {currency.code} importado automáticamente"
        )
        db.add(exchange_rate)
    
    return currency


async def import_world_currencies(force: bool = False):
    """
    Importar todas las monedas mundiales
    
    Args:
        force: Si es True, fuerza la importación ignorando controles
    """
    logger.info("🌍 Iniciando verificación de importación de monedas...")
    
    async for db in get_async_db():
        try:
            # Verificar si se debe ejecutar la importación
            should_import, reason = await should_import_currencies(db, force)
            
            if not should_import:
                logger.info(f"⏭️  Saltando importación de monedas: {reason}")
                return
            
            logger.info(f"✅ Procediendo con importación: {reason}")
            
            base_currency_code = await get_base_currency_code()
            logger.info(f"💰 Moneda base del sistema: {base_currency_code}")
            
            created_count = 0
            skipped_count = 0
            updated_count = 0
            
            for currency_data in WORLD_CURRENCIES:
                currency_code = currency_data["code"].upper()
                
                # Verificar si ya existe
                if await currency_exists(db, currency_code):
                    if force:
                        logger.info(f"🔄 Moneda {currency_code} existe, actualizando por modo forzado...")
                        # En modo forzado, se podría actualizar, pero por ahora solo saltamos
                        updated_count += 1
                    else:
                        logger.debug(f"⚠️  Moneda {currency_code} ya existe, omitiendo...")
                        skipped_count += 1
                    continue
                
                # Determinar si es la moneda base
                is_base_currency = currency_code == base_currency_code.upper()
                
                # Crear la moneda con su exchange rate
                currency = await create_currency_with_exchange_rate(
                    db, 
                    currency_data, 
                    base_currency_code,
                    is_base_currency
                )
                
                created_count += 1
                status = "🟢 ACTIVA (moneda base)" if is_base_currency else "🔵 inactiva"
                logger.info(f"➕ Moneda creada: {currency.code} - {currency.name} [{status}]")
            
            await db.commit()
            
            # Crear archivo de control solo si se crearon monedas
            if created_count > 0:
                await create_control_file()
            
            # Calcular exchange rates creados (todas menos la base si fue creada)
            exchange_rates_created = created_count
            if created_count > 0:
                # Verificar si la moneda base fue creada en esta ejecución
                for currency_data in WORLD_CURRENCIES:
                    if currency_data['code'].upper() == base_currency_code.upper():
                        if not await currency_exists(db, currency_data['code'].upper()):
                            exchange_rates_created -= 1  # No se crea exchange rate para la base
                        break
            
            logger.info(f"""
            ═══════════════════════════════════════════════════════════
            🎉 IMPORTACIÓN DE MONEDAS COMPLETADA
            ═══════════════════════════════════════════════════════════
            ✅ Monedas creadas: {created_count}
            ⚠️  Monedas omitidas (ya existían): {skipped_count}
            🔄 Monedas actualizadas: {updated_count}
            💰 Moneda base: {base_currency_code} (activa)
            🔵 Otras monedas: inactivas (puede activarlas el usuario)
            📊 Exchange rates creados: {exchange_rates_created}
            🗂️  Archivo de control: {CONTROL_FILE}
            ═══════════════════════════════════════════════════════════
            """)
            
        except Exception as e:
            logger.error(f"❌ Error importando monedas: {str(e)}")
            await db.rollback()
            raise
        finally:
            await db.close()


# Función auxiliar para llamadas externas
async def run_currency_import(force: bool = False):
    """
    Función wrapper para llamar desde otros módulos
    """
    await import_world_currencies(force)


if __name__ == "__main__":
    import sys
    
    # Verificar si se pasa el argumento --force
    force = "--force" in sys.argv
    
    if force:
        logger.info("🔥 Modo forzado activado - ignorando controles")
    
    asyncio.run(import_world_currencies(force))
