"""
Test endpoints for resetting journal entries to draft status.
Testing individual and bulk reset operations with proper validations.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.journal_entry import JournalEntryStatus
from app.schemas.journal_entry import (
    JournalEntryResetToDraft,
    JournalEntryResetToDraftValidation,
    BulkJournalEntryResetToDraft,
    BulkJournalEntryResetToDraftResult
)


class TestJournalEntryResetToDraftAPI:
    """Test class for journal entry reset to draft operations"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user with permissions"""
        user = AsyncMock()
        user.id = uuid.uuid4()
        user.can_create_entries = True
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_entry_id(self):
        """Sample journal entry ID"""
        return uuid.uuid4()
    
    @pytest.fixture
    def sample_reset_data(self):
        """Sample reset data"""
        return JournalEntryResetToDraft(
            reason="Test reset to draft"
        )
    
    @pytest.fixture
    def sample_bulk_reset_data(self):
        """Sample bulk reset data"""
        return BulkJournalEntryResetToDraft(
            journal_entry_ids=[uuid.uuid4(), uuid.uuid4()],
            force_reset=False,
            reason="Bulk test reset"
        )

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.reset_journal_entry_to_draft')
    async def test_reset_journal_entry_to_draft_success(
        self, 
        mock_reset, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_entry_id,
        sample_reset_data
    ):
        """Test successful reset of journal entry to draft"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock journal entry response
        mock_entry = AsyncMock()
        mock_entry.id = sample_entry_id
        mock_entry.status = JournalEntryStatus.DRAFT
        mock_entry.number = "JE-2024-001"
        mock_entry.description = "Test entry"
        mock_reset.return_value = mock_entry
        
        # Make request
        response = client.post(
            f"/api/v1/journal-entries/{sample_entry_id}/reset-to-draft",
            json=sample_reset_data.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_entry_id)
        assert data["status"] == JournalEntryStatus.DRAFT
        
        # Verify service was called correctly
        mock_reset.assert_called_once_with(
            entry_id=sample_entry_id,
            reset_by_id=mock_user.id,
            reset_data=sample_reset_data
        )

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    async def test_reset_journal_entry_insufficient_permissions(
        self, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_db,
        sample_entry_id,
        sample_reset_data
    ):
        """Test reset with insufficient permissions"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        user_without_permissions = AsyncMock()
        user_without_permissions.can_create_entries = False
        mock_get_user.return_value = user_without_permissions
        
        # Make request
        response = client.post(
            f"/api/v1/journal-entries/{sample_entry_id}/reset-to-draft",
            json=sample_reset_data.model_dump()
        )
        
        # Assertions
        assert response.status_code == 403

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.validate_journal_entry_for_reset_to_draft')
    async def test_validate_reset_to_draft_success(
        self, 
        mock_validate, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db
    ):
        """Test validation of journal entries for reset to draft"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        entry_ids = [uuid.uuid4(), uuid.uuid4()]
        
        # Mock validation responses
        mock_validations = [
            JournalEntryResetToDraftValidation(
                journal_entry_id=entry_ids[0],
                journal_entry_number="JE-2024-001",
                journal_entry_description="Test entry 1",
                current_status=JournalEntryStatus.APPROVED,
                can_reset=True,
                errors=[],
                warnings=[]
            ),
            JournalEntryResetToDraftValidation(
                journal_entry_id=entry_ids[1],
                journal_entry_number="JE-2024-002",
                journal_entry_description="Test entry 2",
                current_status=JournalEntryStatus.POSTED,
                can_reset=False,
                errors=["Cannot reset posted entry"],
                warnings=[]
            )
        ]
        
        mock_validate.side_effect = mock_validations
        
        # Make request
        response = client.post(
            "/api/v1/journal-entries/validate-reset-to-draft",
            json=[str(entry_id) for entry_id in entry_ids]
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["can_reset"] is True
        assert data[1]["can_reset"] is False
        assert len(data[1]["errors"]) == 1

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.bulk_reset_journal_entries_to_draft')
    async def test_bulk_reset_to_draft_success(
        self, 
        mock_bulk_reset, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_bulk_reset_data
    ):
        """Test successful bulk reset to draft"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock bulk reset result
        mock_result = BulkJournalEntryResetToDraftResult(
            total_requested=2,
            total_reset=1,
            total_failed=1,
            reset_entries=[
                JournalEntryResetToDraftValidation(
                    journal_entry_id=sample_bulk_reset_data.journal_entry_ids[0],
                    journal_entry_number="JE-2024-001",
                    journal_entry_description="Test entry 1",
                    current_status=JournalEntryStatus.DRAFT,
                    can_reset=True,
                    errors=[],
                    warnings=[]
                )
            ],
            failed_entries=[
                JournalEntryResetToDraftValidation(
                    journal_entry_id=sample_bulk_reset_data.journal_entry_ids[1],
                    journal_entry_number="JE-2024-002",
                    journal_entry_description="Test entry 2",
                    current_status=JournalEntryStatus.POSTED,
                    can_reset=False,
                    errors=["Cannot reset posted entry"],
                    warnings=[]
                )
            ],
            errors=[],
            warnings=[]
        )
        
        mock_bulk_reset.return_value = mock_result
        
        # Make request
        response = client.post(
            "/api/v1/journal-entries/bulk-reset-to-draft",
            json=sample_bulk_reset_data.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 2
        assert data["total_reset"] == 1
        assert data["total_failed"] == 1
        
        # Verify service was called correctly
        mock_bulk_reset.assert_called_once_with(
            entry_ids=sample_bulk_reset_data.journal_entry_ids,
            reset_by_id=mock_user.id,
            force_reset=sample_bulk_reset_data.force_reset,
            reason=sample_bulk_reset_data.reason
        )

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.bulk_operation')
    async def test_bulk_operation_reset_to_draft(
        self, 
        mock_bulk_operation, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db
    ):
        """Test bulk operation with reset_to_draft operation"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        entry_ids = [uuid.uuid4(), uuid.uuid4()]
        
        # Mock bulk operation result
        mock_result = {
            "operation": "reset_to_draft",
            "result": {
                "total_requested": 2,
                "total_reset": 2,
                "total_failed": 0,
                "reset_entries": [],
                "failed_entries": [],
                "errors": [],
                "warnings": []
            }
        }
        
        mock_bulk_operation.return_value = mock_result
        
        # Make request
        response = client.post(
            "/api/v1/journal-entries/bulk-operation",
            params={
                "operation": "reset_to_draft",
                "journal_entry_ids": [str(entry_id) for entry_id in entry_ids],
                "force_operation": True,
                "reason": "Test bulk reset"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "reset_to_draft"
        assert data["result"]["total_requested"] == 2
        assert data["result"]["total_reset"] == 2
        
        # Verify service was called correctly
        mock_bulk_operation.assert_called_once_with(
            operation="reset_to_draft",
            entry_ids=entry_ids,
            operation_data={
                "force_delete": False,
                "force_reset": True,
                "reason": "Test bulk reset",
                "approved_by_id": None,
                "cancelled_by_id": None,
                "reset_by_id": mock_user.id
            }
        )

    def test_bulk_reset_data_validation(self):
        """Test validation of bulk reset data"""
        
        # Test duplicate IDs
        duplicate_ids = [uuid.uuid4(), uuid.uuid4()]
        duplicate_ids.append(duplicate_ids[0])  # Add duplicate
        
        with pytest.raises(ValueError):
            BulkJournalEntryResetToDraft(
                journal_entry_ids=duplicate_ids,
                force_reset=False,
                reason="Test with duplicates"
            )
        
        # Test empty reason
        with pytest.raises(ValueError):
            BulkJournalEntryResetToDraft(
                journal_entry_ids=[uuid.uuid4()],
                force_reset=False,
                reason=""
            )
        
        # Test too many IDs
        many_ids = [uuid.uuid4() for _ in range(101)]  # Over limit of 100
        with pytest.raises(ValueError):
            BulkJournalEntryResetToDraft(
                journal_entry_ids=many_ids,
                force_reset=False,
                reason="Too many entries"
            )

    def test_reset_data_validation(self):
        """Test validation of reset data"""
        
        # Test empty reason
        with pytest.raises(ValueError):
            JournalEntryResetToDraft(reason="")
        
        # Test reason too long
        with pytest.raises(ValueError):
            JournalEntryResetToDraft(reason="x" * 501)  # Over 500 char limit
