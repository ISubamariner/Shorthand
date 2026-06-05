# Word Practice Feature — Design Spec

**Date:** 2026-06-05
**Status:** Approved
**Goal:** Add word-level Teeline practice alongside existing individual symbol practice. Users pick a word, see its Teeline letter breakdown, and draw each component letter individually (checked by the existing ML model).

---

## Context

The app currently supports practice of 26 individual Teeline letter symbols. Words were explicitly anti-scoped in the original spec. This feature extends the system to word-level practice without requiring a new ML model — it decomposes words into their Teeline letter sequences and reuses the existing single-letter classifier.

---

## Teeline Word Formation Rules

Teeline is spelling-based. Words are reduced to essential consonant outlines by applying these rules in order:

1. **Phonetic substitutions** — ph→F, qu→Q
2. **Silent letter removal** — known silent-letter patterns (silent K in "know", silent W in "write", etc.) via lookup table
3. **Double letter reduction** — consecutive identical letters collapse to one (ll→l, ss→s)
4. **Interior vowel dropping** — vowels (A, E, I, O, U) at the start or end of a word are kept; all interior vowels are dropped
5. **Blend detection** — letter pairs SH, CH, TH, CM, CN, PL are tagged as Teeline blends. Each letter is still practiced individually, but the UI indicates they form a blend.
6. **R-doubling notation** — DR, TR, LR, MR, WR pairs are flagged. In real Teeline the first letter is lengthened rather than writing R separately. The UI indicates this.

Curated word entries override the algorithmic result for exceptions and special outlines.

---

## Data Model

### Word

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK, from TimestampedModel |
| text | CharField(100) | The English word, unique |
| teeline_letters | CharField(50) | Reduced letter sequence, e.g. "PPL" for "people" |
| difficulty | CharField choices | `beginner`, `intermediate`, `advanced` |
| topic | FK → WordTopic | Category for filtering |
| is_curated | BooleanField | True if letter sequence was manually verified |
| created_at, updated_at | DateTime | From TimestampedModel |

### WordTopic

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK, from TimestampedModel |
| name | CharField(50) | Display name, e.g. "Common Words" |
| slug | SlugField | URL-friendly, unique |

### WordAttemptSession

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK, from TimestampedModel |
| word | FK → Word | The word being practiced |
| user | FK → User, nullable | Authenticated user |
| anonymous_session | CharField, nullable | Anonymous session ID |
| status | CharField choices | `in_progress`, `completed`, `abandoned` |
| letters_correct | IntegerField | Count of correct letter attempts |
| letters_total | IntegerField | Total letters in the word |
| points_awarded | IntegerField | Points earned for this session |
| created_at, updated_at | DateTime | From TimestampedModel |

XOR constraint on user/anonymous_session (same pattern as existing Attempt model).

### Attempt (modified)

Add nullable FK `word_session → WordAttemptSession`. When null, the attempt is standalone symbol practice (existing behavior unchanged). When set, the attempt is part of a word practice session. Also add nullable `word_position` (IntegerField) — the index of the letter in the word's decomposition sequence, so results can be mapped back to specific components.

---

## Teeline Decomposition Engine

Module: `backend/checker/teeline.py`

**Input:** English word string
**Output:** List of `TeelineComponent` dicts:

```python
{
    "letter": "P",          # the symbol letter (A-Z)
    "blend_with": None,     # or the other letter in a blend pair
    "is_doubled_for_r": False,
    "position": 0           # index in sequence
}
```

**Priority:** Curated DB entry (if `is_curated=True`) takes precedence over algorithmic decomposition.

**Seed data:** Management command `seed_words` populates ~50-100 common words using the algorithmic engine. Topics seeded: "Common Words", "Journalism", "Business", "Legal". Difficulty assigned by letter count after decomposition: 2-3 letters = beginner, 4-5 = intermediate, 6+ = advanced.

---

## API Endpoints

