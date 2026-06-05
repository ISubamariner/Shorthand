import base64
import logging

from django.contrib.auth.models import User

from ml.inference import predictor

from .repositories import AttemptRepository, SymbolRepository

logger = logging.getLogger(__name__)


def submit_attempt(user: User, symbol_letter: str, image_data: str):
    symbol = SymbolRepository.get_by_letter(symbol_letter)

    image_bytes = base64.b64decode(image_data)

    attempt = AttemptRepository.create(
        user=user,
        symbol=symbol,
        image_data=image_bytes,
    )

    try:
        predictions = predictor.predict(image_bytes)
        top = predictions[0]
        attempt.predicted_label = top["label"]
        attempt.confidence = top["confidence"]
        attempt.is_correct = attempt.predicted_label == symbol.letter
        attempt.status = "completed"
    except Exception:
        logger.exception("Prediction failed for attempt %s", attempt.id)
        attempt.status = "failed"

    attempt.save(update_fields=["predicted_label", "confidence", "is_correct", "status"])

    return attempt


def get_user_progress(user: User) -> dict:
    return {
        "symbols": AttemptRepository.get_user_progress(user),
        "current_streak": AttemptRepository.get_current_streak(user),
    }
