# Feature Specification: Advanced Cloud Deployment

**Feature Branch**: `006-advanced-cloud-deployment`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "Phase V: Advanced Cloud Deployment - Implement event-driven architecture with Kafka, Dapr integration, advanced task features (recurring tasks, due dates, reminders, priorities, tags), Minikube local deployment, and production deployment on DigitalOcean with CI/CD and monitoring"

---

## Constitution Alignment

This specification MUST comply with all principles in `.specify/memory/constitution.md`:

**Core Principles Applied**:
- Stateless Architecture with Database-Backed Persistence
- Tool-Driven AI Behavior
- Task Operation Correctness
- Conversational State Persistence
- Natural Language Understanding
- Error Handling and User Safety
- Agent Intent Routing
- Data Integrity and Security
- Spec-Driven Development

**Technology Constraints**:
- Frontend: OpenAI ChatKit, Next.js 16+, TypeScript, Tailwind CSS
- Backend: Python FastAPI, SQLModel, Neon Serverless PostgreSQL
- AI: OpenAI Agents SDK, Official MCP SDK
- Auth: Better Auth
- **NEW for Phase V**:
  - Event Streaming: Kafka (Redpanda Cloud for production, Redpanda Docker for local)
  - Distributed Runtime: Dapr (Pub/Sub, State, Bindings, Secrets, Service Invocation)
  - Container Orchestration: Kubernetes (Minikube for local, DigitalOcean DOKS for production)
  - CI/CD: GitHub Actions
  - Monitoring: Prometheus, Grafana, Loki

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Advanced Task Management (Priority: P1)

Users can create and manage tasks with advanced attributes including due dates, priority levels, and tags. Users can set a task as "high priority" with a due date of "tomorrow" and tag it as "work", and the system correctly stores and retrieves this information.

**Why this priority**: This is the foundation for all advanced features. Without the ability to store due dates, priorities, and tags, reminder and recurring task features cannot function. This delivers immediate value by allowing users to organize and prioritize their tasks more effectively.

**Independent Test**: Can be fully tested by creating tasks with various combinations of due dates, priorities, and tags, then verifying they persist correctly and can be filtered/sorted. Delivers immediate organizational value to users.

**Acceptance Scenarios**:

1. **Given** a user is logged in, **When** they create a task with due date "2026-02-15", priority "high", and tags ["work", "urgent"], **Then** the task is saved with all attributes and retrievable via list and filter operations
2. **Given** a user has tasks with different priorities, **When** they filter tasks by "high priority", **Then** only high-priority tasks are displayed
3. **Given** a user has tasks with various due dates, **When** they sort tasks by due date, **Then** tasks are ordered from nearest to furthest due date
4. **Given** a user has tagged tasks, **When** they filter by tag "work", **Then** only work-tagged tasks are displayed
5. **Given** a user is searching, **When** they search for "meeting", **Then** all tasks containing "meeting" in title or description are returned

---

### User Story 2 - Recurring Task Automation (Priority: P2)

Users can create tasks that repeat on a schedule (daily, weekly, monthly). When a recurring task is marked complete, the system automatically creates the next occurrence based on the recurrence pattern.

**Why this priority**: Recurring tasks are a critical productivity feature for repeated activities (daily standups, weekly reports, monthly reviews). This delivers significant automation value by eliminating manual task recreation.

**Independent Test**: Can be fully tested by creating a recurring task (e.g., "Daily standup" recurring daily), marking it complete, and verifying the next day's task is automatically created with correct due date. Delivers hands-off recurring task management.

**Acceptance Scenarios**:

1. **Given** a user creates a task "Weekly team meeting" recurring weekly, **When** they mark it complete, **Then** a new task is automatically created for the same time next week
2. **Given** a user creates a daily recurring task "Check emails", **When** they complete it on Monday, **Then** the next occurrence is scheduled for Tuesday
3. **Given** a user creates a monthly recurring task "Pay rent", **When** they complete it on January 1st, **Then** the next occurrence is scheduled for February 1st
4. **Given** a user has a recurring task, **When** they delete the current occurrence, **Then** the next occurrence is still created according to the schedule
5. **Given** a user wants to stop a recurring task, **When** they delete the parent recurring task, **Then** no future occurrences are created

---

### User Story 3 - Intelligent Reminder System (Priority: P2)

Users can set reminders for tasks with due dates. The system sends notifications (in-app or email) at the specified reminder time, ensuring users never miss important deadlines.

