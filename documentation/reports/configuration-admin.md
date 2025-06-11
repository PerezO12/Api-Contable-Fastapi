# ⚙️ Configuración y Administración del Sistema de Reportes

## Descripción General

Esta guía proporciona información completa sobre la configuración, administración y mantenimiento del sistema de reportes financieros. Incluye configuraciones de seguridad, optimización de rendimiento, monitoreo y resolución de problemas.

## Configuración Inicial

### 📋 **Requisitos del Sistema**

#### Hardware Mínimo
- **CPU**: 2 cores, 2.4 GHz
- **RAM**: 4 GB (8 GB recomendado)
- **Almacenamiento**: 10 GB disponibles
- **Red**: Conexión estable a internet

#### Software Requerido
- **Python**: 3.9 o superior
- **PostgreSQL**: 12 o superior
- **Redis**: 6.0 o superior (para caché)
- **Sistema Operativo**: Windows 10/11, Linux, macOS

### 🔧 **Variables de Entorno**

Configurar las siguientes variables en el archivo `.env`:

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/contable_db
DATABASE_POOL_SIZE=10
DATABASE_POOL_OVERFLOW=20

# Reportes
REPORTS_CACHE_TTL=3600  # Tiempo de vida del caché en segundos
REPORTS_MAX_DATE_RANGE=365  # Máximo rango de fechas en días
REPORTS_ASYNC_TIMEOUT=300  # Timeout para reportes asíncronos
REPORTS_EXPORT_PATH=/tmp/reports  # Directorio para archivos exportados

# Rendimiento
REPORTS_ENABLE_CACHE=true
REPORTS_CACHE_REDIS_URL=redis://localhost:6379/0
REPORTS_PARALLEL_QUERIES=true
REPORTS_QUERY_TIMEOUT=30

# Seguridad
REPORTS_REQUIRE_AUTH=true
REPORTS_RATE_LIMIT=100  # Requests por minuto por usuario
REPORTS_AUDIT_LOG=true

# Logging
REPORTS_LOG_LEVEL=INFO
REPORTS_LOG_FILE=/var/log/reports.log
REPORTS_DEBUG_SQL=false
```

### 🏗️ **Configuración de Base de Datos**

#### Índices Recomendados

```sql
-- Índices para optimización de reportes
CREATE INDEX CONCURRENTLY idx_journal_entries_date 
ON journal_entries(date);

CREATE INDEX CONCURRENTLY idx_journal_entries_company 
ON journal_entries(company_id);

CREATE INDEX CONCURRENTLY idx_accounts_type 
ON accounts(account_type);

CREATE INDEX CONCURRENTLY idx_accounts_parent 
ON accounts(parent_account_id);

-- Índice compuesto para filtros comunes
CREATE INDEX CONCURRENTLY idx_journal_entries_date_company 
ON journal_entries(date, company_id);

-- Índices para auditoría
CREATE INDEX CONCURRENTLY idx_audit_logs_table_action 
ON audit_logs(table_name, action, created_at);
```

#### Configuración de PostgreSQL

```ini
# postgresql.conf - Configuraciones recomendadas

# Memoria
shared_buffers = 256MB
work_mem = 8MB
maintenance_work_mem = 64MB

# Conexiones
max_connections = 100
max_prepared_transactions = 100

# Logging
log_statement = 'mod'
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on

# Autovacuum
autovacuum = on
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
```

## Administración del Sistema

### 👥 **Gestión de Usuarios y Permisos**

#### Roles del Sistema

```python
# Configuración de roles para reportes
REPORT_ROLES = {
    "admin": {
        "permissions": ["read", "export", "admin"],
        "endpoints": ["*"],
        "rate_limit": 1000
    },
    "accountant": {
        "permissions": ["read", "export"],
        "endpoints": [
            "/balance-sheet", "/income-statement", 
            "/trial-balance", "/general-ledger"
        ],
        "rate_limit": 200
    },
    "manager": {
        "permissions": ["read"],
        "endpoints": [
            "/balance-sheet", "/income-statement",
            "/accounts-summary/*"
        ],
        "rate_limit": 100
    },
    "auditor": {
        "permissions": ["read", "audit"],
        "endpoints": [
            "/accounting-integrity", "/trial-balance",
            "/general-ledger"
        ],
        "rate_limit": 150
    }
}
```

#### Script de Configuración de Permisos

```python
# setup_report_permissions.py
import asyncio
from app.services.auth_service import AuthService
from app.services.user_service import UserService

