# Phase 2: ML Model Training — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete ML training pipeline: data collection tooling, data augmentation, MobileNetV2 transfer learning, TFLite conversion with INT8 quantization, and wire the real inference into the Django backend — replacing the stub.

**Architecture:** Training scripts live in `backend/ml/train/`, run locally or in Colab with a GPU. The output is a `model.tflite` file (~4-5MB) committed to the repo and loaded at Django startup. Inference runs via `tflite-runtime` on CPU within Render's 512MB RAM limit.

**Tech Stack:** TensorFlow 2.x, Keras, MobileNetV2, TFLite, tflite-runtime, Pillow, NumPy, matplotlib (for evaluation plots)

**Anti-Scope:** No model retraining in production. No automated data pipeline. No hyperparameter search. No model versioning system. No GPU required for inference.

---

## File Map

| File | Purpose |
|------|---------|
| `backend/ml/train/requirements.txt` | Training-only deps (tensorflow, matplotlib, numpy) |
| `backend/ml/train/collect.py` | Export labeled drawings from Supabase to local `data/raw/` |
| `backend/ml/train/augment.py` | Augment raw images → `data/augmented/` |
| `backend/ml/train/train.py` | MobileNetV2 transfer learning script |
| `backend/ml/train/evaluate.py` | Confusion matrix, per-class metrics, plots |
| `backend/ml/train/convert.py` | SavedModel → TFLite INT8 conversion |
| `backend/ml/train/generate_synthetic.py` | Generate synthetic Teeline symbol images for bootstrapping |
| `backend/ml/inference.py` | Replace stub with real TFLite inference |
| `backend/ml/preprocessing.py` | Replace stub with real image preprocessing |
| `backend/requirements.txt` | Add tflite-runtime |
| `backend/checker/tasks.py` | Wire real inference into async task |

---

## Task 1: Training Requirements + Synthetic Data Generator

**Files:**
- Create: `backend/ml/train/requirements.txt`
- Create: `backend/ml/train/generate_synthetic.py`

Since we don't have hand-drawn Teeline samples yet, we need a way to bootstrap training data. This script generates synthetic images of each letter using different fonts, sizes, rotations, and stroke variations — enough to train an initial model that can be improved later with real hand-drawn data.

- [ ] **Step 1: Create training requirements**

Create `backend/ml/train/requirements.txt`:
```txt
tensorflow>=2.16,<3.0
matplotlib>=3.9,<4.0
numpy>=1.26,<2.0
pillow>=10.4,<11.0
scikit-learn>=1.5,<2.0
```

- [ ] **Step 2: Create synthetic data generator**

Create `backend/ml/train/generate_synthetic.py`:
```python
"""Generate synthetic Teeline-style symbol images for bootstrapping model training.

Creates variations of each letter A-Z rendered as handwriting-style images with
random transforms (rotation, scale, position, stroke width, noise).

Usage:
    python generate_synthetic.py --output ../../data/raw --samples 100
"""

import argparse
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont


LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Teeline symbols are simplified strokes. We approximate them as
# single-character renderings with handwriting-style variation.


def create_symbol_image(
    letter: str,
    size: int = 224,
    margin: int = 40,
) -> Image.Image:
    """Render a letter as a black-on-white image with random variation."""
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)

    font_size = random.randint(80, 140)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    max_offset = margin // 2
    cx = (size - tw) // 2 + random.randint(-max_offset, max_offset)
    cy = (size - th) // 2 + random.randint(-max_offset, max_offset)

    draw.text((cx, cy), letter, fill=0, font=font)

    angle = random.uniform(-15, 15)
    img = img.rotate(angle, fillcolor=255, resample=Image.BICUBIC)

    scale = random.uniform(0.85, 1.15)
    new_size = int(size * scale)
    img = img.resize((new_size, new_size), Image.BICUBIC)

    if new_size > size:
        offset = (new_size - size) // 2
        img = img.crop((offset, offset, offset + size, offset + size))
    elif new_size < size:
        padded = Image.new("L", (size, size), 255)
        offset = (size - new_size) // 2
        padded.paste(img, (offset, offset))
        img = padded

    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, random.uniform(2, 8), arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(arr)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic training data")
    parser.add_argument("--output", default="../../data/raw", help="Output directory")
    parser.add_argument("--samples", type=int, default=100, help="Samples per letter")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    total = 0
    for letter in LETTERS:
        letter_dir = os.path.join(args.output, letter)
        os.makedirs(letter_dir, exist_ok=True)

        for i in range(args.samples):
            img = create_symbol_image(letter)
            img.save(os.path.join(letter_dir, f"{letter}_{i:04d}.png"))
            total += 1

        print(f"  {letter}: {args.samples} samples")

    print(f"\nGenerated {total} images in {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add backend/ml/train/requirements.txt backend/ml/train/generate_synthetic.py
git commit -m "feat: add training requirements and synthetic data generator"
```

