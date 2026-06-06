# Shorthand — System Documentation

> Teeline Shorthand ML Checker: A web application for practicing and learning Teeline shorthand letter forms using machine learning-powered handwriting recognition.

**Generated**: 2026-06-06 | **Phase**: 1 complete (code), Phases 2–4 pending

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Backend](#backend)
   - [Django Apps](#django-apps)
   - [Data Models](#data-models)
   - [API Endpoints](#api-endpoints)
   - [Service Layer](#service-layer)
   - [Repository Layer](#repository-layer)
   - [Middleware & Permissions](#middleware--permissions)
   - [Exception Handling](#exception-handling)
   - [Job System](#job-system)
   - [ML Pipeline](#ml-pipeline)
   - [Management Commands](#management-commands)
   - [Settings & Configuration](#settings--configuration)
5. [Frontend](#frontend)
   - [Routing](#routing)
   - [API Client](#api-client)
   - [Authentication Flow](#authentication-flow)
   - [Components](#components)
   - [Pages](#pages)
   - [Hooks](#hooks)
   - [Type Definitions](#type-definitions)
   - [Styling & Design System](#styling--design-system)
6. [Infrastructure](#infrastructure)
   - [Docker Compose (Development)](#docker-compose-development)
   - [Production Deployment](#production-deployment)
   - [Environment Variables](#environment-variables)
7. [Testing](#testing)
   - [Test Settings](#test-settings)
   - [Endpoint Smoke Tests](#endpoint-smoke-tests)
   - [Running Tests](#running-tests)
8. [Known Issues](#known-issues)
9. [Design Decisions](#design-decisions)
10. [References](#references)

---

## Architecture Overview

```
┌─────────────────┐       ┌──────────────────┐       ┌──────────────┐
│  React SPA      │──API──│  Django REST API  │──ORM──│ PostgreSQL   │
│  (Vite + TS)    │       │  (DRF + JWT)      │       │ (15-alpine)  │
│  Port 5173      │       │  Port 8000        │       │ Port 5432    │
└─────────────────┘       └────────┬─────────-┘       └──────────────┘
                                   │
                          ┌────────┴─────────┐
                          │  Job Worker       │
                          │  (Multi-threaded) │
                          │  TFLite Inference │
                          └──────────────────-┘
```

**Pattern**: Monorepo with layered backend architecture (Views → Services → Repositories → Models). Frontend is a single-page application with no state management library — local `useState` and module-scoped variables only.

**Auth model**: Dual-identity system. Users can practice anonymously (tracked via `X-Session-Token` header / `AnonymousSession` model) or register. On registration, anonymous data is transferred to the user account via session claiming.

---

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 5.1 |
| REST API | Django REST Framework | 3.15 |
| Auth | SimpleJWT | 5.3 |
| Database | PostgreSQL | 15 |
| DB driver | psycopg2-binary | 2.9 |
| CORS | django-cors-headers | 4.4 |
| Static files | WhiteNoise | 6.7 |
| WSGI server | Gunicorn | 22.0 |
| DB URL parsing | dj-database-url | 2.2 |
| Image processing | Pillow | 10.4 |
| ML inference | tflite-runtime | 2.14 |
| Numeric | NumPy | 1.26 |

### Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| UI library | React | 18.3.1 |
| Routing | React Router DOM | 6.28.0 |
| Language | TypeScript | 5.6.3 |
| Build tool | Vite | 6.0.0 |
| HTTP client | Native `fetch` API | — |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Containerization | Docker + Docker Compose |
| Backend hosting | Render (web service) |
| Frontend hosting | Vercel |
| Database hosting | Supabase (PostgreSQL) |

---

## Project Structure

```
Shorthand/
├── backend/
│   ├── accounts/          # Auth & user management app
│   ├── checker/           # Core shorthand practice app
│   ├── jobs/              # Background job queue app
│   ├── admin_api/         # Admin panel backend app
│   ├── config/            # Django project configuration
│   │   ├── settings/      # base.py, local.py, production.py, test.py
│   │   ├── urls.py        # Root URL routing
│   │   ├── middleware.py  # AnonymousSessionMiddleware
│   │   ├── exceptions.py  # Custom exception handler
│   │   └── wsgi.py
│   ├── ml/                # Machine learning module
│   │   ├── inference.py   # TFLite prediction
│   │   ├── preprocessing.py
│   │   └── train/         # Training pipeline scripts
│   ├── tests/             # System-level tests
│   │   └── test_endpoints.py  # Endpoint smoke tests (71 tests)
│   ├── Dockerfile         # Multi-stage (dev/prod)
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           # API client (client.ts, admin.ts)
│   │   ├── components/    # Shared React components
│   │   │   └── admin/     # Admin-specific components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── pages/         # Page components
│   │   │   └── admin/     # Admin page components
│   │   ├── types/         # TypeScript type definitions
│   │   ├── App.tsx        # Root component + routing
│   │   ├── main.tsx       # Entry point
│   │   ├── styles/        # CSS stylesheets
│   │   │   ├── tokens.css     # Design tokens
│   │   │   ├── components.css
│   │   │   ├── layout.css
│   │   │   └── admin.css
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── data/                  # Training data (raw, augmented, reference)
├── docs/                  # Specs and plans
├── docker-compose.yml
├── render.yaml            # Render.com deployment config
├── .env.example
├── .env.prod
└── .gitignore
```

---

## Backend

### Django Apps

| App | Purpose | URL prefix |
|-----|---------|-----------|
| `accounts` | User registration, login, JWT auth, session claiming | `/api/auth/` |
| `checker` | Symbols, attempts, progress, leaderboard, words, word sessions | `/api/` |
| `jobs` | Background job queue with multi-threaded worker | (internal) |
| `admin_api` | Admin dashboard, user/content management, analytics, audit log | `/api/admin/` |

### Data Models

#### accounts.AnonymousSession
| Field | Type | Constraints |
|-------|------|------------|
| session_token | UUIDField | unique, indexed |
| created_at | DateTimeField | auto_now_add |
| last_active | DateTimeField | auto_now |

#### checker.Symbol
| Field | Type | Constraints |
|-------|------|------------|
| letter | CharField(1) | unique |
| name | CharField(50) | |
| reference_image_url | URLField | blank=True |

#### checker.Attempt (extends TimestampedModel)
| Field | Type | Constraints |
|-------|------|------------|
| id | UUIDField | PK, default=uuid4 |
| user | FK → User | nullable, on_delete CASCADE |
| anonymous_session | FK → AnonymousSession | nullable, on_delete CASCADE |
| symbol | FK → Symbol | on_delete CASCADE |
| word_session | FK → WordAttemptSession | nullable, on_delete CASCADE |
| word_position | IntegerField | nullable |
| image_data | BinaryField | |
| predicted_label | CharField(1) | nullable |
| confidence | FloatField | nullable |
| is_correct | BooleanField | nullable |
| status | CharField | choices: pending, processing, completed, failed |
| points | IntegerField | default=0 |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

**Constraint**: XOR on `user` / `anonymous_session` — exactly one must be set.

#### checker.UserStats (extends TimestampedModel)
| Field | Type | Constraints |
|-------|------|------------|
| user | OneToOneField → User | nullable |
| anonymous_session | OneToOneField → AnonymousSession | nullable |
| total_score | IntegerField | default=0 |
| current_streak | IntegerField | default=0 |
| best_streak | IntegerField | default=0 |

**Constraint**: XOR on `user` / `anonymous_session`.

#### checker.WordTopic (extends TimestampedModel)
| Field | Type | Constraints |
|-------|------|------------|
| name | CharField(50) | |
| slug | SlugField | unique |

#### checker.Word (extends TimestampedModel)
| Field | Type | Constraints |
|-------|------|------------|
| text | CharField(100) | unique |
| teeline_letters | CharField(50) | |
| difficulty | CharField | choices: beginner, intermediate, advanced |
| topic | FK → WordTopic | on_delete CASCADE |
| is_curated | BooleanField | default=False |

#### checker.WordAttemptSession (extends TimestampedModel)
| Field | Type | Constraints |
|-------|------|------------|
| word | FK → Word | on_delete CASCADE |
| user | FK → User | nullable |
| anonymous_session | FK → AnonymousSession | nullable |
| status | CharField | choices: in_progress, completed, abandoned |
| letters_correct | IntegerField | default=0 |
| letters_total | IntegerField | default=0 |
| points_awarded | IntegerField | default=0 |

**Constraint**: XOR on `user` / `anonymous_session`.

#### jobs.Job
| Field | Type | Constraints |
|-------|------|------------|
| id | UUIDField | PK |
| type | CharField(50) | indexed |
| user | FK → User | nullable, on_delete SET_NULL |
| correlation_key | CharField(255) | unique, nullable |
| payload | JSONField | default=dict |
| status | CharField | choices: pending, running, completed, failed, dead |
| priority | IntegerField | default=0 |
| attempts | IntegerField | default=0 |
| max_attempts | IntegerField | default=3 |
| error_log | TextField | |
| locked_at | DateTimeField | nullable |
| locked_by | CharField(100) | nullable |
| scheduled_at | DateTimeField | default=now |
| completed_at | DateTimeField | nullable |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

**Index**: `(status, scheduled_at)`. Ordering: `-priority, scheduled_at`.

#### admin_api.AuditLog
| Field | Type | Constraints |
|-------|------|------------|
| id | UUIDField | PK |
| actor | FK → User | nullable, on_delete SET_NULL |
| action | CharField(100) | indexed |
| target_type | CharField(50) | indexed |
| target_id | CharField(255) | |
| details | JSONField | default=dict |
| created_at | DateTimeField | indexed |

#### admin_api.SystemSetting
| Field | Type | Constraints |
|-------|------|------------|
| id | UUIDField | PK |
| key | CharField(100) | unique |
| value | JSONField | default=dict |
| updated_at | DateTimeField | auto_now |
| updated_by | FK → User | nullable, on_delete SET_NULL |

### API Endpoints

#### Authentication — `/api/auth/`

| Method | Path | View | Auth | Description |
|--------|------|------|------|-------------|
| POST | `/register/` | RegisterView | AllowAny | Create user account; claims session via X-Session-Token |
| POST | `/login/` | TokenObtainPairView | AllowAny | Returns JWT access + refresh tokens |
| POST | `/refresh/` | TokenRefreshView | AllowAny | Refresh access token |
| GET | `/me/` | MeView | IsAuthenticated | Current user profile |
| PATCH | `/me/` | MeView | IsAuthenticated | Update email/password (requires current_password) |
| POST | `/claim-session/` | ClaimSessionView | IsAuthenticated | Transfer anonymous data to user |
| POST | `/logout/` | LogoutView | IsAuthenticated | Clears image_data from completed attempts |

#### Public API — `/api/`

| Method | Path | View | Auth | Description |
|--------|------|------|------|-------------|
| GET | `/symbols/` | SymbolListView | AllowAny | List all symbols |
| GET | `/symbols/:letter/` | SymbolDetailView | AllowAny | Symbol detail |
| GET | `/attempts/` | AttemptListView | AllowAnonymousSession | Paginated attempts |
| POST | `/attempts/` | AttemptListView | AllowAnonymousSession | Submit attempt (10/min throttle) |
| GET | `/attempts/:pk/` | AttemptDetailView | AllowAnonymousSession | Attempt detail |
| GET | `/attempts/:pk/image/` | AttemptImageView | AllowAnonymousSession | PNG image (cached 24h) |
| GET | `/progress/` | ProgressView | AllowAnonymousSession | Per-symbol stats + streaks |
| GET | `/leaderboard/` | LeaderboardView | AllowAny | Top 50 by total_score |
| GET | `/word-topics/` | WordTopicListView | AllowAny | All word topics |
| GET | `/words/` | WordListView | AllowAny | Words (filter: difficulty, topic) |
| GET | `/words/:pk/` | WordDetailView | AllowAny | Word detail + teeline components |
| POST | `/word-sessions/` | WordSessionListView | AllowAnonymousSession | Start word practice session |
| GET | `/word-sessions/:pk/` | WordSessionDetailView | AllowAnonymousSession | Session detail + letter results |
| POST | `/word-sessions/:pk/complete/` | WordSessionCompleteView | AllowAnonymousSession | Complete session, award points |
| GET | `/word-progress/` | WordProgressView | AllowAnonymousSession | Word progress (filter: difficulty, topic) |

#### Admin API — `/api/admin/`

All admin endpoints require `IsAuthenticated` + `is_staff`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/stats/` | User count, attempt count, active today, pending/failed jobs |
| GET | `/users/` | Paginated user list (searchable) |
| GET, PATCH | `/users/:pk/` | User detail; toggle is_active/is_staff |
| GET, POST | `/content/symbols/` | List/create symbols |
| GET, PATCH, DELETE | `/content/symbols/:pk/` | Symbol CRUD (no delete if attempts exist) |
| GET, POST | `/content/words/` | List/create words |
| GET, PATCH, DELETE | `/content/words/:pk/` | Word CRUD (no delete if sessions exist) |
| GET | `/analytics/usage/` | Daily attempt counts (param: days 1–365) |
| GET | `/analytics/retention/` | Total/active users + retention rate |
| GET | `/jobs/` | Job list (filter: status) |
| GET | `/jobs/:pk/` | Job detail |
| POST | `/jobs/:pk/retry/` | Retry failed/dead job |
| POST | `/jobs/:pk/cancel/` | Cancel pending job |
| GET | `/audit-log/` | Audit log (filter: action, actor, target_type) |
| GET, POST | `/settings/` | System settings CRUD |

### Service Layer

**`accounts/services.py`**
- `create_user(username, email, password)` → User

**`checker/services.py`**
- `submit_attempt(symbol_letter, image_data, user/session, word_session, word_position)` — Decodes base64, creates Attempt, enqueues predict job
- `get_progress(user/session)` — Aggregates per-symbol stats, streaks, total_score
- `claim_anonymous_session(session_token, user)` — Transfers attempts + word sessions + merges UserStats; returns count
- `record_score(attempt)` — Awards points: 10 base + 5 per 5-streak + up to 5 confidence bonus; updates streaks

**`checker/word_service.py`**
- `get_word_components(word_id)` — Returns teeline components (curated override or algorithmic decomposition)
- `start_session(word_id, user/session)` → WordAttemptSession
- `complete_session(session_id, user/session)` — Calculates letters_correct, awards 10 pts (+5 if perfect), updates UserStats
- `get_session_detail(session_id, user/session)` — Session with per-letter results
- `get_word_progress(user/session, difficulty, topic_slug)` — Aggregated word-level progress

**`admin_api/services.py`**
- `log_audit(actor, action, target_type, target_id, details)` → AuditLog (sanitizes UUID objects in details via custom JSON encoder)

### Repository Layer

**`checker/repositories.py`**
- `SymbolRepository`: `get_all()`, `get_by_letter(letter)`
- `AttemptRepository`: `create()`, `get_by_id()`, `get_by_owner()`, `get_progress()`, `get_current_streak()`, `transfer_session_to_user()`

**`checker/word_repository.py`**
- `WordTopicRepository`: `get_all()`
- `WordRepository`: `get_all(difficulty, topic_slug)`, `get_by_id(word_id)`
- `WordSessionRepository`: `create()`, `get_by_id()`, `get_progress()`, `transfer_session_to_user()`

**`jobs/repository.py`**
- `JobRepository`: `enqueue()`, `poll(worker_id)` (select_for_update skip_locked), `complete()`, `fail()` (exponential backoff: 5s × 2^attempts, max 300s), `reclaim_stale(minutes=10)`, `cleanup_old(days=7)`

### Middleware & Permissions

**AnonymousSessionMiddleware** (`config/middleware.py`):
Reads `X-Session-Token` header → creates or retrieves `AnonymousSession` → updates `last_active` → attaches to `request.anonymous_session`.

**AllowAnonymousSession** (`checker/permissions.py`):
Allows requests from authenticated users OR requests with a valid anonymous session.

**IsAdminUser** (`admin_api/permissions.py`):
Requires `is_authenticated` AND `is_staff`.

### Exception Handling

**`config/exceptions.py`**:
- `AppError(message, status_code)` — Custom exception class for business logic errors
- `custom_exception_handler` — Normalizes DRF errors to `{"error": "..."}` or `{"error": "...", "fields": {...}}` for 400/401/403/404 responses

### Job System

**Architecture**: Custom multi-threaded job queue (no Celery/django-q2 dependency).

**Worker** (`jobs/worker.py`):
- Configurable threads via `JOB_WORKER_THREADS` env (default 2)
- Poll interval via `JOB_POLL_INTERVAL_SECONDS` (default 5)
- Uses `select_for_update(skip_locked)` for safe concurrent polling
- Handler registry pattern via `@register("job_type")` decorator
- Maintenance thread: reclaims stale jobs (every `JOB_RECLAIM_INTERVAL_SECONDS`, default 120s), cleans up old jobs (every `JOB_CLEANUP_INTERVAL_SECONDS`, default 86400s)

**Retry strategy**: Exponential backoff — `5s × 2^attempts`, capped at 300s. Jobs exceeding `max_attempts` are marked `dead`.

**Handlers** (`jobs/handlers.py`, `jobs/predict_handler.py`):
- `predict` job type: runs TFLite inference on attempt image data

### ML Pipeline

**Inference** (`ml/inference.py`): Loads TFLite model, runs prediction on preprocessed image
**Preprocessing** (`ml/preprocessing.py`): Image preparation for the model

**Training pipeline** (`ml/train/`):
| Script | Purpose |
|--------|---------|
| `train.py` | MobileNetV2 transfer learning |
| `augment.py` | Data augmentation |
| `collect.py` | Data collection |
| `convert.py` | Model → TFLite conversion |
| `evaluate.py` | Model evaluation |
| `generate_synthetic.py` | Synthetic training data |

**Training dependencies** (`ml/train/requirements.txt`): tensorflow, matplotlib, numpy, pillow, scikit-learn

**Teeline decomposition** (`checker/teeline.py`): Algorithmic word → letter decomposition with vowel removal, consonant blends, R-doubling rules.

### Management Commands

| Command | App | Purpose |
|---------|-----|---------|
| `seed_admin` | accounts | Creates superuser from `DJANGO_SUPERUSER_*` env vars |
| `make_admin` | admin_api | Promotes existing user to staff |
| `seed_symbols` | checker | Populates Symbol table (a–z) |
| `seed_words` | checker | Populates ~95 words across 4 topics |
| `cleanup_stale_sessions` | checker | Removes old anonymous sessions |

### Settings & Configuration

**Base** (`config/settings/base.py`):
- Installed apps: Django core, rest_framework, corsheaders, accounts, checker, jobs, admin_api
- REST Framework: JWTAuthentication, IsAuthenticated default, PageNumberPagination (20/page), custom exception handler
- JWT: 30-minute access tokens, 7-day refresh tokens
- CORS allowed headers: accept, authorization, content-type, x-csrftoken, x-session-token
- Password validators: minimum length 10

**Local** (`config/settings/local.py`): PostgreSQL (Docker `db` host), DEBUG=True, localhost CORS

**Test** (`config/settings/test.py`): SQLite in-memory database, MD5 password hasher (fast), disables job workers via `DISABLE_JOB_WORKERS` env var

**Production** (`config/settings/production.py`): PostgreSQL via `dj-database-url` (conn_max_age=600), ALLOWED_HOSTS/CORS from env, SSL/HSTS security headers, WhiteNoise compressed static files

---

## Frontend

### Routing

Defined in `App.tsx` via React Router DOM 6:

| Path | Component | Notes |
|------|-----------|-------|
| `/` | PracticePage | Default — letter practice |
| `/words` | WordPracticePage | Word practice |
| `/progress` | ProgressPage | User stats |
| `/leaderboard` | LeaderboardPage | Global rankings |
| `/login` | LoginPage | Register/login |
| `/settings` | SettingsPage | Email/password update |
| `/about` | AboutPage | Project info |
| `/admin/*` | AdminLayout | Lazy-loaded, AdminRoute guard |
| `/admin/` | DashboardPage | Admin overview |
| `/admin/users` | UsersPage | User management |
| `/admin/users/:id` | UserDetailPage | User detail |
| `/admin/content` | ContentPage | Symbol/word management |
| `/admin/analytics` | AnalyticsPage | Usage/retention stats |
| `/admin/jobs` | JobsPage | Job monitoring |
| `/admin/audit-log` | AuditLogPage | Audit trail |
| `/admin/settings` | SettingsPage (admin) | System settings |

### API Client

**`api/client.ts`**:
- Pure `fetch` wrapper (no axios)
- Base URL from `VITE_API_URL` env or `/api`
- Token storage: `shorthand_access_token` / `shorthand_refresh_token` in localStorage
- Anonymous session: UUID in `shorthand_session_token` localStorage key
- All requests include `X-Session-Token` header; authenticated requests add `Authorization: Bearer`
- Auto-refresh on 401: refreshes token, retries original request; on failure clears tokens
- Exported `api` object with namespaced methods: `auth`, `symbols`, `attempts`, `progress`, `leaderboard`, `words`, `wordSessions`, `wordProgress`
- `ApiError` class captures HTTP status + response body

**`api/admin.ts`**:
- `adminRequest` helper prefixes all paths with `/admin`
- Endpoints: dashboard stats, user CRUD, content CRUD, analytics, jobs (list/retry/cancel), audit log, system settings

### Authentication Flow

1. **Anonymous**: Session UUID generated on first visit, stored in localStorage, sent as `X-Session-Token`
2. **Register**: POST `/auth/register/` → POST `/auth/login/` → stores JWT tokens
3. **Login**: POST `/auth/login/` → stores tokens → POST `/auth/claim-session/` to merge anonymous data → clears session token
4. **Token refresh**: On 401, transparently refreshes via `/auth/refresh/` and retries
5. **Logout**: Clears tokens from localStorage

### Components

| Component | File | Purpose |
|-----------|------|---------|
| Header | `components/Header.tsx` | Top nav with tabs (Practice, Words, Progress, Leaderboard, About, Admin for staff). Shows username dropdown when logged in |
| DrawingCanvas | `components/DrawingCanvas.tsx` | Canvas (400x400) with Teeline guidelines at 20%/40%/70%/90%. Mouse + touch drawing. Exports PNG base64. Undo/Clear actions |
| FeedbackPanel | `components/FeedbackPanel.tsx` | Shows correct/incorrect result, predicted label, confidence bar, points. Next/Retry buttons |
| LetterCard | `components/LetterCard.tsx` | Clickable card for word practice — shows letter, teeline image, status icon, blend/R-doubling badges |
| WordReference | `components/WordReference.tsx` | Horizontal strip of teeline images with blend connectors |
| AdminRoute | `components/admin/AdminRoute.tsx` | Guard wrapper — checks auth + is_staff, redirects if unauthorized |
| StatCard | `components/admin/StatCard.tsx` | Simple label + value display card |
| ActionConfirm | `components/admin/ActionConfirm.tsx` | Modal overlay for destructive action confirmation |

### Pages

| Page | Key behavior |
|------|-------------|
| **PracticePage** | Loads symbols, random/sequential mode, DrawingCanvas → submit attempt → poll with useJobPoller → FeedbackPanel. Streak/score badges, milestone toast every 5 |
| **WordPracticePage** | Filter by difficulty/topic, select word → create WordSession → LetterCards per component → draw each letter → complete session |
| **ProgressPage** | Tabs: Symbols (per-symbol accuracy bars, 5 weakest highlighted) / Words (per-word progress bars, mastered count) |
| **LeaderboardPage** | Top 50 table, highlights current user row |
| **LoginPage** | Toggle register/login mode, field error parsing from ApiError |
| **SettingsPage** | Update email + password, requires current_password |
| **Admin pages** | Dashboard stats, user management (activate/deactivate, promote/demote), content CRUD with delete guards, usage/retention analytics with day-range selector, job monitoring with retry/cancel, paginated audit log, system settings editor |

### Hooks

**`useJobPoller<T>`** (`hooks/useJobPoller.ts`):
Polls an async fetcher at configurable interval (default 1s) until status reaches a terminal state (default: `completed` | `failed`). Returns `{ data, status, error, isComplete, startPolling, stopPolling }`.

### Type Definitions

**`types/index.ts`**: `Symbol`, `Attempt`, `Progress`, `ProgressResponse`, `LeaderboardEntry`, `TokenPair`, `User`, `Word`, `WordTopic`, `TeelineComponent`, `WordSession`, `WordProgress`

**`types/admin.ts`**: `AdminUser`, `DashboardStats`, `AdminSymbol`, `AdminWord`, `AdminJob`, `AdminJobDetail`, `AuditLogEntry`, `SystemSetting`, `UsageStats`, `RetentionStats`, `PaginatedResponse<T>`

### Styling & Design System

**Theme**: "Stationery Notebook" — ruled-line overlay via CSS pseudo-element with repeating linear gradient.

**Design tokens** (`styles/tokens.css`):
- Colors: paper `#f7f3eb`, ink `#1a1a1a`, accent/error `#b5350f`, success `#1d6b3a`
- Fonts: Syne (headings), DM Mono (body/monospace)
- Notebook ruled-line effect as fixed background overlay

**Stylesheets**: `styles/tokens.css`, `styles/components.css`, `styles/layout.css`, `styles/admin.css` — all custom CSS, no framework.

---

## Infrastructure

### Docker Compose (Development)

3 services in `docker-compose.yml`:

| Service | Image | Port | Notes |
|---------|-------|------|-------|
| db | postgres:15-alpine | 5433 → 5432 | Healthcheck with pg_isready, named volume `pgdata` |
| backend | ./backend (Dockerfile dev stage) | 8000 | Mounts `./backend`, uses `.env`, depends on db health |
| frontend | ./frontend (Dockerfile) | 5173 | Mounts `./frontend`, excludes node_modules via volume |

**Backend Dockerfile** — Multi-stage:
- **Base**: Python 3.11-slim with libpq-dev/gcc
- **Dev**: Django runserver
- **Prod**: Non-root user, collectstatic, migrations → seed → Gunicorn (2 workers)

**Frontend Dockerfile**: Node 20 Alpine, Vite dev server with `--host 0.0.0.0`

### Production Deployment

Defined in `render.yaml`:
- **Web service** `shorthand-api`: Docker-based, auto-deploy from repo
- **Database** `shorthand-db`: Render free-tier PostgreSQL
- Auto-runs migrations + seed commands on deploy

**Frontend**: Deployed to Vercel (separate config)

**Database**: Supabase PostgreSQL (connection string in `.env.prod`)

### Environment Variables

| Variable | Used by | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | Django | Cryptographic signing |
| `DATABASE_URL` | Django (prod) | PostgreSQL connection string |
| `DJANGO_SETTINGS_MODULE` | Django | Settings module path |
| `ALLOWED_HOSTS` | Django (prod) | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | Django (prod) | Comma-separated frontend origins |
| `DJANGO_SUPERUSER_USERNAME` | seed_admin | Admin username |
| `DJANGO_SUPERUSER_EMAIL` | seed_admin | Admin email |
| `DJANGO_SUPERUSER_PASSWORD` | seed_admin | Admin password |
| `DISABLE_JOB_WORKERS` | Worker | Set to any value to skip worker auto-start (used in tests) |
| `JOB_WORKER_THREADS` | Worker | Thread count (default 2) |
| `JOB_POLL_INTERVAL_SECONDS` | Worker | Poll interval (default 5) |
| `JOB_RECLAIM_INTERVAL_SECONDS` | Worker | Stale job reclaim interval (default 120) |
| `JOB_CLEANUP_INTERVAL_SECONDS` | Worker | Old job cleanup interval (default 86400) |
| `VITE_API_URL` | Frontend | Backend API base URL |
| `POSTGRES_USER` | docker-compose | DB user |
| `POSTGRES_PASSWORD` | docker-compose | DB password |
| `POSTGRES_DB` | docker-compose | DB name |

---

## Testing

### Test Settings

`config/settings/test.py` provides a lightweight test environment:
- **Database**: SQLite in-memory (`:memory:`) — no PostgreSQL dependency for running tests
- **Password hasher**: MD5 (fast, avoids bcrypt overhead in tests)
- **Job workers**: Disabled via `DISABLE_JOB_WORKERS=1` env var to prevent background threads from starting during test setup
- **Migration compatibility**: Migration `checker/0002` skips PostgreSQL-specific raw SQL on SQLite

### Endpoint Smoke Tests

`backend/tests/test_endpoints.py` — **71 tests** across **14 test classes** verifying every API endpoint returns the correct status code. Tests cover:

| Area | Tests | Coverage |
|------|-------|----------|
| Auth (`/api/auth/`) | 12 | register, login, refresh, me (GET/PATCH), claim-session, logout + auth guards |
| Symbols (`/api/symbols/`) | 3 | list, detail, not-found |
| Attempts (`/api/attempts/`) | 5 | list, create (session + authenticated), detail not-found, auth guard |
| Progress & Leaderboard | 4 | progress (authenticated, session, unauthenticated), leaderboard |
| Words (`/api/words/`) | 5 | topics, list, filters, detail, not-found |
| Word Sessions | 4 | create, detail, complete, not-found |
| Word Progress | 3 | authenticated, filters, auth guard |
| Admin Dashboard | 3 | stats, non-admin guard, unauthenticated guard |
| Admin Users | 5 | list, search, detail, patch, non-admin guard |
| Admin Content | 11 | symbol CRUD, word CRUD, delete guards, non-admin guard |
| Admin Analytics | 4 | usage, usage with days filter, retention, non-admin guard |
| Admin Jobs | 6 | list, filter, detail, retry, cancel, non-admin guard |
| Admin Audit Log | 3 | list, filter, non-admin guard |
| Admin Settings | 3 | get, patch, non-admin guard |

**Test infrastructure**:
- Base class `EndpointTestBase` creates 4 pre-configured API clients: anonymous, session-bearing, authenticated user, and admin
- Shared test data via `setUpTestData` (user, admin, anonymous session, symbol, topic, word)
- Inline 1×1 PNG for attempt submission tests (no filesystem dependency)

### Per-App Unit Tests

| File | Tests |
|------|-------|
| `accounts/tests.py` | Registration, login (JWT tokens), /me endpoint |
| `checker/tests.py` | Models, repositories, services, API views |
| `checker/pytest_tests/test_teeline.py` | Teeline decompose function (phonetic substitution, blends, R-doubling) |
| `admin_api/tests.py` | Admin permissions, audit logging, dashboard, user/content/job CRUD |

### Running Tests

```bash
# All endpoint smoke tests (no Docker required)
cd backend
.venv/Scripts/python.exe manage.py test tests.test_endpoints --settings=config.settings.test

# All app-level tests
.venv/Scripts/python.exe manage.py test accounts checker admin_api --settings=config.settings.test

# Pytest tests (teeline decomposition)
.venv/Scripts/python.exe -m pytest checker/pytest_tests/
```

---

## Known Issues

| Issue | Location | Description |
|-------|----------|-------------|
| Missing 404 handling | `checker/views.py:SymbolDetailView` | `SymbolRepository.get_by_letter()` raises `Symbol.DoesNotExist` instead of returning HTTP 404 |
| Missing 404 handling | `checker/views.py:AttemptDetailView` | `AttemptRepository.get_by_id()` raises `Attempt.DoesNotExist` instead of returning HTTP 404 |
| Missing 404 handling | `checker/word_views.py:WordDetailView` | `WordRepository.get_by_id()` raises `Word.DoesNotExist` instead of returning HTTP 404 |
| Missing 404 handling | `checker/word_views.py:WordSessionDetailView` | `WordSessionRepository.get_by_id()` raises `WordAttemptSession.DoesNotExist` instead of returning HTTP 404 |

All four issues share the same root cause: repository methods use `Model.objects.get()` which raises `DoesNotExist` on miss. The custom exception handler (`config/exceptions.py`) does not catch `DoesNotExist` — it only handles DRF's `Http404`. Fix: use `get_object_or_404()` in views, or catch `DoesNotExist` in the exception handler.

---

## Design Decisions

1. **Custom job queue over Celery/django-q2**: Simpler dependency graph; jobs use Django ORM with `select_for_update(skip_locked)` for safe concurrency. No Redis/RabbitMQ needed.

2. **Anonymous sessions**: Users can practice without registering. XOR constraint on all user-facing models ensures data belongs to exactly one identity. Session claiming merges data on registration.

3. **Layered architecture**: Views → Services → Repositories → Models. Views handle HTTP concerns, services contain business logic, repositories encapsulate database access. Keeps each layer testable and swappable.

4. **No frontend state library**: App state is simple enough for `useState` + module-scoped variables. Token state lives in `api/client.ts` module scope + localStorage.

5. **Native fetch over axios**: Reduces bundle size. Custom wrapper in `api/client.ts` handles auth headers, token refresh, and error normalization.

6. **Teeline decomposition engine**: Algorithmic word-to-letter decomposition with vowel removal, consonant blends, and R-doubling — allows word practice without hand-curating every word's letter sequence. Curated overrides available via `is_curated` flag.

7. **Notebook-paper aesthetic**: Distinctive visual identity through CSS-only ruled-line overlay, ink-on-paper color palette, and handwriting-adjacent typography. No CSS framework.

---

## References

### Design Specs
- [`docs/superpowers/specs/2026-06-03-teeline-ml-checker-design.md`](superpowers/specs/2026-06-03-teeline-ml-checker-design.md) — Full architecture and feature spec
- [`docs/superpowers/specs/2026-06-03-branding-design-spec.md`](superpowers/specs/2026-06-03-branding-design-spec.md) — Visual identity and design tokens
- [`docs/superpowers/specs/2026-06-04-phase3-4-integration-polish-deploy.md`](superpowers/specs/2026-06-04-phase3-4-integration-polish-deploy.md) — Integration and deployment spec
- [`docs/superpowers/specs/2026-06-05-word-practice-design.md`](superpowers/specs/2026-06-05-word-practice-design.md) — Word practice feature spec
- [`docs/superpowers/specs/2026-06-06-admin-panel-design.md`](superpowers/specs/2026-06-06-admin-panel-design.md) — Admin panel feature spec

### Implementation Plans
- [`docs/superpowers/plans/2026-06-03-phase1-foundation.md`](superpowers/plans/2026-06-03-phase1-foundation.md) — Phase 1: Monorepo, Docker, Django, React scaffold
- [`docs/superpowers/plans/2026-06-04-phase2-ml-training.md`](superpowers/plans/2026-06-04-phase2-ml-training.md) — Phase 2: MobileNetV2 training pipeline
- [`docs/superpowers/plans/2026-06-04-phase3-4-integration-polish-deploy.md`](superpowers/plans/2026-06-04-phase3-4-integration-polish-deploy.md) — Phase 3+4: Integration, polish, deploy
- [`docs/superpowers/plans/2026-06-05-word-practice.md`](superpowers/plans/2026-06-05-word-practice.md) — Word practice implementation plan
- [`docs/superpowers/plans/2026-06-06-admin-panel.md`](superpowers/plans/2026-06-06-admin-panel.md) — Admin panel implementation plan

### External Resources
- `teeline-paper.pdf` — Teeline shorthand reference paper (project root)
- `data/reference/teeline-online/` — Reference data from teeline-online source
