# Roles y Permisos del Sistema

## Descripción General

El sistema de roles y permisos del API Contable implementa un modelo de control de acceso basado en roles (RBAC - Role-Based Access Control) que garantiza que los usuarios solo puedan acceder a las funcionalidades apropiadas para su posición y responsabilidades en la organización.

## Arquitectura de Roles

### Jerarquía de Roles
```
ADMIN (Administrador del Sistema)
├── Acceso completo a todas las funcionalidades
├── Gestión de usuarios y configuración
└── Supervisión y auditoría

CONTADOR (Especialista Contable)  
├── Gestión completa de operaciones contables
├── Creación y modificación de asientos
├── Gestión del plan de cuentas
└── Reportes financieros avanzados

SOLO_LECTURA (Consulta)
├── Visualización de reportes básicos
├── Consulta del plan de cuentas
├── Visualización de asientos históricos
└── Exportación básica de datos
```

## Definición de Roles

### 👑 ADMIN (Administrador del Sistema)

#### Responsabilidades Principales
- **Gestión de Usuarios**: Crear, modificar y administrar cuentas de usuario
- **Configuración del Sistema**: Ajustar parámetros y configuraciones globales
- **Supervisión**: Monitorear la actividad y rendimiento del sistema
- **Seguridad**: Gestionar políticas de seguridad y acceso
- **Auditoría**: Acceso completo a logs y reportes de auditoría

#### Permisos Específicos
```python
ADMIN_PERMISSIONS = {
    # Gestión de usuarios
    "users.create": True,
    "users.read": True,
    "users.update": True,
    "users.delete": True,
    "users.manage_roles": True,
    "users.reset_passwords": True,
    "users.view_sessions": True,
    
    # Gestión de cuentas
    "accounts.create": True,
    "accounts.read": True,
    "accounts.update": True,
    "accounts.delete": True,
    "accounts.manage_structure": True,
    
    # Asientos contables
    "journal_entries.create": True,
    "journal_entries.read": True,
    "journal_entries.update": True,
    "journal_entries.delete": True,
    "journal_entries.post": True,
    "journal_entries.reverse": True,
    
    # Reportes
    "reports.basic": True,
    "reports.advanced": True,
    "reports.financial": True,
    "reports.audit": True,
    "reports.export_all": True,
    
    # Sistema
    "system.configure": True,
    "system.backup": True,
    "system.audit_logs": True,
    "system.maintenance": True,
    
    # Importación/Exportación
    "import.data": True,
    "export.data": True,
    "import.bulk_operations": True,
    "export.bulk_operations": True
}
```

#### Casos de Uso Típicos
- Configuración inicial del sistema
- Creación de usuarios para nuevos empleados
- Resolución de problemas técnicos
- Configuración de políticas de seguridad
- Supervisión general del sistema

### 📊 CONTADOR (Especialista Contable)

#### Responsabilidades Principales
- **Operaciones Contables**: Creación y gestión de asientos contables
- **Plan de Cuentas**: Mantenimiento y estructura de cuentas
- **Reportes Financieros**: Generación de reportes especializados
- **Importación de Datos**: Carga masiva de información contable
- **Análisis**: Interpretación de datos financieros

#### Permisos Específicos
```python
CONTADOR_PERMISSIONS = {
    # Gestión limitada de usuarios (solo lectura)
    "users.read": True,  # Solo su propia información
    "users.update": False,
    "users.create": False,
    
    # Gestión completa de cuentas
    "accounts.create": True,
    "accounts.read": True,
    "accounts.update": True,
    "accounts.delete": True,  # Con restricciones
    "accounts.manage_structure": True,
    
    # Asientos contables completos
    "journal_entries.create": True,
    "journal_entries.read": True,
    "journal_entries.update": True,
    "journal_entries.delete": True,  # Solo no posteados
    "journal_entries.post": True,
    "journal_entries.reverse": True,  # Con aprobación
    
    # Reportes financieros
    "reports.basic": True,
    "reports.advanced": True,
    "reports.financial": True,
    "reports.audit": False,  # Sin acceso a auditoría
    "reports.export_all": True,
    
    # Sistema limitado
    "system.configure": False,
    "system.backup": False,
    "system.audit_logs": False,
    
    # Importación/Exportación
    "import.data": True,
    "export.data": True,
    "import.bulk_operations": True,
    "export.bulk_operations": True
}
```

