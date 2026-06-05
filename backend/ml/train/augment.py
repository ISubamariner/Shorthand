"""Augment raw training images with preprocessing for Teeline recognition.

Reads from data/raw/{A..Z}/*.png, applies binarization + centering + augmentation,
writes to data/augmented/. Produces clean binary stroke images ready for training.

Usage:
    python augment.py --input ../../data/raw --output ../../data/augmented --factor 10
"""

import argparse
import os
import random
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from preprocessing import binarize_and_center, IMG_SIZE


def augment_image(img: Image.Image) -> Image.Image:
    """Apply random rotation, shift, zoom, and thickness jitter."""
    w, h = img.size

    angle = random.uniform(-15, 15)
    aug = img.rotate(angle, fillcolor=0, resample=Image.BICUBIC)

    shift_x = int(w * random.uniform(-0.1, 0.1))
    shift_y = int(h * random.uniform(-0.1, 0.1))
    aug = aug.transform(
        (w, h), Image.AFFINE, (1, 0, -shift_x, 0, 1, -shift_y),
        fillcolor=0, resample=Image.BICUBIC,
    )

    zoom = random.uniform(0.9, 1.1)
    new_w, new_h = int(w * zoom), int(h * zoom)
    aug = aug.resize((new_w, new_h), Image.BICUBIC)
    if new_w > w:
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        aug = aug.crop((left, top, left + w, top + h))
    elif new_w < w:
        padded = Image.new("L", (w, h), 0)
        padded.paste(aug, ((w - new_w) // 2, (h - new_h) // 2))
        aug = padded

    # Stroke thickness jitter: randomly dilate or erode by 1px
    if random.random() < 0.3:
        aug = aug.filter(ImageFilter.MaxFilter(3))  # dilate
    elif random.random() < 0.3:
        aug = aug.filter(ImageFilter.MinFilter(3))  # erode

    return aug


def augment_dataset(input_dir: str, output_dir: str, factor: int = 10):
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
            processed = binarize_and_center(img)
            base_name = os.path.splitext(fname)[0]

            processed.save(os.path.join(letter_out, f"{base_name}_orig.png"))
            total += 1

            for j in range(factor - 1):
                aug = augment_image(processed)
                aug.save(os.path.join(letter_out, f"{base_name}_aug{j:02d}.png"))
                total += 1

        print(f"  {letter}: {len(files)} originals -> {len(files) * factor} total")

    print(f"\nAugmented {total} images in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Augment training images")
    parser.add_argument("--input", default="../../data/raw")
    parser.add_argument("--output", default="../../data/augmented")
    parser.add_argument("--factor", type=int, default=10, help="Augmentation multiplier")
    args = parser.parse_args()

    augment_dataset(args.input, args.output, args.factor)


if __name__ == "__main__":
    main()
