# 0BullshitIntelligence

🧠 **Inteligencia artificial sin tonterías. Conversaciones reales, respuestas útiles.**

Una aplicación de chat con IA moderna y elegante, powered by Gemini 2.0 Flash, diseñada para proporcionar respuestas precisas y conversaciones naturales.

## ✨ Características

- **🤖 IA Avanzada**: Integración con Gemini 2.0 Flash para conversaciones naturales
- **💬 Chat en Tiempo Real**: WebSockets para comunicación instantánea
- **🎨 UI Moderna**: Interfaz dark theme con animaciones suaves
- **📱 Responsive**: Optimizada para desktop y móvil
- **🌐 Multiidioma**: Soporte para español e inglés
- **⚡ Ultra Rápido**: Arquitectura optimizada para rendimiento

## 🚀 Despliegue en Render

Este proyecto está configurado para deployment directo en Render.

### Variables de Entorno Requeridas

Configura estas variables en tu dashboard de Render:

```
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_anon_key
GEMINI_API_KEY=tu_gemini_api_key
```

### Deploy Automático

1. Conecta tu repositorio a Render
2. Configura las variables de entorno
3. Render detectará automáticamente `render.yaml` y desplegará

## 🛠️ Desarrollo Local

### Requisitos

- Python 3.11+
- pip

### Instalación

1. Clona el repositorio:
```bash
git clone <tu-repo>
cd 0bullshitintelligence
```

2. Instala dependencias:
```bash
pip install -r requirements.txt
```

3. Configura variables de entorno:
```bash
cp env.example .env
# Edita .env con tus valores
```

4. Ejecuta la aplicación:
```bash
python main.py
```

La aplicación estará disponible en `http://localhost:8000`

## 📁 Estructura del Proyecto

```
├── app/                    # Aplicación principal
│   ├── api/               # Endpoints y rutas
│   ├── core/              # Configuración y utilidades
│   ├── database/          # Gestión de base de datos
│   ├── ai_systems/        # Sistemas de IA
│   ├── models/            # Modelos de datos
│   ├── services/          # Servicios de negocio
│   ├── templates/         # Templates HTML
│   └── static/            # Archivos estáticos (CSS, JS)
├── docs/                  # Documentación
├── main.py               # Punto de entrada
├── requirements.txt      # Dependencias
├── render.yaml          # Configuración de Render
├── Procfile            # Para deployment
└── runtime.txt         # Versión de Python
```

## 🎯 Características Técnicas

- **Backend**: FastAPI + Uvicorn + Gunicorn
- **IA**: Google Gemini 2.0 Flash
- **Base de Datos**: Supabase
- **WebSockets**: Para chat en tiempo real
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Deployment**: Render con configuración automática

## 🔧 Configuración de Producción

El proyecto está optimizado para producción con:

- Configuración automática de entorno
- Manejo de errores robusto
- Logs estructurados
- Conexiones WebSocket resilientes
- UI responsiva y accesible

## 📚 API Endpoints

- `GET /` - Página principal
- `GET /chat` - Interfaz de chat
- `GET /api/status` - Estado del sistema
- `WS /ws/chat/{conversation_id}` - WebSocket para chat

## 🎨 UI/UX

- **Tema Dark**: Diseño moderno con gradientes
- **Animaciones**: Transiciones suaves y efectos visuales
- **Responsiva**: Optimizada para todos los dispositivos
- **Accesible**: Cumple estándares de accesibilidad web

## 🔒 Seguridad

- Variables de entorno para credenciales
- Validación de entrada robusta
- Configuración CORS apropiada
- Rate limiting incluido

## 📈 Monitoreo

- Logs estructurados
- Health checks automáticos
- Métricas de rendimiento
- Estado de componentes en tiempo real

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo una licencia personalizada. Ver el archivo de licencia para más detalles.

---

**🧠 0BullshitIntelligence - Sin tonterías, solo resultados.**