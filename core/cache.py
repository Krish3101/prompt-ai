import json
import os
from datetime import datetime, timedelta
from config import settings
import yaml
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_model_styles() -> dict:
    """
    Loads model style information with intelligent caching.
    
    Priority:
    1. Check JSON cache - if fresh, use it
    2. If cache is stale or missing, load from YAML
    3. Update cache with fresh data
    
    Returns:
        dict: Model style configurations
    """
    logger.info("Loading model styles...")
    
    # 1. Check for cached version
    cache_data = load_from_cache()
    if cache_data and is_cache_fresh(cache_data):
        logger.info("Using fresh cache data")
        return cache_data.get('models', {})
    
    # 2. Cache is stale or missing, load from YAML
    logger.info("Cache is stale or missing, loading from YAML configuration")
    models = load_from_yaml()
    
    # Save to cache
    save_to_cache(models)
    
    return models


def load_from_cache() -> Optional[Dict]:
    """
    Loads model styles from JSON cache.
    
    Returns:
        dict: Cached data including timestamp and models
        None: If cache doesn't exist or is invalid
    """
    try:
        if os.path.exists(settings.CACHE_FILE):
            with open(settings.CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                logger.info(f"Loaded cache from {settings.CACHE_FILE}")
                return cache_data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load cache: {e}")
    
    return None


def is_cache_fresh(cache_data: Dict) -> bool:
    """
    Checks if the cache is still fresh based on configured duration.
    
    Args:
        cache_data: Dictionary containing 'timestamp' field
        
    Returns:
        bool: True if cache is fresh, False if stale
    """
    try:
        timestamp_str = cache_data.get('timestamp')
        if not timestamp_str:
            return False
        
        cache_time = datetime.fromisoformat(timestamp_str)
        age = datetime.now() - cache_time
        max_age = timedelta(days=settings.CACHE_DURATION_DAYS)
        
        is_fresh = age < max_age
        logger.info(f"Cache age: {age.days} days, max age: {max_age.days} days, fresh: {is_fresh}")
        return is_fresh
        
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to parse cache timestamp: {e}")
        return False


def load_from_yaml() -> Dict:
    """
    Loads model styles from the static YAML configuration file.
    
    Returns:
        dict: Model configurations
    """
    try:
        with open('config/models.yaml', 'r') as f:
            data = yaml.safe_load(f)
            logger.info("Loaded model configurations from YAML")
            return data or {}
    except FileNotFoundError:
        logger.error("config/models.yaml not found")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML: {e}")
        return {}


def save_to_cache(models: Dict) -> bool:
    """
    Saves model styles to JSON cache with timestamp.
    
    Args:
        models: Model configuration dictionary
        
    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(settings.CACHE_FILE), exist_ok=True)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'models': models
        }
        
        with open(settings.CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.info(f"Saved cache to {settings.CACHE_FILE}")
        return True
        
    except IOError as e:
        logger.error(f"Failed to save cache: {e}")
        return False