**Why this priority**: Reminders prevent missed deadlines and improve task completion rates. This delivers proactive task management value by notifying users at the right time.

**Independent Test**: Can be fully tested by creating a task with due date and reminder time, waiting for the reminder time, and verifying the notification is sent and displayed. Delivers assurance that important tasks won't be forgotten.

**Acceptance Scenarios**:

1. **Given** a user creates a task due at 5 PM with a reminder at 4 PM, **When** the reminder time is reached, **Then** a notification is sent to the user
2. **Given** a user has multiple tasks with reminders, **When** reminder times are reached, **Then** all reminders are sent in order of their scheduled time
3. **Given** a user has already completed a task, **When** the reminder time is reached, **Then** no reminder is sent for the completed task
4. **Given** a user wants to be reminded 1 hour before a task, **When** they set reminder to "1 hour before due", **Then** the reminder is triggered 1 hour before the due date
5. **Given** a reminder fails to send (network issue), **When** the system retries, **Then** the reminder is eventually delivered with a delay notification

---

### User Story 4 - Real-Time Task Synchronization (Priority: P3)

When a user updates a task on one device (e.g., marks complete on mobile), all other connected devices (web, tablet) immediately reflect the change without requiring a page refresh.

**Why this priority**: Real-time sync provides a modern, polished user experience. While not critical for basic functionality, it significantly enhances usability for users with multiple devices.

**Independent Test**: Can be fully tested by opening the application in two browser windows, completing a task in one window, and verifying the change instantly appears in the other window. Delivers seamless multi-device experience.

**Acceptance Scenarios**:

1. **Given** a user has the dashboard open on two devices, **When** they create a task on device A, **Then** the task immediately appears on device B without refresh
2. **Given** a user is viewing the task list on multiple devices, **When** they complete a task on one device, **Then** the task is marked complete on all other devices instantly
3. **Given** a user edits a task title on one device, **When** they save the change, **Then** all connected devices show the updated title immediately
4. **Given** a user deletes a task on one device, **When** the deletion completes, **Then** the task disappears from all other connected devices
5. **Given** network connectivity is temporarily lost, **When** connectivity is restored, **Then** all pending changes are synchronized and devices show consistent state

---

### User Story 5 - Event-Driven Audit Trail (Priority: P3)

All task operations (create, update, complete, delete) are automatically logged to an audit trail. Users and administrators can view the complete history of changes for any task, including who made the change and when.

**Why this priority**: Audit trails provide data integrity, accountability, and debugging capabilities. While not visible to end users, it's critical for production operations and compliance.

**Independent Test**: Can be fully tested by performing various task operations, then querying the audit log to verify all events are recorded with correct timestamps, user IDs, and event types. Delivers complete traceability and data integrity assurance.

**Acceptance Scenarios**:

1. **Given** a user creates a task, **When** the operation completes, **Then** an audit event is logged with event_type="created", task_id, user_id, and timestamp
2. **Given** a user updates a task title, **When** the update completes, **Then** an audit event is logged with event_type="updated", task_id, old_value, new_value, and user_id
3. **Given** a user completes a task, **When** the completion completes, **Then** an audit event is logged with event_type="completed", task_id, and user_id
4. **Given** a user deletes a task, **When** the deletion completes, **Then** an audit event is logged with event_type="deleted", task_id, deleted_task_data, and user_id
5. **Given** a user has performed 10 operations, **When** they query the audit trail, **Then** all 10 events are returned in chronological order with complete details

---

### User Story 6 - Local Development with Minikube (Priority: P1)

Developers can run the entire application stack (frontend, backend, database, Kafka, Dapr) locally on Minikube using Docker and Kubernetes. This enables developers to test the complete event-driven architecture before deploying to production.

**Why this priority**: Local development environment is essential for development velocity and testing. Without this, developers must rely on cloud deployments for every test, which is slow and expensive.

**Independent Test**: Can be fully tested by running `minikube start`, applying Kubernetes manifests, and verifying all services start correctly and the application is accessible at `localhost`. Delivers complete local development capability.

**Acceptance Scenarios**:

1. **Given** a developer has Docker and Minikube installed, **When** they run the setup script, **Then** all services (frontend, backend, database, Kafka, Dapr) start without errors
2. **Given** the application is running locally, **When** a developer accesses `localhost`, **Then** the frontend loads and connects to the local backend
3. **Given** a developer creates a task locally, **When** the operation completes, **Then** the task is stored in the local database and an event is published to local Kafka
4. **Given** a developer makes code changes, **When** they rebuild the Docker containers, **Then** changes are reflected in the local Minikube deployment
5. **Given** a developer stops Minikube, **When** they restart it later, **Then** all data persists and the application resumes from the previous state

