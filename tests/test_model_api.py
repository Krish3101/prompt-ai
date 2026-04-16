"""
Tests for the model_api module.
"""
import pytest
from unittest.mock import patch, MagicMock
from core import model_api
from config import settings


class TestCallOpenRouter:
    """Tests for call_openrouter function."""
    
    @patch('core.model_api.requests.post')
    def test_successful_api_call(self, mock_post):
        """Test successful API call."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Generated response'}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Set a valid API key
        original_key = settings.OPENROUTER_API_KEY
        settings.OPENROUTER_API_KEY = "test-key-123"
        
        try:
            result = model_api.call_openrouter("Test prompt")
            
            assert result == "Generated response"
            mock_post.assert_called_once()
            
            # Verify the request parameters
            call_args = mock_post.call_args
            assert call_args[0][0] == settings.API_URL
            assert call_args[1]['json']['messages'][0]['content'] == "Test prompt"
        finally:
            settings.OPENROUTER_API_KEY = original_key
    
    def test_no_api_key_returns_simulation(self):
        """Test that simulation is used when API key is not configured."""
        original_key = settings.OPENROUTER_API_KEY
        settings.OPENROUTER_API_KEY = ""
        
        try:
            result = model_api.call_openrouter("Test prompt")
            
            # Should return a simulated response
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            settings.OPENROUTER_API_KEY = original_key
    
    @patch('core.model_api.requests.post')
    def test_api_timeout_error(self, mock_post):
        """Test handling of API timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        original_key = settings.OPENROUTER_API_KEY
        settings.OPENROUTER_API_KEY = "test-key"
        
        try:
            result = model_api.call_openrouter("Test prompt")
            
            # Should return error message
            assert "Error" in result
        finally:
            settings.OPENROUTER_API_KEY = original_key
    
    @patch('core.model_api.requests.post')
    def test_api_http_error(self, mock_post):
        """Test handling of HTTP error."""
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
        mock_post.return_value = mock_response
        
        original_key = settings.OPENROUTER_API_KEY
        settings.OPENROUTER_API_KEY = "test-key"
        
        try:
            result = model_api.call_openrouter("Test prompt")
            
            assert "Error" in result
        finally:
            settings.OPENROUTER_API_KEY = original_key
    
    @patch('core.model_api.requests.post')
    def test_custom_model_parameter(self, mock_post):
        """Test calling with custom model."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Response'}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        original_key = settings.OPENROUTER_API_KEY
        settings.OPENROUTER_API_KEY = "test-key"
        
        try:
            custom_model = "custom/model-id"
            result = model_api.call_openrouter("Test prompt", model=custom_model)
            
            # Verify the custom model was used
            call_args = mock_post.call_args
            assert call_args[1]['json']['model'] == custom_model
        finally:
            settings.OPENROUTER_API_KEY = original_key


class TestGetSimulatedResponse:
    """Tests for _get_simulated_response function."""
    
    def test_returns_string(self):
        """Test that simulation returns a string."""
        result = model_api._get_simulated_response("Test prompt", "mistral")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_includes_model_name(self):
        """Test that simulation includes the model name."""
        model = "test-model"
        result = model_api._get_simulated_response("Test prompt", model)
        assert model in result


class TestTestApiConnection:
    """Tests for test_api_connection function."""
    
    @patch('core.model_api.call_openrouter')
    def test_successful_connection(self, mock_call):
        """Test successful API connection."""
        mock_call.return_value = "API connection successful"
        
        result = model_api.test_api_connection()
        assert result is True
    
    @patch('core.model_api.call_openrouter')
    def test_failed_connection(self, mock_call):
        """Test failed API connection."""
        mock_call.return_value = "Error: Connection failed"
        
        result = model_api.test_api_connection()
        assert result is False
    
    @patch('core.model_api.call_openrouter')
    def test_exception_during_connection(self, mock_call):
        """Test exception during connection test."""
        mock_call.side_effect = Exception("Test exception")
        
        result = model_api.test_api_connection()
        assert result is False
