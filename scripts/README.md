# Scripts de Importación de Datos

Este directorio contiene scripts para importar datos iniciales en la base de datos del sistema contable.

## Estructura

```
scripts/
├── __init__.py
├── run_import_scripts.py          # Script principal de gestión
├── data_import/
│   ├── __init__.py
│   ├── import_currencies.py       # Importación de monedas mundiales
│   └── [futuros scripts]
└── README.md                      # Este archivo
```

## Scripts Disponibles

### 1. Importación de Monedas (`import_currencies.py`)

Importa todas las monedas del mundo con sus códigos ISO, símbolos y nombres.

**Características:**
- Solo se ejecuta la primera vez que inicia el servidor
- Se controla con la variable de entorno `MAP_CURRENCY=true`
- Crea automáticamente exchange rates con valor 1.0 para cada moneda
- Las monedas se crean inactivas por defecto
- Usa un archivo de control para evitar reimportaciones

**Configuración en .env:**
```bash
MAP_CURRENCY=true  # Habilitar importación automática
DEFAULT_BASE_CURRENCY=USD  # Moneda base del sistema
```

## Uso Manual

### Ejecutar script de gestión

```bash
# Importar solo monedas
python scripts/run_import_scripts.py currencies

# Forzar reimportación de monedas (ignorar archivo de control)
python scripts/run_import_scripts.py currencies --force

# Ejecutar todos los scripts disponibles
python scripts/run_import_scripts.py all
```

### Ejecutar script individual

```bash
# Ejecutar directamente el script de monedas
python scripts/data_import/import_currencies.py
```

## Archivos de Control

Los scripts crean archivos de control para evitar ejecuciones duplicadas:

- `scripts/.currencies_imported` - Indica que las monedas ya fueron importadas

Para forzar una reimportación, elimine el archivo de control correspondiente o use la opción `--force`.

## Ejecución Automática

Los scripts se ejecutan automáticamente al iniciar el servidor si:

1. La variable de entorno correspondiente está habilitada
2. No existe el archivo de control
3. La condición específica del script se cumple (ej: menos de 50 monedas en BD)

## Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `MAP_CURRENCY` | Habilitar importación de monedas | `false` |
| `DEFAULT_BASE_CURRENCY` | Moneda base del sistema | `USD` |

## Agregar Nuevos Scripts

Para agregar un nuevo script de importación:

1. Crear el archivo en `scripts/data_import/`
2. Implementar la función principal de importación
3. Agregar lógica de control para evitar duplicados
4. Actualizar `run_import_scripts.py` para incluir el nuevo script
5. Actualizar la documentación

### Plantilla para Nuevos Scripts

```python
#!/usr/bin/env python3
"""
Script para importar [DESCRIPCIÓN]
"""
import asyncio
import os
from datetime import datetime

from app.database import get_async_db
from app.utils.logging import get_logger

logger = get_logger(__name__)

async def should_import_data():
    """Verificar si se debe ejecutar la importación"""
    # Verificar variable de entorno
    enabled = os.getenv('MAP_[NOMBRE]', 'false').lower() == 'true'
    if not enabled:
        return False, "Importación deshabilitada"
    
    # Verificar archivo de control
    control_file = "scripts/.[nombre]_imported"
    if os.path.exists(control_file):
        return False, "Ya fue importado anteriormente"
    
    # Verificar condiciones específicas en BD
    # ...
    
    return True, "Proceder con importación"

async def import_data():
    """Función principal de importación"""
    should_import, reason = await should_import_data()
    if not should_import:
        logger.info(f"Saltando importación: {reason}")
        return
    
    # Lógica de importación
    # ...
    
    # Crear archivo de control
    control_file = "scripts/.[nombre]_imported"
    os.makedirs(os.path.dirname(control_file), exist_ok=True)
    with open(control_file, 'w') as f:
        f.write(f"Imported on {datetime.now().isoformat()}\n")

if __name__ == "__main__":
    asyncio.run(import_data())
```

## Logs

Los scripts generan logs detallados sobre el proceso de importación. Los logs incluyen:

- Cantidad de registros procesados
- Errores encontrados
- Tiempo de ejecución
- Estado final de la importación
