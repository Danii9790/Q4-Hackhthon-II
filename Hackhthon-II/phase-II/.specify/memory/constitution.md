<!--
========================================================================
SYNC IMPACT REPORT
========================================================================
Version Change: INITIAL → 1.0.0
Rationale: Initial constitution ratification for Hackathon II Phase II Todo Full-Stack Web Application

Modified Principles: N/A (initial version)

Added Sections:
- Core Principles (6 principles)
- Key Standards (6 standard categories)
- Constraints (5 constraint categories)
- Success Criteria (5 success dimensions)

Removed Sections: N/A (initial version)

Templates Requiring Updates:
✅ .specify/templates/plan-template.md - Constitution Check section compatible
✅ .specify/templates/spec-template.md - Requirements section compatible
✅ .specify/templates/tasks-template.md - Task organization compatible

Follow-up TODOs: None
========================================================================
-->

# Hackathon II – Phase II Constitution
**Todo Full-Stack Web Application (Spec-Driven Implementation)**

## Core Principles

### I. Specification Fidelity
All implementation MUST strictly adhere to the authoritative specifications in `/specs`. No feature MAY be added, modified, or omitted without updating the relevant spec first.

**Rationale**: Specifications are the source of truth. Implementation exists to realize the spec—not reinterpret it. This ensures predictability, testability, and alignment between requirements and delivered functionality.

### II. Security by Design
Authentication, authorization, and data isolation are MANDATORY at every layer. User data MUST NEVER be accessible outside its ownership boundary.

**Rationale**: Security cannot be bolted on retrospectively. Every request must enforce user identity and ownership. Cross-user data access is strictly prohibited to protect user privacy and prevent data leakage.

### III. Determinism & Correctness
System behavior MUST be predictable, testable, and logically consistent. API responses, database mutations, and UI state MUST be deterministic given the same inputs.

**Rationale**: Non-deterministic systems are impossible to test, debug, or reason about. Determinism ensures that identical inputs produce identical outputs, enabling reliable testing and predictable user experiences.

### IV. Simplicity & Maintainability
FAVOR clear, readable, and modular code over cleverness. Every component SHOULD be easy to reason about, test, and extend.

**Rationale**: Complex code breeds bugs and impedes future development. Simplicity reduces cognitive load, accelerates onboarding, and lowers maintenance costs over the project lifecycle.

### V. Reusability & Separation of Concerns
Business logic, data access, API layers, and UI components MUST be cleanly separated and reusable.

**Rationale**: Tight coupling between layers creates fragile systems. Clean separation enables independent testing, parallel development, and the ability to replace or upgrade individual components without cascading changes.

### VI. Spec-Driven Development
Specifications are the source of truth. Implementation exists to realize the spec—not reinterpret it.

**Rationale**: This principle reinforces Specification Fidelity and makes explicit that all development flows from documented requirements. Specs drive implementation, not the reverse.

## Key Standards

### Spec Compliance
- Every implemented feature MUST map to a documented requirement in `/specs`.
- Any deviation REQUIRES an explicit spec update before code changes.

**Rationale**: Traceability from code to requirements ensures nothing is built arbitrarily and all features serve documented needs.

### Authentication & Authorization
- All protected routes REQUIRE valid JWT authentication.
- Every request MUST enforce user identity and ownership.
- Cross-user data access is STRICTLY PROHIBITED.

**Rationale**: JWT-based authentication provides stateless, scalable security. Ownership scoping ensures users cannot access data belonging to other users.

### API Contract
- RESTful conventions MUST be followed.
- All endpoints MUST return appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 500).
- Request/response schemas MUST be validated.

**Rationale**: Consistent API contracts enable reliable client integration, clear error communication, and predictable behavior across all endpoints.

### Database Integrity
- Schema MUST follow defined relationships and constraints.
- Foreign keys, indexes, and normalization rules MUST be respected.
- No orphaned records or inconsistent states are permitted.

**Rationale**: Data integrity is foundational. Violating schema constraints produces corrupted data that cascades into application failures.

