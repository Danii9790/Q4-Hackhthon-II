# Todo AI Chatbot Backend

FastAPI backend for AI-powered task management using natural language.

## Features

- 🤖 **Natural Language Task Management**: Create, view, complete, update, and delete tasks through conversation
- 🔄 **Stateless Architecture**: All conversation state persisted to database
- 🔐 **JWT Authentication**: Secure user authentication with Better Auth
- 🛡️ **Security Hardening**: Rate limiting, input validation, CORS protection
- 📊 **Structured Logging**: JSON logs with request tracking and performance monitoring
- ⚡ **Performance Optimized**: Connection pooling, pagination, caching headers

## Tech Stack

- **Python**: 3.11+
- **FastAPI**: 0.104+ (async web framework)
- **SQLModel**: 0.0.14 (type-safe ORM)
- **Neon PostgreSQL**: Serverless PostgreSQL database
- **OpenAI Agents SDK**: AI agent orchestration
- **Alembic**: Database migrations

## Quick Start

### 1. Prerequisites

```bash
# Install Python 3.11+
python3 --version

# Install PostgreSQL client (for Neon)
sudo apt-get install postgresql-client
```

### 2. Environment Setup

```bash
# Clone repository
cd /home/xdev/Hackhthon-II/phase-III/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 3. Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Better Auth
BETTER_AUTH_SECRET=your-secret-here
BETTER_AUTH_URL=http://localhost:3000

# Application
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development

# Logging (optional)
LOG_LEVEL=INFO
LOG_FORMAT=TEXT  # or JSON for production
LOG_FILE=logs/app.log

# Security
RATE_LIMIT_PER_MINUTE=10
MAX_MESSAGE_LENGTH=10000

# Performance
SLOW_QUERY_THRESHOLD_MS=500
SLOW_REQUEST_THRESHOLD_MS=3000
```

### 4. Database Setup

```bash
# Run migrations
alembic upgrade head

# Verify connection
python -c "from src.db.session import engine; import asyncio; asyncio.run(engine.connect())"
```

### 5. Start Server

```bash
# Development mode (auto-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check OpenAPI docs
open http://localhost:8000/docs
```

## API Endpoints

### Authentication
- `POST /api/auth/signin` - Sign in/sign up
- `POST /api/auth/signout` - Sign out
- `GET /api/auth/session` - Get current session

### Chat
- `POST /api/{user_id}/chat` - Send message to AI chatbot

### Health
- `GET /health` - Health check
- `GET /metrics` - Application metrics

## Database Schema

### Tables
- `users` - User accounts
- `conversations` - Chat conversations
- `messages` - Chat messages
- `tasks` - User tasks

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

## Testing

### Unit Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api_chat.py

# Run with verbose output
pytest -v
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/

# Test with real database
DATABASE_URL=postgresql+asyncpg://... pytest tests/integration/
```

### Manual Testing
```bash
# Test chat endpoint
TOKEN="your-jwt-token"
USER_ID="your-user-id"

curl -X POST "http://localhost:8000/api/$USER_ID/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a task to buy groceries",
    "conversation_id": null
  }'
```

## Architecture

### MCP Tools
- `add_task` - Create new task
- `list_tasks` - List tasks with filtering
- `complete_task` - Mark task as done
- `update_task` - Modify task details
- `delete_task` - Remove task

### Agent
- Uses OpenAI Agents SDK for intent interpretation
- Stateless - no in-memory conversation state
- Tool calls executed through MCP protocol

### Security
- Rate limiting: 10 requests/minute per user
- Message length: Max 10,000 characters
- CORS: Configured for frontend domain only
- Input sanitization: Removes control characters
- JWT authentication: Better Auth integration

## Performance

### Database Connection Pool
- Core pool size: 10 connections
- Max overflow: 20 connections (30 total)
- Connection recycling: 1 hour
- Pre-ping: Validates connections before use

### Pagination
- Default limit: 50 messages
- Maximum limit: 1,000 messages
- Supports time-based filtering

### Caching
- Dynamic responses: No-cache
- Static responses: ETag support
- Browser caching: Configured headers

## Monitoring

### Logs
- Structured JSON logging (production)
- Human-readable text logs (development)
- Request ID tracking
- Performance metrics
- Error context

### Performance Metrics
- Request timing
- Database query timing
- Agent execution timing
- Tool call timing
- Slow operation detection

## Troubleshooting

### Database Connection Issues
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL

# Check pool settings
grep pool_size src/db/session.py
```

### Agent Errors
```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Verify key format (should start with sk-)
echo $OPENAI_API_KEY | grep "^sk-"

# Test API connection
python -c "from openai import OpenAI; OpenAI().models.list()"
```

### Rate Limiting
```bash
# Check current limits
grep RATE_LIMIT .env

# Temporarily disable for testing
RATE_LIMIT_PER_MINUTE=9999 uvicorn src.main:app --reload
```

## Deployment

### Production Checklist
- [ ] Set `ENVIRONMENT=production`
- [ ] Use strong `BETTER_AUTH_SECRET`
- [ ] Configure `FRONTEND_URL` to production domain
- [ ] Set `LOG_FORMAT=JSON`
- [ ] Enable rate limiting
- [ ] Use multiple workers (4-8)
- [ ] Configure monitoring
- [ ] Set up log aggregation
- [ ] Enable database backups
- [ ] Configure CDN for static assets

### Docker Deployment
```bash
# Build image
docker build -t todo-chatbot-backend .

# Run container
docker run -d \
  --name todo-backend \
  -p 8000:8000 \
  --env-file .env \
  todo-chatbot-backend
```

## Contributing

1. Follow PEP 8 style guide
2. Write unit tests for new features
3. Update documentation
4. Run tests before committing
5. Use meaningful commit messages

## License

MIT

## Support

For issues and questions:
- Check documentation in `docs/`
- Review test files for examples
- Open an issue on GitHub
