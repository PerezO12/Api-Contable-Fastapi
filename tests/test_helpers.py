"""
Utilities para tests de integración
"""
import uuid
from typing import Dict, Any, List, Optional
from httpx import AsyncClient
from datetime import date, timedelta


class TestHelpers:
    """Helpers para facilitar la escritura de tests"""
    @staticmethod
    async def create_test_account(
        client: AsyncClient, 
        auth_headers: Dict[str, str], 
        code: Optional[str] = None,
        name: Optional[str] = None,
        account_type: str = "ACTIVO",
        category: str = "ACTIVO_CORRIENTE"
    ) -> Dict[str, Any]:
        """Helper para crear una cuenta de prueba"""
        account_data = {
            "code": code or f"TEST-{uuid.uuid4().hex[:6].upper()}",
            "name": name or f"Cuenta Test {uuid.uuid4().hex[:8]}",
            "account_type": account_type,
            "category": category,
            "description": "Cuenta creada para testing",
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/accounts/",
            json=account_data,
            headers=auth_headers
        )
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create test account: {response.status_code} - {response.text}")

    @staticmethod
    async def create_test_journal_entry(
        client: AsyncClient,
        auth_headers: Dict[str, str],
        account_ids: List[str],
        amounts: Optional[List[float]] = None,
        reference: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Helper para crear un asiento contable de prueba"""
        if len(account_ids) < 2:
            raise ValueError("Se necesitan al menos 2 cuentas para crear un asiento")
        
        if amounts is None:
            amounts = [1000.00, 1000.00]  # Balance básico
        
        if len(amounts) != len(account_ids):
            raise ValueError("El número de montos debe coincidir con el número de cuentas")
        
        line_items = []
        total_amount = sum(amounts[:len(amounts)//2])  # Primera mitad son débitos
        
        # Primera mitad de cuentas como débitos
        for i in range(len(account_ids)//2):
            line_items.append({
                "account_id": account_ids[i],
                "description": f"Débito {i+1}",
                "debit_amount": str(amounts[i]),
                "credit_amount": "0.00"
            })
        
        # Segunda mitad como créditos
        for i in range(len(account_ids)//2, len(account_ids)):
            line_items.append({
                "account_id": account_ids[i],
                "description": f"Crédito {i+1}",
                "debit_amount": "0.00",
                "credit_amount": str(amounts[i])
            })
        
        entry_data = {
            "reference": reference or f"TEST-{uuid.uuid4().hex[:8].upper()}",
            "description": description or "Asiento de prueba generado automáticamente",
            "entry_date": date.today().isoformat(),            "line_items": line_items
        }
        
        response = await client.post(
            "/api/v1/journal-entries/",
            json=entry_data,
            headers=auth_headers
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create test journal entry: {response.status_code} - {response.text}")

    @staticmethod
    async def create_test_user(
        client: AsyncClient,
        auth_headers: Dict[str, str],
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "CONTADOR"    ) -> Dict[str, Any]:
        """Helper para crear un usuario de prueba"""
        user_data = {
            "email": email or f"test-{uuid.uuid4().hex[:8]}@test.com",
            "full_name": full_name or f"Test User {uuid.uuid4().hex[:8]}",
            "role": role,
            "notes": "Usuario creado para testing",
            "temporary_password": "Test123456!"
        }
        
        response = await client.post(
            "/api/v1/users/admin/create-user",
            json=user_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to create test user: {response.status_code} - {response.text}")

    @staticmethod
    async def approve_and_post_journal_entry(
        client: AsyncClient,
        auth_headers: Dict[str, str],
        entry_id: str
    ) -> Dict[str, Any]:
        """Helper para aprobar y contabilizar un asiento"""
        # Aprobar
        approve_response = await client.post(
            f"/api/v1/journal-entries/{entry_id}/approve",
            headers=auth_headers
        )
        
        if approve_response.status_code != 200:
            raise Exception(f"Failed to approve entry: {approve_response.status_code}")
        
        # Contabilizar
        post_response = await client.post(
            f"/api/v1/journal-entries/{entry_id}/post",
            headers=auth_headers
        )
        
        if post_response.status_code != 200:
            raise Exception(f"Failed to post entry: {post_response.status_code}")
        
        return post_response.json()

    @staticmethod
    def generate_date_range(days_back: int = 30) -> tuple[str, str]:
        """Helper para generar un rango de fechas para reportes"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        return start_date.isoformat(), end_date.isoformat()

    @staticmethod
    def assert_response_structure(data: Dict[str, Any], required_fields: List[str]):
        """Helper para verificar la estructura de una respuesta"""
        for field in required_fields:
            assert field in data, f"Campo requerido '{field}' no encontrado en la respuesta"

    @staticmethod
    def assert_pagination_structure(data: Dict[str, Any]):
        """Helper para verificar estructura de respuesta paginada"""
        required_fields = ["items", "total", "skip", "limit"]
        TestHelpers.assert_response_structure(data, required_fields)
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["skip"], int)
        assert isinstance(data["limit"], int)

    @staticmethod
    def assert_account_structure(account: Dict[str, Any]):
        """Helper para verificar estructura de cuenta"""
        required_fields = [
            "id", "code", "name", "account_type", "category", 
            "balance", "is_active", "created_at"
        ]
        TestHelpers.assert_response_structure(account, required_fields)

    @staticmethod
    def assert_journal_entry_structure(entry: Dict[str, Any]):
        """Helper para verificar estructura de asiento contable"""
        required_fields = [
            "id", "entry_number", "reference", "description", 
            "entry_date", "status", "line_items", "total_debit", 
            "total_credit", "created_at"
        ]
        TestHelpers.assert_response_structure(entry, required_fields)
        assert isinstance(entry["line_items"], list)

    @staticmethod
    def assert_user_structure(user: Dict[str, Any]):
        """Helper para verificar estructura de usuario"""
        required_fields = [
            "id", "email", "full_name", "role", "is_active", "created_at"
        ]
        TestHelpers.assert_response_structure(user, required_fields)

    @staticmethod
    def assert_report_structure(report: Dict[str, Any], report_type: str):
        """Helper para verificar estructura de reporte según tipo"""
        if report_type == "balance_sheet":
            required_fields = [
                "report_date", "assets", "liabilities", "equity",
                "total_assets", "total_liabilities", "total_equity", "is_balanced"
            ]
        elif report_type == "income_statement":
            required_fields = [
                "start_date", "end_date", "revenues", "expenses",
                "total_revenues", "total_expenses", "net_income"
            ]
        elif report_type == "trial_balance":
            required_fields = [
                "report_date", "accounts", "total_debits", "total_credits", "is_balanced"
            ]
        elif report_type == "general_ledger":
            required_fields = ["start_date", "end_date", "accounts"]
        else:
            raise ValueError(f"Tipo de reporte desconocido: {report_type}")
        
        TestHelpers.assert_response_structure(report, required_fields)