---

### User Story 7 - Production Deployment on DigitalOcean (Priority: P1)

The application can be deployed to DigitalOcean Kubernetes (DOKS) using production-grade Helm charts. The deployment includes auto-scaling, SSL/TLS, monitoring, logging, and all Phase V features enabled.

**Why this priority**: Production deployment capability is the ultimate goal of Phase V. This delivers a live, scalable application that real users can access.

**Independent Test**: Can be fully tested by deploying to a DigitalOcean Kubernetes cluster, accessing the application via the public URL, and verifying all features work correctly. Delivers a production-ready, publicly accessible application.

**Acceptance Scenarios**:

1. **Given** a developer has a DigitalOcean Kubernetes cluster, **When** they apply the production Helm charts, **Then** all services deploy successfully and pass health checks
2. **Given** the application is deployed, **When** users access the production URL, **Then** the application loads via HTTPS with valid SSL certificates
3. **Given** the production deployment is running, **When** traffic increases, **Then** the Horizontal Pod Autoscaler scales up pods to handle the load
4. **Given** a pod crashes in production, **When** the crash occurs, **Then** Kubernetes automatically restarts the pod and the application remains available
5. **Given** the production deployment is active, **When** developers push code changes, **Then** the CI/CD pipeline automatically builds, tests, and deploys the changes to production

---

### User Story 8 - Continuous Integration and Deployment (Priority: P2)

When developers push code to GitHub, the CI/CD pipeline automatically runs tests, builds Docker images, and deploys to production (or staging) if tests pass. This ensures code quality and enables rapid, reliable deployments.

**Why this priority**: CI/CD automation is essential for team productivity and deployment reliability. Manual deployments are error-prone and time-consuming.

**Independent Test**: Can be fully tested by pushing a code change to GitHub and verifying the pipeline runs tests, builds images, and deploys automatically. Delivers hands-off deployment automation.

**Acceptance Scenarios**:

1. **Given** a developer pushes code to the main branch, **When** the push completes, **Then** GitHub Actions workflow triggers automatically
2. **Given** the CI/CD pipeline is running, **When** tests fail, **Then** the pipeline stops and does not deploy to production
3. **Given** all tests pass, **When** the build phase completes, **Then** Docker images are built and pushed to the container registry
4. **Given** Docker images are built successfully, **When** the deploy phase runs, **Then** the new version is deployed to Kubernetes and rolls out gradually
5. **Given** a deployment fails, **When** the failure is detected, **Then** the pipeline automatically rolls back to the previous stable version

---

### User Story 9 - Monitoring and Observability (Priority: P2)

The application has comprehensive monitoring including metrics (Prometheus), logs (Loki), and dashboards (Grafana). Operators can view system health, performance metrics, error rates, and logs in real-time.

**Why this priority**: Monitoring is essential for production operations. Without observability, operators cannot detect or diagnose issues in production.

**Independent Test**: Can be fully tested by accessing the Grafana dashboard and verifying metrics are displayed, logs are searchable, and alerts are triggered for error conditions. Delivers complete production visibility.

**Acceptance Scenarios**:

1. **Given** the application is deployed, **When** operators access Grafana, **Then** dashboards display metrics for requests per second, error rates, latency, and resource usage
2. **Given** an error occurs in the application, **When** operators search logs in Loki, **Then** they can find the error with stack trace and context
3. **Given** system metrics exceed thresholds (e.g., error rate > 5%), **When** the threshold is crossed, **Then** an alert is sent to operators via configured notification channels
4. **Given** operators investigate a performance issue, **When** they view the tracing data, **Then** they can identify the slow service or database query causing the issue
5. **Given** the system is healthy, **When** operators view the dashboards, **Then** all indicators show green/healthy status

---

### Edge Cases

