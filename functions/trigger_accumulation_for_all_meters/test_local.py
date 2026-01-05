import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock Appwrite services
sys.modules['appwrite'] = MagicMock()
sys.modules['appwrite.client'] = MagicMock()
sys.modules['appwrite.services.tables_db'] = MagicMock()
sys.modules['appwrite.services.functions'] = MagicMock()
sys.modules['appwrite.query'] = MagicMock()

from main import main

class MockResponse:
    def json(self, data, status_code=200):
        return {"data": data, "status_code": status_code}

class MockContext:
    def __init__(self, body):
        self.req = MagicMock()
        self.req.body = body
        self.req.headers = {}
        self.res = MockResponse()
        self.logs = []
        self.errors = []

    def log(self, message):
        print(f"LOG: {message}")
        self.logs.append(str(message))

    def error(self, message):
        print(f"ERROR: {message}")
        self.errors.append(str(message))

@patch('main.TablesDB')
@patch('main.Functions')
def test_function(MockFunctions, MockTablesDB):
    # Mock Environment Variables
    os.environ['APPWRITE_DATABASE_ID'] = 'test_db'
    os.environ['APPWRITE_METERS_COLLECTION_ID'] = 'test_meters'
    os.environ['ACCUMULATE_FUNCTION_ID'] = 'accumulate_fn_id'
    os.environ['APPWRITE_FUNCTION_ENDPOINT'] = 'https://localhost/v1'
    os.environ['APPWRITE_FUNCTION_PROJECT_ID'] = 'test_project'
    os.environ['APPWRITE_API_KEY'] = 'test_key'

    # Mock payload
    payload = {
        "date": "2026-01-05"
    }

    context = MockContext(payload)

    # Setup TablesDB mock
    mock_tables_instance = MockTablesDB.return_value
    mock_tables_instance.list_rows.return_value = {
        'total': 2,
        'rows': [
            {'$id': 'meter_1', 'device-id': 'dev_001', 'active': True},
            {'$id': 'meter_2', 'device-id': 'dev_002', 'active': True}
        ]
    }

    # Setup Functions mock
    mock_functions_instance = MockFunctions.return_value
    mock_functions_instance.create_execution.return_value = {'$id': 'exec_id'}

    print("Running local test for trigger function...")
    result = main(context)
    
    print(f"Result: {result}")
    
    # Assertions
    if result['status_code'] == 200:
        print("SUCCESS: Function returned 200 status.")
        
        # Verify list_rows was called
        mock_tables_instance.list_rows.assert_called_once()
        
        # Verify create_execution was called twice (once for each active meter)
        assert mock_functions_instance.create_execution.call_count == 2
        print("SUCCESS: create_execution called for each active meter.")
        
        # Verify payloads
        calls = mock_functions_instance.create_execution.call_args_list
        body1 = json.loads(calls[0].kwargs['body'])
        body2 = json.loads(calls[1].kwargs['body'])
        
        assert body1['device-id'] == 'dev_001'
        assert body1['date'] == '2026-01-05'
        assert body2['device-id'] == 'dev_002'
        assert body2['date'] == '2026-01-05'
        print("SUCCESS: Trigger payloads are correct.")
        
    else:
        print(f"FAILURE: Function returned status {result['status_code']}")
        sys.exit(1)

if __name__ == "__main__":
    test_function()
