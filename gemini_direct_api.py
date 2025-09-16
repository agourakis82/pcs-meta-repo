"""
Gemini Direct API Implementation
Alternative to deprecated Vertex AI SDK using Google AI Studio API directly
"""

import logging
import os
from typing import Any, Dict, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiDirectAPI:
    """Direct implementation of Gemini API using REST calls"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini API client
        
        Args:
            api_key: Google AI Studio API key. If None, tries env var GEMINI_API_KEY
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set GEMINI_API_KEY env var or pass directly.")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.headers = {
            "Content-Type": "application/json"
        }
        
    def generate_content(self, 
                        prompt: str, 
                        model: str = "gemini-1.5-flash",
                        temperature: float = 0.7,
                        max_tokens: int = 1024) -> Dict[str, Any]:
        """Generate content using Gemini API
        
        Args:
            prompt: Input text prompt
            model: Model name (gemini-1.5-flash, gemini-1.5-pro, etc.)
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            API response with generated content
        """
        url = f"{self.base_url}/models/{model}:generateContent"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "candidateCount": 1
            }
        }
        
        try:
            response = requests.post(
                f"{url}?key={self.api_key}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Gemini API call successful for model {model}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Gemini API error: {e}")
            raise
    
    def extract_text(self, response: Dict[str, Any]) -> str:
        """Extract text from Gemini API response
        
        Args:
            response: Raw API response
            
        Returns:
            Generated text content
        """
        try:
            candidates = response.get('candidates', [])
            if not candidates:
                return "No response generated"
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            
            if parts and 'text' in parts[0]:
                return parts[0]['text']
            else:
                return "No text content found"
                
        except (KeyError, IndexError) as e:
            logger.error(f"❌ Error extracting text: {e}")
            return f"Error extracting response: {e}"
    
    def chat_complete(self, prompt: str, **kwargs: Any) -> str:
        """Simple chat completion interface
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters for generate_content
            
        Returns:
            Generated text response
        """
        response = self.generate_content(prompt, **kwargs)
        return self.extract_text(response)


def test_gemini_direct():
    """Test function for Gemini Direct API"""
    print("🔍 Testing Gemini Direct API...")
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("📝 To get an API key:")
        print("   1. Go to https://makersuite.google.com/app/apikey")
        print("   2. Create new API key")
        print("   3. export GEMINI_API_KEY='your-key-here'")
        return False
    
    try:
        client = GeminiDirectAPI(api_key)
        
        # Test simple generation
        response = client.chat_complete(
            "Test message: Say 'Gemini Direct API is working!' in Portuguese",
            temperature=0.1
        )
        
        print(f"✅ Gemini Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


if __name__ == "__main__":
    test_gemini_direct()