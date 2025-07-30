# 🚨 Troubleshooting Guide - 0BullshitIntelligence Testing Interface

## 🌍 **Gemini API Regional Issues**

### **Error: "400 User location is not supported for the API use"**

Este error es muy común y tiene varias soluciones:

#### **Solución 1: Cambiar Modelo de Gemini**

Edita tu archivo `.env` y prueba diferentes modelos:

```env
# Opción 1: Gemini 1.5 Flash (recomendado)
GEMINI_MODEL=gemini-1.5-flash

# Opción 2: Gemini 1.5 Pro 
GEMINI_MODEL=gemini-1.5-pro

# Opción 3: Gemini Pro (más compatible)
GEMINI_MODEL=gemini-pro

# Opción 4: Modelo más básico (máxima compatibilidad)
GEMINI_MODEL=models/text-bison-001
```

#### **Solución 2: Verificar API Key**

1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **IMPORTANTE:** Asegúrate de que tu API key esté creada para tu región
3. Si tienes problemas, **elimina** la API key actual y crea una nueva
4. Copia la nueva key a tu archivo `.env`

#### **Solución 3: Usar VPN (Si estás en región restringida)**

Si estás en una región donde Gemini no está disponible:

1. **Conecta VPN a Estados Unidos, Reino Unido, o Japón**
2. **Crea una nueva API key** mientras estés conectado al VPN
3. **Configura el modelo más compatible:**
   ```env
   GEMINI_MODEL=gemini-pro
   ```

#### **Solución 4: Modo Fallback (Funciona sin Gemini)**

El sistema tiene respuestas inteligentes de fallback. Edita tu `.env`:

```env
ENABLE_FALLBACK_RESPONSES=true
FALLBACK_MODE=intelligent
```

Con esto, el chat funcionará **sin necesidad de Gemini**, usando respuestas predefinidas inteligentes.

---

## 🔧 **Otras Soluciones Comunes**

### **Problema: Supabase Connection Error**

```bash
# Error: "Could not find a relationship between tables"
```

**Solución:** Algunas consultas están simplificadas para evitar este error. El sistema seguirá funcionando.

### **Problema: Puerto 8001 ocupado**

```bash
# Error: "Address already in use"
```

**Solución:** Cambia el puerto en tu `.env`:
```env
PORT=8002
```

### **Problema: Dependencias faltantes**

```bash
# Error: "ModuleNotFoundError"
```

**Solución:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

## ✅ **Configuración Recomendada para Máxima Compatibilidad**

Crea tu archivo `.env` con esta configuración probada:

```env
# Configuración más compatible
HOST=0.0.0.0
PORT=8001
DEBUG=true

# Tu configuración de Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu-anon-key
SUPABASE_SERVICE_KEY=tu-service-key

# Configuración de Gemini más compatible
GEMINI_API_KEY=tu-api-key-aqui
GEMINI_MODEL=gemini-pro

# Habilitar fallbacks
ENABLE_FALLBACK_RESPONSES=true
FALLBACK_MODE=intelligent
```

---

## 🧪 **Probar la Configuración**

1. **Reinicia el servidor:**
   ```bash
   # Presiona Ctrl+C para parar
   # Luego ejecuta de nuevo:
   python run.py
   ```

2. **Prueba conexión:** Ve a http://localhost:8001 y haz clic en "Test Connection"

3. **Prueba chat:** Escribe "hello" en el chat

4. **Si falla Gemini:** Verás respuestas de fallback inteligentes

---

## 🌟 **El Sistema Funcionará**

**¡Importante!** Incluso si Gemini no funciona por restricciones regionales, el sistema testing **seguirá siendo completamente funcional** con:

- ✅ **Chat con respuestas inteligentes** (sin Gemini)
- ✅ **Dashboard en tiempo real** 
- ✅ **Navegador de base de datos**
- ✅ **Búsqueda de inversores y fondos**
- ✅ **Todas las funciones de testing**

El fallback está diseñado para dar respuestas contextualmente relevantes basadas en lo que escribas.

---

## 📞 **Si Nada Funciona**

1. **Usa modo fallback completo** - el sistema funcionará sin APIs externas
2. **Verifica que Supabase esté configurado** - esto es lo más importante
3. **El resto de la interfaz funcionará perfectamente** para explorar datos

**¡Tu sistema de testing estará operativo en cualquier caso!** 🚀