- **Time Zone Handling**: How does the system handle tasks with due dates when users are in different time zones? System MUST store all datetimes in UTC and display in user's local timezone.
- **Recurring Task End Conditions**: What happens when a recurring task has an end date that is reached? System MUST stop creating new occurrences and mark the recurring task as completed.
- **Kafka Delivery Failures**: What happens if Kafka is down when a task event is published? System MUST retry event publishing with exponential backoff and log failures.
- **Reminder Overflow**: What happens if a user has 100 reminders scheduled for the same time? System MUST process reminders in a queue without crashing and optionally batch notifications.
- **Database Migration Rollback**: What happens if a database migration fails in production? System MUST support rollback to previous schema version and provide clear error messages.
- **Dapr Sidecar Failure**: What happens if the Dapr sidecar crashes but the application pod is still running? Kubernetes MUST detect the sidecar failure and restart the pod.
- **Concurrent Task Updates**: What happens if two users try to update the same task simultaneously? System MUST use optimistic locking or database transactions to prevent last-write-wins conflicts.
- **Large Audit Trail**: What happens if the audit trail grows to millions of events? System MUST support pagination and optional archival of old events.
- **Minikube Resource Limits**: What happens if a developer's laptop doesn't have enough resources for Minikube? System MUST provide clear error messages and minimum resource requirements.
- **DigitalOcean Cluster Upgrade**: What happens when DigitalOcean upgrades the Kubernetes cluster control plane? System MUST use Helm charts that are compatible with multiple K8s versions and support rolling upgrades.

## Requirements *(mandatory)*

### Functional Requirements

#### Advanced Task Features
- **FR-001**: System MUST allow users to set due dates on tasks with timezone support (store in UTC, display in user timezone)
- **FR-002**: System MUST support task priority levels: LOW, MEDIUM, HIGH (default: MEDIUM)
- **FR-003**: System MUST allow users to add multiple tags to any task (tags are free-form text strings)
- **FR-004**: System MUST allow users to filter tasks by priority level, tags, due date range, and completion status
- **FR-005**: System MUST allow users to sort tasks by due date, priority, creation date, and completion date
- **FR-006**: System MUST support full-text search across task titles and descriptions

#### Recurring Tasks
- **FR-007**: System MUST allow users to create recurring tasks with frequency: DAILY, WEEKLY, MONTHLY
- **FR-008**: System MUST automatically create the next occurrence when a recurring task is marked complete
- **FR-009**: System MUST calculate the next occurrence date based on the frequency pattern (e.g., weekly = same day next week)
- **FR-010**: System MUST support optional end dates for recurring tasks (no new occurrences after end date)
- **FR-011**: System MUST allow users to stop a recurring task (delete parent recurring task, no future occurrences)

#### Reminders
- **FR-012**: System MUST allow users to set reminder times for tasks with due dates
- **FR-013**: System MUST send notifications at the specified reminder time (in-app notification, email optional)
- **FR-014**: System MUST NOT send reminders for tasks that are already completed
- **FR-015**: System MUST support relative reminders (e.g., "1 hour before", "1 day before")
- **FR-016**: System MUST retry failed reminder notifications with exponential backoff

#### Event-Driven Architecture
- **FR-017**: System MUST publish events to Kafka for all task operations (created, updated, completed, deleted)
- **FR-018**: System MUST consume task events to trigger reminder notifications
- **FR-019**: System MUST consume task events to create recurring task occurrences
- **FR-020**: System MUST maintain an audit trail by consuming and storing all task events
- **FR-021**: System MUST broadcast task updates to connected clients via Kafka for real-time sync

#### Kafka Topics
- **FR-022**: System MUST create Kafka topic "task-events" for all task CRUD operations
- **FR-023**: System MUST create Kafka topic "reminders" for scheduled reminder notifications
- **FR-024**: System MUST create Kafka topic "task-updates" for real-time client synchronization
- **FR-025**: System MUST configure Kafka topics with appropriate retention and replication settings

#### Dapr Integration
- **FR-026**: System MUST use Dapr Pub/Sub component for Kafka abstraction (no direct Kafka client code)
- **FR-027**: System MUST use Dapr State component for conversation state caching (optional, DB is source of truth)
- **FR-028**: System MUST use Dapr Service Invocation for frontend-to-backend communication
- **FR-029**: System MUST use Dapr Cron Binding component to trigger periodic reminder checks
- **FR-030**: System MUST use Dapr Secrets component to manage sensitive configuration (API keys, DB credentials)

#### Local Development
- **FR-031**: System MUST provide a Docker Compose file for local development (frontend, backend, database, Kafka)
- **FR-032**: System MUST provide Minikube setup scripts to deploy the full stack locally
- **FR-033**: System MUST include local development documentation with step-by-step instructions
- **FR-034**: System MUST support hot-reloading during local development (optional but recommended)

