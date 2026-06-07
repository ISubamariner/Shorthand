"""Evaluate trained model — confusion matrix, per-class accuracy, plots.

Usage:
    python evaluate.py --model ../saved_model --data ../../data/augmented
"""

import argparse
import os

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

IMG_SIZE = 64


def discover_classes(data_dir: str) -> list[str]:
    return sorted(
        d for d in os.listdir(data_dir)
        if os.path.isdir(os.path.join(data_dir, d))
        and any(f.endswith(".png") for f in os.listdir(os.path.join(data_dir, d)))
    )


def main():
    parser = argparse.ArgumentParser(description="Evaluate Teeline classifier")
    parser.add_argument("--model", default="../saved_model")
    parser.add_argument("--data", default="../../data/augmented")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    classes = discover_classes(args.data)
    model = tf.keras.models.load_model(args.model)

    datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1.0 / 255)
    test_gen = datagen.flow_from_directory(
        args.data,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=args.batch_size,
        class_mode="categorical",
        shuffle=False,
        classes=classes,
    )

    predictions = model.predict(test_gen)
    y_pred = np.argmax(predictions, axis=1)
    y_true = test_gen.classes

    print("\n=== Classification Report ===\n")
    print(classification_report(y_true, y_pred, target_names=classes))

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
        tick_marks = np.arange(len(classes))
        ax.set_xticks(tick_marks)
        ax.set_xticklabels(classes, fontsize=8)
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(classes, fontsize=8)
        fig.colorbar(im)
        plt.tight_layout()
        plt.savefig("confusion_matrix.png", dpi=150)
        print("\nConfusion matrix plot saved to confusion_matrix.png")
    except ImportError:
        print("\nmatplotlib not available — skipping plot")

    weak = []
    for i, letter in enumerate(classes):
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
