# Grouping Symbols & ML Expansion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the system from 26 individual letter symbols to include 52 multi-letter groupings (e.g. CM, SH, TR) and 45 special outlines (e.g. BS=business, GV=government), upgrading the ML model from 26 → 78 classes, the decomposition engine to use greedy longest-match against known groupings, and the data pipeline to generate synthetic training images from the teeline-online SVG reference files.

**Architecture:** The teeline-online project at `data/reference/teeline-online/` contains 52 SVG files for letter groupings (in `outline-svgs/letter-groupings/`), 27 alphabet SVGs (in `outline-svgs/alphabet/`), a `special-outlines.json` (45 entries mapping letter groupings to common words/phrases), and an `outlines.json` (6692 entries with SVG path data). We extend the existing training pipeline — `generate_synthetic.py` already parses SVG paths and renders augmented images — to also process grouping SVGs. The CNN architecture stays the same (3 conv layers, 64x64 grayscale) but expands from `NUM_CLASSES=26` to `NUM_CLASSES=78` (26 letters + 52 groupings). The decomposition engine in `teeline.py` gains a greedy longest-match step against known groupings. The paper's methodology (CNN on handwriting images, grayscale, binary-inverted, augmented with rotation/shift/noise) is preserved — we follow the same pipeline, just with more classes.

**Tech Stack:** Same as existing — TensorFlow/Keras, TFLite, Pillow, NumPy, defusedxml, Django/DRF

**Anti-Scope:** No full-word connected-stroke recognition. No sequence models (LSTM/Transformer). No new frontend drawing UX for groupings yet — this plan focuses on backend data, ML, and decomposition. Frontend integration of grouping symbols into word practice will be a separate plan.

---

## File Map

| File | Purpose |
|------|---------|
| `backend/checker/models.py` | Add `symbol_type` field to Symbol model (letter vs grouping) |
| `backend/checker/management/commands/seed_groupings.py` | **Create** — Seed 52 grouping symbols from SVGs |
| `backend/checker/management/commands/seed_special_outlines.py` | **Create** — Seed 45 special outline mappings |
| `backend/checker/models.py` | Add `SpecialOutline` model |
| `backend/checker/teeline.py` | Upgrade decomposition with greedy longest-match |
| `backend/ml/train/generate_synthetic.py` | Extend to process grouping SVGs from `letter-groupings/` dir |
| `backend/ml/train/train.py` | Expand `NUM_CLASSES` from 26 → 78, auto-detect class count |
| `backend/ml/train/augment.py` | Support multi-char directory names (not just single-letter) |
| `backend/ml/inference.py` | Expand class labels from 26 → 78 |
| `backend/ml/preprocessing.py` | No changes needed |
| `tests/test_endpoints.py` | Add tests for grouping symbols and special outlines |
| `backend/checker/pytest_tests/test_teeline.py` | Add tests for greedy decomposition with groupings |
| `data/reference/teeline-online/outline-svgs/letter-groupings/*.svg` | 52 existing SVG source files (read-only) |
| `data/reference/teeline-online/website/src/lib/data/special-outlines.json` | 45 existing special outline mappings (read-only) |

---

## Task 1: Add `symbol_type` Field to Symbol Model

**Files:**
- Modify: `backend/checker/models.py`
- Create: migration via `makemigrations`

The Symbol model currently only holds single letters A-Z. We need a `symbol_type` field to distinguish letters from groupings, and allow `letter` field to hold multi-character values like "CM", "SH", "TR".

- [ ] **Step 1: Write the failing test**

Create `backend/checker/pytest_tests/test_grouping_models.py`:
```python
import pytest
from django.test import TestCase
from checker.models import Symbol


class SymbolTypeTest(TestCase):
    def test_symbol_can_be_letter_type(self):
        s = Symbol.objects.create(letter="A", name="A", symbol_type="letter")
        assert s.symbol_type == "letter"

    def test_symbol_can_be_grouping_type(self):
        s = Symbol.objects.create(letter="CM", name="CM blend", symbol_type="grouping")
        assert s.symbol_type == "grouping"
        assert s.letter == "CM"

    def test_symbol_type_defaults_to_letter(self):
        s = Symbol.objects.create(letter="B", name="B")
        assert s.symbol_type == "letter"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/Scripts/python.exe manage.py test checker.pytest_tests.test_grouping_models --settings=config.settings.test`
Expected: FAIL — `symbol_type` field doesn't exist

- [ ] **Step 3: Modify Symbol model**

In `backend/checker/models.py`, add to the `Symbol` model:

```python
SYMBOL_TYPE_CHOICES = [
    ("letter", "Letter"),
    ("grouping", "Grouping"),
]

class Symbol(TimestampedModel):
    letter = models.CharField(max_length=10, unique=True)  # was max_length=1
    name = models.CharField(max_length=100)
    symbol_type = models.CharField(
        max_length=10,
        choices=SYMBOL_TYPE_CHOICES,
        default="letter",
    )
    # ... existing fields unchanged
```

Change `letter` field `max_length` from `1` to `10` to accommodate multi-character groupings like "OTHR", "CHFR".

