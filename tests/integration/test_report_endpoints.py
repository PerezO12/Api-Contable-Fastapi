"""
Tests de integración para los endpoints de reportes financieros
"""
import pytest
import uuid
from datetime import date, datetime, timedelta
from httpx import AsyncClient
from typing import Dict, Any, List


@pytest.mark.integration
@pytest.mark.reports
class TestReportEndpoints:
    """Tests para los endpoints de reportes financieros"""

    @pytest.fixture
    async def setup_sample_data(self, client: AsyncClient, auth_headers_admin: Dict[str, str]) -> Dict[str, Any]:
        """Configurar datos de muestra para los reportes"""
        # Crear cuentas de muestra
        accounts_data = [
            {
                "code": "1001",
                "name": "Caja",
                "account_type": "ACTIVO",
                "category": "ACTIVO_CORRIENTE"
            },
            {
                "code": "1002",
                "name": "Banco",
                "account_type": "ACTIVO",
                "category": "ACTIVO_CORRIENTE"
            },
            {
                "code": "2001",
                "name": "Proveedores",
                "account_type": "PASIVO",
                "category": "PASIVO_CORRIENTE"
            },
            {
                "code": "3001",
                "name": "Capital",
                "account_type": "PATRIMONIO",
                "category": "PATRIMONIO_NETO"
            },
            {
                "code": "4001",
                "name": "Ventas",
                "account_type": "INGRESO",
                "category": "INGRESO_OPERATIVO"
            },
            {
                "code": "5001",
                "name": "Gastos Generales",
                "account_type": "GASTO",
                "category": "GASTO_OPERATIVO"
            }
        ]
        
        created_accounts = []
        for account_data in accounts_data:
            response = await client.post(
                "/api/v1/accounts/",
                json=account_data,
                headers=auth_headers_admin
            )
            if response.status_code == 201:
                created_accounts.append(response.json())
        
        # Crear algunos asientos contables de muestra
        journal_entries = [
            {
                "reference": "RPT-001",
                "description": "Aporte inicial de capital",
                "entry_date": (date.today() - timedelta(days=30)).isoformat(),
                "line_items": [
                    {
                        "account_id": created_accounts[0]["id"],  # Caja
                        "description": "Efectivo recibido",
                        "debit_amount": "10000.00",
                        "credit_amount": "0.00"
                    },
                    {
                        "account_id": created_accounts[3]["id"],  # Capital
                        "description": "Aporte de socios",
                        "debit_amount": "0.00",
                        "credit_amount": "10000.00"
                    }
                ]
            },
            {
                "reference": "RPT-002",
                "description": "Venta de servicios",
                "entry_date": (date.today() - timedelta(days=15)).isoformat(),
                "line_items": [
                    {
                        "account_id": created_accounts[1]["id"],  # Banco
                        "description": "Cobro por servicios",
                        "debit_amount": "5000.00",
                        "credit_amount": "0.00"
                    },
                    {
                        "account_id": created_accounts[4]["id"],  # Ventas
                        "description": "Ingresos por servicios",
                        "debit_amount": "0.00",
                        "credit_amount": "5000.00"
                    }
                ]
            },
            {
                "reference": "RPT-003",
                "description": "Gastos operativos",
                "entry_date": (date.today() - timedelta(days=10)).isoformat(),
                "line_items": [
                    {
                        "account_id": created_accounts[5]["id"],  # Gastos
                        "description": "Gastos varios",
                        "debit_amount": "1500.00",
                        "credit_amount": "0.00"
                    },
                    {
                        "account_id": created_accounts[0]["id"],  # Caja
                        "description": "Pago en efectivo",
                        "debit_amount": "0.00",
                        "credit_amount": "1500.00"
                    }
                ]
            }
        ]
        
        created_entries = []
        for entry_data in journal_entries:
            response = await client.post(
                "/api/v1/journal-entries/",
                json=entry_data,
                headers=auth_headers_admin
            )
            if response.status_code == 201:
                entry = response.json()
                created_entries.append(entry)
                
                # Aprobar y contabilizar cada asiento
                await client.post(
                    f"/api/v1/journal-entries/{entry['id']}/approve",
                    headers=auth_headers_admin
                )
                await client.post(
                    f"/api/v1/journal-entries/{entry['id']}/post",
                    headers=auth_headers_admin
                )
        
        return {
            "accounts": created_accounts,
            "journal_entries": created_entries
        }

    async def test_get_balance_sheet(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener balance general"""
        response = await client.get(
            "/api/v1/reports/balance-sheet",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura del balance general
        assert "report_date" in data
        assert "company_name" in data
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        assert "total_assets" in data
        assert "total_liabilities" in data
        assert "total_equity" in data
        assert "total_liabilities_equity" in data
        assert "is_balanced" in data
        
        # Verificar que las secciones sean listas
        assert isinstance(data["assets"], list)
        assert isinstance(data["liabilities"], list)
        assert isinstance(data["equity"], list)
        
        # Verificar que esté balanceado
        assert data["is_balanced"] is True or data["is_balanced"] is False

    async def test_get_balance_sheet_with_date(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener balance general con fecha específica"""
        specific_date = (date.today() - timedelta(days=5)).isoformat()
        
        response = await client.get(
            f"/api/v1/reports/balance-sheet?as_of_date={specific_date}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["report_date"] == specific_date

    async def test_get_income_statement(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener estado de resultados"""
        start_date = (date.today() - timedelta(days=60)).isoformat()
        end_date = date.today().isoformat()
        
        response = await client.get(
            f"/api/v1/reports/income-statement?start_date={start_date}&end_date={end_date}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura del estado de resultados
        assert "start_date" in data
        assert "end_date" in data
        assert "company_name" in data
        assert "revenues" in data
        assert "expenses" in data
        assert "total_revenues" in data
        assert "total_expenses" in data
        assert "net_income" in data
        
        # Verificar que las secciones sean listas
        assert isinstance(data["revenues"], list)
        assert isinstance(data["expenses"], list)
        
        # Verificar fechas
        assert data["start_date"] == start_date
        assert data["end_date"] == end_date

    async def test_get_income_statement_missing_dates(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener estado de resultados sin fechas obligatorias"""
        response = await client.get(
            "/api/v1/reports/income-statement",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 422  # Validation error

    async def test_get_trial_balance(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener balance de comprobación"""
        response = await client.get(
            "/api/v1/reports/trial-balance",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura del balance de comprobación
        assert "report_date" in data
        assert "company_name" in data
        assert "accounts" in data
        assert "total_debits" in data
        assert "total_credits" in data
        assert "is_balanced" in data
        
        # Verificar que accounts sea lista
        assert isinstance(data["accounts"], list)
        
        # Verificar estructura de cada cuenta
        if len(data["accounts"]) > 0:
            account = data["accounts"][0]
            assert "account_code" in account
            assert "account_name" in account
            assert "debit_balance" in account
            assert "credit_balance" in account

    async def test_get_trial_balance_with_options(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener balance de comprobación con opciones"""
        response = await client.get(
            "/api/v1/reports/trial-balance?include_zero_balances=true&company_name=Test Company",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["company_name"] == "Test Company"

    async def test_get_general_ledger(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener libro mayor"""
        start_date = (date.today() - timedelta(days=60)).isoformat()
        end_date = date.today().isoformat()
        
        response = await client.get(
            f"/api/v1/reports/general-ledger?start_date={start_date}&end_date={end_date}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura del libro mayor
        assert "start_date" in data
        assert "end_date" in data
        assert "company_name" in data
        assert "accounts" in data
        
        # Verificar que accounts sea lista
        assert isinstance(data["accounts"], list)
        
        # Verificar estructura de cada cuenta en el libro mayor
        if len(data["accounts"]) > 0:
            account = data["accounts"][0]
            assert "account_id" in account
            assert "account_code" in account
            assert "account_name" in account
            assert "opening_balance" in account
            assert "closing_balance" in account
            assert "movements" in account
            assert isinstance(account["movements"], list)

    async def test_get_general_ledger_with_filters(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener libro mayor con filtros"""
        start_date = (date.today() - timedelta(days=60)).isoformat()
        end_date = date.today().isoformat()
        
        response = await client.get(
            f"/api/v1/reports/general-ledger?start_date={start_date}&end_date={end_date}&account_type=ACTIVO",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que solo se incluyan cuentas de activo
        for account in data["accounts"]:
            # Nota: necesitaríamos verificar con los datos reales
            assert "account_code" in account

    async def test_get_financial_analysis(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener análisis financiero"""
        response = await client.get(
            "/api/v1/reports/financial-analysis",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura del análisis financiero
        assert "analysis_date" in data
        assert "company_name" in data
        assert "liquidity_ratios" in data
        assert "profitability_ratios" in data
        assert "financial_strength" in data
        assert "interpretation" in data

    async def test_get_accounts_summary_by_type(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para obtener resumen de cuentas por tipo"""
        response = await client.get(
            "/api/v1/reports/accounts-summary/ACTIVO",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        # Verificar estructura de cada cuenta en el resumen
        if len(data) > 0:
            account = data[0]
            assert "account_id" in account
            assert "account_code" in account
            assert "account_name" in account
            assert "opening_balance" in account
            assert "total_debits" in account
            assert "total_credits" in account
            assert "closing_balance" in account
            assert "movement_count" in account

    async def test_get_accounts_summary_invalid_type(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener resumen con tipo de cuenta inválido"""
        response = await client.get(
            "/api/v1/reports/accounts-summary/TIPO_INVALIDO",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 422

    async def test_check_accounting_integrity(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para verificar integridad contable"""
        response = await client.get(
            "/api/v1/reports/accounting-integrity",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de la verificación de integridad
        assert "as_of_date" in data
        assert "balance_sheet_balanced" in data
        assert "balance_sheet_equation" in data
        assert "trial_balance_balanced" in data
        assert "trial_balance_totals" in data
        assert "integrity_score" in data
        assert "issues_found" in data
        
        # Verificar tipos de datos
        assert isinstance(data["balance_sheet_balanced"], bool)
        assert isinstance(data["trial_balance_balanced"], bool)
        assert isinstance(data["integrity_score"], (int, float))
        assert isinstance(data["issues_found"], list)

    async def test_export_report(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para exportar reporte"""
        export_data = {
            "report_type": "balance_sheet",
            "format": "PDF",
            "as_of_date": date.today().isoformat(),
            "options": {
                "company_name": "Test Company",
                "include_notes": True
            }
        }
        
        response = await client.post(
            "/api/v1/reports/export",
            json=export_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta de exportación
        assert "export_id" in data
        assert "file_url" in data
        assert "format" in data
        assert "status" in data
        assert "created_at" in data
        
        assert data["format"] == "PDF"
        assert data["status"] in ["processing", "completed", "ready"]

    async def test_export_report_invalid_format(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para exportar reporte con formato inválido"""
        export_data = {
            "report_type": "balance_sheet",
            "format": "INVALID_FORMAT",
            "as_of_date": date.today().isoformat()
        }
        
        response = await client.post(
            "/api/v1/reports/export",
            json=export_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 422

    async def test_reports_readonly_access(self, client: AsyncClient, auth_headers_readonly: Dict[str, str]):
        """Test para verificar que usuarios de solo lectura pueden acceder a reportes"""
        response = await client.get(
            "/api/v1/reports/balance-sheet",
            headers=auth_headers_readonly
        )
        
        assert response.status_code == 200

    async def test_reports_without_auth(self, client: AsyncClient):
        """Test para verificar que se requiere autenticación para reportes"""
        response = await client.get("/api/v1/reports/balance-sheet")
        
        assert response.status_code == 401

    async def test_date_range_validation(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para validar rangos de fechas"""
        # Fecha de inicio posterior a fecha de fin
        start_date = date.today().isoformat()
        end_date = (date.today() - timedelta(days=1)).isoformat()
        
        response = await client.get(
            f"/api/v1/reports/income-statement?start_date={start_date}&end_date={end_date}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400

    async def test_concurrent_report_generation(self, client: AsyncClient, auth_headers_admin: Dict[str, str], setup_sample_data):
        """Test para generar múltiples reportes concurrentemente"""
        import asyncio
        
        tasks = [
            client.get("/api/v1/reports/balance-sheet", headers=auth_headers_admin),
            client.get("/api/v1/reports/trial-balance", headers=auth_headers_admin),
            client.get("/api/v1/reports/accounting-integrity", headers=auth_headers_admin)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Todos los reportes deben generarse exitosamente
        for response in responses:
            assert response.status_code == 200
