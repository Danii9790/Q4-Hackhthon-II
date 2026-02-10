# Todo API - FastAPI Backend

A production-grade RESTful API backend for the Todo Full-Stack Web Application. Built with FastAPI, SQLModel, and PostgreSQL, featuring JWT authentication, comprehensive logging, and health monitoring.

## Features

### Core API
- RESTful API for task management (CRUD operations)
- JWT-based authentication and authorization
- Multi-user data isolation
- Request ID tracking for debugging
- Comprehensive error logging
- Health check endpoints for monitoring
- Database migrations with Alembic
- CORS support for frontend integration
- OpenAPI/Swagger documentation

### AI-Powered Chat (NEW!)
- **Stateless Conversation Flow**: Zero server-side memory, all state in database
- **Natural Language Task Management**: Chat with AI to manage tasks
- **MCP Tool Integration**: 5 tools (add_task, list_tasks, complete_task, update_task, delete_task)
- **6-Step Request Cycle**: Auth → Fetch History → Store User → Invoke Agent → Store Assistant → Return
- **Rate Limiting**: 20 requests/minute per user
- **Context Preservation**: Full conversation history for context-aware responses
- **Server Restart Survival**: No data loss across restarts
- **Horizontal Scaling**: Any server can handle any request

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.11 or higher
- **PostgreSQL**: Version 12 or higher
- **pip**: Python package manager
- **Git**: For version control

### Check Python Version

```bash
python --version
# or
python3 --version
```

### Check PostgreSQL

```bash
psql --version
```

## Installation

### 1. Clone the Repository

If you haven't already, clone the repository and navigate to the backend directory:

```bash
cd /path/to/Hackhthon-II/phase-II/backend
```

### 2. Create Virtual Environment

Create a Python virtual environment to isolate project dependencies:

```bash
# Using venv (built-in)
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

Install all required packages including development tools:

```bash
pip install -e .[dev]
```

This installs:
- **Core dependencies**: FastAPI, SQLModel, JWT libraries, database drivers
- **Dev dependencies**: pytest, black, isort, mypy for testing and code quality

### 4. Set Up Environment Variables

Create a `.env` file in the backend directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/todo_db

# Better Auth Configuration (must be at least 32 characters)
BETTER_AUTH_SECRET=your-super-secret-key-at-least-32-chars-long

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Important Security Notes:**
- Generate a strong `BETTER_AUTH_SECRET` using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Never commit `.env` files to version control
- Use different secrets for development and production

### 5. Set Up Database

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE todo_db;

# Create user (optional, if not using default postgres user)
CREATE USER todo_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE todo_db TO todo_user;

# Exit
\q
```

#### Run Migrations

Apply database migrations to create tables:

```bash
# Run all pending migrations
alembic upgrade head
```

If this is a fresh installation, this will create:
- `users` table (for authentication)
- `tasks` table (for todo items)

#### Verify Migration

```bash
# Check migration status
alembic current

# View migration history
alembic history
```

## Running the Application

### Development Server

Start the development server with auto-reload:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Production Server

For production deployment, use a production-grade ASGI server:

```bash
# Install gunicorn with uvicorn workers
pip install gunicorn

# Run with 4 workers (adjust based on your CPU cores)
gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### Using Make Commands (Optional)

If you have a Makefile, you can use convenient commands:

```bash
make dev        # Start development server
make test       # Run tests
make migrate    # Run migrations
make fmt        # Format code with black and isort
make lint       # Run type checking with mypy
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/todo_db` |
| `BETTER_AUTH_SECRET` | Yes | Secret key for JWT tokens (min 32 chars) | `your-secret-key-min-32-chars` |
| `OPENAI_API_KEY` | Yes | OpenAI API key for AI chat | `sk-...` |
| `OPENAI_MODEL` | No | OpenAI model to use (default: gpt-4o-mini) | `gpt-4o-mini`, `gpt-4o` |
| `ENVIRONMENT` | No | Application environment | `development`, `production` |
| `LOG_LEVEL` | No | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Database Migration Guide

### Creating New Migrations

When you modify models in `src/models.py`, create a new migration:

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "Description of changes"

# This creates a new file in alembic/versions/
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade <revision_id>
```

