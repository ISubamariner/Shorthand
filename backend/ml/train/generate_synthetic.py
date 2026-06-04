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