#### Restricciones Importantes
- No puede gestionar usuarios del sistema
- No puede acceder a configuraciones del sistema
- No puede ver logs de auditoría completos
- Eliminación de registros con restricciones según estado

#### Casos de Uso Típicos
- Registro diario de operaciones contables
- Mantenimiento del plan de cuentas
- Generación de reportes financieros mensuales
- Importación de datos desde sistemas externos
- Análisis de balances y estados financieros

### 👁️ SOLO_LECTURA (Usuario de Consulta)

#### Responsabilidades Principales
- **Consulta de Información**: Acceso de solo lectura a datos contables
- **Reportes Básicos**: Generación de reportes estándar
- **Visualización**: Consulta de estados y balances históricos
- **Exportación Limitada**: Descarga de información básica

#### Permisos Específicos
```python
SOLO_LECTURA_PERMISSIONS = {
    # Sin gestión de usuarios
    "users.read": True,  # Solo su propia información
    "users.update": False,
    "users.create": False,
    
    # Solo consulta de cuentas
    "accounts.create": False,
    "accounts.read": True,
    "accounts.update": False,
    "accounts.delete": False,
    
    # Solo lectura de asientos
    "journal_entries.create": False,
    "journal_entries.read": True,
    "journal_entries.update": False,
    "journal_entries.delete": False,
    "journal_entries.post": False,
    
    # Reportes básicos únicamente
    "reports.basic": True,
    "reports.advanced": False,
    "reports.financial": True,  # Solo lectura
    "reports.audit": False,
    "reports.export_basic": True,
    
    # Sin acceso al sistema
    "system.configure": False,
    "system.backup": False,
    "system.audit_logs": False,
    
    # Exportación limitada
    "import.data": False,
    "export.data": True,  # Solo formatos básicos
    "import.bulk_operations": False,
    "export.bulk_operations": False
}
```

#### Restricciones Estrictas
- No puede crear, modificar o eliminar registros
- No puede acceder a funciones administrativas
- No puede ver información sensible de otros usuarios
- Exportación limitada a formatos básicos

#### Casos de Uso Típicos
- Consulta de balances históricos
- Visualización de reportes estándar
- Exportación de datos para análisis externos
- Verificación de información contable

## Implementación Técnica

### Modelo de Usuario
```python
class UserRole(str, Enum):
    """Roles de usuario del sistema contable"""
    ADMIN = "ADMIN"
    CONTADOR = "CONTADOR" 
    SOLO_LECTURA = "SOLO_LECTURA"

class User(Base):
    # ... otros campos
    role: Mapped[UserRole] = mapped_column(
        default=UserRole.SOLO_LECTURA, 
        nullable=False
    )
    
    @property
    def is_admin(self) -> bool:
        """Verifica si el usuario es administrador"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_contador(self) -> bool:
        """Verifica si el usuario es contador"""
        return self.role == UserRole.CONTADOR
    
    @property
    def can_manage_users(self) -> bool:
        """Verifica si puede gestionar usuarios"""
        return self.role == UserRole.ADMIN
```

