# Speech-to-Text Backend API

Backend API para transcripción de audio y generación de respuestas con modelos LLM, construido con FastAPI, Supabase y Celery.

## 🏗️ Arquitectura

### Diagrama de Alto Nivel (Monolito Modular)

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/Vue)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/HTTPS
┌─────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ Text  Router│ │ Chat Router │ │ Health      │            │
│  │             │ │             │ │ Router      │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│           │               │              │                  │
│  ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼─────┐             │
│  │ Text  Service│ │ LLM Service │ │ Auth      │             │
│  │              │ │             │ │ Service   │             │
│  └──────────────┘ └─────────────┘ └───────────┘             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Supabase                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ PostgreSQL  │ │ Storage     │ │ Auth        │            │
│  │ Database    │ │ (Audio      │ │ (JWT)       │            │
│  │             │ │  Files)     │ │             │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico

- **Backend Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **File Storage**: Supabase Storage
- **Authentication**: JWT + Supabase Auth
- **LLM Providers**: OpenAI, Anthropic
- **Documentation**: OpenAPI/Swagger

## 📁 Estructura del Proyecto

```
Back-End-LLM/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuración
│   ├── database.py             # DB y Supabase
│   ├── models.py               # SQLModel models
│   ├── schemas.py              # Pydantic schemas
│   ├── auth.py                 # JWT auth
│   ├── tasks.py                # Celery tasks
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── audio.py            # Audio endpoints
│   │   ├── chat.py             # Chat endpoints
│   │   └── health.py           # Health checks
│   └── services/
│       ├── __init__.py
│       ├── audio_service.py    # Audio management
│       └── llm_service.py      # LLM providers
├── scripts/
│   ├── start_server.py         # Server startup
├── pyproject.toml              # Dependencies
├── env.example                 # Environment template
└── README.md                   # This file
```

## 🚀 Instalación y Configuración

### 1. Prerrequisitos

- Python 3.10+
- Poetry (gestión de dependencias)
- Redis (para Celery)
- Supabase project

### 2. Clonar y Configurar

```bash
# Clonar el repositorio
git clone <repository-url>
cd Back-End-LLM

# Instalar poetry
pip install poetry

# Instalar dependencias
poetry install

# Activar entorno virtual Metodo 1
poetry env activate

# Activar entorno virtual Metodo 2
poetry shell

# Copiar variables de entorno
cp env.example .env
```

### 3. Configurar Variables de Entorno

Edita el archivo `.env` con tus credenciales:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/speech_to_text_db

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30


# LLM Providers
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_AUDIO_TYPES=audio/wav,audio/mp3,audio/m4a,audio/ogg

# App Settings
DEBUG=True
ENVIRONMENT=development
```

### 4. Configurar Supabase (una vez al inicio del proyecto)

```bash
# Ejecutar script de configuración / Creación de BBDD
python scripts/setup_supabase.py
```

## 🏃‍♂️ Ejecución Local

### 2. Iniciar Servidor FastAPI

```bash
poetry env activate
# Opción 1: Poetry
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
poetry run uvicorn app.main:app --reload

# Opción 2: Script
python scripts/start_server.py

# Opción 3: Uvicorn directo
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```

### 4. Verificar Funcionamiento

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Root**: http://localhost:8000/

## 📋 Endpoints API

### Health Checks

```bash
# Health check básico
GET /api/v1/health/

# Liveness check
GET /api/v1/health/liveness

# Readiness check
GET /api/v1/health/readiness
```

### Text Management

```bash
# Subir texto transcrito
POST /api/v1/audio/upload
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer <jwt-token>
{
  "title": "Mi transcripción",
  "original_text": "Texto transcrito del audio...",
  "language": "es",
  "source": "upload"
}

# Listar entradas de texto
GET /api/v1/audio/
Authorization: Bearer <jwt-token>

# Obtener transcripción
GET /api/v1/audio/{audio_id}/transcription
Authorization: Bearer <jwt-token>

