# Teeline Shorthand ML Checker — Design Spec

**Date:** 2026-06-03
**Status:** Draft
**Goal:** Full-stack ML app to verify handwritten Teeline shorthand symbols. Mix of learning exercise, practical tool, and portfolio piece.

---

## Architecture

```
Browser → Vercel (Vite + React SPA)
              ↓ REST API
         Render (Docker)
         ├── Django (gunicorn)
         ├── django-q2 worker (qcluster)
         └── TFLite runtime
              ↓
         Supabase
         ├── Postgres (DB + django-q2 broker)
         └── Storage (drawing images)
```

Single Django backend handles auth, DB access, ML inference, and image storage proxy. No separate FastAPI service.

---

## Anti-Scope (DO NOT BUILD)

These features are explicitly excluded. Do not implement, suggest, or plan for them:

1. **No real-time/WebSocket features** — polling for prediction results is sufficient
2. **No multi-language/i18n support** — English only
3. **No social features** — no sharing, leaderboards, or multiplayer
4. **No payment/billing/subscription** — 100% free, no monetization
5. **No mobile app or PWA** — browser-only, no service workers, no offline mode
6. **No admin dashboard beyond Django admin** — no custom admin UI
7. **No CI/CD pipeline** — manual deploys are fine for a personal project
8. **No email service** — no transactional emails, password reset via Django admin only
9. **No rate limiting or API throttling** — single user, not needed
10. **No custom user profiles** — Django's built-in User model is sufficient
11. **No word/phrase recognition** — individual symbol recognition only (26 letters)
12. **No handwriting style adaptation** — model treats all users the same
13. **No model retraining pipeline in production** — retrain locally, redeploy
14. **No Supabase Auth** — Django handles auth exclusively
15. **No Supabase RLS policies** — Django ORM handles data access control
16. **No Redis or external message broker** — django-q2 uses Postgres broker only
17. **No frontend state management library** — React state + context only
18. **No SSR or SSG** — pure client-side SPA
19. **No monitoring/observability beyond Django logging** — no Sentry, no APM
20. **No automated testing infrastructure** — tests are written but no CI runs them

---

## Monorepo Structure

```
Shorthand/
├── docker-compose.yml          # local dev: frontend + backend + worker + db
├── docker-compose.prod.yml     # production overrides
├── .env.example                # template for env vars
├── .gitignore
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   └── client.ts       # typed fetch wrapper for Django API
│       ├── components/
│       │   ├── DrawingCanvas.tsx
│       │   ├── FeedbackPanel.tsx
│       │   ├── SymbolReference.tsx
│       │   └── ProgressChart.tsx
│       ├── pages/
│       │   ├── PracticePage.tsx
│       │   ├── ProgressPage.tsx
│       │   └── LoginPage.tsx
│       └── types/
│           └── index.ts
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # shared settings
│   │   │   ├── local.py        # local Docker dev
│   │   │   └── production.py   # Render production
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── accounts/
│   │   ├── models.py           # uses default Django User
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── checker/
│   │   ├── models.py           # Symbol, Attempt
│   │   ├── serializers.py
│   │   ├── services.py         # business logic
│   │   ├── repositories.py     # data access layer
│   │   ├── tasks.py            # django-q2 async tasks
│   │   ├── views.py
│   │   └── urls.py
│   ├── ml/
│   │   ├── inference.py        # TFLite model loader + predict
│   │   ├── preprocessing.py    # image normalization for inference
│   │   ├── model.tflite        # quantized model (committed to repo)
│   │   └── train/
│   │       ├── train.py        # training script (local/Colab)
│   │       ├── convert.py      # SavedModel → TFLite conversion
│   │       ├── augment.py      # data augmentation utilities
│   │       └── evaluate.py     # confusion matrix, metrics
│   └── storage/
│       └── client.py           # Supabase Storage upload/download adapter
│
├── data/                       # gitignored — local training images
│   ├── raw/                    # hand-drawn samples organized by letter
│   └── augmented/              # augmented training set
│
└── docs/
    └── superpowers/
        └── specs/
```

