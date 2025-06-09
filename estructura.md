Sistema Contable - Estructura del Proyecto
Estructura de Carpetas
accounting_system/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Punto de entrada de FastAPI
│   ├── config.py                  # Configuración de la aplicación
│   ├── database.py                # Configuración de SQLAlchemy
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py               # Modelo de usuarios
│   │   ├── account.py            # Modelo de cuentas contables
│   │   ├── journal_entry.py      # Modelo de asientos contables
│   │   └── base.py               # Clase base para modelos
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py               # Pydantic schemas para usuarios
│   │   ├── account.py            # Pydantic schemas para cuentas
│   │   └── journal_entry.py      # Pydantic schemas para asientos
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py               # Dependencias comunes (auth, db)
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Endpoints de autenticación
│   │   │   ├── users.py         # CRUD de usuarios
│   │   │   ├── accounts.py      # CRUD de cuentas
│   │   │   ├── entries.py       # CRUD de asientos contables
│   │   │   └── reports.py       # Endpoints de reportes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py       # Lógica de autenticación
│   │   ├── account_service.py    # Lógica de negocio cuentas
│   │   ├── entry_service.py      # Lógica de asientos contables
│   │   └── report_service.py     # Generación de reportes
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── security.py           # Hash passwords, JWT
│   │   ├── validators.py         # Validaciones personalizadas
│   │   └── exceptions.py         # Excepciones personalizadas
│   └── static/                   # Archivos estáticos (si los hay)
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Configuración de pytest
│   ├── test_auth.py
│   ├── test_accounts.py
│   └── test_entries.py
├── migrations/                   # Migraciones de Alembic
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml           # Para desarrollo con PostgreSQL
Plan del Proyecto por Sprints
Sprint 1: Fundamentos del Sistema (Semanas 1-2)
Objetivo: Establecer la base del sistema con usuarios, autenticación y estructura básica de cuentas.
Entregables:

Configuración inicial del proyecto con FastAPI, SQLAlchemy y PostgreSQL
Sistema de usuarios con roles (Admin, Contador, Solo Lectura)
Autenticación JWT completa con login/logout
CRUD básico de cuentas contables con jerarquía padre-hijo
Validación de que solo cuentas hoja puedan recibir movimientos

Criterios de Aceptación:

Un administrador puede crear usuarios y asignar roles
Los usuarios pueden autenticarse y mantener sesión
Se pueden crear cuentas con estructura jerárquica
Las cuentas padre no permiten movimientos directos

Sprint 2: Asientos Contables y Validaciones (Semanas 3-4)
Objetivo: Implementar el core contable con asientos de doble partida y validaciones.
Entregables:

Modelo completo de asientos contables (encabezado y detalles)
Validación estricta: suma de débitos = suma de créditos
CRUD de asientos contables con validación de integridad
Historial de movimientos por cuenta
Importación básica de cuentas desde CSV/Excel

Criterios de Aceptación:

Todo asiento debe balancear (suma = 0)
No se pueden crear asientos con una sola línea
Los movimientos se reflejan correctamente en las cuentas
Se puede importar un plan de cuentas desde archivo

Sprint 3: Reportes Financieros (Semanas 5-6)
Objetivo: Generar los tres reportes financieros principales del sistema.
Entregables:

Estado de Flujo de Efectivo
Balance General con jerarquía de cuentas
Estado de Pérdidas y Ganancias
Filtros por rango de fechas en todos los reportes
Exportación de reportes a PDF/Excel

Criterios de Aceptación:

Los reportes muestran datos precisos y balanceados
Los totales cuadran con la contabilidad de doble partida
Se pueden filtrar por períodos específicos
Los reportes son exportables en múltiples formatos

Sprint 4: Funciones Avanzadas (Semanas 7-8)
Objetivo: Pulir el sistema con funcionalidades que mejoren la experiencia del usuario.
Entregables:

Importación masiva de asientos contables
Auditoría de cambios (quién modificó qué y cuándo)
Dashboard con métricas principales
Búsqueda y filtros avanzados en todas las secciones
Validaciones adicionales y mensajes de error mejorados

Manejo Detallado de Usuarios
Roles del Sistema
Administrador:

Permisos completos en todo el sistema
Puede crear, modificar y eliminar usuarios
Gestiona el plan de cuentas maestro
Acceso a todas las funcionalidades sin restricciones
Puede realizar importaciones masivas
Acceso completo a auditorías y logs del sistema

Contador:

Puede crear y modificar asientos contables
Acceso completo a reportes financieros
Puede crear nuevas cuentas (con aprobación del admin)
Puede exportar reportes
No puede gestionar usuarios ni cambiar configuraciones del sistema
Acceso a funciones de importación de datos

Solo Lectura:

Acceso únicamente a consulta de reportes
Puede ver el plan de cuentas sin modificar
Puede consultar asientos contables históricos
Puede exportar reportes en formatos básicos
No puede crear, modificar ni eliminar ningún registro

Flujo de Autenticación
Registro de Usuarios:

Solo los administradores pueden crear nuevos usuarios
Al crear un usuario se define: nombre, email, contraseña temporal y rol
El usuario debe cambiar la contraseña en el primer login
Se envía notificación por email con credenciales iniciales

Proceso de Login:

Validación de email y contraseña
Generación de JWT token con información del rol
El token incluye permisos específicos según el rol
Tiempo de vida del token configurable (por defecto 8 horas)

Gestión de Sesiones:

Tokens JWT con refresh token para renovación automática
Logout que invalida el token actual
Sistema de bloqueo temporal tras intentos fallidos
Registro de actividad de login/logout para auditoría

Seguridad y Validaciones
Contraseñas:

Mínimo 8 caracteres con mayúsculas, minúsculas y números
Hash con bcrypt para almacenamiento seguro
Opción de reseteo de contraseña por email
Historial de contraseñas para evitar reutilización

Autorización por Endpoints:

Decoradores de FastAPI para validar roles en cada endpoint
Middleware para verificar tokens en todas las rutas protegidas
Logs detallados de intentos de acceso no autorizados
Rate limiting para prevenir ataques de fuerza bruta

Base de Datos de Usuarios
Tabla users:

id (Primary Key)
email (Unique, para login)
hashed_password
full_name
role (Admin/Contador/Solo_Lectura)
is_active (para desactivar sin eliminar)
created_at
last_login
password_changed_at
created_by (referencia al admin que lo creó)

Tabla user_sessions: (Para tracking de sesiones activas)

id
user_id (Foreign Key)
token_jti (JWT ID único)
created_at
expires_at
ip_address
user_agent

Esta estructura te permitirá crecer de manera ordenada, manteniendo la seguridad y escalabilidad que necesitas para un sistema contable robusto. Cada sprint construye sobre el anterior, asegurando que siempre tengas una versión funcional del sistema