import json
import logging
import os
from pathlib import Path

import numpy as np

from .preprocessing import preprocess_image  # now returns (1, 64, 64, 1)

logger = logging.getLogger(__name__)

ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
MODEL_PATH = Path(__file__).parent / "model.tflite"
CLASSES_PATH = Path(__file__).parent / "classes.json"


def load_class_labels(classes_path=CLASSES_PATH):
    path = Path(classes_path)
    if path.exists():
        try:
            with open(path, "r") as f:
                labels = json.load(f)
            logger.info("Loaded %d class labels from %s", len(labels), path)
            return labels
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to read %s: %s — using alphabet fallback", path, e)
    return list(ALPHABET)


class TFLitePredictor:
    def __init__(self):
        self._interpreter = None
        self._labels = load_class_labels()

        if MODEL_PATH.exists():
            try:
                import tflite_runtime.interpreter as tflite

                self._interpreter = tflite.Interpreter(model_path=str(MODEL_PATH))
                self._interpreter.allocate_tensors()
                self._input_details = self._interpreter.get_input_details()
                self._output_details = self._interpreter.get_output_details()
                logger.info("TFLite model loaded from %s", MODEL_PATH)
            except Exception as e:
                logger.warning("Failed to load TFLite model: %s — using stub predictions", e)
        else:
            logger.warning("No model.tflite found at %s — using stub predictions", MODEL_PATH)

    def predict(self, image_bytes: bytes) -> list[dict]:
        if self._interpreter is None:
            return [{"label": letter, "confidence": 0.0} for letter in self._labels[:3]]

        input_data = preprocess_image(image_bytes)

        input_detail = self._input_details[0]
        if input_detail["dtype"] == np.uint8:
            scale, zero_point = input_detail["quantization"]
            input_data = (input_data / scale + zero_point).astype(np.uint8)

        self._interpreter.set_tensor(input_detail["index"], input_data)
        self._interpreter.invoke()

        output_data = self._interpreter.get_tensor(self._output_details[0]["index"])
        scores = output_data[0]

        if scores.dtype == np.uint8:
            scale, zero_point = self._output_details[0]["quantization"]
            scores = (scores.astype(np.float32) - zero_point) * scale

        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)

        return [
            {"label": self._labels[idx], "confidence": float(score)}
            for idx, score in indexed[:3]
        ]


predictor = TFLitePredictor()
