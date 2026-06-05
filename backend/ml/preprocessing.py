import io

import numpy as np
from PIL import Image, ImageFilter

IMG_SIZE = 64


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Convert raw PNG bytes to a normalized numpy array for TFLite inference.

    Pipeline: grayscale → binarize → invert → crop → center → resize 64x64
    Output shape: (1, 64, 64, 1)
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = binarize_and_center(img)
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr.reshape(1, IMG_SIZE, IMG_SIZE, 1)


def binarize_and_center(img: Image.Image) -> Image.Image:
    """Binarize, invert, crop to stroke bounding box, pad square, resize."""
    arr = np.array(img)

    # Otsu threshold
    threshold = _otsu_threshold(arr)
    binary = (arr < threshold).astype(np.uint8) * 255

    # Crop to bounding box of stroke content
    coords = np.argwhere(binary > 0)
    if len(coords) == 0:
        return Image.new("L", (IMG_SIZE, IMG_SIZE), 0)

    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    cropped = binary[y_min:y_max + 1, x_min:x_max + 1]

    # Pad to square with 10% margin
    h, w = cropped.shape
    side = max(h, w)
    margin = max(int(side * 0.1), 4)
    padded_size = side + 2 * margin

    padded = np.zeros((padded_size, padded_size), dtype=np.uint8)
    y_offset = (padded_size - h) // 2
    x_offset = (padded_size - w) // 2
    padded[y_offset:y_offset + h, x_offset:x_offset + w] = cropped

    result = Image.fromarray(padded, mode="L")
    result = result.resize((IMG_SIZE, IMG_SIZE), Image.BICUBIC)
    return result


def _otsu_threshold(arr: np.ndarray) -> int:
    """Compute Otsu's threshold for a grayscale image array."""
    hist = np.bincount(arr.ravel(), minlength=256).astype(np.float64)
    total = arr.size
    sum_total = np.dot(np.arange(256), hist)

    sum_bg = 0.0
    weight_bg = 0.0
    max_variance = 0.0
    best_threshold = 0

    for t in range(256):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break

        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg

        variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if variance > max_variance:
            max_variance = variance
            best_threshold = t

    return best_threshold