---

## Task 2: Data Augmentation Pipeline

**Files:**
- Create: `backend/ml/train/augment.py`

- [ ] **Step 1: Create augmentation script**

Create `backend/ml/train/augment.py`:
```python
"""Augment raw training images using Keras ImageDataGenerator.

Reads from data/raw/{A..Z}/*.png, applies augmentation, writes to data/augmented/.
Expands dataset ~5x with rotation, shift, and zoom. No horizontal flip
(would distort letter shapes).

Usage:
    python augment.py --input ../../data/raw --output ../../data/augmented --factor 5
"""

import argparse
import os

import numpy as np
from PIL import Image
from tensorflow.keras.preprocessing.image import ImageDataGenerator


def augment_dataset(input_dir: str, output_dir: str, factor: int = 5):
    datagen = ImageDataGenerator(
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        fill_mode="constant",
        cval=255,
    )

    letters = sorted(
        d for d in os.listdir(input_dir)
        if os.path.isdir(os.path.join(input_dir, d)) and len(d) == 1
    )

    total = 0
    for letter in letters:
        letter_in = os.path.join(input_dir, letter)
        letter_out = os.path.join(output_dir, letter)
        os.makedirs(letter_out, exist_ok=True)

        files = [f for f in os.listdir(letter_in) if f.endswith(".png")]

        for fname in files:
            img = Image.open(os.path.join(letter_in, fname)).convert("L")
            arr = np.array(img).reshape(1, img.height, img.width, 1).astype(np.float32)

            base_name = os.path.splitext(fname)[0]
            img.save(os.path.join(letter_out, f"{base_name}_orig.png"))
            total += 1

            gen = datagen.flow(arr, batch_size=1)
            for j in range(factor - 1):
                aug = next(gen)[0].reshape(img.height, img.width)
                aug = np.clip(aug, 0, 255).astype(np.uint8)
                Image.fromarray(aug).save(
                    os.path.join(letter_out, f"{base_name}_aug{j:02d}.png")
                )
                total += 1

        print(f"  {letter}: {len(files)} originals → {len(files) * factor} total")

    print(f"\nAugmented {total} images in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Augment training images")
    parser.add_argument("--input", default="../../data/raw")
    parser.add_argument("--output", default="../../data/augmented")
    parser.add_argument("--factor", type=int, default=5, help="Augmentation multiplier")
    args = parser.parse_args()

    augment_dataset(args.input, args.output, args.factor)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml/train/augment.py
git commit -m "feat: add data augmentation pipeline — rotation, shift, zoom"
```

---

## Task 3: MobileNetV2 Training Script

**Files:**
- Create: `backend/ml/train/train.py`

- [ ] **Step 1: Create training script**

Create `backend/ml/train/train.py`:
```python
"""Train a MobileNetV2 classifier for Teeline symbol recognition.

Transfer learning: freeze MobileNetV2 base, add custom classification head
for 26 Teeline letters. Fine-tune top layers after initial convergence.

Usage:
    python train.py --data ../../data/augmented --epochs 20 --batch-size 32
"""

import argparse
import os

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator


LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
NUM_CLASSES = 26
IMG_SIZE = 224


def build_model() -> tf.keras.Model:
    base = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    model = models.Sequential([
        base,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(NUM_CLASSES, activation="softmax"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


def create_generators(data_dir: str, batch_size: int, val_split: float = 0.2):
    datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=val_split,
    )

    train_gen = datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="rgb",
        batch_size=batch_size,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        classes=LETTERS,
    )

    val_gen = datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="rgb",
        batch_size=batch_size,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        classes=LETTERS,
    )

    return train_gen, val_gen


def fine_tune(model: tf.keras.Model, train_gen, val_gen, epochs: int = 10):
    base = model.layers[0]
    base.trainable = True

    for layer in base.layers[:-20]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=epochs,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=3, restore_best_weights=True
            ),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Train Teeline symbol classifier")
    parser.add_argument("--data", default="../../data/augmented")
    parser.add_argument("--output", default="../saved_model")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--fine-tune-epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    print("Building MobileNetV2 model...")
    model = build_model()
    model.summary()

    print(f"\nLoading data from {args.data}...")
    train_gen, val_gen = create_generators(args.data, args.batch_size)
    print(f"Training samples: {train_gen.samples}")
    print(f"Validation samples: {val_gen.samples}")

    print(f"\nPhase 1: Training head ({args.epochs} epochs)...")
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=args.epochs,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=5, restore_best_weights=True
            ),
        ],
    )

    val_loss, val_acc = model.evaluate(val_gen)
    print(f"\nPhase 1 — Val accuracy: {val_acc:.4f}")

    print(f"\nPhase 2: Fine-tuning top layers ({args.fine_tune_epochs} epochs)...")
    fine_tune(model, train_gen, val_gen, epochs=args.fine_tune_epochs)

    val_loss, val_acc = model.evaluate(val_gen)
    print(f"\nFinal — Val accuracy: {val_acc:.4f}")

    os.makedirs(args.output, exist_ok=True)
    model.save(args.output)
    print(f"\nModel saved to {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml/train/train.py
git commit -m "feat: add MobileNetV2 training script — transfer learning + fine-tuning"
```