### Configuration & Secrets
- No secrets, tokens, or credentials MAY be hard-coded.
- All sensitive values MUST be provided via environment variables.

**Rationale**: Hard-coded secrets in source code are exposed in version control and cannot be rotated. Environment variables enable secure secret management and deployment flexibility.

### Error Handling
- Failures MUST be explicit, informative, and secure.
- No internal implementation details MAY be exposed to clients.

**Rationale**: Errors should guide users toward resolution without revealing system internals that could aid attackers. Stack traces and debug information belong in logs, not API responses.

## Constraints

### Frontend
- Framework: Next.js (App Router)
- Language: TypeScript
- Styling: Tailwind CSS
- Data exchange: JSON only

**Rationale**: Next.js App Router provides modern React features with server components. TypeScript ensures type safety. Tailwind CSS enables rapid styling development. JSON simplifies data serialization.

### Backend
- Framework: Python FastAPI
- ORM: SQLModel
- Architecture: RESTful API

**Rationale**: FastAPI provides high-performance async APIs with automatic validation. SQLModel offers intuitive ORM capabilities on top of Pydantic. RESTful architecture ensures predictable, standards-compliant endpoints.

### Database
- Platform: Neon Serverless PostgreSQL
- Persistence: Required for all task data

**Rationale**: Neon provides serverless PostgreSQL with automatic scaling and zero-downtime migrations. All task data must persist to ensure data durability and user data continuity.

### Authentication
- Provider: Better Auth
- Mechanism: JWT-based authorization
- Header: `Authorization: Bearer <token>` required on all protected endpoints

**Rationale**: Better Auth integrates seamlessly with Next.js and provides JWT token management. The Bearer token header follows RFC 6750 standards for authorization headers.

### Access Control
- All operations MUST be scoped to the authenticated user.
- Users MAY only read, create, update, and delete their own tasks.

**Rationale**: Multi-tenancy requires strict data isolation. Every database query and API endpoint must filter by user ID to prevent unauthorized cross-user access.

## Success Criteria

### Security
- Every API endpoint is protected by JWT authentication.
- Zero unauthorized access to any user's data.

**Validation**: Attempt to access another user's tasks → 403 Forbidden. Attempt to access protected endpoint without token → 401 Unauthorized.

### Data Integrity
- All tasks are persistently stored in Neon PostgreSQL.
- Task ownership is enforced at the database and application layers.

**Validation**: Query database directly → all tasks have valid user_id foreign keys. Attempt to insert task with invalid user_id → database constraint violation.

### Functional Completeness
- All specified CRUD and completion endpoints operate correctly.
- Frontend and backend communicate reliably through the defined API.

**Validation**: Execute full user journey from spec → all scenarios pass. API integration tests → all endpoints return expected responses.

### Spec Adherence
- Implementation fully satisfies the written specifications.
- No undocumented behavior or unverified features exist.

**Validation**: Cross-reference every code path with spec requirement. No features exist that cannot be traced to a spec requirement.

### Code Quality
- Codebase is modular, readable, and aligned with project conventions.
- System is maintainable, testable, and extensible for future phases.

**Validation**: Code review confirms adherence to separation of concerns. New team member can understand code structure within 2 hours. Adding a new feature requires changes in ≤3 well-defined locations.

## Governance

### Amendment Procedure
1. Proposed amendments MUST be documented with rationale and impact analysis.
2. Amendments REQUIRE explicit approval before taking effect.
3. Constitution version MUST be incremented according to semantic versioning:
   - MAJOR: Backward-incompatible governance/principle removals or redefinitions
   - MINOR: New principle/section added or materially expanded guidance
   - PATCH: Clarifications, wording improvements, non-semantic refinements

### Compliance Review
- All pull requests MUST verify compliance with this constitution.
- Violations MUST be justified with documented rationale.
- Complexity MUST be minimized; any deviation from principles requires explicit explanation.

### Constitution Authority
This constitution supersedes all other practices, guidelines, and conventions in the project. In case of conflict, the constitution takes precedence. Runtime development guidance is provided in `.specify/memory/` and `CLAUDE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-01-21 | **Last Amended**: 2026-01-21
