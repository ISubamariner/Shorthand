# Word Practice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add word-level Teeline practice that decomposes words into component letters, letting users draw each letter individually (checked by the existing ML model).

**Architecture:** New Word/WordTopic/WordAttemptSession models following the existing layered pattern (Views → Services → Repositories → Models). A pure-function Teeline decomposition engine reduces English words to letter sequences. The existing Attempt model gains an optional FK to WordAttemptSession. Frontend gets a new WordPracticePage with letter cards and the existing DrawingCanvas.

**Tech Stack:** Django 5.x, DRF, React 18, TypeScript, Vite

**Spec:** `docs/superpowers/specs/2026-06-05-word-practice-design.md`

---

## File Structure

### Backend — New Files

| File | Responsibility |
|------|---------------|
| `backend/checker/teeline.py` | Pure Teeline decomposition engine (no DB access) |
| `backend/checker/word_repository.py` | Word, WordTopic, WordAttemptSession queries |
| `backend/checker/word_service.py` | Session lifecycle, scoring, decomposition orchestration |
| `backend/checker/word_serializers.py` | DRF serializers for Word, WordTopic, WordSession, WordProgress |
| `backend/checker/word_views.py` | API views for word endpoints |
| `backend/checker/management/commands/seed_words.py` | Seed ~80 common words with topics and difficulties |
| `backend/checker/tests/test_teeline.py` | Unit tests for decomposition engine |
| `backend/checker/tests/__init__.py` | Package init |

### Backend — Modified Files

| File | Change |
|------|--------|
| `backend/checker/models.py` | Add Word, WordTopic, WordAttemptSession models |
| `backend/checker/repositories.py` | Add `word_session`/`word_position` params to `AttemptRepository.create()` |
| `backend/checker/serializers.py` | Add `word_session`/`word_position` to `AttemptCreateSerializer` |
| `backend/checker/services.py` | Pass `word_session`/`word_position` through `submit_attempt()` |
| `backend/checker/views.py` | Pass `word_session`/`word_position` from request through to service |
| `backend/checker/urls.py` | Add word endpoint URL patterns |

### Frontend — New Files

| File | Responsibility |
|------|---------------|
| `frontend/src/pages/WordPracticePage.tsx` | Word practice page with letter cards + canvas |
| `frontend/src/components/LetterCard.tsx` | Individual letter card component (clickable, shows status) |
| `frontend/src/components/WordReference.tsx` | Composed word reference from letter images |

### Frontend — Modified Files

| File | Change |
|------|--------|
| `frontend/src/types/index.ts` | Add WordTopic, TeelineComponent, Word, WordSession, WordProgress types |
| `frontend/src/api/client.ts` | Add words, wordSessions, wordProgress API methods |
| `frontend/src/App.tsx` | Add `/words` route |
| `frontend/src/components/Header.tsx` | Add "Words" tab |
| `frontend/src/pages/ProgressPage.tsx` | Add word progress section |

---

### Task 1: Teeline Decomposition Engine

**Files:**
- Create: `backend/checker/teeline.py`
- Create: `backend/checker/tests/__init__.py`
- Create: `backend/checker/tests/test_teeline.py`

- [ ] **Step 1: Create test file with decomposition tests**

Create `backend/checker/tests/__init__.py` (empty file).

Create `backend/checker/tests/test_teeline.py`:

```python
from checker.teeline import decompose


class TestPhoneticSubstitutions:
    def test_ph_becomes_f(self):
        result = decompose("phase")
        letters = "".join(c["letter"] for c in result)
        assert "F" in letters
        assert "P" not in letters or "H" not in letters

    def test_qu_becomes_q(self):
        result = decompose("queen")
        letters = "".join(c["letter"] for c in result)
        assert letters[0] == "Q"
        assert "U" not in letters


class TestSilentLetters:
    def test_silent_k_in_know(self):
        result = decompose("know")
        letters = "".join(c["letter"] for c in result)
        assert letters[0] == "N"

    def test_silent_w_in_write(self):
        result = decompose("write")
        letters = "".join(c["letter"] for c in result)
        assert letters[0] == "R"


class TestDoubleLetterReduction:
    def test_double_l(self):
        result = decompose("tall")
        letters = "".join(c["letter"] for c in result)
        assert letters.count("L") == 1

    def test_double_s(self):
        result = decompose("pass")
        letters = "".join(c["letter"] for c in result)
        assert letters.count("S") == 1


class TestInteriorVowelDropping:
    def test_keeps_leading_vowel(self):
        result = decompose("about")
        letters = "".join(c["letter"] for c in result)
        assert letters[0] == "A"

    def test_keeps_trailing_vowel(self):
        result = decompose("go")
        letters = "".join(c["letter"] for c in result)
        assert letters[-1] == "O"

    def test_drops_interior_vowels(self):
        result = decompose("people")
        letters = "".join(c["letter"] for c in result)
        assert letters == "PPL"

    def test_single_consonant_word(self):
        result = decompose("be")
        letters = "".join(c["letter"] for c in result)
        assert letters == "B"


class TestBlendDetection:
    def test_sh_blend(self):
        result = decompose("ship")
        s_comp = next(c for c in result if c["letter"] == "S")
        h_comp = next(c for c in result if c["letter"] == "H")
        assert s_comp["blend_with"] == "H"
        assert h_comp["blend_with"] == "S"

    def test_th_blend(self):
        result = decompose("the")
        t_comp = next(c for c in result if c["letter"] == "T")
        assert t_comp["blend_with"] == "H"


class TestRDoubling:
    def test_dr_doubling(self):
        result = decompose("drive")
        d_comp = next(c for c in result if c["letter"] == "D")
        assert d_comp["is_doubled_for_r"] is True

    def test_tr_doubling(self):
        result = decompose("tree")
        t_comp = next(c for c in result if c["letter"] == "T")
        assert t_comp["is_doubled_for_r"] is True


class TestPositionIndexing:
    def test_positions_sequential(self):
        result = decompose("the")
        positions = [c["position"] for c in result]
        assert positions == list(range(len(result)))


class TestComponentStructure:
    def test_returns_list_of_dicts(self):
        result = decompose("go")
        assert isinstance(result, list)
        assert all(isinstance(c, dict) for c in result)
        assert all("letter" in c for c in result)
        assert all("blend_with" in c for c in result)
        assert all("is_doubled_for_r" in c for c in result)
        assert all("position" in c for c in result)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest checker/tests/test_teeline.py -v`
