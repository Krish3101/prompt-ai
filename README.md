# 🚀 PromptSmith AI

**The Resilient, Offline-First Prompt Engineering Copilot**

Writing effective prompts is hard, and relying on constant API access just to iterate on prompts slows you down. **PromptSmith** solves this by acting as an offline-first prompt engineering copilot. It locally structures, breaks down, and refines your ideas into expert-level prompt templates. When online, it seamlessly taps into a web-search-augmented LLM to fetch the latest best practices for your target model.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Flask](https://img.shields.io/badge/flask-3.0.3-red)
![License](https://img.shields.io/badge/license-MIT-yellow)

## ✨ Core Features

- **Smart Prompt Generation** - Transform simple ideas into detailed, optimized prompts (Powered by OpenRouter or Offline Template Fallback)
- **Prompt History** - Save, search, and manage all your prompts locally
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
├── app.py                 # Core application & API endpoints
├── requirements.txt       # Python dependencies (Flask, requests, dotenv)
├── README.md              # This file
└── public/                # Frontend assets (Static & Templates)
    ├── index.html         # Main UI
    ├── style.css          # Styles with dark mode
    └── main.js            # Frontend logic
```

## 🔌 Backend Support
PromptSmith is designed as a simplified MVP, supporting:
1. **OpenRouter (Cloud)**: Uses a Mistral LLM to actively optimize your prompts if `OPENROUTER_API_KEY` is provided.
2. **Offline Mode (Fallback)**: If no API key is set or the connection fails, it instantly falls back to a locally generated, hardcoded prompt template that breaks down your request for you to use.
## 🎨 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/api/generate` | POST | Generate new prompt |
| `/api/refine` | POST | Refine existing prompt |
| `/api/config` | GET | Get backend configuration |
| `/api/history` | GET | Get prompt history |
| `/api/history/save` | POST | Save prompt to history |
| `/api/history/<id>` | DELETE | Delete history entry |
| `/api/history/<id>/favorite` | POST | Toggle favorite |

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Generate prompt |
| `Ctrl + K` | Toggle history panel |
| `Ctrl + D` | Toggle dark mode |
| `Esc` | Close modals/panels |

## 🔧 Configuration

### Environment Variables

**OpenRouter Settings:**
```bash
OPENROUTER_API_KEY=your_key_here    # Get from https://openrouter.ai/keys (Optional)
```
If omitted, the app will run entirely in Offline Mode.

## 📊 How It Works

1. **Enter Your Idea** - Type a simple description of what you want your AI to do
2. **Select Target Model** - Choose the AI model you'll be using
3. **Generate** - PromptSmith transforms your idea into an optimized prompt
6. **Save** - Store your prompts in history for future use

## 🐛 Troubleshooting

### Common Issues

**401 Unauthorized Error**
- **OpenRouter**: Check your OPENROUTER_API_KEY in `.env` file
  - Get a free key at https://openrouter.ai/keys
  - Ensure you have credits/free tier enabled
- **Custom API**: Verify CUSTOM_API_KEY is correct

**Backend Status Shows Offline Mode**
- If you intended to use OpenRouter, check your `OPENROUTER_API_KEY` in your `.env` file.
- Otherwise, the app is intentionally running safely in Offline Mode.
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

The application is a lightweight MVP utilizing a single-file backend architecture:
- **app.py** - Flask application holding all logic (REST API, offline generator, LLM requests, and flat-file history persistence).
- **History** is saved locally in `history.json`.
### Running in Development Mode

```bash
# Set environment to development
export FLASK_ENV=development  # Linux/Mac
$env:FLASK_ENV="development"  # Windows PowerShell

# Run with auto-reload
python app.py
```

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
