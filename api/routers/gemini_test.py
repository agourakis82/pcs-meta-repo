"""
Gemini Test Router
Provides a simple endpoint to test Gemini integration within Darwin Platform.
"""

import os

from fastapi import APIRouter, HTTPException

from gemini_direct_api import GeminiDirectAPI

router = APIRouter()

@router.get("/test-gemini", tags=["Tests"])
async def test_gemini_integration(prompt: str = "Say 'Darwin is now connected to Gemini!'"):
    """
    Tests the direct integration with Gemini API.
    """
    try:
        # Ensure the API key is available in the environment
        if not os.getenv("GEMINI_API_KEY"):
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in the environment.")

        client = GeminiDirectAPI()
        response = client.chat_complete(prompt)
        
        return {"status": "success", "prompt": prompt, "gemini_response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
