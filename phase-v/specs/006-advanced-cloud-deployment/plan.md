# Implementation Plan: Advanced Cloud Deployment

**Branch**: `006-advanced-cloud-deployment` | **Date**: 2026-02-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-advanced-cloud-deployment/spec.md`

**Note**: This plan is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Phase V transforms the Todo AI Chatbot from a basic CRUD application into an enterprise-grade, event-driven microservices system with advanced task management capabilities. The system will support recurring tasks, intelligent reminders, real-time synchronization, and complete audit trails while deploying locally on Minikube for development and production on DigitalOcean Kubernetes. The architecture uses Kafka for event streaming, Dapr for distributed application runtime, and follows a stateless, tool-driven AI behavior model per the project constitution.

**Technical Approach**:
- Extend database schema with advanced task attributes (due dates, priorities, tags, recurrence)
- Implement event-driven architecture using Kafka (Redpanda)
- Integrate Dapr for Pub/Sub, State, Bindings, Secrets, and Service Invocation
- Create Kubernetes deployment manifests for local (Minikube) and production (DigitalOcean)
- Build CI/CD pipeline with GitHub Actions
- Add monitoring with Prometheus, Grafana, and Loki

## Technical Context

**Language/Version**:
- Backend: Python 3.12+ (FastAPI)
- Frontend: TypeScript 5.0+ (Next.js 16)
- Infrastructure: YAML (Kubernetes manifests, Helm charts, GitHub Actions)

**Primary Dependencies**:
- **Backend**: FastAPI, SQLModel, Alembic, aiokafka, dapr-sdk, httpx, kafka-python
- **Frontend**: OpenAI ChatKit, Next.js, Better Auth, Axios, React Query
- **Infrastructure**: Docker, Kubernetes, Helm, Minikube, DigitalOcean DOKS
- **Event Streaming**: Redpanda (Kafka-compatible)
- **Dapr**: Dapr sidecar, Dapr components (Pub/Sub, State, Bindings, Secrets)
- **Monitoring**: Prometheus, Grafana, Loki
- **CI/CD**: GitHub Actions

**Storage**:
- **Database**: Neon Serverless PostgreSQL (existing, extended with new models)
- **Event Log**: Kafka topics (task-events, reminders, task-updates)
- **State Store**: PostgreSQL via Dapr State component (optional caching)
- **Secrets**: Kubernetes Secrets via Dapr Secret store

**Testing**:
- **Backend**: pytest, pytest-asyncio, httpx (testing client), pytest-mock
- **Frontend**: Jest, React Testing Library
- **Integration**: Docker Compose for local integration tests
- **E2E**: Playwright or Cypress (optional)

**Target Platform**:
- **Local Development**: Minikube (Kubernetes locally)
- **Production**: DigitalOcean Kubernetes (DOKS)
- **Container Registry**: Docker Hub or DigitalOcean Container Registry

**Project Type**: Full-stack web application with event-driven microservices architecture

**Performance Goals**:
- API response time: < 200ms p95 for CRUD operations
- Event publishing latency: < 50ms p95
- Real-time sync delay: < 2 seconds
- Support 1,000 concurrent users (production target)
- Handle 10,000 tasks with advanced filters without performance degradation

**Constraints**:
- Stateless architecture: No in-memory state, all state in database
- Tool-driven AI: All state changes through MCP tools only
- Kafka message delivery: At-least-once semantics with idempotency
- Deployment: Zero-downtime rolling updates
- Budget: Under $100/month on DigitalOcean for 1,000 active users

**Scale/Scope**:
- Users: 1,000 active users (production target)
- Tasks: 10,000+ tasks with advanced attributes
- Events: 100,000+ events in audit trail
- Services: 5 services (Frontend, Backend, Notification Service, Recurring Task Service, Audit Service)
- Kafka Topics: 3 topics (task-events, reminders, task-updates)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Before proceeding with this plan, verify compliance with the project constitution (`.specify/memory/constitution.md`):

- [x] **Stateless Architecture**: No in-memory state; all state in database
  - **Compliance**: All services are stateless; FastAPI holds no in-memory state; Dapr State component only caches, database is source of truth
- [x] **Tool-Driven AI Behavior**: All state changes through MCP tools
  - **Compliance**: All task operations use existing MCP tools (add_task, update_task, etc.); new tools added for advanced features
- [x] **Task Operation Correctness**: Atomic, traceable operations
  - **Compliance**: Database transactions ensure atomicity; Kafka events provide traceability; audit trail captures all operations
- [x] **Conversational State Persistence**: History reconstructed on each request
  - **Compliance**: Existing conversation flow unchanged; history loaded from database on each request
- [x] **Natural Language Understanding**: Casual, simple phrases supported
  - **Compliance**: AI agent trained to understand advanced queries (e.g., "show high priority work tasks due this week")
- [x] **Error Handling**: Graceful, user-friendly error messages
  - **Compliance**: All Kafka failures retry with exponential backoff; errors logged to audit trail; user never sees stack traces
- [x] **Agent Intent Routing**: Correct tool selection for user intents
  - **Compliance**: New MCP tools for advanced features (set_priority, set_due_date, create_recurring_task, etc.)
- [x] **Data Integrity**: User isolation, referential integrity enforced
  - **Compliance**: All events include user_id; foreign keys enforced; users cannot access others' tasks
- [x] **Spec-Driven Development**: Adheres to Phase-III specification
  - **Compliance**: Extends existing Phase III/IV features; maintains backward compatibility

**Non-Compliance Notes**: None. This plan fully complies with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/006-advanced-cloud-deployment/
├── spec.md              # Feature specification
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── openapi.yaml     # OpenAPI specification for backend APIs
│   └── mcp-tools.yaml   # MCP tool schemas
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/                    # Database models
│   │   ├── user.py                # Existing
│   │   ├── task.py                # EXTEND: Add advanced fields
│   │   ├── conversation.py        # Existing
│   │   ├── message.py             # Existing
│   │   ├── task_event.py          # NEW: Audit trail
│   │   ├── reminder.py            # NEW: Reminders
│   │   ├── recurring_task.py      # NEW: Recurring tasks
│   │   └── __init__.py
│   ├── services/                  # Business logic
│   │   ├── auth.py                # Existing
│   │   ├── task.py                # EXTEND: Advanced features
│   │   ├── conversation.py        # Existing
│   │   ├── agent.py               # Existing
│   │   ├── kafka_producer.py      # NEW: Kafka event publishing
│   │   ├── kafka_consumer.py      # NEW: Reminder consumer
│   │   ├── recurring_service.py   # NEW: Recurring task logic
│   │   └── __init__.py
│   ├── mcp_tools/                 # MCP tools (extensible)
│   │   ├── add_task.py            # Existing: EXTEND for new fields
│   │   ├── update_task.py         # Existing: EXTEND for new fields
│   │   ├── complete_task.py       # Existing: Add Kafka publishing
│   │   ├── delete_task.py         # Existing: Add Kafka publishing
│   │   ├── list_tasks.py          # Existing: EXTEND for filters
│   │   ├── set_task_priority.py   # NEW
│   │   ├── set_task_due_date.py   # NEW
│   │   ├── add_task_tags.py       # NEW
│   │   ├── search_tasks.py        # NEW
│   │   ├── filter_tasks.py        # NEW
│   │   ├── sort_tasks.py          # NEW
│   │   ├── create_recurring_task.py # NEW
│   │   └── __init__.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── tasks.py           # EXTEND: Advanced CRUD endpoints
│   │   │   ├── auth.py            # Existing
│   │   │   ├── chat.py            # Existing
│   │   │   └── __init__.py
│   │   └── dependencies.py        # Existing
│   ├── db/
│   │   ├── session.py             # Existing
│   │   └── __init__.py
│   ├── main.py                    # EXTEND: Add Dapr initialization
│   └── schemas.py                 # EXTEND: Add new request/response schemas
├── tests/
│   ├── unit/                      # NEW: Unit tests for services
│   ├── integration/               # NEW: Integration tests for Kafka
│   └── e2e/                       # NEW: End-to-end tests
├── alembic/
│   └── versions/
│       └── 20250210_phase_v_schema.py  # NEW: Database migration
├── Dockerfile                     # Existing: EXTEND for Dapr sidecar
├── docker-compose.yml             # NEW: Local development
└── requirements.txt               # EXTEND: Add new dependencies

frontend/
├── src/
│   ├── components/
│   │   ├── task/
│   │   │   ├── TaskList.tsx       # EXTEND: Filter, sort, search UI
│   │   │   ├── TaskItem.tsx       # EXTEND: Show priority, tags, due date
│   │   │   ├── CreateTaskForm.tsx # EXTEND: Add advanced fields
│   │   │   ├── TaskFilters.tsx    # NEW: Filter panel
│   │   │   └── EditTaskModal.tsx  # EXTEND: Edit advanced fields
│   │   ├── chat/
│   │   │   └── ChatWidget.tsx     # EXTEND: Real-time updates via Kafka
│   │   └── auth/
│   │       └── AuthGuard.tsx      # Existing
│   ├── lib/
│   │   ├── api.ts                 # EXTEND: Add advanced endpoints
│   │   ├── auth.ts                # Existing
│   │   └── kafka-client.ts        # NEW: Kafka consumer for real-time
│   ├── types/
│   │   ├── task.ts                # EXTEND: Add TaskAdvanced interface
│   │   └── chat.ts                # Existing
│   └── app/
│       ├── dashboard/
│       │   └── page.tsx           # EXTEND: Show advanced filters
│       └── chat/
│           └── page.tsx           # EXTEND: Real-time sync
├── Dockerfile                     # Existing
├── docker-compose.yml             # NEW: Connect to backend services
└── package.json                   # EXTEND: Add Kafka client lib

infrastructure/                    # NEW: Infrastructure as Code
├── docker/
│   ├── docker-compose.yml         # Local development stack
│   ├── kafka-redpanda.yml         # Redpanda configuration
│   └── dapr/                      # Dapr component configurations
│       ├── pubsub.yaml            # Kafka Pub/Sub
│       ├── state.yaml             # State store (PostgreSQL)
│       ├── bindings.yaml          # Cron bindings for reminders
│       └── secrets.yaml           # Kubernetes secrets
├── kubernetes/
│   ├── base/                      # Base Kubernetes manifests
│   │   ├── namespace.yaml
│   │   ├── configmaps.yaml
│   │   ├── secrets.yaml
│   │   ├── backend/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── hpa.yaml
│   │   │   └── podmonitor.yaml    # Prometheus monitoring
│   │   ├── frontend/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── hpa.yaml
│   │   │   └── ingress.yaml
│   │   ├── kafka/                 # Strimzi or Redpanda operator
│   │   │   ├── kafka-cluster.yaml
│   │   │   └── kafka-topics.yaml
│   │   └── monitoring/            # Prometheus, Grafana, Loki
│   │       ├── prometheus.yaml
│   │       ├── grafana.yaml
│   │       └── loki.yaml
│   ├── minikube/                  # Minikube-specific overlays
│   │   └── kustomization.yaml
│   └── production/                # DigitalOcean-specific overlays
│       └── kustomization.yaml
└── helm/                          # Helm charts
    ├── todo-chatbot/              # Existing: EXTEND
    │   ├── Chart.yaml
    │   ├── values.yaml
    │   ├── values-minikube.yaml   # NEW
    │   ├── values-production.yaml # NEW
    │   └── templates/
    │       ├── backend/           # EXTEND: Add Dapr sidecar
    │       ├── frontend/          # Existing
    │       ├── kafka/             # NEW
    │       ├── dapr/              # NEW
    │       └── monitoring/        # NEW
    └── notification-service/      # NEW: Separate service for reminders
        ├── Chart.yaml
        ├── values.yaml
        └── templates/

.github/
└── workflows/
    ├── test.yml                   # NEW: Run tests on PR
    ├── build.yml                  # NEW: Build Docker images
    └── deploy.yml                 # NEW: Deploy to Kubernetes

scripts/
├── setup-minikube.sh              # NEW: One-click Minikube setup
├── setup-dapr.sh                  # NEW: Install Dapr locally
└── deploy-production.sh           # NEW: Deploy to DigitalOcean
```