# Crear transcripción
POST /api/v1/audio/{audio_id}/transcribe
Authorization: Bearer <jwt-token>

# Obtener transcripción por ID
GET /api/v1/audio/transcription/{transcription_id}
Authorization: Bearer <jwt-token>

# Eliminar entrada de texto
DELETE /api/v1/audio/{audio_id}
Authorization: Bearer <jwt-token>
```

### Chat y LLM

```bash
# Generar respuesta LLM
POST /api/v1/chat/completion
Authorization: Bearer <jwt-token>
{
  "transcription_id": 1,
  "message": "¿Qué dice el audio?"
}

# Generar respuesta LLM asíncrona
POST /api/v1/chat/completion/async
Authorization: Bearer <jwt-token>

# Crear sesión de chat
POST /api/v1/chat/sessions
Authorization: Bearer <jwt-token>
{
  "title": "Mi sesión"
}

# Listar sesiones de chat
GET /api/v1/chat/sessions
Authorization: Bearer <jwt-token>

# Agregar mensaje a sesión
POST /api/v1/chat/sessions/{session_id}/messages
Authorization: Bearer <jwt-token>
{
  "content": "Hola",
  "role": "user"
}
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
poetry run pytest

# Tests específicos
poetry run pytest tests/test_health.py

# Con coverage
poetry run pytest --cov=app

# Tests con verbose
poetry run pytest -v
```

### Ejemplos de Tests

```python
# Test de health check
def test_health_check(client: TestClient):
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

## 🔧 Desarrollo


### Migraciones


### Debugging

```bash
# Logs del servidor
tail -f logs/app.log

# Logs de Celery
celery -A app.tasks worker --loglevel=debug

# Debug con pdb
python -m pdb scripts/start_server.py
```

## 🚀 Despliegue

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/speech_to_text_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A app.tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/speech_to_text_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: speech_to_text_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Variables de Entorno de Producción

```bash
# Producción
DEBUG=False
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:5432/db
REDIS_URL=redis://host:6379

# Seguridad
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=https://yourdomain.com
```

## 📊 Monitoreo

### Health Checks

```bash
# Health check básico
curl http://localhost:8000/api/v1/health/

# Readiness check
curl http://localhost:8000/api/v1/health/readiness

# Liveness check
curl http://localhost:8000/api/v1/health/liveness
```

### Logs

```bash
# Logs de la aplicación
tail -f logs/app.log

# Logs de Celery
tail -f logs/celery.log

# Logs de Redis
tail -f logs/redis.log
```

### Métricas

- **Tiempo de respuesta**: Prometheus + Grafana
- **Uso de memoria**: cAdvisor
- **Logs centralizados**: ELK Stack

## 🔒 Seguridad

### Autenticación

- JWT tokens con Supabase Auth
- Refresh tokens automáticos
- Rate limiting por usuario

### Autorización

- Row Level Security (RLS) en PostgreSQL
- Políticas por usuario en Supabase
- Validación de permisos en endpoints

### Validación de Archivos

- Validación de MIME types
- Límite de tamaño de archivo
- Escaneo de malware (opcional)

## 🤝 Contribución

1. Todos somos contributors
2. Bajarse la ultima versión de main (`git checkout main && git pull`)
3. Crear rama de desarrollo (`git checkout -b my_branch`)
4. Una vez terminado el desarrollo hacer rebase con la última version de main (`git checkout main && git pull && git checkout my_branch && git rebase main`)
5. Subir los cambios con un force-push: (`git push --force`)
6. Abrir Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

- **Issues**: GitHub Issues
- **Documentación**: `/docs` endpoint
- **Email**: support@example.com

## 🗺️ Roadmap

- [ ] Integración con Whisper API
- [ ] Soporte para más formatos de audio
- [ ] Streaming de transcripción en tiempo real
- [ ] Dashboard de administración
- [ ] Webhooks para notificaciones
- [ ] Cache con Redis
- [ ] Métricas avanzadas
- [ ] Tests de integración
- [ ] CI/CD pipeline
- [ ] Kubernetes deployment

