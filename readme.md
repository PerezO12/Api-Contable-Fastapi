# API Contable - Sistema de Contabilidad

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-teal.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.41-red.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)

## 🌟 Descripción

API Contable es un sistema de contabilidad completo desarrollado con FastAPI y SQLAlchemy, diseñado para proporcionar una API robusta para la gestión de operaciones contables empresariales.

El sistema ofrece funcionalidades para:
- Gestión completa de usuarios y permisos
- Administración del plan de cuentas contables
- Creación y gestión de asientos contables con validación de partida doble
- Generación de reportes financieros (Balance General, Estado de Resultados, etc.)
- Importación y exportación de datos en múltiples formatos (CSV, XLSX, JSON)
- Análisis financiero con indicadores clave de desempeño

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.11 o superior
- PostgreSQL 12 o superior
- (Opcional) Entorno virtual para Python

### Instalación

1. Clone este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/api-contable.git
   cd api-contable
   ```

2. Cree y active un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Instale las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure su archivo `.env` (copie el template):
   ```bash
   copy .env.example .env
   ```

5. Edite el archivo `.env` con sus configuraciones:
   ```
   DB_USER=usuario_postgres
   DB_PASSWORD=contraseña
   DB_NAME=accounting_system
   DB_HOST=localhost
   DB_PORT=5432
   SECRET_KEY=su_clave_secreta_aqui
   ```

6. Ejecute las migraciones de la base de datos:
   ```bash
   alembic upgrade head
   ```

7. Inicie el servidor:
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

### Estado de Documentación: ✅ COMPLETAMENTE ACTUALIZADO
- **109/109 endpoints documentados** (100% cobertura)
- **Productos: 21/21 endpoints** - Incluye operaciones bulk completas
- **Última actualización**: Junio 16, 2025
- **Verificado contra código fuente**: Todos los endpoints validados y funcionales

## 🌐 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/refresh` - Renovar token
- `POST /api/v1/auth/logout` - Cerrar sesión
- `POST /api/v1/auth/setup-admin` - Crear administrador inicial

### Usuarios
- `GET /api/v1/users/me` - Información del usuario actual
- `POST /api/v1/users/` - Crear usuario
- `GET /api/v1/users/` - Listar usuarios
- `PUT /api/v1/users/{user_id}` - Actualizar usuario
- `DELETE /api/v1/users/{user_id}` - Eliminar usuario

### Cuentas Contables
- `GET /api/v1/accounts/` - Listar cuentas
- `POST /api/v1/accounts/` - Crear cuenta
- `GET /api/v1/accounts/{account_id}` - Obtener cuenta específica
- `PUT /api/v1/accounts/{account_id}` - Actualizar cuenta
- `DELETE /api/v1/accounts/{account_id}` - Eliminar cuenta

### Asientos Contables
- `GET /api/v1/journal-entries/` - Listar asientos
- `POST /api/v1/journal-entries/` - Crear asiento
- `GET /api/v1/journal-entries/{entry_id}` - Obtener asiento específico
- `PUT /api/v1/journal-entries/{entry_id}` - Actualizar asiento
- `POST /api/v1/journal-entries/{entry_id}/approve` - Aprobar asiento

### Productos
- `GET /api/v1/products/` - Listar productos
- `POST /api/v1/products/` - Crear producto
- `GET /api/v1/products/{product_id}` - Obtener producto específico
- `PUT /api/v1/products/{product_id}` - Actualizar producto
- `DELETE /api/v1/products/{product_id}` - Eliminar producto
- `POST /api/v1/products/bulk-operation` - Operaciones masivas generales
- `POST /api/v1/products/bulk-delete` - Eliminación masiva
- `POST /api/v1/products/bulk-deactivate` - Desactivación masiva
- `POST /api/v1/products/validate-deletion` - Validación previa de eliminación