**Structure Decision**: Web application structure (Option 2) with separate frontend and backend repositories. Additional `infrastructure/` directory added for Kubernetes manifests, Helm charts, and CI/CD configurations. The backend is extended with event-driven services (kafka_producer, kafka_consumer, recurring_service). MCP tools are extended with 9 new tools for advanced features.

## Complexity Tracking

> **No violations**: Constitution check passed with full compliance. No complexity tracking required.

---

## Phase 0: Research & Technology Decisions

### Research Tasks

This phase resolves all unknown technologies and validates architectural decisions before implementation.

#### R1: Kafka Integration Pattern Research
**Decision**: Use Redpanda (Kafka-compatible) for event streaming
**Rationale**:
- Free serverless tier for hackathon (no credit card required for basic usage)
- Kafka-compatible: Same APIs, clients work unchanged
- No Zookeeper: Simpler architecture than vanilla Kafka
- Fast setup: Under 5 minutes
- REST API + Native protocols supported

**Alternatives Considered**:
- **Confluent Cloud**: Industry standard but $400 credit expires quickly
- **CloudKarafka**: Simple but limited throughput on free tier
- **Self-hosted Strimzi**: Full control but complex setup for hackathon timeline

**References**:
- https://redpanda.com/cloud
- https://docs.redpanda.com/current/

