import base64
import uuid

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest

from accounts.models import AnonymousSession
from jobs.repository import JobRepository

from .models import UserStats
from .repositories import AttemptRepository, SymbolRepository
from .word_repository import WordSessionRepository


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


def get_progress(
    user: User | None = None,
    session: AnonymousSession | None = None,
) -> dict:
    stats = None
    try:
        if user:
            stats = UserStats.objects.get(user=user)
        elif session:
            stats = UserStats.objects.get(anonymous_session=session)
    except UserStats.DoesNotExist:
        pass

    return {
        "symbols": AttemptRepository.get_progress(user=user, session=session),
        "current_streak": stats.current_streak if stats else 0,
        "best_streak": stats.best_streak if stats else 0,
        "total_score": stats.total_score if stats else 0,
    }


def claim_anonymous_session(session_token_str: str, user: User) -> int:
    """
    Transfer all attempts from an anonymous session to a user.
    Merges UserStats and deletes the AnonymousSession.
    Returns the number of attempts transferred.
    """
    session_token = uuid.UUID(session_token_str)

    with transaction.atomic():
        session = AnonymousSession.objects.get(session_token=session_token)

        attempts_count = AttemptRepository.transfer_session_to_user(session, user)
        WordSessionRepository.transfer_session_to_user(session, user)

        try:
            session_stats = UserStats.objects.select_for_update().get(
                anonymous_session=session
            )
            user_stats, _ = UserStats.objects.select_for_update().get_or_create(
                user=user
            )

            user_stats.total_score += session_stats.total_score
            user_stats.best_streak = max(
                user_stats.best_streak,
                session_stats.best_streak,
                user_stats.current_streak,
                session_stats.current_streak,
            )
            user_stats.current_streak = 0
            user_stats.save()

            session_stats.delete()
        except UserStats.DoesNotExist:
            pass

        session.delete()

    return attempts_count


def record_score(attempt):
    """
    Record score for an attempt and update UserStats.
    Called after prediction is complete.
    Uses select_for_update to prevent race conditions on concurrent scoring.
    """
    with transaction.atomic():
        if attempt.user:
            stats, _ = UserStats.objects.select_for_update().get_or_create(
                user=attempt.user
            )
        elif attempt.anonymous_session:
            stats, _ = UserStats.objects.select_for_update().get_or_create(
                anonymous_session=attempt.anonymous_session
            )
        else:
            return

        if attempt.is_correct:
            new_streak = stats.current_streak + 1
            streak_bonus = 5 if new_streak % 5 == 0 else 0
            confidence_bonus = round((attempt.confidence or 0) * 5)
            points = 10 + streak_bonus + confidence_bonus

            stats.current_streak = new_streak
            stats.total_score = F("total_score") + points
            stats.best_streak = Greatest(F("best_streak"), new_streak)
            stats.save(update_fields=["current_streak", "total_score", "best_streak"])
        else:
            points = 0
            stats.current_streak = 0
            stats.save(update_fields=["current_streak"])

        attempt.points = points
        attempt.save(update_fields=["points"])
