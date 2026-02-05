# Q4 Hackhthon II - Project Phases

This repository contains the Q4 Hackhthon II project organized into three distinct phases, representing progressive development milestones. Each phase is a self-contained project with its own backend and frontend components.

## Repository Structure

```
Q4-Hackhthon-II/
├── phase-I/      # Initial project implementation - Todo CLI Application
├── phase-II/     # Enhanced Todo Application with FastAPI + Next.js + Better Auth
├── phase-III/    # Advanced AI-powered Todo Application
└── README.md     # This file
```

## Phases Overview

### Phase-I: Todo CLI Application
- **Type**: Command-line interface application
- **Tech Stack**: Python, Click, SQLite
- **Features**: Basic todo management via CLI
- **Status**: Completed

### Phase-II: Full-Stack Todo Application
- **Type**: Web application with REST API
- **Tech Stack**:
  - Backend: FastAPI, SQLModel, PostgreSQL, JWT Authentication
  - Frontend: Next.js 16, TypeScript, Tailwind CSS, Better Auth
  - Deployment: Render (backend), Vercel (frontend)
- **Features**:
  - Complete CRUD operations for tasks
  - JWT-based authentication with Better Auth
  - Multi-user data isolation
  - Responsive UI with animations
  - Health monitoring and logging
- **Status**: Ready for deployment
- **Deployment**: See [phase-II/backend/README.md](phase-II/backend/README.md) for deployment guide

### Phase-III: AI-Powered Todo Application
- **Type**: Advanced web application with AI features
- **Tech Stack**: TBD
- **Features**: AI-powered task management, smart suggestions
- **Status**: In development

## Quick Start

### Phase-I (CLI Application)

```bash
cd phase-I/todo-cli
pip install -r requirements.txt
python todo.py
```

### Phase-II (Full-Stack Application)

**Backend**:
```bash
cd phase-II/backend
pip install -e .[dev]
alembic upgrade head
gunicorn src.main:app --reload
```

**Frontend**:
```bash
cd phase-II/frontend
npm install
npm run dev
```

See [phase-II/backend/README.md](phase-II/backend/README.md) for detailed setup and deployment instructions.

### Phase-III

See [phase-III/README.md](phase-III/README.md) for specific instructions.

## Deployment

### Phase-II Current Deployment Status
- **Backend**: Migrated to Render (from Vercel)
  - Configuration: `phase-II/backend/render.yaml`
  - See [Render Deployment Guide](phase-II/backend/README.md#deploying-to-render-recommended)
- **Frontend**: Deployed on Vercel
  - Configuration: `phase-II/frontend/vercel.json`

## Development Workflow

When working on a specific phase:

1. Navigate to the phase directory: `cd phase-X/`
2. Follow the phase-specific README instructions
3. Make changes within that phase directory
4. Test the phase independently
5. Commit changes with clear phase identifiers

## Project Management

Each phase represents a distinct milestone:
- **Phase-I**: Foundation and basic functionality
- **Phase-II**: Production-ready web application with authentication
- **Phase-III**: Advanced features and AI integration

## Contributing

When contributing:
- Clearly indicate which phase you're working on
- Follow the coding standards for that phase
- Update documentation within the phase directory
- Test thoroughly before committing

## License

[Your License Here]

---

**Last Updated**: 2026-02-06
**Repository**: https://github.com/Danii9790/Q4-Hackhthon-II