#### R2: Dapr Component Configuration Research
**Decision**: Use Dapr v1.14 for distributed application runtime
**Rationale**:
- Abstracts infrastructure (Kafka, Redis, Postgres) behind HTTP APIs
- Swap backends by changing YAML config, not code
- Built-in retries, circuit breakers, service discovery
- Sidecar pattern: No code changes to application logic

**Alternatives Considered**:
- **Direct Kafka clients (kafka-python)**: Tight coupling, no retry logic, complex error handling
- **Custom service mesh**: Too much complexity for hackathon

**Components to Configure**:
- `pubsub.kafka`: Event streaming abstraction
- `state.postgresql`: Conversation state caching (optional)
- `bindings.cron`: Scheduled reminder checks
- `secretstores.kubernetes`: API keys, DB credentials

**References**:
- https://docs.dapr.io/
- https://docs.dapr.io/operations/components/setup-supported/

#### R3: Database Schema for Recurring Tasks Research
**Decision**: Add `recurring_task` table linked to tasks with one-to-many relationship
**Rationale**:
- One parent recurring task → Many child task occurrences
- Parent holds schedule (frequency, end_date)
- Children are actual tasks with due dates
- When child completed, Kafka event triggers creation of next child

**Schema Design**:
```sql
CREATE TABLE recurring_tasks (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    frequency VARCHAR(20) NOT NULL, -- 'DAILY', 'WEEKLY', 'MONTHLY'
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,              -- NULL = never ends
    next_occurrence TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Child tasks link back to parent
ALTER TABLE tasks ADD COLUMN recurring_task_id UUID REFERENCES recurring_tasks(id);
```