async def setup_report_permissions():
    """Configurar permisos por defecto para reportes"""
    
    auth_service = AuthService()
    user_service = UserService()
    
    # Crear grupos de permisos
    permissions = [
        "reports:read",
        "reports:export", 
        "reports:admin",
        "reports:audit"
    ]
    
    for permission in permissions:
        await auth_service.create_permission(permission)
    
    # Asignar permisos a roles
    role_permissions = {
        "admin": permissions,
        "accountant": ["reports:read", "reports:export"],
        "manager": ["reports:read"],
        "auditor": ["reports:read", "reports:audit"]
    }
    
    for role, perms in role_permissions.items():
        for perm in perms:
            await auth_service.assign_permission_to_role(role, perm)

if __name__ == "__main__":
    asyncio.run(setup_report_permissions())
```

### 💰 **Configuración del Servicio de Flujo de Efectivo**

#### Categorización de Cuentas

El sistema de flujo de efectivo requiere que las cuentas estén categorizadas correctamente según el tipo de actividad:

```python
# Categorías disponibles
from app.models.account import CashFlowCategory

CASH_FLOW_CATEGORIES = {
    CashFlowCategory.OPERATING: [
        "Ventas y servicios",
        "Cobros de clientes", 
        "Pagos a proveedores",
        "Sueldos y salarios",
        "Gastos operativos",
        "Impuestos operativos"
    ],
    CashFlowCategory.INVESTING: [
        "Compra/venta de activos fijos",
        "Inversiones en equipos",
        "Adquisición de propiedades",
        "Venta de inversiones",
        "Préstamos otorgados/cobrados"
    ],
    CashFlowCategory.FINANCING: [
        "Emisión/recompra de acciones",
        "Dividendos pagados",
        "Préstamos obtenidos/pagados",
        "Aportes de capital",
        "Líneas de crédito"
    ],
    CashFlowCategory.CASH_EQUIVALENTS: [
        "Caja y bancos",
        "Inversiones temporales",
        "Certificados de depósito",
        "Fondos mutuos de corto plazo"
    ]
}
```

#### Script de Migración y Categorización

```python
# categorize_accounts_cash_flow.py
import asyncio
from sqlalchemy import select, update
from app.database import get_async_session
from app.models.account import Account, CashFlowCategory

async def categorize_existing_accounts():
    """Categorizar cuentas existentes según patrones predefinidos"""
    
    async with get_async_session() as session:
        # Obtener todas las cuentas sin categoría
        stmt = select(Account).where(Account.cash_flow_category.is_(None))
        result = await session.execute(stmt)
        uncategorized_accounts = result.scalars().all()
        
        categorization_rules = {
            # Cuentas de efectivo y equivalentes
            CashFlowCategory.CASH_EQUIVALENTS: [
                "1001", "1002", "1003",  # Caja, Bancos, Inversiones temporales
                "efectivo", "caja", "banco", "inversiones temporales"
            ],
            
            # Actividades operativas
            CashFlowCategory.OPERATING: [
                "4001", "4002", "4003",  # Ingresos por ventas
                "5001", "5002", "5003",  # Gastos operativos
                "ventas", "servicios", "sueldos", "gastos operativos"
            ],
            
            # Actividades de inversión
            CashFlowCategory.INVESTING: [
                "1201", "1202", "1203",  # Activos fijos
                "1301", "1302",          # Inversiones a largo plazo
                "equipos", "maquinaria", "inversiones", "propiedades"
            ],
            
            # Actividades de financiamiento
            CashFlowCategory.FINANCING: [
                "2101", "2102",  # Préstamos y financiamiento
                "3001", "3002",  # Capital y aportes
                "prestamos", "capital", "aportes", "dividendos"
            ]
        }
        
        categorized_count = 0
        
        for account in uncategorized_accounts:
            category = determine_account_category(account, categorization_rules)
            
            if category:
                # Actualizar categoría
                stmt = update(Account).where(
                    Account.id == account.id
                ).values(cash_flow_category=category)
                
                await session.execute(stmt)
                categorized_count += 1
                
                print(f"Categorizada: {account.code} - {account.name} -> {category.value}")
        
        await session.commit()
        
        print(f"\nTotal de cuentas categorizadas: {categorized_count}")
        print(f"Cuentas pendientes: {len(uncategorized_accounts) - categorized_count}")

def determine_account_category(account: Account, rules: dict) -> CashFlowCategory:
    """Determinar categoría basada en código y nombre de cuenta"""
    
    account_code = account.code.lower()
    account_name = account.name.lower()
    
    for category, patterns in rules.items():
        for pattern in patterns:
            if (pattern in account_code or 
                pattern in account_name or 
                account_code.startswith(pattern)):
                return category
    
    return None

