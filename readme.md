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
- 📂 [Documentación Técnica](./documentation/README.md)

### Estructura de la Documentación

- [Sistema de Autenticación](./documentation/auth/README.md) - Autenticación y gestión de usuarios
- [Sistema de Cuentas](./documentation/accounts/README.md) - Gestión del plan de cuentas
- [Asientos Contables](./documentation/journal-entries/README.md) - Gestión de asientos contables
- [Importación y Exportación de Datos](./documentation/data-import/README.md) - Sistema de importación/exportación
  - [Plantillas de Exportación](./documentation/data-import/export-templates.md) - Exportación de plantillas y ejemplos

## 🌐 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/refresh` - Renovar token
- `POST /api/v1/auth/logout` - Cerrar sesión

### Usuarios
- `GET /api/v1/users/me` - Información del usuario actual
- `POST /api/v1/users/admin/create-user` - Crear usuario (Admin)
- `GET /api/v1/users/admin/list` - Listar usuarios (Admin)

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