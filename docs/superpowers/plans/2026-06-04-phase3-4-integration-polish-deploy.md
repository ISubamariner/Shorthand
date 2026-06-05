# Phase 3+4 Implementation Plan — Backend Integration, Frontend Polish, Deploy

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the one remaining backend stub (image download before inference), polish the frontend UX (practice flow, progress page, auth UI), and prepare deployment configs for Vercel + Render.

**Architecture:** Backend is Django 5.1 + DRF + django-q2 (Postgres broker). Frontend is Vite + React 18 + TypeScript. ML inference via TFLite model loaded at startup. Supabase for Postgres + Storage. Layered architecture: Views → Services → Repositories → Models.

**Tech Stack:** Django 5.1, DRF, django-q2, TFLite, React 18, TypeScript, Vite, Supabase

---

## File Map

**Backend modifications:**
- `backend/storage/client.py` — add `download()` method
- `backend/checker/tasks.py` — wire real image download before inference
- `backend/checker/repositories.py` — add streak query to `get_user_progress()`
- `backend/checker/serializers.py` — add `current_streak` to `ProgressSerializer`

**Frontend modifications:**
- `frontend/src/components/DrawingCanvas.tsx` — add `resetKey` prop for external clear
- `frontend/src/pages/PracticePage.tsx` — canvas reset, loading card, failed state handling
- `frontend/src/pages/ProgressPage.tsx` — weakest symbols, practice links, streak, empty state
- `frontend/src/pages/LoginPage.tsx` — field-level errors, password hint, success transition
- `frontend/src/types/index.ts` — add `current_streak` to `Progress` type
- `frontend/src/styles/components.css` — pulse animation, new card styles
- `frontend/src/styles/layout.css` — auth centering, progress link styles
- `frontend/src/App.tsx` — add `?symbol=X` query param support to practice route

**New files:**
- `render.yaml` — Render Blueprint
- `frontend/vercel.json` — Vercel config

---

### Task 1: Backend — Image Download from Supabase Storage

**Files:**
- Modify: `backend/storage/client.py`
- Modify: `backend/checker/tasks.py`

- [ ] **Step 1: Add `download()` method to storage client**

In `backend/storage/client.py`, add a `download` method that HTTP GETs the public URL:

```python
import urllib.request

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

    def download(self, url: str) -> bytes:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read()
```

- [ ] **Step 2: Wire real image download in tasks.py**

Replace the stub in `backend/checker/tasks.py`:

```python
import logging

from .models import Attempt
from ml.inference import predictor
from storage.client import SupabaseStorageClient

logger = logging.getLogger(__name__)


def process_and_predict(attempt_id: str):
    try:
        attempt = Attempt.objects.select_related("symbol").get(id=attempt_id)
    except Attempt.DoesNotExist:
        logger.error("Attempt %s not found", attempt_id)
        return

    attempt.status = "processing"
    attempt.save(update_fields=["status"])

    try:
        storage = SupabaseStorageClient()
        image_bytes = storage.download(attempt.image_url)
        predictions = predictor.predict(image_bytes)

        top = predictions[0]
        attempt.predicted_label = top["label"]
        attempt.confidence = top["confidence"]
        attempt.is_correct = attempt.predicted_label == attempt.symbol.letter
        attempt.status = "completed"
        attempt.save(update_fields=["predicted_label", "confidence", "is_correct", "status"])
    except Exception as e:
        logger.exception("Prediction failed for attempt %s", attempt_id)
        attempt.status = "failed"
        attempt.save(update_fields=["status"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/storage/client.py backend/checker/tasks.py
git commit -m "feat: wire real image download from Supabase before TFLite inference"
```

---

### Task 2: Backend — Add Streak to Progress Endpoint

**Files:**
- Modify: `backend/checker/repositories.py`
- Modify: `backend/checker/serializers.py`
- Modify: `backend/checker/views.py`
- Modify: `backend/checker/services.py`

- [ ] **Step 1: Add streak query to repository**

Add a `get_current_streak()` method to `AttemptRepository` in `backend/checker/repositories.py`. This counts consecutive correct attempts from the most recent backward:

```python
@staticmethod
def get_current_streak(user: User) -> int:
    attempts = Attempt.objects.filter(
        user=user, status="completed"
    ).order_by("-created_at").values_list("is_correct", flat=True)

    streak = 0
    for is_correct in attempts:
        if is_correct:
            streak += 1
        else:
            break
    return streak
```

Add this method below the existing `get_user_progress` method.

- [ ] **Step 2: Update service to include streak**

In `backend/checker/services.py`, update `get_user_progress` to return streak:

```python
def get_user_progress(user: User) -> dict:
    return {
        "symbols": AttemptRepository.get_user_progress(user),
        "current_streak": AttemptRepository.get_current_streak(user),
    }
```

- [ ] **Step 3: Update serializer**

In `backend/checker/serializers.py`, add a wrapper serializer for the progress response. Keep `ProgressSerializer` for per-symbol data and add `ProgressResponseSerializer`:

```python
class ProgressResponseSerializer(serializers.Serializer):
    symbols = ProgressSerializer(many=True)
    current_streak = serializers.IntegerField()
```

- [ ] **Step 4: Update view**

In `backend/checker/views.py`, update `ProgressView` to use the new serializer:

```python
class ProgressView(APIView):
    def get(self, request):
        progress = get_user_progress(request.user)
        return Response(ProgressResponseSerializer(progress).data)
```

- [ ] **Step 5: Commit**

```bash
git add backend/checker/repositories.py backend/checker/serializers.py backend/checker/views.py backend/checker/services.py
git commit -m "feat: add current_streak to progress endpoint"
```

---

### Task 3: Frontend — Canvas Reset and Loading/Failed States

**Files:**
- Modify: `frontend/src/components/DrawingCanvas.tsx`
- Modify: `frontend/src/pages/PracticePage.tsx`
- Modify: `frontend/src/styles/components.css`

- [ ] **Step 1: Add `resetKey` prop to DrawingCanvas**

In `frontend/src/components/DrawingCanvas.tsx`, add a `resetKey` prop and a `useEffect` that clears strokes when it changes:

Add to `DrawingCanvasProps`:
```typescript
interface DrawingCanvasProps {
  width?: number;
  height?: number;
  lineWidth?: number;
  resetKey?: number;
  onExport: (imageData: string) => void;
}
```

Add to the component body (after the `strokes` state declaration at line 22):
```typescript
useEffect(() => {
  setStrokes([]);
}, [resetKey]);
```

Add `resetKey` to the destructured props at line 14:
```typescript
export function DrawingCanvas({
  width = 400,
  height = 400,
  lineWidth = 3,
  resetKey,
  onExport,
}: DrawingCanvasProps) {
```

- [ ] **Step 2: Update PracticePage with reset, loading card, and failed state**

Replace the full content of `frontend/src/pages/PracticePage.tsx`:

```tsx
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { DrawingCanvas } from "../components/DrawingCanvas";
import { FeedbackPanel } from "../components/FeedbackPanel";
import { useJobPoller } from "../hooks/useJobPoller";
import type { Attempt, Symbol } from "../types";

export function PracticePage() {
  const [searchParams] = useSearchParams();
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<Symbol | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [canvasResetKey, setCanvasResetKey] = useState(0);

  const fetchAttempt = useCallback((id: string) => api.attempts.get(id), []);
  const poller = useJobPoller<Attempt>(fetchAttempt);

  useEffect(() => {
    api.symbols.list().then((syms) => {
      setSymbols(syms);
      const preselect = searchParams.get("symbol");
      if (preselect) {
        const match = syms.find((s) => s.letter === preselect.toUpperCase());
        if (match) setSelectedSymbol(match);
      }
    }).catch(() => setSubmitError("Failed to load symbols"));
  }, [searchParams]);

  async function handleExport(imageData: string) {
    if (!selectedSymbol) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const attempt = await api.attempts.create({
        symbol_letter: selectedSymbol.letter,
        image_data: imageData,
      });
      poller.startPolling(attempt.id);
    } catch {
      setSubmitError("Failed to submit drawing");
    } finally {
      setSubmitting(false);
    }
  }

  function handleNext() {
    if (!symbols.length || !selectedSymbol) return;
    const idx = symbols.findIndex((s) => s.letter === selectedSymbol.letter);
    const next = symbols[(idx + 1) % symbols.length];
    setSelectedSymbol(next ?? null);
    poller.stopPolling();
    setCanvasResetKey((k) => k + 1);
  }

  function handleRetry() {
    poller.stopPolling();
    setCanvasResetKey((k) => k + 1);
  }

  const currentAttempt = poller.data;
  const isProcessing = submitting || (!poller.isComplete && poller.status !== "");

  return (
    <div className="main">
      {/* Symbol header */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 24 }}>
        {selectedSymbol && (
          <div
            style={{
              width: 56,
              height: 56,
              background: "var(--surface)",
              border: "1.5px solid var(--line)",
              borderRadius: 3,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontSize: 32,
                color: "var(--accent)",
                fontStyle: "italic",
                fontFamily: "var(--font-heading)",
              }}
            >
              {selectedSymbol.letter.toLowerCase()}
            </span>
          </div>
        )}
        <div style={{ flex: 1 }}>
          <div className="eyebrow">
            {selectedSymbol ? "Draw this symbol" : "Select a symbol"}
          </div>
          <div className="section-title">
            {selectedSymbol ? (
              <>
                <span className="accent">{selectedSymbol.letter}</span> — {selectedSymbol.name}
              </>
            ) : (
              "Practice"
            )}
          </div>
        </div>
        <select
          className="select"
          value={selectedSymbol?.letter ?? ""}
          onChange={(e) => {
            const s = symbols.find((sym) => sym.letter === e.target.value);
            setSelectedSymbol(s ?? null);
            poller.stopPolling();
            setCanvasResetKey((k) => k + 1);
          }}
        >
          <option value="">Choose...</option>
          {symbols.map((s) => (
            <option key={s.letter} value={s.letter}>
              {s.letter} — {s.name}
            </option>
          ))}
        </select>
      </div>

      {/* Canvas */}
      {selectedSymbol && <DrawingCanvas onExport={handleExport} resetKey={canvasResetKey} />}

      {/* Processing state */}
      {isProcessing && (
        <div className="card processing-card">
          <div className="processing-pulse" />
          <span>Analyzing your drawing...</span>
        </div>
      )}

      {/* Errors */}
      {submitError && (
        <p style={{ textAlign: "center", color: "var(--accent)", fontSize: 12, marginTop: 16 }}>
          {submitError}
        </p>
      )}
      {poller.error && (
        <p style={{ textAlign: "center", color: "var(--accent)", fontSize: 12, marginTop: 16 }}>
          {poller.error}
        </p>
      )}

      {/* Failed prediction */}
      {currentAttempt && currentAttempt.status === "failed" && (
        <div className="card result-card incorrect" style={{ marginTop: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: 18 }}>!</span>
            <span className="eyebrow" style={{ color: "var(--accent)" }}>
              Analysis failed — please try again
            </span>
          </div>
          <div style={{ display: "flex", justifyContent: "center", marginTop: 12 }}>
            <button className="btn btn-retry" onClick={handleRetry}>
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {currentAttempt && currentAttempt.status === "completed" && selectedSymbol && (
        <div style={{ marginTop: 24 }}>
          <FeedbackPanel
            attempt={currentAttempt}
            expectedLetter={selectedSymbol.letter}
            onNext={handleNext}
            onRetry={handleRetry}
          />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Add CSS for processing card**

Append to `frontend/src/styles/components.css`:

```css
/* Processing state */
.processing-card {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  font-size: 12px;
  color: var(--muted);
}
.processing-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DrawingCanvas.tsx frontend/src/pages/PracticePage.tsx frontend/src/styles/components.css
git commit -m "feat: canvas reset on retry/next, loading card, failed state handling"
```

---

### Task 4: Frontend — Progress Page Polish

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/pages/ProgressPage.tsx`
- Modify: `frontend/src/styles/layout.css`

- [ ] **Step 1: Update Progress type and API client**