# Ejecutar categorización
if __name__ == "__main__":
    asyncio.run(categorize_existing_accounts())
```

#### Configuración del CashFlowService

```python
# En app/config.py
class CashFlowSettings:
    # Métodos de flujo de efectivo
    DEFAULT_METHOD = "indirect"  # indirect | direct
    
    # Configuración de validación
    ENABLE_CASH_RECONCILIATION = True
    TOLERANCE_THRESHOLD = Decimal('0.01')  # Tolerancia para diferencias
    
    # Configuración de narrativa
    ENABLE_AI_NARRATIVE = True
    NARRATIVE_DETAIL_LEVEL = "medium"  # low | medium | high
    
    # Límites de consulta
    MAX_DATE_RANGE_DAYS = 365
    QUERY_TIMEOUT_SECONDS = 60
    
    # Caché
    CACHE_DURATION_MINUTES = 30
    ENABLE_STATEMENT_CACHE = True
```

#### Validación de Configuración

```python
# validate_cash_flow_setup.py
async def validate_cash_flow_configuration():
    """Validar que el sistema esté correctamente configurado para flujo de efectivo"""
    
    validation_results = {
        "accounts_categorized": False,
        "cash_accounts_identified": False,
        "sample_calculation": False,
        "errors": []
    }
    
    try:
        async with get_async_session() as session:
            # Verificar cuentas categorizadas
            stmt = select(Account).where(Account.cash_flow_category.isnot(None))
            categorized = await session.execute(stmt)
            categorized_count = len(categorized.scalars().all())
            
            if categorized_count > 0:
                validation_results["accounts_categorized"] = True
            else:
                validation_results["errors"].append("No hay cuentas categorizadas para flujo de efectivo")
            
            # Verificar cuentas de efectivo
            cash_stmt = select(Account).where(
                Account.cash_flow_category == CashFlowCategory.CASH_EQUIVALENTS
            )
            cash_accounts = await session.execute(cash_stmt)
            cash_count = len(cash_accounts.scalars().all())
            
            if cash_count > 0:
                validation_results["cash_accounts_identified"] = True
            else:
                validation_results["errors"].append("No se identificaron cuentas de efectivo")
            
            # Prueba de cálculo
            from app.services.cash_flow_service import CashFlowService
            from datetime import date, timedelta
            
            cash_service = CashFlowService(session)
            
            try:
                test_statement = await cash_service.generate_cash_flow_statement(
                    start_date=date.today() - timedelta(days=30),
                    end_date=date.today(),
                    method="indirect"
                )
                
                validation_results["sample_calculation"] = True
                
            except Exception as e:
                validation_results["errors"].append(f"Error en cálculo de prueba: {str(e)}")
    
    except Exception as e:
        validation_results["errors"].append(f"Error de conexión: {str(e)}")
    
    # Generar reporte de validación
    print("=== VALIDACIÓN DE CONFIGURACIÓN DE FLUJO DE EFECTIVO ===")
    print(f"✅ Cuentas categorizadas: {validation_results['accounts_categorized']}")
    print(f"✅ Cuentas de efectivo identificadas: {validation_results['cash_accounts_identified']}")
    print(f"✅ Cálculo de prueba exitoso: {validation_results['sample_calculation']}")
    
    if validation_results["errors"]:
        print("\n❌ ERRORES ENCONTRADOS:")
        for error in validation_results["errors"]:
            print(f"• {error}")
        return False
    
    print("\n🎉 Configuración válida - Sistema listo para generar flujos de efectivo")
    return True

# Ejecutar validación
if __name__ == "__main__":
    asyncio.run(validate_cash_flow_configuration())
```

### 📊 **Monitoreo y Métricas**

#### Dashboard de Administración

```python
# admin_dashboard.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_admin_user

admin_router = APIRouter(prefix="/admin/reports")

@admin_router.get("/metrics")
async def get_report_metrics(
    admin_user = Depends(get_current_admin_user)
):
    """Obtener métricas del sistema de reportes"""
    
    return {
        "performance": {
            "avg_response_time": "1.2s",
            "reports_generated_today": 142,
            "cache_hit_rate": "78%",
            "active_sessions": 23
        },
        "usage": {
            "most_requested_report": "balance_sheet",
            "peak_hours": "09:00-11:00",
            "total_exports_month": 1247,
            "storage_used": "2.3 GB"
        },
        "health": {
            "database_status": "healthy",
            "cache_status": "healthy",
            "last_backup": "2025-06-10 02:00:00",
            "system_load": "normal"
        }
    }

