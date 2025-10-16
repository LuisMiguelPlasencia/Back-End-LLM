# Conversa API

Simple FastAPI REST API for conversation management with courses and messaging functionality.

## Features

- User authentication with PostgreSQL and pgcrypto
- Course management based on user types
- Conversation creation and management
- Real-time messaging with automatic assistant responses
- Clean, simple architecture with minimal dependencies

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   Copy `env.example` to `.env` and update the DATABASE_URL:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and set your PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/database_name
   ```

3. **Database setup:**
   Ensure your PostgreSQL database has the required schema and pgcrypto extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pgcrypto;
   ```
   
   Run the schema initialization from `db_init_schema.sql`.

## Running the API

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

- Interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## API Endpoints

### Authentication

**POST /auth/login**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### Read Operations

**GET /read/courses** - Get user courses
```bash
curl "http://localhost:8000/read/courses?user_id=123e4567-e89b-12d3-a456-426614174000"
```

**GET /read/conversation** - Get user conversations
```bash
curl "http://localhost:8000/read/conversation?user_id=123e4567-e89b-12d3-a456-426614174000"
```

**GET /read/messages** - Get conversation messages
```bash
curl "http://localhost:8000/read/messages?conversation_id=123e4567-e89b-12d3-a456-426614174000"
```

### Insert Operations

**POST /insert/conversation** - Start new conversation
```bash
curl -X POST "http://localhost:8000/insert/conversation" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"123e4567-e89b-12d3-a456-426614174000","course_id":"123e4567-e89b-12d3-a456-426614174001"}'
```

**POST /insert/message** - Send message
```bash
curl -X POST "http://localhost:8000/insert/message" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"123e4567-e89b-12d3-a456-426614174000","conversation_id":"123e4567-e89b-12d3-a456-426614174002","message":"Hello!"}'
```

## Project Structure

```
app/
├── main.py                 # FastAPI app creation and configuration
├── routers/
│   ├── auth.py            # Authentication endpoints
│   ├── read.py            # Data retrieval endpoints
│   ├── insert.py          # Data creation endpoints
│   ├── db_operations.py   # Existing database operations
│   └── health.py          # Existing health check endpoints
├── services/
│   ├── db.py              # Database connection pool
│   ├── auth_service.py    # Authentication logic
│   ├── courses_service.py # Course management
│   ├── conversations_service.py # Conversation management
│   └── messages_service.py # Message handling
├── schemas/
│   ├── auth.py            # Authentication models
│   ├── read.py            # Read operation models
│   └── insert.py          # Insert operation models
└── utils/
    └── responses.py       # Response formatting helpers
```

## Database Schema

The API expects these PostgreSQL tables:

- `conversaConfig.user_info` - User accounts with pgcrypto passwords
- `conversaConfig.master_courses` - Available courses
- `conversaConfig.user_type_relations` - Course access by user type
- `conversaApp.conversations` - User conversations
- `conversaApp.messages` - Conversation messages

## Notes

- Passwords are hashed using PostgreSQL's `crypt()` function (requires pgcrypto extension)
- Assistant responses are currently static echoes (ready for AI integration)
- Course IDs are accepted in conversation creation but not stored (for API compatibility)
- Assistant messages have `user_id = NULL` (system messages)

## Development

The app is exported from `app.main:app` for easy testing and deployment with ASGI servers.