### Migration Best Practices

1. **Review auto-generated migrations**: Always check the generated migration file
2. **Write descriptive messages**: Use clear, concise migration descriptions
3. **Test migrations**: Test migrations on a copy of production data first
4. **Backup before migration**: Always backup database before applying to production
5. **Never edit existing migrations**: Create new ones instead

## API Documentation

### Interactive Swagger UI

Access the interactive API documentation at:
```
http://localhost:8000/docs
```

This provides:
- Complete API reference
- Request/response schemas
- Try-it-out functionality for testing endpoints

### ReDoc Documentation

Alternative documentation format:
```
http://localhost:8000/redoc
```

### Health Check Endpoints

- **GET** `/health` - Basic health check
- **GET** `/health/live` - Liveness probe (is server running?)
- **GET** `/health/ready` - Readiness probe (is server ready to handle requests?)

Example response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-22"
}
```

### Chat API Endpoints

#### POST /api/users/{user_id}/chat

Send a message to the AI assistant and receive a response.

**Authentication:** Required (JWT token in Authorization header)

**Request Body:**
```json
{
  "message": "Add a task to buy groceries"
}
```

**Response (200 OK):**
```json
{
  "response": "I've added 'Buy groceries' to your tasks.",
  "tool_calls": [
    {
      "tool_name": "add_task",
      "parameters": {"title": "Buy groceries"},
      "result": {
        "success": true,
        "data": {
          "id": "123",
          "title": "Buy groceries",
          "completed": false
        }
      }
    }
  ]
}
```

**Rate Limiting:** 20 requests per minute per user

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/api/users/{user_id}/chat" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me my incomplete tasks"}'
```

**Error Responses:**
- `400 Bad Request`: Invalid message format
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Accessing another user's conversation
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server or AI processing error

**How It Works:**

1. **Stateless Architecture**: No server-side memory. Each request fetches conversation history from database
2. **Context Awareness**: AI sees full conversation history for coherent responses
3. **Tool Execution**: AI automatically invokes MCP tools (add_task, complete_task, etc.) based on user intent
4. **Transaction Safety**: All database operations wrapped in transactions
5. **Graceful Degradation**: AI responses delivered even if logging fails

**Available MCP Tools:**
- `add_task`: Create new task
- `list_tasks`: List tasks (all/pending/completed)
- `complete_task`: Mark task as completed
- `update_task`: Modify task
- `delete_task`: Remove task

For more details, see [Conversation Flow Quickstart](../specs/005-conversation-flow/quickstart.md)


## Project Structure

```
backend/
├── alembic/                 # Database migrations
│   ├── versions/            # Migration files
│   └── env.py               # Alembic environment configuration
├── logs/                    # Application logs (created at runtime)
│   └── app.log              # Main application log file
├── src/
│   ├── api/
│   │   ├── routes/          # API route handlers
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── tasks.py     # Task CRUD endpoints
│   │   │   └── chat.py      # AI chat endpoint (NEW!)
│   │   └── dependencies.py  # FastAPI dependencies (JWT auth, DB session)
│   ├── models/              # SQLModel database models
│   │   ├── user.py          # User model
│   │   ├── task.py          # Task model
│   │   ├── conversation.py  # Conversation model (NEW!)
│   │   └── message.py       # Message model (NEW!)
│   ├── services/            # Business logic services
│   │   ├── auth.py          # Authentication service
│   │   ├── task.py          # Task service
│   │   ├── agent.py         # AI agent service (NEW!)
│   │   ├── conversation.py  # Conversation service (NEW!)
│   │   └── mcp_server.py    # MCP server integration
│   ├── mcp_tools/           # MCP tool implementations (NEW!)
│   │   ├── add_task.py      # Add task tool
│   │   ├── list_tasks.py    # List tasks tool
│   │   ├── complete_task.py # Complete task tool
│   │   ├── update_task.py   # Update task tool
│   │   └── delete_task.py   # Delete task tool
│   ├── db.py                # Database connection and session management
│   ├── schemas.py           # Pydantic request/response models
│   └── main.py              # FastAPI application setup
├── tests/                   # Test files
│   ├── conftest.py          # Pytest fixtures
│   ├── test_auth.py         # Authentication tests
│   └── test_tasks.py        # Task API tests
├── .env.example             # Environment variables template
├── alembic.ini              # Alembic configuration
├── pyproject.toml           # Project dependencies and configuration
└── README.md                # This file
```