Expected: ImportError — `checker.teeline` does not exist.

- [ ] **Step 3: Implement the decomposition engine**

Create `backend/checker/teeline.py`:

```python
VOWELS = set("AEIOU")

SILENT_LETTER_PATTERNS = {
    "KN": "N",
    "WR": "R",
    "GN": "N",
    "PN": "N",
    "MN": "N",
    "MB": "M",
}

PHONETIC_SUBS = [
    ("PH", "F"),
    ("QU", "Q"),
]

BLENDS = {"SH", "CH", "TH", "CM", "CN", "PL"}

R_DOUBLE_PREFIXES = {"D", "T", "L", "M", "W"}


def decompose(word: str) -> list[dict]:
    text = word.upper().strip()

    for old, new in PHONETIC_SUBS:
        text = text.replace(old, new)

    for pattern, replacement in SILENT_LETTER_PATTERNS.items():
        if text.startswith(pattern):
            text = replacement + text[len(pattern):]

    reduced = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == text[i + 1]:
            reduced.append(text[i])
            i += 2
            while i < len(text) and text[i] == text[i - 1]:
                i += 1
        else:
            reduced.append(text[i])
            i += 1
    text = "".join(reduced)

    if len(text) > 2:
        first = text[0]
        last = text[-1]
        middle = "".join(c for c in text[1:-1] if c not in VOWELS)
        text = first + middle + last
    elif len(text) == 2:
        if text[0] in VOWELS and text[1] in VOWELS:
            text = text[0]
        elif text[1] in VOWELS and text[0] not in VOWELS:
            text = text[0]

    blend_pairs = set()
    for idx in range(len(text) - 1):
        pair = text[idx] + text[idx + 1]
        if pair in BLENDS:
            blend_pairs.add((idx, idx + 1))

    r_doubled = set()
    for idx in range(len(text) - 1):
        if text[idx] in R_DOUBLE_PREFIXES and text[idx + 1] == "R":
            r_doubled.add(idx)

    components = []
    for idx, letter in enumerate(text):
        blend_with = None
        for a, b in blend_pairs:
            if idx == a:
                blend_with = text[b]
            elif idx == b:
                blend_with = text[a]

        components.append({
            "letter": letter,
            "blend_with": blend_with,
            "is_doubled_for_r": idx in r_doubled,
            "position": idx,
        })

    return components


def decompose_to_letters(word: str) -> str:
    return "".join(c["letter"] for c in decompose(word))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest checker/tests/test_teeline.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/checker/teeline.py backend/checker/tests/__init__.py backend/checker/tests/test_teeline.py
git commit -m "feat: add Teeline decomposition engine with tests"
```

---

### Task 2: Word Data Models

**Files:**
- Modify: `backend/checker/models.py`

- [ ] **Step 1: Add WordTopic, Word, and WordAttemptSession models**

Append to `backend/checker/models.py` after the `UserStats` class:

```python
class WordTopic(TimestampedModel):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Word(TimestampedModel):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"

    text = models.CharField(max_length=100, unique=True)
    teeline_letters = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=12, choices=Difficulty.choices)
    topic = models.ForeignKey(
        WordTopic,
        on_delete=models.CASCADE,
        related_name="words",
    )
    is_curated = models.BooleanField(default=False)

    class Meta:
        ordering = ["text"]

    def __str__(self):
        return f"{self.text} → {self.teeline_letters}"


class WordAttemptSession(TimestampedModel):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        ABANDONED = "abandoned"

    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="word_sessions",
        null=True,
        blank=True,
    )
    anonymous_session = models.ForeignKey(
        "accounts.AnonymousSession",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="word_sessions",
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    letters_correct = models.IntegerField(default=0)
    letters_total = models.IntegerField(default=0)
    points_awarded = models.IntegerField(default=0)

    objects = UserScopedManager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, anonymous_session__isnull=True)
                    | models.Q(user__isnull=True, anonymous_session__isnull=False)
                ),
                name="word_session_owner_xor",
            ),
        ]

    def __str__(self):
        owner = self.user.username if self.user else f"Session {str(self.anonymous_session.session_token)[:8]}"
        return f"{owner} → {self.word.text} ({self.status})"
```

- [ ] **Step 2: Add word_session and word_position FKs to Attempt model**

In `backend/checker/models.py`, add these two fields to the `Attempt` class after the `symbol` field:

```python
    word_session = models.ForeignKey(
        "WordAttemptSession",
        on_delete=models.CASCADE,
        related_name="attempts",
        null=True,
        blank=True,
    )
    word_position = models.IntegerField(null=True, blank=True)
```

- [ ] **Step 3: Generate and apply migration**

Run: `cd backend && python manage.py makemigrations checker && python manage.py migrate`
Expected: Migration created and applied successfully.

- [ ] **Step 4: Commit**

```bash
git add backend/checker/models.py backend/checker/migrations/
git commit -m "feat: add Word, WordTopic, WordAttemptSession models"
```

---

### Task 3: Seed Words Command

**Files:**
- Create: `backend/checker/management/commands/seed_words.py`

- [ ] **Step 1: Create the seed_words management command**

Create `backend/checker/management/commands/seed_words.py`:

