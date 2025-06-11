# Guía de Uso del Sistema de Exportación

## Introducción

Esta guía proporciona ejemplos prácticos y casos de uso comunes para el sistema de exportación de datos del API Contable. El sistema permite exportar cualquier tabla en múltiples formatos con filtrado automático de datos sensibles.

## Casos de Uso Comunes

### 1. Exportación Simple de Registros Específicos

#### Exportar usuarios específicos en CSV
```bash
curl -X POST "http://localhost:8000/api/v1/export/" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table": "users",
    "format": "csv",
    "ids": [1, 2, 3, 4, 5]
  }'
```

**Respuesta:**
```json
{
  "file_name": "users_20241210_143022.csv",
  "file_content": "id,email,first_name,last_name,is_active,role,created_at\n1,admin@example.com,Admin,User,true,ADMIN,2024-01-15T10:30:00\n...",
  "content_type": "text/csv",
  "success": true,
  "message": "Exportación exitosa: 5 registros"
}
```

#### Exportar cuentas contables en Excel
```bash
curl -X POST "http://localhost:8000/api/v1/export/" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table": "accounts",
    "format": "xlsx",
    "ids": [100, 110, 120, 200, 210]
  }'
```

### 2. Exportación con Filtros Avanzados

#### Exportar asientos contables del año actual
```bash
curl -X POST "http://localhost:8000/api/v1/export/advanced" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "journal_entries",
    "export_format": "xlsx",
    "filters": {
      "date_from": "2024-01-01",
      "date_to": "2024-12-31",
      "active_only": true
    },
    "file_name": "asientos_2024"
  }'
```

#### Exportar últimas 100 sesiones de usuario
```bash
curl -X POST "http://localhost:8000/api/v1/export/advanced" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "user_sessions",
    "export_format": "json",
    "filters": {
      "limit": 100,
      "offset": 0
    }
  }'
```

### 3. Consulta de Información de Tablas

#### Listar todas las tablas disponibles
```bash
curl -X GET "http://localhost:8000/api/v1/export/tables/" \
  -H "Authorization: Bearer your_jwt_token"
```

#### Obtener esquema detallado de tabla específica
```bash
curl -X GET "http://localhost:8000/api/v1/export/tables/users" \
  -H "Authorization: Bearer your_jwt_token"
```

**Respuesta:**
```json
{
  "table_name": "users",
  "display_name": "Usuarios",
  "description": "Tabla Usuarios",
  "available_columns": [
    {
      "name": "id",
      "data_type": "number",
      "include": true
    },
    {
      "name": "email",
      "data_type": "string",
      "include": true
    }
  ],
  "total_records": 150,
  "sample_data": [
    {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John"
    }
  ]
}
```

### 4. Exportaciones Rápidas (Endpoints de Conveniencia)

#### Exportar usuarios usando endpoint específico
```bash
curl -X POST "http://localhost:8000/api/v1/export/users/" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "ids": [1, 2, 3]
  }'
```

#### Exportar cuentas contables
```bash
curl -X POST "http://localhost:8000/api/v1/export/accounts/" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "ids": [100, 110, 120]
  }'
```

## Ejemplos con Código

### Python - Usando requests
```python
import requests
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8000/api/v1"
JWT_TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def export_users_csv(user_ids):
    """Exporta usuarios específicos en formato CSV"""
    url = f"{API_BASE_URL}/export/"
    data = {
        "table": "users",
        "format": "csv",
        "ids": user_ids
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            # Guardar archivo
            filename = result["file_name"]
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(result["file_content"])
            
            print(f"Exportación exitosa: {filename}")
            print(f"Registros exportados: {result['metadata']['exported_records']}")
            return filename
    
    return None

def export_journal_entries_year(year):
    """Exporta asientos contables de un año específico"""
    url = f"{API_BASE_URL}/export/advanced"
    data = {
        "table_name": "journal_entries",
        "export_format": "xlsx",
        "filters": {
            "date_from": f"{year}-01-01",
            "date_to": f"{year}-12-31"
        },
        "file_name": f"asientos_{year}"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            # Para archivos Excel, el contenido viene en base64 o bytes
            filename = result["file_name"]
            content = result["file_content"]
            
            # Si es string, escribir como texto
            if isinstance(content, str):
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # Si son bytes, escribir en modo binario
                with open(filename, 'wb') as f:
                    f.write(content)
            
            return filename
    
    return None

def get_table_info(table_name):
    """Obtiene información de una tabla específica"""
    url = f"{API_BASE_URL}/export/tables/{table_name}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    
    return None

# Ejemplos de uso
if __name__ == "__main__":
    # Exportar usuarios específicos
    user_file = export_users_csv([1, 2, 3, 4, 5])
    if user_file:
        print(f"Usuarios exportados a: {user_file}")
    
    # Exportar asientos del año 2024
    journal_file = export_journal_entries_year(2024)
    if journal_file:
        print(f"Asientos exportados a: {journal_file}")
    
    # Obtener información de tabla de cuentas
    accounts_info = get_table_info("accounts")
    if accounts_info:
        print(f"Tabla: {accounts_info['display_name']}")
        print(f"Total registros: {accounts_info['total_records']}")
        print(f"Columnas disponibles: {len(accounts_info['available_columns'])}")
```

