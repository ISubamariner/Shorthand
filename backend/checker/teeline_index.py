import threading
from collections import defaultdict

_index = None
_prefix_index = None
_lock = threading.Lock()


def _build():
    global _index, _prefix_index
    from .models import Word

    words = Word.objects.exclude(teeline_skeleton="").select_related("topic")
    new_index = defaultdict(list)
    new_prefix_index = defaultdict(list)

    for word in words:
        skeleton = word.teeline_skeleton
        new_index[skeleton].append(word)
        parts = skeleton.split("-")
        for i in range(1, len(parts) + 1):
            prefix = "-".join(parts[:i])
            new_prefix_index[prefix].append(word)

    _index = new_index
    _prefix_index = new_prefix_index


def invalidate():
    """Call after seeding or modifying words to rebuild the index."""
    global _index, _prefix_index
    with _lock:
        _index = None
        _prefix_index = None


def _ensure_built():
    if _index is None:
        with _lock:
            if _index is None:
                _build()


def lookup(skeleton: str) -> list:
    """Exact match: return words whose full skeleton matches."""
    _ensure_built()
    idx = _index
    return list(idx.get(skeleton, [])) if idx else []


def prefix_lookup(prefix: str) -> list:
    """Prefix match: return words whose skeleton starts with the given prefix."""
    _ensure_built()
    idx = _prefix_index
    return list(idx.get(prefix, [])) if idx else []


def suggest_from_groupings(groupings: list[str]) -> list:
    """Given a sequence of recognized groupings, find matching words.

    Tries exact match first, then prefix match.
    Returns list of Word objects (exact matches first, then prefix matches in DB order).
    """
    skeleton = "-".join(g.upper() for g in groupings)

    exact = lookup(skeleton)
    if exact:
        return exact

    return prefix_lookup(skeleton)