**Alternatives Considered**:
- **Single table with recurrence columns**: Hard to query history of occurrences
- **Separate schedule table**: Over-engineered for hackathon

#### R4: Real-Time Sync Architecture Research
**Decision**: Use Kafka for broadcast, frontend polls Kafka topic via WebSocket gateway
**Rationale**:
- Kafka handles message ordering and durability
- Frontend doesn't need direct Kafka connection (security risk)
- WebSocket gateway subscribes to Kafka, forwards to clients
- Dapr Service Invocation for frontend → gateway communication

**Architecture Flow**:
```
Task Update → Backend → Kafka (task-updates topic)
                            ↓
                     WebSocket Gateway (Kafka consumer)
                            ↓
                     Connected Clients (WebSocket)
```

**Alternatives Considered**:
- **Direct WebSocket in backend**: Tightly coupled, hard to scale
- **Server-Sent Events (SSE)**: One-way only, no bidirectional communication
- **Push notifications**: Doesn't update UI in real-time

#### R5: Kubernetes Deployment Strategy Research
**Decision**: Use Helm charts with environment-specific values (minikube, production)
**Rationale**:
- Helm standard for Kubernetes packaging
- Reusable across environments (DRY principle)
- Easy upgrades with `helm upgrade`
- DigitalOcean has excellent Helm support

**Helm Chart Structure**:
- `values.yaml`: Default configuration
- `values-minikube.yaml`: Local development overrides
- `values-production.yaml`: DigitalOcean production overrides
- `templates/`: Kubernetes manifests with Go templating

**Alternatives Considered**:
- **Kustomize**: More verbose, harder to manage for complex charts
- **Plain manifests**: No environment-specific configuration, hard to maintain

#### R6: CI/CD Pipeline Research
**Decision**: GitHub Actions with build, test, and deploy stages
**Rationale**:
- Native GitHub integration
- Free for public repositories
- YAML-based, easy to version control
- Excellent marketplace actions (docker/login-action, azure/k8s-deploy)

**Pipeline Stages**:
1. **Test**: `pytest` for backend, `npm test` for frontend
2. **Build**: Build Docker images, push to registry
3. **Deploy**: Apply Helm charts to Kubernetes with `helm upgrade`

**Alternatives Considered**:
- **GitLab CI**: Not hosted on GitHub, requires migration
- **CircleCI / TravisCI**: External services, less integrated

