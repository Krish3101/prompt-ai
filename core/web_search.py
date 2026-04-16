"""
Web search and scraping module for fetching model prompt style information.

This module uses DuckDuckGo search to find latest information about AI models
and their preferred prompt styles from the web.
"""

import requests
from typing import Dict, Optional
import logging
from bs4 import BeautifulSoup
import time
import os
import json
from config import settings

logger = logging.getLogger(__name__)


def search_duckduckgo(query: str, max_results: int = 3) -> list:
    """
    Search DuckDuckGo and return results.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        list: Search results with title and snippet
    """
    try:
        # Use DuckDuckGo HTML search (no API key needed)
        url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        data = {'q': query}
        
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Parse search results
        for result in soup.find_all('div', class_='result', limit=max_results):
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')
            
            if title_elem:
                results.append({
                    'title': title_elem.get_text(strip=True),
                    'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                    'url': title_elem.get('href', '')
                })
        
        return results
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return []


def search_model_best_practices(model_id: str) -> Dict:
    """
    Searches for best practices and prompt formatting for a specific model.
    
    Uses real web search via DuckDuckGo to find latest information.
    
    Args:
        model_id: The model identifier (e.g., "anthropic/claude-3-opus")
        
    Returns:
        dict: Model information including name, format, and best practices
    """
    logger.info(f"Searching for best practices for model: {model_id}")
    # Respect feature flag
    if not settings.ENABLE_WEB_SEARCH:
        logger.info("Web search disabled by settings; returning generic info")
        model_name = model_id.split('/')[-1] if '/' in model_id else model_id
        return {
            'model_id': model_id,
            'model_name': model_name,
            'preferred_format': 'Clear, structured instructions with specific examples',
            'best_practices': 'Be specific, provide context, use clear formatting, and break complex tasks into steps.',
            'note': 'Web search disabled; using generic guidance'
        }
    
    # Extract model name from ID
    model_name = model_id.split('/')[-1] if '/' in model_id else model_id
    
    # Check if this is a common model we know about
    known_models = {
        'gpt-5': {
            'note': 'GPT-5 is not released yet. Using GPT-4 Turbo instead.',
            'actual_model': 'openai/gpt-4-turbo',
            'format': 'System prompt with clear role definition, then detailed instructions with examples and constraints',
            'practices': 'Use structured output format. Provide context, examples, and specific requirements. GPT-4 Turbo supports JSON mode and function calling.'
        },
        'chatgpt-5': {
            'note': 'ChatGPT-5 is not released yet. Using GPT-4 Turbo instead.',
            'actual_model': 'openai/gpt-4-turbo',
            'format': 'System prompt with clear role definition, then detailed instructions with examples and constraints',
            'practices': 'Use structured output format. Provide context, examples, and specific requirements. GPT-4 Turbo supports JSON mode and function calling.'
        },
        'gpt-4-turbo': {
            'actual_model': 'openai/gpt-4-turbo',
            'format': 'System + user messages. Use clear role definitions and structured instructions',
            'practices': 'Excellent for complex reasoning. Use JSON mode for structured output. Provide detailed context and examples.'
        },
        'claude-3-opus': {
            'actual_model': 'anthropic/claude-3-opus',
            'format': 'Use XML tags for structure: <instructions>, <context>, <examples>. Claude responds well to chain-of-thought prompting.',
            'practices': 'Best for analysis and reasoning. Use thinking tags. Provide extensive context. Claude excels at following complex instructions.'
        },
        'claude-3-sonnet': {
            'actual_model': 'anthropic/claude-3-sonnet',
            'format': 'XML-structured prompts with clear sections. Use tags like <task>, <rules>, <output_format>',
            'practices': 'Balance of speed and quality. Great for analysis. Use structured thinking approach.'
        },
        'gemini-pro-1.5': {
            'actual_model': 'google/gemini-pro-1.5',
            'format': 'Clear, numbered instructions. Handles very long context (1M tokens)',
            'practices': 'Excellent for long documents. Use step-by-step instructions. Great for research and analysis.'
        }
    }
    
    # Normalize model ID for lookup
    model_key = model_id.lower().replace(' ', '-').replace('_', '-')
    
    if model_key in known_models:
        info = known_models[model_key]
        return {
            'model_id': info.get('actual_model', model_id),
            'model_name': model_name,
            'preferred_format': info['format'],
            'best_practices': info['practices'],
            'note': info.get('note', '')
        }
    
    # File cache check
    cache_dir = os.path.join('data', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, 'web_model_info.json')
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                stored = json.load(f)
            entry = stored.get(model_key)
            if entry and time.time() - entry.get('ts', 0) < settings.CACHE_DURATION_DAYS * 86400:
                logger.info("Returning cached web search info")
                return entry['data']
    except Exception:
        pass

    # Use real web search to find latest information
    logger.info(f"Searching web for model: {model_id}")
    search_query = f"{model_name} AI model prompt best practices format"
    
    search_results = search_duckduckgo(search_query, max_results=3)
    
    if search_results:
        # Compile information from search results
        snippets = ' '.join([r['snippet'] for r in search_results[:3]])
        
        # Use brief AI analysis to extract key information
        from core import model_api
        
        analysis_prompt = f"""Based on these search results about the AI model "{model_name}":

{snippets}

Extract:
1. Preferred prompt format (system/user, XML tags, etc.)
2. 1-2 key best practices

Format: Format: [format]
Practices: [practices]

Be brief and specific."""
        
        try:
            response = model_api.call_openrouter(
                prompt=analysis_prompt,
                model="mistralai/mistral-7b-instruct:free"
            )
            
            # Parse response
            preferred_format = "Clear, structured instructions"
            best_practices = "Use specific examples and clear requirements"
            
            for line in response.strip().split('\n'):
                if line.startswith('Format:'):
                    preferred_format = line.replace('Format:', '').strip()
                elif line.startswith('Practices:'):
                    best_practices = line.replace('Practices:', '').strip()
            
            data = {
                'model_id': model_id,
                'model_name': model_name,
                'preferred_format': preferred_format,
                'best_practices': best_practices,
                'note': f'Information from web search: {search_results[0]["title"]}'
            }
            # Save to cache file
            try:
                blob = {}
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        blob = json.load(f)
                blob[model_key] = {'ts': time.time(), 'data': data}
                tmp = cache_path + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(blob, f, indent=2, ensure_ascii=False)
                os.replace(tmp, cache_path)
            except Exception:
                pass
            return data
        except:
            pass
    
    # Fallback to generic information
    logger.warning(f"No web results found for {model_id}, using generic info")
    return {
        'model_id': model_id,
        'model_name': model_name,
        'preferred_format': 'Clear, structured instructions with specific examples',
        'best_practices': 'Be specific, provide context, use clear formatting, and break complex tasks into steps.',
        'note': 'Using generic prompt engineering best practices'
    }
