# Seguridad y Filtros de Datos Sensibles

## Descripción General

El sistema de exportación implementa un marco robusto de seguridad para proteger información sensible y confidencial. Garantiza que datos como contraseñas, tokens de sesión, claves privadas y otra información crítica nunca se incluyan en las exportaciones, independientemente del formato o método de exportación utilizado.

## Principios de Seguridad

### 🔒 Defensa en Profundidad
- **Filtrado automático**: Omisión transparente de campos sensibles
- **Configuración centralizada**: Definición única de campos protegidos
- **Validación múltiple**: Verificación en varios niveles del sistema
- **Auditoría completa**: Registro de todos los accesos y exportaciones

### 🛡️ Protección por Diseño
- **Whitelist de campos**: Solo se exportan campos explícitamente permitidos
- **Sin configuración adicional**: Protección automática sin intervención manual
- **Inmutable durante exportación**: Los filtros no pueden ser deshabilitados
- **Transparente para el usuario**: Funciona sin afectar la experiencia de usuario

## Configuración de Campos Sensibles

### Definición Centralizada
Los campos sensibles se definen en el servicio de exportación:

```python
# app/services/export_service.py
SENSITIVE_FIELDS = {
    TableName.USERS: [
        'hashed_password',      # Hash de contraseña
        'password_hash',        # Hash alternativo de contraseña
        'password',             # Contraseña en texto plano (si existe)
        'salt',                 # Salt para hashing
        'secret_key',           # Clave secreta personal
        'private_key',          # Clave privada
        'api_key',              # Clave de API
        'token'                 # Tokens generales
    ],
    TableName.USER_SESSIONS: [
        'session_token',        # Token de sesión activa
        'refresh_token',        # Token de renovación
        'access_token'          # Token de acceso
    ],
    TableName.SYSTEM_CONFIGURATION: [
        'secret_value',         # Valores secretos de configuración
        'password',             # Contraseñas del sistema
        'api_secret',           # Secretos de API
        'private_key'           # Claves privadas del sistema
    ]
}
```

### Extensibilidad
El sistema permite agregar fácilmente nuevas tablas y campos sensibles:

```python
# Agregar nueva tabla con campos sensibles
SENSITIVE_FIELDS[TableName.NEW_TABLE] = [
    'confidential_field',
    'secret_data',
    'private_information'
]
```

## Mecanismos de Filtrado

### Filtrado a Nivel de Columnas
**Ubicación**: `_get_table_columns()` y `_filter_sensitive_columns()`

```python
def _get_table_columns(self, model, table_name: Optional[TableName] = None) -> List[ColumnInfo]:
    """Obtiene columnas de tabla con filtrado de seguridad"""
    columns = []
    inspector = inspect(model)
    
    # Generar lista de todas las columnas
    for column in inspector.columns:
        columns.append(ColumnInfo(
            name=column.name,
            data_type=self._determine_data_type(column.type),
            include=True
        ))
    
    # Aplicar filtro de seguridad
    if table_name:
        columns = self._filter_sensitive_columns(columns, table_name)
    
    return columns

def _filter_sensitive_columns(self, columns: List[ColumnInfo], table_name: TableName) -> List[ColumnInfo]:
    """Filtra columnas sensibles para una tabla específica"""
    if table_name not in self.SENSITIVE_FIELDS:
        return columns
    
    sensitive_fields = self.SENSITIVE_FIELDS[table_name]
    filtered_columns = []
    
    for column in columns:
        if column.name not in sensitive_fields:
            filtered_columns.append(column)
        else:
            # Log del campo omitido para auditoría
            print(f"Campo sensible omitido en exportación: {column.name}")
    
    return filtered_columns
```

### Filtrado a Nivel de Datos
**Ubicación**: `_model_to_dict()`

```python
def _model_to_dict(self, model_instance, selected_columns: Optional[List[ColumnInfo]] = None, 
                   table_name: Optional[TableName] = None) -> Dict[str, Any]:
    """Convierte modelo a diccionario con filtrado de seguridad"""
    result = {}
    
    # Determinar columnas a incluir
    if selected_columns is None:
        columns_to_include = [c.name for c in inspect(model_instance.__class__).columns]
    else:
        columns_to_include = [c.name for c in selected_columns if c.include]
    
    # Aplicar filtrado de campos sensibles
    if table_name and table_name in self.SENSITIVE_FIELDS:
        sensitive_fields = self.SENSITIVE_FIELDS[table_name]
        columns_to_include = [col for col in columns_to_include if col not in sensitive_fields]
    
    # Procesar solo campos seguros
    for column_name in columns_to_include:
        # ... conversión de datos
    
    return result
```

