"""
Comprehensive tests for lib.llm module.

Tests LLM client functionality including API communication, error handling,
and different model configurations.
"""
from unittest.mock import Mock, patch
import pytest
import requests

from giv.lib.llm import LLMClient
from giv.errors import APIError
from giv.constants import DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_API_TIMEOUT


class TestLLMClientInit:
    """Test LLMClient initialization."""
    
    def test_llm_client_default_init(self):
        """Test LLMClient with default parameters."""
        client = LLMClient()
        
        assert client.api_url is None
        assert client.api_key is None
        assert client.model == "default"  # Default model name
        assert client.temperature == DEFAULT_TEMPERATURE
        assert client.max_tokens == DEFAULT_MAX_TOKENS
        assert client.timeout == DEFAULT_API_TIMEOUT
    
    def test_llm_client_custom_init(self):
        """Test LLMClient with custom parameters."""
        client = LLMClient(
            api_url="http://custom:11434",
            api_key="custom_key",
            model="custom_model",
            temperature=0.5,
            max_tokens=4096,
            timeout=60
        )
        
        assert client.api_url == "http://custom:11434"
        assert client.api_key == "custom_key"
        assert client.model == "custom_model"
        assert client.temperature == 0.5
        assert client.max_tokens == 4096
        assert client.timeout == 60
    
    def test_llm_client_parameter_validation(self):
        """Test LLMClient parameter validation."""
        # Test temperature bounds
        client = LLMClient(temperature=0.0)
        assert client.temperature == 0.0
        
        client = LLMClient(temperature=1.0)
        assert client.temperature == 1.0
        
        # Test max_tokens
        client = LLMClient(max_tokens=1)
        assert client.max_tokens == 1
        
        client = LLMClient(max_tokens=32000)
        assert client.max_tokens == 32000


class TestLLMClientAPIGeneration:
    """Test LLM API functionality."""
    
    @patch('requests.post')
    def test_generate_success(self, mock_post):
        """Test successful API generation."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Generated text from OpenAI"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(
            api_url="https://api.openai.com/v1/chat/completions",
            api_key="test_key",
            model="gpt-4"
        )
        
        result = client.generate("Test prompt")
        
        assert result["content"] == "Generated text from OpenAI"
        # Note: success key is not returned by current implementation
        
        # Verify request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check headers
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_key"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        
        # Check request data
        request_data = call_args[1]["json"]
        assert request_data["model"] == "gpt-4"
        assert request_data["messages"][0]["content"] == "Test prompt"
        assert request_data["temperature"] == DEFAULT_TEMPERATURE
        assert request_data["max_completion_tokens"] == DEFAULT_MAX_TOKENS
    
    @patch('requests.post')
    def test_generate_with_custom_params(self, mock_post):
        """Test API with custom parameters."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Generated text"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(
            api_url="https://api.openai.com/v1/chat/completions",
            api_key="test_key",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=1024
        )
        
        result = client.generate("Test prompt")
        
        request_data = mock_post.call_args[1]["json"]
        assert request_data["temperature"] == 0.5
        assert request_data["max_completion_tokens"] == 1024
    
    @patch('requests.post')
    def test_generate_no_choices(self, mock_post):
        """Test API response with no choices."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response
        
        client = LLMClient(
            api_url="https://api.openai.com/v1/chat/completions",
            api_key="test_key"
        )
        
        result = client.generate("Test prompt")
        assert result["content"] == "Error: No content in API response"
    
    @patch('requests.post')
    def test_generate_missing_content(self, mock_post):
        """Test API response with missing content."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {}  # Missing content
            }]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(
            api_url="https://api.openai.com/v1/chat/completions",
            api_key="test_key"
        )
        
        result = client.generate("Test prompt")
        assert result["content"] == "Error: No content in API response"


class TestLLMClientDryRun:
    """Test dry run functionality."""
    
    def test_generate_dry_run(self):
        """Test dry run functionality."""
        client = LLMClient(api_url="https://api.openai.com/v1/chat/completions")
        
        result = client.generate("Test prompt", dry_run=True)
        
        assert result["content"] == "Test prompt"
    
    def test_generate_dry_run_no_api_calls(self):
        """Test that dry run makes no actual API calls."""
        with patch('requests.post') as mock_post:
            client = LLMClient(api_url="http://localhost:11434")
            
            result = client.generate("Test prompt", dry_run=True)
            
            # No API calls should be made
            mock_post.assert_not_called()
            

class TestLLMClientEdgeCases:
    """Test LLM client edge cases."""
    
    def test_generate_empty_prompt(self):
        """Test generating with empty prompt."""
        client = LLMClient()
        
        result = client.generate("", dry_run=True)
        
        assert result["content"] == ""
    
    def test_generate_none_prompt(self):
        """Test generating with None prompt."""
        client = LLMClient()
        
        with pytest.raises(APIError, match="API error: Prompt cannot be None"):
            client.generate(None)
    
    def test_generate_no_api_url(self):
        """Test generating without API URL."""
        client = LLMClient()
        
        with pytest.raises(APIError, match="API error: No API URL configured"):
            client.generate("Test prompt")
    
    @patch('requests.post')
    def test_generate_timeout(self, mock_post):
        """Test API request timeout."""
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        client = LLMClient(
            api_url="http://localhost:11434",
            timeout=1
        )
        
        with pytest.raises(APIError, match="API error: Request timed out"):
            client.generate("Test prompt")
    
    @patch('requests.post')
    def test_generate_connection_error(self, mock_post):
        """Test API connection error."""
        mock_post.side_effect = requests.ConnectionError("Connection refused")
        
        client = LLMClient(api_url="http://localhost:11434")
        
        with pytest.raises(APIError, match="API error: Connection refused"):
            client.generate("Test prompt")


class TestLLMClientIntegration:
    """Test LLM client integration scenarios."""
    
    @patch('requests.post')
    def test_full_api_workflow(self, mock_post):
        """Test complete API workflow."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "This is a generated commit message from GPT"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "total_tokens": 50
            }
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(
            api_url="https://api.openai.com/v1/chat/completions",
            api_key="sk-test-key",
            model="gpt-4",
            temperature=0.8,
            max_tokens=256
        )
        
        prompt = "Generate a commit message for: Fixed bug in authentication"
        result = client.generate(prompt)
        
        assert "generated commit message from gpt" in result["content"].lower()
        
        # Verify authentication and parameters
        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer sk-test-key"
        
        request_data = mock_post.call_args[1]["json"]
        assert request_data["model"] == "gpt-4"
        assert request_data["temperature"] == 0.8
        assert request_data["max_completion_tokens"] == 256
    
    def test_error_recovery_patterns(self):
        """Test error recovery and fallback patterns."""
        # Test that exceptions are properly wrapped
        with patch('requests.post', side_effect=Exception("Unexpected error")):
            client = LLMClient(api_url="http://localhost:11434")
            
            with pytest.raises(APIError) as exc_info:
                client.generate("Test prompt")
            
            assert "Unexpected error" in str(exc_info.value)
    
    def test_client_configuration_priority(self):
        """Test that client configuration takes priority correctly."""
        # Test parameter precedence
        client = LLMClient(
            api_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.5
        )
        
        assert client.api_url == "http://localhost:11434"
        assert client.model == "llama3.2"
        assert client.temperature == 0.5
        
        # Default values should be used for unspecified parameters
        assert client.max_tokens == DEFAULT_MAX_TOKENS
        assert client.timeout == DEFAULT_API_TIMEOUT