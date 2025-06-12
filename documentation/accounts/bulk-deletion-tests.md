# Tests para Eliminación Múltiple de Cuentas

## Descripción General

Esta documentación proporciona ejemplos y casos de prueba para los nuevos endpoints de eliminación múltiple de cuentas, incluyendo validaciones y escenarios de error.

## Configuración de Pruebas

### Datos de Prueba

```python
# Cuentas de ejemplo para testing
test_accounts = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "code": "TEST001",
        "name": "Cuenta Test Sin Movimientos",
        "account_type": "ACTIVO",
        "balance": 0,
        "has_movements": False,
        "has_children": False
    },
    {
        "id": "22222222-2222-2222-2222-222222222222", 
        "code": "TEST002",
        "name": "Cuenta Test Con Movimientos",
        "account_type": "ACTIVO",
        "balance": 1500.00,
        "has_movements": True,
        "has_children": False
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "code": "TEST003", 
        "name": "Cuenta Test Con Hijas",
        "account_type": "ACTIVO",
        "balance": 0,
        "has_movements": False,
        "has_children": True
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "code": "1",
        "name": "Cuenta Sistema",
        "account_type": "ACTIVO",
        "balance": 0,
        "has_movements": False,
        "has_children": True
    }
]
```

### Headers de Autenticación

```python
admin_headers = {
    "Authorization": "Bearer <admin_jwt_token>",
    "Content-Type": "application/json"
}

non_admin_headers = {
    "Authorization": "Bearer <user_jwt_token>",
    "Content-Type": "application/json"
}
```

## Tests de Validación Previa

### Test 1: Validación Exitosa de Cuentas Mixtas

```python
def test_validate_deletion_mixed_accounts():
    """Test validación de cuentas con diferentes estados"""
    
    # Request
    url = "/api/v1/accounts/validate-deletion"
    payload = [
        "11111111-1111-1111-1111-111111111111",  # Sin problemas
        "22222222-2222-2222-2222-222222222222",  # Con movimientos
        "33333333-3333-3333-3333-333333333333"   # Con hijas
    ]
    
    response = requests.post(url, json=payload, headers=admin_headers)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    # Cuenta sin problemas
    assert data[0]["can_delete"] == True
    assert len(data[0]["blocking_reasons"]) == 0
    
    # Cuenta con movimientos
    assert data[1]["can_delete"] == False
    assert "movimientos contables" in data[1]["blocking_reasons"][0]
    assert data[1]["dependencies"]["movements_count"] > 0
    
    # Cuenta con hijas
    assert data[2]["can_delete"] == False
    assert "cuentas hijas" in data[2]["blocking_reasons"][0]
    assert data[2]["dependencies"]["children_count"] > 0
```

### Test 2: Validación de Cuenta Inexistente

```python
def test_validate_deletion_nonexistent_account():
    """Test validación de cuenta que no existe"""
    
    url = "/api/v1/accounts/validate-deletion"
    payload = ["99999999-9999-9999-9999-999999999999"]
    
    response = requests.post(url, json=payload, headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data[0]["can_delete"] == False
    assert "Cuenta no encontrada" in data[0]["blocking_reasons"]
```

### Test 3: Validación Sin Permisos de Admin

```python
def test_validate_deletion_insufficient_permissions():
    """Test validación sin permisos de administrador"""
    
    url = "/api/v1/accounts/validate-deletion"
    payload = ["11111111-1111-1111-1111-111111111111"]
    
    response = requests.post(url, json=payload, headers=non_admin_headers)
    
    assert response.status_code == 403
    assert "insuficientes" in response.json()["detail"].lower()
```

## Tests de Eliminación Múltiple

### Test 4: Eliminación Exitosa

```python
def test_bulk_delete_success():
    """Test eliminación exitosa de cuentas válidas"""
    
    url = "/api/v1/accounts/bulk-delete"
    payload = {
        "account_ids": ["11111111-1111-1111-1111-111111111111"],
        "force_delete": False,
        "delete_reason": "Test de eliminación unitaria"
    }
    
    response = requests.post(url, json=payload, headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_requested"] == 1
    assert len(data["successfully_deleted"]) == 1
    assert len(data["failed_to_delete"]) == 0
    assert data["success_rate"] == 100.0
    assert "Test de eliminación unitaria" in data["warnings"]
```

### Test 5: Eliminación con Errores de Validación

```python
def test_bulk_delete_with_validation_errors():
    """Test eliminación de cuentas con problemas de validación"""
    
    url = "/api/v1/accounts/bulk-delete"
    payload = {
        "account_ids": [
            "22222222-2222-2222-2222-222222222222",  # Con movimientos
            "33333333-3333-3333-3333-333333333333"   # Con hijas
        ],
        "force_delete": False,
        "delete_reason": "Test de eliminación con errores"
    }
    
    response = requests.post(url, json=payload, headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_requested"] == 2
    assert len(data["successfully_deleted"]) == 0
    assert len(data["failed_to_delete"]) == 2
    assert data["success_rate"] == 0.0
    
    # Verificar razones específicas
    failed_reasons = [item["reason"] for item in data["failed_to_delete"]]
    assert any("movimientos" in reason for reason in failed_reasons)
    assert any("hijas" in reason for reason in failed_reasons)
```

