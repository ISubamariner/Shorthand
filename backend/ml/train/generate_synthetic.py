"""Generate synthetic Teeline shorthand training images from reference SVGs.

Parses actual Teeline symbol SVGs (from gonzo-engineering/teeline-online),
extracts stroke paths, and renders them with random augmentation (rotation,
scale, position shift, stroke width, noise) to create training data.

Usage:
    python generate_synthetic.py --svgs ../../../data/reference/teeline-online/outline-svgs/alphabet --output ../../../data/raw --samples 100
"""

import argparse
import math
import os
import random
import re
import defusedxml.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw


LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def parse_svg_path(svg_file: str) -> list[list[tuple[float, float]]]:
    """Extract stroke polylines from an SVG file by sampling cubic bezier curves."""
    tree = ET.parse(svg_file)
    root = tree.getroot()

    strokes = []
    for path_el in root.iter("{http://www.w3.org/2000/svg}path"):
        d = path_el.get("d", "")
        transform = path_el.get("transform", "")

        tx, ty = 0.0, 0.0
        t_match = re.search(r"translate\(([-\d.]+),\s*([-\d.]+)\)", transform)
        if t_match:
            tx, ty = float(t_match.group(1)), float(t_match.group(2))

        points = parse_d_attribute(d)
        points = [(x + tx, y + ty) for x, y in points]

        if points:
            strokes.append(points)

    return strokes


def parse_d_attribute(d: str) -> list[tuple[float, float]]:
    """Parse SVG path d attribute into a list of (x, y) points by sampling curves."""
    tokens = re.findall(r"[MmCcLlZzQqSsHhVv]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d)

    points = []
    cx, cy = 0.0, 0.0
    i = 0
    current_cmd = ""

    while i < len(tokens):
        if tokens[i].isalpha():
            current_cmd = tokens[i]
            i += 1
        elif not current_cmd:
            i += 1
            continue

        cmd = current_cmd

        if cmd == "M":
            if i + 1 >= len(tokens):
                break
            cx, cy = float(tokens[i]), float(tokens[i + 1])
            points.append((cx, cy))
            i += 2
            current_cmd = "L"

        elif cmd == "m":
            if i + 1 >= len(tokens):
                break
            cx += float(tokens[i])
            cy += float(tokens[i + 1])
            points.append((cx, cy))
            i += 2
            current_cmd = "l"

        elif cmd == "L":
            if i + 1 >= len(tokens):
                break
            cx, cy = float(tokens[i]), float(tokens[i + 1])
            points.append((cx, cy))
            i += 2

        elif cmd == "l":
            if i + 1 >= len(tokens):
                break
            cx += float(tokens[i])
            cy += float(tokens[i + 1])
            points.append((cx, cy))
            i += 2

        elif cmd == "C":
            if i + 5 >= len(tokens):
                break
            x1, y1 = float(tokens[i]), float(tokens[i + 1])
            x2, y2 = float(tokens[i + 2]), float(tokens[i + 3])
            x3, y3 = float(tokens[i + 4]), float(tokens[i + 5])
            for t in [j / 20 for j in range(1, 21)]:
                bx = cubic_bezier(cx, x1, x2, x3, t)
                by = cubic_bezier(cy, y1, y2, y3, t)
                points.append((bx, by))
            cx, cy = x3, y3
            i += 6

        elif cmd == "c":
            if i + 5 >= len(tokens):
                break
            x1 = cx + float(tokens[i])
            y1 = cy + float(tokens[i + 1])
            x2 = cx + float(tokens[i + 2])
            y2 = cy + float(tokens[i + 3])
            x3 = cx + float(tokens[i + 4])
            y3 = cy + float(tokens[i + 5])
            for t in [j / 20 for j in range(1, 21)]:
                bx = cubic_bezier(cx, x1, x2, x3, t)
                by = cubic_bezier(cy, y1, y2, y3, t)
                points.append((bx, by))
            cx, cy = x3, y3
            i += 6

        elif cmd in ("Z", "z"):
            current_cmd = ""

        elif cmd == "H":
            if i >= len(tokens):
                break
            cx = float(tokens[i])
            points.append((cx, cy))
            i += 1

        elif cmd == "h":
            if i >= len(tokens):
                break
            cx += float(tokens[i])
            points.append((cx, cy))
            i += 1

        elif cmd == "V":
            if i >= len(tokens):
                break
            cy = float(tokens[i])
            points.append((cx, cy))
            i += 1

        elif cmd == "v":
            if i >= len(tokens):
                break
            cy += float(tokens[i])
            points.append((cx, cy))
            i += 1

        else:
            i += 1

    return points


def cubic_bezier(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * p1
        + 3 * (1 - t) * t ** 2 * p2
        + t ** 3 * p3
    )


def render_strokes(
    strokes: list[list[tuple[float, float]]],
    size: int = 224,
    stroke_width: float = 3.0,
    rotation: float = 0.0,
    scale: float = 1.0,
    shift_x: float = 0.0,
    shift_y: float = 0.0,
) -> Image.Image:
    all_points = [p for stroke in strokes for p in stroke]
    if not all_points:
        return Image.new("L", (size, size), 255)

    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x or 1
    h = max_y - min_y or 1

    margin = 40
    fit = (size - 2 * margin) / max(w, h)

    def transform(x: float, y: float) -> tuple[float, float]:
        nx = (x - min_x) * fit + margin
        ny = (y - min_y) * fit + margin

        cx_img = size / 2
        cy_img = size / 2
        nx -= cx_img
        ny -= cy_img

        nx *= scale
        ny *= scale

        rad = math.radians(rotation)
        rx = nx * math.cos(rad) - ny * math.sin(rad)
        ry = nx * math.sin(rad) + ny * math.cos(rad)

        rx += cx_img + shift_x
        ry += cy_img + shift_y
        return (rx, ry)

    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)

    for stroke in strokes:
        transformed = [transform(x, y) for x, y in stroke]
        if len(transformed) >= 2:
            draw.line(transformed, fill=0, width=max(1, int(stroke_width)), joint="curve")

    return img


