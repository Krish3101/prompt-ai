import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
os.makedirs('data/logs', exist_ok=True)
os.makedirs('data/cache', exist_ok=True)
log_filename = f"data/logs/app_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_filename), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max request size
HISTORY_FILE = 'data/cache/history.json'

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def generate_offline_prompt(user_text: str, model_id: str) -> str:
    """Fallback offline generator using a hardcoded template."""
    return f"""Please act as an expert AI assistant optimized for the {model_id} model.

I need help with the following request:
---
{user_text}
---

Please execute this request by breaking it down into clear, logical steps, improving the grammar, and providing a comprehensive response."""

def call_llm_api(user_text: str, model_id: str, action: str = "Optimize") -> str:
    """Attempts to call an LLM API. Falls back to offline mode if it fails."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.info("No API key found. Using offline mode.")
        return generate_offline_prompt(user_text, model_id)
        
    try:
        logger.info("Attempting to use LLM via OpenRouter...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "google/gemini-2.0-pro-exp-02-05:free",
                "messages": [
                    {"role": "system", "content": "You are an expert prompt engineer. Use your web search capabilities if needed to find the latest best practices for the target model."},
                    {"role": "user", "content": f"{action} this prompt for {model_id}:\n\n{user_text}"}
                ],
                "plugins": [{"id": "web"}]
            },
            timeout=15
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(f"LLM API failed, falling back to offline mode: {e}")
        
    return generate_offline_prompt(user_text, model_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def api_generate_prompt():
    try:
        data = request.get_json()
        user_input = data.get('user_text')
        model_id = data.get('model', 'mistral')
        custom_model_id = data.get('custom_model_id')
        
        if not user_input:
            return jsonify({"error": "Missing 'user_text'"}), 400

        actual_model = custom_model_id if custom_model_id else model_id
        final_prompt = call_llm_api(user_input, actual_model, action="Optimize")
        
        return jsonify({"generated_prompt": final_prompt, "model_used": actual_model})
    except Exception as e:
        logger.error(f"Error in /api/generate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/refine', methods=['POST'])
def api_refine_prompt():
    try:
        data = request.get_json()
        previous_prompt = data.get('previous_prompt')
        feedback = data.get('feedback')
        model_id = data.get('model', 'mistral')
        custom_model_id = data.get('custom_model_id')
        
        if not previous_prompt or not feedback:
            return jsonify({"error": "Missing required fields"}), 400

        actual_model = custom_model_id if custom_model_id else model_id
        refine_req = f"Previous: {previous_prompt}\nFeedback: {feedback}"
        refined_prompt = call_llm_api(refine_req, actual_model, action="Refine")
        
        return jsonify({"generated_prompt": refined_prompt, "model_used": actual_model})
    except Exception as e:
        logger.error(f"Error in /api/refine: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def api_get_config():
    is_online = bool(os.getenv("OPENROUTER_API_KEY"))
    return jsonify({
        "backend": "offline" if not is_online else "openrouter",
        "backends": {
            "offline": {"name": "Offline Mode (Hardcoded Template)", "configured": True},
            "openrouter": {"name": "OpenRouter (LLM)", "configured": is_online}
        },
        "default_model": "mistralai/mistral-7b-instruct:free"
    })

@app.route('/api/history/save', methods=['POST'])
def api_save_history():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        model = data.get('model', 'mistral')
        user_input = data.get('input', '')
        
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400
            
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
                
        new_id = int(datetime.utcnow().timestamp())
        entry = {
            "id": new_id, "prompt": prompt, "model": model,
            "user_input": user_input, "timestamp": datetime.utcnow().isoformat(),
            "favorite": False
        }
        history.insert(0, entry)
        if len(history) > 100:
            history = history[:100]
            
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
            
        return jsonify({"success": True, "id": new_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def api_get_history():
    try:
        if not os.path.exists(HISTORY_FILE):
            return jsonify([])
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
            
        search = request.args.get('search', '').lower()
        favorites_only = request.args.get('favorites') == 'true'
        
        result = [item for item in history if 
                  (not search or search in item.get('prompt', '').lower()) and 
                  (not favorites_only or item.get('favorite', False))]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/<int:item_id>', methods=['DELETE'])
def api_delete_history(item_id):
    try:
        if not os.path.exists(HISTORY_FILE):
            return jsonify({"error": "Not found"}), 404
        with open(HISTORY_FILE, 'r') as f:
            history = [h for h in json.load(f) if h.get('id') != item_id]
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
        return jsonify({"success": True})
    except Exception:
        return jsonify({"error": "Error deleting"}), 500

@app.route('/api/history/<int:item_id>/favorite', methods=['POST'])
def api_toggle_favorite(item_id):
    try:
        if not os.path.exists(HISTORY_FILE):
            return jsonify({"error": "Not found"}), 404
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        for item in history:
            if item.get('id') == item_id:
                item['favorite'] = not item.get('favorite', False)
                break
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
        return jsonify({"success": True})
    except Exception:
        return jsonify({"error": "Error toggling favorite"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
