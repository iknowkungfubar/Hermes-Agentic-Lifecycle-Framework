# Technical Specification: Task Management API

## Functional Requirements

### FR-001: User Registration
**Priority:** P0 | **Depends on:** Nothing | **Estimate:** 2-4h

**Description:** A user can create an account with email + password.

**Acceptance Criteria:**
- [ ] POST /api/v1/auth/register accepts {email, password, name}
- [ ] Returns 201 with user object on success
- [ ] Returns 409 with code EMAIL_TAKEN on duplicate
- [ ] Password hashed with bcrypt (cost >= 12)
- [ ] Email normalized to lowercase before storage

### FR-002: User Login
**Priority:** P0 | **Depends on:** FR-001 | **Estimate:** 1-2h

**Description:** A registered user can log in to receive a JWT session.

**Acceptance Criteria:**
- [ ] POST /api/v1/auth/login accepts {email, password}
- [ ] Returns 200 with JWT token on success
- [ ] Returns 401 with INVALID_CREDENTIALS on bad password
- [ ] Token expires after 24 hours
- [ ] HTTP-only cookie with session token set on success

### FR-003: Create Task
**Priority:** P0 | **Depends on:** FR-002 | **Estimate:** 2-3h

**Description:** An authenticated user can create a task.

**Acceptance Criteria:**
- [ ] POST /api/v1/tasks accepts {title, description?, due_date?, priority?, tags?}
- [ ] Returns 201 with task object
- [ ] Returns 401 if not authenticated
- [ ] Returns 422 if title missing or empty
- [ ] Task automatically assigned to creating user

### FR-004: List Tasks
**Priority:** P0 | **Depends on:** FR-003 | **Estimate:** 1-2h

**Description:** An authenticated user can list their tasks with pagination.

**Acceptance Criteria:**
- [ ] GET /api/v1/tasks returns paginated task list
- [ ] Supports ?page=X&per_page=Y
- [ ] Defaults to page 1, per_page 20
- [ ] Only returns tasks owned by the authenticated user
- [ ] Supports ?status=done|pending filter

### FR-005: Update Task
**Priority:** P1 | **Depends on:** FR-003 | **Estimate:** 1-2h

**Description:** An authenticated user can update their task.

**Acceptance Criteria:**
- [ ] PATCH /api/v1/tasks/{id} accepts partial updates
- [ ] Returns 200 with updated task
- [ ] Returns 404 if task doesn't exist
- [ ] Returns 403 if task belongs to another user

### FR-006: Delete Task
**Priority:** P1 | **Depends on:** FR-003 | **Estimate:** 1h

**Description:** An authenticated user can delete their task.

**Acceptance Criteria:**
- [ ] DELETE /api/v1/tasks/{id} returns 204
- [ ] Returns 404 if task doesn't exist
- [ ] Returns 403 if task belongs to another user

## Non-Functional Requirements

| ID | Category | Description | Target |
|----|----------|-------------|--------|
| NFR-001 | Performance | Create task p95 latency | <200ms |
| NFR-002 | Performance | List tasks p95 latency (1000 tasks) | <100ms |
| NFR-003 | Security | Password hashing algorithm | bcrypt cost 12 |
| NFR-004 | Security | Auth token type | JWT, 24h expiry |
| NFR-005 | Scalability | Concurrent users | 1000 |
| NFR-006 | Observability | Health check endpoint | /health |
| NFR-007 | Observability | Structured JSON logging | All services |
| NFR-008 | Security | Rate limiting | 100 req/min/user |

## API Contracts

### POST /api/v1/auth/register
**Request:** {email: string, password: string, name: string}
**Response 201:** {id: uuid, email: string, name: string, created_at: datetime}
**Errors:** 409 (duplicate), 422 (validation)

### POST /api/v1/auth/login
**Request:** {email: string, password: string}
**Response 200:** {token: string, user: {id, email, name}}
**Errors:** 401 (invalid credentials)

### GET /api/v1/tasks
**Query:** ?page=1&per_page=20&status=pending
**Response 200:** {items: Task[], total: int, page: int, per_page: int}
**Errors:** 401 (unauthorized)

### POST /api/v1/tasks
**Request:** {title: string, description?: string, priority?: "low"|"medium"|"high"}
**Response 201:** Task object
**Errors:** 401, 422 (validation)

### PATCH /api/v1/tasks/{id}
**Request:** {title?: string, status?: "pending"|"done"}
**Response 200:** Updated Task object
**Errors:** 401, 403, 404

### DELETE /api/v1/tasks/{id}
**Response:** 204
**Errors:** 401, 403, 404

## Data Model

### User
- id: UUID (PK)
- email: string (unique, indexed)
- password_hash: string
- name: string
- created_at: datetime
- updated_at: datetime

### Task
- id: UUID (PK)
- user_id: UUID (FK -> User.id, indexed)
- title: string (max 255)
- description: text (nullable)
- status: enum(pending, done) (default: pending)
- priority: enum(low, medium, high) (default: medium)
- due_date: datetime (nullable)
- created_at: datetime
- updated_at: datetime
