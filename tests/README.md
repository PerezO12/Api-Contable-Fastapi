# Tests de Integración - API Contable

Esta carpeta contiene tests de integración completos para todos los endpoints de la API Contable.

## Estructura

```
tests/
├── __init__.py
├── conftest.py                    # Configuración global de pytest
├── test_helpers.py                # Utilities y helpers para tests
└── integration/
    ├── __init__.py
    ├── test_auth_endpoints.py      # Tests de autenticación
    ├── test_user_endpoints.py      # Tests de gestión de usuarios
    ├── test_account_endpoints.py   # Tests de cuentas contables
    ├── test_journal_entry_endpoints.py  # Tests de asientos contables
    └── test_report_endpoints.py    # Tests de reportes financieros
```

## Configuración

Los tests utilizan una base de datos SQLite en memoria para cada ejecución, garantizando aislamiento y velocidad.

### Fixtures Principales

- `client`: Cliente HTTP async para hacer requests a la API
- `db_session`: Sesión de base de datos limpia para cada test
- `admin_user`, `contador_user`, `readonly_user`: Usuarios de prueba con diferentes roles
- `auth_headers_*`: Headers de autenticación para cada tipo de usuario

## Ejecutar Tests

### Instalar dependencias de testing

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### Ejecutar todos los tests

```bash
pytest
```

### Ejecutar tests específicos

```bash
# Solo tests de autenticación
pytest tests/integration/test_auth_endpoints.py

# Solo tests de cuentas
pytest tests/integration/test_account_endpoints.py

# Solo tests marcados como "slow"
pytest -m "not slow"

# Tests con verbose output
pytest -v

# Tests con coverage
pytest --cov=app --cov-report=html
```

### Ejecutar tests por categoría

```bash
# Tests de integración
pytest -m integration

# Tests relacionados con autenticación
pytest -m auth

# Tests relacionados con reportes
pytest -m reports
```

## Cobertura de Tests

Los tests cubren:

### 🔐 Autenticación (`test_auth_endpoints.py`)
- ✅ Login con credenciales válidas/inválidas
- ✅ Refresh token
- ✅ Logout
- ✅ OAuth2 compatibility
- ✅ Endpoints protegidos
- ✅ Setup de administrador inicial

### 👥 Gestión de Usuarios (`test_user_endpoints.py`)
- ✅ Información de usuario actual
- ✅ Creación de usuarios por admin
- ✅ Estadísticas de usuarios
- ✅ Listado y filtrado de usuarios
- ✅ Activar/desactivar usuarios
- ✅ Reset de contraseñas
- ✅ Cambio de contraseñas
- ✅ Permisos por rol

### 💰 Cuentas Contables (`test_account_endpoints.py`)
- ✅ CRUD completo de cuentas
- ✅ Validaciones de datos
- ✅ Filtros y búsquedas
- ✅ Árbol de cuentas
- ✅ Estadísticas
- ✅ Saldos y movimientos
- ✅ Validación de cuentas
- ✅ Operaciones masivas
- ✅ Exportación
- ✅ Permisos por rol

### 📊 Asientos Contables (`test_journal_entry_endpoints.py`)
- ✅ Creación de asientos
- ✅ Validación de balance
- ✅ Estados del asiento (Draft, Approved, Posted, Cancelled)
- ✅ Listado con filtros y paginación
- ✅ CRUD completo
- ✅ Aprobación y contabilización
- ✅ Cancelación y reversión
- ✅ Búsqueda avanzada
- ✅ Creación masiva
- ✅ Estadísticas
- ✅ Permisos por rol

### 📈 Reportes Financieros (`test_report_endpoints.py`)
- ✅ Balance General
- ✅ Estado de Resultados
- ✅ Balance de Comprobación
- ✅ Libro Mayor
- ✅ Análisis Financiero
- ✅ Resúmenes por tipo de cuenta
- ✅ Verificación de integridad contable
- ✅ Exportación de reportes
- ✅ Validación de fechas
- ✅ Generación concurrente

## Datos de Prueba

Los tests utilizan datos de muestra consistentes:

### Usuarios de Prueba
- **Admin**: `admin@test.com` / `admin123`
- **Contador**: `contador@test.com` / `contador123`
- **Solo Lectura**: `readonly@test.com` / `readonly123`

### Plan de Cuentas de Prueba
- **Activos**: Caja (1001), Banco (1002), Equipos (1501)
- **Pasivos**: Proveedores (2001), Sueldos por Pagar (2002)
- **Patrimonio**: Capital (3001), Resultados Acumulados (3002)
- **Ingresos**: Ventas (4001), Servicios (4002)
- **Gastos**: Sueldos (5101), Alquiler (5201)

## Helpers y Utilities

### `TestHelpers`
- Creación automática de cuentas de prueba
- Creación automática de asientos contables balanceados
- Creación automática de usuarios
- Aprobación y contabilización automática de asientos
- Verificación de estructuras de respuesta
- Generación de rangos de fechas

### `TestDataFactory`
- Datos de muestra para plan de cuentas completo
- Usuarios de muestra con diferentes roles
- Escenarios de asientos contables típicos

## Mejores Prácticas

1. **Aislamiento**: Cada test es independiente y no afecta a otros
2. **Datos Limpios**: Se crean datos frescos para cada test
3. **Validaciones Completas**: Se verifican tanto códigos de estado como estructura de respuestas
4. **Cobertura de Permisos**: Se validan permisos para todos los roles
5. **Casos Edge**: Se incluyen tests para casos límite y errores
6. **Performance**: Se usan fixtures eficientes y operaciones en paralelo cuando es apropiado

## Troubleshooting

### Error: "Database is locked"
```bash
# Asegúrate de que no hay procesos usando la DB
pkill -f python
```

### Error: "Module not found"
```bash
# Ejecutar desde el directorio raíz del proyecto
cd "e:\trabajo\Aplicacion\API Contable"
pytest
```

### Tests muy lentos
```bash
# Ejecutar solo tests rápidos
pytest -m "not slow"
```

### Ver output detallado
```bash
# Para debugging
pytest -v -s
```

## Configuración de Coverage

El coverage está configurado para:
- **Mínimo**: 70% de cobertura
- **Excluir**: Tests, migraciones, cache
- **Formatos**: Terminal y HTML
- **Reportes**: `htmlcov/index.html`

## CI/CD Integration

Estos tests están diseñados para ejecutarse en pipelines de CI/CD:

```yaml
# Ejemplo GitHub Actions
- name: Run Integration Tests
  run: |
    pytest tests/integration/ -v --cov=app --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

## Extensión

Para agregar nuevos tests:

1. Crear archivo `test_nuevo_endpoint.py` en `tests/integration/`
2. Usar fixtures existentes de `conftest.py`
3. Importar helpers de `test_helpers.py`
4. Seguir nomenclatura `test_*` para funciones
5. Agregar markers apropiados con `@pytest.mark.*`
6. Documentar casos de prueba en docstrings
