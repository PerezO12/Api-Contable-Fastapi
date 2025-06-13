"""
Test endpoints for bulk operations on journal entries.
Testing approve, post, cancel, and reverse operations with proper validations.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.journal_entry import JournalEntryStatus
from app.schemas.journal_entry import (
    BulkJournalEntryApprove, BulkJournalEntryApproveResult, JournalEntryApproveValidation,
    BulkJournalEntryPost, BulkJournalEntryPostResult, JournalEntryPostValidation,
    BulkJournalEntryCancel, BulkJournalEntryCancelResult, JournalEntryCancelValidation,
    BulkJournalEntryReverse, BulkJournalEntryReverseResult, JournalEntryReverseValidation
)


class TestJournalEntryBulkOperationsAPI:
    """Test class for journal entry bulk operations"""
    
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
    def sample_entry_ids(self):
        """Sample journal entry IDs"""
        return [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

    # ========== BULK APPROVE TESTS ==========

    @pytest.fixture
    def sample_bulk_approve_data(self, sample_entry_ids):
        """Sample bulk approve data"""
        return BulkJournalEntryApprove(
            journal_entry_ids=sample_entry_ids[:2],
            force_approve=False,
            reason="Test bulk approval"
        )

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.bulk_approve_journal_entries')
    async def test_bulk_approve_success(
        self, 
        mock_bulk_approve, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_bulk_approve_data
    ):
        """Test successful bulk approval"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock bulk approve result
        mock_result = BulkJournalEntryApproveResult(
            total_requested=2,
            total_approved=2,
            total_failed=0,
            approved_entries=[
                JournalEntryApproveValidation(
                    journal_entry_id=sample_bulk_approve_data.journal_entry_ids[0],
                    journal_entry_number="JE-2024-001",
                    journal_entry_description="Test entry 1",
                    current_status=JournalEntryStatus.APPROVED,
                    can_approve=True,
                    errors=[],
                    warnings=[]
                ),
                JournalEntryApproveValidation(
                    journal_entry_id=sample_bulk_approve_data.journal_entry_ids[1],
                    journal_entry_number="JE-2024-002",
                    journal_entry_description="Test entry 2",
                    current_status=JournalEntryStatus.APPROVED,
                    can_approve=True,
                    errors=[],
                    warnings=[]
                )
            ],
            failed_entries=[],
            errors=[],
            warnings=[]
        )
        
        mock_bulk_approve.return_value = mock_result
        
        # Make request
        response = client.post(
            "/api/v1/journal-entries/bulk-approve",
            json=sample_bulk_approve_data.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 2
        assert data["total_approved"] == 2
        assert data["total_failed"] == 0

    # ========== BULK POST TESTS ==========

    @pytest.fixture
    def sample_bulk_post_data(self, sample_entry_ids):
        """Sample bulk post data"""
        return BulkJournalEntryPost(
            journal_entry_ids=sample_entry_ids[:2],
            force_post=False,
            reason="Test bulk posting"
        )

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.bulk_post_journal_entries')
    async def test_bulk_post_success(
        self, 
        mock_bulk_post, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_bulk_post_data
    ):
        """Test successful bulk posting"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock bulk post result
        mock_result = BulkJournalEntryPostResult(
            total_requested=2,
            total_posted=2,
            total_failed=0,
            posted_entries=[
                JournalEntryPostValidation(
                    journal_entry_id=sample_bulk_post_data.journal_entry_ids[0],
                    journal_entry_number="JE-2024-001",
                    journal_entry_description="Test entry 1",
                    current_status=JournalEntryStatus.POSTED,
                    can_post=True,
                    errors=[],
                    warnings=[]
                ),
                JournalEntryPostValidation(
                    journal_entry_id=sample_bulk_post_data.journal_entry_ids[1],
                    journal_entry_number="JE-2024-002",
                    journal_entry_description="Test entry 2",
                    current_status=JournalEntryStatus.POSTED,
                    can_post=True,
                    errors=[],
                    warnings=[]
                )
            ],
            failed_entries=[],
            errors=[],
            warnings=[]
        )
        
        mock_bulk_post.return_value = mock_result
        
        # Make request
        response = client.post(
            "/api/v1/journal-entries/bulk-post",
            json=sample_bulk_post_data.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 2
        assert data["total_posted"] == 2
        assert data["total_failed"] == 0

    # ========== BULK CANCEL TESTS ==========

    @pytest.fixture
    def sample_bulk_cancel_data(self, sample_entry_ids):
        """Sample bulk cancel data"""
        return BulkJournalEntryCancel(
            journal_entry_ids=sample_entry_ids[:2],
            force_cancel=False,
            reason="Test bulk cancellation"
        )

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.bulk_cancel_journal_entries')
    async def test_bulk_cancel_success(
        self, 
        mock_bulk_cancel, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_bulk_cancel_data
    ):
        """Test successful bulk cancellation"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock bulk cancel result
        mock_result = BulkJournalEntryCancelResult(
            total_requested=2,
            total_cancelled=2,
            total_failed=0,
            cancelled_entries=[
                JournalEntryCancelValidation(
                    journal_entry_id=sample_bulk_cancel_data.journal_entry_ids[0],
                    journal_entry_number="JE-2024-001",
                    journal_entry_description="Test entry 1",
                    current_status=JournalEntryStatus.CANCELLED,
                    can_cancel=True,
                    errors=[],
                    warnings=[]
                ),
                JournalEntryCancelValidation(
                    journal_entry_id=sample_bulk_cancel_data.journal_entry_ids[1],
                    journal_entry_number="JE-2024-002",
                    journal_entry_description="Test entry 2",
                    current_status=JournalEntryStatus.CANCELLED,
                    can_cancel=True,
                    errors=[],
                    warnings=[]
                )
            ],
            failed_entries=[],
            errors=[],
            warnings=[]
        )
        
        mock_bulk_cancel.return_value = mock_result
        
        # Make request
        response = client.post(
            "/api/v1/journal-entries/bulk-cancel",
            json=sample_bulk_cancel_data.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 2
        assert data["total_cancelled"] == 2
        assert data["total_failed"] == 0

    # ========== BULK REVERSE TESTS ==========

    @pytest.fixture
    def sample_bulk_reverse_data(self, sample_entry_ids):
        """Sample bulk reverse data"""
        return BulkJournalEntryReverse(
            journal_entry_ids=sample_entry_ids[:2],  # Only 2 for reverse (limit is 50)
            force_reverse=False,
            reason="Test bulk reversal"
        )

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.bulk_reverse_journal_entries')
    async def test_bulk_reverse_success(
        self, 
        mock_bulk_reverse, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_bulk_reverse_data
    ):
        """Test successful bulk reversal"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock bulk reverse result
        mock_result = BulkJournalEntryReverseResult(
            total_requested=2,
            total_reversed=2,
            total_failed=0,
            reversed_entries=[
                JournalEntryReverseValidation(
                    journal_entry_id=sample_bulk_reverse_data.journal_entry_ids[0],
                    journal_entry_number="JE-2024-001",
                    journal_entry_description="Test entry 1",
                    current_status=JournalEntryStatus.POSTED,
                    can_reverse=True,
                    errors=[],
                    warnings=[]
                ),
                JournalEntryReverseValidation(
                    journal_entry_id=sample_bulk_reverse_data.journal_entry_ids[1],
                    journal_entry_number="JE-2024-002",
                    journal_entry_description="Test entry 2",
                    current_status=JournalEntryStatus.POSTED,
                    can_reverse=True,
                    errors=[],
                    warnings=[]
                )
            ],
            failed_entries=[],
            created_reversal_entries=["REV-JE-2024-001", "REV-JE-2024-002"],
            errors=[],
            warnings=[]
        )
        
        mock_bulk_reverse.return_value = mock_result
        
        # Make request
        response = client.post(
            "/api/v1/journal-entries/bulk-reverse",
            json=sample_bulk_reverse_data.model_dump()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 2
        assert data["total_reversed"] == 2
        assert data["total_failed"] == 0
        assert len(data["created_reversal_entries"]) == 2

    # ========== VALIDATION TESTS ==========

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.validate_journal_entry_for_approve')
    async def test_validate_approve(
        self, 
        mock_validate, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_entry_ids
    ):
        """Test validation for approval"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock validation responses
        mock_validations = [
            JournalEntryApproveValidation(
                journal_entry_id=sample_entry_ids[0],
                journal_entry_number="JE-2024-001",
                journal_entry_description="Test entry 1",
                current_status=JournalEntryStatus.DRAFT,
                can_approve=True,
                errors=[],
                warnings=[]
            ),
            JournalEntryApproveValidation(
                journal_entry_id=sample_entry_ids[1],
                journal_entry_number="JE-2024-002",
                journal_entry_description="Test entry 2",
                current_status=JournalEntryStatus.APPROVED,
                can_approve=False,
                errors=["El asiento ya está aprobado"],
                warnings=[]
            )
        ]
        
        mock_validate.side_effect = mock_validations
        
        # Make request
        response = client.post(
            "/api/v1/journal-entries/validate-approve",
            json=[str(entry_id) for entry_id in sample_entry_ids[:2]]
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["can_approve"] is True
        assert data[1]["can_approve"] is False
        assert len(data[1]["errors"]) == 1

    # ========== BULK OPERATION UNIFIED ENDPOINT TESTS ==========

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.bulk_operation')
    async def test_bulk_operation_approve(
        self, 
        mock_bulk_operation, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_entry_ids
    ):
        """Test bulk operation with approve operation"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock bulk operation result
        mock_result = {
            "operation": "approve",
            "result": {
                "total_requested": 2,
                "total_approved": 2,
                "total_failed": 0,
                "approved_entries": [],
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
                "operation": "approve",
                "journal_entry_ids": [str(entry_id) for entry_id in sample_entry_ids[:2]],
                "force_operation": False,
                "reason": "Test bulk approve"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "approve"
        assert data["result"]["total_requested"] == 2
        assert data["result"]["total_approved"] == 2

    @patch('app.api.v1.journal_entries.get_db')
    @patch('app.api.v1.journal_entries.get_current_active_user')
    @patch('app.services.journal_entry_service.JournalEntryService.bulk_operation')
    async def test_bulk_operation_post(
        self, 
        mock_bulk_operation, 
        mock_get_user, 
        mock_get_db,
        client,
        mock_user,
        mock_db,
        sample_entry_ids
    ):
        """Test bulk operation with post operation"""
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock bulk operation result
        mock_result = {
            "operation": "post",
            "result": {
                "total_requested": 2,
                "total_posted": 2,
                "total_failed": 0,
                "posted_entries": [],
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
                "operation": "post",
                "journal_entry_ids": [str(entry_id) for entry_id in sample_entry_ids[:2]],
                "force_operation": False,
                "reason": "Test bulk post"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "post"
        assert data["result"]["total_requested"] == 2
        assert data["result"]["total_posted"] == 2

    def test_bulk_reverse_data_validation(self):
        """Test validation of bulk reverse data"""
        
        # Test too many IDs (over limit of 50)
        many_ids = [uuid.uuid4() for _ in range(51)]
        with pytest.raises(ValueError):
            BulkJournalEntryReverse(
                journal_entry_ids=many_ids,
                force_reverse=False,
                reason="Too many entries"
            )

    def test_insufficient_permissions(self, client):
        """Test endpoints with insufficient permissions"""
        
        with patch('app.api.v1.journal_entries.get_db') as mock_get_db, \
             patch('app.api.v1.journal_entries.get_current_active_user') as mock_get_user:
            
            # Setup user without permissions
            user_without_permissions = AsyncMock()
            user_without_permissions.can_create_entries = False
            mock_get_user.return_value = user_without_permissions
            mock_get_db.return_value = AsyncMock()
            
            # Test various endpoints
            bulk_data = {
                "journal_entry_ids": [str(uuid.uuid4())],
                "force_approve": False,
                "reason": "Test"
            }
            
            endpoints = [
                "/api/v1/journal-entries/bulk-approve",
                "/api/v1/journal-entries/bulk-post", 
                "/api/v1/journal-entries/bulk-cancel",
                "/api/v1/journal-entries/bulk-reverse"
            ]
            
            for endpoint in endpoints:
                response = client.post(endpoint, json=bulk_data)
                assert response.status_code == 403