#### Production Deployment
- **FR-035**: System MUST provide production Helm charts for DigitalOcean Kubernetes deployment
- **FR-036**: System MUST configure Horizontal Pod Autoscaler for frontend and backend pods
- **FR-037**: System MUST configure SSL/TLS certificates using cert-manager or DigitalOcean Load Balancer
- **FR-038**: System MUST support multiple deployment environments (dev, staging, production)
- **FR-039**: System MUST include production deployment documentation

#### CI/CD Pipeline
- **FR-040**: System MUST provide GitHub Actions workflow for automated testing
- **FR-041**: System MUST provide GitHub Actions workflow for automated Docker image building
- **FR-042**: System MUST provide GitHub Actions workflow for automated deployment to Kubernetes
- **FR-043**: CI/CD pipeline MUST run database migrations automatically during deployment
- **FR-044**: CI/CD pipeline MUST support rollback to previous version if deployment fails

#### Monitoring and Logging
- **FR-045**: System MUST expose Prometheus metrics for HTTP requests, error rates, latency, and resource usage
- **FR-046**: System MUST send structured logs to Loki (or stdout for log aggregation)
- **FR-047**: System MUST provide Grafana dashboards for monitoring application health
- **FR-048**: System MUST configure alerts for critical conditions (high error rate, pod crashes, database connection failures)
- **FR-049**: System MUST include health check endpoints `/health` and `/ready` for Kubernetes probes

#### MCP Tools Enhancements
- **FR-050**: System MUST provide MCP tool `set_task_priority` to update task priority
- **FR-051**: System MUST provide MCP tool `set_task_due_date` to set task due date
- **FR-052**: System MUST provide MCP tool `add_task_tags` to add tags to a task
- **FR-053**: System MUST provide MCP tool `search_tasks` to search tasks by text
- **FR-054**: System MUST provide MCP tool `filter_tasks` to filter by priority, tags, due date
- **FR-055**: System MUST provide MCP tool `sort_tasks` to sort tasks by various fields
- **FR-056**: System MUST provide MCP tool `create_recurring_task` to create recurring tasks
- **FR-057**: System MUST provide MCP tool `list_reminders` to view upcoming reminders
- **FR-058**: All existing MCP tools MUST publish events to Kafka after successful operations
- **FR-059**: AI agent MUST be trained to understand advanced task queries ("show me high priority work tasks due this week")

#### Database Schema
- **FR-060**: System MUST extend Task model with fields: due_date, priority, tags (JSON), recurring, frequency, end_date, next_occurrence, reminder_enabled, reminder_time
- **FR-061**: System MUST create TaskEvent model for audit trail (id, event_type, task_id, user_id, timestamp, event_data)
- **FR-062**: System MUST create Reminder model (id, task_id, remind_at, sent, created_at)
- **FR-063**: System MUST create database indexes on due_date, priority, and user_id for performance
- **FR-064**: System MUST provide Alembic migration scripts for all schema changes

### Key Entities

#### Task (Extended)
- **What it represents**: A todo item with advanced scheduling and categorization capabilities
- **Key Attributes**:
  - Basic: title, description, completed (inherited from Phase III)
  - Scheduling: due_date (datetime with timezone), priority (enum: LOW/MEDIUM/HIGH)
  - Categorization: tags (array of strings)
  - Recurrence: recurring (boolean), frequency (enum: DAILY/WEEKLY/MONTHLY), end_date (optional), next_occurrence (datetime)
  - Reminders: reminder_enabled (boolean), reminder_time (datetime)

#### TaskEvent (Audit Trail)
- **What it represents**: A record of every task operation for auditing and debugging
- **Key Attributes**:
  - event_type (enum: created/updated/completed/deleted)
  - task_id (foreign key to Task)
  - user_id (foreign key to User)
  - timestamp (when event occurred)
  - event_data (JSON: before/after state, changes made)

#### Reminder
- **What it represents**: A scheduled notification for a task with a due date
- **Key Attributes**:
  - task_id (foreign key to Task)
  - remind_at (when to send reminder)
  - sent (boolean: whether reminder was sent)
  - created_at (when reminder was created)

#### RecurringTask (Parent)
- **What it represents**: A template for recurring tasks that generates occurrences
- **Key Attributes**:
  - title, description (inherited from Task)
  - frequency (enum: DAILY/WEEKLY/MONTHLY)
  - start_date (first occurrence)
  - end_date (optional: last occurrence)
  - next_occurrence (calculated date of next task)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create tasks with advanced attributes (due date, priority, tags) in under 10 seconds via natural language