- [ ] **Step 4: Generate and apply migration**

```bash
cd backend
.venv/Scripts/python.exe manage.py makemigrations checker --settings=config.settings.test
.venv/Scripts/python.exe manage.py migrate --settings=config.settings.test
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && .venv/Scripts/python.exe manage.py test checker.pytest_tests.test_grouping_models --settings=config.settings.test
```
Expected: PASS

- [ ] **Step 6: Run existing tests to verify no regressions**

```bash
cd backend && .venv/Scripts/python.exe manage.py test tests.test_endpoints --settings=config.settings.test
```
Expected: All 71 existing tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/checker/models.py backend/checker/migrations/ backend/checker/pytest_tests/test_grouping_models.py
git commit -m "feat(models): add symbol_type field to Symbol, expand letter max_length for groupings"
```

---

## Task 2: SpecialOutline Model

**Files:**
- Modify: `backend/checker/models.py`
- Create: migration

Special outlines map abbreviated letter groupings to common words (e.g., "BS" → "business", "GV" → "government"). These are distinct from decomposition — they're whole-word shortcuts that skip the normal vowel-removal algorithm.

- [ ] **Step 1: Write the failing test**

Add to `backend/checker/pytest_tests/test_grouping_models.py`:
```python
from checker.models import Symbol, SpecialOutline


class SpecialOutlineTest(TestCase):
    def test_special_outline_links_grouping_to_meaning(self):
        sym = Symbol.objects.create(letter="BS", name="BS blend", symbol_type="grouping")
        outline = SpecialOutline.objects.create(
            symbol=sym,
            meaning="business",
        )
        assert outline.symbol == sym
        assert outline.meaning == "business"

    def test_multiple_meanings_for_same_grouping(self):
        sym = Symbol.objects.create(letter="MR", name="MR blend", symbol_type="grouping")
        SpecialOutline.objects.create(symbol=sym, meaning="march")
        SpecialOutline.objects.create(symbol=sym, meaning="metre")
        assert SpecialOutline.objects.filter(symbol=sym).count() == 2

    def test_unique_meaning(self):
        sym = Symbol.objects.create(letter="AC", name="AC blend", symbol_type="grouping")
        SpecialOutline.objects.create(symbol=sym, meaning="account")
        with pytest.raises(Exception):
            SpecialOutline.objects.create(symbol=sym, meaning="account")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/Scripts/python.exe manage.py test checker.pytest_tests.test_grouping_models --settings=config.settings.test
```
Expected: FAIL — `SpecialOutline` model doesn't exist

- [ ] **Step 3: Add SpecialOutline model**

In `backend/checker/models.py`:

```python
class SpecialOutline(TimestampedModel):
    symbol = models.ForeignKey(
        Symbol,
        on_delete=models.CASCADE,
        related_name="special_outlines",
    )
    meaning = models.CharField(max_length=100)

    class Meta:
        unique_together = [("symbol", "meaning")]
        ordering = ["meaning"]

    def __str__(self):
        return f"{self.symbol.letter} → {self.meaning}"
```

- [ ] **Step 4: Generate and apply migration**

```bash
cd backend
.venv/Scripts/python.exe manage.py makemigrations checker --settings=config.settings.test
.venv/Scripts/python.exe manage.py migrate --settings=config.settings.test
```

- [ ] **Step 5: Run tests**

```bash
cd backend && .venv/Scripts/python.exe manage.py test checker.pytest_tests.test_grouping_models --settings=config.settings.test
```
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/checker/models.py backend/checker/migrations/ backend/checker/pytest_tests/test_grouping_models.py
git commit -m "feat(models): add SpecialOutline model for word-to-grouping shortcuts"
```

---

## Task 3: Seed Grouping Symbols from SVGs

**Files:**
- Create: `backend/checker/management/commands/seed_groupings.py`

This command reads the 52 SVG files from `data/reference/teeline-online/outline-svgs/letter-groupings/` and creates Symbol entries with `symbol_type="grouping"`.

- [ ] **Step 1: Write the failing test**

Add to `backend/checker/pytest_tests/test_grouping_models.py`:
```python
from django.core.management import call_command


class SeedGroupingsTest(TestCase):
    def test_seed_groupings_creates_52_symbols(self):
        call_command("seed_groupings")
        groupings = Symbol.objects.filter(symbol_type="grouping")
        assert groupings.count() == 52

    def test_seed_groupings_idempotent(self):
        call_command("seed_groupings")
        call_command("seed_groupings")
        groupings = Symbol.objects.filter(symbol_type="grouping")
        assert groupings.count() == 52

    def test_seed_groupings_sets_correct_letters(self):
        call_command("seed_groupings")
        assert Symbol.objects.filter(letter="CM", symbol_type="grouping").exists()
        assert Symbol.objects.filter(letter="SH", symbol_type="grouping").exists()
        assert Symbol.objects.filter(letter="TR", symbol_type="grouping").exists()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/Scripts/python.exe manage.py test checker.pytest_tests.test_grouping_models.SeedGroupingsTest --settings=config.settings.test
```
Expected: FAIL — `seed_groupings` command not found

- [ ] **Step 3: Create seed_groupings command**