### Test 6: Eliminación con force_delete

```python
def test_bulk_delete_with_force():
    """Test eliminación con force_delete habilitado"""
    
    # Primero crear una cuenta con saldo pero sin movimientos críticos
    test_account_id = create_test_account_with_balance()
    
    url = "/api/v1/accounts/bulk-delete"
    payload = {
        "account_ids": [test_account_id],
        "force_delete": True,
        "delete_reason": "Test forzado de eliminación"
    }
    
    response = requests.post(url, json=payload, headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["successfully_deleted"]) == 1
    assert "saldo pendiente" in " ".join(data["warnings"])
```

### Test 7: Eliminación de Cuenta de Sistema

```python
def test_bulk_delete_system_account():
    """Test intentar eliminar cuenta de sistema"""
    
    url = "/api/v1/accounts/bulk-delete"
    payload = {
        "account_ids": ["44444444-4444-4444-4444-444444444444"],  # Código "1"
        "force_delete": True,
        "delete_reason": "Test eliminación cuenta sistema"
    }
    
    response = requests.post(url, json=payload, headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["successfully_deleted"]) == 0
    assert len(data["failed_to_delete"]) == 1
    assert "cuenta de sistema" in data["failed_to_delete"][0]["reason"]
```

### Test 8: Validación de Límites

```python
def test_bulk_delete_limits():
    """Test validación de límites de cuentas por operación"""
    
    # Generar más de 100 IDs
    account_ids = [str(uuid.uuid4()) for _ in range(101)]
    
    url = "/api/v1/accounts/bulk-delete"
    payload = {
        "account_ids": account_ids,
        "force_delete": False,
        "delete_reason": "Test de límites"
    }
    
    response = requests.post(url, json=payload, headers=admin_headers)
    
    assert response.status_code == 422  # Validation error
    error_details = response.json()["detail"]
    assert any("max_length" in str(error) for error in error_details)
```

### Test 9: IDs Duplicados

```python
def test_bulk_delete_duplicate_ids():
    """Test validación de IDs duplicados"""
    
    duplicate_id = "11111111-1111-1111-1111-111111111111"
    
    url = "/api/v1/accounts/bulk-delete"
    payload = {
        "account_ids": [duplicate_id, duplicate_id],
        "force_delete": False,
        "delete_reason": "Test IDs duplicados"
    }
    
    response = requests.post(url, json=payload, headers=admin_headers)
    
    assert response.status_code == 422
    error_details = response.json()["detail"]
    assert "duplicados" in str(error_details)
```

## Tests de Integración

### Test 10: Flujo Completo de Validación + Eliminación

```python
def test_complete_validation_deletion_flow():
    """Test flujo completo: validación seguida de eliminación"""
    
    # Crear cuentas de prueba
    deletable_accounts = create_deletable_test_accounts(3)
    problematic_accounts = create_problematic_test_accounts(2)
    
    all_account_ids = deletable_accounts + problematic_accounts
    
    # Paso 1: Validación previa
    validation_response = requests.post(
        "/api/v1/accounts/validate-deletion",
        json=all_account_ids,
        headers=admin_headers
    )
    
    assert validation_response.status_code == 200
    validations = validation_response.json()
    
    # Filtrar solo las cuentas que pueden eliminarse
    deletable_ids = [
        v["account_id"] for v in validations 
        if v["can_delete"]
    ]
    
    # Paso 2: Eliminación de cuentas válidas
    delete_response = requests.post(
        "/api/v1/accounts/bulk-delete",
        json={
            "account_ids": deletable_ids,
            "force_delete": False,
            "delete_reason": "Flujo completo de testing"
        },
        headers=admin_headers
    )
    
    assert delete_response.status_code == 200
    delete_result = delete_response.json()
    
    # Verificaciones finales
    assert len(delete_result["successfully_deleted"]) == len(deletable_ids)
    assert delete_result["success_rate"] == 100.0
```

## Tests de Performance

### Test 11: Eliminación de Lote Grande

```python
def test_bulk_delete_large_batch():
    """Test performance con lote grande de cuentas"""
    
    # Crear 50 cuentas eliminables
    account_ids = create_deletable_test_accounts(50)
    
    start_time = time.time()
    
    response = requests.post(
        "/api/v1/accounts/bulk-delete",
        json={
            "account_ids": account_ids,
            "force_delete": False,
            "delete_reason": "Test performance lote grande"
        },
        headers=admin_headers
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    assert response.status_code == 200
    assert execution_time < 30  # Menos de 30 segundos
    
    data = response.json()
    assert data["success_rate"] == 100.0
```

## Tests de Error Handling

### Test 12: Manejo de Errores de BD

```python
def test_bulk_delete_database_error():
    """Test manejo de errores de base de datos"""
    
    # Simular error de BD (requiere mock en entorno de testing)
    with mock_database_error():
        response = requests.post(
            "/api/v1/accounts/bulk-delete",
            json={
                "account_ids": ["11111111-1111-1111-1111-111111111111"],
                "force_delete": False,
                "delete_reason": "Test error BD"
            },
            headers=admin_headers
        )
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
```

