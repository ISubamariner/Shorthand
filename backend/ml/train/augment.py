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
