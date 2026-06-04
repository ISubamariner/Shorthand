import base64
import logging

from .models import Attempt
from ml.inference import predictor

logger = logging.getLogger(__name__)


def process_and_predict(attempt_id: str):
    try:
        attempt = Attempt.objects.select_related("symbol").get(id=attempt_id)
    except Attempt.DoesNotExist:
        logger.error("Attempt %s not found", attempt_id)
        return

    attempt.status = "processing"
    attempt.save(update_fields=["status"])

    try:
        # Fetch the image bytes from the stored URL
        # In production this would download from Supabase Storage
        # For now, we pass empty bytes which triggers stub predictions
        # until a real model.tflite is committed
        predictions = predictor.predict(b"")

        top = predictions[0]
        attempt.predicted_label = top["label"]
        attempt.confidence = top["confidence"]
        attempt.is_correct = attempt.predicted_label == attempt.symbol.letter
        attempt.status = "completed"
        attempt.save(update_fields=["predicted_label", "confidence", "is_correct", "status"])
    except Exception as e:
        logger.exception("Prediction failed for attempt %s", attempt_id)
        attempt.status = "failed"
        attempt.save(update_fields=["status"])
