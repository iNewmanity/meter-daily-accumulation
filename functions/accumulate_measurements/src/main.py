from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.query import Query
import json
import os
import warnings
from datetime import datetime, time

# Suppress DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def main(context):
    # Retrieve environment variables
    database_id = os.environ.get('APPWRITE_DATABASE_ID')
    raw_collection_id = os.environ.get('APPWRITE_RAW_COLLECTION_ID')
    daily_collection_id = os.environ.get('APPWRITE_DAILY_COLLECTION_ID')

    if not all([database_id, raw_collection_id, daily_collection_id]):
        context.error("Missing environment variables.")
        return context.res.json({"error": "Configuration error"}, 500)

    # Parse request body
    try:
        if isinstance(context.req.body, str):
            payload = json.loads(context.req.body)
        else:
            payload = context.req.body
    except Exception as e:
        context.error(f"Failed to parse request body: {str(e)}")
        return context.res.json({"error": "Invalid request body"}, 400)

    device_id = payload.get('device-id')
    date_str = payload.get('date') # Expected format: YYYY-MM-DD

    if not device_id or not date_str:
        return context.res.json({"error": "Missing device-id or date"}, 400)

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return context.res.json({"error": "Invalid date format. Use YYYY-MM-DD"}, 400)

    context.log(f"Processing accumulation for device {device_id} on {date_str}")

    # Define the time range for the day
    start_of_day = datetime.combine(target_date, time.min).isoformat()
    end_of_day = datetime.combine(target_date, time.max).isoformat()

    client = Client()
    client.set_endpoint(os.environ.get('APPWRITE_FUNCTION_ENDPOINT'))
    client.set_project(os.environ.get('APPWRITE_FUNCTION_PROJECT_ID'))
    client.set_key(context.req.headers.get('x-appwrite-key') or os.environ.get('APPWRITE_API_KEY'))

    tables_db = TablesDB(client)

    try:
        # Fetch all measurements for the day
        context.log(f"Fetching measurements between {start_of_day} and {end_of_day} using 'timestamp' attribute")
        measurements_res = tables_db.list_rows(
            database_id,
            raw_collection_id,
            queries=[
                Query.equal('meters', device_id),
                Query.greater_than_equal('timestamp', start_of_day),
                Query.less_than_equal('timestamp', end_of_day),
                Query.order_asc('timestamp'),
                Query.limit(100) # Increased limit to fetch all (up to 100)
            ]
        )

        total_found = measurements_res['total']
        rows = measurements_res['rows']

        if total_found == 0:
            context.log("No data found for the given device and date")
            return context.res.json({"message": "No data found for the given device and date"}, 404)

        context.log(f"Found {total_found} measurements for this day")

        # Log all measurements
        for i, row in enumerate(rows):
            context.log(f"Measurement {i+1}: {json.dumps(row)}")

        earliest_doc = rows[0]
        latest_doc = rows[-1]

        start_val = earliest_doc.get('current_consumption_hca', 0)
        end_val = latest_doc.get('current_consumption_hca', 0)
        
        daily_current = end_val - start_val
        context.log(f"Calculated daily consumption: {daily_current}")

        # Create row in daily-measurements
        new_row = tables_db.create_row(
            database_id,
            daily_collection_id,
            'unique()',
            {
                'day': start_of_day,
                'start': start_val,
                'end': end_val,
                'meters': device_id,
                'current': daily_current
            }
        )

        context.log(f"Successfully created daily measurement row: {new_row['$id']}")
        return context.res.json({
            "message": "Daily measurement accumulated successfully",
            "documentId": new_row['$id']
        }, 201)

    except Exception as e:
        context.error(f"Error during accumulation: {str(e)}")
        return context.res.json({"error": str(e)}, 500)
