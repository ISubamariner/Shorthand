"""Convert SavedModel to TFLite with INT8 quantization.

Usage:
    python convert.py --model ../saved_model --output ../model.tflite
"""

import argparse
import os

import numpy as np
import tensorflow as tf

IMG_SIZE = 224


def representative_dataset():
    for _ in range(100):
        data = np.random.rand(1, IMG_SIZE, IMG_SIZE, 3).astype(np.float32)
        yield [data]


def main():
    parser = argparse.ArgumentParser(description="Convert to TFLite")
    parser.add_argument("--model", default="../saved_model")
    parser.add_argument("--output", default="../model.tflite")
    parser.add_argument("--quantize", choices=["none", "dynamic", "int8"], default="int8")
    args = parser.parse_args()

    print(f"Loading model from {args.model}...")
    converter = tf.lite.TFLiteConverter.from_saved_model(args.model)

    if args.quantize == "dynamic":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        print("Applying dynamic range quantization...")
    elif args.quantize == "int8":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type = tf.float32
        print("Applying INT8 quantization...")

    tflite_model = converter.convert()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "wb") as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    print(f"\nModel saved to {args.output}")
    print(f"Size: {size_mb:.2f} MB")

    if size_mb > 5:
        print("WARNING: Model exceeds 5MB target - consider stronger quantization")
    else:
        print("OK - Model is within 5MB target")


if __name__ == "__main__":
    main()
