# Teeline Shorthand ML Checker — Phase 3+4 Design Spec

**Date:** 2026-06-04
**Status:** Approved
**Scope:** Backend integration (finish the one stub), frontend polish (UX flow, progress page, auth UI), deployment (Vercel + Render)

---

## 1. Backend Integration

### Problem

`checker/tasks.py` passes `b""` to the predictor instead of downloading the actual drawing from Supabase Storage. This is the only remaining backend stub.

### Solution

Download the image via HTTP from the public URL stored on the Attempt record.

**Changes:**

- **`storage/client.py`** — add `download(url: str) -> bytes` method that HTTP GETs the public URL and returns raw bytes. Use `urllib.request.urlopen` (stdlib, no new dependency).
- **`checker/tasks.py`** — instantiate `SupabaseStorageClient`, call `download(attempt.image_url)`, pass the result to `predictor.predict(image_bytes)`.

No schema changes. No migrations. The public URL is already stored on the Attempt model.

---

## 2. Frontend Polish — UX Flow

### Canvas reset on retry/next

Pass a `resetKey` number prop to `DrawingCanvas`. Increment it on retry/next. The canvas `useEffect` watches `resetKey` and clears when it changes.

### Better loading state

Replace the plain "Analyzing your drawing..." text with a CSS-animated pulsing card. No new dependencies — pure CSS `@keyframes`.

### Handle failed predictions

When `attempt.status === "failed"`, render an error card with a "Try Again" button. Currently this state falls through and renders nothing.

### Keyboard shortcut

Not included — nice-to-have that adds complexity for minimal benefit. Cut per YAGNI.

---

## 3. Progress Page

### Weakest symbols highlight

Sort symbols with the lowest accuracy to the top and visually flag the bottom 5 with a distinct color (e.g., `var(--accent)` border or background). Symbols with no attempts show at the bottom as "not practiced."

### Practice links

Each symbol row is clickable. Clicking navigates to `/practice?symbol=X` and PracticePage reads the query param to pre-select that symbol.

### Streak counter

Add `current_streak` to the backend progress response. Computed in `AttemptRepository.get_user_progress()` by counting consecutive correct attempts (most recent first) across all symbols. Displayed as a fourth stat card.

### Empty state

When `progress` is empty, show a friendly message: "Start practicing to see your progress here" with a link to the practice page. Hide the stat cards and symbol bars.

---

## 4. Auth UI

### Field-level validation errors

Parse the backend's `fields` error response and display errors next to their respective inputs instead of a single error banner.

### Password requirements hint

Show "Minimum 10 characters" below the password input during registration mode. Visible before submission, not only after failure.

### Visual polish

- Vertically center the auth card on the page
- Improve spacing between form groups
- Add the app name/brand mark at the top

### Success transition

Brief "Welcome, {username}!" message displayed for ~800ms before navigating to the practice page. Uses a simple state flag + `setTimeout`.

---

## 5. Deployment

### Render (backend)

**`render.yaml`** (Blueprint):
- **Web service:** `gunicorn config.wsgi --bind 0.0.0.0:$PORT` using the production Dockerfile
  - Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
  - Pre-deploy command: `python manage.py migrate`
  - Environment: `DJANGO_SETTINGS_MODULE=config.settings.production`, `DATABASE_URL`, `SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_STORAGE_BUCKET`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`
- **Background worker:** Same image, start command `python manage.py qcluster`

### Vercel (frontend)

**`vercel.json`:**
- Framework: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Rewrites: `{ "source": "/(.*)", "destination": "/index.html" }` (SPA catch-all)
- Environment: `VITE_API_URL` pointing to the Render backend URL

### Production settings audit

Verify in `config/settings/production.py`:
- `DEBUG = False`
- `ALLOWED_HOSTS` from env
- `CORS_ALLOWED_ORIGINS` from env
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` all `True`
- `SECRET_KEY` from env with no fallback

### Keepalives

- UptimeRobot: HTTP ping to the Render health endpoint every 5 minutes
- GitHub Actions: cron workflow that pings Supabase every 3 days (a simple `SELECT 1` via the Supabase REST API)

These are manual setup steps, not code changes. Document in a deployment checklist section of the README.

---

## Anti-Scope

Explicitly NOT doing:
- No new dependencies (no `requests`, no `httpx` — use stdlib `urllib`)
- No database migrations
- No password strength meter, OAuth, or "forgot password" flow
- No keyboard shortcuts for the canvas
- No SSR, no service workers, no PWA features
- No CI/CD pipeline — manual deploys
- No monitoring beyond Django logging
