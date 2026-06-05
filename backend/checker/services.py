import base64

from django.contrib.auth.models import User

from jobs.repository import JobRepository

from .repositories import AttemptRepository, SymbolRepository


def submit_attempt(user: User, symbol_letter: str, image_data: str):
    symbol = SymbolRepository.get_by_letter(symbol_letter)

    image_bytes = base64.b64decode(image_data)

    attempt = AttemptRepository.create(
        user=user,
        symbol=symbol,
        image_data=image_bytes,
    )

    JobRepository.enqueue(
        job_type="predict",
        payload={"attempt_id": str(attempt.id)},
        user=user,
        correlation_key=f"predict:{attempt.id}",
    )

    return attempt


def get_user_progress(user: User) -> dict:
    return {
        "symbols": AttemptRepository.get_user_progress(user),
        "current_streak": AttemptRepository.get_current_streak(user),
    }