### Validación de Permisos en Servicios
```python
class AuthService:
    async def validate_user_permissions(
        self, 
        user: User, 
        required_permissions: List[str]
    ) -> bool:
        """Valida si un usuario tiene los permisos requeridos"""
        user_permissions = self._get_permissions_for_role(user.role)
        
        for permission in required_permissions:
            if not user_permissions.get(permission, False):
                raise InsufficientPermissionsException(
                    required_permission=permission,
                    user_role=user.role.value
                )
        
        return True
    
    def _get_permissions_for_role(self, role: UserRole) -> Dict[str, bool]:
        """Obtiene los permisos para un rol específico"""
        permission_map = {
            UserRole.ADMIN: ADMIN_PERMISSIONS,
            UserRole.CONTADOR: CONTADOR_PERMISSIONS,
            UserRole.SOLO_LECTURA: SOLO_LECTURA_PERMISSIONS
        }
        return permission_map.get(role, {})
```

### Dependencias de FastAPI
```python
from app.api.deps import get_current_admin_user, get_current_active_user

# Solo administradores
@router.post("/admin-only-endpoint")
async def admin_endpoint(
    current_user: User = Depends(get_current_admin_user)
):
    # Solo accesible por ADMIN
    pass

# Usuarios activos con validación específica
@router.post("/contador-endpoint")
async def contador_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    # Validar permisos específicos
    if current_user.role not in [UserRole.ADMIN, UserRole.CONTADOR]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    pass
```

## Control de Acceso por Endpoint

### Endpoints Públicos
- `/auth/login` - Login de usuarios
- `/auth/refresh` - Renovación de tokens
- `/docs` - Documentación API (según configuración)

### Endpoints por Rol

#### ADMIN únicamente
- `POST /auth/setup-admin` - Crear administrador inicial
- `POST /users/admin/create-user` - Crear nuevos usuarios
- `PUT /users/{user_id}/reset-password` - Reset contraseñas
- `PUT /users/{user_id}/force-password-change` - Forzar cambio
- `GET /users/stats` - Estadísticas de usuarios
- `GET /audit/logs` - Logs de auditoría

#### ADMIN + CONTADOR
- `POST /accounts` - Crear cuentas
- `PUT /accounts/{account_id}` - Modificar cuentas
- `POST /journal-entries` - Crear asientos
- `PUT /journal-entries/{entry_id}` - Modificar asientos
- `POST /journal-entries/{entry_id}/post` - Postear asientos
- `POST /import/data` - Importar datos

#### Todos los roles autenticados
- `GET /users/me` - Información del usuario actual
- `PUT /users/me/password` - Cambiar propia contraseña
- `GET /accounts` - Consultar cuentas
- `GET /journal-entries` - Consultar asientos
- `GET /reports/basic` - Reportes básicos

#### Solo SOLO_LECTURA (restricciones especiales)
- Acceso limitado a endpoints de consulta
- No puede acceder a operaciones de escritura
- Reportes con formato y datos limitados

## Matriz de Permisos

| Funcionalidad | ADMIN | CONTADOR | SOLO_LECTURA |
|---------------|-------|----------|--------------|
| **Gestión de Usuarios** |
| Crear usuarios | ✅ | ❌ | ❌ |
| Ver usuarios | ✅ | ❌ | ❌ |
| Modificar usuarios | ✅ | ❌ | ❌ |
| Eliminar usuarios | ✅ | ❌ | ❌ |
| Reset contraseñas | ✅ | ❌ | ❌ |
| **Plan de Cuentas** |
| Crear cuentas | ✅ | ✅ | ❌ |
| Ver cuentas | ✅ | ✅ | ✅ |
| Modificar cuentas | ✅ | ✅ | ❌ |
| Eliminar cuentas | ✅ | ⚠️* | ❌ |
| **Asientos Contables** |
| Crear asientos | ✅ | ✅ | ❌ |
| Ver asientos | ✅ | ✅ | ✅ |
| Modificar asientos | ✅ | ✅ | ❌ |
| Eliminar asientos | ✅ | ⚠️* | ❌ |
| Postear asientos | ✅ | ✅ | ❌ |
| Reversar asientos | ✅ | ⚠️* | ❌ |
| **Reportes** |
| Reportes básicos | ✅ | ✅ | ✅ |
| Reportes avanzados | ✅ | ✅ | ❌ |
| Reportes financieros | ✅ | ✅ | ✅** |
| Reportes de auditoría | ✅ | ❌ | ❌ |
| **Sistema** |
| Configuración | ✅ | ❌ | ❌ |
| Logs de auditoría | ✅ | ❌ | ❌ |
| Backup/Restore | ✅ | ❌ | ❌ |
| **Importación/Exportación** |
| Importar datos | ✅ | ✅ | ❌ |
| Exportar datos | ✅ | ✅ | ✅** |
| Operaciones masivas | ✅ | ✅ | ❌ |