### JavaScript/TypeScript - Usando fetch
```javascript
class ExportService {
    constructor(apiBaseUrl, jwtToken) {
        this.apiBaseUrl = apiBaseUrl;
        this.headers = {
            'Authorization': `Bearer ${jwtToken}`,
            'Content-Type': 'application/json'
        };
    }

    async exportUsers(userIds, format = 'csv') {
        const url = `${this.apiBaseUrl}/export/`;
        const data = {
            table: 'users',
            format: format,
            ids: userIds
        };

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Descargar archivo
                    this.downloadFile(result.file_content, result.file_name, result.content_type);
                    return result;
                }
            }
        } catch (error) {
            console.error('Error en exportación:', error);
        }
        
        return null;
    }

    async exportWithAdvancedFilters(tableName, format, filters) {
        const url = `${this.apiBaseUrl}/export/advanced`;
        const data = {
            table_name: tableName,
            export_format: format,
            filters: filters
        };

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.downloadFile(result.file_content, result.file_name, result.content_type);
                    return result;
                }
            }
        } catch (error) {
            console.error('Error en exportación avanzada:', error);
        }
        
        return null;
    }

    async getTableInfo(tableName) {
        const url = `${this.apiBaseUrl}/export/tables/${tableName}`;

        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: this.headers
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error obteniendo información de tabla:', error);
        }
        
        return null;
    }

    downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}

// Uso del servicio
const exportService = new ExportService('http://localhost:8000/api/v1', 'your_jwt_token');

// Exportar usuarios específicos
exportService.exportUsers([1, 2, 3], 'csv')
    .then(result => {
        if (result) {
            console.log(`Exportación exitosa: ${result.metadata.exported_records} registros`);
        }
    });

// Exportar asientos del año
exportService.exportWithAdvancedFilters('journal_entries', 'xlsx', {
    date_from: '2024-01-01',
    date_to: '2024-12-31',
    active_only: true
})
    .then(result => {
        if (result) {
            console.log(`Asientos exportados: ${result.file_name}`);
        }
    });
```

## Casos de Uso por Rol

### Administrador
```python
# Los administradores pueden exportar todas las tablas
def admin_full_export():
    # Exportar todos los usuarios
    export_users_csv(range(1, 1001))  # Primeros 1000 usuarios
    
    # Exportar todas las cuentas
    export_accounts_excel(get_all_account_ids())
    
    # Exportar logs de auditoría
    export_audit_logs(date_from="2024-01-01", date_to="2024-12-31")
```

### Contador
```python
# Los contadores se enfocan en datos contables
def accountant_exports():
    # Exportar plan de cuentas completo
    export_accounts_excel()
    
    # Exportar asientos del periodo
    export_journal_entries_period("2024-01-01", "2024-03-31")
    
    # Exportar líneas de asientos para análisis
    export_journal_entry_lines()
```

### Usuario de Solo Lectura
```python
# Usuarios de solo lectura pueden exportar datos básicos
def readonly_user_exports():
    # Solo pueden exportar sus propios datos
    export_my_user_data()
    
    # Pueden ver el plan de cuentas público
    export_public_accounts()
```

## Integración con Frontend