@admin_router.get("/active-reports")
async def get_active_reports(
    admin_user = Depends(get_current_admin_user)
):
    """Ver reportes en proceso"""
    
    return {
        "running_reports": [
            {
                "report_id": "rpt_001",
                "type": "balance_sheet",
                "user": "accountant@company.com",
                "started_at": "2025-06-10 14:30:00",
                "progress": "85%",
                "estimated_completion": "2025-06-10 14:32:15"
            }
        ],
        "queued_reports": [],
        "failed_reports": []
    }
```

#### Alertas y Notificaciones

```python
# monitoring.py
import logging
from datetime import datetime, timedelta
from app.core.notifications import NotificationService

class ReportMonitoring:
    def __init__(self):
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
    
    async def check_system_health(self):
        """Verificar salud del sistema"""
        
        alerts = []
        
        # Verificar rendimiento
        avg_response_time = await self.get_avg_response_time()
        if avg_response_time > 5.0:
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": f"Tiempo de respuesta alto: {avg_response_time}s"
            })
        
        # Verificar uso de memoria
        cache_usage = await self.get_cache_usage()
        if cache_usage > 90:
            alerts.append({
                "type": "memory",
                "severity": "critical", 
                "message": f"Uso de caché crítico: {cache_usage}%"
            })
        
        # Verificar reportes fallidos
        failed_reports = await self.get_failed_reports_count()
        if failed_reports > 10:
            alerts.append({
                "type": "reliability",
                "severity": "warning",
                "message": f"Reportes fallidos: {failed_reports} en la última hora"
            })
        
        # Enviar alertas
        for alert in alerts:
            await self.notification_service.send_alert(alert)
        
        return alerts
```

### 🔒 **Seguridad y Auditoría**

#### Configuración de Seguridad

```python
# security_config.py
SECURITY_CONFIG = {
    "authentication": {
        "require_mfa": True,
        "session_timeout": 3600,  # 1 hora
        "max_login_attempts": 3,
        "lockout_duration": 300   # 5 minutos
    },
    "authorization": {
        "rbac_enabled": True,
        "permission_cache_ttl": 1800,
        "require_explicit_permissions": True
    },
    "audit": {
        "log_all_requests": True,
        "log_sensitive_data": False,
        "retention_days": 90,
        "real_time_monitoring": True
    },
    "rate_limiting": {
        "enabled": True,
        "default_limit": 100,  # requests per minute
        "burst_limit": 20,
        "whitelist_ips": ["10.0.0.0/8"]
    }
}
```

#### Auditoría de Reportes

```sql
-- Tabla de auditoría para reportes
CREATE TABLE report_audit_log (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    parameters JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para consultas de auditoría
CREATE INDEX idx_report_audit_user_date 
ON report_audit_log(user_id, created_at);

CREATE INDEX idx_report_audit_type_date 
ON report_audit_log(report_type, created_at);
```

### 🚀 **Optimización de Rendimiento**

#### Configuración de Caché

```python
# cache_config.py
import redis
from app.core.config import settings

class ReportCache:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            settings.REPORTS_CACHE_REDIS_URL,
            decode_responses=True
        )
    
    async def get_cache_key(self, report_type: str, params: dict) -> str:
        """Generar clave de caché para reporte"""
        
        # Crear hash único basado en parámetros
        import hashlib
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        return f"report:{report_type}:{param_hash}"
    
    async def cache_report(self, key: str, data: dict, ttl: int = 3600):
        """Guardar reporte en caché"""
        
        await self.redis_client.setex(
            key, ttl, json.dumps(data, default=str)
        )
    
    async def get_cached_report(self, key: str) -> dict:
        """Obtener reporte del caché"""
        
        data = await self.redis_client.get(key)
        return json.loads(data) if data else None
```

#### Pool de Conexiones

```python
# database_pool.py
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import QueuePool

class DatabasePool:
    def __init__(self):
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=20,           # Conexiones permanentes
            max_overflow=30,        # Conexiones adicionales
            pool_pre_ping=True,     # Verificar conexiones
            pool_recycle=3600,      # Reciclar cada hora
            echo=settings.DEBUG_SQL
        )
```

### 🔧 **Mantenimiento y Respaldo**

#### Scripts de Mantenimiento

```bash
#!/bin/bash
# maintenance.sh - Script de mantenimiento diario

echo "Iniciando mantenimiento del sistema de reportes..."

# Limpiar caché expirado
redis-cli FLUSHDB

# Optimizar base de datos
psql -d contable_db -c "VACUUM ANALYZE;"

