from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query
import json
import os
from datetime import datetime, time

def main(context):
    # Retrieve environment variables
    # These should be set in the Appwrite Console for the function
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

    # Define the time range for the day
    start_of_day = datetime.combine(target_date, time.min).isoformat()
    end_of_day = datetime.combine(target_date, time.max).isoformat()

    client = Client()
    client.set_endpoint(os.environ.get('APPWRITE_FUNCTION_ENDPOINT'))
    client.set_project(os.environ.get('APPWRITE_FUNCTION_PROJECT_ID'))
    client.set_key(context.req.headers.get('x-appwrite-key') or os.environ.get('APPWRITE_API_KEY'))

    databases = Databases(client)

    try:
        # Fetch earliest measurement for the day
        earliest_res = databases.list_documents(
            database_id,
            raw_collection_id,
            queries=[
                Query.equal('meters', device_id),
                Query.greater_than_equal('device_time', start_of_day),
                Query.less_than_equal('device_time', end_of_day),
                Query.order_asc('device_time'),
                Query.limit(1)
            ]
        )

        # Fetch latest measurement for the day
        latest_res = databases.list_documents(
            database_id,
            raw_collection_id,
            queries=[
                Query.equal('meters', device_id),
                Query.greater_than_equal('device_time', start_of_day),
                Query.less_than_equal('device_time', end_of_day),
                Query.order_desc('device_time'),
                Query.limit(1)
            ]
        )

        if earliest_res['total'] == 0:
            return context.res.json({"message": "No data found for the given device and date"}, 404)

        earliest_doc = earliest_res['documents'][0]
        latest_doc = latest_res['documents'][0]

        start_val = earliest_doc.get('current_consumption_hca', 0)
        end_val = latest_doc.get('current_consumption_hca', 0)
        
        # In the schema image, 'current' seems to be the delta or the current total
        # Usually it's end - start
        daily_current = end_val - start_val

        # Create row in daily-measurements
        # Schema from image: day (datetime), start (int), end (int), meters (rel), current (int)
        new_doc = databases.create_document(
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

        return context.res.json({
            "message": "Daily measurement accumulated successfully",
            "documentId": new_doc['$id']
        }, 201)

    except Exception as e:
        context.error(f"Error during accumulation: {str(e)}")
        return context.res.json({"error": str(e)}, 500)
