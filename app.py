from flask import Flask, render_template, request, jsonify
from core import generator
from config import settings
from utils.helpers import estimate_tokens
from utils import validation
import json
import logging
import os
import yaml
from datetime import datetime

# Configure logging
os.makedirs('data/logs', exist_ok=True)
log_filename = f"data/logs/app_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security: Limit request size to prevent DoS attacks
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max request size

# 1. Serve the main HTML page
@app.route('/')
def index():
    """Serves the main index.html page."""
    logger.info("Serving index page")
    return render_template('index.html')

# 2. API endpoint for generating a new prompt
@app.route('/api/generate', methods=['POST'])
def api_generate_prompt():
    """
    Handles the POST request from the frontend to generate a prompt.
    """
    try:
        data = request.get_json()
        user_input = data.get('user_text')
        model_id = data.get('model') # e.g., "mistral", "claude", "custom"
        custom_model_id = data.get('custom_model_id')  # For custom models
        
        logger.info(f"Generate request received for model: {model_id}")

        # Validate inputs
        if not user_input or not model_id:
            logger.warning("Missing required fields in generate request")
            return jsonify({"error": "Missing 'user_text' or 'model'"}), 400
        
        # Basic input validation
        is_valid, err = validation.validate_user_text(user_input)
        if not is_valid:
            logger.warning(f"Invalid user_text: {err}")
            return jsonify({"error": err}), 400

        # Use custom model ID if provided
        actual_model = custom_model_id if custom_model_id else model_id

        # Call our core logic
        final_prompt = generator.expand_prompt(
            user_text=user_input,
            model_id=actual_model
        )
        
        logger.info("Prompt generated successfully")
        return jsonify({
            "generated_prompt": final_prompt,
            "model_used": actual_model
        })

    except Exception as e:
        logger.error(f"Error in /api/generate: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# 3. API endpoint for refining an existing prompt
@app.route('/api/refine', methods=['POST'])
def api_refine_prompt():
    """
    Handles the POST request from the frontend to refine a prompt.
    """
    try:
        data = request.get_json()
        previous_prompt = data.get('previous_prompt')
        feedback = data.get('feedback')
        model_id = data.get('model')
        custom_model_id = data.get('custom_model_id')  # For custom models
        
        logger.info(f"Refine request received for model: {model_id}")

        # Validate inputs
        if not previous_prompt or not feedback or not model_id:
            logger.warning("Missing required fields in refine request")
            return jsonify({"error": "Missing required fields"}), 400
        
        # Use custom model ID if provided
        actual_model = custom_model_id if custom_model_id else model_id

        # Call our core logic
        refined_prompt = generator.refine_prompt(
            previous_prompt=previous_prompt,
            feedback=feedback,
            model_id=actual_model
        )
        
        logger.info("Prompt refined successfully")
        return jsonify({
            "generated_prompt": refined_prompt,
            "model_used": actual_model
        })

    except Exception as e:
        logger.error(f"Error in /api/refine: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 4. API endpoint for searching model best practices
@app.route('/api/search-model', methods=['POST'])
def api_search_model():
    """
    Searches for best practices and prompt formatting for a specific model.
    """
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        
        logger.info(f"Model search request for: {model_id}")
        
        if not model_id:
            return jsonify({"error": "Missing 'model_id'"}), 400
        
        # Search for model information
        from core import web_search
        model_info = web_search.search_model_best_practices(model_id)
        
        logger.info(f"Model info retrieved for {model_id}")
        return jsonify(model_info)
        
    except Exception as e:
        logger.error(f"Error in /api/search-model: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 5. API endpoint for saving prompt to history
@app.route('/api/history/save', methods=['POST'])
def api_save_history():
    """
    Saves a prompt to history.
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        model = data.get('model')
        user_input = data.get('user_input', '')
        
        if not prompt or not model:
            return jsonify({"error": "Missing prompt or model"}), 400
        
        # Load existing history
        history_file = str(settings.HISTORY_FILE)
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                # Corrupted history; start clean but don't crash
                history = []
        else:
            history = []
        
        # Add new entry
        entry = {
            "id": len(history) + 1,
            "prompt": prompt,
            "model": model,
            "user_input": user_input,
            "timestamp": datetime.now().isoformat(),
            "favorite": False
        }
        
        history.insert(0, entry)  # Add to beginning
        
        # Keep only last N entries from settings
        history = history[: settings.MAX_HISTORY_ENTRIES]
        
        # Save
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Saved prompt to history (ID: {entry['id']})")
        return jsonify({"success": True, "id": entry['id']})
        
    except Exception as e:
        logger.error(f"Error saving history: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 6. API endpoint for getting history
@app.route('/api/history', methods=['GET'])
def api_get_history():
    """
    Retrieves prompt history.
    """
    try:
        history_file = str(settings.HISTORY_FILE)
        
        if not os.path.exists(history_file):
            return jsonify([])
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []
        
        # Apply filters if provided
        search = request.args.get('search', '').lower()
        model_filter = request.args.get('model', '').lower()
        favorites_only = request.args.get('favorites') == 'true'
        
        filtered = history
        
        if search:
            filtered = [h for h in filtered if search in h['prompt'].lower() or search in h.get('user_input', '').lower()]
        
        if model_filter:
            filtered = [h for h in filtered if model_filter in h['model'].lower()]
        
        if favorites_only:
            filtered = [h for h in filtered if h.get('favorite', False)]
        
        logger.info(f"Retrieved {len(filtered)} history items")
        return jsonify(filtered)
        
    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 7. API endpoint for deleting history item
@app.route('/api/history/<int:item_id>', methods=['DELETE'])
def api_delete_history(item_id):
    """
    Deletes a history item.
    """
    try:
        history_file = str(settings.HISTORY_FILE)
        
        if not os.path.exists(history_file):
            return jsonify({"error": "History not found"}), 404
        
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # Find and remove
        history = [h for h in history if h['id'] != item_id]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)        
        logger.info(f"Deleted history item {item_id}")
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Error deleting history: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 8. API endpoint for toggling favorite
@app.route('/api/history/<int:item_id>/favorite', methods=['POST'])
def api_toggle_favorite(item_id):
    """
    Toggles favorite status of a history item.
    """
    try:
        history_file = str(settings.HISTORY_FILE)
        
        if not os.path.exists(history_file):
            return jsonify({"error": "History not found"}), 404
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"error": "History is corrupted"}), 500
        
        # Find and toggle
        for item in history:
            if item['id'] == item_id:
                item['favorite'] = not item.get('favorite', False)
                break
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Toggled favorite for history item {item_id}")
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 9. API endpoint for getting templates
@app.route('/api/templates', methods=['GET'])
def api_get_templates():
    """
    Retrieves available prompt templates.
    """
    try:
        templates_file = str(settings.TEMPLATES_CONFIG)
        
        if not os.path.exists(templates_file):
            return jsonify({})
        
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        logger.info(f"Retrieved {len(templates)} templates")
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 10. API endpoint for analyzing prompt quality
@app.route('/api/analyze-quality', methods=['POST'])
def api_analyze_quality():
    """
    Analyzes the quality of a prompt and provides feedback.
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        model = data.get('model', 'mistral')
        
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400
        
        logger.info(f"Analyzing prompt quality for model: {model}")
        
        # Analyze using our generator logic
        analysis = generator.analyze_prompt_quality(prompt, model)
        
        logger.info("Prompt analysis completed")
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing quality: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 10. API endpoint for A/B testing (generate multiple variations)
@app.route('/api/ab-test', methods=['POST'])
def api_ab_test():
    """
    Generates 3 variations of a prompt for A/B testing.
    """
    try:
        data = request.get_json()
        user_input = data.get('input')
        model = data.get('model', 'mistral')
        
        if not user_input:
            return jsonify({"error": "Missing input"}), 400
        
        logger.info(f"Generating A/B test variations for model: {model}")
        
        # Generate 3 different variations with different emphasis
        variations = []
        strategies = [
            {"name": "Detailed & Structured", "modifier": "Focus on structure, examples, and comprehensive detail."},
            {"name": "Concise & Direct", "modifier": "Keep it brief and to the point with clear objectives."},
            {"name": "Creative with Context", "modifier": "Include creative angles and rich contextual background."}
        ]
        
        for i, strategy in enumerate(strategies, 1):
            # Add strategy hint to the input
            modified_input = f"{user_input}\n\nStyle note: {strategy['modifier']}"
            
            # Generate using the AI
            prompt = generator.expand_prompt(modified_input, model)
            
            # Calculate stats
            token_count = estimate_tokens(prompt)
            word_count = len(prompt.split())
            char_count = len(prompt)
            
            variations.append({
                "id": i,
                "prompt": prompt,
                "strategy": strategy['name'],
                "stats": {
                    "tokens": token_count,
                    "words": word_count,
                    "characters": char_count
                }
            })
        
        logger.info(f"Generated {len(variations)} variations successfully")
        
        return jsonify({
            "variations": variations,
            "model": model,
            "user_input": user_input
        })
        
    except Exception as e:
        logger.error(f"Error generating A/B test: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 11. API endpoint for getting backend configuration
@app.route('/api/config', methods=['GET'])
def api_get_config():
    """
    Returns the current API backend configuration.
    """
    try:
        config = {
            "backend": settings.API_BACKEND,
            "backends": {
                "openrouter": {
                    "name": "OpenRouter",
                    "configured": bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY != settings.PLACEHOLDER_API_KEY),
                    "url": settings.OPENROUTER_API_URL
                },
                "lmstudio": {
                    "name": "LM Studio",
                    "configured": True,  # No auth required
                    "url": settings.LMSTUDIO_API_URL
                },
                "ollama": {
                    "name": "Ollama",
                    "configured": True,  # No auth required
                    "url": settings.OLLAMA_API_URL
                },
                "custom": {
                    "name": "Custom API",
                    "configured": bool(settings.CUSTOM_API_URL),
                    "url": settings.CUSTOM_API_URL
                }
            },
            "default_model": settings.DEFAULT_MODEL
        }
        
        logger.info(f"Backend configuration retrieved: {settings.API_BACKEND}")
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve configuration"}), 500


# 12. API endpoint for testing API connection
@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    """
    Tests the API connection with the current backend.
    """
    try:
        from core import model_api
        
        logger.info(f"Testing connection to {settings.API_BACKEND}")
        
        success = model_api.test_api_connection()
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Successfully connected to {settings.API_BACKEND}",
                "backend": settings.API_BACKEND
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Failed to connect to {settings.API_BACKEND}. Check your configuration.",
                "backend": settings.API_BACKEND
            }), 500
        
    except Exception as e:
        logger.error(f"Error testing connection: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "Connection test failed",
            "backend": settings.API_BACKEND
        }), 500


if __name__ == '__main__':
    # Ensure data/cache directories exist
    os.makedirs('data/cache', exist_ok=True)
    os.makedirs('data/logs', exist_ok=True)
    
    logger.info("Starting PromptSmith application...")
    logger.info(f"Server running on http://{settings.HOST}:{settings.PORT}")
    
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
