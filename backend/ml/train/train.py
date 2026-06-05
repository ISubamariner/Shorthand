"""Train a CNN classifier for Teeline symbol recognition.

Purpose-built CNN for binary line drawings. Uses 64x64 grayscale input
with runtime augmentation.

Usage:
    python train.py --data ../../data/augmented --epochs 100 --batch-size 32
"""

import argparse
import os
import sys

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator


LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
NUM_CLASSES = 26
IMG_SIZE = 64


def build_model() -> tf.keras.Model:
    model = models.Sequential([
        layers.Input(shape=(IMG_SIZE, IMG_SIZE, 1)),

        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Flatten(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.4),
        layers.Dense(NUM_CLASSES, activation="softmax"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


def create_generators(data_dir: str, batch_size: int, val_split: float = 0.2):
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=val_split,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        fill_mode="constant",
        cval=0,
    )

    val_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=val_split,
    )

    train_gen = train_datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=batch_size,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        classes=LETTERS,
    )

    val_gen = val_datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=batch_size,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        classes=LETTERS,
    )

    return train_gen, val_gen


def main():
    parser = argparse.ArgumentParser(description="Train Teeline symbol classifier")
    parser.add_argument("--data", default="../../data/augmented")
    parser.add_argument("--output", default="../model.keras")
    parser.add_argument("--tflite-output", default="../model.tflite")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    print("Building CNN model...")
    model = build_model()
    model.summary()

    print(f"\nLoading data from {args.data}...")
    train_gen, val_gen = create_generators(args.data, args.batch_size)
    print(f"Training samples: {train_gen.samples}")
    print(f"Validation samples: {val_gen.samples}")

    print(f"\nTraining ({args.epochs} epochs max, early stopping)...")
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=args.epochs,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=10, restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6
            ),
        ],
    )

    val_loss, val_acc = model.evaluate(val_gen)
    print(f"\nFinal — Val loss: {val_loss:.4f}, Val accuracy: {val_acc:.4f}")

    model.save(args.output)
    print(f"Keras model saved to {args.output}")

    # Convert to TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(args.tflite_output, "wb") as f:
        f.write(tflite_model)
    print(f"TFLite model saved to {args.tflite_output}")


if __name__ == "__main__":
    main()
