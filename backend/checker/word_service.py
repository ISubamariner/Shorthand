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
