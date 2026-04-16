"""
Tests for backend configuration functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from config import settings
from core import model_api


class TestGetApiConfig:
    """Tests for get_api_config function"""
    
    @patch('config.settings.API_BACKEND', 'openrouter')
    @patch('config.settings.OPENROUTER_API_KEY', 'test-key')
    def test_openrouter_config(self):
        """Test OpenRouter configuration"""
        config = model_api.get_api_config()
        
        assert config['api_url'] == settings.OPENROUTER_API_URL
        assert 'Authorization' in config['headers']
        assert config['format'] == 'openai'
        assert config['requires_auth'] is True
    
    @patch('config.settings.API_BACKEND', 'lmstudio')
    def test_lmstudio_config(self):
        """Test LM Studio configuration"""
        config = model_api.get_api_config()
        
        assert config['api_url'] == settings.LMSTUDIO_API_URL
        assert 'Authorization' not in config['headers']
        assert config['format'] == 'openai'
        assert config['requires_auth'] is False
    
    @patch('config.settings.API_BACKEND', 'ollama')
    def test_ollama_config(self):
        """Test Ollama configuration"""
        config = model_api.get_api_config()
        
        assert config['api_url'] == settings.OLLAMA_API_URL
        assert 'Authorization' not in config['headers']
        assert config['format'] == 'ollama'
        assert config['requires_auth'] is False
    
    @patch('config.settings.API_BACKEND', 'custom')
    @patch('config.settings.CUSTOM_API_KEY', 'custom-key')
    def test_custom_config_with_key(self):
        """Test Custom API configuration with API key"""
        config = model_api.get_api_config()
        
        assert config['api_url'] == settings.CUSTOM_API_URL
        assert 'Authorization' in config['headers']
        assert config['format'] == 'openai'
        assert config['requires_auth'] is True
    
    @patch('config.settings.API_BACKEND', 'custom')
    @patch('config.settings.CUSTOM_API_KEY', '')
    def test_custom_config_without_key(self):
        """Test Custom API configuration without API key"""
        config = model_api.get_api_config()
        
        assert config['api_url'] == settings.CUSTOM_API_URL
        assert 'Authorization' not in config['headers']
        assert config['format'] == 'openai'
        assert config['requires_auth'] is False


class TestFormatRequest:
    """Tests for request formatting functions"""
    
    def test_format_request_openai(self):
        """Test OpenAI format request"""
        result = model_api.format_request_openai("test prompt", "test-model")
        
        assert 'model' in result
        assert 'messages' in result
        assert result['model'] == 'test-model'
        assert len(result['messages']) == 1
        assert result['messages'][0]['role'] == 'user'
        assert result['messages'][0]['content'] == 'test prompt'
    
    def test_format_request_ollama(self):
        """Test Ollama format request"""
        result = model_api.format_request_ollama("test prompt", "test-model")
        
        assert 'model' in result
        assert 'prompt' in result
        assert 'stream' in result
        assert result['model'] == 'test-model'
        assert result['prompt'] == 'test prompt'
        assert result['stream'] is False


class TestExtractResponse:
    """Tests for response extraction functions"""
    
    def test_extract_response_openai(self):
        """Test OpenAI format response extraction"""
        response = {
            'choices': [
                {
                    'message': {
                        'content': 'test response'
                    }
                }
            ]
        }
        
        result = model_api.extract_response_openai(response)
        assert result == 'test response'
    
    def test_extract_response_ollama(self):
        """Test Ollama format response extraction"""
        response = {
            'response': 'test response'
        }
        
        result = model_api.extract_response_ollama(response)
        assert result == 'test response'


class TestBackendErrorMessages:
    """Tests for backend-specific error messages"""
    
    @patch('config.settings.API_BACKEND', 'openrouter')
    @patch('core.model_api.requests.post')
    def test_openrouter_401_error_message(self, mock_post):
        """Test OpenRouter 401 error returns helpful message"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        import requests
        error = requests.exceptions.HTTPError("401")
        error.response = mock_response
        mock_response.raise_for_status.side_effect = error
        mock_post.return_value = mock_response
        
        # Set API key to avoid simulation mode
        original_key = settings.OPENROUTER_API_KEY
        settings.OPENROUTER_API_KEY = "test-key"
        
        try:
            result = model_api.call_openrouter("test prompt")
            assert "Authentication failed" in result
            assert "OPENROUTER_API_KEY" in result
        finally:
            settings.OPENROUTER_API_KEY = original_key
    
    @patch('config.settings.API_BACKEND', 'lmstudio')
    @patch('core.model_api.requests.post')
    def test_lmstudio_connection_error_message(self, mock_post):
        """Test LM Studio connection error returns helpful message"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        result = model_api.call_openrouter("test prompt")
        assert "Error" in result
        assert "lmstudio" in result.lower()


class TestBackendConfigEndpoint:
    """Tests for /api/config endpoint"""
    
    def test_config_endpoint_returns_backends(self):
        """Test that config endpoint returns all backends"""
        from app import app
        
        client = app.test_client()
        response = client.get('/api/config')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'backend' in data
        assert 'backends' in data
        assert 'default_model' in data
        
        # Check all backends are present
        assert 'openrouter' in data['backends']
        assert 'lmstudio' in data['backends']
        assert 'ollama' in data['backends']
        assert 'custom' in data['backends']
        
        # Check each backend has required fields
        for backend_name, backend_info in data['backends'].items():
            assert 'name' in backend_info
            assert 'configured' in backend_info
            assert 'url' in backend_info


class TestConnectionTest:
    """Tests for connection testing"""
    
    @patch('core.model_api.call_openrouter')
    def test_test_api_connection_success(self, mock_call):
        """Test successful API connection"""
        mock_call.return_value = "API connection successful"
        
        result = model_api.test_api_connection()
        assert result is True
    
    @patch('core.model_api.call_openrouter')
    def test_test_api_connection_failure(self, mock_call):
        """Test failed API connection"""
        mock_call.return_value = "Error: Connection failed"
        
        result = model_api.test_api_connection()
        assert result is False
    
    @patch('core.model_api.call_openrouter')
    def test_test_api_connection_exception(self, mock_call):
        """Test API connection with exception"""
        mock_call.side_effect = Exception("Test exception")
        
        result = model_api.test_api_connection()
        assert result is False
