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
                      any("order_desc" in str(q) for q in queries) # Fallback for how it's mocked
            
            # Since Query is mocked, we need to be careful. 
            # In the real code Query.order_asc/desc are used.
            # In test_local.py, sys.modules['appwrite.query'] = MagicMock()
            
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
        return {'total': 0, 'rows': []}

    mock_instance.list_rows.side_effect = side_effect
    
    # Mock behavior of create_row to return our dict
    mock_instance.create_row.return_value = {'$id': 'new_doc_id'}

    print("Running local test with mocked Appwrite SDK (TablesDB)...")
    result = main(context)
    
    print(f"Result: {result}")
    print(f"Logs: {context.logs}")
    print(f"Errors: {context.errors}")

    # Check if 'timestamp' was used in logs
    timestamp_log_found = any("using 'timestamp' attribute" in log for log in context.logs)
    if not timestamp_log_found:
        print("\nFAILURE: Function did not log using 'timestamp' attribute.")
        sys.exit(1)

    if result['status_code'] == 201:
        # Verify last_month was passed to create_row
        call_args = mock_instance.create_row.call_args[0]
        row_data = call_args[3]
        if row_data.get('last_month') == 600 and row_data.get('date_last_month') == '2025-12-15T00:00:00Z':
            print("SUCCESS: last_month and date_last_month correctly passed to create_row from RAW.")
        else:
            print(f"FAILURE: last_month or date_last_month not found or incorrect in create_row: {row_data}")
            sys.exit(1)
        print("\nSUCCESS: Function executed correctly with mocked TablesDB and timestamp attribute.")
    else:
        print(f"\nFAILURE: Function returned status {result['status_code']}")
        sys.exit(1)

if __name__ == "__main__":
    test_function()
