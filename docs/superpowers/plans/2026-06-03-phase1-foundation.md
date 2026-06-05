# Phase 1: Foundation & Data — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the monorepo, Dockerize all services, build the Django backend with layered architecture (accounts + checker apps), and create a React drawing canvas that uploads to Supabase Storage — producing a working data-collection pipeline.

**Architecture:** Monorepo with `frontend/` (Vite + React + TypeScript) and `backend/` (Django + DRF). Local dev runs via `docker-compose.yml` with 4 services: `db` (Postgres 15), `backend` (Django runserver), `worker` (django-q2 qcluster), `frontend` (Vite dev server). The layered pattern is Views → Services → Repositories → Models in every Django app.

**Tech Stack:** Python 3.11, Django 5.x, DRF, djangorestframework-simplejwt, django-q2, django-cors-headers, supabase-py, Pillow, psycopg2-binary | Node 20, React 18, TypeScript, Vite | Postgres 15 | Docker + Docker Compose

**Anti-Scope (from spec — DO NOT BUILD):** No WebSockets, no i18n, no social features, no payments, no PWA, no custom admin, no CI/CD, no email, no rate limiting, no custom profiles, no Supabase Auth/RLS, no Redis, no state management library, no SSR, no monitoring.

---

## File Map

### Root

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Local dev: db + backend + worker + frontend |
| `.env.example` | Template for all env vars |
| `.gitignore` | Python, Node, Docker, data/ ignores |

### Backend

| File | Purpose |
|------|---------|
| `backend/Dockerfile` | Python 3.11-slim, dev + prod stages |
| `backend/requirements.txt` | All Python deps |
| `backend/manage.py` | Django management entry point |
| `backend/config/__init__.py` | Package marker |
| `backend/config/settings/__init__.py` | Imports from DJANGO_SETTINGS_MODULE |
| `backend/config/settings/base.py` | Shared settings (apps, middleware, DRF, Q_CLUSTER, etc.) |
| `backend/config/settings/local.py` | DEBUG=True, local DB, CORS localhost |
| `backend/config/settings/production.py` | DEBUG=False, DATABASE_URL parsing, Render host |
| `backend/config/urls.py` | Root URL conf: admin + api/ includes |
| `backend/config/wsgi.py` | WSGI entry point |
| `backend/accounts/__init__.py` | Package marker |
| `backend/accounts/models.py` | Empty — uses Django's built-in User |
| `backend/accounts/serializers.py` | RegisterSerializer, UserSerializer |
| `backend/accounts/services.py` | `create_user()` |
| `backend/accounts/views.py` | RegisterView, MeView |
| `backend/accounts/urls.py` | Auth URL patterns |
| `backend/checker/__init__.py` | Package marker |
| `backend/checker/models.py` | Symbol, Attempt models |
| `backend/checker/serializers.py` | SymbolSerializer, AttemptSerializer, AttemptCreateSerializer |
| `backend/checker/repositories.py` | SymbolRepository, AttemptRepository |
| `backend/checker/services.py` | `submit_attempt()`, `get_user_progress()` |
| `backend/checker/tasks.py` | `process_and_predict` django-q2 task (stub for Phase 1) |
| `backend/checker/views.py` | SymbolViewSet, AttemptViewSet, ProgressView |
| `backend/checker/urls.py` | Checker URL patterns |
| `backend/checker/management/__init__.py` | Package marker |
| `backend/checker/management/commands/__init__.py` | Package marker |
| `backend/checker/management/commands/seed_symbols.py` | Seed 26 Teeline symbols |
| `backend/storage/__init__.py` | Package marker |
| `backend/storage/client.py` | Supabase Storage upload/download adapter |
| `backend/ml/__init__.py` | Package marker |
| `backend/ml/inference.py` | TFLite model loader + predict (stub for Phase 1) |
| `backend/ml/preprocessing.py` | Image normalization (stub for Phase 1) |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/Dockerfile` | Node 20-alpine, Vite dev server |
| `frontend/package.json` | React, TypeScript, Vite deps |
| `frontend/tsconfig.json` | TypeScript config |
| `frontend/tsconfig.node.json` | TypeScript config for Vite |
| `frontend/vite.config.ts` | Vite config with API proxy |
| `frontend/index.html` | SPA entry point |
| `frontend/src/main.tsx` | React DOM render |
| `frontend/src/App.tsx` | Router + layout shell |
| `frontend/src/types/index.ts` | Shared TypeScript types |
| `frontend/src/api/client.ts` | Typed fetch wrapper with JWT |
| `frontend/src/components/DrawingCanvas.tsx` | HTML5 Canvas with undo/clear |
| `frontend/src/pages/PracticePage.tsx` | Draw + submit flow (basic for Phase 1) |

### Tests

| File | Purpose |
|------|---------|
| `backend/accounts/tests.py` | Auth registration + login tests |
| `backend/checker/tests.py` | Symbol + Attempt model/view tests |
| `backend/storage/tests.py` | Supabase Storage adapter tests |

---

## Task 1: Root Files — .gitignore, .env.example, docker-compose.yml

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
*.egg
.venv/
venv/

# Django
db.sqlite3
*.log
staticfiles/
mediafiles/

# Node
node_modules/
frontend/dist/

# Environment
.env
.env.local
.env.production

# Data (training images)
data/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker
*.pyc

# OS
.DS_Store
Thumbs.db

# ML models (large, tracked separately if needed)
# backend/ml/model.tflite is committed intentionally

# Docs build artifacts (but not docs themselves)
docs/_build/
```

- [ ] **Step 2: Create .env.example**