### New

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/words/` | List words. Query params: `difficulty`, `topic` (slug). Paginated. |
| GET | `/api/words/<id>/` | Word detail with full decomposition (letter components with blend/R metadata) |
| GET | `/api/word-topics/` | List all topics |
| POST | `/api/word-sessions/` | Start a word practice session. Body: `{word_id}` |
| GET | `/api/word-sessions/<id>/` | Poll session status, letters completed so far |
| POST | `/api/word-sessions/<id>/complete/` | Mark session complete, calculate and award points |
| GET | `/api/word-progress/` | Per-word accuracy stats. Query params: `difficulty`, `topic` |

### Modified

| Method | Path | Change |
|--------|------|--------|
| POST | `/api/attempts/` | Accept optional `word_session` UUID and `word_position` integer. When present, link attempt to that session at that position. |

### Unchanged

- `GET /api/leaderboard/` — already reads from `UserStats.total_score`, which word points feed into
- `GET /api/progress/` — remains symbol-only

---

## Scoring

- Completing all letters in a word session: **10 base points**
- All letters correct on first try (no retries): **+5 bonus points**
- Points added to `UserStats.total_score` (shared with symbol practice)
- Word streaks tracked separately in WordAttemptSession queries (consecutive completed sessions with all letters correct)

---

## Frontend

### New: WordPracticePage (`/words`)

**Layout:**
- **Top:** Word selector with difficulty dropdown + topic dropdown filters
- **Middle-left:** Composed reference image — individual letter reference images laid out horizontally, with indicators for blends and R-doubling
- **Middle-right:** Letter breakdown as clickable cards. Each card shows: letter, reference image thumbnail, status (not started / correct / incorrect). Cards are clickable in any order; user can skip known letters.
- **Bottom:** Existing `DrawingCanvas` component (reused as-is). Activates when a letter card is clicked.
- **Flow:** Click letter card → draw on canvas → submit → ML check → card updates → repeat for remaining letters → word summary with points

### Modified: ProgressPage

Add a "Words" tab/section alongside existing symbol progress:
- Per-word accuracy
- Words practiced / words mastered (100% accuracy)
- Filter by difficulty / topic

### Modified: Header

Add "Words" navigation link.

### New TypeScript Types

```typescript
interface WordTopic {
  id: string;
  name: string;
  slug: string;
}

interface TeelineComponent {
  letter: string;
  blend_with: string | null;
  is_doubled_for_r: boolean;
  position: number;
}

interface Word {
  id: string;
  text: string;
  teeline_letters: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  topic: WordTopic;
  components: TeelineComponent[];
}

interface WordSession {
  id: string;
  word: Word;
  status: 'in_progress' | 'completed' | 'abandoned';
  letters_correct: number;
  letters_total: number;
  points_awarded: number;
  letter_results: Record<number, { attempt_id: string; is_correct: boolean }>; // derived from Attempts linked to this session, keyed by component position
}

interface WordProgress {
  word_id: string;
  word_text: string;
  total_sessions: number;
  completed_sessions: number;
  perfect_sessions: number;
  accuracy: number;
}
```

---

## Architecture Alignment

Follows existing layered pattern:

- **Views** → `WordViewSet`, `WordTopicViewSet`, `WordSessionViewSet` (DRF ViewSets)
- **Services** → `word_service.py` — session lifecycle, scoring, decomposition orchestration
- **Repositories** → `word_repository.py` — Word/WordTopic/WordAttemptSession queries
- **Models** → Word, WordTopic, WordAttemptSession
- **Utility** → `teeline.py` — pure decomposition logic, no DB access

Existing `AttemptRepository`, `AttemptSerializer`, and `submit_attempt` service are modified minimally (add optional `word_session` FK).

---

## Anti-Scope

These are NOT part of this feature:

1. **No full-word ML recognition** — letters are checked individually by the existing model
2. **No hand-drawn word reference images** — composed programmatically from letter images
3. **No connected-stroke analysis** — each letter is drawn and checked in isolation
4. **No real-time collaboration or sharing of word lists**
5. **No user-created custom word lists** — words are seeded/admin-managed only
6. **No spaced repetition algorithm** — simple practice, no scheduling
