# Shorthand

A web app for practicing [Teeline shorthand](https://en.wikipedia.org/wiki/Teeline_Shorthand) with ML-powered handwriting recognition. Draw shorthand forms on a canvas and get instant feedback on accuracy.

## Features

- **Letter practice** -- draw individual Teeline letter forms (A-Z) and get ML predictions
- **Grouping practice** -- practice 51 multi-letter groupings (blends, common combos)
- **Word practice** -- write full Teeline outlines for ~95 common words with algorithmic decomposition
- **Special outlines** -- reference outlines for irregular words
- **Anonymous sessions** -- practice without an account; optionally register to keep your history
- **Leaderboard** -- compare accuracy with other users
- **Admin dashboard** -- manage symbols, words, and view system stats

## Tech Stack

| Layer    | Stack                                        |
|----------|----------------------------------------------|
| Frontend | React 18, TypeScript, Vite, Recharts         |
| Backend  | Django 5.1, Django REST Framework, SimpleJWT  |
| ML       | TensorFlow Lite (inference), NumPy            |
| Database | PostgreSQL 15                                 |
| Deploy   | Docker, Render                                |

## Quick Start

### Docker (recommended)

```bash
cp .env.example .env   # if an .env.example exists, otherwise create .env with SECRET_KEY
docker compose up
```

This starts PostgreSQL, the Django API on `localhost:8000`, and the Vite dev server on `localhost:5173`.

### Local Development

**Backend** (requires Python 3.11+ and a running Postgres instance):

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # or source .venv/bin/activate on Unix
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_symbols
python manage.py seed_groupings
python manage.py seed_words
python manage.py seed_special_outlines
python manage.py seed_settings
python manage.py runserver
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000/api` (configurable via `VITE_API_URL`).

## Testing

```bash
# All endpoint smoke tests (75 tests, SQLite in-memory, no Docker needed)
cd backend
python manage.py test tests.test_endpoints --settings=config.settings.test

# Per-app unit tests
python manage.py test accounts checker admin_api --settings=config.settings.test

# Teeline decomposition tests
python -m pytest checker/pytest_tests/test_teeline.py
```

## Architecture

```
backend/
  accounts/       # User registration, login, session claiming
  checker/        # Symbols, attempts, words, practice sessions
  admin_api/      # Staff-only management endpoints
  jobs/           # Custom async job queue (no Celery)
  ml/             # TFLite model loading + inference
  config/         # Django settings (local / test / production)

frontend/
  src/
    api/          # Fetch-based API client with JWT handling
    pages/        # Route-level components
    components/   # Shared UI components
    hooks/        # Custom React hooks (job poller, etc.)
```

The backend follows a **Views -> Services -> Repositories -> Models** layering. Business logic lives in services; ORM queries live in repositories.

Users can practice anonymously (via `X-Session-Token` header) or authenticated (JWT). On login/register, anonymous session data is claimed into the user account.

## Deployment

Deployed on [Render](https://render.com). The `render.yaml` blueprint defines the web service and Postgres database. Seed commands run automatically on every deploy via `preDeployCommand`.

## License

MIT