```env
# Backend
DJANGO_SETTINGS_MODULE=config.settings.local
SECRET_KEY=change-me-to-a-real-secret-key
DATABASE_URL=postgres://shorthand:shorthand@db:5432/shorthand
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=drawings
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Frontend
VITE_API_URL=http://localhost:8000/api

# Postgres (used by docker-compose db service)
POSTGRES_USER=shorthand
POSTGRES_PASSWORD=shorthand
POSTGRES_DB=shorthand
```

- [ ] **Step 3: Create docker-compose.yml**

```yaml
services:
  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-shorthand}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-shorthand}
      POSTGRES_DB: ${POSTGRES_DB:-shorthand}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-shorthand}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      target: dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.local
    depends_on:
      db:
        condition: service_healthy
    command: python manage.py runserver 0.0.0.0:8000

  worker:
    build:
      context: ./backend
      target: dev
    volumes:
      - ./backend:/app
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.local
    depends_on:
      db:
        condition: service_healthy
    command: python manage.py qcluster

  frontend:
    build:
      context: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: http://localhost:8000/api

volumes:
  pgdata:
```

- [ ] **Step 4: Create .env from example**

```bash
cp .env.example .env
```

- [ ] **Step 5: Commit**

```bash
git init
git add .gitignore .env.example docker-compose.yml
git commit -m "chore: add root config — gitignore, env template, docker-compose"
```

---

## Task 2: Backend Dockerfile + requirements.txt

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```txt
django>=5.1,<5.2
djangorestframework>=3.15,<4.0
djangorestframework-simplejwt>=5.3,<6.0
django-cors-headers>=4.4,<5.0
django-q2>=1.7,<2.0
psycopg2-binary>=2.9,<3.0
pillow>=10.4,<11.0
supabase>=2.9,<3.0
gunicorn>=22.0,<23.0
dj-database-url>=2.2,<3.0
```

Note: `tflite-runtime` is omitted for Phase 1 — it will be added in Phase 3 when the ML model is ready. The inference module will be a stub.

- [ ] **Step 2: Create Dockerfile**

```dockerfile
FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Dev stage — used by docker-compose
FROM base AS dev
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Prod stage — used by Render
FROM base AS prod
RUN python manage.py collectstatic --noinput 2>/dev/null || true
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/Dockerfile backend/requirements.txt
git commit -m "chore: add backend Dockerfile and Python dependencies"
```

---

## Task 3: Django Project Config (settings, urls, wsgi)

**Files:**
- Create: `backend/manage.py`
- Create: `backend/config/__init__.py`
- Create: `backend/config/settings/__init__.py`
- Create: `backend/config/settings/base.py`
- Create: `backend/config/settings/local.py`
- Create: `backend/config/settings/production.py`
- Create: `backend/config/urls.py`
- Create: `backend/config/wsgi.py`

- [ ] **Step 1: Create manage.py**

```python
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create config/__init__.py**

```python
```

(Empty file.)

- [ ] **Step 3: Create config/settings/__init__.py**

```python
```

(Empty file. Django uses `DJANGO_SETTINGS_MODULE` env var to select the settings module.)

- [ ] **Step 4: Create config/settings/base.py**

```python
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-dev-key-change-me")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_q",
    # Local
    "accounts",
    "checker",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# SimpleJWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# django-q2
Q_CLUSTER = {
    "name": "shorthand",
    "workers": 2,
    "timeout": 120,
    "retry": 180,
    "orm": "default",
}

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_STORAGE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "drawings")
```

- [ ] **Step 5: Create config/settings/local.py**

```python
from .base import *  # noqa: F401,F403

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "shorthand",
        "USER": "shorthand",
        "PASSWORD": "shorthand",
        "HOST": "db",
        "PORT": "5432",
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

ALLOWED_HOSTS = ["*"]
```

- [ ] **Step 6: Create config/settings/production.py**

```python
import os

import dj_database_url

from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": dj_database_url.config(conn_max_age=600),
}

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
```

- [ ] **Step 7: Create config/urls.py**

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("checker.urls")),
]
```

- [ ] **Step 8: Create config/wsgi.py**

```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
```

- [ ] **Step 9: Commit**

```bash
git add backend/manage.py backend/config/
git commit -m "feat: add Django project config with split settings"
```

---

## Task 4: Accounts App (Auth)

**Files:**
- Create: `backend/accounts/__init__.py`
- Create: `backend/accounts/models.py`
- Create: `backend/accounts/serializers.py`
- Create: `backend/accounts/services.py`
- Create: `backend/accounts/views.py`
- Create: `backend/accounts/urls.py`
- Test: `backend/accounts/tests.py`

- [ ] **Step 1: Write tests for registration and me endpoint**

Create `backend/accounts/tests.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class RegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user(self):
        response = self.client.post("/api/auth/register/", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_duplicate_username_fails(self):
        User.objects.create_user("testuser", "test@example.com", "testpass123")
        response = self.client.post("/api/auth/register/", {
            "username": "testuser",
            "email": "other@example.com",
            "password": "testpass123",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.create_user("testuser", "test@example.com", "testpass123")

    def test_login_returns_tokens(self):
        response = self.client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "testpass123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class MeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("testuser", "test@example.com", "testpass123")

    def test_me_returns_user_info(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_me_unauthenticated_returns_401(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

- [ ] **Step 2: Create accounts/__init__.py and accounts/models.py**

`backend/accounts/__init__.py`: empty file.

`backend/accounts/models.py`:

```python
# Uses Django's built-in User model — no custom model needed.
```

- [ ] **Step 3: Create accounts/serializers.py**

```python
from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")
```

- [ ] **Step 4: Create accounts/services.py**

```python
from django.contrib.auth.models import User