## Development Guidelines

### Code Style

This project follows Python best practices:

- **Formatter**: Black (line length: 100)
- **Import sorting**: isort
- **Type checking**: mypy (strict mode)
- **Linting**: pylint (optional)

Format your code before committing:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type check
mypy src/
```

### Logging

The application uses Python's built-in logging module:

- **Log files**: Stored in `logs/app.log`
- **Console output**: Enabled for development
- **Log levels**: Controlled by `LOG_LEVEL` environment variable
- **Request tracking**: Each request gets a unique ID for debugging

Example log entry:
```
2026-01-22 10:30:45 - INFO - src.main - Request started: POST /api/auth/register [ID: 123e4567-e89b-12d3-a456-426614174000]
```

### Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_tasks.py

# Run with verbose output
pytest -v
```

### Error Handling

The API provides detailed error responses:

```json
{
  "detail": {
    "error": "Validation error",
    "request_id": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

Each response includes a `request_id` for tracing issues in logs.

## Common Issues and Solutions

### Issue: Database Connection Failed

**Error**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**:
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check DATABASE_URL in `.env` file
3. Ensure database exists: `psql -U postgres -l`
4. Verify user permissions

### Issue: Import Errors

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -e .[dev]`

### Issue: Migration Conflicts

**Error**: `alembic.util.exc.CommandError: Target database is not up to date`

**Solution**:
```bash
# Check current version
alembic current

# View migration history
alembic history

# Reset database (WARNING: This deletes all data)
# 1. Drop all tables
alembic downgrade base

# 2. Re-apply migrations
alembic upgrade head
```

### Issue: Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn src.main:app --port 8001
```

## Security Best Practices

1. **Environment Variables**: Never commit `.env` files
2. **Secrets**: Use strong, randomly generated secrets
3. **Database**: Use separate database user for application (not postgres superuser)
4. **Dependencies**: Keep dependencies updated: `pip install --upgrade -e .[dev]`
5. **HTTPS**: Always use HTTPS in production
6. **CORS**: Configure `allow_origins` to match your frontend domain only
7. **Logging**: Be careful not to log sensitive data (passwords, tokens)

## Performance Optimization

### Database Connection Pooling

The application uses SQLAlchemy's connection pooling. Configure pool size in `src/db.py`:

```python
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,        # Adjust based on load
    max_overflow=20,      # Additional connections under load
)
```

### Caching

For frequently accessed data, consider adding Redis caching (future enhancement).

## Deployment

### Deploying to Render (Recommended)

Render provides a simple, powerful platform for deploying FastAPI applications with automatic SSL, continuous deployment, and built-in monitoring.

#### Prerequisites

1. **Render Account**: Sign up at https://render.com
2. **GitHub Repository**: Your code should be on GitHub
3. **PostgreSQL Database**: Create a PostgreSQL database on Render

#### Deployment Steps

1. **Create PostgreSQL Database on Render**:

   - Go to Render Dashboard → New → PostgreSQL
   - Choose a database name (e.g., `todo_db`)
   - Select the region closest to your users
   - Copy the **Internal Database URL** from the dashboard

2. **Prepare Your Repository**:

   Ensure your `render.yaml` file is in the `backend` directory.

3. **Create Web Service on Render**:

   - Go to Render Dashboard → New → Web Service
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` configuration
   - Verify the following settings:
     - **Root Directory**: `backend` (if deploying from monorepo root)
     - **Runtime**: Python 3.12
     - **Build Command**: `pip install -e .[dev]`
     - **Start Command**: `gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`