#### R7: Monitoring Stack Research
**Decision**: Prometheus + Grafana + Loki for metrics, dashboards, and logs
**Rationale**:
- Prometheus: Industry standard for metrics (pull-based)
- Grafana: Beautiful dashboards, Prometheus-native
- Loki: Lightweight log aggregation (labels vs full-text search)
- All three integrate seamlessly

**Deployment**:
- All three run in Kubernetes (Helm charts available)
- Prometheus scrapes `/metrics` endpoints from services
- Grafana reads Prometheus data for visualization
- Loki aggregates logs from all pods

**Alternatives Considered**:
- **ELK Stack (Elasticsearch, Logstash, Kibana)**: Heavy resource requirements
- **CloudWatch**: DigitalOcean-specific, lock-in
- **DataDog**: Expensive for hackathon budget

---

### Research Output: research.md

**Status**: ✅ Complete

All research tasks resolved. Key decisions:
1. **Kafka**: Redpanda Cloud (free tier) for production, Redpanda Docker for local
2. **Dapr**: Full Dapr for Pub/Sub, State, Bindings, Secrets
3. **Database**: Extend Task model, add TaskEvent, Reminder, RecurringTask models
4. **Real-Time**: Kafka + WebSocket gateway pattern
5. **Kubernetes**: Helm charts with environment-specific values
6. **CI/CD**: GitHub Actions with test, build, deploy stages
7. **Monitoring**: Prometheus + Grafana + Loki stack

---

## Phase 1: Design & Contracts

### Data Model Design

See [data-model.md](./data-model.md) for complete database schema including:
- Extended Task model with advanced fields
- TaskEvent model for audit trail
- Reminder model for scheduled notifications
- RecurringTask model for recurring task templates
- Relationships and indexes

### API Contracts

See [contracts/openapi.yaml](./contracts/openapi.yaml) for complete API specification including:
- Extended task endpoints (filter, sort, search)
- Reminder endpoints
- Recurring task endpoints
- Real-time sync endpoints (WebSocket gateway)

See [contracts/mcp-tools.yaml](./contracts/mcp-tools.yaml) for MCP tool schemas:
- 9 new MCP tools for advanced features
- Extended existing tools with new parameters

### Quick Start Guide

See [quickstart.md](./quickstart.md) for:
- Local development setup with Docker Compose
- Minikube deployment instructions
- Production deployment to DigitalOcean
- CI/CD pipeline setup

---

## Architecture Decision Records (ADRs)

### ADR-001: Event-Driven Architecture with Kafka

**Status**: Accepted

**Context**: Phase V requires decoupled services for reminders, recurring tasks, and real-time sync. Direct API calls create tight coupling and don't scale.

**Decision**: Use Kafka for event streaming with three topics:
- `task-events`: All task CRUD operations (create, update, complete, delete)
- `reminders`: Scheduled reminder notifications
- `task-updates`: Real-time synchronization broadcasts

**Consequences**:
- **Positive**: Loose coupling, async processing, scalability
- **Positive**: Built-in audit trail (all events persisted)
- **Positive**: Multiple consumers can process same event independently
- **Negative**: Added complexity (Kafka cluster, consumer groups)
- **Negative**: Eventual consistency (not immediate)

**Alternatives Considered**:
- Direct HTTP calls between services: Tight coupling
- Database polling: Inefficient, doesn't scale
- Redis pub/sub: Not durable, no replay capability

### ADR-002: Dapr for Distributed Application Runtime

**Status**: Accepted

**Context**: Application needs to interact with Kafka, PostgreSQL, and Kubernetes secrets. Direct client libraries create tight coupling and infrastructure lock-in.

**Decision**: Use Dapr sidecar with HTTP APIs for Pub/Sub, State, Bindings, and Secrets.

**Consequences**:
- **Positive**: Infrastructure abstraction (swap Kafka for RabbitMQ via config)
- **Positive**: Built-in retries, circuit breakers, service discovery
- **Positive**: No infrastructure code in application logic
- **Negative**: Additional sidecar container (resource overhead)
- **Negative**: Learning curve for Dapr APIs

**Alternatives Considered**:
- Direct Kafka clients (kafka-python): Tightly coupled
- Custom service mesh: Too complex for hackathon

### ADR-003: Stateless Services with Database Persistence

**Status**: Accepted (Constitution Principle)

**Context**: Multiple services (backend, notification, recurring task) need to share state. In-memory state creates scaling issues and data loss on crashes.

**Decision**: All services are stateless; all state persisted in Neon PostgreSQL. Services reconstruct state on each request.