def create_user(username: str, email: str, password: str) -> User:
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
```

- [ ] **Step 5: Create accounts/views.py**

```python
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserSerializer
from .services import create_user


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.validate()
        user = create_user(**serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
```

- [ ] **Step 6: Create accounts/urls.py**

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", MeView.as_view(), name="me"),
]
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `docker compose run --rm backend python manage.py test accounts -v 2`

Expected: 4 tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/accounts/
git commit -m "feat: add accounts app — register, login (JWT), me endpoint"
```

---

## Task 5: Checker App — Models + Migrations

**Files:**
- Create: `backend/checker/__init__.py`
- Create: `backend/checker/models.py`
- Test: `backend/checker/tests.py` (model tests only in this task)

- [ ] **Step 1: Write model tests**

Create `backend/checker/tests.py`:

```python
import uuid

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Attempt, Symbol


class SymbolModelTest(TestCase):
    def test_create_symbol(self):
        symbol = Symbol.objects.create(
            letter="A",
            name="Alpha",
            reference_image_url="https://example.com/a.png",
        )
        self.assertEqual(str(symbol), "A — Alpha")
        self.assertEqual(symbol.letter, "A")

    def test_letter_is_unique(self):
        Symbol.objects.create(letter="A", name="Alpha")
        with self.assertRaises(Exception):
            Symbol.objects.create(letter="A", name="Alpha duplicate")


class AttemptModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.symbol = Symbol.objects.create(letter="A", name="Alpha")

    def test_create_attempt_defaults_to_pending(self):
        attempt = Attempt.objects.create(
            user=self.user,
            symbol=self.symbol,
            image_url="https://example.com/drawing.png",
        )
        self.assertEqual(attempt.status, "pending")
        self.assertIsInstance(attempt.id, uuid.UUID)
        self.assertIsNone(attempt.predicted_label)
        self.assertIsNone(attempt.confidence)
        self.assertIsNone(attempt.is_correct)
```

- [ ] **Step 2: Create checker/__init__.py and checker/models.py**

`backend/checker/__init__.py`: empty file.

`backend/checker/models.py`:

```python
import uuid

from django.conf import settings
from django.db import models


class Symbol(models.Model):
    letter = models.CharField(max_length=1, unique=True)
    name = models.CharField(max_length=50)
    reference_image_url = models.URLField(blank=True, default="")

    class Meta:
        ordering = ["letter"]

    def __str__(self):
        return f"{self.letter} — {self.name}"


class Attempt(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    symbol = models.ForeignKey(
        Symbol,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    image_url = models.URLField()
    predicted_label = models.CharField(max_length=1, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} → {self.symbol.letter} ({self.status})"
```

- [ ] **Step 3: Run migrations**

```bash
docker compose run --rm backend python manage.py makemigrations accounts checker
docker compose run --rm backend python manage.py migrate
```

- [ ] **Step 4: Run tests**

Run: `docker compose run --rm backend python manage.py test checker.tests.SymbolModelTest checker.tests.AttemptModelTest -v 2`

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/checker/
git commit -m "feat: add checker models — Symbol and Attempt"
```

---

## Task 6: Checker App — Repository Layer

**Files:**
- Create: `backend/checker/repositories.py`
- Modify: `backend/checker/tests.py` (add repository tests)

- [ ] **Step 1: Write repository tests**

Append to `backend/checker/tests.py`:

```python
from .repositories import AttemptRepository, SymbolRepository


class SymbolRepositoryTest(TestCase):
    def setUp(self):
        Symbol.objects.create(letter="A", name="Alpha")
        Symbol.objects.create(letter="B", name="Bravo")

    def test_get_all_returns_all_symbols(self):
        symbols = SymbolRepository.get_all()
        self.assertEqual(len(symbols), 2)

    def test_get_by_letter(self):
        symbol = SymbolRepository.get_by_letter("A")
        self.assertEqual(symbol.name, "Alpha")

    def test_get_by_letter_not_found(self):
        with self.assertRaises(Symbol.DoesNotExist):
            SymbolRepository.get_by_letter("Z")


class AttemptRepositoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.symbol_a = Symbol.objects.create(letter="A", name="Alpha")
        self.symbol_b = Symbol.objects.create(letter="B", name="Bravo")

    def test_create_attempt(self):
        attempt = AttemptRepository.create(
            user=self.user,
            symbol=self.symbol_a,
            image_url="https://example.com/drawing.png",
        )
        self.assertEqual(attempt.status, "pending")
        self.assertEqual(attempt.symbol.letter, "A")

    def test_get_by_user(self):
        AttemptRepository.create(user=self.user, symbol=self.symbol_a, image_url="https://ex.com/1.png")
        AttemptRepository.create(user=self.user, symbol=self.symbol_b, image_url="https://ex.com/2.png")
        attempts = AttemptRepository.get_by_user(self.user)
        self.assertEqual(len(attempts), 2)

    def test_get_user_progress(self):
        a1 = AttemptRepository.create(user=self.user, symbol=self.symbol_a, image_url="https://ex.com/1.png")
        a1.is_correct = True
        a1.status = "completed"
        a1.save()
        a2 = AttemptRepository.create(user=self.user, symbol=self.symbol_a, image_url="https://ex.com/2.png")
        a2.is_correct = False
        a2.status = "completed"
        a2.save()

        progress = AttemptRepository.get_user_progress(self.user)
        entry = next(p for p in progress if p["symbol__letter"] == "A")
        self.assertEqual(entry["total"], 2)
        self.assertEqual(entry["correct"], 1)
```

- [ ] **Step 2: Create checker/repositories.py**

```python
from django.contrib.auth.models import User
from django.db.models import Count, Q, QuerySet

from .models import Attempt, Symbol


class SymbolRepository:
    @staticmethod
    def get_all() -> QuerySet[Symbol]:
        return Symbol.objects.all()

    @staticmethod
    def get_by_letter(letter: str) -> Symbol:
        return Symbol.objects.get(letter=letter.upper())


class AttemptRepository:
    @staticmethod
    def create(user: User, symbol: Symbol, image_url: str) -> Attempt:
        return Attempt.objects.create(
            user=user,
            symbol=symbol,
            image_url=image_url,
        )

    @staticmethod
    def get_by_id(attempt_id, user: User) -> Attempt:
        return Attempt.objects.get(id=attempt_id, user=user)

    @staticmethod
    def get_by_user(user: User) -> QuerySet[Attempt]:
        return Attempt.objects.filter(user=user)

    @staticmethod
    def get_user_progress(user: User) -> list[dict]:
        return list(
            Attempt.objects.filter(user=user, status="completed")
            .values("symbol__letter")
            .annotate(
                total=Count("id"),
                correct=Count("id", filter=Q(is_correct=True)),
            )
            .order_by("symbol__letter")
        )
```

- [ ] **Step 3: Run tests**

Run: `docker compose run --rm backend python manage.py test checker.tests.SymbolRepositoryTest checker.tests.AttemptRepositoryTest -v 2`

Expected: 5 tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/checker/repositories.py backend/checker/tests.py
git commit -m "feat: add checker repository layer — Symbol and Attempt queries"
```

---

## Task 7: Checker App — Serializers

**Files:**
- Create: `backend/checker/serializers.py`

- [ ] **Step 1: Create checker/serializers.py**

```python
from rest_framework import serializers

from .models import Attempt, Symbol


class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = ("id", "letter", "name", "reference_image_url")


class AttemptSerializer(serializers.ModelSerializer):
    symbol_letter = serializers.CharField(source="symbol.letter", read_only=True)

    class Meta:
        model = Attempt
        fields = (
            "id",
            "symbol",
            "symbol_letter",
            "image_url",
            "predicted_label",
            "confidence",
            "is_correct",
            "status",
            "created_at",
        )
        read_only_fields = (
            "id",
            "image_url",
            "predicted_label",
            "confidence",
            "is_correct",
            "status",
            "created_at",
        )


class AttemptCreateSerializer(serializers.Serializer):
    symbol_letter = serializers.CharField(max_length=1)
    image_data = serializers.CharField(help_text="Base64-encoded PNG image data")


class ProgressSerializer(serializers.Serializer):
    symbol_letter = serializers.CharField(source="symbol__letter")
    total = serializers.IntegerField()
    correct = serializers.IntegerField()
    accuracy = serializers.SerializerMethodField()

    def get_accuracy(self, obj):
        if obj["total"] == 0:
            return 0.0
        return round(obj["correct"] / obj["total"], 4)
```

- [ ] **Step 2: Commit**

```bash
git add backend/checker/serializers.py
git commit -m "feat: add checker serializers — Symbol, Attempt, Progress"
```

---

## Task 8: Supabase Storage Adapter

**Files:**
- Create: `backend/storage/__init__.py`
- Create: `backend/storage/client.py`
- Test: `backend/storage/tests.py`

- [ ] **Step 1: Write storage adapter tests**

Create `backend/storage/__init__.py`: empty file.

Create `backend/storage/tests.py`:

```python
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from .client import SupabaseStorageClient


@override_settings(
    SUPABASE_URL="https://test.supabase.co",
    SUPABASE_SERVICE_KEY="test-key",
    SUPABASE_STORAGE_BUCKET="test-bucket",
)
class SupabaseStorageClientTest(TestCase):
    @patch("storage.client.create_client")
    def test_upload_returns_public_url(self, mock_create):
        mock_storage = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.upload.return_value = None
        mock_bucket.get_public_url.return_value = "https://test.supabase.co/storage/v1/object/public/test-bucket/test.png"
        mock_storage.storage.from_.return_value = mock_bucket
        mock_create.return_value = mock_storage

        client = SupabaseStorageClient()
        url = client.upload(b"fake-image-bytes", "test.png", "image/png")

        self.assertEqual(url, "https://test.supabase.co/storage/v1/object/public/test-bucket/test.png")
        mock_bucket.upload.assert_called_once_with("test.png", b"fake-image-bytes", {"content-type": "image/png"})
```

- [ ] **Step 2: Create storage/client.py**

```python
from django.conf import settings
from supabase import create_client


class SupabaseStorageClient:
    def __init__(self):
        self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self._bucket = settings.SUPABASE_STORAGE_BUCKET

    def upload(self, file_bytes: bytes, path: str, content_type: str = "image/png") -> str:
        bucket = self._client.storage.from_(self._bucket)
        bucket.upload(path, file_bytes, {"content-type": content_type})
        return bucket.get_public_url(path)
```

- [ ] **Step 3: Run tests**

Run: `docker compose run --rm backend python manage.py test storage -v 2`

Expected: 1 test passes.

- [ ] **Step 4: Commit**

```bash
git add backend/storage/
git commit -m "feat: add Supabase Storage adapter — upload with public URL"
```

---

## Task 9: Checker App — Service Layer + Tasks (stubs)

**Files:**
- Create: `backend/checker/services.py`
- Create: `backend/checker/tasks.py`
- Create: `backend/ml/__init__.py`
- Create: `backend/ml/inference.py`
- Create: `backend/ml/preprocessing.py`
- Modify: `backend/checker/tests.py` (add service tests)

- [ ] **Step 1: Write service tests**

Append to `backend/checker/tests.py`:

```python
from unittest.mock import patch

from .services import submit_attempt, get_user_progress


class SubmitAttemptServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        Symbol.objects.create(letter="A", name="Alpha")

    @patch("checker.services.SupabaseStorageClient")
    @patch("checker.services.async_task")
    def test_submit_attempt_creates_pending_attempt(self, mock_async, mock_storage_cls):
        mock_storage = mock_storage_cls.return_value
        mock_storage.upload.return_value = "https://example.com/uploaded.png"

        attempt = submit_attempt(
            user=self.user,
            symbol_letter="A",
            image_data="aW1hZ2VkYXRh",  # base64 of "imagedata"
        )

        self.assertEqual(attempt.status, "pending")
        self.assertEqual(attempt.image_url, "https://example.com/uploaded.png")
        mock_async.assert_called_once()

    def test_submit_attempt_invalid_symbol_raises(self):
        with self.assertRaises(Symbol.DoesNotExist):
            submit_attempt(
                user=self.user,
                symbol_letter="Z",
                image_data="aW1hZ2VkYXRh",
            )


class GetUserProgressServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.symbol = Symbol.objects.create(letter="A", name="Alpha")

    def test_returns_progress_list(self):
        attempt = Attempt.objects.create(
            user=self.user, symbol=self.symbol,
            image_url="https://ex.com/1.png",
            is_correct=True, status="completed",
        )
        progress = get_user_progress(self.user)
        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0]["symbol__letter"], "A")
        self.assertEqual(progress[0]["correct"], 1)
```

- [ ] **Step 2: Create ML stubs**

`backend/ml/__init__.py`: empty file.

`backend/ml/inference.py`:

```python
class TFLitePredictor:
    """Stub — real implementation in Phase 3."""

    def predict(self, image_bytes: bytes) -> list[dict]:
        return [
            {"label": "A", "confidence": 0.0},
            {"label": "B", "confidence": 0.0},
            {"label": "C", "confidence": 0.0},
        ]


predictor = TFLitePredictor()
```

`backend/ml/preprocessing.py`:

```python
def preprocess_image(image_bytes: bytes) -> bytes:
    """Stub — real implementation in Phase 3."""
    return image_bytes
```

- [ ] **Step 3: Create checker/services.py**

```python
import base64
import uuid

from django.contrib.auth.models import User
from django_q.tasks import async_task

from storage.client import SupabaseStorageClient
from .repositories import AttemptRepository, SymbolRepository


def submit_attempt(user: User, symbol_letter: str, image_data: str):
    symbol = SymbolRepository.get_by_letter(symbol_letter)

    image_bytes = base64.b64decode(image_data)

    storage = SupabaseStorageClient()
    path = f"attempts/{user.id}/{uuid.uuid4().hex}.png"
    image_url = storage.upload(image_bytes, path)

    attempt = AttemptRepository.create(
        user=user,
        symbol=symbol,
        image_url=image_url,
    )

    async_task("checker.tasks.process_and_predict", str(attempt.id))

    return attempt


def get_user_progress(user: User) -> list[dict]:
    return AttemptRepository.get_user_progress(user)
```

- [ ] **Step 4: Create checker/tasks.py**

```python
from .models import Attempt
from ml.inference import predictor


def process_and_predict(attempt_id: str):
    """Process an attempt: run ML inference and update the record.

    Stub for Phase 1 — always marks as completed with dummy predictions.
    Real ML inference is wired in Phase 3.
    """
    attempt = Attempt.objects.get(id=attempt_id)
    attempt.status = "processing"
    attempt.save(update_fields=["status"])

    predictions = predictor.predict(b"")

    top_prediction = predictions[0]
    attempt.predicted_label = top_prediction["label"]
    attempt.confidence = top_prediction["confidence"]
    attempt.is_correct = attempt.predicted_label == attempt.symbol.letter
    attempt.status = "completed"
    attempt.save(update_fields=["predicted_label", "confidence", "is_correct", "status"])
```

- [ ] **Step 5: Run tests**

Run: `docker compose run --rm backend python manage.py test checker.tests.SubmitAttemptServiceTest checker.tests.GetUserProgressServiceTest -v 2`

Expected: 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/checker/services.py backend/checker/tasks.py backend/checker/tests.py backend/ml/
git commit -m "feat: add checker service layer, async task stub, ML inference stub"
```

---

## Task 10: Checker App — Views + URLs

**Files:**
- Create: `backend/checker/views.py`
- Create: `backend/checker/urls.py`
- Modify: `backend/checker/tests.py` (add view tests)

- [ ] **Step 1: Write view tests**

Append to `backend/checker/tests.py`:

```python
from rest_framework.test import APIClient
from rest_framework import status as http_status


class SymbolViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)
        Symbol.objects.create(letter="A", name="Alpha")
        Symbol.objects.create(letter="B", name="Bravo")

    def test_list_symbols(self):
        response = self.client.get("/api/symbols/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_symbol_by_letter(self):
        response = self.client.get("/api/symbols/A/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["letter"], "A")

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/symbols/")
        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)


class AttemptViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)
        self.symbol = Symbol.objects.create(letter="A", name="Alpha")

    @patch("checker.services.SupabaseStorageClient")
    @patch("checker.services.async_task")
    def test_create_attempt(self, mock_async, mock_storage_cls):
        mock_storage_cls.return_value.upload.return_value = "https://ex.com/uploaded.png"
        response = self.client.post("/api/attempts/", {
            "symbol_letter": "A",
            "image_data": "aW1hZ2VkYXRh",
        })
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")

    def test_list_attempts(self):
        Attempt.objects.create(user=self.user, symbol=self.symbol, image_url="https://ex.com/1.png")
        response = self.client.get("/api/attempts/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_attempts_only_own(self):
        other_user = User.objects.create_user("other", password="testpass123")
        Attempt.objects.create(user=other_user, symbol=self.symbol, image_url="https://ex.com/1.png")
        response = self.client.get("/api/attempts/")
        self.assertEqual(len(response.data["results"]), 0)


class ProgressViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)
        self.symbol = Symbol.objects.create(letter="A", name="Alpha")

    def test_progress_returns_stats(self):
        Attempt.objects.create(
            user=self.user, symbol=self.symbol,
            image_url="https://ex.com/1.png",
            is_correct=True, status="completed",
        )
        response = self.client.get("/api/progress/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["symbol_letter"], "A")
```

- [ ] **Step 2: Create checker/views.py**

```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .repositories import AttemptRepository, SymbolRepository
from .serializers import (
    AttemptCreateSerializer,
    AttemptSerializer,
    ProgressSerializer,
    SymbolSerializer,
)
from .services import get_user_progress, submit_attempt


class SymbolListView(APIView):
    def get(self, request):
        symbols = SymbolRepository.get_all()
        return Response(SymbolSerializer(symbols, many=True).data)


class SymbolDetailView(APIView):
    def get(self, request, letter):
        symbol = SymbolRepository.get_by_letter(letter)
        return Response(SymbolSerializer(symbol).data)


class AttemptListView(APIView):
    def get(self, request):
        attempts = AttemptRepository.get_by_user(request.user)
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(attempts, request)
        return paginator.get_paginated_response(AttemptSerializer(page, many=True).data)

    def post(self, request):
        serializer = AttemptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = submit_attempt(
            user=request.user,
            symbol_letter=serializer.validated_data["symbol_letter"],
            image_data=serializer.validated_data["image_data"],
        )
        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class AttemptDetailView(APIView):
    def get(self, request, pk):
        attempt = AttemptRepository.get_by_id(pk, request.user)
        return Response(AttemptSerializer(attempt).data)


class ProgressView(APIView):
    def get(self, request):
        progress = get_user_progress(request.user)
        return Response(ProgressSerializer(progress, many=True).data)
```

- [ ] **Step 3: Create checker/urls.py**

```python
from django.urls import path

from .views import (
    AttemptDetailView,
    AttemptListView,
    ProgressView,
    SymbolDetailView,
    SymbolListView,
)

urlpatterns = [
    path("symbols/", SymbolListView.as_view(), name="symbol-list"),
    path("symbols/<str:letter>/", SymbolDetailView.as_view(), name="symbol-detail"),
    path("attempts/", AttemptListView.as_view(), name="attempt-list"),
    path("attempts/<uuid:pk>/", AttemptDetailView.as_view(), name="attempt-detail"),
    path("progress/", ProgressView.as_view(), name="progress"),
]
```

- [ ] **Step 4: Run all checker tests**

Run: `docker compose run --rm backend python manage.py test checker -v 2`

Expected: All tests pass (model + repo + service + view tests).

- [ ] **Step 5: Commit**

```bash
git add backend/checker/views.py backend/checker/urls.py backend/checker/tests.py
git commit -m "feat: add checker views and URL routing — symbols, attempts, progress"
```

---

## Task 11: Seed Symbols Management Command

**Files:**
- Create: `backend/checker/management/__init__.py`
- Create: `backend/checker/management/commands/__init__.py`
- Create: `backend/checker/management/commands/seed_symbols.py`

- [ ] **Step 1: Create package init files**

`backend/checker/management/__init__.py`: empty file.
`backend/checker/management/commands/__init__.py`: empty file.

- [ ] **Step 2: Create seed_symbols command**

```python
from django.core.management.base import BaseCommand

from checker.models import Symbol

TEELINE_SYMBOLS = [
    ("A", "Alpha"), ("B", "Bravo"), ("C", "Charlie"), ("D", "Delta"),
    ("E", "Echo"), ("F", "Foxtrot"), ("G", "Golf"), ("H", "Hotel"),
    ("I", "India"), ("J", "Juliet"), ("K", "Kilo"), ("L", "Lima"),
    ("M", "Mike"), ("N", "November"), ("O", "Oscar"), ("P", "Papa"),
    ("Q", "Quebec"), ("R", "Romeo"), ("S", "Sierra"), ("T", "Tango"),
    ("U", "Uniform"), ("V", "Victor"), ("W", "Whiskey"), ("X", "X-ray"),
    ("Y", "Yankee"), ("Z", "Zulu"),
]


class Command(BaseCommand):
    help = "Seed the database with 26 Teeline letter symbols"

    def handle(self, *args, **options):
        created_count = 0
        for letter, name in TEELINE_SYMBOLS:
            _, created = Symbol.objects.get_or_create(
                letter=letter,
                defaults={"name": name},
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} symbols ({26 - created_count} already existed)"))
```

- [ ] **Step 3: Run the command**

```bash
docker compose run --rm backend python manage.py seed_symbols
```

Expected output: `Seeded 26 symbols (0 already existed)`

- [ ] **Step 4: Commit**

```bash
git add backend/checker/management/
git commit -m "feat: add seed_symbols management command — seeds 26 Teeline letters"
```

---

## Task 12: Frontend Scaffold — Dockerfile, Vite, React, TypeScript

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/vite-env.d.ts`

- [ ] **Step 1: Create frontend/Dockerfile**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

- [ ] **Step 2: Create frontend/package.json**

```json
{
  "name": "shorthand-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.6.3",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 3: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: Create frontend/tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 5: Create frontend/vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 6: Create frontend/index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Teeline Shorthand Checker</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7: Create frontend/src/vite-env.d.ts**

```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

- [ ] **Step 8: Create frontend/src/types/index.ts**

```typescript
export interface Symbol {
  id: number;
  letter: string;
  name: string;
  reference_image_url: string;
}

export interface Attempt {
  id: string;
  symbol: number;
  symbol_letter: string;
  image_url: string;
  predicted_label: string | null;
  confidence: number | null;
  is_correct: boolean | null;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
}

export interface Progress {
  symbol_letter: string;
  total: number;
  correct: number;
  accuracy: number;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
}
```

- [ ] **Step 9: Create frontend/src/main.tsx**

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 10: Create frontend/src/App.tsx**

```tsx
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { PracticePage } from "./pages/PracticePage";

export function App() {
  return (
    <BrowserRouter>
      <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
        <h1>Teeline Shorthand Checker</h1>
        <Routes>
          <Route path="/" element={<PracticePage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
```

- [ ] **Step 11: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold frontend — Vite + React + TypeScript + Docker"
```

---

## Task 13: Frontend API Client

**Files:**
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: Create the typed API client**

```typescript
import type { Attempt, Progress, Symbol, TokenPair, User } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

let accessToken: string | null = null;

function setAccessToken(token: string | null) {
  accessToken = token;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown
  ) {
    super(`API error ${status}`);
  }
}