Create `backend/checker/management/commands/seed_groupings.py`:
```python
"""Seed multi-letter grouping symbols from teeline-online SVG reference files."""

import os

from django.core.management.base import BaseCommand

from checker.models import Symbol

GROUPINGS_SVG_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..",
    "data", "reference", "teeline-online", "outline-svgs", "letter-groupings",
)


class Command(BaseCommand):
    help = "Seed Teeline letter grouping symbols from reference SVGs"

    def handle(self, *args, **options):
        svg_dir = os.path.normpath(GROUPINGS_SVG_DIR)
        if not os.path.isdir(svg_dir):
            self.stderr.write(f"SVG directory not found: {svg_dir}")
            return

        svg_files = sorted(f for f in os.listdir(svg_dir) if f.endswith(".svg"))
        created = 0

        for svg_file in svg_files:
            # "tr,thr.svg" → "TR/THR", "cm.svg" → "CM"
            stem = os.path.splitext(svg_file)[0]
            letter = stem.upper().replace(",", "/")
            name = f"{letter} grouping"

            _, was_created = Symbol.objects.update_or_create(
                letter=letter,
                defaults={
                    "name": name,
                    "symbol_type": "grouping",
                },
            )
            if was_created:
                created += 1

        total = Symbol.objects.filter(symbol_type="grouping").count()
        self.stdout.write(f"Groupings: {created} created, {total} total")
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/Scripts/python.exe manage.py test checker.pytest_tests.test_grouping_models.SeedGroupingsTest --settings=config.settings.test
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/checker/management/commands/seed_groupings.py backend/checker/pytest_tests/test_grouping_models.py
git commit -m "feat(seeder): add seed_groupings command — 52 multi-letter grouping symbols"
```

---

## Task 4: Seed Special Outlines

**Files:**
- Create: `backend/checker/management/commands/seed_special_outlines.py`

Reads `data/reference/teeline-online/website/src/lib/data/special-outlines.json` and creates SpecialOutline entries linking grouping symbols to their word meanings.

- [ ] **Step 1: Write the failing test**

Add to `backend/checker/pytest_tests/test_grouping_models.py`:
```python
class SeedSpecialOutlinesTest(TestCase):
    def test_seed_special_outlines_creates_entries(self):
        call_command("seed_groupings")
        call_command("seed_special_outlines")
        assert SpecialOutline.objects.count() > 0

    def test_seed_special_outlines_links_to_grouping_symbols(self):
        call_command("seed_groupings")
        call_command("seed_special_outlines")
        bs = SpecialOutline.objects.filter(meaning="business").first()
        assert bs is not None
        assert bs.symbol.letter == "BS"

    def test_seed_special_outlines_handles_multiple_meanings(self):
        call_command("seed_groupings")
        call_command("seed_special_outlines")
        # MR maps to both "march" and "metre"
        mr_outlines = SpecialOutline.objects.filter(symbol__letter="MR")
        assert mr_outlines.count() >= 2

    def test_seed_special_outlines_idempotent(self):
        call_command("seed_groupings")
        call_command("seed_special_outlines")
        count1 = SpecialOutline.objects.count()
        call_command("seed_special_outlines")
        count2 = SpecialOutline.objects.count()
        assert count1 == count2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/Scripts/python.exe manage.py test checker.pytest_tests.test_grouping_models.SeedSpecialOutlinesTest --settings=config.settings.test
```
Expected: FAIL — `seed_special_outlines` command not found

- [ ] **Step 3: Create seed_special_outlines command**

Create `backend/checker/management/commands/seed_special_outlines.py`:
```python
"""Seed special outline mappings from teeline-online reference data."""

import json
import os

from django.core.management.base import BaseCommand

from checker.models import SpecialOutline, Symbol

SPECIAL_OUTLINES_JSON = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..",
    "data", "reference", "teeline-online",
    "website", "src", "lib", "data", "special-outlines.json",
)


class Command(BaseCommand):
    help = "Seed special outline word mappings from teeline-online reference data"

    def handle(self, *args, **options):
        json_path = os.path.normpath(SPECIAL_OUTLINES_JSON)
        if not os.path.isfile(json_path):
            self.stderr.write(f"Special outlines JSON not found: {json_path}")
            return

        with open(json_path, "r") as f:
            data = json.load(f)

        created = 0
        skipped = 0

        for entry in data:
            letter_grouping = entry["letterGrouping"].upper()

            try:
                symbol = Symbol.objects.get(letter=letter_grouping)
            except Symbol.DoesNotExist:
                # Some special outlines use single letters (e.g., "F" → "from")
                # or groupings we haven't seeded — create them as needed
                symbol, _ = Symbol.objects.get_or_create(
                    letter=letter_grouping,
                    defaults={
                        "name": f"{letter_grouping} special",
                        "symbol_type": "grouping" if len(letter_grouping) > 1 else "letter",
                    },
                )

            for meaning in entry["meanings"]:
                _, was_created = SpecialOutline.objects.get_or_create(
                    symbol=symbol,
                    meaning=meaning.lower(),
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(f"Special outlines: {created} created, {skipped} skipped")
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/Scripts/python.exe manage.py test checker.pytest_tests.test_grouping_models.SeedSpecialOutlinesTest --settings=config.settings.test
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/checker/management/commands/seed_special_outlines.py backend/checker/pytest_tests/test_grouping_models.py
git commit -m "feat(seeder): add seed_special_outlines command — 45 word-to-grouping mappings"
```