In `frontend/src/types/index.ts`, update the `Progress` type and add a response wrapper:

```typescript
export interface ProgressResponse {
  symbols: Progress[];
  current_streak: number;
}
```

Add this after the existing `Progress` interface.

In `frontend/src/api/client.ts`, update the progress API call (line 103-105):

```typescript
progress: {
  get(): Promise<ProgressResponse> {
    return request("/progress/");
  },
},
```

Update the import at line 1:

```typescript
import type { Attempt, ProgressResponse, Symbol, TokenPair, User } from "../types";
```

- [ ] **Step 2: Rewrite ProgressPage**

Replace the full content of `frontend/src/pages/ProgressPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Progress } from "../types";

const ALL_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export function ProgressPage() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState<Progress[]>([]);
  const [streak, setStreak] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.progress
      .get()
      .then((data) => {
        setProgress(data.symbols);
        setStreak(data.current_streak);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const totalAttempts = progress.reduce((sum, p) => sum + p.total, 0);
  const totalCorrect = progress.reduce((sum, p) => sum + p.correct, 0);
  const overallAccuracy = totalAttempts > 0 ? (totalCorrect / totalAttempts) * 100 : 0;

  function getSymbolProgress(letter: string) {
    return progress.find((p) => p.symbol_letter === letter);
  }

  if (loading) {
    return (
      <div className="main">
        <p style={{ textAlign: "center", color: "var(--muted)", fontSize: 12 }}>
          Loading progress...
        </p>
      </div>
    );
  }

  if (totalAttempts === 0) {
    return (
      <div className="main">
        <div className="eyebrow">Your Progress</div>
        <div className="section-title" style={{ marginBottom: 24 }}>
          Symbol <span className="accent">Accuracy</span>
        </div>
        <div className="card" style={{ textAlign: "center", padding: "40px 20px" }}>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}>
            No attempts yet. Start practicing to see your progress here.
          </div>
          <button className="btn btn-primary" onClick={() => navigate("/")}>
            Start Practicing
          </button>
        </div>
      </div>
    );
  }

  const sorted = ALL_LETTERS.map((letter) => ({
    letter,
    progress: getSymbolProgress(letter),
  })).sort((a, b) => {
    const aHas = a.progress && a.progress.total > 0;
    const bHas = b.progress && b.progress.total > 0;
    if (!aHas && !bHas) return 0;
    if (!aHas) return 1;
    if (!bHas) return -1;
    const aPct = a.progress!.correct / a.progress!.total;
    const bPct = b.progress!.correct / b.progress!.total;
    return aPct - bPct;
  });

  const weakestLetters = new Set(
    sorted
      .filter((s) => s.progress && s.progress.total > 0)
      .slice(0, 5)
      .map((s) => s.letter)
  );

  return (
    <div className="main">
      <div className="eyebrow">Your Progress</div>
      <div className="section-title" style={{ marginBottom: 24 }}>
        Symbol <span className="accent">Accuracy</span>
      </div>

      {/* Stats row */}
      <div className="progress-stats">
        <div className="stat-card">
          <div className="stat-value">{totalAttempts}</div>
          <div className="stat-label">Attempts</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{overallAccuracy.toFixed(0)}%</div>
          <div className="stat-label">Accuracy</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{streak}</div>
          <div className="stat-label">Streak</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{progress.length}</div>
          <div className="stat-label">Practiced</div>
        </div>
      </div>

      {/* Weakest symbols callout */}
      {weakestLetters.size > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Focus on these</div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {[...weakestLetters].map((letter) => (
              <button
                key={letter}
                className="btn btn-retry"
                style={{ padding: "4px 10px", fontSize: 11 }}
                onClick={() => navigate(`/?symbol=${letter}`)}
              >
                {letter}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Per-symbol bars */}
      <div className="symbol-bars">
        {sorted.map(({ letter, progress: p }) => {
          const pct = p && p.total > 0 ? (p.correct / p.total) * 100 : 0;
          const hasData = p && p.total > 0;
          const isWeak = weakestLetters.has(letter);
          const barClass = !hasData ? "none" : pct >= 70 ? "good" : "weak";

          return (
            <div
              className={`symbol-bar-row ${hasData ? "clickable" : ""} ${isWeak ? "highlight" : ""}`}
              key={letter}
              onClick={() => hasData && navigate(`/?symbol=${letter}`)}
              role={hasData ? "button" : undefined}
              tabIndex={hasData ? 0 : undefined}
            >
              <div className="symbol-bar-letter">{letter}</div>
              <div className="symbol-bar-track">
                <div
                  className={`symbol-bar-fill ${barClass}`}
                  style={{ width: hasData ? `${Math.max(pct, 3)}%` : "3%" }}
                />
              </div>
              <div className="symbol-bar-pct">
                {hasData ? `${pct.toFixed(0)}%` : "—"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Add CSS for clickable rows and highlights**

Append to `frontend/src/styles/layout.css`:

```css
/* Progress page — clickable rows */
.symbol-bar-row.clickable {
  cursor: pointer;
  border-radius: 2px;
  padding: 2px 4px;
  margin: 0 -4px;
  transition: background 0.15s;
}
.symbol-bar-row.clickable:hover {
  background: var(--surface);
}
.symbol-bar-row.highlight .symbol-bar-letter {
  color: var(--accent);
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/api/client.ts frontend/src/pages/ProgressPage.tsx frontend/src/styles/layout.css
git commit -m "feat: progress page — streak counter, weakest symbols, practice links, empty state"
```

---

### Task 5: Frontend — Auth UI Polish

**Files:**
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/styles/layout.css`

- [ ] **Step 1: Rewrite LoginPage with field-level errors, password hint, and success transition**

Replace the full content of `frontend/src/pages/LoginPage.tsx`:

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";

export function LoginPage() {
  const navigate = useNavigate();
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [welcomeUser, setWelcomeUser] = useState<string | null>(null);

  function clearErrors() {
    setFieldErrors({});
    setGeneralError(null);
  }

  function parseErrors(body: Record<string, unknown>) {
    if (typeof body.fields === "object" && body.fields !== null) {
      const fields = body.fields as Record<string, string | string[]>;
      const parsed: Record<string, string> = {};
      for (const [key, val] of Object.entries(fields)) {
        parsed[key] = Array.isArray(val) ? val[0] : val;
      }
      setFieldErrors(parsed);
    } else if (typeof body.error === "string") {
      setGeneralError(body.error);
    } else {
      setGeneralError("Something went wrong");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearErrors();
    setLoading(true);

    try {
      if (isRegistering) {
        await api.auth.register({ username, email, password });
      }
      await api.auth.login({ username, password });
      setWelcomeUser(username);
      setTimeout(() => navigate("/"), 800);
    } catch (err) {
      if (err instanceof ApiError) {
        parseErrors(err.body as Record<string, unknown>);
      } else {
        setGeneralError("Connection failed");
      }
    } finally {
      setLoading(false);
    }
  }

  if (welcomeUser) {
    return (
      <div className="auth-container auth-centered">
        <div className="auth-card" style={{ textAlign: "center", padding: "48px 28px" }}>
          <div className="section-title">
            Welcome, <span className="accent">{welcomeUser}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container auth-centered">
      <div className="auth-card">
        <div className="logo" style={{ textAlign: "center", fontSize: 24, marginBottom: 24 }}>
          Teeline <span className="accent">ML</span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              className={`input ${fieldErrors.username ? "input-error" : ""}`}
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="your username"
              required
            />
            {fieldErrors.username && (
              <div className="field-error">{fieldErrors.username}</div>
            )}
          </div>

          {isRegistering && (
            <div className="form-group">
              <label>Email</label>
              <input
                className={`input ${fieldErrors.email ? "input-error" : ""}`}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
              {fieldErrors.email && (
                <div className="field-error">{fieldErrors.email}</div>
              )}
            </div>
          )}

          <div className="form-group">
            <label>Password</label>
            <input
              className={`input ${fieldErrors.password ? "input-error" : ""}`}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="your password"
              required
              minLength={10}
            />
            {isRegistering && !fieldErrors.password && (
              <div className="field-hint">Minimum 10 characters</div>
            )}
            {fieldErrors.password && (
              <div className="field-error">{fieldErrors.password}</div>
            )}
          </div>

          {generalError && <div className="form-error">{generalError}</div>}

          <div className="form-actions">
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading
                ? "Please wait..."
                : isRegistering
                  ? "Create Account"
                  : "Login"}
            </button>
          </div>

          <div className="form-footer">
            {isRegistering ? (
              <>
                Already have an account?{" "}
                <a href="#" onClick={(e) => { e.preventDefault(); setIsRegistering(false); clearErrors(); }}>
                  Login
                </a>
              </>
            ) : (
              <>
                Need an account?{" "}
                <a href="#" onClick={(e) => { e.preventDefault(); setIsRegistering(true); clearErrors(); }}>
                  Register
                </a>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add CSS for field errors, hints, and centering**

Append to `frontend/src/styles/layout.css`:

```css
/* Auth centering */
.auth-container.auth-centered {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 80px);
  margin: 0 auto;
}

/* Field-level errors and hints */
.field-error {
  font-size: 11px;
  color: var(--accent);
  margin-top: 4px;
}
.field-hint {
  font-size: 11px;
  color: var(--muted);
  margin-top: 4px;
}
.input-error {
  border-color: var(--accent);
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/LoginPage.tsx frontend/src/styles/layout.css
git commit -m "feat: auth UI — field-level errors, password hint, success transition, centering"
```

---

### Task 6: Deployment — Render Blueprint + Vercel Config

**Files:**
- Create: `render.yaml`
- Create: `frontend/vercel.json`
- Modify: `backend/config/settings/base.py` (add `STATIC_URL` for whitenoise if needed)

- [ ] **Step 1: Create render.yaml**

Create `render.yaml` in the project root:

```yaml
services:
  - type: web
    name: shorthand-api
    runtime: docker
    dockerfilePath: backend/Dockerfile
    dockerContext: backend
    dockerTarget: prod
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: shorthand-db
          property: connectionString
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: SUPABASE_STORAGE_BUCKET
        value: drawings
      - key: ALLOWED_HOSTS
        sync: false
      - key: CORS_ALLOWED_ORIGINS
        sync: false
    buildCommand: ""
    preDeployCommand: "python manage.py migrate"

  - type: worker
    name: shorthand-worker
    runtime: docker
    dockerfilePath: backend/Dockerfile
    dockerContext: backend
    dockerTarget: prod
    dockerCommand: "python manage.py qcluster"
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
      - key: SECRET_KEY
        fromService:
          name: shorthand-api
          type: web
          envVarKey: SECRET_KEY
      - key: DATABASE_URL
        fromDatabase:
          name: shorthand-db
          property: connectionString
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: SUPABASE_STORAGE_BUCKET
        value: drawings

databases:
  - name: shorthand-db
    plan: free
    databaseName: shorthand
    user: shorthand
```

- [ ] **Step 2: Create vercel.json**

Create `frontend/vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

- [ ] **Step 3: Audit production settings**

Verify `backend/config/settings/production.py` has all required settings. The current file is already correct:
- `DEBUG = False` ✓
- `ALLOWED_HOSTS` from env ✓
- `CORS_ALLOWED_ORIGINS` from env ✓
- `SESSION_COOKIE_SECURE = True` ✓
- `CSRF_COOKIE_SECURE = True` ✓
- `SECURE_SSL_REDIRECT = True` ✓
- `SECRET_KEY` from env (inherited from base.py `os.environ["SECRET_KEY"]`) ✓

No changes needed to production settings.

- [ ] **Step 4: Commit**

```bash
git add render.yaml frontend/vercel.json
git commit -m "feat: add Render blueprint and Vercel config for deployment"
```

---

## Post-Implementation Checklist

After all tasks are complete:

1. Run `npm run build` in `frontend/` to verify the frontend builds without errors
2. Run `python manage.py check --deploy` in `backend/` to verify Django deployment checks pass
3. Start docker-compose and test the full flow: register → login → select symbol → draw → submit → see result → check progress
