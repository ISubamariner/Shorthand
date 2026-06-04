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
