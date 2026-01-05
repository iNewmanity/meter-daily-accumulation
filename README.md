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