export const api = {
  auth: {
    register(data: { username: string; email: string; password: string }): Promise<User> {
      return request("/auth/register/", { method: "POST", body: JSON.stringify(data) });
    },
    login(data: { username: string; password: string }): Promise<TokenPair> {
      return request<TokenPair>("/auth/login/", { method: "POST", body: JSON.stringify(data) }).then(
        (tokens) => {
          setAccessToken(tokens.access);
          return tokens;
        }
      );
    },
    me(): Promise<User> {
      return request("/auth/me/");
    },
    logout() {
      setAccessToken(null);
    },
  },
  symbols: {
    list(): Promise<Symbol[]> {
      return request("/symbols/");
    },
    get(letter: string): Promise<Symbol> {
      return request(`/symbols/${letter}/`);
    },
  },
  attempts: {
    create(data: { symbol_letter: string; image_data: string }): Promise<Attempt> {
      return request("/attempts/", { method: "POST", body: JSON.stringify(data) });
    },
    list(): Promise<{ results: Attempt[]; count: number }> {
      return request("/attempts/");
    },
    get(id: string): Promise<Attempt> {
      return request(`/attempts/${id}/`);
    },
  },
  progress: {
    get(): Promise<Progress[]> {
      return request("/progress/");
    },
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/
git commit -m "feat: add typed API client with JWT auth"
```

---

## Task 14: Drawing Canvas Component

**Files:**
- Create: `frontend/src/components/DrawingCanvas.tsx`

- [ ] **Step 1: Create DrawingCanvas component**

```tsx
import { useCallback, useEffect, useRef, useState } from "react";

interface DrawingCanvasProps {
  width?: number;
  height?: number;
  lineWidth?: number;
  onExport: (imageData: string) => void;
}

interface Stroke {
  points: Array<{ x: number; y: number }>;
}

export function DrawingCanvas({
  width = 400,
  height = 400,
  lineWidth = 3,
  onExport,
}: DrawingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const currentStrokeRef = useRef<Stroke>({ points: [] });

  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    for (const stroke of strokes) {
      if (stroke.points.length < 2) continue;
      ctx.beginPath();
      ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
      for (let i = 1; i < stroke.points.length; i++) {
        ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
      }
      ctx.stroke();
    }
  }, [strokes, width, height, lineWidth]);

  useEffect(() => {
    redraw();
  }, [redraw]);

  function getPos(e: React.MouseEvent | React.TouchEvent) {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = width / rect.width;
    const scaleY = height / rect.height;

    if ("touches" in e) {
      const touch = e.touches[0];
      return {
        x: (touch.clientX - rect.left) * scaleX,
        y: (touch.clientY - rect.top) * scaleY,
      };
    }
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  }

  function handleStart(e: React.MouseEvent | React.TouchEvent) {
    e.preventDefault();
    setIsDrawing(true);
    const pos = getPos(e);
    currentStrokeRef.current = { points: [pos] };
  }

  function handleMove(e: React.MouseEvent | React.TouchEvent) {
    if (!isDrawing) return;
    e.preventDefault();
    const pos = getPos(e);
    currentStrokeRef.current.points.push(pos);

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx) return;
    const pts = currentStrokeRef.current.points;
    if (pts.length < 2) return;
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(pts[pts.length - 2].x, pts[pts.length - 2].y);
    ctx.lineTo(pts[pts.length - 1].x, pts[pts.length - 1].y);
    ctx.stroke();
  }

  function handleEnd() {
    if (!isDrawing) return;
    setIsDrawing(false);
    setStrokes((prev) => [...prev, { ...currentStrokeRef.current }]);
    currentStrokeRef.current = { points: [] };
  }

  function handleUndo() {
    setStrokes((prev) => prev.slice(0, -1));
  }

  function handleClear() {
    setStrokes([]);
  }

  function handleSubmit() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL("image/png");
    const base64 = dataUrl.split(",")[1];
    onExport(base64);
  }

  return (
    <div>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          border: "2px solid #333",
          borderRadius: 4,
          cursor: "crosshair",
          touchAction: "none",
          maxWidth: "100%",
          height: "auto",
        }}
        onMouseDown={handleStart}
        onMouseMove={handleMove}
        onMouseUp={handleEnd}
        onMouseLeave={handleEnd}
        onTouchStart={handleStart}
        onTouchMove={handleMove}
        onTouchEnd={handleEnd}
      />
      <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
        <button onClick={handleUndo} disabled={strokes.length === 0}>
          Undo
        </button>
        <button onClick={handleClear} disabled={strokes.length === 0}>
          Clear
        </button>
        <button onClick={handleSubmit} disabled={strokes.length === 0}>
          Submit
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/DrawingCanvas.tsx
git commit -m "feat: add DrawingCanvas component — draw, undo, clear, export PNG"
```

---

## Task 15: Practice Page (Basic)

**Files:**
- Create: `frontend/src/pages/PracticePage.tsx`

- [ ] **Step 1: Create PracticePage**

```tsx
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { DrawingCanvas } from "../components/DrawingCanvas";
import type { Attempt, Symbol } from "../types";