4. **Set Environment Variables**:

   In your web service settings, add these environment variables:

   ```bash
   # Required
   DATABASE_URL=postgresql://user:password@host/database  # Use your Render PostgreSQL URL
   BETTER_AUTH_SECRET=your-super-secret-key-at-least-32-chars-long

   # Recommended
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

   **Generate a secure secret**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Deploy**:

   - Click "Create Web Service"
   - Render will automatically deploy your application
   - The deployment will run migrations automatically via the `preDeployCommand`

6. **Verify Deployment**:

   - Check the deployment logs in Render Dashboard
   - Visit your API URL: `https://your-service.onrender.com`
   - Test health check: `https://your-service.onrender.com/health`
   - Access API docs: `https://your-service.onrender.com/docs`

#### Automatic Deploys

Render automatically deploys when you push to your connected branch (default: `main`):

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

#### Environment Variables in Render

Manage environment variables via:

1. **Render Dashboard**: Your Service → Environment
2. **Render CLI**: `render env add BETTER_AUTH_SECRET`

#### Database Migrations

The `render.yaml` configuration includes a `preDeployCommand` that automatically runs migrations:

```yaml
preDeployCommand: alembic upgrade head
```

This ensures your database schema is always up to date with your code.

#### Monitoring and Logs

- **Live Logs**: View in Render Dashboard → Logs
- **Metrics**: CPU, memory, and response times in Dashboard
- **Alerts**: Configure alerting for downtime or errors
- **Health Checks**: Render monitors the `/health` endpoint

#### Scaling

Upgrade your plan as needed:

- **Free**: Good for development/testing
- **Starter ($7/month)**: Basic production usage
- **Standard ($25/month)**: Higher performance
- **Pro**: Custom resources and support

#### Advanced Configuration

Modify `render.yaml` for custom needs:

```yaml
services:
  - type: web
    name: fastapi-backend
    runtime: python
    buildCommand: pip install -e .[dev]
    startCommand: gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: todo-db  # Reference your Render database
          property: connectionString
      - key: BETTER_AUTH_SECRET
        generateValue: true  # Let Render generate a secure secret
```

#### Troubleshooting

**Issue**: Deployment fails
- **Solution**: Check the deployment logs in Render Dashboard
- Verify `DATABASE_URL` is correctly set
- Ensure all dependencies are in `requirements.txt`

**Issue**: Health check fails
- **Solution**: Verify the `/health` endpoint is accessible
- Check if the port is correct (default: 8000)
- Ensure the application starts without errors

**Issue**: Database connection errors
- **Solution**: Verify PostgreSQL is accepting connections
- Check if the database is in the same region as your web service
- Ensure SSL is enabled in the DATABASE_URL

### Using Docker (Alternative)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .[dev]

# Copy application
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Run migrations
CMD ["alembic", "upgrade", "head"] && \
    ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t todo-api .
docker run -p 8000:8000 --env-file .env todo-api
```

### Using Systemd (Linux)

Create `/etc/systemd/system/todo-api.service`:

```ini
[Unit]
Description=Todo API FastAPI Application
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/todo-api
Environment="PATH=/var/www/todo-api/.venv/bin"
ExecStart=/var/www/todo-api/.venv/bin/gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable todo-api
sudo systemctl start todo-api
sudo systemctl status todo-api
```

## Monitoring and Maintenance

### Log Monitoring

Monitor application logs:

```bash
# Follow logs in real-time
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# View recent errors
grep ERROR logs/app.log | tail -20
```

### Health Checks

Set up automated health checks:

```bash
# Basic health check
curl http://localhost:8000/health

# Readiness check (includes database)
curl http://localhost:8000/health/ready

# Liveness check
curl http://localhost:8000/health/live
```

## Contributing

When contributing to the backend:

1. Create a feature branch from `main`
2. Make your changes following the code style guidelines
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Format code: `black . && isort .`
6. Type check: `mypy src/`
7. Submit a pull request with a clear description

## License

This project is part of the Todo Full-Stack Web Application.

## Support

For issues, questions, or contributions, please refer to the main project repository.

---

**Last Updated**: 2026-01-22
**Version**: 1.0.0