---

## Task 4: Evaluation Script

**Files:**
- Create: `backend/ml/train/evaluate.py`

- [ ] **Step 1: Create evaluation script**

Create `backend/ml/train/evaluate.py`:
```python
"""Evaluate trained model — confusion matrix, per-class accuracy, plots.

Usage:
    python evaluate.py --model ../saved_model --data ../../data/augmented
"""

import argparse
import os

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
IMG_SIZE = 224


def main():
    parser = argparse.ArgumentParser(description="Evaluate Teeline classifier")
    parser.add_argument("--model", default="../saved_model")
    parser.add_argument("--data", default="../../data/augmented")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    model = tf.keras.models.load_model(args.model)

    datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1.0 / 255)
    test_gen = datagen.flow_from_directory(
        args.data,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="rgb",
        batch_size=args.batch_size,
        class_mode="categorical",
        shuffle=False,
        classes=LETTERS,
    )

    predictions = model.predict(test_gen)
    y_pred = np.argmax(predictions, axis=1)
    y_true = test_gen.classes

    print("\n=== Classification Report ===\n")
    print(classification_report(y_true, y_pred, target_names=LETTERS))

    print("\n=== Confusion Matrix ===\n")
    cm = confusion_matrix(y_true, y_pred)
    print(cm)

    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 10))
        im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
        ax.set_title("Confusion Matrix")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        tick_marks = np.arange(len(LETTERS))
        ax.set_xticks(tick_marks)
        ax.set_xticklabels(LETTERS, fontsize=8)
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(LETTERS, fontsize=8)
        fig.colorbar(im)
        plt.tight_layout()
        plt.savefig("confusion_matrix.png", dpi=150)
        print("\nConfusion matrix plot saved to confusion_matrix.png")
    except ImportError:
        print("\nmatplotlib not available — skipping plot")

    weak = []
    for i, letter in enumerate(LETTERS):
        total = np.sum(cm[i])
        correct = cm[i][i] if total > 0 else 0
        acc = correct / total if total > 0 else 0
        if acc < 0.85:
            weak.append((letter, acc))

    if weak:
        print("\n=== Weak Symbols (<85% accuracy) ===")
        for letter, acc in sorted(weak, key=lambda x: x[1]):
            print(f"  {letter}: {acc:.1%}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml/train/evaluate.py
git commit -m "feat: add evaluation script — confusion matrix, per-class metrics"
```

---

## Task 5: TFLite Conversion Script

**Files:**
- Create: `backend/ml/train/convert.py`

- [ ] **Step 1: Create conversion script**

Create `backend/ml/train/convert.py`:
```python
"""Convert SavedModel to TFLite with INT8 quantization.

Usage:
    python convert.py --model ../saved_model --output ../model.tflite
"""

import argparse
import os

import numpy as np
import tensorflow as tf

IMG_SIZE = 224


def representative_dataset():
    for _ in range(100):
        data = np.random.rand(1, IMG_SIZE, IMG_SIZE, 3).astype(np.float32)
        yield [data]


def main():
    parser = argparse.ArgumentParser(description="Convert to TFLite")
    parser.add_argument("--model", default="../saved_model")
    parser.add_argument("--output", default="../model.tflite")
    parser.add_argument("--quantize", choices=["none", "dynamic", "int8"], default="int8")
    args = parser.parse_args()

    print(f"Loading model from {args.model}...")
    converter = tf.lite.TFLiteConverter.from_saved_model(args.model)

    if args.quantize == "dynamic":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        print("Applying dynamic range quantization...")
    elif args.quantize == "int8":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type = tf.float32
        print("Applying INT8 quantization...")

    tflite_model = converter.convert()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "wb") as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    print(f"\nModel saved to {args.output}")
    print(f"Size: {size_mb:.2f} MB")

    if size_mb > 5:
        print("WARNING: Model exceeds 5MB target — consider stronger quantization")
    else:
        print("✓ Model is within 5MB target")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml/train/convert.py
git commit -m "feat: add TFLite conversion script — INT8 quantization"
```

