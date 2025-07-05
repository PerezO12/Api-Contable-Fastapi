# API Contable - Sistema de Contabilidad(en desarrollo)

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![License](https://img.shields.io/badge/license-CC--BY--NC--ND--4.0-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-teal.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.41-red.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)

## 🌟 Descripción

API Contable es un sistema de contabilidad completo desarrollado con FastAPI y SQLAlchemy, diseñado para proporcionar una API robusta para la gestión de operaciones contables empresariales.

El sistema ofrece funcionalidades para:
- Gestión completa de usuarios y permisos con roles (ADMIN, CONTADOR, SOLO_LECTURA)
- Administración del plan de cuentas contables con estructura jerárquica
- Creación y gestión de asientos contables con validación de partida doble
- Generación de reportes financieros (Balance General, Estado de Resultados, etc.)
- Importación y exportación de datos en múltiples formatos (CSV, XLSX, JSON)
- Análisis financiero con indicadores clave de desempeño
- Sistema de productos con operaciones masivas y validación previa
- Gestión de centros de costo con análisis de rentabilidad
- Integración con NFe (Notas Fiscales Electrónicas)
- API unificada de reportes con formato consistente
- Términos de pago con cronogramas personalizables
- Operaciones asíncronas optimizadas con asyncpg
- Sistema completo de auditoría y trazabilidad

### Características Técnicas Destacadas

- **Arquitectura Asíncrona**: Implementación completa con FastAPI y asyncpg
- **Validación Automática**: Esquemas Pydantic para request/response
- **Operaciones Masivas**: Endpoints bulk con validación previa
- **API Unificada**: Formato consistente en todos los endpoints
- **Seguridad Robusta**: JWT con refresh tokens y RBAC
- **Documentación OpenAPI**: Swagger UI y ReDoc actualizados
- **Testing Completo**: Suite de pruebas con pytest
- **Migraciones Automáticas**: Sistema de migraciones con Alembic

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.11 o superior
- PostgreSQL 12 o superior  
- Node.js 18+ (para el frontend)
- Git (para clonar el repositorio)

### 🤖 Configuración con Servicios de IA (Recomendado)

Para usar las funcionalidades de chat con IA y traducción automática:

```bash
# 1. Verificación rápida del sistema
powershell -ExecutionPolicy Bypass -File quick_check.ps1

# 2. Configurar entorno virtual aislado
python setup_ai_environment.py

# 3. Activar entorno virtual
# PowerShell:
.\activate_ai_env.ps1
# CMD:
activate_ai_env.bat

# 4. Configurar token de Hugging Face en .env
# Editar HUGGINGFACE_API_TOKEN=tu_token_real

# 5. Verificar e iniciar
python start_ai_chat.py
```

### 📦 Instalación Tradicional

1. Clone este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/api-contable.git
   cd api-contable
   ```

2. Cree y active un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # Linux/Mac
   ```

3. Instale las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure su archivo `.env`:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=api_contable_dev2
   DB_USER=postgres
   DB_PASSWORD=123456
   SECRET_KEY=su_clave_secreta_aqui
   ENVIRONMENT=development
   DEBUG=True
   ```

5. Ejecute las migraciones de la base de datos:
   ```bash
   alembic upgrade head
   ```

6. Inicie el servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

## 📚 Documentación

La documentación completa está disponible en:

- 📖 [Documentación API (Swagger UI)](http://localhost:8000/docs)
- 📱 [Documentación Alternativa (ReDoc)](http://localhost:8000/redoc)
- 📂 [Documentación Técnica Completa](./documentation/README.md)

### Estructura de la Documentación

- [Sistema de Autenticación](./documentation/auth/README.md) - Autenticación JWT y gestión de usuarios
- [Sistema de Cuentas](./documentation/accounts/README.md) - Gestión del plan de cuentas contables
- [Asientos Contables](./documentation/journal-entries/README.md) - Gestión de asientos con validación de partida doble
- [Sistema de Productos](./documentation/products/README.md) - Gestión completa de productos e inventario
- [Terceros](./documentation/third-parties/README.md) - Clientes, proveedores y empleados
- [Centros de Costo](./documentation/cost-centers/README.md) - Gestión de centros de costo y análisis de rentabilidad
- [Reportes Financieros](./documentation/reports/README.md) - Reportes clásicos y API unificada
- [Importación y Exportación](./documentation/data-import/README.md) - Sistema profesional de importación/exportación

## 🌐 Endpoints Principales

### Autenticación y Usuarios
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/refresh` - Renovar token
- `POST /api/v1/auth/logout` - Cerrar sesión
- `GET /api/v1/users/me` - Información del usuario actual
- `GET /api/v1/users/roles` - Obtener roles disponibles
- `POST /api/v1/users/` - Crear usuario
- `GET /api/v1/users/` - Listar usuarios
- `PUT /api/v1/users/{user_id}` - Actualizar usuario

### Cuentas Contables
- `GET /api/v1/accounts/` - Listar cuentas con filtros
- `POST /api/v1/accounts/` - Crear cuenta
- `GET /api/v1/accounts/tree` - Ver árbol jerárquico
- `PUT /api/v1/accounts/{account_id}` - Actualizar cuenta
- `POST /api/v1/accounts/bulk-operation` - Operaciones masivas
- `POST /api/v1/accounts/bulk-delete` - Eliminación masiva
- `POST /api/v1/accounts/validate-deletion` - Validación previa

### Asientos Contables
- `GET /api/v1/journal-entries/` - Listar asientos
- `POST /api/v1/journal-entries/` - Crear asiento
- `GET /api/v1/journal-entries/{entry_id}` - Obtener asiento específico
- `POST /api/v1/journal-entries/{entry_id}/approve` - Aprobar asiento
- `POST /api/v1/journal-entries/bulk` - Operaciones masivas
- `POST /api/v1/journal-entries/validate` - Validar asiento

### Productos
- `GET /api/v1/products/` - Listar productos con filtros
- `GET /api/v1/products/search` - Búsqueda avanzada
- `POST /api/v1/products/` - Crear producto
- `POST /api/v1/products/bulk-operation` - Operaciones masivas
- `POST /api/v1/products/bulk-delete` - Eliminación masiva
- `POST /api/v1/products/validate-deletion` - Validación previa

### Facturas
- `GET /api/v1/invoices/` - Listar facturas con filtros
- `POST /api/v1/invoices/` - Crear factura
- `GET /api/v1/invoices/{id}` - Obtener factura
- `POST /api/v1/invoices/bulk-post` - Contabilización masiva
- `POST /api/v1/invoices/bulk-cancel` - Cancelación masiva
- `GET /api/v1/invoices/types/` - Tipos de factura

### Términos de Pago
- `GET /api/v1/payment-terms/` - Listar términos
- `POST /api/v1/payment-terms/` - Crear término
- `GET /api/v1/payment-terms/{id}` - Obtener término
- `PUT /api/v1/payment-terms/{id}` - Actualizar término

### Reportes Financieros
- `GET /api/v1/reports/balance-general` - Balance general
- `GET /api/v1/reports/estado-resultados` - Estado de resultados
- `GET /api/v1/reports/flujo-efectivo` - Flujo de efectivo
- `GET /api/v1/reports/balance-comprobacion` - Balance de comprobación
- `GET /api/v1/reports/accounts-summary/{type}` - Resumen de cuentas
- `GET /api/v1/reports/accounting-integrity` - Verificar integridad
- `GET /api/v1/reports/tipos` - Listar tipos de reportes

### Importación y Exportación
- `GET /api/v1/templates/` - Listar plantillas disponibles
- `GET /api/v1/templates/{type}/{format}` - Descargar plantilla
- `POST /api/v1/export/` - Exportación simple
- `POST /api/v1/export/advanced` - Exportación avanzada
- `POST /api/v1/export/bulk` - Exportación masiva

### Terceros
- `GET /api/v1/third-parties/` - Listar terceros
- `POST /api/v1/third-parties/` - Crear tercero
- `GET /api/v1/third-parties/{id}` - Obtener tercero
- `PUT /api/v1/third-parties/{id}` - Actualizar tercero
- `GET /api/v1/third-parties/bulk-operations/{id}/status` - Estado de operación masiva

## ⚙️ Arquitectura

El proyecto sigue una arquitectura en capas:

- **API (Controllers)**: Gestión de HTTP y endpoints REST
- **Servicios**: Lógica de negocio y reglas contables
- **Modelos**: Estructura de datos y relaciones
- **Repositorios**: Acceso y persistencia de datos

### Principios Contables Implementados

- Ecuación Fundamental: `Activos = Pasivos + Patrimonio`
- Balance de Comprobación: `Σ Débitos = Σ Créditos`
- Estado de Resultados: `Utilidad Neta = Ingresos - Gastos`
- Flujo de Efectivo: `Flujo Neto = Operativo + Inversión + Financiamiento`

### Características de Base de Datos

- **Pool de Conexiones**: Configurado para óptimo rendimiento
- **Migraciones**: Sistema robusto con Alembic
- **Transacciones**: Soporte completo ACID
- **Índices**: Optimizados para consultas frecuentes
- **Triggers**: Para auditoría y validaciones automáticas

## 🔒 Seguridad

- Autenticación JWT con tokens de acceso y refresh
- Permisos basados en roles (RBAC)
- Encriptación de contraseñas con bcrypt
- Validación exhaustiva de datos
- CORS configurado para desarrollo y producción
- Rate limiting para prevención de abusos(desactivado para desarrollo)
- Validación de sesiones activas

## 🧪 Testing

Para ejecutar las pruebas:

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas con cobertura
pytest --cov=app

# Ejecutar pruebas específicas
pytest tests/api/test_auth.py
```

## 📦 Tecnologías Principales

- **FastAPI 0.115.12**: Framework web rápido con validación automática
- **SQLAlchemy 2.0.41**: ORM con soporte para async/await
- **Pydantic 2.11.5**: Validación de datos y generación de esquemas
- **PostgreSQL 12+**: Base de datos relacional
- **Alembic**: Migraciones de base de datos
- **JWT**: Autenticación mediante tokens
- **asyncpg 0.30.0**: Driver asíncrono para PostgreSQL
- **pytest 8.4.0**: Framework de testing
- **uvicorn 0.34.2**: Servidor ASGI de alto rendimiento
- **python-jose 3.4.0**: Implementación de JWT
- **bcrypt 4.3.0**: Hashing de contraseñas
- **python-multipart 0.0.20**: Manejo de formularios
- **rich 14.0.0**: Formateo de consola mejorado

## 📋 Licencia

Este proyecto está bajo la Licencia Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC-BY-NC-ND-4.0). 

Esta licencia permite que otros descarguen y compartan el trabajo siempre que den crédito, pero no permite su uso comercial ni la creación de trabajos derivados.

### Términos principales:
- **Atribución** — Debe dar crédito adecuado y proporcionar un enlace a la licencia
- **NoComercial** — No puede utilizar el material con fines comerciales
- **NoDerivadas** — No puede distribuir el material modificado
- **Sin restricciones adicionales** — No puede aplicar términos legales adicionales

Para más detalles, consulte el archivo [LICENSE.md](./LICENSE.md) o visite:
https://creativecommons.org/licenses/by-nc-nd/4.0/

## 📞 Soporte

Para preguntas o soporte técnico:
- Abra un issue en el repositorio
- Contacte al equipo de desarrollo

---

⭐ **API Contable - Simplificando la Contabilidad Empresarial** ⭐