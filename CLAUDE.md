# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Teeline Shorthand ML Checker — a web app for practicing Teeline shorthand letter forms with ML-powered handwriting recognition. Monorepo: `backend/` (Django 5.1 + DRF) and `frontend/` (Vite + React 18 + TypeScript).

## Development Commands

### Full stack (Docker)
```bash
docker compose up          # starts db (Postgres 15), backend (:8000), frontend (:5173)
docker compose up -d db    # just the database
```

### Backend (local, needs venv + Postgres running)
```bash
cd backend
.venv/Scripts/python.exe manage.py runserver          # dev server
.venv/Scripts/python.exe manage.py migrate             # apply migrations
.venv/Scripts/python.exe manage.py seed_symbols        # seed A-Z letter symbols
.venv/Scripts/python.exe manage.py seed_groupings      # seed 51 multi-letter grouping symbols
.venv/Scripts/python.exe manage.py seed_words          # seed ~95 practice words
.venv/Scripts/python.exe manage.py seed_admin          # create superuser from env vars
```

### Frontend (local)
```bash
cd frontend && npm run dev       # Vite dev server on :5173
cd frontend && npm run build     # tsc + vite build
```

### Tests
```bash
# Endpoint smoke tests (75 tests, SQLite in-memory, no Docker needed)
cd backend && .venv/Scripts/python.exe manage.py test tests.test_endpoints --settings=config.settings.test

# Single test class
.venv/Scripts/python.exe manage.py test tests.test_endpoints.AuthEndpointsTest --settings=config.settings.test

# Per-app unit tests
.venv/Scripts/python.exe manage.py test accounts checker admin_api --settings=config.settings.test

# Teeline decomposition tests (pytest)
.venv/Scripts/python.exe -m pytest checker/pytest_tests/test_teeline.py
```

## Architecture

### Backend Layered Pattern

All backend apps follow **Views → Services → Repositories → Models**. Views handle HTTP, services contain business logic, repositories encapsulate ORM queries. When adding new functionality, follow this pattern — don't put business logic in views or ORM queries in services.

### Dual Identity System

Users can practice anonymously or logged in. The `AnonymousSessionMiddleware` reads `X-Session-Token` header and attaches `request.anonymous_session`. All user-facing models (`Attempt`, `UserStats`, `WordAttemptSession`) have both `user` and `anonymous_session` FK fields with an XOR constraint — exactly one must be set.

Views use `_get_owner(request)` to resolve `{"user": ..., "session": ...}` and pass it to repositories. The `AllowAnonymousSession` permission class allows either authenticated or session-bearing requests.

On registration/login, `claim_anonymous_session()` transfers all anonymous data to the user account.

### Custom Job Queue

No Celery — custom multi-threaded worker in `jobs/`. Uses `select_for_update(skip_locked)` for safe polling. Handlers are registered via `@register("job_type")` decorator in `jobs/handlers.py`. The worker auto-starts in `JobsConfig.ready()` — set `DISABLE_JOB_WORKERS=1` to prevent this (used in tests).

### API Authentication

- JWT via SimpleJWT (30min access, 7-day refresh)
- All endpoints default to `IsAuthenticated`
- Public endpoints use `AllowAny` (symbols, words, leaderboard)
- Practice endpoints use `AllowAnonymousSession`
- Admin endpoints use `IsAdminUser` (requires `is_staff`)

### Frontend API Client

`frontend/src/api/client.ts` is a custom `fetch` wrapper (no axios). Handles JWT token storage in localStorage, auto-refresh on 401, and `X-Session-Token` header injection. Admin API is separate in `api/admin.ts`.

### Key Files

- `config/exceptions.py` — `AppError` exception + custom DRF exception handler normalizing errors to `{"error": "..."}`
- `checker/teeline.py` — algorithmic word-to-letter decomposition (vowel removal, blends, R-doubling)
- `jobs/worker.py` — multi-threaded job worker with exponential backoff retry
- `frontend/src/hooks/useJobPoller.ts` — polls async job status until terminal state

## Settings

Three Django settings modules:
- `config.settings.local` — dev (Postgres via Docker, DEBUG=True)
- `config.settings.test` — tests (SQLite in-memory, fast password hasher, no workers)
- `config.settings.production` — prod (Postgres via DATABASE_URL, HTTPS, WhiteNoise)

`base.py` requires `SECRET_KEY` env var on import. Local/test override it, but the env var must exist or be set before import.

## Known Issues

Four views (`SymbolDetailView`, `AttemptDetailView`, `WordDetailView`, `WordSessionDetailView`) raise unhandled `DoesNotExist` on missing resources instead of returning 404. Documented in endpoint smoke tests with `# BUG:` comments.

## Documentation

- `docs/SYSTEM_DOCUMENTATION.md` — comprehensive system reference (models, all endpoints, services, infrastructure)
- `docs/superpowers/specs/` — design specs for each feature
- `docs/superpowers/plans/` — implementation plans for each phase
