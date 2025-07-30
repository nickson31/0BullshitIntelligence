# 0BullshitIntelligence - AI Microservice

🎯 **Specialized AI-powered microservice for connecting startups with investors**

## ⚡ Powered by Google Gemini 2.0 Flash

This microservice is **100% optimized for Google Gemini 2.0 Flash**, providing:

- 🧠 **Judge System** - Advanced intent analysis and multi-decision routing
- 🔍 **Hybrid Search** - Intelligent investor (Angels + Funds) and company matching  
- 💬 **Y-Combinator Mentor** - Direct, actionable advice in YC style
- 🚀 **Real-time WebSockets** - Live search progress and chat updates
- 🛡️ **Anti-spam & Language Detection** - Robust conversation management
- 💰 **Smart Upselling** - Non-intrusive plan upgrade suggestions

## 🚀 Quick Start

1. **Configure Gemini API**:
   ```bash
   cp env.example .env
   # Add your GEMINI_API_KEY to .env
   ```

2. **Install & Run**:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

3. **Access API**: `http://localhost:8000/docs`

## 📚 Documentation

- **[API Endpoints](docs/ENDPOINTS.md)** - Complete API reference (142 endpoints)
- **[Implementation Summary](docs/RESUMEN_IMPLEMENTACION.md)** - Technical details
- **[README](docs/README.md)** - Detailed architecture overview

## 🎯 Key Features

### AI-Powered Decision Making
- **Multi-decision Judge System** using Gemini 2.0 Flash
- **Context-aware responses** based on project completeness
- **Simultaneous actions**: Search + Questions + Upselling

### Intelligent Search
- **Hybrid investor search** (70/30 Angels/Funds ratio by stage)
- **Company B2B matching** with keyword enhancement
- **Real-time progress updates** via WebSockets
- **CTO-ready results** stored for outreach campaigns

### Production Ready
- **JWT Authentication** with service-to-service communication
- **Rate limiting** and CORS middleware
- **Structured logging** with request tracking
- **Health checks** for all critical systems

---

**Ready for production deployment with Docker + Supabase + Gemini 2.0 Flash** 🚀