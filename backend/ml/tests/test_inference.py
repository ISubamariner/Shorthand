import json
import os
import tempfile
from django.test import TestCase
from ml.inference import load_class_labels


class InferenceClassLoadingTest(TestCase):
    def test_loads_classes_from_json(self):
        classes = ["A", "B", "CM", "SH"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(classes, f)
            f.flush()
            result = load_class_labels(f.name)
        assert result == classes
        os.unlink(f.name)

    def test_falls_back_to_alphabet(self):
        result = load_class_labels("/nonexistent/classes.json")
        assert result == list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        assert len(result) == 26