---

## Task 5: Upgrade Teeline Decomposition Engine with Greedy Longest-Match

**Files:**
- Modify: `backend/checker/teeline.py`
- Modify: `backend/checker/pytest_tests/test_teeline.py`

The current decomposition strips vowels and detects a few hardcoded blends. The new version first checks for special outline matches (whole-word shortcuts), then uses greedy longest-match against known groupings when decomposing the consonant skeleton.

- [ ] **Step 1: Write the failing tests**

Add to `backend/checker/pytest_tests/test_teeline.py`:
```python
from checker.teeline import decompose_to_letters, resolve_special_outline


KNOWN_GROUPINGS = [
    "ABT", "ANY", "AS", "BD", "BT", "CD", "CHF", "CM", "CR", "CV",
    "DB", "DR", "FB", "FL", "FM", "FR", "FW", "HV", "IF", "IS",
    "IT", "MB", "MN", "MNY", "MR", "NO", "NV", "NW", "O", "OM",
    "ON", "OTHR", "PV", "RF", "SD", "SE", "SHE", "SM", "SN", "SO",
    "TB", "THS", "TLN", "TR/THR", "US", "VN", "WF", "WN", "WR", "WRD", "WS",
]


class GreedyDecompositionTest:
    def test_simple_word_uses_grouping(self):
        """'command' → consonant skeleton 'CMND' should match CM grouping."""
        result = decompose_to_letters("command", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert "CM" in letters

    def test_greedy_picks_longest_match(self):
        """'money' → skeleton 'MNY' should match MNY (3-char) not MN + Y."""
        result = decompose_to_letters("money", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert "MNY" in letters

    def test_other_uses_othr_grouping(self):
        """'other' → skeleton 'THR' should match grouping."""
        result = decompose_to_letters("other", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert "OTHR" in letters or "TR/THR" in letters

    def test_no_grouping_falls_back_to_individual(self):
        """'dog' → 'DG' has no grouping, stays as D, G."""
        result = decompose_to_letters("dog", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert letters == ["D", "G"]

    def test_mixed_grouping_and_individual(self):
        """'discover' → 'DSCVR' → D, S, CV, R — CV is a grouping."""
        result = decompose_to_letters("discover", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert "CV" in letters

    def test_empty_groupings_list_falls_back(self):
        """With no known groupings, behaves like current decomposition."""
        result = decompose_to_letters("command", known_groupings=[])
        letters = [c["letter"] for c in result]
        assert all(len(l) == 1 for l in letters)


class SpecialOutlineResolutionTest:
    def test_known_special_outline_returns_grouping(self):
        specials = {"business": "BS", "account": "AC", "government": "GV"}
        result = resolve_special_outline("business", specials)
        assert result is not None
        assert result["letter"] == "BS"
        assert result["is_special_outline"] is True

    def test_unknown_word_returns_none(self):
        specials = {"business": "BS"}
        result = resolve_special_outline("xylophone", specials)
        assert result is None

    def test_case_insensitive_lookup(self):
        specials = {"business": "BS"}
        result = resolve_special_outline("Business", specials)
        assert result is not None
        assert result["letter"] == "BS"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && .venv/Scripts/python.exe -m pytest checker/pytest_tests/test_teeline.py -v -k "Greedy or SpecialOutline"
```
Expected: FAIL — `known_groupings` param and `resolve_special_outline` don't exist

- [ ] **Step 3: Add `resolve_special_outline` function**

In `backend/checker/teeline.py`, add:

```python
def resolve_special_outline(
    word: str,
    special_outlines: dict[str, str] | None = None,
) -> dict | None:
    """Check if a word has a special outline shortcut.

    Args:
        word: English word to look up
        special_outlines: dict mapping word → letter grouping (e.g. {"business": "BS"})

    Returns:
        Single TeelineComponent dict if found, None otherwise.
    """
    if not special_outlines:
        return None

    key = word.lower().strip()
    if key in special_outlines:
        return {
            "letter": special_outlines[key],
            "blend_with": None,
            "is_doubled_for_r": False,
            "is_special_outline": True,
            "position": 0,
        }
    return None
```

- [ ] **Step 4: Modify `decompose_to_letters` to accept `known_groupings` and use greedy matching**

In `backend/checker/teeline.py`, modify the `decompose_to_letters` function signature and add greedy matching after the consonant skeleton is built:

```python
def _greedy_match(skeleton: str, known_groupings: list[str]) -> list[str]:
    """Greedy longest-match of consonant skeleton against known groupings.

    At each position, try the longest possible substring first.
    If it matches a known grouping, consume it. Otherwise, emit a single character.
    """
    # Normalize groupings: "TR/THR" → try both "TR" and "THR"
    expanded = set()
    for g in known_groupings:
        for variant in g.split("/"):
            expanded.add(variant)

    # Sort by length descending for greedy matching
    sorted_groupings = sorted(expanded, key=len, reverse=True)
    max_len = max((len(g) for g in sorted_groupings), default=1)

    result = []
    i = 0
    while i < len(skeleton):
        matched = False
        for length in range(min(max_len, len(skeleton) - i), 1, -1):
            candidate = skeleton[i:i + length]
            if candidate in expanded:
                result.append(candidate)
                i += length
                matched = True
                break
        if not matched:
            result.append(skeleton[i])
            i += 1

    return result
```

Then modify `decompose_to_letters` to use `_greedy_match` after building the consonant skeleton:

```python
def decompose_to_letters(
    word: str,
    known_groupings: list[str] | None = None,
) -> list[dict]:
    # ... existing phonetic substitutions, silent letter removal,
    #     double reduction, vowel dropping ...
    # (all existing code stays the same up to the point where
    #  individual letters are emitted)

    # After building consonant skeleton string:
    if known_groupings:
        matched_units = _greedy_match(skeleton, known_groupings)
    else:
        matched_units = list(skeleton)

    components = []
    for pos, unit in enumerate(matched_units):
        components.append({
            "letter": unit,
            "blend_with": None,
            "is_doubled_for_r": False,
            "is_special_outline": False,
            "position": pos,
        })

    return components
```

The key insight: the existing code already builds a consonant skeleton. The greedy matcher just groups those consonants into longer known units before emitting components.

- [ ] **Step 5: Run tests**

```bash
cd backend && .venv/Scripts/python.exe -m pytest checker/pytest_tests/test_teeline.py -v
```
Expected: All tests PASS (both new and existing)

- [ ] **Step 6: Run full endpoint tests for regression**

```bash
cd backend && .venv/Scripts/python.exe manage.py test tests.test_endpoints --settings=config.settings.test
```
Expected: All 71 tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/checker/teeline.py backend/checker/pytest_tests/test_teeline.py
git commit -m "feat(teeline): add greedy longest-match decomposition against known groupings"
```

---

## Task 6: Extend Synthetic Data Generator for Groupings

**Files:**
- Modify: `backend/ml/train/generate_synthetic.py`

The existing generator reads from `outline-svgs/alphabet/` and creates images for 26 letters. Extend it to also read from `outline-svgs/letter-groupings/` for the 52 grouping SVGs.

- [ ] **Step 1: Modify the CLI to accept a `--groupings-svgs` flag**

In `backend/ml/train/generate_synthetic.py`, update the argument parser:

```python
def main():
    parser = argparse.ArgumentParser(description="Generate synthetic training data")
    parser.add_argument(
        "--svgs",
        default="../../../data/reference/teeline-online/outline-svgs/alphabet",
        help="Directory of single-letter SVG files",
    )
    parser.add_argument(
        "--groupings-svgs",
        default="../../../data/reference/teeline-online/outline-svgs/letter-groupings",
        help="Directory of grouping SVG files (optional)",
    )
    parser.add_argument("--output", default="../../../data/raw", help="Output directory")
    parser.add_argument("--samples", type=int, default=100, help="Samples per symbol")
    parser.add_argument(
        "--groupings-only",
        action="store_true",
        help="Only generate grouping images (skip letters)",
    )
    args = parser.parse_args()

    total = 0

    # Generate letter images (existing behavior)
    if not args.groupings_only:
        for letter in LETTERS:
            svg_file = os.path.join(args.svgs, f"{letter.lower()}.svg")
            if not os.path.isfile(svg_file):
                print(f"  WARNING: {svg_file} not found, skipping {letter}")
                continue
            letter_dir = os.path.join(args.output, letter)
            os.makedirs(letter_dir, exist_ok=True)
            for i in range(args.samples):
                strokes = parse_svg_path(svg_file)
                img = render_strokes(strokes)
                img.save(os.path.join(letter_dir, f"{letter}_{i:04d}.png"))
                total += 1
            print(f"  {letter}: {args.samples} samples")

    # Generate grouping images
    groupings_dir = args.groupings_svgs
    if os.path.isdir(groupings_dir):
        svg_files = sorted(f for f in os.listdir(groupings_dir) if f.endswith(".svg"))
        for svg_file in svg_files:
            stem = os.path.splitext(svg_file)[0]
            label = stem.upper().replace(",", "_")  # "tr,thr" → "TR_THR"
            svg_path = os.path.join(groupings_dir, svg_file)
            out_dir = os.path.join(args.output, label)
            os.makedirs(out_dir, exist_ok=True)
            for i in range(args.samples):
                strokes = parse_svg_path(svg_path)
                img = render_strokes(strokes)
                img.save(os.path.join(out_dir, f"{label}_{i:04d}.png"))
                total += 1
            print(f"  {label}: {args.samples} samples")

    print(f"\nGenerated {total} total images in {args.output}")
