# Meter Daily Accumulation

Appwrite function to accumulate daily measurements from raw data.

## Features

- Takes `device-id` and `date` (YYYY-MM-DD) as input.
- Queries the `raw` collection for the first and last measurement of the day.
- Calculates daily consumption.
- Stores the results in the `daily-measurements` collection.

## Deployment

1. Create a new Appwrite function using the Python runtime.
2. Add the following environment variables to your function:
   - `APPWRITE_DATABASE_ID`: The ID of your database.
   - `APPWRITE_RAW_COLLECTION_ID`: The ID of the `raw` collection.
   - `APPWRITE_DAILY_COLLECTION_ID`: The ID of the `daily-measurements` collection.
   - `APPWRITE_API_KEY`: An API key with read/write access to databases.
3. Deploy the code from the `functions/accumulate_measurements` directory.

## Input Format

The function expects a JSON body:

```json
{
  "device-id": "DEVICE_ID",
  "date": "2026-01-05"
}
```

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