**Leyenda:**
- ✅ Acceso completo
- ❌ Sin acceso
- ⚠️* Con restricciones según estado/contexto
- ✅** Solo lectura o formato limitado

## Validación y Seguridad

### Validación en Tiempo de Ejecución
```python
async def validate_permission(user: User, permission: str):
    """Valida un permiso específico para un usuario"""
    permissions = get_user_permissions(user.role)
    
    if not permissions.get(permission, False):
        logger.warning(
            f"Permission denied: {user.email} attempted {permission}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions for action: {permission}"
        )
```

### Auditoría de Accesos
- Todos los intentos de acceso son registrados
- Permisos denegados generan alertas
- Cambios de rol son auditados automáticamente
- Escalamiento de privilegios monitoreado

### Principio de Menor Privilegio
- Usuarios inician con rol SOLO_LECTURA
- Escalamiento de privilegios manual por admin
- Permisos revisados periódicamente
- Acceso basado en necesidad laboral

## Casos de Uso y Escenarios

### Onboarding de Empleado
1. Admin crea usuario con rol apropiado
2. Usuario recibe credenciales temporales
3. Primer login requiere cambio de contraseña
4. Acceso limitado a funciones de su rol

### Cambio de Responsabilidades
1. Admin evalúa nuevas necesidades de acceso
2. Actualiza rol del usuario
3. Cambio auditado automáticamente
4. Usuario notificado de nuevos permisos

### Rotación de Personal
1. Admin desactiva cuenta inmediatamente
2. Sesiones activas invalidas gradualmente
3. Datos históricos preservados
4. Posible reactivación futura

### Auditoría de Seguridad
1. Revisión periódica de roles asignados
2. Identificación de usuarios inactivos
3. Verificación de permisos necesarios
4. Ajuste de accesos según función actual

## Extensibilidad del Sistema

### Agregar Nuevos Roles
```python
# En user.py
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CONTADOR = "CONTADOR"
    SOLO_LECTURA = "SOLO_LECTURA"
    SUPERVISOR = "SUPERVISOR"  # Nuevo rol
    AUDITOR = "AUDITOR"        # Nuevo rol

# Definir permisos para nuevos roles
SUPERVISOR_PERMISSIONS = {
    # Permisos específicos del supervisor
}
```

### Permisos Granulares
```python
# Sistema de permisos más específico
GRANULAR_PERMISSIONS = {
    "accounts.view": ["ADMIN", "CONTADOR", "SOLO_LECTURA"],
    "accounts.create": ["ADMIN", "CONTADOR"],
    "accounts.modify": ["ADMIN", "CONTADOR"], 
    "accounts.delete": ["ADMIN"],
    "journal_entries.post": ["ADMIN", "CONTADOR"],
    "journal_entries.reverse": ["ADMIN"],
    "reports.financial.detailed": ["ADMIN", "CONTADOR"],
    "reports.audit": ["ADMIN"]
}
```

## Referencias

- [Autenticación y Seguridad](./authentication.md)
- [Gestión de Usuarios](./user-management.md)
- [Endpoints de Usuarios](./user-endpoints.md)
- [Sesiones y Tokens](./sessions-tokens.md)