```python
from django.core.management.base import BaseCommand

from checker.models import Word, WordTopic
from checker.teeline import decompose_to_letters

TOPICS = [
    ("Common Words", "common"),
    ("Journalism", "journalism"),
    ("Business", "business"),
    ("Legal", "legal"),
]

WORDS = {
    "common": [
        "the", "be", "to", "of", "and", "in", "that", "have", "it", "for",
        "not", "on", "with", "he", "do", "at", "but", "we", "his", "from",
        "they", "she", "or", "an", "will", "my", "all", "would", "there",
        "their", "what", "so", "up", "out", "if", "about", "who", "get",
        "which", "go", "me", "when", "can", "no", "just", "him", "know",
        "take", "people", "into",
    ],
    "journalism": [
        "report", "source", "quote", "press", "editor", "publish", "article",
        "deadline", "interview", "breaking", "headline", "column", "feature",
        "broadcast", "journalist",
    ],
    "business": [
        "market", "profit", "invest", "budget", "contract", "manage",
        "strategy", "revenue", "client", "meeting", "project", "target",
        "growth", "finance", "company",
    ],
    "legal": [
        "court", "judge", "law", "trial", "evidence", "witness", "verdict",
        "appeal", "charge", "counsel", "defend", "guilty", "sentence",
        "statute", "justice",
    ],
}


def _difficulty(teeline_letters: str) -> str:
    length = len(teeline_letters)
    if length <= 3:
        return "beginner"
    elif length <= 5:
        return "intermediate"
    return "advanced"


class Command(BaseCommand):
    help = "Seed the database with common Teeline practice words"

    def handle(self, *args, **options):
        topic_objects = {}
        for name, slug in TOPICS:
            topic, _ = WordTopic.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )
            topic_objects[slug] = topic

        created_count = 0
        for topic_slug, words in WORDS.items():
            topic = topic_objects[topic_slug]
            for word_text in words:
                teeline = decompose_to_letters(word_text)
                difficulty = _difficulty(teeline)
                _, created = Word.objects.get_or_create(
                    text=word_text,
                    defaults={
                        "teeline_letters": teeline,
                        "difficulty": difficulty,
                        "topic": topic,
                        "is_curated": False,
                    },
                )
                if created:
                    created_count += 1

        total = sum(len(w) for w in WORDS.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} words ({total - created_count} already existed)"
            )
        )
```

- [ ] **Step 2: Run the seed command**

Run: `cd backend && python manage.py seed_words`
Expected: "Seeded NN words (0 already existed)"

- [ ] **Step 3: Commit**

```bash
git add backend/checker/management/commands/seed_words.py
git commit -m "feat: add seed_words management command with ~95 common words"
```

---

### Task 4: Word Repository

**Files:**
- Create: `backend/checker/word_repository.py`
- Modify: `backend/checker/repositories.py`

- [ ] **Step 1: Create the word repository**

Create `backend/checker/word_repository.py`:

```python
from django.contrib.auth.models import User
from django.db.models import Count, F, Q, QuerySet

from accounts.models import AnonymousSession

from .models import Word, WordAttemptSession, WordTopic


class WordTopicRepository:
    @staticmethod
    def get_all() -> QuerySet[WordTopic]:
        return WordTopic.objects.all()


class WordRepository:
    @staticmethod
    def get_all(
        difficulty: str | None = None,
        topic_slug: str | None = None,
    ) -> QuerySet[Word]:
        qs = Word.objects.select_related("topic")
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if topic_slug:
            qs = qs.filter(topic__slug=topic_slug)
        return qs

    @staticmethod
    def get_by_id(word_id) -> Word:
        return Word.objects.select_related("topic").get(id=word_id)


class WordSessionRepository:
    @staticmethod
    def _owner_filter(
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> Q:
        if user:
            return Q(user=user)
        elif session:
            return Q(anonymous_session=session)
        raise ValueError("Either user or session must be provided")

    @staticmethod
    def create(
        word: Word,
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> WordAttemptSession:
        return WordAttemptSession.objects.create(
            word=word,
            user=user,
            anonymous_session=session,
            letters_total=len(word.teeline_letters),
        )

    @staticmethod
    def get_by_id(
        session_id,
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> WordAttemptSession:
        owner_filter = WordSessionRepository._owner_filter(user, session)
        return WordAttemptSession.objects.select_related("word", "word__topic").get(
            Q(id=session_id) & owner_filter
        )

    @staticmethod
    def get_progress(
        user: User | None = None,
        session: AnonymousSession | None = None,
        difficulty: str | None = None,
        topic_slug: str | None = None,
    ) -> list[dict]:
        owner_filter = WordSessionRepository._owner_filter(user, session)
        qs = WordAttemptSession.objects.filter(
            owner_filter,
            status=WordAttemptSession.Status.COMPLETED,
        )
        if difficulty:
            qs = qs.filter(word__difficulty=difficulty)
        if topic_slug:
            qs = qs.filter(word__topic__slug=topic_slug)

        return list(
            qs.values("word__id", "word__text")
            .annotate(
                total_sessions=Count("id"),
                perfect_sessions=Count(
                    "id",
                    filter=Q(letters_correct=F("letters_total")),
                ),
            )
            .order_by("word__text")
        )

    @staticmethod
    def transfer_session_to_user(
        anon_session: AnonymousSession,
        user: User,
    ) -> int:
        count = WordAttemptSession.objects.filter(
            anonymous_session=anon_session
        ).update(user=user, anonymous_session=None)
        return count
```

- [ ] **Step 2: Modify AttemptRepository.create() to accept word_session and word_position**

In `backend/checker/repositories.py`, update the `create` method of `AttemptRepository`:

```python
    @staticmethod
    def create(
        symbol: Symbol,
        user: User | None = None,
        session: AnonymousSession | None = None,
        image_data: bytes = b"",
        word_session=None,
        word_position: int | None = None,
    ) -> Attempt:
        return Attempt.objects.create(
            user=user,
            anonymous_session=session,
            symbol=symbol,
            image_data=image_data,
            word_session=word_session,
            word_position=word_position,
        )
```

- [ ] **Step 3: Commit**

```bash
git add backend/checker/word_repository.py backend/checker/repositories.py
git commit -m "feat: add word repository and update AttemptRepository for word sessions"
```

---

### Task 5: Word Service

**Files:**
- Create: `backend/checker/word_service.py`
- Modify: `backend/checker/services.py`

- [ ] **Step 1: Create the word service**

Create `backend/checker/word_service.py`:

```python
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest

from accounts.models import AnonymousSession

from .models import UserStats, WordAttemptSession
from .teeline import decompose
from .word_repository import WordRepository, WordSessionRepository


def get_word_components(word_id):
    word = WordRepository.get_by_id(word_id)
    if word.is_curated:
        return [
            {
                "letter": letter,
                "blend_with": None,
                "is_doubled_for_r": False,
                "position": idx,
            }
            for idx, letter in enumerate(word.teeline_letters)
        ]
    return decompose(word.text)


def start_session(
    word_id,
    user: User | None = None,
    session: AnonymousSession | None = None,
) -> WordAttemptSession:
    word = WordRepository.get_by_id(word_id)
    return WordSessionRepository.create(word=word, user=user, session=session)


def complete_session(
    session_id,
    user: User | None = None,
    session: AnonymousSession | None = None,
) -> WordAttemptSession:
    word_session = WordSessionRepository.get_by_id(
        session_id, user=user, session=session
    )

    completed_attempts = word_session.attempts.filter(status="completed")
    correct_count = completed_attempts.filter(is_correct=True).count()
    total_letters = word_session.letters_total

    all_correct_first_try = (
        correct_count == total_letters
        and completed_attempts.count() == total_letters
    )

    points = 10
    if all_correct_first_try:
        points += 5

    word_session.letters_correct = correct_count
    word_session.points_awarded = points
    word_session.status = WordAttemptSession.Status.COMPLETED
    word_session.save(update_fields=[
        "letters_correct", "points_awarded", "status", "updated_at",
    ])

    _award_points(points, user=user, session=session)

    return word_session


def _award_points(
    points: int,
    user: User | None = None,
    session: AnonymousSession | None = None,
):
    with transaction.atomic():
        if user:
            stats, _ = UserStats.objects.select_for_update().get_or_create(user=user)
        elif session:
            stats, _ = UserStats.objects.select_for_update().get_or_create(
                anonymous_session=session
            )
        else:
            return

        stats.total_score = F("total_score") + points
        stats.save(update_fields=["total_score"])


def get_session_detail(
    session_id,
    user: User | None = None,
    session: AnonymousSession | None = None,
) -> dict:
    word_session = WordSessionRepository.get_by_id(
        session_id, user=user, session=session
    )

    letter_results = {}
    for attempt in word_session.attempts.filter(status="completed"):
        if attempt.word_position is not None:
            letter_results[attempt.word_position] = {
                "attempt_id": str(attempt.id),
                "is_correct": attempt.is_correct,
            }

    return {
        "session": word_session,
        "letter_results": letter_results,
    }


def get_word_progress(
    user: User | None = None,
    session: AnonymousSession | None = None,
    difficulty: str | None = None,
    topic_slug: str | None = None,
) -> list[dict]:
    owner_filter = WordSessionRepository._owner_filter(user, session)
    completed = WordAttemptSession.objects.filter(
        owner_filter,
        status=WordAttemptSession.Status.COMPLETED,
    )
    if difficulty:
        completed = completed.filter(word__difficulty=difficulty)
    if topic_slug:
        completed = completed.filter(word__topic__slug=topic_slug)

    word_ids = completed.values_list("word_id", flat=True).distinct()
    results = []
    for word_id in word_ids:
        sessions = completed.filter(word_id=word_id)
        total = sessions.count()
        perfect = sessions.filter(letters_correct=F("letters_total")).count()
        word = sessions.first().word
        results.append({
            "word_id": str(word.id),
            "word_text": word.text,
            "total_sessions": total,
            "completed_sessions": total,
            "perfect_sessions": perfect,
            "accuracy": round(perfect / total, 4) if total > 0 else 0.0,
        })

    return sorted(results, key=lambda r: r["word_text"])
```

- [ ] **Step 2: Update submit_attempt to pass word_session and word_position**

In `backend/checker/services.py`, update the `submit_attempt` function signature and the `AttemptRepository.create` call:

```python
def submit_attempt(
    symbol_letter: str,
    image_data: str,
    user: User | None = None,
    session: AnonymousSession | None = None,
    word_session=None,
    word_position: int | None = None,
):
    symbol = SymbolRepository.get_by_letter(symbol_letter)

    image_bytes = base64.b64decode(image_data)

    attempt = AttemptRepository.create(
        symbol=symbol,
        user=user,
        session=session,
        image_data=image_bytes,
        word_session=word_session,
        word_position=word_position,
    )

    JobRepository.enqueue(
        job_type="predict",
        payload={"attempt_id": str(attempt.id)},
        user=user,
        correlation_key=f"predict:{attempt.id}",
    )

    return attempt
```

- [ ] **Step 3: Update claim_anonymous_session to transfer word sessions**

In `backend/checker/services.py`, add the word session transfer after the attempt transfer. Add the import at the top:

```python
from .word_repository import WordSessionRepository
```

Then in `claim_anonymous_session`, after `attempts_count = AttemptRepository.transfer_session_to_user(session, user)`:

```python
    WordSessionRepository.transfer_session_to_user(session, user)
```

- [ ] **Step 4: Commit**

```bash
git add backend/checker/word_service.py backend/checker/services.py
git commit -m "feat: add word service and wire word_session through submit_attempt"
```

---

### Task 6: Word Serializers

**Files:**
- Create: `backend/checker/word_serializers.py`
- Modify: `backend/checker/serializers.py`

- [ ] **Step 1: Create word serializers**

Create `backend/checker/word_serializers.py`:

```python
from rest_framework import serializers

from .models import Word, WordAttemptSession, WordTopic


class WordTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordTopic
        fields = ("id", "name", "slug")


class TeelineComponentSerializer(serializers.Serializer):
    letter = serializers.CharField()
    blend_with = serializers.CharField(allow_null=True)
    is_doubled_for_r = serializers.BooleanField()
    position = serializers.IntegerField()


class WordSerializer(serializers.ModelSerializer):
    topic = WordTopicSerializer(read_only=True)
    components = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = ("id", "text", "teeline_letters", "difficulty", "topic", "components")

    def get_components(self, obj):
        from .teeline import decompose

        if obj.is_curated:
            components = [
                {
                    "letter": letter,
                    "blend_with": None,
                    "is_doubled_for_r": False,
                    "position": idx,
                }
                for idx, letter in enumerate(obj.teeline_letters)
            ]
        else:
            components = decompose(obj.text)
        return TeelineComponentSerializer(components, many=True).data


class WordListSerializer(serializers.ModelSerializer):
    topic = WordTopicSerializer(read_only=True)

    class Meta:
        model = Word
        fields = ("id", "text", "teeline_letters", "difficulty", "topic")


class WordSessionCreateSerializer(serializers.Serializer):
    word_id = serializers.UUIDField()


class LetterResultSerializer(serializers.Serializer):
    attempt_id = serializers.CharField()
    is_correct = serializers.BooleanField()


class WordSessionSerializer(serializers.ModelSerializer):
    word = WordSerializer(read_only=True)
    letter_results = serializers.DictField(
        child=LetterResultSerializer(),
        read_only=True,
    )

    class Meta:
        model = WordAttemptSession
        fields = (
            "id", "word", "status", "letters_correct",
            "letters_total", "points_awarded", "letter_results",
        )


class WordProgressSerializer(serializers.Serializer):
    word_id = serializers.CharField()
    word_text = serializers.CharField()
    total_sessions = serializers.IntegerField()
    completed_sessions = serializers.IntegerField()
    perfect_sessions = serializers.IntegerField()
    accuracy = serializers.FloatField()
```

- [ ] **Step 2: Add word_session and word_position to AttemptCreateSerializer**

In `backend/checker/serializers.py`, update `AttemptCreateSerializer`:

```python
class AttemptCreateSerializer(serializers.Serializer):
    symbol_letter = serializers.CharField(max_length=1)
    image_data = serializers.CharField(max_length=700_000, help_text="Base64-encoded PNG image data")
    word_session = serializers.UUIDField(required=False, allow_null=True)
    word_position = serializers.IntegerField(required=False, allow_null=True)
```

- [ ] **Step 3: Commit**

```bash
git add backend/checker/word_serializers.py backend/checker/serializers.py
git commit -m "feat: add word serializers and update AttemptCreateSerializer"
```

---

### Task 7: Word Views and URLs

**Files:**
- Create: `backend/checker/word_views.py`
- Modify: `backend/checker/urls.py`
- Modify: `backend/checker/views.py`

- [ ] **Step 1: Create word views**

Create `backend/checker/word_views.py`:

```python
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WordAttemptSession
from .permissions import AllowAnonymousSession
from .word_repository import WordRepository, WordTopicRepository
from .word_serializers import (
    WordListSerializer,
    WordProgressSerializer,
    WordSerializer,
    WordSessionCreateSerializer,
    WordSessionSerializer,
    WordTopicSerializer,
)
from .word_service import (
    complete_session,
    get_session_detail,
    get_word_progress,
    start_session,
)


def _get_owner(request):
    if request.user.is_authenticated:
        return {"user": request.user, "session": None}
    return {"user": None, "session": getattr(request, "anonymous_session", None)}


class WordTopicListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        topics = WordTopicRepository.get_all()
        return Response(WordTopicSerializer(topics, many=True).data)


class WordListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        difficulty = request.query_params.get("difficulty")
        topic = request.query_params.get("topic")
        words = WordRepository.get_all(difficulty=difficulty, topic_slug=topic)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(words, request)
        return paginator.get_paginated_response(WordListSerializer(page, many=True).data)


class WordDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        word = WordRepository.get_by_id(pk)
        return Response(WordSerializer(word).data)


class WordSessionListView(APIView):
    permission_classes = [AllowAnonymousSession]

    def post(self, request):
        serializer = WordSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        word_session = start_session(
            word_id=serializer.validated_data["word_id"],
            **_get_owner(request),
        )
        detail = get_session_detail(word_session.id, **_get_owner(request))
        return Response(
            WordSessionSerializer(
                detail["session"],
                context={"letter_results": detail["letter_results"]},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class WordSessionDetailView(APIView):
    permission_classes = [AllowAnonymousSession]

    def get(self, request, pk):
        detail = get_session_detail(pk, **_get_owner(request))
        data = WordSessionSerializer(detail["session"]).data
        data["letter_results"] = detail["letter_results"]
        return Response(data)


class WordSessionCompleteView(APIView):
    permission_classes = [AllowAnonymousSession]

    def post(self, request, pk):
        word_session = complete_session(pk, **_get_owner(request))
        detail = get_session_detail(pk, **_get_owner(request))
        data = WordSessionSerializer(detail["session"]).data
        data["letter_results"] = detail["letter_results"]
        return Response(data)


class WordProgressView(APIView):
    permission_classes = [AllowAnonymousSession]

    def get(self, request):
        difficulty = request.query_params.get("difficulty")
        topic = request.query_params.get("topic")
        progress = get_word_progress(
            **_get_owner(request),
            difficulty=difficulty,
            topic_slug=topic,
        )
        return Response(WordProgressSerializer(progress, many=True).data)
```

- [ ] **Step 2: Update AttemptListView to pass word_session and word_position**

In `backend/checker/views.py`, update the `post` method of `AttemptListView`. Add this import at the top:

```python
from .models import UserStats, WordAttemptSession
```

Replace the existing `UserStats` import. Then update the `post` method:

```python
    def post(self, request):
        serializer = AttemptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        word_session = None
        word_session_id = serializer.validated_data.get("word_session")
        if word_session_id:
            owner = _get_owner(request)
            owner_filter = {}
            if owner["user"]:
                owner_filter["user"] = owner["user"]
            else:
                owner_filter["anonymous_session"] = owner["session"]
            word_session = WordAttemptSession.objects.get(
                id=word_session_id, **owner_filter
            )

        attempt = submit_attempt(
            **_get_owner(request),
            symbol_letter=serializer.validated_data["symbol_letter"],
            image_data=serializer.validated_data["image_data"],
            word_session=word_session,
            word_position=serializer.validated_data.get("word_position"),
        )
        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)
```

