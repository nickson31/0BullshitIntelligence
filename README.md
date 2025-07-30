# 0BullshitIntelligence

AI-powered chat application with modern UI and Gemini 2.0 Flash integration.

## 🚀 Features

- **Real-time Chat**: WebSocket-powered conversations with Gemini 2.0 Flash
- **Smart Search**: Find investors and companies based on your project needs  
- **Intelligent Upselling**: AI-powered upgrade suggestions based on user plan
- **Modern UI**: Clean, responsive interface with dark theme
- **Supabase Integration**: User management and data persistence

## 🛠 Tech Stack

- **Backend**: FastAPI + Uvicorn/Gunicorn
- **AI**: Google Gemini 2.0 Flash
- **Database**: Supabase
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Deployment**: Render

## 🌐 Deployment

### Render Configuration

The application is configured for Render deployment with:
- `render.yaml` for service configuration
- `Procfile` for process definition
- Environment variables managed in Render dashboard

### Environment Variables

Set these in Render:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `GEMINI_API_KEY`: Your Google AI API key
- `GEMINI_MODEL`: Model name (default: gemini-2.0-flash)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run locally  
python main.py
```

## 📁 Project Structure

```
├── app/
│   ├── api/          # FastAPI routes and middleware
│   ├── core/         # Configuration and logging
│   ├── models/       # Pydantic models
│   ├── static/       # CSS, JS, assets
│   └── templates/    # Jinja2 HTML templates
├── main.py           # Application entry point
├── requirements.txt  # Python dependencies
└── render.yaml       # Render deployment config
```

## 🎯 Technical Features

- **WebSocket Communication**: Real-time bidirectional chat
- **Structured Logging**: JSON-formatted logs with context
- **Error Handling**: Comprehensive exception management
- **Rate Limiting**: API protection against abuse
- **CORS Support**: Cross-origin resource sharing
- **Static File Serving**: Efficient asset delivery

## 🎨 UI/UX

- **Responsive Design**: Works on desktop and mobile
- **Dark Theme**: Modern, eye-friendly interface
- **Smooth Animations**: CSS transitions and effects
- **Toast Notifications**: User feedback system
- **Loading States**: Progress indicators
- **Typing Indicators**: Real-time chat feedback

## 🔒 Security

- **Environment Variables**: Sensitive data not in code
- **Input Validation**: Pydantic model validation
- **Rate Limiting**: Request throttling
- **CORS Configuration**: Controlled cross-origin access

## 📊 Monitoring

- **Health Checks**: Service status endpoints
- **Performance Logging**: Request timing and metrics
- **Error Tracking**: Comprehensive error logging
- **Business Events**: User interaction analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

---

**Built with ❤️ for intelligent business conversations**