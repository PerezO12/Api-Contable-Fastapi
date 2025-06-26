"""
Test script to verify batch processing functionality
"""
import asyncio
import pandas as pd
import tempfile
import os
from app.services.import_session_service_simple import import_session_service

async def test_batch_processing():
    """Test the batch reading functionality"""
    
    # Create a test CSV file with many rows
    test_data = []
    for i in range(1, 5001):  # 5000 rows
        test_data.append({
            'name': f'Third Party {i}',
            'email': f'email{i}@example.com',
            'phone': f'+123456789{i:04d}',
            'document_number': f'DOC{i:06d}'
        })
    
    df = pd.DataFrame(test_data)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_file_path = f.name
    
    try:
        print(f"Created test file with {len(df)} rows: {temp_file_path}")
        
        # Test file analysis
        from fastapi import UploadFile
        import io
        
        # Simulate file upload
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()
        
        # Create a mock UploadFile
        class MockUploadFile:
            def __init__(self, filename, content):
                self.filename = filename
                self.content = content
                
            async def read(self):
                return self.content
        
        mock_file = MockUploadFile("test.csv", file_content)
        
        # Test session creation (this would require the model metadata registry to be properly set up)
        print("Testing file analysis...")
        file_info, detected_columns, sample_rows = await import_session_service._analyze_file(
            mock_file, temp_file_path
        )
        
        print(f"File analysis results:")
        print(f"  Total rows detected: {file_info.total_rows}")
        print(f"  Sample rows returned: {len(sample_rows)}")
        print(f"  Detected columns: {[col.name for col in detected_columns]}")
        
        # Test batch reading (without creating a full session)
        print("\\nTesting batch reading...")
        
        # Manually create a simple session token and add to service for testing
        session_token = "test-session-123"
        
        # Create a minimal session object for testing
        from app.schemas.generic_import import ImportSession, ModelMetadata
        from datetime import datetime, timedelta
        
        # This is a simplified test - in real usage, the session would be created properly
        mock_session = ImportSession(
            token=session_token,
            model="third_party",
            model_metadata=ModelMetadata(
                model_name="third_party",
                display_name="Third Party",
                fields=[],
                business_key_fields=[]
            ),
            file_info=file_info,
            detected_columns=detected_columns,
            sample_rows=sample_rows,
            user_id="test-user",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=2),
            file_path=temp_file_path
        )
        
        # Manually add to sessions for testing
        import_session_service._sessions[session_token] = mock_session
        
        # Test different batch sizes
        batch_sizes = [500, 1000, 2000]
        
        for batch_size in batch_sizes:
            print(f"\\nTesting batch size: {batch_size}")
            total_batches = import_session_service.get_total_batches(session_token, batch_size)
            print(f"  Total batches calculated: {total_batches}")
            
            total_rows_read = 0
            for batch_num in range(min(3, total_batches)):  # Test first 3 batches only
                batch_data = await import_session_service.read_file_batch(
                    session_token, batch_size, batch_num
                )
                total_rows_read += len(batch_data)
                print(f"  Batch {batch_num + 1}: {len(batch_data)} rows")
                
                if batch_data:
                    print(f"    First row sample: {list(batch_data[0].keys())}")
            
            print(f"  Total rows read in first 3 batches: {total_rows_read}")
            expected_in_3_batches = min(batch_size * 3, file_info.total_rows)
            print(f"  Expected: {expected_in_3_batches}")
            
        print("\\nBatch processing test completed successfully!")
        
    finally:
        # Clean up
        try:
            os.unlink(temp_file_path)
            print(f"Cleaned up test file: {temp_file_path}")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_batch_processing())