---

## Layered Architecture

Each Django app follows this pattern:

```
Views (DRF APIViews)
  ↓ delegates to
Services (business logic, orchestration)
  ↓ calls
Repositories (data access, queryset encapsulation)
  ↓ uses
Models (Django ORM — schema only, no business logic)
```

**Views**: Parse HTTP request, call service, return serialized response. No business logic.
**Services**: Orchestrate operations. Example: `submit_attempt()` = validate input → upload image → queue prediction → create Attempt record.
**Repositories**: Encapsulate all ORM queries. Views and services never call `.objects` directly.
**Models**: Define schema and field-level validators only.

---

## Data Models

### Symbol

| Field | Type | Notes |
|-------|------|-------|
| id | AutoField | PK |
| letter | CharField(1) | A-Z, unique |
| name | CharField(50) | Display name |
| reference_image_url | URLField | Supabase Storage URL |

Seeded via Django management command with all 26 Teeline letters.

### Attempt

| Field | Type | Notes |
|-------|------|-------|
| id | UUIDField | PK |
| user | ForeignKey(User) | Django's built-in User |
| symbol | ForeignKey(Symbol) | Target symbol |
| image_url | URLField | Drawing in Supabase Storage |
| predicted_label | CharField(1), nullable | ML prediction result |
| confidence | FloatField, nullable | Prediction confidence 0.0-1.0 |
| is_correct | BooleanField, nullable | predicted == symbol.letter |
| status | CharField | pending → processing → completed / failed |
| created_at | DateTimeField(auto_now_add) | |

---

## API Endpoints

### Auth (accounts app)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register/` | Create account (username, email, password) |
| POST | `/api/auth/login/` | Get JWT token pair |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Current user info |

Auth via `djangorestframework-simplejwt`. Frontend stores access token in React state (lost on page refresh — user re-logs in). Refresh token in httpOnly cookie set by Django.

### Symbols (checker app)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/symbols/` | List all 26 symbols |
| GET | `/api/symbols/{letter}/` | Single symbol + reference image |

### Attempts (checker app)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/attempts/` | Submit drawing (base64 image + target symbol) |
| GET | `/api/attempts/` | User's attempt history (paginated) |
| GET | `/api/attempts/{id}/` | Single attempt + prediction result |

### Progress (checker app)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/progress/` | Per-symbol accuracy, streak, weakest symbols |

---

## Async Tasks (django-q2)

