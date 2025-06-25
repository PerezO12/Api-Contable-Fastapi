#!/usr/bin/env python3
"""
Simple test for batch processing functionality
"""
import sys
import os

# Add current directory to Python path
sys.path.append(os.getcwd())

def test_batch_processing():
    try:
        from app.services.import_session_service_simple import import_session_service
        print('✅ Import session service loaded successfully')
        
        # Test batch calculation
        class MockFileInfo:
            def __init__(self, total_rows):
                self.total_rows = total_rows
        
        class MockSession:
            def __init__(self, total_rows):
                self.file_info = MockFileInfo(total_rows)
        
        # Mock a session
        import_session_service._sessions['test'] = MockSession(10000)
        
        # Test batch calculations
        total_batches_2000 = import_session_service.get_total_batches('test', 2000)
        total_batches_1000 = import_session_service.get_total_batches('test', 1000)
        total_batches_5000 = import_session_service.get_total_batches('test', 5000)
        total_batches_3333 = import_session_service.get_total_batches('test', 3333)
        
        print('✅ Batch calculations work:')
        print(f'   10000 rows with batch_size 2000 = {total_batches_2000} batches (expected: 5)')
        print(f'   10000 rows with batch_size 1000 = {total_batches_1000} batches (expected: 10)')
        print(f'   10000 rows with batch_size 5000 = {total_batches_5000} batches (expected: 2)')
        print(f'   10000 rows with batch_size 3333 = {total_batches_3333} batches (expected: 4)')
        
        # Verify calculations
        assert total_batches_2000 == 5, f"Expected 5 batches for 2000 batch_size, got {total_batches_2000}"
        assert total_batches_1000 == 10, f"Expected 10 batches for 1000 batch_size, got {total_batches_1000}"
        assert total_batches_5000 == 2, f"Expected 2 batches for 5000 batch_size, got {total_batches_5000}"
        assert total_batches_3333 == 4, f"Expected 4 batches for 3333 batch_size, got {total_batches_3333}"
        
        # Clean up
        del import_session_service._sessions['test']
        
        print('🎉 All batch calculation tests passed!')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_import_endpoints():
    try:
        from app.api.v1.generic_import import router
        print('✅ Generic import router loaded successfully')
        
        # Count endpoints
        endpoint_count = len(router.routes)
        print(f'✅ Router has {endpoint_count} endpoints defined')
        
        # Check for new config endpoint
        config_endpoint_found = False
        execute_endpoint_found = False
        
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                if '/config' in route.path:
                    config_endpoint_found = True
                    print('✅ Found new /config endpoint')
                elif '/execute' in route.path:
                    execute_endpoint_found = True
                    print('✅ Found /execute endpoint')
        
        assert config_endpoint_found, "Config endpoint not found"
        assert execute_endpoint_found, "Execute endpoint not found"
        
        print('🎉 All endpoint tests passed!')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting batch processing tests...")
    print("=" * 50)
    
    test1_passed = test_batch_processing()
    print()
    test2_passed = test_import_endpoints()
    
    print()
    print("=" * 50)
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED! Batch processing implementation is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
