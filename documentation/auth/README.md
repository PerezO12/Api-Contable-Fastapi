# Índice de Documentación - Sistema de Autenticación y Usuarios

Este directorio contiene la documentación completa del sistema de autenticación y gestión de usuarios del API Contable.

## 📚 Documentos Disponibles

### 🔐 [authentication.md](./authentication.md)
**Sistema de Autenticación y Seguridad**
- Descripción general del sistema de autenticación
- Arquitectura basada en JWT
- Flujos de autenticación
- Configuración de seguridad
- Protecciones implementadas
- Manejo de errores y excepciones
- Integración con FastAPI

### 👥 [user-management.md](./user-management.md)
**Gestión de Usuarios**
- CRUD completo de usuarios
- Funcionalidades administrativas
- Operaciones masivas
- Estados de usuario y transiciones
- Validaciones de negocio
- Gestión de sesiones de usuario
- Estadísticas y métricas

### 🛡️ [roles-permissions.md](./roles-permissions.md)
**Roles y Permisos del Sistema**
- Jerarquía de roles (ADMIN, CONTADOR, SOLO_LECTURA)
- Definición detallada de permisos
- Matriz de permisos por funcionalidad
- Implementación técnica del RBAC
- Control de acceso por endpoint
- Validación y seguridad
- Casos de uso y escenarios

### 🎫 [sessions-tokens.md](./sessions-tokens.md)
**Sesiones y Tokens JWT**
- Arquitectura de tokens (access + refresh)
- Gestión de sesiones activas
- JWTManager y utilidades
- Flujos de autenticación completos
- Configuración de seguridad
- Sesiones múltiples y concurrentes
- Limpieza y mantenimiento automático

### 🌐 [auth-endpoints.md](./auth-endpoints.md)
**Endpoints de Autenticación**
- `/login` - Autenticación de usuarios
- `/login/form` - Login compatible OAuth2
- `/refresh` - Renovación de tokens
- `/logout` - Cierre de sesión
- `/setup-admin` - Configuración inicial
- Ejemplos de uso completos
- Manejo de errores
- Testing y validación

### 👤 [user-endpoints.md](./user-endpoints.md)
**Endpoints de Gestión de Usuarios**
- `/me` - Información del usuario actual
- `/me/password` - Cambio de contraseña
- `/admin/create-user` - Creación por admin
- `/stats` - Estadísticas de usuarios
- CRUD completo de usuarios
- Gestión de sesiones
- Operaciones administrativas

## 🔧 Cómo Usar Esta Documentación

### Para Desarrolladores
1. **Comenzar con**: [authentication.md](./authentication.md) para entender la arquitectura general
2. **Implementar autenticación**: [auth-endpoints.md](./auth-endpoints.md) para los endpoints básicos
3. **Gestión de usuarios**: [user-endpoints.md](./user-endpoints.md) para operaciones CRUD
4. **Configurar permisos**: [roles-permissions.md](./roles-permissions.md) para control de acceso

### Para Administradores del Sistema
1. **Configuración inicial**: [authentication.md](./authentication.md) - sección de configuración
2. **Gestión de usuarios**: [user-management.md](./user-management.md) - operaciones administrativas
3. **Seguridad**: [roles-permissions.md](./roles-permissions.md) - asignación de roles

### Para Integraciones
1. **Flujos de autenticación**: [sessions-tokens.md](./sessions-tokens.md) - manejo de tokens
2. **APIs disponibles**: [auth-endpoints.md](./auth-endpoints.md) y [user-endpoints.md](./user-endpoints.md)
3. **Ejemplos de código**: Todos los documentos incluyen ejemplos prácticos

## 📋 Resumen de Funcionalidades

### ✅ Implementado Completamente
- ✅ Autenticación JWT con access y refresh tokens
- ✅ Sistema de roles granular (ADMIN, CONTADOR, SOLO_LECTURA)
- ✅ CRUD completo de usuarios
- ✅ Gestión de sesiones activas
- ✅ Cambio de contraseñas con validación
- ✅ Reset de contraseñas por admin
- ✅ Bloqueo automático por intentos fallidos
- ✅ Auditoría básica de acciones
- ✅ Endpoints de administración
- ✅ Validaciones de seguridad robustas

### 🔄 Características Principales
- **Seguridad**: bcrypt, JWT, validación de contraseñas, rate limiting
- **Escalabilidad**: Sesiones en base de datos, limpieza automática
- **Usabilidad**: APIs REST estándar, documentación completa
- **Mantenibilidad**: Código modular, excepciones personalizadas
- **Auditoría**: Logs automáticos, tracking de actividad

## 🗺️ Mapa de Navegación

```
Sistema de Autenticación
├── 🔐 Autenticación General ────── authentication.md
├── 👥 Gestión de Usuarios ─────── user-management.md  
├── 🛡️ Roles y Permisos ───────── roles-permissions.md
├── 🎫 Sesiones y Tokens ──────── sessions-tokens.md
├── 🌐 APIs de Autenticación ──── auth-endpoints.md
└── 👤 APIs de Usuarios ───────── user-endpoints.md
```

## 🔗 Enlaces Rápidos

### Configuración Inicial
- [Variables de entorno](./authentication.md#configuración-de-seguridad)
- [Crear primer admin](./auth-endpoints.md#👤-post-setup-admin)
- [Configurar JWT](./sessions-tokens.md#configuración-de-seguridad)

### Operaciones Comunes
- [Login de usuario](./auth-endpoints.md#🔐-post-login)
- [Crear usuario](./user-endpoints.md#➕-post-admincreate-user)
- [Cambiar contraseña](./user-endpoints.md#🔑-put-mepassword)
- [Gestionar roles](./roles-permissions.md#definición-de-roles)

### Troubleshooting
- [Errores comunes](./sessions-tokens.md#troubleshooting-común)
- [Códigos de error](./auth-endpoints.md#manejo-de-errores)
- [Validaciones](./user-management.md#validaciones-de-negocio)

## 📞 Soporte

### Para Issues Técnicos
- Revisar [manejo de errores](./auth-endpoints.md#manejo-de-errores)
- Consultar [troubleshooting](./sessions-tokens.md#troubleshooting-común)
- Verificar [configuración](./authentication.md#configuración-de-seguridad)

### Para Nuevas Funcionalidades
- Revisar [extensibilidad](./roles-permissions.md#extensibilidad-del-sistema)
- Consultar arquitectura en [authentication.md](./authentication.md)
- Verificar casos de uso en [user-management.md](./user-management.md)

---

## 📝 Notas de la Versión

**Versión Actual**: 1.0.0 (Junio 2025)

### ✨ Características Implementadas
- Sistema de autenticación JWT completo
- Gestión de usuarios con 3 roles
- API REST con documentación completa
- Seguridad robusta con múltiples protecciones
- Testing automatizado incluido

### 🔮 Próximas Funcionalidades
- Autenticación multifactor (2FA)
- Integración con proveedores OAuth2 externos
- Políticas de contraseña configurables
- Dashboard de administración web
- Notificaciones por email

---

**Última actualización**: 10 de Junio, 2025  
**Mantenido por**: Equipo de Desarrollo API Contable
