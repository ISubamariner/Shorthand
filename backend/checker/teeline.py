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


def _greedy_match(skeleton: str, known_groupings: list[str]) -> list[str]:
    """Greedy longest-match of consonant skeleton against known groupings."""
    expanded = set()
    for g in known_groupings:
        for variant in g.split("/"):
            expanded.add(variant)

    max_len = max((len(g) for g in expanded), default=1)

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


def resolve_special_outline(word, special_outlines=None):
    """Resolve a word to its special outline if one exists."""
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


def decompose(word: str, known_groupings: list[str] | None = None) -> list[dict]:
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

        # Build the result
        result = first + middle

        # Keep last letter if it's a consonant, or if we'd have no letters otherwise
        if last not in VOWELS or len(result) == 0:
            result += last
        # Or if the middle had consonants and last is a vowel, check if we should keep it
        elif len(middle) == 0:
            result += last

        text = result
    elif len(text) == 2:
        # For 2-letter words: special handling
        if text[0] not in VOWELS and text[1] in VOWELS:
            # consonant-vowel: drop trailing E, keep other vowels
            if text[1] == 'E':
                text = text[0]
            # else keep both (like "go" -> "GO")
        elif text[0] in VOWELS and text[1] in VOWELS:
            # two vowels: keep first
            text = text[0]
        # else: keep both (vowel-consonant or two consonants)

    # If known_groupings provided, use greedy matching
    if known_groupings:
        units = _greedy_match(text, known_groupings)
        components = []
        for idx, unit in enumerate(units):
            components.append({
                "letter": unit,
                "blend_with": None,
                "is_doubled_for_r": False,
                "position": idx,
            })
        return components

    # Otherwise, use original per-letter logic with blend/R-doubling detection
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


def decompose_to_letters(word: str, known_groupings: list[str] | None = None) -> str:
    return "".join(c["letter"] for c in decompose(word, known_groupings=known_groupings))
