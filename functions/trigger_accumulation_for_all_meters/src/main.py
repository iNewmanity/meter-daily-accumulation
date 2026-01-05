from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.services.functions import Functions
from appwrite.query import Query
import json
import os
import warnings

# Suppress DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def main(context):
    # Retrieve environment variables
    database_id = os.environ.get('APPWRITE_DATABASE_ID')
    meters_collection_id = os.environ.get('APPWRITE_METERS_COLLECTION_ID')
    accumulate_function_id = os.environ.get('ACCUMULATE_FUNCTION_ID')

    if not all([database_id, meters_collection_id, accumulate_function_id]):
        context.error("Missing environment variables.")
        return context.res.json({"error": "Configuration error"}, 500)

    # Parse request body for the date
    try:
        if isinstance(context.req.body, str) and context.req.body:
            payload = json.loads(context.req.body)
        elif isinstance(context.req.body, dict):
            payload = context.req.body
        else:
            payload = {}
    except Exception as e:
        context.error(f"Failed to parse request body: {str(e)}")
        return context.res.json({"error": "Invalid request body"}, 400)

    # Get date from payload or use yesterday if not provided?
    # The issue says "trigger another function with ... the date with which this function was called"
    # So we expect 'date' in the payload.
    date_str = payload.get('date')
    if not date_str:
        context.error("Missing 'date' in request body.")
        return context.res.json({"error": "Missing 'date' in request body"}, 400)

    client = Client()
    client.set_endpoint(os.environ.get('APPWRITE_FUNCTION_ENDPOINT'))
    client.set_project(os.environ.get('APPWRITE_FUNCTION_PROJECT_ID'))
    client.set_key(context.req.headers.get('x-appwrite-key') or os.environ.get('APPWRITE_API_KEY'))

    tables_db = TablesDB(client)
    functions = Functions(client)

    try:
        context.log(f"Fetching active meters from collection: {meters_collection_id}")
        
        # Query meters that are active
        # Assuming there is an 'active' boolean attribute or similar. 
        # The prompt says "every meter from the table meters that is active"
        
        meters_res = tables_db.list_rows(
            database_id,
            meters_collection_id,
            queries=[
                Query.equal('active', True)
            ]
        )

        total_meters = meters_res.get('total', 0)
        context.log(f"Found {total_meters} active meters.")

        triggered_count = 0
        for meter in meters_res.get('rows', []):
            device_id = meter.get('device-id')
            if not device_id:
                context.log(f"Skipping meter {meter.get('$id')} because it has no device-id")
                continue

            context.log(f"Triggering accumulation for device: {device_id} on date: {date_str}")
            
            # Trigger the accumulation function
            trigger_payload = {
                "device-id": device_id,
                "date": date_str
            }
            
            try:
                functions.create_execution(
                    function_id=accumulate_function_id,
                    body=json.dumps(trigger_payload)
                )
                triggered_count += 1
            except Exception as e:
                context.error(f"Failed to trigger function for device {device_id}: {str(e)}")

        context.log(f"Successfully triggered {triggered_count} accumulation executions.")
        return context.res.json({
            "message": f"Triggered {triggered_count} accumulation executions.",
            "total_active": total_meters
        }, 200)

    except Exception as e:
        context.error(f"Error during trigger process: {str(e)}")
        return context.res.json({"error": str(e)}, 500)
