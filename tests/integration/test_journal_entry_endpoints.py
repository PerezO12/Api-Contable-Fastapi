"""
Tests de integración para los endpoints de asientos contables
"""
import pytest
import uuid
from datetime import date, datetime
from decimal import Decimal
from httpx import AsyncClient
from typing import Dict, Any, List


@pytest.mark.integration
@pytest.mark.journal_entries
class TestJournalEntryEndpoints:
    """Tests para los endpoints de gestión de asientos contables"""

    @pytest.fixture
    async def sample_accounts(self, client: AsyncClient, auth_headers_admin: Dict[str, str]) -> List[Dict[str, Any]]:
        """Crear cuentas de muestra para los tests"""
        accounts_data = [
            {
                "code": "1001",
                "name": "Caja",
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
        
        return created_accounts

    @pytest.fixture
    async def sample_journal_entry_data(self, sample_accounts: List[Dict[str, Any]]):
        """Datos de muestra para crear asiento contable"""
        return {
            "reference": "TEST-001",
            "description": "Asiento de prueba",
            "entry_date": date.today().isoformat(),
            "line_items": [
                {
                    "account_id": sample_accounts[0]["id"],  # Caja
                    "description": "Entrada de efectivo",
                    "debit_amount": "1000.00",
                    "credit_amount": "0.00"
                },
                {
                    "account_id": sample_accounts[2]["id"],  # Capital
                    "description": "Aporte de capital",
                    "debit_amount": "0.00",
                    "credit_amount": "1000.00"
                }
            ]
        }

    async def test_create_journal_entry_admin(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para crear asiento contable siendo administrador"""
        response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verificar campos obligatorios
        assert "id" in data
        assert "entry_number" in data
        assert "reference" in data
        assert "description" in data
        assert "entry_date" in data
        assert "status" in data
        assert "line_items" in data
        assert "total_debit" in data
        assert "total_credit" in data
        assert "created_at" in data
        
        # Verificar valores
        assert data["reference"] == sample_journal_entry_data["reference"]
        assert data["description"] == sample_journal_entry_data["description"]
        assert data["status"] == "DRAFT"
        assert len(data["line_items"]) == 2
        assert data["total_debit"] == "1000.00"
        assert data["total_credit"] == "1000.00"

    async def test_create_journal_entry_contador(self, client: AsyncClient, auth_headers_contador: Dict[str, str], sample_journal_entry_data):
        """Test para crear asiento contable siendo contador"""
        sample_journal_entry_data["reference"] = "TEST-002"
        
        response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_contador
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["reference"] == "TEST-002"

    async def test_create_journal_entry_readonly_forbidden(self, client: AsyncClient, auth_headers_readonly: Dict[str, str], sample_journal_entry_data):
        """Test para crear asiento contable siendo usuario de solo lectura"""
        response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_readonly
        )
        
        assert response.status_code == 403

    async def test_create_journal_entry_unbalanced(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_accounts: List[Dict[str, Any]]):
        """Test para crear asiento contable desbalanceado"""
        unbalanced_data = {
            "reference": "TEST-UNBALANCED",
            "description": "Asiento desbalanceado",
            "entry_date": date.today().isoformat(),
            "line_items": [
                {
                    "account_id": sample_accounts[0]["id"],
                    "description": "Débito",
                    "debit_amount": "1000.00",
                    "credit_amount": "0.00"
                },
                {
                    "account_id": sample_accounts[1]["id"],
                    "description": "Crédito parcial",
                    "debit_amount": "0.00",
                    "credit_amount": "500.00"  # No balancea
                }
            ]
        }
        
        response = await client.post(
            "/api/v1/journal-entries/",
            json=unbalanced_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400

    async def test_list_journal_entries(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para listar asientos contables"""
        # Crear un asiento primero
        await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        
        response = await client.get(
            "/api/v1/journal-entries/",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta paginada
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert len(data["items"]) >= 1

    async def test_list_journal_entries_with_filters(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para listar asientos contables con filtros"""
        response = await client.get(
            "/api/v1/journal-entries/?status=DRAFT&limit=10",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que los filtros se aplicaron
        for item in data["items"]:
            assert item["status"] == "DRAFT"

    async def test_list_journal_entries_pagination(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para listar asientos contables con paginación"""
        response = await client.get(
            "/api/v1/journal-entries/?skip=0&limit=5",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) <= 5
        assert data["skip"] == 0
        assert data["limit"] == 5

    async def test_get_journal_entry_detail(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para obtener detalle de asiento contable"""
        # Crear asiento primero
        create_response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        created_entry = create_response.json()
        entry_id = created_entry["id"]
        
        # Obtener detalle
        response = await client.get(
            f"/api/v1/journal-entries/{entry_id}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == entry_id
        assert data["reference"] == sample_journal_entry_data["reference"]
        assert "line_items" in data
        assert len(data["line_items"]) == 2

    async def test_get_nonexistent_journal_entry(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener asiento contable inexistente"""
        nonexistent_id = str(uuid.uuid4())
        
        response = await client.get(
            f"/api/v1/journal-entries/{nonexistent_id}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 404

    async def test_update_journal_entry(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para actualizar asiento contable"""
        # Crear asiento primero
        create_response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        created_entry = create_response.json()
        entry_id = created_entry["id"]
        
        # Actualizar asiento
        update_data = {
            "description": "Descripción actualizada",
            "reference": "TEST-001-UPDATED"
        }
        
        response = await client.put(
            f"/api/v1/journal-entries/{entry_id}",
            json=update_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["description"] == update_data["description"]
        assert data["reference"] == update_data["reference"]

    async def test_delete_journal_entry(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para eliminar asiento contable"""
        # Crear asiento primero
        create_response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        created_entry = create_response.json()
        entry_id = created_entry["id"]
        
        # Eliminar asiento
        response = await client.delete(
            f"/api/v1/journal-entries/{entry_id}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 204

    async def test_approve_journal_entry(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para aprobar asiento contable"""
        # Crear asiento primero
        create_response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        created_entry = create_response.json()
        entry_id = created_entry["id"]
        
        # Aprobar asiento
        response = await client.post(
            f"/api/v1/journal-entries/{entry_id}/approve",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "APPROVED"
        assert "approved_at" in data
        assert "approved_by_id" in data

    async def test_post_journal_entry(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para contabilizar asiento contable"""
        # Crear y aprobar asiento primero
        create_response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        created_entry = create_response.json()
        entry_id = created_entry["id"]
        
        # Aprobar primero
        await client.post(
            f"/api/v1/journal-entries/{entry_id}/approve",
            headers=auth_headers_admin
        )
        
        # Contabilizar asiento
        response = await client.post(
            f"/api/v1/journal-entries/{entry_id}/post",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "POSTED"
        assert "posted_at" in data
        assert "posted_by_id" in data

    async def test_cancel_journal_entry(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para cancelar asiento contable"""
        # Crear asiento primero
        create_response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        created_entry = create_response.json()
        entry_id = created_entry["id"]
        
        # Cancelar asiento
        cancel_data = {
            "reason": "Error en el asiento"
        }
        
        response = await client.post(
            f"/api/v1/journal-entries/{entry_id}/cancel",
            json=cancel_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "CANCELLED"
        assert "cancelled_at" in data
        assert "cancelled_by_id" in data

    async def test_reverse_journal_entry(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para reversar asiento contable"""
        # Crear, aprobar y contabilizar asiento primero
        create_response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        created_entry = create_response.json()
        entry_id = created_entry["id"]
        
        # Aprobar y contabilizar
        await client.post(f"/api/v1/journal-entries/{entry_id}/approve", headers=auth_headers_admin)
        await client.post(f"/api/v1/journal-entries/{entry_id}/post", headers=auth_headers_admin)
        
        # Reversar asiento
        response = await client.post(
            f"/api/v1/journal-entries/{entry_id}/reverse?reason=Corrección de error",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Debe crear un nuevo asiento de reversión
        assert data["id"] != entry_id
        assert "REVERSAL" in data["reference"] or "REVERSE" in data["reference"]

    async def test_get_journal_entry_statistics(self, client: AsyncClient, auth_headers_admin: Dict[str, str]):
        """Test para obtener estadísticas de asientos contables"""
        response = await client.get(
            "/api/v1/journal-entries/statistics/summary",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar campos de estadísticas
        assert "total_entries" in data
        assert "entries_by_status" in data
        assert "total_amount" in data
        assert isinstance(data["total_entries"], int)
        assert isinstance(data["entries_by_status"], dict)

    async def test_search_journal_entries(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para buscar asientos contables"""
        # Crear asiento primero
        await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        
        response = await client.get(
            f"/api/v1/journal-entries/search?reference={sample_journal_entry_data['reference']}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            assert data[0]["reference"] == sample_journal_entry_data["reference"]

    async def test_bulk_create_journal_entries(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_accounts: List[Dict[str, Any]]):
        """Test para crear múltiples asientos contables"""
        bulk_data = [
            {
                "reference": "BULK-001",
                "description": "Primer asiento masivo",
                "entry_date": date.today().isoformat(),
                "line_items": [
                    {
                        "account_id": sample_accounts[0]["id"],
                        "description": "Débito 1",
                        "debit_amount": "500.00",
                        "credit_amount": "0.00"
                    },
                    {
                        "account_id": sample_accounts[1]["id"],
                        "description": "Crédito 1",
                        "debit_amount": "0.00",
                        "credit_amount": "500.00"
                    }
                ]
            },
            {
                "reference": "BULK-002",
                "description": "Segundo asiento masivo",
                "entry_date": date.today().isoformat(),
                "line_items": [
                    {
                        "account_id": sample_accounts[0]["id"],
                        "description": "Débito 2",
                        "debit_amount": "300.00",
                        "credit_amount": "0.00"
                    },
                    {
                        "account_id": sample_accounts[2]["id"],
                        "description": "Crédito 2",
                        "debit_amount": "0.00",
                        "credit_amount": "300.00"
                    }
                ]
            }
        ]
        
        response = await client.post(
            "/api/v1/journal-entries/bulk-create",
            json=bulk_data,
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["reference"] == "BULK-001"
        assert data[1]["reference"] == "BULK-002"

    async def test_get_journal_entry_by_number(self, client: AsyncClient, auth_headers_admin: Dict[str, str], sample_journal_entry_data):
        """Test para obtener asiento contable por número"""
        # Crear asiento primero
        create_response = await client.post(
            "/api/v1/journal-entries/",
            json=sample_journal_entry_data,
            headers=auth_headers_admin
        )
        created_entry = create_response.json()
        entry_number = created_entry["entry_number"]
        
        # Obtener por número
        response = await client.get(
            f"/api/v1/journal-entries/by-number/{entry_number}",
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["entry_number"] == entry_number
        assert data["reference"] == sample_journal_entry_data["reference"]