### React Component
```jsx
import React, { useState } from 'react';

const ExportComponent = ({ jwtToken }) => {
    const [loading, setLoading] = useState(false);
    const [selectedTable, setSelectedTable] = useState('users');
    const [selectedFormat, setSelectedFormat] = useState('csv');
    const [selectedIds, setSelectedIds] = useState('');

    const handleExport = async () => {
        setLoading(true);
        
        const ids = selectedIds.split(',').map(id => parseInt(id.trim()));
        
        try {
            const response = await fetch('/api/v1/export/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${jwtToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    table: selectedTable,
                    format: selectedFormat,
                    ids: ids
                })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Descargar archivo
                    downloadFile(result.file_content, result.file_name);
                    alert(`Exportación exitosa: ${result.metadata.exported_records} registros`);
                }
            }
        } catch (error) {
            alert('Error en la exportación: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    const downloadFile = (content, filename) => {
        const blob = new Blob([content], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    return (
        <div className="export-component">
            <h3>Exportar Datos</h3>
            
            <div>
                <label>Tabla:</label>
                <select value={selectedTable} onChange={(e) => setSelectedTable(e.target.value)}>
                    <option value="users">Usuarios</option>
                    <option value="accounts">Cuentas</option>
                    <option value="journal_entries">Asientos Contables</option>
                </select>
            </div>

            <div>
                <label>Formato:</label>
                <select value={selectedFormat} onChange={(e) => setSelectedFormat(e.target.value)}>
                    <option value="csv">CSV</option>
                    <option value="json">JSON</option>
                    <option value="xlsx">Excel</option>
                </select>
            </div>

            <div>
                <label>IDs (separados por coma):</label>
                <input 
                    type="text" 
                    value={selectedIds} 
                    onChange={(e) => setSelectedIds(e.target.value)}
                    placeholder="1, 2, 3, 4, 5"
                />
            </div>

            <button onClick={handleExport} disabled={loading}>
                {loading ? 'Exportando...' : 'Exportar'}
            </button>
        </div>
    );
};

export default ExportComponent;
```

## Mejores Prácticas

### 1. Manejo de Archivos Grandes
```python
def export_large_dataset(table_name, total_records, batch_size=1000):
    """Exporta grandes volúmenes de datos en lotes"""
    all_files = []
    
    for offset in range(0, total_records, batch_size):
        filters = {
            "offset": offset,
            "limit": batch_size
        }
        
        result = export_with_filters(table_name, "csv", filters)
        if result:
            all_files.append(result["file_name"])
    
    # Combinar archivos si es necesario
    return combine_csv_files(all_files)
```

### 2. Cache de Metadatos
```python
import redis
import json

def get_table_info_cached(table_name):
    """Obtiene información de tabla con cache"""
    cache_key = f"table_info:{table_name}"
    
    # Intentar obtener del cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Si no está en cache, obtener de API
    info = get_table_info(table_name)
    if info:
        # Guardar en cache por 1 hora
        redis_client.setex(cache_key, 3600, json.dumps(info))
    
    return info
```

### 3. Validación de Entrada
```python
def validate_export_request(table, format, ids):
    """Valida parámetros antes de enviar request"""
    valid_tables = ["users", "accounts", "journal_entries", "journal_entry_lines"]
    valid_formats = ["csv", "json", "xlsx"]
    
    if table not in valid_tables:
        raise ValueError(f"Tabla inválida: {table}")
    
    if format not in valid_formats:
        raise ValueError(f"Formato inválido: {format}")
    
    if not ids or len(ids) == 0:
        raise ValueError("Lista de IDs no puede estar vacía")
    
    if len(ids) > 10000:
        raise ValueError("Máximo 10,000 IDs por solicitud")
    
    return True
```

## Troubleshooting

### Problemas Comunes

#### Error 401 - No Autorizado
```python
# Verificar que el token JWT sea válido
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

# El token puede haber expirado
if response.status_code == 401:
    print("Token expirado o inválido. Renovar autenticación.")
```

#### Error 422 - Datos Inválidos
```python
# Validar parámetros antes de enviar
try:
    validate_export_request(table, format, ids)
except ValueError as e:
    print(f"Error de validación: {e}")
```

#### Export Vacío
```python
# Verificar que los IDs existan
table_info = get_table_info(table_name)
print(f"Total de registros en tabla: {table_info['total_records']}")

# Verificar que no todos los campos sean sensibles
print(f"Columnas disponibles: {[col['name'] for col in table_info['available_columns']]}")
```

### Debug y Logging
```python
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def export_with_debug(table, format, ids):
    logger.debug(f"Iniciando exportación: tabla={table}, formato={format}, ids={len(ids)}")
    
    result = export_data(table, format, ids)
    
    if result:
        logger.info(f"Exportación exitosa: {result['metadata']['exported_records']} registros")
        logger.debug(f"Columnas exportadas: {result['metadata']['columns_exported']}")
    else:
        logger.error("Exportación falló")
    
    return result
```