export function PracticePage() {
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<Symbol | null>(null);
  const [currentAttempt, setCurrentAttempt] = useState<Attempt | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.symbols.list().then(setSymbols).catch(() => setError("Failed to load symbols"));
  }, []);

  async function handleExport(imageData: string) {
    if (!selectedSymbol) return;
    setSubmitting(true);
    setError(null);
    try {
      const attempt = await api.attempts.create({
        symbol_letter: selectedSymbol.letter,
        image_data: imageData,
      });
      setCurrentAttempt(attempt);
      pollAttempt(attempt.id);
    } catch {
      setError("Failed to submit drawing");
      setSubmitting(false);
    }
  }

  async function pollAttempt(id: string) {
    const maxAttempts = 30;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      try {
        const updated = await api.attempts.get(id);
        setCurrentAttempt(updated);
        if (updated.status === "completed" || updated.status === "failed") {
          setSubmitting(false);
          return;
        }
      } catch {
        break;
      }
    }
    setSubmitting(false);
    setError("Prediction timed out");
  }

  return (
    <div>
      <h2>Practice</h2>

      <div style={{ marginBottom: 16 }}>
        <label>Select a symbol to practice: </label>
        <select
          value={selectedSymbol?.letter ?? ""}
          onChange={(e) => {
            const s = symbols.find((sym) => sym.letter === e.target.value);
            setSelectedSymbol(s ?? null);
            setCurrentAttempt(null);
          }}
        >
          <option value="">-- Choose --</option>
          {symbols.map((s) => (
            <option key={s.letter} value={s.letter}>
              {s.letter} — {s.name}
            </option>
          ))}
        </select>
      </div>

      {selectedSymbol && (
        <>
          <p>Draw the Teeline symbol for: <strong>{selectedSymbol.letter}</strong></p>
          <DrawingCanvas onExport={handleExport} />
        </>
      )}

      {submitting && <p>Analyzing your drawing...</p>}

      {error && <p style={{ color: "red" }}>{error}</p>}

      {currentAttempt && currentAttempt.status === "completed" && (
        <div style={{ marginTop: 16, padding: 16, border: "1px solid #ccc", borderRadius: 4 }}>
          <h3>Result</h3>
          <p>
            Predicted: <strong>{currentAttempt.predicted_label}</strong>
            {" "}({((currentAttempt.confidence ?? 0) * 100).toFixed(1)}% confidence)
          </p>
          <p>
            {currentAttempt.is_correct
              ? "✓ Correct!"
              : `✗ Expected ${selectedSymbol?.letter}`}
          </p>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/PracticePage.tsx
git commit -m "feat: add PracticePage — symbol select, draw, submit, poll results"
```

---

## Task 16: Docker Compose Smoke Test

**Files:** None — this is a verification task.

- [ ] **Step 1: Build and start all services**

```bash
docker compose build
docker compose up -d
```

- [ ] **Step 2: Run backend migrations and seed**

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_symbols
```

Expected: Migration succeeds, 26 symbols seeded.

- [ ] **Step 3: Run backend tests**

```bash
docker compose exec backend python manage.py test -v 2
```

Expected: All tests pass.

- [ ] **Step 4: Verify frontend loads**

Open `http://localhost:5173` in a browser. Verify:
- Page shows "Teeline Shorthand Checker" heading
- Symbol dropdown populates with 26 letters (requires backend to be running and CORS to work)

- [ ] **Step 5: Create superuser for Django admin**

```bash
docker compose exec backend python manage.py createsuperuser
```

Verify Django admin at `http://localhost:8000/admin/`.

- [ ] **Step 6: Commit any fixes**

If any fixes were needed during smoke testing, commit them:

```bash
git add -A
git commit -m "fix: address issues found during Docker Compose smoke test"
```

---

## Task 17: Fix RegisterView Validation Bug

There is a bug in Task 4 Step 5: `RegisterView.post()` calls `serializer.validate()` but should call `serializer.is_valid(raise_exception=True)`. Fix it now.

**Files:**
- Modify: `backend/accounts/views.py`

- [ ] **Step 1: Fix the validation call**

In `backend/accounts/views.py`, change `RegisterView.post()`:

```python
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_user(**serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
```

- [ ] **Step 2: Run account tests to verify**

```bash
docker compose run --rm backend python manage.py test accounts -v 2
```

Expected: All 4 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend/accounts/views.py
git commit -m "fix: use is_valid() instead of validate() in RegisterView"
```