- [ ] **Step 3: Add word URL patterns**

Replace `backend/checker/urls.py` with:

```python
from django.urls import path

from .views import (
    AttemptDetailView,
    AttemptImageView,
    AttemptListView,
    LeaderboardView,
    ProgressView,
    SymbolDetailView,
    SymbolListView,
)
from .word_views import (
    WordDetailView,
    WordListView,
    WordProgressView,
    WordSessionCompleteView,
    WordSessionDetailView,
    WordSessionListView,
    WordTopicListView,
)

urlpatterns = [
    path("symbols/", SymbolListView.as_view(), name="symbol-list"),
    path("symbols/<str:letter>/", SymbolDetailView.as_view(), name="symbol-detail"),
    path("attempts/", AttemptListView.as_view(), name="attempt-list"),
    path("attempts/<uuid:pk>/", AttemptDetailView.as_view(), name="attempt-detail"),
    path("attempts/<uuid:pk>/image/", AttemptImageView.as_view(), name="attempt-image"),
    path("progress/", ProgressView.as_view(), name="progress"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("word-topics/", WordTopicListView.as_view(), name="word-topic-list"),
    path("words/", WordListView.as_view(), name="word-list"),
    path("words/<uuid:pk>/", WordDetailView.as_view(), name="word-detail"),
    path("word-sessions/", WordSessionListView.as_view(), name="word-session-list"),
    path("word-sessions/<uuid:pk>/", WordSessionDetailView.as_view(), name="word-session-detail"),
    path("word-sessions/<uuid:pk>/complete/", WordSessionCompleteView.as_view(), name="word-session-complete"),
    path("word-progress/", WordProgressView.as_view(), name="word-progress"),
]
```

- [ ] **Step 4: Verify the server starts**

Run: `cd backend && python manage.py check`
Expected: "System check identified no issues."

- [ ] **Step 5: Commit**

```bash
git add backend/checker/word_views.py backend/checker/urls.py backend/checker/views.py
git commit -m "feat: add word API views and URL patterns"
```

---

### Task 8: Frontend Types and API Client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Add word-related TypeScript types**

Append to `frontend/src/types/index.ts`:

```typescript
export interface WordTopic {
  id: string;
  name: string;
  slug: string;
}

export interface TeelineComponent {
  letter: string;
  blend_with: string | null;
  is_doubled_for_r: boolean;
  position: number;
}

export interface Word {
  id: string;
  text: string;
  teeline_letters: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  topic: WordTopic;
  components: TeelineComponent[];
}

export interface WordListItem {
  id: string;
  text: string;
  teeline_letters: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  topic: WordTopic;
}

export interface WordSession {
  id: string;
  word: Word;
  status: "in_progress" | "completed" | "abandoned";
  letters_correct: number;
  letters_total: number;
  points_awarded: number;
  letter_results: Record<number, { attempt_id: string; is_correct: boolean }>;
}

export interface WordProgress {
  word_id: string;
  word_text: string;
  total_sessions: number;
  completed_sessions: number;
  perfect_sessions: number;
  accuracy: number;
}
```

- [ ] **Step 2: Add word API methods to client**

Update the import in `frontend/src/api/client.ts`:

```typescript
import type {
  Attempt, LeaderboardEntry, ProgressResponse, Symbol, TokenPair, User,
  Word, WordListItem, WordProgress, WordSession, WordTopic,
} from "../types";
```

Add these new API namespaces to the `api` object, after the `leaderboard` section:

```typescript
  words: {
    list(params?: { difficulty?: string; topic?: string }): Promise<{ results: WordListItem[]; count: number }> {
      const search = new URLSearchParams();
      if (params?.difficulty) search.set("difficulty", params.difficulty);
      if (params?.topic) search.set("topic", params.topic);
      const qs = search.toString();
      return request(`/words/${qs ? `?${qs}` : ""}`);
    },
    get(id: string): Promise<Word> {
      return request(`/words/${id}/`);
    },
    topics(): Promise<WordTopic[]> {
      return request("/word-topics/");
    },
  },
  wordSessions: {
    create(wordId: string): Promise<WordSession> {
      return request("/word-sessions/", {
        method: "POST",
        body: JSON.stringify({ word_id: wordId }),
      });
    },
    get(id: string): Promise<WordSession> {
      return request(`/word-sessions/${id}/`);
    },
    complete(id: string): Promise<WordSession> {
      return request(`/word-sessions/${id}/complete/`, { method: "POST" });
    },
  },
  wordProgress: {
    get(params?: { difficulty?: string; topic?: string }): Promise<WordProgress[]> {
      const search = new URLSearchParams();
      if (params?.difficulty) search.set("difficulty", params.difficulty);
      if (params?.topic) search.set("topic", params.topic);
      const qs = search.toString();
      return request(`/word-progress/${qs ? `?${qs}` : ""}`);
    },
  },
```

Also update the `attempts.create` method to accept optional word session params:

```typescript
  attempts: {
    create(data: {
      symbol_letter: string;
      image_data: string;
      word_session?: string;
      word_position?: number;
    }): Promise<Attempt> {
      return request("/attempts/", { method: "POST", body: JSON.stringify(data) });
    },
    list(): Promise<{ results: Attempt[]; count: number }> {
      return request("/attempts/");
    },
    get(id: string): Promise<Attempt> {
      return request(`/attempts/${id}/`);
    },
  },
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/api/client.ts
git commit -m "feat: add word types and API client methods"
```

---

### Task 9: LetterCard and WordReference Components

**Files:**
- Create: `frontend/src/components/LetterCard.tsx`
- Create: `frontend/src/components/WordReference.tsx`

- [ ] **Step 1: Create the LetterCard component**

Create `frontend/src/components/LetterCard.tsx`:

```tsx
import type { TeelineComponent, Symbol } from "../types";

interface LetterCardProps {
  component: TeelineComponent;
  symbol: Symbol | undefined;
  status: "pending" | "correct" | "incorrect";
  isActive: boolean;
  onClick: () => void;
}

export function LetterCard({ component, symbol, status, isActive, onClick }: LetterCardProps) {
  const statusClass =
    status === "correct" ? "card-correct" :
    status === "incorrect" ? "card-incorrect" :
    "";

  return (
    <button
      className={`letter-card ${statusClass} ${isActive ? "card-active" : ""}`}
      onClick={onClick}
      type="button"
    >
      <div className="letter-card-letter">{component.letter}</div>
      {symbol?.reference_image_url && (
        <img
          className="letter-card-img"
          src={symbol.reference_image_url}
          alt={`Teeline ${component.letter}`}
        />
      )}
      {component.blend_with && (
        <div className="letter-card-badge">blend: {component.blend_with}</div>
      )}
      {component.is_doubled_for_r && (
        <div className="letter-card-badge">+ R (lengthen)</div>
      )}
      <div className="letter-card-status">
        {status === "correct" ? "✓" : status === "incorrect" ? "✗" : "—"}
      </div>
    </button>
  );
}
```

- [ ] **Step 2: Create the WordReference component**

Create `frontend/src/components/WordReference.tsx`:

```tsx
import type { TeelineComponent, Symbol } from "../types";

interface WordReferenceProps {
  components: TeelineComponent[];
  symbols: Symbol[];
}

export function WordReference({ components, symbols }: WordReferenceProps) {
  const symbolMap = new Map(symbols.map(s => [s.letter, s]));

  return (
    <div className="word-reference">
      {components.map((comp) => {
        const sym = symbolMap.get(comp.letter);
        return (
          <div key={comp.position} className="word-reference-letter">
            {sym?.reference_image_url ? (
              <img
                src={sym.reference_image_url}
                alt={comp.letter}
                className="word-reference-img"
              />
            ) : (
              <div className="word-reference-placeholder">{comp.letter}</div>
            )}
            {comp.blend_with && <div className="word-reference-blend" />}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/LetterCard.tsx frontend/src/components/WordReference.tsx
git commit -m "feat: add LetterCard and WordReference components"
```

---

### Task 10: WordPracticePage

**Files:**
- Create: `frontend/src/pages/WordPracticePage.tsx`

- [ ] **Step 1: Create the WordPracticePage component**

Create `frontend/src/pages/WordPracticePage.tsx`:

```tsx
import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { DrawingCanvas } from "../components/DrawingCanvas";
import { FeedbackPanel } from "../components/FeedbackPanel";
import { LetterCard } from "../components/LetterCard";
import { WordReference } from "../components/WordReference";
import { useJobPoller } from "../hooks/useJobPoller";
import type {
  Attempt,
  Symbol,
  Word,
  WordListItem,
  WordSession,
  WordTopic,
} from "../types";

type LetterStatus = "pending" | "correct" | "incorrect";

export function WordPracticePage() {
  const [topics, setTopics] = useState<WordTopic[]>([]);
  const [words, setWords] = useState<WordListItem[]>([]);
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState("");
  const [selectedWord, setSelectedWord] = useState<Word | null>(null);
  const [session, setSession] = useState<WordSession | null>(null);
  const [activePosition, setActivePosition] = useState<number | null>(null);
  const [letterStatuses, setLetterStatuses] = useState<Record<number, LetterStatus>>({});
  const [canvasResetKey, setCanvasResetKey] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const { attempt, startPolling, reset: resetPoller } = useJobPoller();

  useEffect(() => {
    api.symbols.list().then(setSymbols);
    api.words.topics().then(setTopics);
  }, []);

  useEffect(() => {
    api.words
      .list({
        difficulty: selectedDifficulty || undefined,
        topic: selectedTopic || undefined,
      })
      .then((res) => setWords(res.results));
  }, [selectedDifficulty, selectedTopic]);

  async function handleSelectWord(wordId: string) {
    const word = await api.words.get(wordId);
    setSelectedWord(word);
    const newSession = await api.wordSessions.create(wordId);
    setSession(newSession);
    setLetterStatuses({});
    setActivePosition(null);
    resetPoller();
    setCanvasResetKey((k) => k + 1);
  }

  async function handleExport(dataUrl: string) {
    if (!selectedWord || !session || activePosition === null) return;
    setSubmitting(true);
    setSubmitError("");
    try {
      const base64 = dataUrl.split(",")[1];
      const component = selectedWord.components[activePosition];
      const created = await api.attempts.create({
        symbol_letter: component.letter,
        image_data: base64,
        word_session: session.id,
        word_position: activePosition,
      });
      startPolling(created.id);
    } catch {
      setSubmitError("Failed to submit. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    if (attempt?.status === "completed" && activePosition !== null) {
      setLetterStatuses((prev) => ({
        ...prev,
        [activePosition]: attempt.is_correct ? "correct" : "incorrect",
      }));
    }
  }, [attempt?.status]);

  const allDone =
    selectedWord &&
    selectedWord.components.length > 0 &&
    selectedWord.components.every((_, i) => letterStatuses[i] === "correct" || letterStatuses[i] === "incorrect");

  async function handleComplete() {
    if (!session) return;
    const updated = await api.wordSessions.complete(session.id);
    setSession(updated);
  }

  function handleNextLetter() {
    resetPoller();
    setCanvasResetKey((k) => k + 1);
    if (!selectedWord) return;
    const next = selectedWord.components.find(
      (_, i) => !letterStatuses[i]
    );
    if (next) {
      setActivePosition(next.position);
    }
  }

  function handleRetry() {
    resetPoller();
    setCanvasResetKey((k) => k + 1);
  }

  return (
    <div className="page">
      <h1>Word Practice</h1>

      <div className="word-filters">
        <select
          value={selectedDifficulty}
          onChange={(e) => setSelectedDifficulty(e.target.value)}
        >
          <option value="">All Difficulties</option>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>

        <select
          value={selectedTopic}
          onChange={(e) => setSelectedTopic(e.target.value)}
        >
          <option value="">All Topics</option>
          {topics.map((t) => (
            <option key={t.slug} value={t.slug}>
              {t.name}
            </option>
          ))}
        </select>

        <select
          value={selectedWord?.id || ""}
          onChange={(e) => {
            if (e.target.value) handleSelectWord(e.target.value);
          }}
        >
          <option value="">Select a word...</option>
          {words.map((w) => (
            <option key={w.id} value={w.id}>
              {w.text} ({w.teeline_letters})
            </option>
          ))}
        </select>
      </div>

      {selectedWord && (
        <>
          <div className="word-practice-layout">
            <div className="word-practice-left">
              <h3>
                "{selectedWord.text}" → {selectedWord.teeline_letters}
              </h3>
              <WordReference
                components={selectedWord.components}
                symbols={symbols}
              />
            </div>

            <div className="word-practice-right">
              <div className="letter-cards">
                {selectedWord.components.map((comp) => (
                  <LetterCard
                    key={comp.position}
                    component={comp}
                    symbol={symbols.find((s) => s.letter === comp.letter)}
                    status={letterStatuses[comp.position] || "pending"}
                    isActive={activePosition === comp.position}
                    onClick={() => {
                      setActivePosition(comp.position);
                      resetPoller();
                      setCanvasResetKey((k) => k + 1);
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {activePosition !== null && !attempt && (
            <div className="canvas-section">
              <p>
                Draw letter: <strong>{selectedWord.components[activePosition].letter}</strong>
              </p>
              <DrawingCanvas
                key={canvasResetKey}
                onExport={handleExport}
                disabled={submitting}
              />
              {submitError && <p className="error">{submitError}</p>}
            </div>
          )}

          {attempt && (
            <FeedbackPanel
              attempt={attempt}
              onRetry={handleRetry}
              onNext={handleNextLetter}
            />
          )}

          {allDone && session?.status !== "completed" && (
            <button className="btn btn-primary" onClick={handleComplete}>
              Complete Word
            </button>
          )}

          {session?.status === "completed" && (
            <div className="word-summary">
              <h3>Word Complete!</h3>
              <p>
                {session.letters_correct} / {session.letters_total} correct
              </p>
              <p>Points earned: {session.points_awarded}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/WordPracticePage.tsx
git commit -m "feat: add WordPracticePage component"
```

