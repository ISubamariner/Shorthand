from checker.models import Attempt
from ml.inference import predictor

from .handlers import register
from .models import Job


@register("predict")
def handle_predict(job: Job) -> None:
    attempt = Attempt.objects.select_related("symbol").get(id=job.payload["attempt_id"])

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
