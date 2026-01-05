import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock TablesDB before importing main
sys.modules['appwrite'] = MagicMock()
sys.modules['appwrite.client'] = MagicMock()
sys.modules['appwrite.services.tables_db'] = MagicMock()
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
        # Convert MagicMock to string for easier reading in test output
        if isinstance(message, MagicMock):
            message = str(message)
        print(f"LOG: {message}")
        self.logs.append(message)

    def error(self, message):
        if isinstance(message, MagicMock):
            message = str(message)
        print(f"ERROR: {message}")
        self.errors.append(message)

@patch('main.TablesDB')
def test_function(MockTablesDB):
    # Mock Environment Variables
    os.environ['APPWRITE_DATABASE_ID'] = 'test_db'
    os.environ['APPWRITE_RAW_COLLECTION_ID'] = 'test_raw'
    os.environ['APPWRITE_DAILY_COLLECTION_ID'] = 'test_daily'
    os.environ['APPWRITE_METERS_COLLECTION_ID'] = 'test_meters'
    os.environ['APPWRITE_FUNCTION_ENDPOINT'] = 'https://localhost/v1'
    os.environ['APPWRITE_FUNCTION_PROJECT_ID'] = 'test_project'
    os.environ['APPWRITE_API_KEY'] = 'test_key'

    # Mock payload
    payload = {
        "device-id": "device_123",
        "date": "2026-01-05"
    }

    context = MockContext(payload)

    # Create return values that are actual dicts, not MagicMocks when accessed
    mock_rows = [
        {
            'timestamp': '2026-01-05T08:00:00Z', 
            'current_consumption_hca': 100, 
            'meters': 'device_123',
            'consumption_at_set_date_17_hca': 600,
            'set_date_17': '2025-12-15T00:00:00Z'
        },
        {
            'timestamp': '2026-01-05T12:00:00Z', 
            'current_consumption_hca': 125, 
            'meters': 'device_123'
        },
        {
            'timestamp': '2026-01-05T20:00:00Z', 
            'current_consumption_hca': 150, 
            'meters': 'device_123'
        }
    ]
    
    # Setup mock behavior
    mock_instance = MockTablesDB.return_value
    
    # Mock behavior of list_rows
    def side_effect(database_id, collection_id, queries=None):
        if collection_id == 'test_meters':
            return {
                'total': 1,
                'rows': [{
                    '$id': 'internal_device_456', 
                    'device-id': 'device_123'
                }]
            }
        elif collection_id == 'test_raw':
            # Identify if it is asking for earliest (ASC) or latest (DESC)
            is_desc = any(isinstance(q, MagicMock) and "order_desc" in str(q) for q in queries) or \
                      any("order_desc" in str(q) for q in queries)
            
            if is_desc:
                return {
                    'total': 3,
                    'rows': [mock_rows[-1]]
                }
            else:
                return {
                    'total': 3,
                    'rows': [mock_rows[0]]
                }
        elif collection_id == 'test_daily':
            # This is the existence check for daily-measurements
            # We can control this to test CREATE vs UPDATE
            if os.environ.get('TEST_MODE') == 'UPDATE':
                return {
                    'total': 1,
                    'rows': [{'$id': 'existing_row_789'}]
                }
            else:
                return {
                    'total': 0,
                    'rows': []
                }
        return {'total': 0, 'rows': []}

    mock_instance.list_rows.side_effect = side_effect
    
    # Mock behavior of create_row and update_row
    mock_instance.create_row.return_value = {'$id': 'new_doc_id'}
    mock_instance.update_row.return_value = {'$id': 'existing_row_789'}

    print("\n--- Testing CREATE Mode ---")
    os.environ['TEST_MODE'] = 'CREATE'
    result = main(context)
    print(f"Result: {result}")
    
    if result['status_code'] == 201 and "accumulated successfully" in result['data']['message']:
        print("SUCCESS: Create mode verified.")
    else:
        print(f"FAILURE: Unexpected result in Create mode: {result}")
        sys.exit(1)

    print("\n--- Testing UPDATE Mode ---")
    os.environ['TEST_MODE'] = 'UPDATE'
    # We need a new context or clear the logs if we want to be clean, but for now just run
    context_update = MockContext(payload)
    result_update = main(context_update)
    print(f"Result: {result_update}")

    if result_update['status_code'] == 200 and "updated" in result_update['data']['message']:
        print("SUCCESS: Update mode verified.")
    else:
        print(f"FAILURE: Unexpected result in Update mode: {result_update}")
        sys.exit(1)

    # Check if 'timestamp' was used in logs
    timestamp_log_found = any("using 'timestamp' attribute" in log for log in context.logs)
    if not timestamp_log_found:
        print("\nFAILURE: Function did not log using 'timestamp' attribute.")
        sys.exit(1)

    # Verify last_month was passed to create_row (from the first run)
    create_call_args = next(call for call in mock_instance.create_row.call_args_list)
    row_data = create_call_args[0][3]
    if row_data.get('last_month') == 600 and row_data.get('date_last_month') == '2025-12-15T00:00:00Z':
        print("SUCCESS: last_month and date_last_month correctly passed to create_row.")
    else:
        print(f"FAILURE: last_month or date_last_month incorrect in create_row: {row_data}")
        sys.exit(1)
    
    # Verify update_row was called (from the second run)
    if mock_instance.update_row.called:
        update_call_args = mock_instance.update_row.call_args[0]
        if update_call_args[2] == 'existing_row_789':
            print("SUCCESS: update_row called with correct ID.")
        else:
            print(f"FAILURE: update_row called with wrong ID: {update_call_args[2]}")
            sys.exit(1)
    else:
        print("FAILURE: update_row was not called in UPDATE mode.")
        sys.exit(1)

    print("\nALL LOCAL TESTS PASSED")

if __name__ == "__main__":
    test_function()