### Test 13: Timeout de Operación

```python
def test_bulk_delete_timeout():
    """Test timeout en operaciones largas"""
    
    # Simular operación que excede timeout
    with mock_slow_operation():
        response = requests.post(
            "/api/v1/accounts/bulk-delete",
            json={
                "account_ids": create_deletable_test_accounts(100),
                "force_delete": False,
                "delete_reason": "Test timeout"
            },
            headers=admin_headers,
            timeout=30
        )
        
        # Debería manejar timeout gracefully
        assert response.status_code in [200, 408, 504]
```

## Utilidades de Testing

### Funciones Helper

```python
def create_deletable_test_accounts(count: int) -> List[str]:
    """Crear cuentas que pueden eliminarse sin problemas"""
    accounts = []
    for i in range(count):
        account_data = {
            "code": f"TEST{1000+i}",
            "name": f"Cuenta Test Eliminable {i+1}",
            "account_type": "ACTIVO",
            "allows_movements": True,
            "is_active": True
        }
        response = requests.post(
            "/api/v1/accounts/",
            json=account_data,
            headers=admin_headers
        )
        accounts.append(response.json()["id"])
    return accounts

def create_problematic_test_accounts(count: int) -> List[str]:
    """Crear cuentas con problemas que impiden eliminación"""
    accounts = []
    for i in range(count):
        # Crear cuenta
        account_data = {
            "code": f"PROB{1000+i}",
            "name": f"Cuenta Problemática {i+1}",
            "account_type": "ACTIVO"
        }
        response = requests.post("/api/v1/accounts/", json=account_data, headers=admin_headers)
        account_id = response.json()["id"]
        
        # Agregar movimientos para hacer problemática
        add_test_movements(account_id)
        accounts.append(account_id)
    return accounts

def create_test_account_with_balance() -> str:
    """Crear cuenta con saldo pero sin movimientos críticos"""
    account_data = {
        "code": "BALANCE001",
        "name": "Cuenta Con Saldo",
        "account_type": "ACTIVO",
        "balance": 500.00
    }
    response = requests.post("/api/v1/accounts/", json=account_data, headers=admin_headers)
    return response.json()["id"]

def cleanup_test_accounts(account_ids: List[str]):
    """Limpiar cuentas de prueba después de tests"""
    for account_id in account_ids:
        try:
            requests.delete(f"/api/v1/accounts/{account_id}", headers=admin_headers)
        except:
            pass  # Ignorar errores de limpieza
```

### Fixtures de Pytest

```python
@pytest.fixture
def deletable_accounts():
    """Fixture para cuentas eliminables"""
    account_ids = create_deletable_test_accounts(3)
    yield account_ids
    cleanup_test_accounts(account_ids)

@pytest.fixture
def problematic_accounts():
    """Fixture para cuentas problemáticas"""
    account_ids = create_problematic_test_accounts(2)
    yield account_ids
    cleanup_test_accounts(account_ids)

@pytest.fixture
def admin_client():
    """Cliente HTTP con permisos de admin"""
    return TestClient(app, headers=admin_headers)
```

## Ejecución de Tests

### Comando de Ejecución

```bash
# Ejecutar todos los tests de eliminación múltiple
pytest tests/test_bulk_account_deletion.py -v

# Ejecutar test específico
pytest tests/test_bulk_account_deletion.py::test_bulk_delete_success -v

# Ejecutar con coverage
pytest tests/test_bulk_account_deletion.py --cov=app.services.account_service --cov-report=html
```

### Variables de Entorno para Testing

```bash
# .env.test
DATABASE_URL=postgresql://test_user:test_pass@localhost/test_db
JWT_SECRET_KEY=test_secret_key_for_jwt
TESTING=true
LOG_LEVEL=DEBUG
```

## Checklist de Testing

### Pre-requisitos
- [ ] Base de datos de testing configurada
- [ ] Usuarios de prueba creados (admin y no-admin)
- [ ] Tokens JWT válidos generados
- [ ] Datos de prueba inicializados

### Tests Básicos
- [ ] Validación previa exitosa
- [ ] Eliminación simple exitosa
- [ ] Manejo de cuentas inexistentes
- [ ] Validación de permisos de admin

### Tests de Validación
- [ ] Cuentas con movimientos
- [ ] Cuentas con hijas
- [ ] Cuentas de sistema
- [ ] Límites de cantidad (100 máximo)
- [ ] IDs duplicados

### Tests de Funcionalidad Avanzada
- [ ] Parámetro force_delete
- [ ] Documentación con delete_reason
- [ ] Procesamiento de lotes mixtos
- [ ] Flujo completo validación + eliminación

### Tests de Robustez
- [ ] Performance con lotes grandes
- [ ] Manejo de errores de BD
- [ ] Timeout de operaciones
- [ ] Recuperación de errores parciales

### Tests de Integración
- [ ] Impacto en otros módulos
- [ ] Verificación de integridad post-eliminación
- [ ] Logging y auditoría
- [ ] Notificaciones a sistemas externos
