"""
Tests for the cache module.
"""
import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from core import cache
from config import settings


class TestGetModelStyles:
    """Tests for get_model_styles function."""
    
    @patch('core.cache.load_from_cache')
    @patch('core.cache.is_cache_fresh')
    def test_uses_fresh_cache(self, mock_is_fresh, mock_load_cache):
        """Test that fresh cache is used when available."""
        mock_cache_data = {
            'timestamp': datetime.now().isoformat(),
            'models': {'mistral': {'description': 'Test'}}
        }
        mock_load_cache.return_value = mock_cache_data
        mock_is_fresh.return_value = True
        
        result = cache.get_model_styles()
        
        assert result == mock_cache_data['models']
        mock_load_cache.assert_called_once()
        mock_is_fresh.assert_called_once_with(mock_cache_data)
    
    @patch('core.cache.load_from_cache')
    @patch('core.cache.load_from_yaml')
    @patch('core.cache.save_to_cache')
    def test_loads_from_yaml_when_cache_missing(self, mock_save, mock_load_yaml, mock_load_cache):
        """Test that YAML is loaded when cache is missing."""
        mock_load_cache.return_value = None
        mock_yaml_data = {'claude': {'description': 'Analytical'}}
        mock_load_yaml.return_value = mock_yaml_data
        
        result = cache.get_model_styles()
        
        assert result == mock_yaml_data
        mock_load_yaml.assert_called_once()
        mock_save.assert_called_once_with(mock_yaml_data)


class TestIsCacheFresh:
    """Tests for is_cache_fresh function."""
    
    def test_fresh_cache(self):
        """Test with fresh cache data."""
        cache_data = {
            'timestamp': datetime.now().isoformat()
        }
        result = cache.is_cache_fresh(cache_data)
        assert result is True
    
    def test_stale_cache(self):
        """Test with stale cache data."""
        old_time = datetime.now() - timedelta(days=30)
        cache_data = {
            'timestamp': old_time.isoformat()
        }
        result = cache.is_cache_fresh(cache_data)
        assert result is False
    
    def test_missing_timestamp(self):
        """Test with missing timestamp."""
        cache_data = {}
        result = cache.is_cache_fresh(cache_data)
        assert result is False
    
    def test_invalid_timestamp(self):
        """Test with invalid timestamp format."""
        cache_data = {
            'timestamp': 'invalid-timestamp'
        }
        result = cache.is_cache_fresh(cache_data)
        assert result is False


class TestLoadFromYaml:
    """Tests for load_from_yaml function."""
    
    @patch('builtins.open', create=True)
    @patch('yaml.safe_load')
    def test_load_valid_yaml(self, mock_yaml_load, mock_open):
        """Test loading valid YAML file."""
        mock_data = {'mistral': {'description': 'Test'}}
        mock_yaml_load.return_value = mock_data
        
        result = cache.load_from_yaml()
        
        assert result == mock_data
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_missing_yaml_file(self, mock_open):
        """Test handling of missing YAML file."""
        result = cache.load_from_yaml()
        assert result == {}


class TestSaveToCache:
    """Tests for save_to_cache function."""
    
    def test_save_valid_data(self, tmp_path):
        """Test saving valid data to cache."""
        # Temporarily override the cache file setting
        original_cache_file = settings.CACHE_FILE
        settings.CACHE_FILE = str(tmp_path / "test_cache.json")
        
        try:
            test_models = {'mistral': {'description': 'Test'}}
            result = cache.save_to_cache(test_models)
            
            assert result is True
            assert os.path.exists(settings.CACHE_FILE)
            
            # Verify the saved data
            with open(settings.CACHE_FILE, 'r') as f:
                saved_data = json.load(f)
            
            assert 'timestamp' in saved_data
            assert saved_data['models'] == test_models
        finally:
            settings.CACHE_FILE = original_cache_file


class TestLoadFromCache:
    """Tests for load_from_cache function."""
    
    def test_load_existing_cache(self, tmp_path):
        """Test loading existing cache file."""
        # Create a test cache file
        cache_file = tmp_path / "cache.json"
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'models': {'test': 'data'}
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        # Temporarily override settings
        original_cache_file = settings.CACHE_FILE
        settings.CACHE_FILE = str(cache_file)
        
        try:
            result = cache.load_from_cache()
            assert result == cache_data
        finally:
            settings.CACHE_FILE = original_cache_file
    
    def test_load_nonexistent_cache(self):
        """Test loading non-existent cache file."""
        original_cache_file = settings.CACHE_FILE
        settings.CACHE_FILE = "/nonexistent/cache.json"
        
        try:
            result = cache.load_from_cache()
            assert result is None
        finally:
            settings.CACHE_FILE = original_cache_file
    
    def test_load_corrupted_cache(self, tmp_path):
        """Test loading corrupted cache file."""
        cache_file = tmp_path / "corrupted_cache.json"
        with open(cache_file, 'w') as f:
            f.write("{ invalid json }")
        
        original_cache_file = settings.CACHE_FILE
        settings.CACHE_FILE = str(cache_file)
        
        try:
            result = cache.load_from_cache()
            assert result is None
        finally:
            settings.CACHE_FILE = original_cache_file
