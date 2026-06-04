"""Augment raw training images using Pillow transforms.

Reads from data/raw/{A..Z}/*.png, applies augmentation, writes to data/augmented/.
Expands dataset ~5x with rotation, shift, and zoom. No horizontal flip
(would distort letter shapes).

Usage:
    python augment.py --input ../../data/raw --output ../../data/augmented --factor 5
"""

import argparse
import os
import random

import numpy as np
from PIL import Image


def augment_image(img: Image.Image) -> Image.Image:
    """Apply random rotation, shift, and zoom to a grayscale image."""
    w, h = img.size

    angle = random.uniform(-15, 15)
    aug = img.rotate(angle, fillcolor=255, resample=Image.BICUBIC)

    shift_x = int(w * random.uniform(-0.1, 0.1))
    shift_y = int(h * random.uniform(-0.1, 0.1))
    aug = aug.transform(
        (w, h), Image.AFFINE, (1, 0, -shift_x, 0, 1, -shift_y),
        fillcolor=255, resample=Image.BICUBIC,
    )

    zoom = random.uniform(0.9, 1.1)
    new_w, new_h = int(w * zoom), int(h * zoom)
    aug = aug.resize((new_w, new_h), Image.BICUBIC)
    if new_w > w:
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        aug = aug.crop((left, top, left + w, top + h))
    elif new_w < w:
        padded = Image.new("L", (w, h), 255)
        padded.paste(aug, ((w - new_w) // 2, (h - new_h) // 2))
        aug = padded

    return aug


def augment_dataset(input_dir: str, output_dir: str, factor: int = 5):
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
            base_name = os.path.splitext(fname)[0]

            img.save(os.path.join(letter_out, f"{base_name}_orig.png"))
            total += 1

            for j in range(factor - 1):
                aug = augment_image(img)
                aug.save(os.path.join(letter_out, f"{base_name}_aug{j:02d}.png"))
                total += 1

        print(f"  {letter}: {len(files)} originals -> {len(files) * factor} total")

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
