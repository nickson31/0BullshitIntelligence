# 🔗 API Endpoints - 0BullshitIntelligence

**Base URL:** `http://localhost:8000` (desarrollo)

Todos los endpoints (excepto health y webhooks) requieren autenticación JWT en el header:
```
Authorization: Bearer <jwt_token>
```

## 📋 Índice de Endpoints

### 🏥 Health & Status
- [GET /health](#get-health) - Health check básico
- [GET /health/detailed](#get-healthdetailed) - Health check detallado  
- [GET /health/ready](#get-healthready) - Readiness check
- [GET /health/live](#get-healthlive) - Liveness check
- [GET /status](#get-status) - Estado detallado del sistema
- [GET /metrics](#get-metrics) - Métricas del servicio

### 💬 Chat
- [POST /api/v1/chat/send](#post-apiv1chatsend) - Enviar mensaje al chat
- [GET /api/v1/chat/welcome](#get-apiv1chatwelcome) - Obtener mensaje de bienvenida
- [POST /api/v1/chat/regenerate](#post-apiv1chatregenerate) - Regenerar respuesta
- [GET /api/v1/chat/stream/{conversation_id}](#get-apiv1chatstreamconversation_id) - Stream de respuesta

### 🗨️ Conversaciones
- [POST /api/v1/chat/conversations](#post-apiv1chatconversations) - Crear conversación
- [GET /api/v1/chat/conversations](#get-apiv1chatconversations) - Listar conversaciones
- [GET /api/v1/chat/conversations/{id}](#get-apiv1chatconversationsid) - Obtener conversación
- [POST /api/v1/chat/conversations/{id}/title](#post-apiv1chatconversationsidtitle) - Actualizar título
- [DELETE /api/v1/chat/conversations/{id}](#delete-apiv1chatconversationsid) - Eliminar conversación

### 🔍 Búsquedas
- [POST /api/v1/search/investors](#post-apiv1searchinvestors) - Buscar inversores
- [POST /api/v1/search/companies](#post-apiv1searchcompanies) - Buscar companies
- [GET /api/v1/search/investors/saved](#get-apiv1searchinvestorssaved) - Búsquedas guardadas de inversores
- [GET /api/v1/search/companies/saved](#get-apiv1searchcompaniessaved) - Búsquedas guardadas de companies
- [GET /api/v1/search/investors/{id}/employees](#get-apiv1searchinvestorsidemployees) - Empleados de fondo

### 🔗 WebSockets
- [WS /ws/chat/{conversation_id}](#ws-wschatconversation_id) - WebSocket para chat en tiempo real

---

## 🏥 Health & Status Endpoints

### GET /health
Health check básico del servicio.

**Response:**
```json
{
  "success": true,
  "message": "Service is healthy",
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00.000Z",
    "service": "0BullshitIntelligence"
  }
}
```

### GET /health/detailed
Health check detallado con estado de componentes.

**Response:**
```json
{
  "success": true,
  "message": "Detailed health check completed",
  "data": {
    "overall_status": "healthy",
    "components": [
      {"component": "database", "healthy": true},
      {"component": "ai_systems", "healthy": true},
      {"component": "search_engines", "healthy": true}
    ],
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

### GET /status
Estado detallado del sistema con información de componentes.

**Response:**
```json
{
  "success": true,
  "message": "Service status check completed",
  "data": {
    "overall_status": "healthy",
    "components": {
      "database": "healthy",
      "ai_systems": "healthy",
      "search_engines": "healthy"
    },
    "uptime": "calculated_uptime_here",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

---

## 💬 Chat Endpoints

### POST /api/v1/chat/send
Envía un mensaje al sistema de chat AI.

**Request Body:**
```json
{
  "content": "Busco inversores para mi startup de fintech",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "project_id": "project-123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message processed successfully",
  "data": {
    "ai_response": "Como mentor te ayudo a encontrar inversores...",
    "search_results": {
      "results": [...],
      "metadata": {...},
      "search_type": "investors"
    },
    "message_type": "mentor"
  },
  "ai_response": "Como mentor te ayudo a encontrar inversores...",
  "search_results": {...},
  "upsell_message": "💡 Con el Plan Pro podrías buscar inversores específicos...",
  "processing_time_ms": 1250.5
}
```

### GET /api/v1/chat/welcome
Obtiene mensaje de bienvenida personalizado.

**Query Parameters:**
- `project_id` (optional): ID del proyecto

**Response:**
```json
{
  "success": true,
  "message": "Welcome message generated",
  "data": {
    "welcome_message": "¡Hola! 👋 Soy tu mentor de startup especializado..."
  }
}
```

### POST /api/v1/chat/regenerate
Regenera la última respuesta del AI.

**Request Body:**
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message_id": "msg-123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Response regenerated successfully",
  "ai_response": "Nueva respuesta regenerada...",
  "processing_time_ms": 850.2
}
```

---

## 🗨️ Conversation Endpoints

### POST /api/v1/chat/conversations
Crea una nueva conversación.

**Request Body:**
```json
{
  "title": "Conversación sobre financiación",
  "project_id": "project-123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Conversation created successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Conversación sobre financiación",
    "user_id": "user-123",
    "project_id": "project-123",
    "created_at": "2024-01-01T12:00:00.000Z",
    "active": true
  }
}
```

### GET /api/v1/chat/conversations
Lista las conversaciones del usuario.

**Query Parameters:**
- `project_id` (optional): Filtrar por proyecto
- `limit` (default: 20): Número máximo de resultados
- `offset` (default: 0): Offset para paginación

**Response:**
```json
{
  "success": true,
  "message": "Conversations retrieved successfully",
  "data": {
    "conversations": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Conversación sobre financiación",
        "created_at": "2024-01-01T12:00:00.000Z",
        "message_count": 15,
        "last_activity": "2024-01-01T14:30:00.000Z"
      }
    ],
    "total_count": 1,
    "limit": 20,
    "offset": 0
  }
}
```

### GET /api/v1/chat/conversations/{id}
Obtiene una conversación específica con historial de mensajes.

**Response:**
```json
{
  "success": true,
  "message": "Conversation retrieved successfully",
  "data": {
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "Busco inversores para mi startup",
        "created_at": "2024-01-01T12:00:00.000Z"
      },
      {
        "id": "msg-2", 
        "role": "assistant",
        "content": "Te ayudo a encontrar inversores...",
        "ai_response_data": {...},
        "search_results": {...},
        "created_at": "2024-01-01T12:00:05.000Z"
      }
    ],
    "message_count": 2
  }
}
```

---

## 🔍 Search Endpoints

### POST /api/v1/search/investors
Busca inversores relevantes (Ángeles + Fondos).

**Request Body:**
```json
{
  "keywords": ["fintech", "payments", "blockchain"],
  "stage_keywords": ["seed", "series_a"],
  "categories": ["financial_services"],
  "project_id": "project-123",
  "limit": 15,
  "min_angel_score": 40.0,
  "min_employee_score": 5.9
}
```

**Response:**
```json
{
  "success": true,
  "message": "Investor search completed successfully",
  "data": {
    "results": [
      {
        "investor_type": "angel",
        "display_name": "John Doe",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "contact_email": "john@example.com",
        "location": "San Francisco, CA",
        "profile_image": "https://...",
        "score": 85.0,
        "relevance_score": 92.5,
        "description": "Experienced fintech investor...",
        "categories": ["fintech", "payments"],
        "stages": ["seed", "series_a"]
      },
      {
        "investor_type": "fund",
        "display_name": "Fintech Ventures",
        "linkedin_url": "https://linkedin.com/company/fintechvc",
        "contact_email": "contact@fintechvc.com",
        "website": "https://fintechvc.com",
        "location": "New York, NY",
        "score": 88.0,
        "relevance_score": 89.2,
        "description": "Leading fintech-focused VC fund...",
        "categories": ["fintech", "blockchain"],
        "stages": ["seed", "series_a", "series_b"]
      }
    ],
    "metadata": {
      "search_id": "search-123",
      "total_results": 15,
      "angels_found": 8,
      "funds_found": 7,
      "search_distribution": {"angels": 0.7, "funds": 0.3},
      "search_time": "2024-01-01T12:00:00.000Z",
      "keywords_used": ["fintech", "payments", "blockchain"],
      "filters_applied": {
        "stage_keywords": ["seed", "series_a"],
        "categories": ["financial_services"],
        "min_angel_score": 40.0
      }
    },
    "search_type": "investors",
    "success": true
  }
}
```

### POST /api/v1/search/companies
Busca companies B2B para servicios específicos.

**Request Body:**
```json
{
  "service_keywords": ["marketing", "digital", "seo"],
  "service_type": "marketing",
  "location_preference": "Spain",
  "project_id": "project-123",
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "message": "Company search completed successfully",
  "data": {
    "results": [
      {
        "company_type": "service_provider",
        "display_name": "Digital Marketing Pro",
        "linkedin_url": "https://linkedin.com/company/digitalmarketing",
        "website": "https://digitalmarketing.com",
        "contact_email": "contact@digitalmarketing.com",
        "phone": "+34 123 456 789",
        "location": "Madrid, Spain",
        "description": "Agencia de marketing digital especializada...",
        "sector": "Digital Marketing, SEO, SEM",
        "relevance_score": 95.5,
        "service_match": 89.2,
        "keywords": ["marketing digital", "seo", "sem", "social media"],
        "services": ["Marketing", "SEO", "Social Media"]
      }
    ],
    "metadata": {
      "search_id": "search-456",
      "total_results": 8,
      "companies_found": 8,
      "search_time": "2024-01-01T12:00:00.000Z",
      "keywords_used": ["marketing", "digital", "seo"],
      "service_type": "marketing",
      "location_preference": "Spain"
    },
    "search_type": "companies",
    "success": true
  }
}
```

### GET /api/v1/search/investors/saved
Obtiene búsquedas guardadas de inversores del usuario.

**Query Parameters:**
- `project_id` (optional): Filtrar por proyecto
- `limit` (default: 20): Número máximo de resultados
- `offset` (default: 0): Offset para paginación

**Response:**
```json
{
  "success": true,
  "message": "Saved investor searches retrieved",
  "data": {
    "searches": [
      {
        "search_id": "search-123",
        "created_at": "2024-01-01T12:00:00.000Z",
        "query_data": {...},
        "results_count": 15,
        "used_in_campaigns": false
      }
    ],
    "total_count": 1,
    "limit": 20,
    "offset": 0
  }
}
```

### GET /api/v1/search/investors/{investor_id}/employees
Obtiene empleados de un fondo de inversión específico.

**Response:**
```json
{
  "success": true,
  "message": "Fund employees retrieved successfully",
  "data": {
    "fund_id": "fund-123",
    "employees": [
      {
        "fullname": "Jane Smith",
        "linkedin_url": "https://linkedin.com/in/janesmith",
        "email": "jane@fund.com",
        "job_title": "Investment Manager",
        "score": 8.5,
        "profile_image": "https://...",
        "about": "Investment professional focusing on fintech..."
      }
    ],
    "count": 1
  }
}
```

---

## 🔗 WebSocket

### WS /ws/chat/{conversation_id}
WebSocket para comunicación en tiempo real durante el chat.

**Conexión:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/123e4567-e89b-12d3-a456-426614174000');
```

**Mensajes que puedes enviar:**
```json
{
  "type": "ping"
}

{
  "type": "typing",
  "user_id": "user-123",
  "is_typing": true
}
```

**Mensajes que recibirás:**
```json
{
  "type": "connection_established",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "message": "Connected to chat"
}

{
  "type": "judge_decision",
  "decision": "search_investors",
  "confidence": 0.85,
  "reasoning": "User is looking for investors..."
}

{
  "type": "search_progress",
  "status": "searching",
  "progress": 50,
  "message": "Buscando inversores relevantes..."
}

{
  "type": "search_results",
  "results": {...},
  "timestamp": "2024-01-01T12:00:05.000Z"
}

{
  "type": "ai_response",
  "response": "He encontrado 15 inversores relevantes...",
  "timestamp": "2024-01-01T12:00:06.000Z"
}

{
  "type": "pong",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

---

## 🔐 Autenticación

Para desarrollo, si no proporcionas token JWT, el sistema usará un usuario mock:

```json
{
  "user_id": "dev-user-001",
  "email": "dev@0bullshit.com",
  "plan": "pro",
  "credits": 10000,
  "language": "spanish",
  "projects": ["dev-project-001"]
}
```

Para producción, incluye el JWT token en todas las requests:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📊 Códigos de Estado

- **200** - Success
- **400** - Bad Request (parámetros inválidos)
- **401** - Unauthorized (token JWT inválido/ausente)
- **404** - Not Found
- **429** - Rate Limit Exceeded
- **500** - Internal Server Error

## 🚀 Rate Limits

- **Por minuto:** 60 requests
- **Por hora:** 1000 requests

Los headers de rate limit se incluyen en todas las responses:
```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 823
X-RateLimit-Reset: 1704110460
```

---

## 🔧 Notas para Desarrollo

1. **Base URL de desarrollo:** `http://localhost:8000`
2. **Documentación Swagger:** `http://localhost:8000/docs` (solo en desarrollo)
3. **WebSocket de testing:** Disponible para probar conexiones en tiempo real
4. **Logs:** Todas las requests se loggean con request IDs únicos en headers `X-Request-ID`

## 🐛 Debugging

Cada response incluye headers útiles para debugging:
```
X-Request-ID: ab12cd34
X-RateLimit-Remaining-Minute: 45
```

Para reportar errores, incluye siempre el `X-Request-ID` para facilitar el debugging.

---

**¿Preguntas?** Contacta al equipo de backend para clarificaciones sobre cualquier endpoint.