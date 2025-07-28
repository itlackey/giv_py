"""
Comprehensive tests for lib.llm module.

Tests LLM client functionality including API communication, error handling,
and different model configurations.
"""
import json
from unittest.mock import Mock, patch, MagicMock
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


@pytest.mark.skip(reason="LLMClient._detect_api_type() method no longer exists")
class TestLLMClientAPIDetection:
    """Test API type detection."""
    
    def test_detect_api_type_ollama(self):
        """Test detecting Ollama API."""
        client = LLMClient(api_url="http://localhost:11434")
        assert client._detect_api_type() == "ollama"
        
        client = LLMClient(api_url="http://localhost:11434/")
        assert client._detect_api_type() == "ollama"
        
        client = LLMClient(api_url="http://192.168.1.100:11434/api/generate")
        assert client._detect_api_type() == "ollama"
    
    def test_detect_api_type_openai(self):
        """Test detecting OpenAI API."""
        client = LLMClient(api_url="https://api.openai.com/v1/chat/completions")
        assert client._detect_api_type() == "openai"
        
        client = LLMClient(api_url="https://api.openai.com/v1")
        assert client._detect_api_type() == "openai"
        
        # Custom OpenAI-compatible endpoints
        client = LLMClient(api_url="https://api.anthropic.com/v1/chat/completions")
        assert client._detect_api_type() == "openai"
    
    def test_detect_api_type_none(self):
        """Test API type detection with no URL."""
        client = LLMClient()
        assert client._detect_api_type() == "ollama"  # Default
    
    def test_detect_api_type_unknown(self):
        """Test detecting unknown API type."""
        client = LLMClient(api_url="https://custom-api.example.com/generate")
        # Should default to openai for unknown HTTPS endpoints
        assert client._detect_api_type() == "openai"


class TestLLMClientOllamaAPI:
    """Test Ollama API functionality."""
    
    @patch('requests.post')
    def test_generate_ollama_success(self, mock_post):
        """Test successful Ollama API generation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": "Generated text from Ollama",
            "done": True
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(
            api_url="http://localhost:11434",
            model="llama3.2"
        )
        
        result = client.generate("Test prompt")
        
        assert result["content"] == "Generated text from Ollama"
        # Note: success key is not returned by current implementation
        
        # Verify request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434"  # Direct URL call
        
        request_data = call_args[1]["json"]  # Implementation uses json= parameter
        assert request_data["model"] == "llama3.2"
        assert request_data["messages"] == [{"role": "user", "content": "Test prompt"}]
        assert request_data["temperature"] == DEFAULT_TEMPERATURE
        assert request_data["max_completion_tokens"] == DEFAULT_MAX_TOKENS
    
    @patch('requests.post')
    def test_generate_ollama_with_options(self, mock_post):
        """Test Ollama API with custom options."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": "Generated text",
            "done": True
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(
            api_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.8,
            max_tokens=2048
        )
        
        result = client.generate("Test prompt")
        
        # Verify options are passed in OpenAI format
        request_data = mock_post.call_args[1]["json"]
        assert request_data["temperature"] == 0.8
        assert request_data["max_completion_tokens"] == 2048
    
    @patch('requests.post')
    def test_generate_ollama_request_error(self, mock_post):
        """Test Ollama API request error."""
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        client = LLMClient(api_url="http://localhost:11434")
        
        with pytest.raises(APIError, match="API error: Connection failed"):
            client.generate("Test prompt")
    
    @patch('requests.post')
    def test_generate_ollama_http_error(self, mock_post):
        """Test Ollama API HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_post.return_value = mock_response
        
        client = LLMClient(api_url="http://localhost:11434")
        
        with pytest.raises(APIError, match="API error: 404 Not Found"):
            client.generate("Test prompt")
    
    @patch('requests.post')
    def test_generate_ollama_invalid_json(self, mock_post):
        """Test Ollama API invalid JSON response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_post.return_value = mock_response
        
        client = LLMClient(api_url="http://localhost:11434")
        
        with pytest.raises(APIError, match="API error: Invalid JSON response"):
            client.generate("Test prompt")


class TestLLMClientOpenAIAPI:
    """Test OpenAI API functionality."""
    
    @patch('requests.post')
    def test_generate_openai_success(self, mock_post):
        """Test successful OpenAI API generation."""
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
    def test_generate_openai_with_custom_params(self, mock_post):
        """Test OpenAI API with custom parameters."""
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
    def test_generate_openai_no_choices(self, mock_post):
        """Test OpenAI API response with no choices."""
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
    def test_generate_openai_missing_content(self, mock_post):
        """Test OpenAI API response with missing content."""
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
    
    def test_generate_dry_run_ollama(self):
        """Test dry run with Ollama API."""
        client = LLMClient(api_url="http://localhost:11434")
        
        result = client.generate("Test prompt", dry_run=True)
        
        assert result["content"] == "Test prompt"
    
    def test_generate_dry_run_openai(self):
        """Test dry run with OpenAI API."""
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


class TestLLMClientURLHandling:
    """Test URL handling and normalization."""
    
    @pytest.mark.skip(reason="LLMClient._build_url() method no longer exists")
    def test_build_url_ollama_basic(self):
        """Test building Ollama URL."""
        client = LLMClient(api_url="http://localhost:11434")
        url = client._build_url()
        assert url == "http://localhost:11434/api/generate"
    
    @pytest.mark.skip(reason="LLMClient._build_url() method no longer exists")
    def test_build_url_ollama_with_path(self):
        """Test building Ollama URL with existing path."""
        client = LLMClient(api_url="http://localhost:11434/api")
        url = client._build_url()
        assert url == "http://localhost:11434/api/generate"
    
    @pytest.mark.skip(reason="LLMClient._build_url() method no longer exists")
    def test_build_url_ollama_with_trailing_slash(self):
        """Test building Ollama URL with trailing slash."""
        client = LLMClient(api_url="http://localhost:11434/")
        url = client._build_url()
        assert url == "http://localhost:11434/api/generate"
    
    @pytest.mark.skip(reason="LLMClient._build_url() method no longer exists")
    def test_build_url_openai(self):
        """Test building OpenAI URL."""
        client = LLMClient(api_url="https://api.openai.com/v1/chat/completions")
        url = client._build_url()
        assert url == "https://api.openai.com/v1/chat/completions"
    
    @pytest.mark.skip(reason="LLMClient._build_url() method no longer exists")
    def test_build_url_openai_base(self):
        """Test building OpenAI URL from base."""
        client = LLMClient(api_url="https://api.openai.com/v1")
        url = client._build_url()
        assert url == "https://api.openai.com/v1/chat/completions"


class TestLLMClientIntegration:
    """Test LLM client integration scenarios."""
    
    @patch('requests.post')
    def test_full_ollama_workflow(self, mock_post):
        """Test complete Ollama workflow."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": "This is a generated commit message",
            "done": True,
            "context": [1, 2, 3]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(
            api_url="http://localhost:11434",
            model="llama3.2:latest",
            temperature=0.7,
            max_tokens=512
        )
        
        prompt = "Generate a commit message for: Added new feature"
        result = client.generate(prompt)
        
        assert "generated commit message" in result["content"].lower()
        
        # Verify all parameters were passed correctly
        request_data = mock_post.call_args[1]["json"]
        assert request_data["model"] == "llama3.2:latest"
        assert request_data["messages"][0]["content"] == prompt
        assert request_data["temperature"] == 0.7
        assert request_data["max_completion_tokens"] == 512
    
    @patch('requests.post')
    def test_full_openai_workflow(self, mock_post):
        """Test complete OpenAI workflow."""
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