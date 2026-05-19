# 🤖 AIMO — Sistema Inteligente de Acompañamiento Emocional

[![Frontend Status](https://img.shields.io/badge/Frontend-Vercel-000?logo=vercel)](https://aimo-amber.vercel.app)
[![Backend Status](https://img.shields.io/badge/Backend-Railway-0B0D0E?logo=railway)](https://railway.app)
[![Python Version](https://img.shields.io/badge/Python-3.13+-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![React Version](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-red)](LICENSE)

---

## 📋 Descripción General

**AIMO** es un asistente conversacional impulsado por **Inteligencia Artificial Generativa**, diseñado para brindar **acompañamiento emocional inicial** a estudiantes universitarios en situaciones de estrés, ansiedad o preocupación académica.

El sistema implementa una **arquitectura de 3 agentes en cascada** con evaluación continua en tiempo real, garantizando respuestas empáticas, seguras y contextualizadas según el nivel de riesgo del usuario.

> **Proyecto académico** desarrollado en la Universidad del Cauca, Facultad de Ingeniería Electrónica y Telecomunicaciones.

---

## 🌐 Acceso a la Aplicación

| Componente | URL | Servidor |
|-----------|-----|----------|
| **Frontend** | [aimo-amber.vercel.app](https://aimo-amber.vercel.app) | Vercel (Global CDN) |
| **Backend API** | Railway (configurado como variable de entorno) | Railway (us-east-1) |

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                     APLICACIÓN WEB (React)                      │
│                   (Vercel / aimo-amber.vercel.app)              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK API REST (Python)                      │
│              (Railway / aimo-production-c6ad.up.railway.app)    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         PIPELINE DE 3 AGENTES EN CASCADA                │  │
│  │                                                          │  │
│  │  1. AGENTE DE CONTEXTO (Groq - LLaMA 3.3-70B)         │  │
│  │     ├─ Multi-turn conversation                         │  │
│  │     ├─ Gathering phase (0-3 turnos)                   │  │
│  │     └─ Evaluación intermedia (GPT-3.5)               │  │
│  │                                                          │  │
│  │  2. CLASIFICADOR DE RIESGO (Groq)                     │  │
│  │     ├─ Bajo (consejería preventiva)                   │  │
│  │     ├─ Medio (derivación a profesional)               │  │
│  │     └─ Alto (intervención inmediata)                  │  │
│  │                                                          │  │
│  │  3. GENERADOR DE RECOMENDACIONES (AWS Bedrock)        │  │
│  │     ├─ Recursos según nivel de riesgo                 │  │
│  │     ├─ Claude Sonnet 4.5 para respuestas             │  │
│  │     └─ Respuesta final evaluada (GPT-4)              │  │
│  │                                                          │  │
│  │  ⚠️  MODERADOR DE CONTENIDO (OpenAI Moderation)      │  │
│  │     ├─ Bloquea self-harm, hate speech, violencia     │  │
│  │     └─ Fallback seguro si se detecta contenido riesgoso│  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  📊 PERSISTENCIA: Base de datos de sesiones (JSON)             │
│     └─ Registro académico de cada interacción                  │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Procesamiento

```
Usuario envía mensaje
         │
         ▼
    [MODERACIÓN] ──(detecta riesgo)──> FALLBACK_SEGURO → respuesta
         │
         ├─(seguro)
         ▼
  [AGENTE CONTEXTO]
    • Validación del mensaje
    • Reflexión empática
    • Sugerencia inicial
    • Evaluación intermedia (GPT-3.5)
         │
         ├─(0-3 turnos)──> Siguiente turno
         │
         ├─(turno 3+)
         ▼
  [CLASIFICADOR RIESGO]
    • Análisis de indicadores
    • Categorización (Bajo/Medio/Alto)
         │
         ├─(Bajo)─────────────────────────┐
         │                                  │
         ├─(Medio)────────┐                │
         │                 │                │
         ├─(Alto)─────┐   │                │
         │            │   │                │
         └────┬────┬──┴───┴────────────────┘
              │    │
              ▼    ▼
        [RECOMENDACIONES] ──> Evaluación Final (GPT-4)
              │
              ▼
         Response → Frontend → Usuario
```

---

## 🛠️ Stack Tecnológico

### Frontend
- **Framework:** React 18 + Vite
- **Estilo:** CSS 3 (Custom properties, Grid, Flexbox)
- **Deployment:** Vercel (Global CDN)
- **Características:**
  - Interfaz RPG con personaje animado (AIMO)
  - Panel administrativo con métricas de empatía
  - Historial de conversaciones persistente
  - Indicadores visuales de fase y carga

### Backend
- **Framework:** Flask 3.0
- **Runtime:** Python 3.13
- **Deployment:** Railway (US East 1)
- **CORS:** Flask-CORS (configurado para Vercel)

### Modelos de IA
| Servicio | Proveedor | Modelo | Uso |
|----------|-----------|--------|-----|
| **LLM Principal** | Groq | LLaMA 3.3-70B (versatile) | Generación de respuestas empáticas |
| **Evaluación Intermedia** | OpenAI | GPT-3.5-turbo | Evaluación de empatía por turno |
| **Evaluación Final** | OpenAI | GPT-4 | Evaluación final y recomendaciones |
| **Generación de Recomendaciones** | AWS Bedrock | Claude Sonnet 4.5 | Recomendaciones personalizadas |
| **Moderación de Contenido** | OpenAI | Omni-Moderation-Latest | Detección de contenido riesgoso |

### Otras Tecnologías
- **Persistent Storage:** JSON (data/sessions/)
- **Task Queue:** No requerido (respuestas sincrónicas)
- **Logging:** Sistema personalizado (src/logger.py)

---

## 📦 Instalación y Configuración

### Requisitos Previos
- **Python 3.13+**
- **Node.js 18+** (para frontend)
- **Git**

### 1. Clonar el Repositorio

```bash
git clone https://github.com/JDiegoG12/AIMO.git
cd AIMO
```

### 2. Configurar el Backend

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto `AIMO/`:

```env
# ============================================
# LLM APIs
# ============================================
GROQ_API_KEY=gsk_tu_clave_groq_aqui
OPENAI_API_KEY=sk-proj-tu_clave_openai_aqui

# ============================================
# AWS Bedrock (Recomendaciones)
# ============================================
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0

```

### 4. Configurar el Frontend

```bash
cd frontend
npm install
```

Crea un archivo `.env` en `frontend/`:

```env
VITE_API_URL=http://localhost:5000
```

---

## 🚀 Ejecución Local

### Backend (Terminal 1)

```bash
# Desde la raíz del proyecto (AIMO/)
python -m flask --app api:app run --host=0.0.0.0 --port=5000
```

Verás:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Verás:
```
 Local:   http://localhost:5173/
```

Abre [http://localhost:5173](http://localhost:5173) en tu navegador.

---

## 📁 Estructura del Proyecto

```
AIMO/
│
├── 📂 data/
│   ├── escenarios_prueba.json          # Casos de prueba predefinidos
│   └── sessions/                       # Registro persistente de sesiones
│       └── s_1777231689155.json        # (Auto-generado) Historial por sesión
│
├── 📂 frontend/                        # Aplicación React (Vercel)
│   ├── src/
│   │   ├── App.jsx                     # Componente raíz
│   │   ├── App.css                     # Estilos globales
│   │   ├── components/                 # Componentes React
│   │   │   ├── AimoCharacter.jsx       # Personaje animado
│   │   │   ├── SpeechBubble.jsx        # Burbuja de diálogo
│   │   │   ├── MessageItem.jsx         # Item de mensaje
│   │   │   ├── UserInput.jsx           # Campo de entrada
│   │   │   ├── AdminPanel.jsx          # Panel de admin (métricas)
│   │   │   ├── ThinkLog.jsx            # Log de pensamiento (cadena de razonamiento)
│   │   │   ├── RecommendationsModal.jsx# Modal de recomendaciones finales
│   │   │   └── WorldBackground.jsx     # Fondo del mundo
│   │   ├── hooks/
│   │   │   └── useTypewriter.js        # Hook para efecto typewriter
│   │   └── assets/                     # Imágenes y recursos
│   ├── vite.config.js                  # Configuración de Vite
│   ├── package.json                    # Dependencias (React, Vite)
│   └── index.html                      # HTML de entrada
│
├── 📂 logs/                            # Archivos de log
│   └── aimo.log                        # Log del sistema
│
├── 📂 prompts/                         # Prompts de los agentes
│   ├── aimo_answer.txt                 # System prompt del Agente de Contexto (Groq)
│   ├── aimo_classifier.txt             # System prompt del Clasificador de Riesgo (Groq)
│   ├── aimo_recommendations.txt        # System prompt del Generador de Recomendaciones (Bedrock)
│   ├── evaluador_contexto_v1.txt       # Rúbrica de evaluación intermedia por turno (GPT-3.5)
│   └── evaluador_v1.txt                # Rúbrica AERI de evaluación final — 4 dimensiones PT/FT/EC/PD (GPT-4)
│
├── 📂 src/                             # Código del backend (Flask)
│   ├── agente_aimo.py                  # Generador de respuestas (Groq)
│   ├── agente_clasificador.py          # Clasificador de riesgo
│   ├── agente_recomendaciones.py       # Generador de recomendaciones (Bedrock)
│   ├── agente_evaluador.py             # Evaluador de empatía (GPT)
│   ├── config_api.py                   # Configuración centralizada de APIs
│   ├── logger.py                       # Sistema de logging personalizado
│   ├── moderador.py                    # Moderación de contenido (OpenAI)
│   └── session_store.py                # Persistencia de sesiones
│
├── 📄 .env                             # Variables de entorno (NO SUBIR)
├── 📄 .env.example                     # Plantilla de .env
├── 📄 .gitignore                       # Archivos ignorados por git
├── 📄 api.py                           # Aplicación Flask principal
├── 📄 main_tester.py                   # Script de pruebas (CLI)
├── 📄 test_bedrock.py                  # Tests de Bedrock
├── 📄 requirements.txt                 # Dependencias Python
├── 📄 package-lock.json                # Lock de dependencias del frontend
└── 📄 README.md                        # Este archivo
```

---

## 🔌 API Endpoints

### Base URL
- **Local:** `http://localhost:5000`
- **Producción:** Configurado como variable de entorno `VITE_API_URL` en Vercel

### Endpoints Disponibles

#### `POST /api/chat`
Envía un mensaje y obtiene la respuesta del pipeline AIMO.

**Request:**
```json
{
  "message": "Me siento muy ansioso por los exámenes",
  "session_id": "s_1234567890123"
}
```

**Response:**
```json
{
  "response": "Escucho que los exámenes te generan ansiedad. Es completamente normal...",
  "phase": "gathering",
  "evaluation": {
    "perspective_taking": {
      "score": 5,
      "justification": "El agente refleja el estado emocional..."
    },
    "fantasy": {...},
    "empathic_concern": {...},
    "personal_distress": {...}
  },
  "classification": {
    "risk_level": "bajo",
    "indicators": [...]
  },
  "thinking": "cadena de razonamiento...",
  "moderacion_activa": false,
  "pipeline_complete": false,
  "recommendations": null
}
```

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `message` | string | Mensaje del usuario |
| `session_id` | string | ID único de la sesión |

**Status Codes:**
- `200` - OK
- `400` - Mensaje inválido
- `401` - API key no configurada
- `500` - Error del servidor

#### `POST /api/reset`
Reinicia una sesión existente.

**Request:**
```json
{
  "session_id": "s_1234567890123"
}
```

**Response:**
```json
{
  "ok": true,
  "message": "Sesión reiniciada correctamente"
}
```

---

## 🧪 Evaluación de Empatía

El sistema implementa el índice **AERI** (Xu & Jiang, 2024 — *Affective Empathy in Robotic Interaction*), una adaptación del IRI de Davis diseñada específicamente para asistentes conversacionales de IA. Cada respuesta final se evalúa en **4 dimensiones independientes** mediante un único llamado a GPT-4:

| Dimensión | Rango | Peso | Descripción |
|-----------|-------|------|-------------|
| **Perspective Taking (PT)** | 1-5 | 30% | Comprensión cognitiva: ¿el agente entendió la situación específica del estudiante? |
| **Empathic Concern (EC)** | 1-5 | 30% | Calidez afectiva: ¿valida emociones con sinceridad y evita *toxic positivity*? |
| **Personal Distress (PD)** | 1-5 (↓) | 25% | Estabilidad emocional del agente. **Menor = mejor**: penaliza respuestas ansiosas, reactivas o sobre-emocionales. |
| **Fantasy (FT)** | 1-5 | 15% | Creatividad y naturalidad humana: ¿usa metáforas o se siente formulaico/robótico? |

**Score compuesto:**
```
composite = PT × 0.30 + EC × 0.30 + (6 − PD) × 0.25 + FT × 0.15
```

PT y EC son las dimensiones cognitiva y afectiva del soporte; PD se invierte porque alta reactividad emocional en el agente daña la percepción del usuario; FT recibe menos peso al no ser crítica en contextos clínicos.

Cada dimensión incluye una **justificación textual** del evaluador. Adicionalmente, durante la fase de recolección de contexto se ejecuta una evaluación intermedia por turno con GPT-3.5 sobre 3 criterios complementarios (empatía, naturalidad, adecuación de la pregunta) descritos en `prompts/evaluador_contexto_v1.txt`.

---

## 🛡️ Seguridad y Moderación

### Sistema de Moderación Multinivel

1. **Pre-procesamiento:** Validación de entrada (largo, caracteres especiales)
2. **Detección:** OpenAI Moderation API en todas las respuestas
3. **Categorías Bloqueadas:**
   - Self-harm / Instructions for self-harm
   - Hate speech / Harassment
   - Threatening language / Violence
   - Graphic violence

4. **Fallback Seguro:** Si se detecta contenido riesgoso:
```
"⚠️ Detectamos que tu mensaje podría indicar una situación de riesgo. 
Por favor, contacta con los servicios de bienestar de tu universidad 
o llama a la línea de prevención de suicidio."
```

### Registro de Incidentes
- Todas las detecciones se registran en la sesión JSON
- Los administradores pueden revisar el historial

---

## 📊 Análisis de Sesiones

Cada sesión genera un archivo JSON con:

```json
{
  "session_id": "s_1777231689155",
  "created_at": "2026-04-26T14:28:19.123Z",
  "turns": [
    {
      "turn": 1,
      "user_message": "Me siento muy solo en la universidad",
      "aimo_response": "Escucho que te sientes solo...",
      "evaluation": {...},
      "classification": null,
      "thinking": "Estrategia: validar emoción...",
      "timestamp": "2026-04-26T14:28:25.456Z"
    }
  ],
  "final_classification": {
    "risk_level": "bajo",
    "indicators": [...]
  },
  "final_recommendations": "Aquí está tu plan de acción...",
  "moderation_incidents": [],
  "total_turns": 3,
  "duration_seconds": 127
}
```

Útil para análisis académico posterior.

---

## 🔒 Variables de Entorno Requeridas

| Variable | Requerida | Descripción | Ejemplo |
|----------|-----------|-------------|---------|
| `GROQ_API_KEY` | ✅ | Clave API de Groq | `gsk_...` |
| `OPENAI_API_KEY` | ✅ | Clave API de OpenAI | `sk-proj-...` |
| `AWS_ACCESS_KEY_ID` | ✅ | Clave de acceso AWS | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | ✅ | Clave secreta AWS | |
| `AWS_REGION` | ❌ | Región AWS | `us-east-1` |
| `BEDROCK_MODEL_ID` | ❌ | ID del modelo Bedrock | `us.amazon.nova-pro-v1:0` |
| `VITE_API_URL` | ❌ (Frontend) | URL del backend API | Configurado en Vercel como variable de entorno |

---

## 📈 Performance y Escalabilidad

### Métricas Actuales
- **Latencia promedio:** ~3-5 segundos (incluye llamadas a múltiples APIs)
- **Throughput:** 1 sesión simultánea (desarrollo)
- **Storage:** ~2KB por sesión (JSON)

### Limitaciones Conocidas
- Flask development server no es para producción (usar Gunicorn en Railway)
- Sin caché de respuestas (cada pregunta consulta APIs en vivo)
- Sin rate limiting (implementar en futuro)

### Para Escalar
- Implementar Redis para caché de sesiones
- Usar Gunicorn + Nginx en Railway
- Agregar queue de tareas (Celery + Redis)
- CDN para assets estáticos (CloudFront)

---

## 🤝 Equipo Desarrollador

| Rol | Nombre | Responsabilidad |
|-----|--------|-----------------|
| 👩‍💻 Desarrolladora | Ana Sofia Arango Yanza | Backend, evaluación, moderación |
| 👨‍💻 Desarrollador | Juan Diego Gomez Garces | Frontend, UX/UI |
| 👨‍💻 Desarrollador | Juan David Vela Coronado | Backend, APIs, deployment |

**Profesor Asesor:** Néstor Milciades Díaz Marino  
**Institución:** Universidad del Cauca, Facultad de Ingeniería Electrónica y Telecomunicaciones

---

## 🧠 Metodología de Investigación

Este proyecto implementa la metodología **LLM-as-a-Judge** para evaluación de empatía:

1. **Agente Generador** produce respuestas según reglas estrictas
2. **Agente Evaluador** califica cada respuesta en 4 dimensiones
3. **Iteración** en prompts basada en feedback del evaluador

Objetivo: Alcanzar consistentemente puntuaciones **4-5 en empatía**.

---

## 📝 Cómo Contribuir

1. **Fork** el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/mejora`)
3. Haz commit de tus cambios (`git commit -m 'Add: nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Abre un **Pull Request**

**Notas:**
- Nunca commits con `.env` (credenciales)
- Usa el formato de commit `feat:`, `fix:`, `docs:`, `refactor:`
- Agrega tests si modificas lógica crítica

---

## 📄 Licencia

**© 2026 Ana Sofia Arango Yanza, Juan Diego Gomez Garces, Juan David Vela Coronado**  
Universidad del Cauca — Facultad de Ingeniería Electrónica y Telecomunicaciones

Todos los derechos reservados. Queda prohibida la copia, distribución o uso del
código sin autorización escrita de los autores. Ver [LICENSE](LICENSE) para más detalles.

---

## 🐛 Reporte de Bugs

¿Encontraste un bug? Por favor:

1. Verifica que no esté reportado en [Issues](https://github.com/JDiegoG12/AIMO/issues)
2. Abre un nuevo Issue con:
   - Descripción clara del problema
   - Pasos para reproducir
   - Expected vs actual behavior
   - Logs relevantes

---

## 📚 Recursos Adicionales

- [Documentación de Groq](https://console.groq.com/docs)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [AWS Bedrock Guide](https://docs.aws.amazon.com/bedrock/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [IRI - Interpersonal Reactivity Index](https://en.wikipedia.org/wiki/Empathic_concern)

---

## 🙋 Preguntas?

Abre un [Discussion](https://github.com/JDiegoG12/AIMO/discussions) en GitHub o contacta al equipo de desarrollo.

---

**Última actualización:** Abril 26, 2026  
**Versión:** 3.0 (Producción con Frontend + Backend + Multi-Agent Pipeline)