**Consequences**:
- **Positive**: Horizontal scalability (add more pods)
- **Positive**: Survives pod crashes without data loss
- **Positive**: Simple deployment (no sticky sessions required)
- **Negative**: Added latency (database queries vs memory)
- **Negative**: Database becomes bottleneck (mitigate with caching)

**Alternatives Considered**:
- Redis cache: Adds complexity, violates constitution (in-memory state)
- Distributed cache (Memcached): Additional infrastructure to manage

### ADR-004: Helm Charts for Multi-Environment Deployment

**Status**: Accepted

**Context**: Application must deploy locally (Minikube) and production (DigitalOcean). Hardcoded values don't work across environments.

**Decision**: Use Helm charts with environment-specific values files:
- `values.yaml`: Defaults
- `values-minikube.yaml`: Local development (smaller resource limits)
- `values-production.yaml`: DigitalOcean (HPA, SSL, monitoring)

**Consequences**:
- **Positive**: Single chart for all environments
- **Positive**: DRY principle (reuse templates)
- **Positive**: Easy upgrades with `helm upgrade`
- **Negative**: Helm templating learning curve
- **Negative**: Debugging templates can be tricky

**Alternatives Considered**:
- Kustomize: More verbose, patch-based approach
- Plain manifests: No environment-specific config

---

## Implementation Phases Overview

The implementation will follow a phased approach, delivering value incrementally:

### Phase 1: Database Schema & Basic Advanced Features (P1)
- Extend Task model with due_date, priority, tags
- Create migration scripts
- Update MCP tools to support new fields
- Implement filter, sort, search functionality

### Phase 2: Event-Driven Architecture (P1)
- Set up Kafka (Redpanda)
- Implement event producers in MCP tools
- Create audit trail via TaskEvent model

### Phase 3: Recurring Tasks & Reminders (P2)
- Implement RecurringTask model and logic
- Create reminder scheduler service
- Add Kafka consumers for reminders and recurring tasks

### Phase 4: Real-Time Sync (P3)
- Implement WebSocket gateway
- Connect Kafka to WebSocket gateway
- Frontend integration for real-time updates

### Phase 5: Local Deployment (P1)
- Create Docker Compose for local development
- Set up Minikube with Dapr
- Deploy full stack locally

### Phase 6: Production Deployment (P1)
- Update Helm charts for production
- Configure CI/CD pipeline
- Deploy to DigitalOcean

### Phase 7: Monitoring & Observability (P2)
- Set up Prometheus, Grafana, Loki
- Create dashboards and alerts
- Configure logging

---

## Dependencies & Risks

### External Dependencies
- **Neon PostgreSQL**: Database uptime (external service)
- **Redpanda Cloud**: Kafka cluster availability
- **DigitalOcean DOKS**: Kubernetes cluster uptime
- **GitHub Actions**: CI/CD pipeline execution

### Technical Risks
1. **Kafka Delivery Failures**: Mitigated with exponential backoff retries
2. **Database Migration Failures**: Mitigated with Alembic transaction support
3. **Dapr Sidecar Crashes**: Kubernetes liveness probes restart pod
4. **Concurrent Task Updates**: Database transactions with row locking
5. **Minikube Resource Limits**: Document minimum requirements (8GB RAM, 4 CPU)

### Operational Risks
1. **Production Deployment Downtime**: Use rolling updates, readiness probes
2. **Cost Overrun**: Monitor DigitalOcean spend alerts
3. **CI/CD Pipeline Failures**: Manual approval for production deployments
4. **Monitoring Gaps**: Comprehensive alerts for critical metrics

---

## Success Metrics

The implementation is considered successful when:

1. **Advanced Task Features**: Users can create tasks with due dates, priorities, tags in under 10 seconds
2. **Recurring Tasks**: System auto-creates next occurrence within 5 seconds of completion
3. **Reminders**: 95% of reminders sent within 1 minute of scheduled time
4. **Real-Time Sync**: Changes appear on all devices within 2 seconds
5. **Audit Trail**: 100% of task operations captured in event log
6. **Local Deployment**: Minikube setup completes in under 30 minutes
7. **Production Deployment**: Application handles 1,000 concurrent users
8. **CI/CD**: Full test, build, deploy cycle completes in under 15 minutes
9. **Monitoring**: Operators alerted within 1 minute of critical failures
10. **Uptime**: 99.9% uptime in production (excluding maintenance)

---

**END OF IMPLEMENTATION PLAN**