Broker: Postgres (via `django-q2`'s ORM broker — no Redis needed).

| Task | Trigger | Description |
|------|---------|-------------|
| `process_and_predict` | POST /api/attempts/ | Resize image → upload to Supabase Storage → run TFLite inference → update Attempt with results |
| `aggregate_user_stats` | Scheduled (daily) | Pre-compute per-user/per-symbol accuracy for the progress endpoint |
| `export_training_data` | Manual (management command) | Export labeled attempts as CSV for model retraining |

The `POST /api/attempts/` endpoint returns immediately with `status: "pending"`. Frontend polls `GET /api/attempts/{id}/` until `status: "completed"`.

---

## ML Pipeline

### Training (local or Colab)

1. Collect 50-100 hand-drawn samples per symbol via the drawing canvas
2. Augment with Keras ImageDataGenerator: rotation ±15°, width/height shift 10%, zoom 10%. No horizontal flip.
3. MobileNetV2 transfer learning: freeze base, add Dense(128, relu) → Dropout(0.3) → Dense(26, softmax)
4. Fine-tune top layers after initial convergence
5. Target: ≥85% validation accuracy

### Conversion

1. Export as SavedModel
2. Convert to TFLite with INT8 post-training quantization
3. Target: <5MB model file
4. Commit `model.tflite` to repo

### Inference (production)

1. Load TFLite model once at Django startup (module-level singleton in `ml/inference.py`)
2. Preprocess input: resize to 224×224, normalize to [0,1], expand dims
3. Run interpreter.invoke()
4. Return top-3 predictions with confidence scores
5. Expected: <500ms inference on CPU, <200MB RAM

---

## Frontend (Vite + React + TypeScript)

### Pages

**PracticePage**: Select target symbol → draw on canvas → submit → show loading → show results (predicted symbol, confidence bar, reference image comparison, correct/incorrect indicator) → "Try Again" or "Next Symbol".

**ProgressPage**: Per-symbol accuracy bar chart, overall accuracy, current streak, weakest 5 symbols highlighted for focused practice.

**LoginPage**: Simple email/password login + registration forms.

### Components

**DrawingCanvas**: HTML5 Canvas with touch support, undo, clear, pen thickness adjustment. Exports as PNG compressed to <50KB.

**FeedbackPanel**: Shows prediction result — top-3 guesses with confidence bars, correct answer reference image side-by-side.

**ProgressChart**: Bar chart (using a lightweight library like recharts or just CSS bars) showing per-symbol accuracy.

**SymbolReference**: Displays the correct Teeline symbol for comparison.

### API Client

Typed fetch wrapper (`api/client.ts`) that handles JWT token injection, refresh, and error handling. All API calls go through this.

---

## Docker Setup

### docker-compose.yml (local dev)

Services:
- **db**: postgres:15-alpine, port 5432, persistent volume
- **backend**: Django dev server (runserver), port 8000, hot reload via volume mount
- **worker**: django-q2 qcluster process, same image as backend
- **frontend**: Vite dev server, port 5173, hot reload via volume mount

### Dockerfile (backend)

- Base: python:3.11-slim
- Install: tflite-runtime, django, djangorestframework, djangorestframework-simplejwt, django-q2, django-cors-headers, supabase, pillow, gunicorn, psycopg2-binary
- Copy model.tflite
- Production: gunicorn serves HTTP; qcluster runs as a separate Render Background Worker (free tier supports one web service + one worker)

### Dockerfile (frontend)

- Dev: node:20-alpine with vite dev server
- Prod: multi-stage build → nginx serving static files (or just `vite build` output deployed to Vercel)

---

## Environment Variables

```
# Backend
DJANGO_SETTINGS_MODULE=config.settings.local  # or production
SECRET_KEY=<django-secret>
DATABASE_URL=postgres://user:pass@db:5432/shorthand
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=drawings
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Frontend
VITE_API_URL=http://localhost:8000/api
```

---

## Free-Tier Constraints

| Service | Limit | Mitigation |
|---------|-------|------------|
| Render | 512MB RAM, 0.1 CPU | tflite-runtime only (not full TF), ~200MB used |
| Render | Sleeps after 15 min | UptimeRobot ping every 5 min; frontend shows warmup spinner |
| Supabase | 500MB Postgres | More than enough for this use case |
| Supabase | 1GB Storage, 50MB/file | Drawings are ~5-30KB each |
| Supabase | Pauses after 7 days inactive | GitHub Actions ping cron every 3 days |
| Vercel | Personal/non-commercial only | This is a personal learning tool |
| Vercel | 100GB bandwidth/month | SPA is lightweight |

---

## Phases

### Phase 1: Foundation & Data (Week 1-2)
- Monorepo scaffolding + Docker Compose
- Django project with accounts + checker apps (layered architecture)
- Models + migrations
- React drawing canvas (functional, not polished)
- Supabase Storage adapter
- Data collection workflow: draw → upload → label

### Phase 2: ML Model Training (Week 3-4)
- Collect 50-100 samples per symbol via the canvas
- Training script with MobileNetV2 transfer learning
- Data augmentation pipeline
- TFLite conversion + quantization
- Evaluation and confusion matrix

### Phase 3: Backend Integration (Week 5-6)
- TFLite inference service in Django
- django-q2 setup with Postgres broker
- Prediction endpoint (submit → queue → poll)
- Progress/stats endpoint
- Dockerize for Render deployment

### Phase 4: Frontend Polish & Launch (Week 7-8)
- Practice page with full flow (draw → submit → feedback)
- Progress dashboard
- Auth UI (login/register)
- Deploy: Vercel (frontend) + Render (backend)
- Keepalive crons for Render + Supabase