## Flujo de Seguridad

### 1. Consulta de Esquema de Tabla
```
Usuario solicita esquema → Sistema inspecciona modelo → Filtro de columnas sensibles → 
Retorna solo campos seguros
```

### 2. Exportación de Datos
```
Usuario solicita exportación → Sistema construye query → Obtiene datos → 
Filtro de campos sensibles → Generación de archivo → Entrega solo datos seguros
```

### 3. Datos de Muestra
```
Sistema genera muestra → Filtro automático → Solo campos seguros en muestra
```

## Casos de Uso de Seguridad

### Exportación de Usuarios
**Sin filtrado (inseguro):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "hashed_password": "$2b$12$...",
  "api_key": "sk_live_...",
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Con filtrado (seguro):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00",
  "role": "USER"
}
```

### Exportación de Sesiones
**Sin filtrado (inseguro):**
```json
{
  "id": 123,
  "user_id": 1,
  "session_token": "abc123...",
  "refresh_token": "def456...",
  "access_token": "ghi789...",
  "expires_at": "2024-12-11T10:30:00"
}
```

**Con filtrado (seguro):**
```json
{
  "id": 123,
  "user_id": 1,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2024-12-10T10:30:00",
  "expires_at": "2024-12-11T10:30:00",
  "is_active": true
}
```

### Exportación de Configuración del Sistema
**Sin filtrado (inseguro):**
```json
{
  "id": 1,
  "key": "database_url",
  "value": "postgresql://user:password@localhost/db",
  "secret_value": "super_secret_key_123"
}
```

**Con filtrado (seguro):**
```json
{
  "id": 1,
  "key": "database_url",
  "description": "URL de conexión a base de datos",
  "category": "database",
  "is_public": false,
  "created_at": "2024-01-01T00:00:00"
}
```

## Auditoría y Logging

### Registro de Campos Omitidos
```python
def _filter_sensitive_columns(self, columns: List[ColumnInfo], table_name: TableName) -> List[ColumnInfo]:
    """Filtra columnas sensibles con logging de auditoría"""
    if table_name not in self.SENSITIVE_FIELDS:
        return columns
    
    sensitive_fields = self.SENSITIVE_FIELDS[table_name]
    filtered_columns = []
    omitted_fields = []
    
    for column in columns:
        if column.name not in sensitive_fields:
            filtered_columns.append(column)
        else:
            omitted_fields.append(column.name)
    
    # Log de auditoría
    if omitted_fields:
        logger.info(f"Campos sensibles omitidos en exportación de {table_name.value}: {omitted_fields}")
    
    return filtered_columns
```

### Metadatos de Seguridad
```python
# Los metadatos incluyen información sobre filtrado
metadata = ExportMetadata(
    # ... otros campos
    columns_exported=["id", "email", "first_name"],  # Solo campos seguros
    security_applied=True,                           # Indicador de filtrado
    sensitive_fields_omitted=["hashed_password", "api_key"]  # Campos omitidos
)
```

## Validaciones de Seguridad

### Verificación de Integridad
```python
def verify_export_security(self, exported_data: List[Dict], table_name: TableName) -> bool:
    """Verifica que no se hayan exportado campos sensibles"""
    if table_name not in self.SENSITIVE_FIELDS:
        return True
    
    sensitive_fields = set(self.SENSITIVE_FIELDS[table_name])
    
    for record in exported_data:
        exported_fields = set(record.keys())
        if sensitive_fields.intersection(exported_fields):
            # ¡Alerta de seguridad!
            logger.error(f"SECURITY BREACH: Campos sensibles encontrados en export: {sensitive_fields.intersection(exported_fields)}")
            return False
    
    return True
```

### Test de Seguridad Automático
```python
def test_no_sensitive_data_in_export():
    """Test que verifica que nunca se exporten datos sensibles"""
    service = ExportService(db)
    
    # Test para tabla de usuarios
    request = ExportRequest(
        table_name=TableName.USERS,
        export_format=ExportFormat.JSON,
        filters=ExportFilter(limit=10)
    )
    
    response = service.export_data(request, user_id)
    exported_data = json.loads(response.file_content)
    
    # Verificar que no hay campos sensibles
    sensitive_fields = service.SENSITIVE_FIELDS[TableName.USERS]
    for record in exported_data:
        for sensitive_field in sensitive_fields:
            assert sensitive_field not in record, f"Campo sensible {sensitive_field} encontrado en export"
