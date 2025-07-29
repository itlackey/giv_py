"""
Language Model API client and utilities.

This module provides comprehensive LLM integration using the OpenAI ChatCompletion 
format for all API endpoints, including:
- Support for unified API format (OpenAI ChatCompletion)
- Comprehensive error handling and retries
- Proper dry-run mode implementation
- Temperature and context window configuration
- Request/response logging for debugging
- JSON escaping and parsing
- Local service detection (skips auth for localhost)
- Fallback JSON parsing without external dependencies
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, Optional

import requests

from ..constants import DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_API_TIMEOUT
from ..errors import APIError

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified language model client using OpenAI ChatCompletion format.
    
    This class provides a normalized interface to various LLM APIs,
    with comprehensive error handling and configuration options.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: int = DEFAULT_API_TIMEOUT,
        retries: int = 3,
    ) -> None:
        """Initialize LLM client with configuration.
        
        Parameters
        ----------
        api_url : Optional[str]
            API endpoint URL
        api_key : Optional[str]
            API authentication key
        model : Optional[str]
            Model name to use
        temperature : float
            Sampling temperature (0.0-1.0)
        max_tokens : int
            Maximum completion tokens
        timeout : int
            Request timeout in seconds
        retries : int
            Number of retry attempts
        """
        # Clean URL and key of surrounding quotes (matching Bash sed logic)
        self.api_url = self._clean_quotes(api_url) if api_url else None
        self.api_key = self._clean_quotes(api_key) if api_key else None
        self.model = self._clean_quotes(model) if model else "default"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retries = retries
        
        # For backward compatibility with tests
        self.api_base = self.api_url
        self.headers = self._build_headers()

    @staticmethod
    def _clean_quotes(value: str) -> str:
        """Remove surrounding quotes from configuration values."""
        if not value:
            return value
        # Remove double quotes
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        # Remove single quotes
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        return value

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "giv-cli/1.0.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers

    def generate(self, prompt: str, dry_run: bool = False) -> Dict[str, Any]:
        """Generate a response from the language model.

        Parameters
        ----------
        prompt : str
            The full prompt to send to the model
        dry_run : bool
            If True, return the prompt without calling API

        Returns
        -------
        Dict[str, Any]
            A mapping containing at least a ``content`` key with the
            generated text.
        """
        # Validate prompt parameter
        if prompt is None:
            raise APIError("API error: Prompt cannot be None")
        
        if dry_run:
            # Dry-run mode: just echo the prompt
            logger.debug("Dry-run mode; returning prompt as output")
            return {"content": prompt.strip()}
        
        if not self.api_url:
            raise APIError("API error: No API URL configured")

        # Validate required configuration
        if not self.model:
            logger.error("Missing required model configuration")
            return {"content": "Error: Missing required model configuration"}

        # Make API request with retries
        for attempt in range(self.retries):
            try:
                response = self._make_request(prompt)
                if response:
                    return response
            except Exception as e:
                logger.warning(f"API request attempt {attempt + 1} failed: {e}")
                if attempt < self.retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All {self.retries} API request attempts failed")
                    raise APIError(f"API error: {e}")

        return {"content": "Error: Failed to generate response after multiple attempts"}

    def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make a single API request."""
        # Prepare request data
        headers = {"Content-Type": "application/json"}

        if self.api_url and ("localhost" in self.api_url or "127.0.0.1" in self.api_url) and not self.api_key:
            self.api_key = "giv"  # Use 'giv' as the key for local services
        
        headers["Authorization"] = f"Bearer {self.api_key}"
        logger.debug(f"Using Authorization header with API key: {self._mask_api_key(self.api_key)}")

        # Prepare request body (OpenAI ChatCompletion format)
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        logger.debug(f"Making request to: {self.api_url}")
        # Create a copy of data for logging without sensitive information
        log_data = data.copy()
        logger.debug(f"Request data: {json.dumps(log_data, indent=2)}")

        # Make request
        resp = requests.post(
            self.api_url,
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        logger.debug(f"Response status: {resp.status_code}")
        logger.debug(f"Response content: {resp.text}")

        resp.raise_for_status()

        # Parse response
        try:
            response_data = resp.json()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from API: {e}")
            raise APIError("API error: Invalid JSON response")

        # Extract content from response
        content = self._extract_content(response_data)
        if not content:
            logger.error("No content found in API response")
            return {"content": "Error: No content in API response"}

        return {"content": content}

    def _extract_content(self, response_data: Any) -> str:
        """Extract content from API response, supporting multiple formats."""
        if not isinstance(response_data, dict):
            logger.error(f"Unexpected response type: {type(response_data)}")
            return ""

        # OpenAI ChatCompletion format
        if "choices" in response_data:
            choices = response_data["choices"]
            if isinstance(choices, list) and choices:
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    # ChatCompletion format: choices[0].message.content
                    message = first_choice.get("message", {})
                    if isinstance(message, dict) and "content" in message:
                        return str(message["content"])
                    # Legacy completion format: choices[0].text
                    if "text" in first_choice:
                        return str(first_choice["text"])

        # Generic content key
        if "content" in response_data:
            return str(response_data["content"])

        # Fallback: extract using regex if jq-style parsing fails
        content = self._extract_content_fallback(response_data)
        if content:
            return content

        logger.error(f"Unrecognized response format: {response_data}")
        return ""

    def _extract_content_fallback(self, response_data: Dict[str, Any]) -> str:
        """Fallback content extraction matching Bash extract_content_from_response."""
        # Convert to JSON string and use regex patterns
        json_str = json.dumps(response_data)
        
        # Try to match OpenAI ChatCompletion format
        pattern = r'"choices"\s*:\s*\[\s*{\s*[^}]*"message"\s*:\s*{\s*[^}]*"content"\s*:\s*"([^"]*)"'
        match = re.search(pattern, json_str)
        if match:
            # Unescape JSON string
            content = match.group(1)
            content = content.replace('\\"', '"')
            content = content.replace('\\n', '\n')
            content = content.replace('\\t', '\t')
            content = content.replace('\\r', '\r')
            content = content.replace('\\b', '\b')
            content = content.replace('\\f', '\f')
            content = content.replace('\\\\', '\\')
            return content

        # Try simpler content pattern
        pattern = r'"content"\s*:\s*"([^"]*)"'
        match = re.search(pattern, json_str)
        if match:
            content = match.group(1)
            # Unescape JSON string
            content = content.replace('\\"', '"')
            content = content.replace('\\n', '\n')
            content = content.replace('\\t', '\t')
            content = content.replace('\\r', '\r')
            content = content.replace('\\b', '\b')
            content = content.replace('\\f', '\f')
            content = content.replace('\\\\', '\\')
            return content

        return ""

    def test_connection(self) -> bool:
        """Test the API connection with a simple request."""
        try:
            response = self.generate("Test", dry_run=False)
            return "Error:" not in response.get("content", "")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_models(self) -> list:
        """Get list of available models if API supports it."""
        if not self.api_url:
            return []
        
        # Try OpenAI-style models endpoint
        try:
            models_url = self.api_url.replace("/chat/completions", "/models")
            headers = {}
            if self.api_key and "localhost" not in self.api_url:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            resp = requests.get(models_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data:
                    return [model["id"] for model in data["data"]]
        except Exception as e:
            logger.debug(f"Failed to get models list: {e}")
        
        return []

    def _mask_api_key(self, api_key: str) -> str:
        """Mask API key for safe logging.
        
        Parameters
        ----------
        api_key : str
            API key to mask
            
        Returns
        -------
        str
            Masked API key showing only first and last few characters
        """
        if not api_key or len(api_key) <= 8:
            return "***"
        
        # Show first 4 and last 4 characters, mask the middle
        return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"

    @staticmethod
    def json_escape(text: str) -> str:
        """Escape text for JSON inclusion, matching Bash json_escape function."""
        # Replace special characters with JSON escape sequences
        text = text.replace("\\", "\\\\")  # Must be first
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        text = text.replace('\b', '\\b')
        text = text.replace('\f', '\\f')
        
        # Return as quoted JSON string
        return f'"{text}"'