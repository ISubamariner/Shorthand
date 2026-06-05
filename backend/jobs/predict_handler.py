import logging

from checker.models import Attempt
from checker.services import record_score
from ml.inference import predictor

logger = logging.getLogger(__name__)

from .handlers import register
from .models import Job


@register("predict")
def handle_predict(job: Job) -> None:
    attempt = Attempt.objects.select_related("symbol", "user", "anonymous_session").get(
        id=job.payload["attempt_id"]
    )

    attempt.status = Attempt.Status.PROCESSING
    attempt.save(update_fields=["status"])

    image_bytes = bytes(attempt.image_data)
    predictions = predictor.predict(image_bytes)

    top = predictions[0]
    attempt.predicted_label = top["label"]
    attempt.confidence = top["confidence"]
    attempt.is_correct = attempt.predicted_label == attempt.symbol.letter
    attempt.status = Attempt.Status.COMPLETED
    attempt.save(update_fields=["predicted_label", "confidence", "is_correct", "status"])

    try:
        record_score(attempt)
    except Exception:
        logger.exception("Failed to record score for attempt %s", attempt.id)
    finally:
        attempt.image_data = b""
        attempt.save(update_fields=["image_data"])