class TestDataFactory:
    """Factory para generar datos de prueba consistentes"""
    
    @staticmethod
    def sample_accounts_data() -> List[Dict[str, Any]]:
        """Genera datos de cuentas de muestra para un plan contable básico"""
        return [
            {
                "code": "1001",
                "name": "Caja",
                "account_type": "ACTIVO",
                "category": "ACTIVO_CORRIENTE",
                "description": "Efectivo en caja"
            },
            {
                "code": "1002", 
                "name": "Banco Cuenta Corriente",
                "account_type": "ACTIVO",
                "category": "ACTIVO_CORRIENTE",
                "description": "Cuenta corriente bancaria"
            },
            {
                "code": "1003",
                "name": "Cuentas por Cobrar",
                "account_type": "ACTIVO",
                "category": "ACTIVO_CORRIENTE",
                "description": "Deudas de clientes"
            },
            {
                "code": "1501",
                "name": "Equipos de Oficina",
                "account_type": "ACTIVO",
                "category": "ACTIVO_NO_CORRIENTE",
                "description": "Equipos y mobiliario"
            },
            {
                "code": "2001",
                "name": "Proveedores",
                "account_type": "PASIVO",
                "category": "PASIVO_CORRIENTE",
                "description": "Deudas con proveedores"
            },
            {
                "code": "2002",
                "name": "Sueldos por Pagar",
                "account_type": "PASIVO",
                "category": "PASIVO_CORRIENTE",
                "description": "Salarios pendientes de pago"
            },
            {
                "code": "3001",
                "name": "Capital Social",
                "account_type": "PATRIMONIO",
                "category": "PATRIMONIO_NETO",
                "description": "Capital aportado por socios"
            },
            {
                "code": "3002",
                "name": "Resultados Acumulados",
                "account_type": "PATRIMONIO",
                "category": "PATRIMONIO_NETO",
                "description": "Utilidades retenidas"
            },
            {
                "code": "4001",
                "name": "Ventas",
                "account_type": "INGRESO",
                "category": "INGRESO_OPERATIVO",
                "description": "Ingresos por ventas"
            },
            {
                "code": "4002",
                "name": "Servicios",
                "account_type": "INGRESO",
                "category": "INGRESO_OPERATIVO",
                "description": "Ingresos por servicios"
            },
            {
                "code": "5001",
                "name": "Costo de Ventas",
                "account_type": "GASTO",
                "category": "GASTO_OPERATIVO",
                "description": "Costo directo de productos vendidos"
            },
            {
                "code": "5101",
                "name": "Sueldos y Salarios",
                "account_type": "GASTO",
                "category": "GASTO_OPERATIVO",
                "description": "Gastos de personal"
            },
            {
                "code": "5201",
                "name": "Alquiler",
                "account_type": "GASTO",
                "category": "GASTO_OPERATIVO",
                "description": "Alquiler de oficina"
            },
            {
                "code": "5301",
                "name": "Servicios Públicos",
                "account_type": "GASTO",
                "category": "GASTO_OPERATIVO",
                "description": "Electricidad, agua, gas"
            }
        ]

    @staticmethod
    def sample_users_data() -> List[Dict[str, Any]]:
        """Genera datos de usuarios de muestra"""
        return [
            {
                "email": "admin@empresa.com",
                "full_name": "Administrador Principal",
                "role": "ADMIN"
            },
            {
                "email": "contador@empresa.com",
                "full_name": "Contador General",
                "role": "CONTADOR"
            },
            {
                "email": "asistente@empresa.com",
                "full_name": "Asistente Contable",
                "role": "CONTADOR"
            },
            {
                "email": "auditor@empresa.com",
                "full_name": "Auditor Externo",
                "role": "SOLO_LECTURA"
            }
        ]

    @staticmethod
    def sample_journal_entries_scenarios() -> List[Dict[str, Any]]:
        """Genera escenarios de asientos contables típicos"""
        return [
            {
                "name": "aporte_inicial_capital",
                "description": "Aporte inicial de capital en efectivo",
                "reference": "CAP-001",
                "accounts": ["1001", "3001"],  # Caja, Capital
                "amounts": [100000.00, 100000.00]
            },
            {
                "name": "compra_equipos",
                "description": "Compra de equipos de oficina",
                "reference": "EQ-001", 
                "accounts": ["1501", "1002"],  # Equipos, Banco
                "amounts": [25000.00, 25000.00]
            },
            {
                "name": "venta_servicios",
                "description": "Venta de servicios al contado",
                "reference": "SRV-001",
                "accounts": ["1001", "4002"],  # Caja, Servicios
                "amounts": [15000.00, 15000.00]
            },
            {
                "name": "pago_sueldos",
                "description": "Pago de sueldos del mes",
                "reference": "SUE-001",
                "accounts": ["5101", "1002"],  # Sueldos, Banco
                "amounts": [8000.00, 8000.00]
            },
            {
                "name": "pago_alquiler",
                "description": "Pago alquiler mensual",
                "reference": "ALQ-001",
                "accounts": ["5201", "1001"],  # Alquiler, Caja
                "amounts": [3000.00, 3000.00]
            }
        ]
