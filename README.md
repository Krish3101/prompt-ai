# 🚀 PromptSmith AI

**AI Prompt Refinery & Optimization Platform**

PromptSmith is a powerful web application that helps you create, refine, and optimize AI prompts for any language model. Transform simple ideas into detailed, effective prompts optimized for your target AI model.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Flask](https://img.shields.io/badge/flask-3.0.3-red)
![License](https://img.shields.io/badge/license-MIT-yellow)

## ✨ Core Features

- **Smart Prompt Generation** - Transform simple ideas into detailed, optimized prompts
- **Multi-Model Support** - Optimized for GPT-4, Claude 3, Gemini, Mistral, and custom models  
- **Real-time Refinement** - Iteratively improve prompts with AI assistance
- **Prompt History** - Save, search, and manage all your prompts with favorites
- **Quality Analysis** - Get detailed feedback and improvement suggestions
- **Dark Mode** - Eye-friendly dark theme
- **Mobile Responsive** - Works seamlessly on desktop and mobile devices

## 🚀 Getting Started

For a detailed, step-by-step guide to getting started with PromptSmith, please see the [QUICKSTART.md](QUICKSTART.md) file.

The basic steps are:

1.  **Install Python 3.10+**
2.  **Clone the repository**
3.  **Install dependencies:** `pip install -r requirements.txt`
4.  **Configure your backend** in the `.env` file
5.  **Run the application:** `python app.py`

## 📁 Project Structure

```
promptsmith/
├── app.py                 # Flask application & API endpoints
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── config/               # Configuration files
│   ├── models.yaml      # AI model configurations
│   ├── templates.yaml   # Prompt templates
│   └── settings.py      # App settings
│
├── core/                # Core business logic
│   ├── generator.py     # Prompt generation engine
│   ├── model_api.py     # OpenRouter API integration
│   ├── web_search.py    # DuckDuckGo search + AI analysis
│   └── cache.py         # Caching utilities
│
├── utils/               # Helper utilities
│   ├── helpers.py       # General helpers
│   └── validation.py    # Input validation
│
├── templates/           # HTML templates
│   └── index.html       # Main UI
│
├── static/              # Static assets
│   ├── css/
│   │   └── style.css    # Styles with dark mode
│   └── js/
│       └── main.js      # Frontend logic
│
└── data/                # Data storage
    ├── cache/           # Cached data
    │   ├── history.json # Prompt history
    │   └── prompt_styles.json
    └── logs/            # Application logs
```

## 🔌 API Backend Support

PromptSmith supports multiple AI backends for maximum flexibility:

### OpenRouter (Cloud)
- **Pros**: Access to 100+ models, free tier available, no local setup
- **Cons**: Requires internet connection, API key needed
- **Best for**: Quick start, trying different models, production use

### LM Studio (Local)
- **Pros**: Fully offline, free, privacy-focused, easy to use
- **Cons**: Requires powerful hardware, manual model management
- **Best for**: Privacy-sensitive work, offline usage, development

### Ollama (Local)
- **Pros**: Fully offline, free, simple CLI, optimized for Mac
- **Cons**: Requires hardware resources, limited to supported models
- **Best for**: Mac users, local development, simple deployment

### Custom API
- **Pros**: Use any OpenAI-compatible API, flexible configuration
- **Cons**: Requires technical setup
- **Best for**: Enterprise deployments, custom LLM infrastructure

## 🎨 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/api/generate` | POST | Generate new prompt |
| `/api/refine` | POST | Refine existing prompt |
| `/api/search-model` | POST | Search model best practices |
| `/api/analyze-quality` | POST | Analyze prompt quality |
| `/api/ab-test` | POST | Generate A/B test variations |
| `/api/config` | GET | Get backend configuration |
| `/api/test-connection` | POST | Test API connection |
| `/api/history` | GET | Get prompt history |
| `/api/history/save` | POST | Save prompt to history |
| `/api/history/<id>` | DELETE | Delete history entry |
| `/api/history/<id>/favorite` | POST | Toggle favorite |
| `/api/templates` | GET | Get all templates |

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Generate prompt |
| `Ctrl + K` | Toggle history panel |
| `Ctrl + D` | Toggle dark mode |
| `Esc` | Close modals/panels |

## 🔧 Configuration

### Supported Models
- Mistral 7B (Free)
- Claude 3 Haiku
- ChatGPT (GPT-3.5)
- GPT-4
- GPT-4o (Optimized)
- Gemini Pro
- Llama 3 (Free)
- Custom models via OpenRouter

### Environment Variables

**Backend Configuration:**
```bash
API_BACKEND=openrouter              # openrouter, lmstudio, ollama, or custom
```

**OpenRouter Settings:**
```bash
OPENROUTER_API_KEY=your_key_here    # Get from https://openrouter.ai/keys
```

**LM Studio Settings:**
```bash
LMSTUDIO_API_URL=http://localhost:1234/v1/chat/completions
```

**Ollama Settings:**
```bash
OLLAMA_API_URL=http://localhost:11434/api/generate
```

**Custom API Settings:**
```bash
CUSTOM_API_URL=http://your-endpoint/v1/chat/completions
CUSTOM_API_KEY=your_key               # Optional
```

**General Settings:**
```bash
DEFAULT_MODEL=mistralai/mistral-7b-instruct:free  # Default model to use
FLASK_ENV=development                             # Optional
PORT=5001                         # Optional
```

## 📊 How It Works

1. **Enter Your Idea** - Type a simple description of what you want your AI to do
2. **Select Target Model** - Choose the AI model you'll be using
3. **Generate** - PromptSmith transforms your idea into an optimized prompt
4. **Refine** - Iteratively improve the prompt with specific requirements
5. **Analyze** - Get quality feedback and suggestions for improvement
6. **Save** - Store your prompts in history for future use

## 🧪 Testing

The project includes a comprehensive test suite with 88+ tests covering all modules.

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Module
```bash
pytest tests/test_validation.py -v
pytest tests/test_generator.py -v
pytest tests/test_app.py -v
```

### Run Tests with Coverage (if pytest-cov installed)
```bash
pytest tests/ --cov=. --cov-report=html
```

### Test Structure
- `tests/test_validation.py` - Input validation tests
- `tests/test_helpers.py` - Helper utility tests
- `tests/test_cache.py` - Caching system tests
- `tests/test_model_api.py` - API integration tests
- `tests/test_generator.py` - Prompt generation tests
- `tests/test_app.py` - Flask API endpoint tests

## 🐛 Troubleshooting

### Common Issues

**401 Unauthorized Error**
- **OpenRouter**: Check your OPENROUTER_API_KEY in `.env` file
  - Get a free key at https://openrouter.ai/keys
  - Ensure you have credits/free tier enabled
- **Custom API**: Verify CUSTOM_API_KEY is correct

**Connection Errors**
- **LM Studio**: 
  - Make sure LM Studio is running
  - Check that the local server is started in LM Studio
  - Verify LMSTUDIO_API_URL matches your LM Studio port
- **Ollama**:
  - Ensure Ollama is installed and running
  - Check that you've pulled a model: `ollama pull mistral`
  - Verify OLLAMA_API_URL is correct

**Backend Status Shows Disconnected**
- Check your API_BACKEND setting in `.env`
- Verify the backend service is running (for local backends)
- Test connection using the UI - try generating a prompt

**Port Already in Use**
```bash
# Kill process on port 5001
# Linux/Mac:
lsof -ti:5001 | xargs kill -9

# Windows PowerShell:
Stop-Process -Id (Get-NetTCPConnection -LocalPort 5001).OwningProcess -Force
```

**ModuleNotFoundError**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Model Not Found**
- For LM Studio/Ollama: Ensure the model name in DEFAULT_MODEL matches your loaded model
- For OpenRouter: Use the full model path (e.g., `mistralai/mistral-7b-instruct:free`)

## 💻 Development

### Project Architecture

The application follows a modular architecture:

- **app.py** - Flask application with RESTful API endpoints
- **core/** - Core business logic
  - `generator.py` - Prompt generation and refinement engine
  - `model_api.py` - Multi-backend API integration (OpenRouter, LM Studio, Ollama, Custom)
  - `cache.py` - Intelligent caching system
  - `web_search.py` - Web search for model best practices
- **utils/** - Utility modules
  - `helpers.py` - Common helper functions
  - `validation.py` - Input validation and sanitization
- **config/** - Configuration files
  - `settings.py` - Application settings and environment variables
  - `models.yaml` - Model configurations
  - `templates.yaml` - Prompt templates

### Code Quality

The project maintains high code quality standards:

- ✅ All functions have comprehensive docstrings
- ✅ Input validation and sanitization on all user inputs
- ✅ Comprehensive test coverage (88+ tests)
- ✅ Error handling with proper logging
- ✅ Type hints where applicable

### Running in Development Mode

```bash
# Set environment to development
export FLASK_ENV=development  # Linux/Mac
$env:FLASK_ENV="development"  # Windows PowerShell

# Run with auto-reload
python app.py
```

### Adding a New Model

1. Add model configuration to `config/models.yaml`:
```yaml
your_model:
  description: "Model description"
  preferred_format: "Preferred prompt style"
  model_id: "provider/model-id"
  tips: "Best practices for this model"
```

2. The model will be automatically available in the UI

### Security Considerations

- API keys are stored in `.env` file (never committed)
- All user inputs are validated and sanitized
- No sensitive data is logged
- CORS headers can be configured for production
- Rate limiting should be added for production deployment

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- OpenRouter for API access
- DuckDuckGo for web search
- Flask community
- All contributors and users

## 📧 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

**Made with ❤️ by the PromptSmith Team**
