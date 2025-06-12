"""
Integration tests for bulk journal entry deletion API endpoints.

Tests the actual HTTP endpoints for bulk deletion functionality.
"""
import pytest
import uuid
from decimal import Decimal
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.journal_entry import JournalEntry, JournalEntryStatus
from app.services.journal_entry_service import JournalEntryService
from app.schemas.journal_entry import (
    BulkJournalEntryDelete,
    BulkJournalEntryDeleteResult,
    JournalEntryDeleteValidation
)


class TestBulkDeletionAPIEndpoints:
    """Test API endpoints for bulk journal entry deletion"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for authentication"""
        return User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            is_active=True
        )
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def override_dependencies(self, mock_user, mock_db):
        """Override FastAPI dependencies for testing"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()
    
    def test_validate_deletion_endpoint_success(self, client, override_dependencies):
        """Test successful validation endpoint"""
        entry_ids = [str(uuid.uuid4()) for _ in range(2)]
        
        # Mock service response
        mock_validations = [
            {
                "journal_entry_id": entry_ids[0],
                "journal_entry_number": "JE-2024-001",
                "can_delete": True,
                "errors": [],
                "warnings": []
            },
            {
                "journal_entry_id": entry_ids[1],
                "journal_entry_number": "JE-2024-002",
                "can_delete": True,
                "errors": [],
                "warnings": ["Monto alto detectado"]
            }
        ]
        
        # Patch the service method
        with patch('app.services.journal_entry_service.JournalEntryService.validate_journal_entry_for_deletion') as mock_validate:
            mock_validate.side_effect = [
                JournalEntryDeleteValidation(**validation)
                for validation in mock_validations
            ]
            
            response = client.post(
                "/api/v1/journal-entries/validate-deletion",
                json={"entry_ids": entry_ids}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(validation["can_delete"] for validation in data)
    
    def test_validate_deletion_endpoint_invalid_ids(self, client, override_dependencies):
        """Test validation endpoint with invalid UUIDs"""
        response = client.post(
            "/api/v1/journal-entries/validate-deletion",
            json={"entry_ids": ["invalid-uuid"]}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_validate_deletion_endpoint_empty_list(self, client, override_dependencies):
        """Test validation endpoint with empty entry list"""
        response = client.post(
            "/api/v1/journal-entries/validate-deletion",
            json={"entry_ids": []}
        )
        
        assert response.status_code == 422
        assert "at least 1 item" in response.json()["detail"][0]["msg"]
    
    def test_bulk_delete_endpoint_success(self, client, override_dependencies):
        """Test successful bulk deletion"""
        entry_ids = [str(uuid.uuid4()) for _ in range(2)]
        
        mock_result = {
            "total_requested": 2,
            "total_deleted": 2,
            "total_failed": 0,
            "deleted_entries": [
                {
                    "journal_entry_id": entry_ids[0],
                    "journal_entry_number": "JE-2024-001",
                    "can_delete": True,
                    "errors": [],
                    "warnings": []
                },
                {
                    "journal_entry_id": entry_ids[1],
                    "journal_entry_number": "JE-2024-002",
                    "can_delete": True,
                    "errors": [],
                    "warnings": []
                }
            ],
            "failed_entries": [],
            "errors": [],
            "warnings": []
        }
        
        with patch('app.services.journal_entry_service.JournalEntryService.bulk_delete_journal_entries') as mock_delete:
            mock_delete.return_value = BulkJournalEntryDeleteResult(**mock_result)
            
            response = client.post(
                "/api/v1/journal-entries/bulk-delete",
                json={
                    "entry_ids": entry_ids,
                    "force_delete": False,
                    "reason": "Test deletion"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 2
        assert data["total_deleted"] == 2
        assert data["total_failed"] == 0
    
    def test_bulk_delete_endpoint_partial_success(self, client, override_dependencies):
        """Test bulk deletion with partial success"""
        entry_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        mock_result = {
            "total_requested": 3,
            "total_deleted": 2,
            "total_failed": 1,
            "deleted_entries": [
                {
                    "journal_entry_id": entry_ids[0],
                    "journal_entry_number": "JE-2024-001",
                    "can_delete": True,
                    "errors": [],
                    "warnings": []
                },
                {
                    "journal_entry_id": entry_ids[1],
                    "journal_entry_number": "JE-2024-002",
                    "can_delete": True,
                    "errors": [],
                    "warnings": []
                }
            ],
            "failed_entries": [
                {
                    "journal_entry_id": entry_ids[2],
                    "journal_entry_number": "JE-2024-003",
                    "can_delete": False,
                    "errors": ["Solo se pueden eliminar asientos en estado BORRADOR"],
                    "warnings": []
                }
            ],
            "errors": [],
            "warnings": []
        }
        
        with patch('app.services.journal_entry_service.JournalEntryService.bulk_delete_journal_entries') as mock_delete:
            mock_delete.return_value = BulkJournalEntryDeleteResult(**mock_result)
            
            response = client.post(
                "/api/v1/journal-entries/bulk-delete",
                json={
                    "entry_ids": entry_ids,
                    "force_delete": False,
                    "reason": "Partial deletion test"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 3
        assert data["total_deleted"] == 2
        assert data["total_failed"] == 1
        assert len(data["failed_entries"]) == 1
    
    def test_bulk_delete_endpoint_force_delete(self, client, override_dependencies):
        """Test bulk deletion with force delete flag"""
        entry_ids = [str(uuid.uuid4())]
        
        with patch('app.services.journal_entry_service.JournalEntryService.bulk_delete_journal_entries') as mock_delete:
            mock_delete.return_value = BulkJournalEntryDeleteResult(
                total_requested=1,
                total_deleted=1,
                total_failed=0,
                deleted_entries=[],
                failed_entries=[],
                errors=[],
                warnings=[]
            )
            
            response = client.post(
                "/api/v1/journal-entries/bulk-delete",
                json={
                    "entry_ids": entry_ids,
                    "force_delete": True,
                    "reason": "Force delete test"
                }
            )
        
        assert response.status_code == 200
        # Verify force_delete was passed to service
        mock_delete.assert_called_once()
        call_args = mock_delete.call_args
        assert call_args.kwargs["force_delete"] is True
    
    def test_bulk_delete_endpoint_missing_required_fields(self, client, override_dependencies):
        """Test bulk deletion with missing required fields"""
        response = client.post(
            "/api/v1/journal-entries/bulk-delete",
            json={}  # Missing entry_ids
        )
        
        assert response.status_code == 422
    
    def test_bulk_operation_endpoint_delete_operation(self, client, override_dependencies):
        """Test unified bulk operation endpoint with delete operation"""
        entry_ids = [str(uuid.uuid4())]
        
        mock_result = {
            "operation": "delete",
            "result": {
                "total_requested": 1,
                "total_deleted": 1,
                "total_failed": 0,
                "deleted_entries": [],
                "failed_entries": [],
                "errors": [],
                "warnings": []
            }
        }
        
        with patch('app.services.journal_entry_service.JournalEntryService.bulk_operation') as mock_operation:
            mock_operation.return_value = mock_result
            
            response = client.post(
                "/api/v1/journal-entries/bulk-operation",
                json={
                    "operation": "delete",
                    "entry_ids": entry_ids,
                    "operation_data": {
                        "force_delete": True,
                        "reason": "Bulk operation test"
                    }
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "delete"
        assert "result" in data
    
    def test_bulk_operation_endpoint_unsupported_operation(self, client, override_dependencies):
        """Test bulk operation endpoint with unsupported operation"""
        entry_ids = [str(uuid.uuid4())]
        
        with patch('app.services.journal_entry_service.JournalEntryService.bulk_operation') as mock_operation:
            from app.utils.exceptions import JournalEntryError
            mock_operation.side_effect = JournalEntryError("Operación no soportada: invalid")
            
            response = client.post(
                "/api/v1/journal-entries/bulk-operation",
                json={
                    "operation": "invalid",
                    "entry_ids": entry_ids
                }
            )
        
        assert response.status_code == 400
        assert "Operación no soportada" in response.json()["detail"]
    
    def test_endpoints_authentication_required(self, client):
        """Test that endpoints require authentication"""
        # Test without dependency override (no authentication)
        entry_ids = [str(uuid.uuid4())]
        
        # Validate deletion endpoint
        response = client.post(
            "/api/v1/journal-entries/validate-deletion",
            json={"entry_ids": entry_ids}
        )
        assert response.status_code == 401
        
        # Bulk delete endpoint
        response = client.post(
            "/api/v1/journal-entries/bulk-delete",
            json={
                "entry_ids": entry_ids,
                "force_delete": False,
                "reason": "Test"
            }
        )
        assert response.status_code == 401
        
        # Bulk operation endpoint
        response = client.post(
            "/api/v1/journal-entries/bulk-operation",
            json={
                "operation": "delete",
                "entry_ids": entry_ids
            }
        )
        assert response.status_code == 401


# Import patch for mocking
from unittest.mock import patch
