"""
BigQuery Test Router
Provides a simple endpoint to test BigQuery integration within Darwin Platform.
"""

import os

from fastapi import APIRouter, HTTPException
from google.cloud import bigquery

router = APIRouter()

@router.get("/test-bigquery", tags=["Tests"])
async def test_bigquery_integration():
    """
    Tests the connection to BigQuery by running a simple query.
    """
    try:
        project_id = os.getenv("PROJECT_ID", "pcs-helio")
        client = bigquery.Client(project=project_id)

        # Perform a simple query to test the connection
        query = "SELECT 1 as test_value"
        query_job = client.query(query)  # Make an API request.
        results = query_job.result()  # Wait for the job to complete.

        # Extract the result
        first_row = next(results)
        test_value = first_row.test_value

        return {
            "status": "success",
            "project_id": project_id,
            "query": query,
            "result": f"Query returned {test_value}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred with BigQuery: {str(e)}")
