# Tasks: Advanced Cloud Deployment

**Input**: Design documents from `/specs/006-advanced-cloud-deployment/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

**Tests**: Test tasks included for backend services and infrastructure validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Constitution Compliance Check

All tasks MUST comply with the project constitution (`.specify/memory/constitution.md`):

**Principle Compliance Matrix**:

| Task ID | Stateless | Tool-Driven | Correctness | Persistence | NL Understanding | Error Handling | Intent Routing | Data Integrity | Spec-Driven |
|---------|-----------|-------------|-------------|-------------|------------------|----------------|----------------|----------------|-------------|
| All Tasks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Legend**: ✅ Complies | ⚠️ Partial | ❌ Non-compliant (requires justification)

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`
- **Frontend**: `frontend/src/`
- **Infrastructure**: `infrastructure/`
- **Tests**: `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency installation

- [x] T001 Install backend dependencies in backend/requirements.txt (kafka-python, aiokafka, dapr-sdk-python, httpx)
- [x] T002 [P] Install frontend dependencies in frontend/package.json (@kafkajs/consumer, react-query for real-time)
- [x] T003 [P] Create infrastructure directory structure in infrastructure/docker/, infrastructure/kubernetes/, infrastructure/helm/
- [x] T004 [P] Initialize Dapr component configuration files in infrastructure/docker/dapr/ (pubsub.yaml, state.yaml, bindings.yaml, secrets.yaml)
- [x] T005 [P] Create GitHub Actions workflow templates in .github/workflows/ (test.yml, build.yml, deploy.yml)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Schema

- [x] T006 Create Alembic migration for Phase V schema in backend/alembic/versions/20250210_phase_v_schema.py (extend Task, add TaskEvent, Reminder, RecurringTask models)

### Kafka Infrastructure

- [x] T007 [P] Create Docker Compose file for local Kafka in infrastructure/docker/docker-compose.yml (Redpanda, PostgreSQL, backend, frontend)
- [x] T008 [P] Create Kafka topics configuration in infrastructure/docker/kafka-topics.yaml (task-events, reminders, task-updates)
- [x] T009 Create Kafka producer service in backend/src/services/kafka_producer.py (publish events with error handling and retries)

### Dapr Integration

- [ ] T010 [P] Create Dapr Pub/Sub component in infrastructure/kubernetes/base/dapr/pubsub.yaml (Kafka configuration)
- [ ] T011 [P] Create Dapr State component in infrastructure/kubernetes/base/dapr/state.yaml (PostgreSQL state store)
- [ ] T012 [P] Create Dapr Cron Binding component in infrastructure/kubernetes/base/dapr/bindings.yaml (reminder scheduler)
- [ ] T013 [P] Create Dapr Secrets component in infrastructure/kubernetes/base/dapr/secrets.yaml (Kubernetes secrets)
- [ ] T014 Initialize Dapr client in backend/src/main.py (Dapr sidecar integration)

### Extended Models

- [x] T015 [P] Extend Task model in backend/src/models/task.py (add due_date, priority, tags, recurring_task_id fields)
- [x] T016 [P] Create TaskEvent model in backend/src/models/task_event.py (audit trail: event_type, task_id, user_id, event_data, timestamp)
- [x] T017 [P] Create Reminder model in backend/src/models/reminder.py (task_id, remind_at, sent, sent_at)
- [x] T018 [P] Create RecurringTask model in backend/src/models/recurring_task.py (title, frequency, start_date, end_date, next_occurrence)

### Base Services

- [x] T019 Implement event publishing middleware in backend/src/services/event_publisher.py (publish to Kafka after DB operations)
- [x] T020 Create audit logging service in backend/src/services/audit_service.py (log all task operations to TaskEvent)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Advanced Task Management (Priority: P1) 🎯 MVP

**Goal**: Users can create tasks with due dates, priorities, and tags, and filter/sort/search tasks

**Independent Test**: Create task with due date "2026-02-15", priority "high", tags ["work", "urgent"], then verify it persists and can be filtered by priority, sorted by due date, and searched for text

### Tests for User Story 1

- [x] T021 [P] [US1] Write integration test for task creation with advanced fields in backend/tests/integration/test_task_advanced.py
- [x] T022 [P] [US1] Write integration test for task filtering by priority in backend/tests/integration/test_task_filters.py
- [x] T023 [P] [US1] Write integration test for task sorting by due date in backend/tests/integration/test_task_sort.py
- [x] T024 [P] [US1] Write integration test for task full-text search in backend/tests/integration/test_task_search.py

### Implementation for User Story 1

**Backend MCP Tools**

- [x] T025 [P] [US1] Extend add_task MCP tool in backend/src/mcp_tools/add_task.py (add due_date, priority, tags parameters, publish event to Kafka)
- [x] T026 [P] [US1] Extend update_task MCP tool in backend/src/mcp_tools/update_task.py (support updating due_date, priority, tags, publish event)
- [x] T027 [P] [US1] Extend complete_task MCP tool in backend/src/mcp_tools/complete_task.py (publish task-completed event to Kafka)
- [x] T028 [P] [US1] Extend delete_task MCP tool in backend/src/mcp_tools/delete_task.py (publish task-deleted event to Kafka)
- [x] T029 [P] [US1] Extend list_tasks MCP tool in backend/src/mcp_tools/list_tasks.py (add priority, tags, due_before, due_after, sort_by, sort_order parameters)

**Backend New MCP Tools**

- [x] T030 [P] [US1] Create set_task_priority MCP tool in backend/src/mcp_tools/set_task_priority.py (update priority field, publish event)
- [x] T031 [P] [US1] Create set_task_due_date MCP tool in backend/src/mcp_tools/set_task_due_date.py (update due_date field, publish event)
- [x] T032 [P] [US1] Create add_task_tags MCP tool in backend/src/mcp_tools/add_task_tags.py (append tags to existing tags array, publish event)
- [x] T033 [P] [US1] Create search_tasks MCP tool in backend/src/mcp_tools/search_tasks.py (full-text search in title and description)
- [x] T034 [P] [US1] Create filter_tasks MCP tool in backend/src/mcp_tools/filter_tasks.py (filter by priority, tags, due date range)
- [x] T035 [P] [US1] Create sort_tasks MCP tool in backend/src/mcp_tools/sort_tasks.py (sort by due_date, priority, created_at, completed_at)

**Backend Services**

- [x] T036 [US1] Extend task service with advanced query logic in backend/src/services/task.py (filter, sort, search implementation with indexes)
- [x] T037 [US1] Add validation for priority enum in backend/src/services/task.py (LOW, MEDIUM, HIGH only)
- [x] T038 [US1] Add validation for tags array in backend/src/services/task.py (max 10 tags, max 50 chars each)
- [x] T039 [US1] Add validation for due_date timezone in backend/src/services/task.py (store in UTC, validate future date)

**Backend API Routes**

- [x] T040 [P] [US1] Add GET /api/tasks endpoint with filters in backend/src/api/routes/tasks.py (priority, tags, due_before, due_after, search, sort_by, sort_order, limit, offset)
- [x] T041 [P] [US1] Add PATCH /api/tasks/{task_id}/priority endpoint in backend/src/api/routes/tasks.py
- [x] T042 [P] [US1] Add PATCH /api/tasks/{task_id}/due-date endpoint in backend/src/api/routes/tasks.py
- [x] T043 [P] [US1] Add POST /api/tasks/{task_id}/tags endpoint in backend/src/api/routes/tasks.py

**Backend Schemas**

- [x] T044 [P] [US1] Extend TaskCreate schema in backend/src/schemas.py (add due_date, priority, tags optional fields)
- [x] T045 [P] [US1] Extend TaskUpdate schema in backend/src/schemas.py (add due_date, priority, tags optional fields)
- [x] T046 [P] [US1] Extend TaskResponse schema in backend/src/schemas.py (add due_date, priority, tags fields)

**Frontend Components**

- [x] T047 [P] [US1] Extend TaskItem component in frontend/src/components/task/TaskItem.tsx (display priority badge, due date, tags)
- [x] T048 [P] [US1] Extend CreateTaskForm component in frontend/src/components/task/CreateTaskForm.tsx (add due date picker, priority selector, tags input)
- [x] T049 [P] [US1] Extend EditTaskModal component in frontend/src/components/task/EditTaskModal.tsx (add due date, priority, tags editing)
- [x] T050 [P] [US1] Create TaskFilters component in frontend/src/components/task/TaskFilters.tsx (filter panel with priority, tags, date range)

**Frontend Services**

- [x] T051 [US1] Extend API client with advanced task endpoints in frontend/src/lib/api.ts (filterTasks, sortTasks, searchTasks functions)
- [x] T052 [US1] Add task filter state management in frontend/src/lib/api.ts (filter params state)

**Frontend Pages**

- [x] T053 [US1] Extend dashboard page with filter UI in frontend/src/app/dashboard/page.tsx (integrate TaskFilters component)

**Checkpoint**: User Story 1 complete - users can create advanced tasks and filter/sort/search them

---

## Phase 4: User Story 2 - Recurring Task Automation (Priority: P2)

**Goal**: Users can create recurring tasks that auto-generate next occurrences when completed

**Independent Test**: Create recurring task "Daily standup" with frequency DAILY, complete it, verify next occurrence created for tomorrow

### Tests for User Story 2

- [ ] T054 [P] [US2] Write integration test for recurring task creation in backend/tests/integration/test_recurring_tasks.py
- [ ] T055 [P] [US2] Write integration test for next occurrence calculation in backend/tests/integration/test_recurring_logic.py
- [ ] T056 [P] [US2] Write integration test for recurring task completion triggers next occurrence in backend/tests/integration/test_recurring_completion.py

### Implementation for User Story 2

**Backend Services**

- [ ] T057 [P] [US2] Create recurring task service in backend/src/services/recurring_service.py (calculate next occurrence based on frequency)
- [ ] T058 [US2] Implement DAILY frequency logic in backend/src/services/recurring_service.py (next_day = current_day + 1 day)
- [ ] T059 [US2] Implement WEEKLY frequency logic in backend/src/services/recurring_service.py (next_week = current_day + 7 days)
- [ ] T060 [US2] Implement MONTHLY frequency logic in backend/src/services/recurring_service.py (next_month = same day number next month)
- [ ] T061 [US2] Add end_date handling in backend/src/services/recurring_service.py (stop creating occurrences if next_occurrence > end_date)

**Backend Kafka Consumer**

- [ ] T062 [P] [US2] Create recurring task Kafka consumer in backend/src/services/recurring_consumer.py (consume task-completed events from Kafka)
- [ ] T063 [US2] Implement next occurrence creation in backend/src/services/recurring_consumer.py (check if task has recurring_task_id, create next occurrence)
- [ ] T064 [US2] Add error handling and retry logic in backend/src/services/recurring_consumer.py (handle Kafka failures)

**Backend MCP Tools**

- [ ] T065 [P] [US2] Create create_recurring_task MCP tool in backend/src/mcp_tools/create_recurring_task.py (create RecurringTask and first Task occurrence)
- [ ] T066 [US2] Extend complete_task MCP tool in backend/src/mcp_tools/complete_task.py (return next_occurrence info in response)

**Backend API Routes**

- [ ] T067 [P] [US2] Add GET /api/recurring-tasks endpoint in backend/src/api/routes/tasks.py (list user's recurring task templates)
- [ ] T068 [P] [US2] Add POST /api/recurring-tasks endpoint in backend/src/api/routes/tasks.py (create new recurring task template)
- [ ] T069 [P] [US2] Add GET /api/recurring-tasks/{id} endpoint in backend/src/api/routes/tasks.py (get recurring task details)
- [ ] T070 [P] [US2] Add DELETE /api/recurring-tasks/{id} endpoint in backend/src/api/routes/tasks.py (stop recurring task)

**Backend Schemas**

- [ ] T071 [P] [US2] Create RecurringTaskCreate schema in backend/src/schemas.py
- [ ] T072 [P] [US2] Create RecurringTaskResponse schema in backend/src/schemas.py

**Frontend Components**

- [ ] T073 [P] [US2] Create RecurringTaskForm component in frontend/src/components/task/RecurringTaskForm.tsx (form with frequency selector, start date, end date)

**Frontend Pages**

- [ ] T074 [US2] Add recurring tasks section to dashboard in frontend/src/app/dashboard/page.tsx (display recurring task templates and upcoming occurrences)

**Checkpoint**: User Story 2 complete - users can create recurring tasks that auto-generate occurrences

---

## Phase 5: User Story 3 - Intelligent Reminder System (Priority: P2)

**Goal**: Users can set reminders for tasks and receive notifications at the specified time

**Independent Test**: Create task due at 5 PM with reminder at 4 PM, verify notification sent at 4 PM

### Tests for User Story 3

- [ ] T075 [P] [US3] Write integration test for reminder creation in backend/tests/integration/test_reminders.py
- [ ] T076 [P] [US3] Write integration test for reminder scheduling in backend/tests/integration/test_reminder_scheduler.py
- [ ] T077 [P] [US3] Write integration test for reminder sending in backend/tests/integration/test_reminder_sending.py

### Implementation for User Story 3

**Backend Services**

- [ ] T078 [P] [US3] Create reminder service in backend/src/services/reminder_service.py (create, list, send reminders)
- [ ] T079 [US3] Implement reminder scheduler in backend/src/services/reminder_service.py (query unsent reminders where remind_at <= NOW())
- [ ] T080 [US3] Implement in-app notification sending in backend/src/services/reminder_service.py (store notifications in database or send via WebSocket)
- [ ] T081 [US3] Add email notification support (optional) in backend/src/services/reminder_service.py (send email via SMTP or API)

**Backend Kafka Consumer**

- [ ] T082 [P] [US3] Create reminder Kafka consumer in backend/src/services/reminder_consumer.py (poll for due reminders using Dapr cron binding)
- [ ] T083 [US3] Process reminders and mark as sent in backend/src/services/reminder_consumer.py (set sent=true, sent_at=NOW())

**Backend MCP Tools**

- [ ] T084 [P] [US3] Create list_reminders MCP tool in backend/src/mcp_tools/list_reminders.py (list upcoming reminders for user)

**Backend API Routes**

- [ ] T085 [P] [US3] Add POST /api/tasks/{task_id}/reminders endpoint in backend/src/api/routes/tasks.py (create reminder for task)
- [ ] T086 [P] [US3] Add GET /api/tasks/{task_id}/reminders endpoint in backend/src/api/routes/tasks.py (list all reminders for task)
- [ ] T087 [P] [US3] Add GET /api/reminders endpoint in backend/src/api/routes/tasks.py (list all upcoming reminders for user)

**Backend Schemas**

- [ ] T088 [P] [US3] Create ReminderCreate schema in backend/src/schemas.py
- [ ] T089 [P] [US3] Create ReminderResponse schema in backend/src/schemas.py

**Dapr Configuration**

- [ ] T090 [US3] Configure Dapr cron binding for reminder scheduler in infrastructure/docker/dapr/bindings.yaml (schedule: "*/5 * * * *" to check every 5 minutes)

**Checkpoint**: User Story 3 complete - users can set reminders and receive notifications

---

## Phase 6: User Story 4 - Real-Time Task Synchronization (Priority: P3)

**Goal**: Task updates are instantly synchronized across all connected devices without page refresh

**Independent Test**: Open app in two browser windows, complete task in window A, verify it instantly appears complete in window B

### Tests for User Story 4

- [ ] T091 [P] [US4] Write integration test for Kafka real-time publishing in backend/tests/integration/test_realtime.py
- [ ] T092 [P] [US4] Write integration test for WebSocket gateway consuming task updates in backend/tests/integration/test_websocket_gateway.py

### Implementation for User Story 4

**Backend Kafka Publishing**

- [ ] T093 [P] [US4] Publish to task-updates topic in backend/src/services/event_publisher.py (publish all task updates: created, updated, completed, deleted)

**Backend WebSocket Gateway**

- [ ] T094 [P] [US4] Create WebSocket gateway service in backend/src/services/websocket_gateway.py (subscribe to task-updates topic, broadcast to connected clients)
- [ ] T095 [US4] Implement WebSocket connection management in backend/src/services/websocket_gateway.py (track connected clients by user_id)
- [ ] T096 [US4] Add WebSocket endpoint in backend/src/api/routes/chat.py (WebSocket route for real-time updates)

**Frontend Kafka Client**

- [ ] T097 [P] [US4] Create Kafka WebSocket client in frontend/src/lib/kafka-client.ts (connect to WebSocket gateway, receive task updates)
- [ ] T098 [US4] Implement task update handler in frontend/src/lib/kafka-client.ts (update local state when task updates received)

**Frontend Components**

- [ ] T099 [P] [US4] Integrate real-time updates in TaskList component in frontend/src/components/task/TaskList.tsx (auto-update when Kafka message received)
- [ ] T100 [US4] Add connection status indicator in frontend/src/components/chat/ChatWidget.tsx (show WebSocket connection status)

**Checkpoint**: User Story 4 complete - tasks sync in real-time across all devices

---

## Phase 7: User Story 5 - Event-Driven Audit Trail (Priority: P3)

**Goal**: All task operations are logged to an immutable audit trail with complete history

**Independent Test**: Perform various task operations, query audit log, verify all events recorded with correct timestamps and user IDs

### Tests for User Story 5

- [ ] T101 [P] [US5] Write integration test for audit trail creation in backend/tests/integration/test_audit_trail.py
- [ ] T102 [P] [US5] Write integration test for audit trail querying in backend/tests/integration/test_audit_query.py

### Implementation for User Story 5

**Backend Services**

- [ ] T103 [P] [US5] Extend audit logging service in backend/src/services/audit_service.py (log all task operations with before/after state)
- [ ] T104 [US5] Add audit event creation in all MCP tools in backend/src/mcp_tools/ (create TaskEvent after each operation)
- [ ] T105 [US5] Implement event_data JSON structure in backend/src/services/audit_service.py (include before, after, changes arrays)

**Backend API Routes**

- [ ] T106 [P] [US5] Add GET /api/audit/tasks/{task_id} endpoint in backend/src/api/routes/tasks.py (get audit trail for specific task)

**Backend Schemas**

- [ ] T107 [P] [US5] Create TaskEventResponse schema in backend/src/schemas.py

**Checkpoint**: User Story 5 complete - all operations logged to immutable audit trail

---

## Phase 8: User Story 6 - Local Development with Minikube (Priority: P1)

**Goal**: Developers can run full stack locally on Minikube with Dapr and Kafka

**Independent Test**: Run minikube start, apply manifests, verify all services start and app accessible at localhost

### Tests for User Story 6

- [ ] T108 [P] [US6] Write infrastructure validation test in infrastructure/tests/test_minikube.sh (verify all services start)
- [ ] T109 [P] [US6] Write end-to-end test for local deployment in infrastructure/tests/test_local_e2e.sh (create task, verify Kafka event)

### Implementation for User Story 6

**Kubernetes Manifests**

- [ ] T110 [P] [US6] Create namespace manifest in infrastructure/kubernetes/base/namespace.yaml
- [ ] T111 [P] [US6] Create ConfigMap manifest in infrastructure/kubernetes/base/configmaps.yaml (environment variables)
- [ ] T112 [P] [US6] Create Secrets manifest in infrastructure/kubernetes/base/secrets.yaml (placeholder for local development)

**Backend Kubernetes**

- [ ] T113 [P] [US6] Create backend deployment manifest in infrastructure/kubernetes/base/backend/deployment.yaml (include Dapr sidecar annotations)
- [ ] T114 [P] [US6] Create backend service manifest in infrastructure/kubernetes/base/backend/service.yaml
- [ ] T115 [P] [US6] Create backend HPA manifest in infrastructure/kubernetes/base/backend/hpa.yaml (Horizontal Pod Autoscaler)
- [ ] T116 [P] [US6] Create backend PodMonitor manifest in infrastructure/kubernetes/base/backend/podmonitor.yaml (Prometheus monitoring)

**Frontend Kubernetes**

- [ ] T117 [P] [US6] Create frontend deployment manifest in infrastructure/kubernetes/base/frontend/deployment.yaml
- [ ] T118 [P] [US6] Create frontend service manifest in infrastructure/kubernetes/base/frontend/service.yaml
- [ ] T119 [P] [US6] Create frontend HPA manifest in infrastructure/kubernetes/base/frontend/hpa.yaml
- [ ] T120 [P] [US6] Create frontend ingress manifest in infrastructure/kubernetes/base/frontend/ingress.yaml (local ingress for Minikube)

**Kafka Kubernetes**

- [ ] T121 [P] [US6] Create Kafka cluster manifest in infrastructure/kubernetes/base/kafka/kafka-cluster.yaml (Redpanda operator or Strimzi)
- [ ] T122 [P] [US6] Create Kafka topics manifest in infrastructure/kubernetes/base/kafka/kafka-topics.yaml (create task-events, reminders, task-updates topics)

**Dapr Kubernetes Components**

- [ ] T123 [P] [US6] Create Dapr Pub/Sub component in infrastructure/kubernetes/base/dapr/pubsub.yaml (Kafka configuration)
- [ ] T124 [P] [US6] Create Dapr State component in infrastructure/kubernetes/base/dapr/state.yaml (PostgreSQL state store)
- [ ] T125 [P] [US6] Create Dapr Cron Binding component in infrastructure/kubernetes/base/dapr/bindings.yaml (reminder scheduler)
- [ ] T126 [P] [US6] Create Dapr Secrets component in infrastructure/kubernetes/base/dapr/secrets.yaml (Kubernetes secrets)

**Minikube Overlay**

- [ ] T127 [US6] Create Minikube Kustomization in infrastructure/kubernetes/minikube/kustomization.yaml (resource limits for local development)

**Setup Scripts**

- [ ] T128 [US6] Create Minikube setup script in infrastructure/scripts/setup-minikube.sh (start Minikube, install Dapr, deploy all services)
- [ ] T129 [US6] Create Dapr setup script in infrastructure/scripts/setup-dapr.sh (initialize Dapr on Minikube)
- [ ] T130 [US6] Update quickstart.md with Minikube instructions in specs/006-advanced-cloud-deployment/quickstart.md (add local deployment section)

**Checkpoint**: User Story 6 complete - full stack runs on Minikube locally

---

## Phase 9: User Story 7 - Production Deployment on DigitalOcean (Priority: P1)

**Goal**: Deploy production-grade application to DigitalOcean Kubernetes with SSL, HPA, monitoring

**Independent Test**: Deploy to DOKS, access via public URL, verify SSL, test auto-scaling

### Tests for User Story 7

- [ ] T131 [P] [US7] Write production deployment validation in infrastructure/tests/test_production.sh (verify all services healthy)
- [ ] T132 [P] [US7] Write SSL/TLS validation test in infrastructure/tests/test_ssl.sh (verify HTTPS works)

### Implementation for User Story 7

**Helm Chart**

- [ ] T133 [P] [US7] Update Helm Chart.yaml in infrastructure/helm/todo-chatbot/Chart.yaml (add version, appVersion)
- [ ] T134 [P] [US7] Update Helm values.yaml in infrastructure/helm/todo-chatbot/values.yaml (default configuration)
- [ ] T135 [P] [US7] Create values-minikube.yaml in infrastructure/helm/todo-chatbot/values-minikube.yaml (local development overrides)
- [ ] T136 [P] [US7] Create values-production.yaml in infrastructure/helm/todo-chatbot/values-production.yaml (DigitalOcean production settings: HPA, resources, replicas)

**Helm Templates**

- [ ] T137 [P] [US7] Extend backend deployment template in infrastructure/helm/todo-chatbot/templates/backend/deployment.yaml (add Dapr sidecar, resources, probes)
- [ ] T138 [P] [US7] Extend backend HPA template in infrastructure/helm/todo-chatbot/templates/backend/hpa.yaml (Horizontal Pod Autoscaler configuration)
- [ ] T139 [P] [US7] Extend frontend ingress template in infrastructure/helm/todo-chatbot/templates/frontend/ingress.yaml (add TLS/SSL configuration)
- [ ] T140 [P] [US7] Create cert-manager template in infrastructure/helm/todo-chatbot/templates/frontend/cert-manager.yaml (Let's Encrypt SSL)

**Production Secrets**

- [ ] T141 [US7] Create production secrets setup in infrastructure/scripts/setup-secrets.sh (create Kubernetes secrets for DB, JWT, OpenAI, Redpanda)
- [ ] T142 [US7] Add secrets documentation in specs/006-advanced-cloud-deployment/quickstart.md (how to set up production secrets)

**Deployment Scripts**

- [ ] T143 [US7] Create production deployment script in infrastructure/scripts/deploy-production.sh (deploy to DigitalOcean using Helm)
- [ ] T144 [US7] Update quickstart.md with DigitalOcean instructions in specs/006-advanced-cloud-deployment/quickstart.md (add production deployment section)

**Checkpoint**: User Story 7 complete - production deployment on DigitalOcean with SSL

---

## Phase 10: User Story 8 - CI/CD Pipeline (Priority: P2)

**Goal**: Automated testing, building, and deployment on git push

**Independent Test**: Push code change to GitHub, verify pipeline runs tests, builds images, deploys automatically

### Tests for User Story 8

- [ ] T145 [P] [US8] Write CI/CD pipeline test in .github/workflows/test-ci-cd.yml (validate pipeline works)

### Implementation for User Story 8

**GitHub Actions Workflows**

- [ ] T146 [P] [US8] Create test workflow in .github/workflows/test.yml (run pytest for backend, npm test for frontend on PR)
- [ ] T147 [P] [US8] Create build workflow in .github/workflows/build.yml (build Docker images for backend and frontend, push to registry)
- [ ] T148 [P] [US8] Create deploy workflow in .github/workflows/deploy.yml (deploy to DigitalOcean using helm upgrade)
- [ ] T149 [US8] Add workflow triggers in .github/workflows/ (on push to main, on PR, manual trigger)

**CI/CD Configuration**

- [ ] T150 [US8] Configure GitHub Secrets in repository settings (DATABASE_URL, JWT_SECRET, OPENAI_API_KEY, REDPANDA_CREDENTIALS, DIGITALOCEAN_TOKEN, REGISTRY_USERNAME, REGISTRY_PASSWORD)
- [ ] T151 [US8] Add rollout validation in deploy workflow (verify deployment succeeds before marking complete)
- [ ] T152 [US8] Add rollback mechanism in deploy workflow (auto-rollback on failure)

**Documentation**

- [ ] T153 [US8] Document CI/CD pipeline in specs/006-advanced-cloud-deployment/quickstart.md (how to use, troubleshooting)

**Checkpoint**: User Story 8 complete - automated CI/CD pipeline

---

## Phase 11: User Story 9 - Monitoring and Observability (Priority: P2)

**Goal**: Comprehensive monitoring with metrics (Prometheus), logs (Loki), dashboards (Grafana)

**Independent Test**: Access Grafana dashboard, verify metrics displayed, search logs in Loki, trigger alert

### Tests for User Story 9

- [ ] T154 [P] [US9] Write monitoring stack test in infrastructure/tests/test_monitoring.sh (verify Prometheus, Grafana, Loki running)

### Implementation for User Story 9

**Monitoring Stack**

- [ ] T155 [P] [US9] Create Prometheus manifest in infrastructure/kubernetes/base/monitoring/prometheus.yaml (Prometheus deployment)
- [ ] T156 [P] [US9] Create Grafana manifest in infrastructure/kubernetes/base/monitoring/grafana.yaml (Grafana deployment)
- [ ] T157 [P] [US9] Create Loki manifest in infrastructure/kubernetes/base/monitoring/loki.yaml (Loki log aggregation)
- [ ] T158 [P] [US9] Create monitoring Helm chart in infrastructure/helm/monitoring/ (kube-prometheus-stack)

**Backend Metrics**

- [ ] T159 [P] [US9] Add Prometheus metrics endpoint in backend/src/main.py (/metrics endpoint with prometheus-client)
- [ ] T160 [P] [US9] Add HTTP request metrics in backend/src/main.py (track request count, latency, error rate)
- [ ] T161 [P] [US9] Add Kafka metrics in backend/src/services/kafka_producer.py (track publish success/failure, latency)
- [ ] T162 [P] [US9] Add database query metrics in backend/src/db/session.py (track query latency, connection pool usage)

**Grafana Dashboards**

- [ ] T163 [P] [US9] Create application dashboard in infrastructure/monitoring/dashboards/application.json (requests per second, error rate, latency)
- [ ] T164 [P] [US9] Create Kafka dashboard in infrastructure/monitoring/dashboards/kafka.json (message rate, consumer lag)
- [ ] T165 [P] [US9] Create infrastructure dashboard in infrastructure/monitoring/dashboards/infrastructure.json (pod CPU, memory, network)

**Alerting**

- [ ] T166 [US9] Configure Prometheus alerting rules in infrastructure/monitoring/alerts/ (alert on high error rate, pod crashes)
- [ ] T167 [US9] Set up alert notification channels in Grafana (email, Slack - optional)

**Logging**

- [ ] T168 [P] [US9] Add structured logging in backend/src/main.py (JSON logs with timestamp, level, context)
- [ ] T169 [P] [US9] Configure Loki datasource in Grafana (connect Loki to Grafana)

**Documentation**

- [ ] T170 [US9] Document monitoring setup in specs/006-advanced-cloud-deployment/quickstart.md (how to access dashboards, interpret metrics)

**Checkpoint**: User Story 9 complete - full monitoring and observability stack

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T171 [P] Update README.md in project root (add Phase V features, architecture diagram, deployment links)
- [ ] T172 [P] Create API documentation in backend/docs/api.md (document all Phase V endpoints with examples)
- [ ] T173 Add error handling for all Kafka operations in backend/src/services/kafka_producer.py (retry with exponential backoff)
- [ ] T174 Add timeout handling for all external API calls in backend/src/services/ (add timeouts to httpx calls)
- [ ] T175 Add input validation and sanitization for all API endpoints in backend/src/api/routes/ (validate all user inputs)
- [ ] T176 Add rate limiting to API endpoints in backend/src/api/routes/ (prevent abuse)
- [ ] T177 [P] Add unit tests for all new services in backend/tests/unit/ (kafka_producer, reminder_service, recurring_service, audit_service)
- [ ] T178 [P] Add unit tests for all new MCP tools in backend/tests/unit/mcp_tools/ (test all 9 new tools)
- [ ] T179 Run security audit on dependencies (backend and frontend)
- [ ] T180 Performance testing: load test API endpoints with 1000 concurrent users
- [ ] T181 Validate quickstart.md instructions end-to-end (test local and production deployment)
- [ ] T182 Create demo video (90 seconds max) showing all Phase V features
- [ ] T183 Update submission requirements document (add production URLs, demo video link)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-11)**: All depend on Foundational phase completion
  - User Story 1 (P1) BLOCKS User Stories 2, 3 (they depend on advanced task fields)
  - User Stories 2, 3, 4, 5 can proceed in parallel after US1
  - User Stories 6, 7 (deployment) are independent of feature stories (can proceed in parallel)
  - User Story 8 (CI/CD) depends on US7 (production deployment)
  - User Story 9 (monitoring) depends on US7 (production deployment)
- **Polish (Phase 12)**: Depends on all desired user stories being complete

### User Story Dependencies

**Critical Path**:
1. **Setup (Phase 1)** → Foundational (Phase 2) → **User Story 1 (Advanced Tasks)** → User Story 2 (Recurring) / User Story 3 (Reminders)

**Parallel Tracks**:
- **Track A (Features)**: US1 → US2, US3, US4, US5 (can parallelize US2-US5 after US1)
- **Track B (Infrastructure)**: US6 (Local) / US7 (Production) (can proceed in parallel with features)
- **Track C (Operations)**: US7 → US8 (CI/CD) / US9 (Monitoring) (sequential after US7)

### Within Each User Story

- Integration tests MUST be written and FAIL before implementation (if TDD approach)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Maximum Parallelization** (with sufficient team members):
- After Foundational (Phase 2) completes:
  - **Team A**: User Story 1 (Advanced Tasks)
  - **Team B**: User Story 6 (Local Minikube)
  - **Team C**: User Story 7 (Production DOKS)
- After US1 completes:
  - **Team A-1**: User Story 2 (Recurring Tasks)
  - **Team A-2**: User Story 3 (Reminders)
  - **Team A-3**: User Story 4 (Real-Time Sync)
  - **Team A-4**: User Story 5 (Audit Trail)
- After US7 completes:
  - **Team B-1**: User Story 8 (CI/CD)
  - **Team B-2**: User Story 9 (Monitoring)

---

## Parallel Example: User Story 1

```bash
# Launch all integration tests for User Story 1 together (in parallel):
Task T021: "Write integration test for task creation with advanced fields"
Task T022: "Write integration test for task filtering by priority"
Task T023: "Write integration test for task sorting by due date"
Task T024: "Write integration test for task full-text search"