```

- [ ] **Step 2: Test manually**

```bash
cd backend/ml/train
.venv/Scripts/python.exe generate_synthetic.py --groupings-only --samples 5 --output ../../../data/raw_test
ls ../../../data/raw_test/
```
Expected: Directories like `CM/`, `SH/`, `TR_THR/` etc. with 5 images each.

- [ ] **Step 3: Clean up test output**

```bash
rm -rf ../../../data/raw_test
```

- [ ] **Step 4: Commit**

```bash
git add backend/ml/train/generate_synthetic.py
git commit -m "feat(training): extend synthetic generator to produce grouping images from SVGs"
```

---

## Task 7: Update Augmentation Pipeline for Multi-Char Labels

**Files:**
- Modify: `backend/ml/train/augment.py`

The current augmentation script filters directories by `len(d) == 1` to find letter folders. With groupings like `CM/`, `SH/`, `TR_THR/`, it needs to accept any directory.

- [ ] **Step 1: Modify the directory filter**

In `backend/ml/train/augment.py`, change the letters discovery logic:

```python
def augment_dataset(input_dir: str, output_dir: str, factor: int = 5):
    # ... existing setup ...

    # Old: letters = sorted(d for d in os.listdir(input_dir) if os.path.isdir(...) and len(d) == 1)
    # New: accept any directory that contains PNG files
    labels = sorted(
        d for d in os.listdir(input_dir)
        if os.path.isdir(os.path.join(input_dir, d))
        and any(f.endswith(".png") for f in os.listdir(os.path.join(input_dir, d)))
    )

    total = 0
    for label in labels:
        label_in = os.path.join(input_dir, label)
        label_out = os.path.join(output_dir, label)
        os.makedirs(label_out, exist_ok=True)
        # ... rest of augmentation logic unchanged, just rename variable from `letter` to `label` ...
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml/train/augment.py
git commit -m "feat(training): augmentation pipeline accepts multi-char grouping labels"
```

---

## Task 8: Expand Training Script to Auto-Detect Class Count

**Files:**
- Modify: `backend/ml/train/train.py`

Instead of hardcoding `NUM_CLASSES=26` and `LETTERS`, the training script should auto-detect classes from the data directory. This handles 26 letters, 52 groupings, and any future additions without code changes.

- [ ] **Step 1: Replace hardcoded class list with auto-detection**

In `backend/ml/train/train.py`:

```python
# Remove these hardcoded constants:
# LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
# NUM_CLASSES = 26

def discover_classes(data_dir: str) -> list[str]:
    """Auto-discover class labels from subdirectory names in training data dir."""
    labels = sorted(
        d for d in os.listdir(data_dir)
        if os.path.isdir(os.path.join(data_dir, d))
        and any(f.endswith(".png") for f in os.listdir(os.path.join(data_dir, d)))
    )
    if not labels:
        print(f"ERROR: No class directories with PNG files found in {data_dir}")
        sys.exit(1)
    return labels


