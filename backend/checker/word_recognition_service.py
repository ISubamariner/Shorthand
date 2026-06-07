from . import teeline_index


def _word_to_dict(w) -> dict:
    return {
        "word_id": str(w.id),
        "text": w.text,
        "teeline_skeleton": w.teeline_skeleton,
        "difficulty": w.difficulty,
        "topic_name": w.topic.name if w.topic else None,
    }


def recognize_grouping(image_bytes: bytes) -> list[dict]:
    """Run ML prediction on a drawn grouping image."""
    from ml.inference import predictor
    return predictor.predict(image_bytes)


def suggest_words(grouping_sequence: list[str]) -> list[dict]:
    """Given a sequence of recognized groupings, return candidate words."""
    words = teeline_index.suggest_from_groupings(grouping_sequence)
    return [_word_to_dict(w) for w in words[:20]]


def suggest_words_by_skeleton(skeleton: str) -> list[dict]:
    """Look up words by full skeleton string (dash-separated)."""
    words = teeline_index.lookup(skeleton)
    return [_word_to_dict(w) for w in words[:20]]


def suggest_words_by_prefix(prefix: str) -> list[dict]:
    """Look up words whose skeleton starts with the given prefix."""
    words = teeline_index.prefix_lookup(prefix)
    return [_word_to_dict(w) for w in words[:20]]