# After tests fail (TDD), launch all MCP tools for User Story 1 together:
Task T025: "Extend add_task MCP tool"
Task T026: "Extend update_task MCP tool"
Task T027: "Extend complete_task MCP tool"
Task T028: "Extend delete_task MCP tool"
Task T029: "Extend list_tasks MCP tool"
Task T030: "Create set_task_priority MCP tool"
Task T031: "Create set_task_due_date MCP tool"
Task T032: "Create add_task_tags MCP tool"
Task T033: "Create search_tasks MCP tool"
Task T034: "Create filter_tasks MCP tool"
Task T035: "Create sort_tasks MCP tool"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T020) - **CRITICAL**
3. Complete Phase 3: User Story 1 (T021-T053)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

**MVP Deliverable**: Users can create advanced tasks with due dates, priorities, tags, and filter/sort/search them

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready (T001-T020)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!) (T021-T053)
3. Add User Stories 2, 3 → Test independently → Deploy/Demo (T054-T090)
4. Add User Stories 4, 5 → Test independently → Deploy/Demo (T091-T107)
5. Add Deployment Stories 6, 7 → Deploy locally and to production (T108-T144)
6. Add Operations Stories 8, 9 → Full production stack (T145-T170)
7. Polish → Complete Phase V (T171-T183)

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 3-5 developers:

**Sprint 1 (Foundation)**: All developers work together on Setup + Foundational (T001-T020)

**Sprint 2 (Core Features + Infrastructure)**:
- Developer A: User Story 1 (Advanced Tasks) (T021-T053)
- Developer B: User Story 6 (Local Minikube) (T108-T130)
- Developer C: User Story 7 (Production DOKS) (T131-T144)

**Sprint 3 (Advanced Features)**:
- Developer A-1: User Story 2 (Recurring Tasks) (T054-T074)
- Developer A-2: User Story 3 (Reminders) (T075-T090)
- Developer B: User Story 4 (Real-Time Sync) (T091-T100)
- Developer C: User Story 5 (Audit Trail) (T101-T107)

**Sprint 4 (Operations)**:
- Developer B: User Story 8 (CI/CD) (T145-T153)
- Developer C: User Story 9 (Monitoring) (T154-T170)

**Sprint 5 (Polish)**: All developers contribute to polish (T171-T183)

---

## Summary

**Total Tasks**: 183 tasks
**Task Count per User Story**:
- Setup: 5 tasks
- Foundational: 15 tasks
- US1 (Advanced Tasks): 33 tasks
- US2 (Recurring): 21 tasks
- US3 (Reminders): 16 tasks
- US4 (Real-Time Sync): 10 tasks
- US5 (Audit Trail): 7 tasks
- US6 (Local Minikube): 23 tasks
- US7 (Production DOKS): 14 tasks
- US8 (CI/CD): 9 tasks
- US9 (Monitoring): 16 tasks
- Polish: 13 tasks

**Parallel Opportunities Identified**: 91 tasks marked [P] can run in parallel within their phases

**Independent Test Criteria**: Each user story has clearly defined independent test criteria

**MVP Scope**: User Story 1 (Advanced Task Management) - 33 tasks - delivers immediate organizational value

**Format Validation**: ✅ ALL tasks follow the checklist format with checkbox, ID, labels, file paths

---

**END OF TASKS**