- **SC-002**: System can handle 10,000 concurrent tasks with advanced filters without performance degradation (filter response time < 500ms)
- **SC-003**: Recurring tasks automatically create next occurrence within 5 seconds after completion
- **SC-004**: 95% of reminders are sent within 1 minute of the scheduled reminder time
- **SC-005**: Real-time task synchronization across devices occurs within 2 seconds of any change
- **SC-006**: Kafka event publishing has 99.9% success rate (failed events are retried and eventually delivered)
- **SC-007**: Audit trail captures 100% of task operations with complete data (before/after state)
- **SC-008**: Local Minikube deployment can be set up by a new developer in under 30 minutes following documentation
- **SC-009**: Production deployment on DigitalOcean passes 100% of health checks and handles 1,000 requests per second
- **SC-010**: CI/CD pipeline completes full test, build, and deploy cycle in under 15 minutes
- **SC-011**: Monitoring dashboards display metrics with 99% uptime and alert operators within 1 minute of critical failures
- **SC-012**: Developers can deploy new features to production with a single git push (zero manual steps)
- **SC-013**: System achieves 99.9% uptime in production (excluding planned maintenance)
- **SC-014**: 90% of users successfully use advanced task features (recurring tasks, reminders, priorities) on first attempt without documentation
- **SC-015**: Production deployment cost on DigitalOcean is under $100/month for 1,000 active users

---

## Dependencies and Assumptions

### Dependencies
- **External Services**:
  - Neon Serverless PostgreSQL (database) - already configured from Phase III
  - Redpanda Cloud (Kafka) - free tier for hackathon, requires account setup
  - DigitalOcean Kubernetes (DOKS) - $200 free credit for new accounts
  - GitHub Actions (CI/CD) - free for public repositories
  - Docker Hub or DigitalOcean Container Registry (image storage)

- **Existing Features**:
  - Phase III basic task CRUD must be fully functional
  - Phase IV conversation flow and MCP tools must be working
  - Better Auth authentication must be configured

### Assumptions
- Developers have Docker and Minikube installed locally for development
- Production deployment will use DigitalOcean Kubernetes cluster (minimum 2 nodes, 4GB RAM each)
- Kafka cluster will use Redpanda Cloud free tier (3 topics, 1 partition each)
- Monitoring stack (Prometheus, Grafana, Loki) will run in the same Kubernetes cluster
- CI/CD pipeline will deploy to production after tests pass (manual approval optional)
- SSL/TLS certificates will be managed by DigitalOcean Load Balancer or cert-manager
- Application will be deployed in a single Kubernetes namespace (e.g., "todo-app")
- Database migrations will be run automatically during deployment via init containers or jobs
- All services (frontend, backend) will run as non-root users in containers for security
- Sensitive credentials (API keys, DB passwords) will be stored in Kubernetes Secrets and accessed via Dapr

---

## Out of Scope *(optional but recommended)*

The following features are explicitly OUT OF SCOPE for Phase V:

- **Mobile Applications**: Native iOS or Android apps (web app must work on mobile browsers)
- **Advanced Collaboration Features**: Task sharing between users, comments, mentions
- **File Attachments**: Uploading and attaching files to tasks
- **Task Dependencies**: Tasks that block other tasks (dependencies)
- **Calendar Integration**: Sync with Google Calendar, Outlook, etc.
- **Third-party Integrations**: Slack notifications, Zapier, IFTTT
- **Advanced Analytics**: Reports, charts, productivity insights
- **Multi-tenancy**: Separate workspaces or organizations
- **Advanced Recurrence Patterns**: Complex rules (e.g., "first Monday of every month", "every 2 weeks")
- **SMS/Phone Reminders**: Reminders via SMS or voice calls (email only)
- **WebSocket-based Real-time Features**: Direct WebSocket connections (using Kafka-based approach instead)
- **Custom Alert Rules**: User-defined alert thresholds and rules
- **Advanced Search**: Natural language queries, faceted search
- **Batch Operations**: Bulk delete, bulk update, bulk complete
- **Task Templates**: Pre-defined task templates for common workflows
- **Time Tracking**: Tracking time spent on tasks
- **Subtasks**: Nested task hierarchies
- **Kanban Board**: Drag-and-drop board view of tasks

These features may be considered for future phases (Phase VI+) but are not required for Phase V completion.

---

**END OF SPECIFICATION**