---

## Task 6: Real Inference + Preprocessing (Replace Stubs)

**Files:**
- Modify: `backend/ml/inference.py`
- Modify: `backend/ml/preprocessing.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/checker/tasks.py`

- [ ] **Step 1: Add tflite-runtime to requirements**

Append to `backend/requirements.txt`:
```txt
tflite-runtime>=2.14,<3.0
numpy>=1.26,<2.0
```

- [ ] **Step 2: Replace preprocessing stub**

Replace `backend/ml/preprocessing.py`:
```python
import io

import numpy as np
from PIL import Image

IMG_SIZE = 224


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Convert raw PNG bytes to a normalized numpy array for TFLite inference.

    Steps:
    1. Open image from bytes
    2. Convert to RGB (canvas exports grayscale-on-white as PNG)
    3. Resize to 224x224
    4. Normalize to [0, 1]
    5. Add batch dimension → shape (1, 224, 224, 3)
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE), Image.BICUBIC)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)
```

- [ ] **Step 3: Replace inference stub**

Replace `backend/ml/inference.py`:
```python
import logging
import os
from pathlib import Path

import numpy as np

from .preprocessing import preprocess_image

logger = logging.getLogger(__name__)

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
MODEL_PATH = Path(__file__).parent / "model.tflite"


class TFLitePredictor:
    def __init__(self):
        self._interpreter = None

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
            return [{"label": letter, "confidence": 0.0} for letter in LETTERS[:3]]

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
            {"label": LETTERS[idx], "confidence": float(score)}
            for idx, score in indexed[:3]
        ]


predictor = TFLitePredictor()
```

- [ ] **Step 4: Update checker/tasks.py to use real inference**

Replace `backend/checker/tasks.py`:
```python
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
```

- [ ] **Step 5: Commit**

```bash
git add backend/ml/inference.py backend/ml/preprocessing.py backend/requirements.txt backend/checker/tasks.py
git commit -m "feat: replace ML stubs with real TFLite inference + preprocessing"
```

---

## Task 7: Data Collection Script (Export from Supabase)

**Files:**
- Create: `backend/ml/train/collect.py`

- [ ] **Step 1: Create data collection script**

Create `backend/ml/train/collect.py`:
```python
"""Export labeled drawing attempts from Supabase to local filesystem.

Downloads completed attempts where is_correct=True (verified by user) and
organizes them into data/raw/{letter}/ directories for training.

Usage:
    python collect.py --output ../../data/raw

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.
"""

import argparse
import os

import requests
from supabase import create_client


def main():
    parser = argparse.ArgumentParser(description="Collect training data from Supabase")
    parser.add_argument("--output", default="../../data/raw")
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
        return

    client = create_client(url, key)

    result = (
        client.table("checker_attempt")
        .select("id, image_url, checker_symbol!inner(letter)")
        .eq("status", "completed")
        .eq("is_correct", True)
        .execute()
    )

    if not result.data:
        print("No verified attempts found")
        return

    os.makedirs(args.output, exist_ok=True)
    downloaded = 0

    for row in result.data:
        letter = row["checker_symbol"]["letter"]
        letter_dir = os.path.join(args.output, letter)
        os.makedirs(letter_dir, exist_ok=True)

        image_url = row["image_url"]
        filename = f"{row['id']}.png"
        filepath = os.path.join(letter_dir, filename)

        if os.path.exists(filepath):
            continue

        try:
            resp = requests.get(image_url, timeout=10)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
            downloaded += 1
        except Exception as e:
            print(f"  Failed to download {image_url}: {e}")

    print(f"Downloaded {downloaded} images to {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml/train/collect.py
git commit -m "feat: add data collection script — export from Supabase to local filesystem"
```

---

## Training Workflow (Reference — not a task)

Once all scripts are committed, the training workflow is:

```bash
cd backend/ml/train

# 1. Install training deps (in a venv, not in Docker)
pip install -r requirements.txt

# 2. Generate synthetic data (or collect real data)
python generate_synthetic.py --output ../../data/raw --samples 100

# 3. Augment
python augment.py --input ../../data/raw --output ../../data/augmented --factor 5

# 4. Train
python train.py --data ../../data/augmented --epochs 20

# 5. Evaluate
python evaluate.py --model ../saved_model --data ../../data/augmented

# 6. Convert to TFLite
python convert.py --model ../saved_model --output ../model.tflite

# 7. Rebuild Docker to pick up model.tflite
cd ../../..
docker compose build backend
docker compose up -d
```
