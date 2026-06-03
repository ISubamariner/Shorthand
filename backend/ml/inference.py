class TFLitePredictor:
    """Stub — real implementation in Phase 3."""

    def predict(self, image_bytes: bytes) -> list[dict]:
        return [
            {"label": "A", "confidence": 0.0},
            {"label": "B", "confidence": 0.0},
            {"label": "C", "confidence": 0.0},
        ]


predictor = TFLitePredictor()
