# Meter Daily Accumulation

Appwrite functions for processing meter measurements.

## Functions

### 1. Accumulate Measurements
Accumulates daily measurements from raw data for a specific device.
- **Path**: `functions/accumulate_measurements`
- **Input**: `{"device-id": "DEVICE_ID", "date": "YYYY-MM-DD"}`

### 2. Trigger Accumulation for All Meters
Queries all active meters and triggers the `Accumulate Measurements` function for each.
- **Path**: `functions/trigger_accumulation_for_all_meters`
- **Input**: `{"date": "YYYY-MM-DD"}`

## Setup and Deployment

1. Create two Python Appwrite functions.
2. Configure the following environment variables:

#### For both functions:
- `APPWRITE_DATABASE_ID`: Database ID.
- `APPWRITE_METERS_COLLECTION_ID`: ID of the `meters` collection.
- `APPWRITE_FUNCTION_ENDPOINT`: Appwrite endpoint (e.g., `https://cloud.appwrite.io/v1`).
- `APPWRITE_FUNCTION_PROJECT_ID`: Project ID.
- `APPWRITE_API_KEY`: API key with Database and Execution permissions.

#### Specifically for `accumulate_measurements`:
- `APPWRITE_RAW_COLLECTION_ID`: ID of the `raw` collection.
- `APPWRITE_DAILY_COLLECTION_ID`: ID of the `daily-measurements` collection.

#### Specifically for `trigger_accumulation_for_all_meters`:
- `ACCUMULATE_FUNCTION_ID`: The ID of the `accumulate_measurements` function.

3. Deploy each function from its respective directory.

## Testing

### 1. Testing in Appwrite Console
1. Navigate to your function in the **Appwrite Console**.
2. Go to the **Execute** tab.
3. In the **Body** field, enter the JSON payload:
   ```json
   {
     "device-id": "your-device-id",
     "date": "2026-01-05"
   }
   ```
4. Click **Execute Now**.
5. Check the **Execution Logs** to see the result and any errors.

### 2. Testing via Appwrite CLI
If you have the Appwrite CLI installed, you can trigger the function using:
```bash
appwrite functions create-execution \
    --functionId [FUNCTION_ID] \
    --body '{"device-id": "your-device-id", "date": "2026-01-05"}'
```

### 3. Local Testing (Mocked)
You can run a local test to verify the logic (without calling the actual Appwrite API) using the provided `test_local.py` script.

1. Install dependencies:
   ```bash
   pip install -r functions/accumulate_measurements/requirements.txt
   ```
2. Run the test:
   ```bash
   python functions/accumulate_measurements/test_local.py
   ```
   Note: The local test mocks the Appwrite context but will fail when attempting to make actual network calls to Appwrite unless you provide valid environment variables in the script.