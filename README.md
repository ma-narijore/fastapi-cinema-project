# FastAPI Cinema Project

A FastAPI backend for a cinema application with user management, JWT authentication, role-based access control, Celery background tasks, and admin-only Swagger documentation.

---

## Tech Stack

- **FastAPI** — web framework
- **PostgreSQL** — database (SQLAlchemy + Alembic)
- **Redis + Celery** — background tasks (activation emails, password reset, expired token cleanup)
- **MinIO** — object storage
- **Mailpit** — local SMTP testing
- **Poetry** — dependency management
- **Docker & Docker Compose** — containerization

---

## Requirements

The only requirement is Docker and Docker Compose.

Python and Poetry are only needed if you want to run tests or development tools locally.

---

# Quick Start

Start the entire application:

```bash
docker compose up --build
```

On startup the application automatically:

- applies all Alembic migrations
- creates the default admin user
- starts the API on port **8000**
- starts Celery worker and Celery Beat
- starts Redis, PostgreSQL, MinIO, and Mailpit

---

# Services

| Service | URL / Port | Notes |
|----------|------------|-------|
| FastAPI API | http://localhost:8000 | Main application |
| Swagger UI | http://localhost:8000/docs | Admin only |
| ReDoc | http://localhost:8000/redoc | Admin only |
| OpenAPI | http://localhost:8000/openapi.json | Admin only |
| Mailpit | http://localhost:8025 | View activation/reset emails |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| PostgreSQL | localhost:5432 | postgres / postgres (database: cinema) |
| Redis | localhost:6379 | Celery broker |

---

# Default Admin User

The application creates an administrator automatically during startup.

| Field | Value |
|------|------|
| Email | `admin@example.com` |
| Password | `Admin123!` |

These values can be changed using the following environment variables:

- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

---

# Authentication

The API uses JWT Bearer authentication.

Log in to obtain an access token.

```bash
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"admin@example.com",
    "password":"Admin123!"
}'
```

Example response:

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

---

## Save the access token

For better usage add access_token to ModHeader or any other header modify 
`I used HeaderSmith` in google extensions:

```bash
Authorization Bearer {token}
```
Then You can easily access Swagger Docs
---

---

# Swagger Documentation

The documentation endpoints are protected and require an **admin** access token.

- `/docs`
- `/redoc`
- `/openapi.json`

Example:

```url
http://localhost:8000/docs
```

---

# User API

Once the application is running, open the interactive API documentation:

**Swagger UI:** http://localhost:8000/docs

Authorize using the admin bearer token obtained during login. From there you can test all available user endpoints directly from the browser.

The User API includes:

- **POST** `/users/register` — Register a new user
- **GET** `/users/activate` — Activate an account using an activation token
- **POST** `/users/{user_id}/activate` — Activate a user manually (Admin)
- **POST** `/users/login` — Authenticate and receive access and refresh tokens
- **GET** `/users/{user_id}` — Get a user's details (Authenticated)
- **PATCH** `/users/{user_id}/group` — Change a user's role (Admin)
- **DELETE** `/users/{user_id}` — Delete a user (Admin)
- **POST** `/users/forgot-password` — Request a password reset email
- **POST** `/users/reset-password` — Reset a password using a reset token
- **POST** `/users/change-password` — Change the current user's password
- **POST** `/users/logout` — Revoke a refresh token
---

# Running Tests

Tests use an in-memory SQLite database and do not require Docker.

Install dependencies:

```bash
poetry install
```

Run tests:

```bash
poetry run pytest -v
```

Run with coverage:

```bash
poetry run pytest \
--cov=app \
--cov-report=term-missing
```

---

# Code Quality

Lint:

```bash
poetry run ruff check .
```

Type checking:

```bash
poetry run mypy
```

---

# Continuous Integration

GitHub Actions runs on every push and pull request to the `main` branch and performs:

- Ruff linting
- Type checking
- Unit tests
- Coverage reporting

---

# Stopping the Application

Stop containers:

```bash
docker compose down
```

Stop containers and remove all volumes (fresh database):

```bash
docker compose down -v
```