---

### Task 11: Wire Up Routing and Navigation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Header.tsx`

- [ ] **Step 1: Add the /words route to App.tsx**

In `frontend/src/App.tsx`, add the import:

```typescript
import { WordPracticePage } from "./pages/WordPracticePage";
```

Add the route inside `<Routes>`, after the `/` route:

```tsx
        <Route path="/words" element={<WordPracticePage />} />
```

- [ ] **Step 2: Add the Words tab to Header.tsx**

In `frontend/src/components/Header.tsx`, add this `<NavLink>` after the "Practice" tab:

```tsx
        <NavLink
          to="/words"
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
        >
          Words
        </NavLink>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/Header.tsx
git commit -m "feat: add Words route and navigation tab"
```

---

### Task 12: Word Progress on ProgressPage

**Files:**
- Modify: `frontend/src/pages/ProgressPage.tsx`

- [ ] **Step 1: Read the current ProgressPage to understand its structure**

Read `frontend/src/pages/ProgressPage.tsx` fully before editing.

- [ ] **Step 2: Add word progress section**

Add these imports to the top of `frontend/src/pages/ProgressPage.tsx`:

```typescript
import type { WordProgress } from "../types";
```

Add state for word progress alongside existing state:

```typescript
const [wordProgress, setWordProgress] = useState<WordProgress[]>([]);
const [activeTab, setActiveTab] = useState<"symbols" | "words">("symbols");
```

In the `useEffect` that fetches progress, add:

```typescript
api.wordProgress.get().then(setWordProgress);
```

Wrap the existing progress content in a tab container. Add a tab bar before the existing content:

```tsx
<div className="progress-tabs">
  <button
    className={`tab ${activeTab === "symbols" ? "active" : ""}`}
    onClick={() => setActiveTab("symbols")}
  >
    Symbols
  </button>
  <button
    className={`tab ${activeTab === "words" ? "active" : ""}`}
    onClick={() => setActiveTab("words")}
  >
    Words
  </button>
</div>
```

When `activeTab === "words"`, render:

```tsx
{activeTab === "words" && (
  <div className="word-progress-section">
    <div className="stat-cards">
      <div className="stat-card">
        <div className="stat-value">{wordProgress.length}</div>
        <div className="stat-label">Words Practiced</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">
          {wordProgress.filter(w => w.perfect_sessions > 0).length}
        </div>
        <div className="stat-label">Words Mastered</div>
      </div>
    </div>
    <div className="progress-list">
      {wordProgress.map((wp) => (
        <div key={wp.word_id} className="progress-bar-row">
          <span className="progress-label">{wp.word_text}</span>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${wp.accuracy * 100}%` }}
            />
          </div>
          <span className="progress-value">
            {Math.round(wp.accuracy * 100)}%
          </span>
        </div>
      ))}
      {wordProgress.length === 0 && (
        <p className="empty-state">No word practice yet. Try the Words tab!</p>
      )}
    </div>
  </div>
)}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ProgressPage.tsx
git commit -m "feat: add word progress section to ProgressPage"
```

---

### Task 13: Manual Smoke Test

**Files:** None (verification only)

- [ ] **Step 1: Start the backend and run migrations**

Run: `cd backend && python manage.py migrate && python manage.py seed_words`

- [ ] **Step 2: Start the dev servers**

Run backend: `cd backend && python manage.py runserver`
Run frontend: `cd frontend && npm run dev`

- [ ] **Step 3: Verify the word practice flow in the browser**

1. Navigate to the Words tab
2. Select a difficulty and topic filter
3. Pick a word from the dropdown
4. Verify the word reference and letter cards render
5. Click a letter card, draw on the canvas, submit
6. Verify the ML check runs and the card updates
7. Complete all letters and click "Complete Word"
8. Verify points are awarded
9. Check the Progress page → Words tab shows the word

- [ ] **Step 4: Commit any CSS/style fixes needed**

If any layout issues are found during smoke testing, fix and commit them.