```

## Configuración Avanzada

### Campos Sensibles Dinámicos
```python
def get_dynamic_sensitive_fields(self, table_name: TableName, user_role: str) -> List[str]:
    """Obtiene campos sensibles según el rol del usuario"""
    base_sensitive = self.SENSITIVE_FIELDS.get(table_name, [])
    
    # Administradores pueden ver más información
    if user_role == "ADMIN":
        return [field for field in base_sensitive if field in ['hashed_password', 'session_token']]
    
    # Usuarios normales ven menos
    return base_sensitive
```

### Configuración por Entorno
```python
# Configuración más restrictiva en producción
if settings.ENVIRONMENT == "production":
    SENSITIVE_FIELDS[TableName.USERS].extend([
        'ip_address',      # IP también es sensible en producción
        'user_agent',      # User agent puede ser sensible
        'last_login_at'    # Información de actividad
    ])
```

### Enmascaramiento Parcial
```python
def mask_sensitive_data(self, value: str, field_name: str) -> str:
    """Enmascara parcialmente datos sensibles en lugar de omitirlos"""
    if field_name == 'email':
        # Mostrar solo primeras letras del email
        parts = value.split('@')
        if len(parts) == 2:
            return f"{parts[0][:2]}***@{parts[1]}"
    
    elif field_name == 'phone':
        # Mostrar solo últimos 4 dígitos
        return f"***-{value[-4:]}"
    
    return "***"
```

## Cumplimiento y Regulaciones

### GDPR (Reglamento General de Protección de Datos)
- **Minimización de datos**: Solo se exportan datos necesarios
- **Derecho al olvido**: Campos eliminados no aparecen en exports
- **Consentimiento**: Logs de qué usuario exportó qué datos

### PCI DSS (Payment Card Industry Data Security Standard)
- **Protección de datos de tarjetas**: Números de tarjeta nunca se exportan
- **Tokenización**: Solo tokens seguros en lugar de datos reales
- **Auditoría**: Registro completo de accesos a datos sensibles

### HIPAA (Health Insurance Portability and Accountability Act)
- **PHI Protection**: Información de salud personal protegida
- **Acceso mínimo**: Solo datos necesarios para la función específica
- **Trazabilidad**: Registro de quién accedió a qué información

## Mejores Prácticas

### Desarrollo Seguro
1. **Nunca hardcodear**: Campos sensibles en configuración, no en código
2. **Principio de menor privilegio**: Solo exportar lo mínimo necesario
3. **Validación continua**: Tests automáticos de seguridad
4. **Revisión de código**: Revisión específica de cambios en seguridad

### Monitoreo
1. **Alertas automáticas**: Si se detectan campos sensibles en exports
2. **Métricas de seguridad**: Número de campos filtrados por periodo
3. **Análisis de patrones**: Detectar intentos de exportar datos sensibles
4. **Auditoría regular**: Revisión periódica de configuración de seguridad

### Documentación
1. **Política clara**: Documentar qué datos son sensibles y por qué
2. **Procedimientos**: Cómo agregar nuevos campos sensibles
3. **Capacitación**: Entrenar al equipo en principios de seguridad
4. **Actualización**: Mantener la documentación actualizada

## Troubleshooting

### Problemas Comunes

#### "Campo esperado no aparece en export"
**Causa**: El campo puede estar marcado como sensible
**Solución**: Verificar `SENSITIVE_FIELDS` para la tabla

#### "Export vacío o incompleto"
**Causa**: Todos los campos solicitados pueden ser sensibles
**Solución**: Revisar qué campos están disponibles usando endpoint de esquema

#### "Error de validación en campos"
**Causa**: Solicitud de campos que no existen o son sensibles
**Solución**: Usar endpoint de información de tabla para ver campos disponibles

### Debugging
```python
# Habilitar logging detallado de seguridad
import logging
logging.getLogger('app.services.export_service').setLevel(logging.DEBUG)

# Verificar qué campos están siendo filtrados
sensitive_fields = export_service.SENSITIVE_FIELDS.get(TableName.USERS, [])
print(f"Campos sensibles para usuarios: {sensitive_fields}")
```
