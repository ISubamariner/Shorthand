from .models import Attempt
from ml.inference import predictor


def process_and_predict(attempt_id: str):
    attempt = Attempt.objects.get(id=attempt_id)
    attempt.status = "processing"
    attempt.save(update_fields=["status"])

    predictions = predictor.predict(b"")

    top_prediction = predictions[0]
    attempt.predicted_label = top_prediction["label"]
    attempt.confidence = top_prediction["confidence"]
    attempt.is_correct = attempt.predicted_label == attempt.symbol.letter
    attempt.status = "completed"
    attempt.save(update_fields=["predicted_label", "confidence", "is_correct", "status"])