# Limpiar archivos de exportación antiguos
find /tmp/reports -name "*.pdf" -mtime +7 -delete
find /tmp/reports -name "*.xlsx" -mtime +7 -delete

# Rotar logs
logrotate /etc/logrotate.d/reports

# Verificar integridad
python -c "
import asyncio
from app.services.report_service import ReportService

async def check_integrity():
    service = ReportService()
    result = await service.check_accounting_integrity()
    if not result['overall_integrity']:
        print('ALERTA: Integridad contable comprometida')
        exit(1)

asyncio.run(check_integrity())
"

echo "Mantenimiento completado"
```

#### Respaldo de Configuraciones

```python
# backup_config.py
import json
import os
from datetime import datetime

class ConfigBackup:
    def __init__(self, backup_path: str = "/backups/reports"):
        self.backup_path = backup_path
        os.makedirs(backup_path, exist_ok=True)
    
    async def backup_configuration(self):
        """Respaldar configuración del sistema"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        config_data = {
            "database_config": await self.get_db_config(),
            "cache_config": await self.get_cache_config(),
            "security_config": await self.get_security_config(),
            "user_permissions": await self.get_user_permissions(),
            "system_settings": await self.get_system_settings()
        }
        
        backup_file = f"{self.backup_path}/config_backup_{timestamp}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        return backup_file
```

## Resolución de Problemas

### 🚨 **Problemas Comunes**

#### Reportes Lentos

**Síntomas:**
- Tiempo de respuesta > 10 segundos
- Timeouts frecuentes
- Alta utilización de CPU

**Soluciones:**
1. Verificar índices de base de datos
2. Optimizar consultas SQL
3. Aumentar pool de conexiones
4. Implementar paginación
5. Usar caché para reportes frecuentes

```sql
-- Consultar reportes lentos
SELECT 
    query,
    mean_exec_time,
    calls
FROM pg_stat_statements 
WHERE query LIKE '%report%'
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

#### Errores de Memoria

**Síntomas:**
- OutOfMemory exceptions
- Procesos terminados abruptamente
- Sistema lento

**Soluciones:**
1. Aumentar límites de memoria
2. Implementar streaming para reportes grandes
3. Optimizar algoritmos de procesamiento
4. Usar procesamiento por lotes

```python
# Procesamiento por lotes para reportes grandes
async def generate_large_report_streaming(params):
    batch_size = 1000
    offset = 0
    
    while True:
        batch = await get_report_data_batch(
            params, limit=batch_size, offset=offset
        )
        
        if not batch:
            break
            
        yield process_batch(batch)
        offset += batch_size
```

### 📞 **Soporte y Contacto**

#### Canales de Soporte

- **Email Técnico**: soporte-reportes@empresa.com
- **Slack**: #soporte-contabilidad
- **Documentación**: `/docs/reports`
- **Tickets**: Jira REPORTS project

#### Información para Reportes de Errores

Al reportar un error, incluir:

1. **Versión del sistema**
2. **Timestamp del error**
3. **Parámetros del reporte**
4. **Logs relevantes**
5. **Comportamiento esperado vs actual**

```python
# Template para reporte de errores
ERROR_REPORT_TEMPLATE = {
    "timestamp": "2025-06-10T14:30:00Z",
    "version": "1.2.3",
    "endpoint": "/api/v1/reports/balance-sheet",
    "parameters": {
        "as_of_date": "2025-06-10",
        "company_name": "Example Corp"
    },
    "error_message": "Connection timeout",
    "stack_trace": "...",
    "user_id": "user123",
    "session_id": "sess456"
}
```

## Mejores Prácticas

### ✅ **Recomendaciones Operativas**

1. **Monitoreo Continuo**
   - Configurar alertas proactivas
   - Revisar métricas diariamente
   - Mantener logs actualizados

2. **Seguridad**
   - Auditar accesos regularmente
   - Actualizar permisos según cambios organizacionales
   - Revisar logs de seguridad

3. **Rendimiento**
   - Mantener estadísticas de base de datos
   - Optimizar consultas frecuentes
   - Monitorear uso de recursos

4. **Respaldos**
   - Respaldar configuraciones semanalmente
   - Probar restauración mensualmente
   - Documentar procedimientos

### 📚 **Recursos Adicionales**

- [📖 Guía de Instalación](./installation-guide.md)
- [📖 Manual de Usuario](./user-manual.md)
- [📖 API Reference](./api-reference.md)
- [📖 Changelog](./changelog.md)

---

*Última actualización: Junio 10, 2025*
*Versión del documento: 1.0.0*