### Terceros
- `GET /api/v1/third-parties/` - Listar terceros
- `POST /api/v1/third-parties/` - Crear tercero
- `GET /api/v1/third-parties/{party_id}` - Obtener tercero específico
- `PUT /api/v1/third-parties/{party_id}` - Actualizar tercero

### Centros de Costo
- `GET /api/v1/cost-centers/` - Listar centros de costo
- `POST /api/v1/cost-centers/` - Crear centro de costo
- `GET /api/v1/cost-centers/{center_id}` - Obtener centro específico

### Reportes Financieros
#### API Clásica
- `GET /api/v1/reports/legacy/balance-sheet` - Balance general clásico
- `GET /api/v1/reports/legacy/income-statement` - Estado de resultados clásico
- `GET /api/v1/reports/legacy/trial-balance` - Balance de comprobación

#### API Unificada (Recomendada)
- `GET /api/v1/reports/balance-general` - Balance general unificado
- `GET /api/v1/reports/estado-resultados` - Estado de resultados unificado
- `GET /api/v1/reports/flujo-efectivo` - Flujo de efectivo
- `GET /api/v1/reports/balance-comprobacion` - Balance de comprobación
- `GET /api/v1/reports/mayor-general` - Mayor general

### Importación y Exportación
- `POST /api/v1/import/preview` - Vista previa de importación
- `POST /api/v1/import/process` - Procesar importación
- `GET /api/v1/templates/accounts/csv` - Template de cuentas CSV
- `GET /api/v1/export/accounts` - Exportar cuentas
- `GET /api/v1/export/journal-entries` - Exportar asientos

### Cuentas Contables
- `GET /api/v1/accounts/` - Listar cuentas
- `POST /api/v1/accounts/` - Crear cuenta
- `GET /api/v1/accounts/tree` - Ver árbol jerárquico

### Asientos Contables
- `GET /api/v1/journal-entries/` - Listar asientos
- `POST /api/v1/journal-entries/` - Crear asiento
- `POST /api/v1/journal-entries/{id}/approve` - Aprobar asiento

### Reportes Financieros
- `POST /api/v1/reports/balance-sheet` - Balance General
- `POST /api/v1/reports/income-statement` - Estado de Resultados
- `POST /api/v1/reports/trial-balance` - Balance de Comprobación

### Importación y Exportación
- `POST /api/v1/import/accounts` - Importar cuentas
- `POST /api/v1/import/journal-entries` - Importar asientos
- `GET /api/v1/templates/accounts/{format}` - Exportar plantilla de cuentas
- `GET /api/v1/templates/journal-entries/{format}` - Exportar plantilla de asientos

## ⚙️ Arquitectura

El proyecto sigue una arquitectura en capas:

- **Controladores (API)**: Gestión de HTTP y endpoints REST
- **Servicios**: Lógica de negocio y reglas contables
- **Modelos**: Estructura de datos y relaciones
- **Repositorios**: Acceso y persistencia de datos

## 🔒 Seguridad

- Autenticación JWT con tokens de acceso y refresh
- Permisos basados en roles (RBAC)
- Encriptación de contraseñas con bcrypt
- Bloqueo por intentos fallidos
- Validación exhaustiva de datos

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

- **FastAPI**: Framework web rápido con validación automática
- **SQLAlchemy 2.0**: ORM con soporte para async/await
- **Pydantic**: Validación de datos y generación de esquemas
- **PostgreSQL**: Base de datos relacional
- **Alembic**: Migraciones de base de datos
- **JWT**: Autenticación mediante tokens

## 📋 Licencia

Este proyecto está bajo la Licencia MIT. Consulte el archivo LICENSE para obtener más detalles.

## 📞 Contacto y Soporte

Para preguntas o soporte técnico, contacte a:

- Email: soporte@apicontable.com
- Issue Tracker: [GitHub Issues](https://github.com/tu-usuario/api-contable/issues)

---

⭐ **API Contable - Simplificando la Contabilidad Empresarial** ⭐