def create_symbol_image(
    strokes: list[list[tuple[float, float]]],
    size: int = 224,
) -> Image.Image:
    img = render_strokes(
        strokes,
        size=size,
        stroke_width=random.uniform(2.0, 5.0),
        rotation=random.uniform(-15, 15),
        scale=random.uniform(0.8, 1.2),
        shift_x=random.uniform(-10, 10),
        shift_y=random.uniform(-10, 10),
    )

    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, random.uniform(2, 8), arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(arr)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Teeline training data from SVGs")
    parser.add_argument("--svgs", default="../../../data/reference/teeline-online/outline-svgs/alphabet")
    parser.add_argument("--output", default="../../../data/raw")
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--size", type=int, default=224)
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    total = 0
    missing = []

    for letter in LETTERS:
        svg_file = os.path.join(args.svgs, f"{letter.lower()}.svg")
        if not os.path.exists(svg_file):
            missing.append(letter)
            continue

        strokes = parse_svg_path(svg_file)
        if not strokes:
            print(f"  {letter}: WARNING - no strokes found in SVG")
            missing.append(letter)
            continue

        letter_dir = os.path.join(args.output, letter)
        os.makedirs(letter_dir, exist_ok=True)

        for i in range(args.samples):
            img = create_symbol_image(strokes, size=args.size)
            img.save(os.path.join(letter_dir, f"{letter}_{i:04d}.png"))
            total += 1

        print(f"  {letter}: {args.samples} samples from SVG")

    if missing:
        print(f"\n  Missing SVGs for: {', '.join(missing)}")

    print(f"\nGenerated {total} images in {args.output}")


if __name__ == "__main__":
    main()