def build_model(num_classes: int) -> tf.keras.Model:
    model = models.Sequential([
        layers.Input(shape=(IMG_SIZE, IMG_SIZE, 1)),

        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Flatten(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.4),
        layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


def create_generators(data_dir: str, batch_size: int, classes: list[str], val_split: float = 0.2):
    # ... same as before but pass `classes` instead of hardcoded LETTERS ...
    train_gen = datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=batch_size,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        classes=classes,
    )
    # ... val_gen same pattern ...
    return train_gen, val_gen
```

- [ ] **Step 2: Save class index alongside model**

At the end of `main()`, save the class list so inference knows the label order:

```python
    import json

    classes_path = os.path.join(os.path.dirname(args.output), "classes.json")
    with open(classes_path, "w") as f:
        json.dump(classes, f)
    print(f"Class index saved to {classes_path} ({len(classes)} classes)")
```

- [ ] **Step 3: Update main() to use auto-detection**

```python
def main():
    # ... argument parsing unchanged ...

    classes = discover_classes(args.data)
    num_classes = len(classes)
    print(f"Discovered {num_classes} classes: {classes}")

    model = build_model(num_classes)
    model.summary()

    train_gen, val_gen = create_generators(args.data, args.batch_size, classes)
    # ... rest unchanged ...
```

- [ ] **Step 4: Commit**

```bash
git add backend/ml/train/train.py
git commit -m "feat(training): auto-detect class count from data directory, save class index"
```

---

## Task 9: Update Inference Engine for Dynamic Class Labels

**Files:**
- Modify: `backend/ml/inference.py`

The inference engine currently hardcodes `LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")`. It needs to load the class list from `classes.json` (saved by the training script) to support 78 classes.

- [ ] **Step 1: Write the failing test**

Create `backend/ml/tests/test_inference.py`:
```python
import json
import os
import tempfile
from unittest.mock import patch

from django.test import TestCase


class InferenceClassLoadingTest(TestCase):
    def test_loads_classes_from_json_when_available(self):
        from ml.inference import load_class_labels

        classes = ["A", "B", "CM", "SH"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(classes, f)
            f.flush()
            result = load_class_labels(f.name)

        assert result == classes
        os.unlink(f.name)

    def test_falls_back_to_alphabet_when_no_json(self):
        from ml.inference import load_class_labels

        result = load_class_labels("/nonexistent/classes.json")
        assert result == list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        assert len(result) == 26
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/Scripts/python.exe manage.py test ml.tests.test_inference --settings=config.settings.test
```
Expected: FAIL — `load_class_labels` doesn't exist

- [ ] **Step 3: Add `load_class_labels` and update inference**

In `backend/ml/inference.py`:

```python
import json
import logging
import os
from pathlib import Path

import numpy as np

from .preprocessing import preprocess_image

logger = logging.getLogger(__name__)

ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
MODEL_PATH = Path(__file__).parent / "model.tflite"
CLASSES_PATH = Path(__file__).parent / "classes.json"


def load_class_labels(classes_path: str | Path = CLASSES_PATH) -> list[str]:
    """Load class labels from classes.json, falling back to A-Z alphabet."""
    path = Path(classes_path)
    if path.exists():
        try:
            with open(path, "r") as f:
                labels = json.load(f)
            logger.info("Loaded %d class labels from %s", len(labels), path)
            return labels
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to read %s: %s — using alphabet fallback", path, e)
    return list(ALPHABET)


class TFLitePredictor:
    def __init__(self):
        self._interpreter = None
        self._labels = load_class_labels()

        if MODEL_PATH.exists():
            try:
                import tflite_runtime.interpreter as tflite

                self._interpreter = tflite.Interpreter(model_path=str(MODEL_PATH))
                self._interpreter.allocate_tensors()
                self._input_details = self._interpreter.get_input_details()
                self._output_details = self._interpreter.get_output_details()
                logger.info("TFLite model loaded — %d classes", len(self._labels))
            except Exception as e:
                logger.warning("Failed to load TFLite model: %s — using stub", e)
        else:
            logger.warning("No model.tflite found — using stub predictions")

    def predict(self, image_bytes: bytes) -> list[dict]:
        if self._interpreter is None:
            return [{"label": l, "confidence": 0.0} for l in self._labels[:3]]

        input_data = preprocess_image(image_bytes)

        input_detail = self._input_details[0]
        if input_detail["dtype"] == np.uint8:
            scale, zero_point = input_detail["quantization"]
            input_data = (input_data / scale + zero_point).astype(np.uint8)

        self._interpreter.set_tensor(input_detail["index"], input_data)
        self._interpreter.invoke()

        output_data = self._interpreter.get_tensor(self._output_details[0]["index"])
        scores = output_data[0]

        if scores.dtype == np.uint8:
            scale, zero_point = self._output_details[0]["quantization"]
            scores = (scores.astype(np.float32) - zero_point) * scale

        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)

        return [
            {"label": self._labels[idx], "confidence": float(score)}
            for idx, score in indexed[:3]
        ]


predictor = TFLitePredictor()
```

- [ ] **Step 4: Create `backend/ml/tests/__init__.py`**

```bash
touch backend/ml/tests/__init__.py
```

- [ ] **Step 5: Run tests**

```bash
cd backend && .venv/Scripts/python.exe manage.py test ml.tests.test_inference --settings=config.settings.test
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/ml/inference.py backend/ml/tests/
git commit -m "feat(inference): load class labels from classes.json, support 78+ classes"
```

---

## Task 10: Update Evaluation Script for Dynamic Classes

**Files:**
- Modify: `backend/ml/train/evaluate.py`

Same pattern as inference — auto-detect classes from data directory instead of hardcoding A-Z.

- [ ] **Step 1: Update evaluate.py**

In `backend/ml/train/evaluate.py`, replace the hardcoded `LETTERS` constant:

```python
# Remove: LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def discover_classes(data_dir: str) -> list[str]:
    """Auto-discover class labels from subdirectory names."""
    return sorted(
        d for d in os.listdir(data_dir)
        if os.path.isdir(os.path.join(data_dir, d))
        and any(f.endswith(".png") for f in os.listdir(os.path.join(data_dir, d)))
    )


def main():
    # ... argument parsing unchanged ...

    classes = discover_classes(args.data)
    print(f"Discovered {len(classes)} classes: {classes}")

    # Use classes instead of LETTERS everywhere:
    test_gen = datagen.flow_from_directory(
        args.data,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=args.batch_size,
        class_mode="categorical",
        shuffle=False,
        classes=classes,
    )

    # ... rest uses `classes` instead of `LETTERS` ...
    print(classification_report(y_true, y_pred, target_names=classes))
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml/train/evaluate.py
git commit -m "feat(training): evaluation script auto-detects classes from data directory"
```

---

## Task 11: Data Collection Script Supports Groupings

**Files:**
- Modify: `backend/ml/train/collect.py`

The collector exports user-verified correct attempts. It needs to handle grouping symbols by using the symbol's `letter` field (which can now be multi-char) as the directory name.

- [ ] **Step 1: Update collect.py query**

In `backend/ml/train/collect.py`, the query already uses `checker_symbol.letter` as the directory name. The only change needed is to handle multi-character letter values:

```python
    for row in result.data:
        letter = row["checker_symbol"]["letter"]
        # Sanitize for filesystem: "TR/THR" → "TR_THR"
        dir_name = letter.replace("/", "_")
        label_dir = os.path.join(args.output, dir_name)
        os.makedirs(label_dir, exist_ok=True)
        # ... rest unchanged ...
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml/train/collect.py
git commit -m "feat(training): data collector handles multi-char grouping labels"
```

---

## Task 12: API Endpoints for Grouping Symbols

**Files:**
- Modify: `backend/checker/serializers.py`
- Modify: `backend/checker/views.py` (or `backend/checker/urls.py`)
- Modify: `tests/test_endpoints.py`

Expose grouping symbols and special outlines through the API so the frontend can display them.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_endpoints.py`:
```python
class GroupingSymbolEndpointsTest(TestCase):
    def setUp(self):
        from checker.models import Symbol, SpecialOutline
        self.letter_sym = Symbol.objects.create(letter="A", name="A", symbol_type="letter")
        self.grouping_sym = Symbol.objects.create(letter="CM", name="CM blend", symbol_type="grouping")
        SpecialOutline.objects.create(symbol=self.grouping_sym, meaning="command")

    def test_symbols_list_filters_by_type(self):
        response = self.client.get("/api/symbols/?symbol_type=grouping")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertTrue(all(s["symbol_type"] == "grouping" for s in results))

    def test_symbols_list_returns_all_by_default(self):
        response = self.client.get("/api/symbols/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        letters = [s["letter"] for s in results]
        self.assertIn("A", letters)
        self.assertIn("CM", letters)

    def test_special_outlines_endpoint(self):
        response = self.client.get("/api/special-outlines/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertTrue(any(o["meaning"] == "command" for o in results))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && .venv/Scripts/python.exe manage.py test tests.test_endpoints.GroupingSymbolEndpointsTest --settings=config.settings.test
```
Expected: FAIL

- [ ] **Step 3: Add `symbol_type` to SymbolSerializer**

In `backend/checker/serializers.py`:
```python
class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = ["id", "letter", "name", "symbol_type", "created_at"]
```

- [ ] **Step 4: Add query param filter to SymbolViewSet**

In the symbols list view, add filtering:
```python
def get_queryset(self):
    qs = Symbol.objects.all()
    symbol_type = self.request.query_params.get("symbol_type")
    if symbol_type in ("letter", "grouping"):
        qs = qs.filter(symbol_type=symbol_type)
    return qs
```

- [ ] **Step 5: Create SpecialOutlineSerializer and view**

```python
# serializers.py
class SpecialOutlineSerializer(serializers.ModelSerializer):
    symbol_letter = serializers.CharField(source="symbol.letter", read_only=True)

    class Meta:
        model = SpecialOutline
        fields = ["id", "symbol_letter", "meaning"]


# views.py
class SpecialOutlineListView(generics.ListAPIView):
    serializer_class = SpecialOutlineSerializer
    permission_classes = [AllowAny]
    queryset = SpecialOutline.objects.select_related("symbol").all()
```

- [ ] **Step 6: Add URL route**

In `backend/checker/urls.py`:
```python
path("special-outlines/", SpecialOutlineListView.as_view(), name="special-outline-list"),
```

- [ ] **Step 7: Run tests**

```bash
cd backend && .venv/Scripts/python.exe manage.py test tests.test_endpoints --settings=config.settings.test
```
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add backend/checker/serializers.py backend/checker/views.py backend/checker/urls.py tests/test_endpoints.py
git commit -m "feat(api): add symbol_type filter and special-outlines endpoint"
```

---

## Training Workflow (Reference — not a task)

After all tasks are complete, the expanded training workflow is:

```bash
cd backend/ml/train

# 1. Generate synthetic data for ALL symbols (letters + groupings)
python generate_synthetic.py --samples 200 --output ../../../data/raw

# 2. Augment (handles both single-letter and multi-char directories)
python augment.py --input ../../../data/raw --output ../../../data/augmented --factor 10

# 3. Train (auto-detects 78 classes from directory structure)
python train.py --data ../../../data/augmented --epochs 100 --batch-size 32

# 4. Evaluate
python evaluate.py --model ../model.keras --data ../../../data/augmented

# 5. Convert to TFLite
python convert.py --model ../model.keras --output ../model.tflite

# 6. classes.json is auto-saved alongside model during training

# 7. Rebuild and test
cd ../../..
docker compose build backend
docker compose up -d
```

**Per the paper's methodology:** The pipeline follows the same approach as the Teeline recognition paper — CNN on digital-pen/SVG-derived images, grayscale, binary-inverted, augmented with rotation/shift/noise, trained with categorical crossentropy. The paper used 28x28 images and 27 classes reaching 92% with 3 epochs. Our pipeline uses 64x64 images (more detail for complex groupings) and will have 78 classes. The paper's 200 images per class is our minimum target — `--samples 200` in the generator plus `--factor 10` augmentation gives 2000 effective training images per class.

**Expected class list (78 total):**
- 26 single letters: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
- 52 groupings: ABT ANY AS BD BT CD CHF CM CR CV DB DR FB FL FM FR FW HV IF IS IT MB MN MNY MR NO NV NW O OM ON OTHR PV RF SD SE SHE SM SN SO TB THS TLN TR_THR US VN WF WN WR WRD WS
