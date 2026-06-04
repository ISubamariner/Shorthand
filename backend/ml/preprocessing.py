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
