import requests
from config import settings
import logging
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


def get_api_config() -> Dict[str, Any]:
    """
    Get API configuration based on the selected backend.
    
    Returns:
        Dict containing api_url, headers, and format_function
    """
    backend = settings.API_BACKEND
    
    if backend == "openrouter":
        return {
            "api_url": settings.OPENROUTER_API_URL,
            "headers": {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5001",
                "X-Title": "PromptSmith AI"
            },
            "format": "openai",
            "requires_auth": True
        }
    elif backend == "lmstudio":
        return {
            "api_url": settings.LMSTUDIO_API_URL,
            "headers": {
                "Content-Type": "application/json"
            },
            "format": "openai",
            "requires_auth": False
        }
    elif backend == "ollama":
        return {
            "api_url": settings.OLLAMA_API_URL,
            "headers": {
                "Content-Type": "application/json"
            },
            "format": "ollama",
            "requires_auth": False
        }
    elif backend == "custom":
        headers = {"Content-Type": "application/json"}
        if settings.CUSTOM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.CUSTOM_API_KEY}"
        return {
            "api_url": settings.CUSTOM_API_URL,
            "headers": headers,
            "format": "openai",
            "requires_auth": bool(settings.CUSTOM_API_KEY)
        }
    else:
        logger.warning(f"Unknown backend '{backend}', defaulting to OpenRouter")
        return {
            "api_url": settings.OPENROUTER_API_URL,
            "headers": {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            "format": "openai",
            "requires_auth": True
        }


def format_request_openai(prompt: str, model: str) -> Dict[str, Any]:
    """Format request for OpenAI-compatible API (OpenRouter, LM Studio, Custom)"""
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }


def format_request_ollama(prompt: str, model: str) -> Dict[str, Any]:
    """Format request for Ollama API"""
    return {
        "model": model,
        "prompt": prompt,
        "stream": False
    }


def extract_response_openai(response_json: Dict[str, Any]) -> str:
    """Extract response from OpenAI-compatible API response"""
    return response_json['choices'][0]['message']['content']


def extract_response_ollama(response_json: Dict[str, Any]) -> str:
    """Extract response from Ollama API response"""
    return response_json['response']


def call_openrouter(prompt: str, model: str = settings.DEFAULT_MODEL) -> str:
    """
    Sends a prompt to the configured API backend and returns the response.
    
    Args:
        prompt: The prompt text to send to the model
        model: The model ID to use (defaults to DEFAULT_MODEL from settings)
        
    Returns:
        str: The generated response from the API
        
    Raises:
        Exception: If API call fails after retries
    """
    logger.info(f"Calling {settings.API_BACKEND} API with model: {model}")
    
    # Get API configuration
    config = get_api_config()
    
    # Check if authentication is configured when required
    if config["requires_auth"]:
        if settings.API_BACKEND == "openrouter" and (not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY == settings.PLACEHOLDER_API_KEY):
            logger.warning("OpenRouter API key not configured, returning simulated response")
            return _get_simulated_response(prompt, model)
        elif settings.API_BACKEND == "custom" and not settings.CUSTOM_API_KEY:
            logger.warning("Custom API key not configured, returning simulated response")
            return _get_simulated_response(prompt, model)
    
    # Format request based on API type
    if config["format"] == "ollama":
        data = format_request_ollama(prompt, model)
        extract_response = extract_response_ollama
    else:  # openai format
        data = format_request_openai(prompt, model)
        extract_response = extract_response_openai
    
    # Basic retry with exponential backoff for transient errors
    attempts = max(1, settings.API_MAX_RETRIES + 1)  # initial try + retries
    backoff = max(0.0, settings.API_RETRY_BACKOFF_SECONDS)

    last_error = None
    for attempt in range(1, attempts + 1):
        result = None  # Initialize result to avoid undefined variable
        try:
            # Log request without exposing sensitive information
            logger.debug(f"Sending request to {settings.API_BACKEND} backend (attempt {attempt}/{attempts})")
            response = requests.post(
                config["api_url"],
                headers=config["headers"],
                json=data,
                timeout=settings.API_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = extract_response(result)
            logger.info("API call successful")
            return generated_text
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_error = f"Connection error (is {settings.API_BACKEND} server running?): {e}"
            logger.warning(last_error)
            if attempt < attempts:
                sleep_for = backoff * (2 ** (attempt - 1))
                time.sleep(sleep_for)
                continue
            else:
                error_msg = f"API request failed after {attempts} attempts. Last error: {e}"
                logger.error(error_msg)
                return f"Error: {error_msg}\n\nTip: Make sure your {settings.API_BACKEND} server is running and accessible."
        except requests.exceptions.HTTPError as e:
            # Non-retryable HTTP errors
            error_msg = f"HTTP error occurred: {e}"
            logger.error(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    if hasattr(e.response, 'text'):
                        logger.error(f"Response: {e.response.text}")
                except Exception:
                    pass  # Ignore errors when trying to log response text
                
                # Provide helpful error messages based on status code
                if e.response.status_code == 401:
                    if settings.API_BACKEND == "openrouter":
                        return f"Error: Authentication failed. Please check your OPENROUTER_API_KEY in .env file.\nGet a free API key at: https://openrouter.ai/keys"
                    else:
                        return f"Error: Authentication failed. Please check your API key configuration."
                elif e.response.status_code == 404:
                    return f"Error: API endpoint not found. Please check your {settings.API_BACKEND.upper()} configuration."
            
            return f"Error: Could not get response from API. {error_msg}"
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            logger.error(error_msg)
            return f"Error: Could not get response from API. {error_msg}"
        except (KeyError, IndexError, ValueError) as e:
            error_msg = f"Unexpected API response format: {e}"
            logger.error(error_msg)
            # Note: Not logging full response data to avoid exposing sensitive information
            return f"Error: Unexpected API response format. {error_msg}"


def _get_simulated_response(prompt: str, model: str) -> str:
    """
    Returns a simulated API response for testing without an API key.
    
    Args:
        prompt: The prompt that was sent
        model: The model that would have been used
        
    Returns:
        str: A simulated response
    """
    logger.info("--- SIMULATING API CALL (No API key configured) ---")
    logger.info(f"Backend: {settings.API_BACKEND}")
    logger.info(f"Model: {model}")
    logger.debug(f"Prompt: {prompt[:100]}...")
    logger.info("---------------------------")
    
    # Simulate a network delay
    import time
    time.sleep(1)

    # Simulated response:
    simulated_response = f"""
Here is a professionally generated prompt, optimized for '{model}':

**Role:** A startup founder who has experienced a significant business failure.
**Topic:** A reflective blog post about the lessons learned from the failure.
**Tone:** Vulnerable, honest, and ultimately optimistic.
**Key Points to Include:**
- The initial excitement and vision.
- The moment things started to go wrong.
- The single biggest mistake that was made.
- The emotional toll of the failure.
- The key lesson that will be carried forward.
**Format:** A 1000-word first-person article.
    """
    return simulated_response


def test_api_connection() -> bool:
    """
    Tests the API connection with a simple prompt.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        test_prompt = "Say 'API connection successful' if you can read this."
        response = call_openrouter(test_prompt, settings.DEFAULT_MODEL)
        
        if "error" in response.lower() and response.startswith("Error:"):
            return False
        
        logger.info("API connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False