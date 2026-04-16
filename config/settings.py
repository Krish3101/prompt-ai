"""
PromptSmith Application Settings

Central configuration file for all app settings, API keys, and constants.
"""

import os
from pathlib import Path

# Load environment variables from .env file if it exists
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# ===== API SETTINGS =====

# API Backend Selection: openrouter, lmstudio, ollama, or custom
API_BACKEND = os.getenv("API_BACKEND", "openrouter").lower()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# LM Studio Configuration
LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234/v1/chat/completions")

# Ollama Configuration
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

# Custom API Configuration
CUSTOM_API_URL = os.getenv("CUSTOM_API_URL", "http://localhost:8000/v1/chat/completions")
CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "")

# API timeout in seconds
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "30"))

# API retry behavior
API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "2"))
API_RETRY_BACKOFF_SECONDS = float(os.getenv("API_RETRY_BACKOFF_SECONDS", "1.0"))

# Default model to use for generation
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "mistralai/mistral-7b-instruct:free")

# Legacy support
FREE_MODEL = DEFAULT_MODEL
API_URL = OPENROUTER_API_URL

# ===== APPLICATION SETTINGS =====

# Flask app settings
FLASK_ENV = os.getenv("FLASK_ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
PORT = int(os.getenv("PORT", "5001"))
HOST = os.getenv("HOST", "localhost")

# ===== CACHE SETTINGS =====

# Cache duration in days
CACHE_DURATION_DAYS = int(os.getenv("CACHE_DURATION_DAYS", "7"))

# Cache file location
CACHE_FILE = "data/cache/prompt_styles.json"

# History file location
HISTORY_FILE = "data/cache/history.json"

# Maximum history entries to keep
MAX_HISTORY_ENTRIES = int(os.getenv("MAX_HISTORY_ENTRIES", "100"))

# ===== FILE PATHS =====

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data directory
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
LOGS_DIR = DATA_DIR / "logs"

# Config directory
CONFIG_DIR = BASE_DIR / "config"
MODELS_CONFIG = CONFIG_DIR / "models.yaml"
TEMPLATES_CONFIG = CONFIG_DIR / "templates.yaml"

# ===== FEATURE FLAGS =====

# Enable/disable features
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "True").lower() == "true"
ENABLE_QUALITY_SCORER = os.getenv("ENABLE_QUALITY_SCORER", "True").lower() == "true"
ENABLE_HISTORY = os.getenv("ENABLE_HISTORY", "True").lower() == "true"

# ===== WEB SEARCH SETTINGS =====

# DuckDuckGo search settings
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "3"))
SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "10"))

# ===== QUALITY SCORER SETTINGS =====

# Quality score thresholds
SCORE_EXCELLENT = 80
SCORE_GOOD = 60
SCORE_FAIR = 40

# ===== TOKEN COUNTER SETTINGS =====

# Token estimation (characters per token)
CHARS_PER_TOKEN = 4

# Token warning thresholds
TOKEN_WARNING_THRESHOLD = 2000
TOKEN_DANGER_THRESHOLD = 4000

# ===== LOGGING SETTINGS =====

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "promptsmith.log"

# ===== VALIDATION =====

# Placeholder API key value
PLACEHOLDER_API_KEY = "your_api_key_here"

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Only warn about missing API key for OpenRouter backend
    if API_BACKEND == "openrouter" and not OPENROUTER_API_KEY:
        errors.append("OPENROUTER_API_KEY is not set. Please add it to your .env file or switch to a local backend (lmstudio/ollama).")
    
    # Create required directories
    for directory in [DATA_DIR, CACHE_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    return errors

# Validate on import
_errors = validate_config()
if _errors:
    import warnings
    for error in _errors:
        warnings.warn(error)