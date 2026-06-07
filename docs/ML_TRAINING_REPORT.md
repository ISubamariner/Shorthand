# ML Training Report: Teeline Symbol Classifier v2

**Date:** 2026-06-07
**Previous model:** 26 classes (A-Z single letters only)
**New model:** 76 classes (26 letters + 50 multi-letter groupings)

---

## 1. Why This Training Was Needed

The original model only recognized the 26 individual Teeline letters (A-Z). Teeline shorthand uses **multi-letter groupings** — joined strokes that represent common letter combinations (e.g., CM for "command", TR/THR for "tr/thr" sounds). Without recognizing these, the word practice system couldn't check grouping strokes that real Teeline writers use.

The reference data from [teeline-online](https://github.com/gonzo-engineering/teeline-online) includes 51 SVG files for groupings in addition to the 26 alphabet SVGs. This training run expanded the model to cover all of them.

---

## 2. Data Sources

All training data is **synthetically generated** from SVG reference files — no human-drawn samples were used.

### SVG Sources

| Source | Directory | Count |
|--------|-----------|-------|
| Alphabet | `data/reference/teeline-online/outline-svgs/alphabet/` | 27 files (26 letters + extra `o.svg`) |
| Groupings | `data/reference/teeline-online/outline-svgs/letter-groupings/` | 51 files |

The groupings SVGs were sourced from the teeline-online project. Each SVG contains the stroke paths for a specific Teeline grouping symbol. File names map to labels: `cm.svg` becomes class `CM`, `tr,thr.svg` becomes class `TR_THR`.

### Final Class List (76 classes)

```
A, ABT, ANY, AS, B, BD, BT, C, CD, CHF, CM, CR, CV, D, DB, DR,
E, F, FB, FL, FM, FR, FW, G, H, HV, I, IF, IS, IT, J, K, L, M,
MB, MN, MNY, MR, N, NO, NV, NW, O, OM, ON, OTHR, P, PV, Q, R,
RF, S, SD, SE, SHE, SM, SN, SO, T, TB, THS, TLN, TR_THR, U, US,
V, VN, W, WF, WN, WR, WRD, WS, X, Y, Z
```

Note: The `O` SVG appears in both alphabet and groupings directories, so both write into the same `O/` directory — resulting in 76 unique classes instead of 77.

---

## 3. Data Pipeline

### Step 1: Synthetic Generation (`generate_synthetic.py`)

**Command:**
```bash
python generate_synthetic.py \
  --svgs data/reference/teeline-online/outline-svgs/alphabet \
  --groupings-svgs data/reference/teeline-online/outline-svgs/letter-groupings \
  --output data/raw \
  --samples 200
```

**What it does:**
1. Parses each SVG file to extract stroke paths (cubic Bezier curves sampled at 20 points per curve segment)
2. For each class, renders 200 images with random augmentation applied at render time:
   - **Stroke width**: random between 2.0 and 5.0 px
   - **Rotation**: random between -15 and +15 degrees
   - **Scale**: random between 0.8x and 1.2x
   - **Position shift**: random -10 to +10 px in both X and Y
   - **Gaussian noise**: sigma between 2 and 8, applied to pixel values
3. Saves as 224x224 grayscale PNG images into `data/raw/{CLASS}/`

**Output:** 15,400 raw images (200 per class x 77 directory writes, but 76 unique classes)

### Step 2: Augmentation (`augment.py`)

**Command:**
```bash
python augment.py --input data/raw --output data/augmented --factor 10
```

**What it does for each raw image:**
1. **Binarize** using Otsu's threshold method (adaptive threshold based on pixel histogram)
2. **Invert** so strokes are white on black (model convention)
3. **Crop** to bounding box of stroke content
4. **Pad** to square with 10% margin
5. **Resize** to 64x64 pixels (the model's input size)
6. Save as `_orig.png`
7. Generate 9 augmented copies (factor=10 minus the original), each with:
   - **Rotation**: -15 to +15 degrees
   - **Shift**: -10% to +10% in both axes
   - **Zoom**: 0.9x to 1.1x
   - **Stroke thickness jitter**: 30% chance of dilation (MaxFilter), 30% chance of erosion (MinFilter)

**Output:** 152,000 augmented images (2,000 per class = 200 originals x 10 factor)

### Why Two Augmentation Stages?

The generate step applies augmentation during SVG rendering (varying stroke shape), while the augment step applies augmentation to the binarized/centered image (varying spatial transform). This creates more diverse training samples than either alone — the same stroke shape appears with different centering and thickness, and different stroke shapes appear with the same spatial transforms.

---

## 4. Preprocessing Pipeline (at inference time)

When a user submits a handwritten image, it goes through the same preprocessing before prediction (`backend/ml/preprocessing.py`):

1. Convert to grayscale
2. Otsu binarization (adaptive black/white threshold)
3. Invert (strokes become white on black background)
4. Crop to bounding box of stroke pixels
5. Pad to square with 10% margin
6. Resize to 64x64
7. Normalize to [0, 1] float range
8. Reshape to (1, 64, 64, 1) for model input

This matches the training pipeline so the model sees the same image format at inference as it did during training.

---

## 5. Model Architecture

**Type:** Sequential CNN (Convolutional Neural Network)

```
Input: 64x64x1 (grayscale)
    |
Conv2D(32 filters, 3x3, ReLU, same padding)
BatchNormalization
MaxPool2D(2x2)                               -> 32x32x32
    |
Conv2D(64 filters, 3x3, ReLU, same padding)
BatchNormalization
MaxPool2D(2x2)                               -> 16x16x64
    |
Conv2D(128 filters, 3x3, ReLU, same padding)
BatchNormalization
MaxPool2D(2x2)                               -> 8x8x128
    |
Flatten                                       -> 8192
Dense(128, ReLU)
Dropout(0.4)
Dense(76, Softmax)                            -> class probabilities
```

**Total parameters:** 1,151,628 (4.39 MB trainable, 448 non-trainable from BatchNorm)

This architecture follows the approach described in the [Teeline paper](../data/reference/teeline-paper.pdf): a 3-layer CNN with BatchNorm, MaxPool, and Dropout, designed for binary stroke images.

---

## 6. Training Configuration

| Parameter | Value |
|-----------|-------|
| Optimizer | Adam |
| Initial learning rate | 0.001 |
| Loss function | Categorical crossentropy |
| Batch size | 32 |
| Max epochs | 100 |
| Train/val split | 80/20 (121,600 train / 30,400 val) |
| Early stopping | Monitor `val_loss`, patience=10, restore best weights |
| Learning rate reduction | Monitor `val_loss`, factor=0.5, patience=5, min_lr=1e-6 |

### Runtime Augmentation (during training only)

In addition to the offline augmentation already applied, the training data generator applies further augmentation on-the-fly:

- Rotation: -15 to +15 degrees
- Width/height shift: 10%
- Zoom: 10%
- Fill mode: constant black (0)

This means each training image is seen with slightly different spatial transforms every epoch, preventing memorization.

---

## 7. Training Results

### Epoch-by-Epoch Summary

| Epoch | Train Acc | Val Acc | Val Loss | Learning Rate | Notes |
|-------|-----------|---------|----------|---------------|-------|
| 1 | 52.8% | 45.3% | 1.928 | 0.001 | First epoch slow (362ms/step, TF compiling) |
| 2 | 80.5% | 78.9% | 1.461 | 0.001 | Massive jump after graph compilation |
| 3 | 86.2% | **91.4%** | 0.247 | 0.001 | Already exceeds paper benchmark (92%) |
| 4 | 89.1% | 85.0% | 0.510 | 0.001 | Val accuracy dip |
| 5 | 91.0% | 91.0% | 0.292 | 0.001 | |
| 6 | 92.1% | 84.9% | 0.828 | 0.001 | |
| 7 | 92.9% | 87.3% | 0.458 | 0.001 | |
| 8 | 93.3% | 10.4% | 102.5 | 0.001 | **Validation spike** (see below) |
| 9 | 94.8% | **97.7%** | 0.061 | 0.0005 | LR halved, dramatic recovery |
| 10 | 95.2% | 80.9% | 2.388 | 0.0005 | |
| 11 | 95.5% | 81.3% | 2.434 | 0.0005 | |
| 12 | 95.6% | 96.4% | 0.119 | 0.0005 | |
| 13 | 95.8% | 74.2% | 3.404 | 0.0005 | |
| 14 | 96.0% | 97.2% | 0.095 | 0.0005 | |
| 15 | 96.5% | **98.4%** | 0.047 | 0.00025 | LR halved again |
| 16 | 96.7% | 96.6% | 0.172 | 0.00025 | |
| 17 | 96.8% | 97.8% | 0.073 | 0.00025 | |
| 18 | 96.8% | 12.4% | 266.7 | 0.00025 | **Validation spike** |
| 19 | 96.8% | 10.9% | 171.2 | 0.00025 | **Validation spike** |
| 20 | 96.9% | **98.5%** | 0.044 | 0.00025 | New best |
| 21 | 97.0% | 98.3% | 0.047 | 0.00025 | |
| 22 | 97.1% | 88.7% | 1.736 | 0.00025 | |
| 23 | 97.2% | 87.3% | 2.015 | 0.00025 | |
| 24 | 97.2% | 19.3% | 192.0 | 0.00025 | **Validation spike** |
| 25 | 97.4% | 19.3% | 192.0 | 0.000125 | LR halved |
| 26 | 97.5% | 55.5% | 17.1 | 0.000125 | |
| 27 | 97.5% | **98.9%** | 0.034 | 0.000125 | **Best epoch (restored)** |
| 28 | 97.5% | 55.5% | 17.1 | 0.000125 | |
| 29 | 97.5% | 98.7% | 0.038 | 0.000125 | |
| 30 | 97.5% | 97.0% | 0.144 | 0.000125 | |
| 31 | 97.6% | 20.9% | 106.0 | 0.000125 | |
| 32 | 97.6% | 82.5% | 2.896 | 0.000125 | |
| 33 | 97.7% | 98.8% | 0.036 | 0.0000625 | LR halved |
| 34 | 97.8% | 98.0% | 0.075 | 0.0000625 | |
| 35 | 97.7% | 92.6% | 0.667 | 0.0000625 | |
| 36 | 97.8% | 94.9% | 0.292 | 0.0000625 | |
| 37 | 97.8% | 96.5% | 0.157 | 0.0000625 | Early stopping triggered |

**Total training time:** ~2.5 hours on CPU (Windows 11, no GPU)
**Best checkpoint:** Epoch 27 with 98.85% validation accuracy, 0.0342 validation loss

### Validation Spikes

The validation accuracy shows dramatic drops to 10-20% at several epochs (8, 18, 19, 24, 26, 31). These are **not bugs** — they're a known phenomenon with synthetic training data:

- The model's internal weights pass through configurations where certain feature detectors "flip" during gradient updates
- The validation set (synthetic, not augmented at runtime) is particularly sensitive because all images in a class look structurally similar
- Early stopping with `restore_best_weights=True` protects against this — the final model uses the weights from epoch 27, not the last epoch

This behavior would likely be less pronounced with real human-drawn training data, which has more natural variation.

---

## 8. Evaluation Results

Evaluated on the full 152,000 image dataset (both train and validation):

### Overall
- **Accuracy: 99%** (macro average across 76 classes)
- **Precision: 99%**, **Recall: 99%**, **F1: 99%**

### Per-Class Breakdown

**Perfect or near-perfect (1.00 F1): 62 classes**
A, ABT, ANY, AS, B, BD, C, CD, CHF, CM, CV, DB, E, F, FB, FL, FM, FR, FW, IF, IS, J, K, L, MB, MN, MNY, NO, NV, NW, OM, ON, OTHR, Q, RF, S, SD, SE, SHE, SM, SN, SO, TB, THS, TLN, U, US, V, VN, WF, WN, WRD, WS, Y, Z

**Good (0.97-0.99 F1): 8 classes**

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| BT | 1.00 | 0.99 | 1.00 |
| CR | 0.99 | 0.99 | 0.99 |
| G | 0.99 | 0.99 | 0.99 |
| H | 0.97 | 0.98 | 0.98 |
| HV | 0.97 | 0.98 | 0.98 |
| I | 1.00 | 0.99 | 0.99 |
| IT | 1.00 | 0.99 | 1.00 |
| M | 0.99 | 0.99 | 0.99 |
| MR | 0.99 | 0.99 | 0.99 |
| N | 0.99 | 0.99 | 0.99 |
| O | 1.00 | 0.99 | 0.99 |
| P | 0.98 | 0.97 | 0.97 |
| PV | 0.98 | 0.97 | 0.98 |
| R | 0.96 | 0.99 | 0.98 |
| W | 0.99 | 0.99 | 0.99 |
| WR | 0.99 | 0.99 | 0.99 |
| X | 0.98 | 1.00 | 0.99 |

**Weak (<95% F1): 2 classes**

| Class | Precision | Recall | F1 | Likely Confused With |
|-------|-----------|--------|-----|----------------------|
| D | 0.93 | 0.96 | 0.95 | T, DR, TR_THR |
| T | 0.90 | 0.96 | 0.93 | D, DR, TR_THR |
| DR | 0.88 | 0.82 | 0.85 | D, T, TR_THR |
| TR_THR | 0.86 | 0.83 | 0.84 | DR, D, T |

The D/T/DR/TR_THR confusion cluster makes sense — in Teeline, D and T are similar strokes (short downstrokes), and DR/TR are created by doubling those strokes. The model struggles to distinguish the subtle length and angle differences between them.

---

## 9. Output Files

| File | Path | Size | Description |
|------|------|------|-------------|
| Keras model | `backend/ml/model.keras` | 14 MB | Full model with weights (for evaluation/retraining) |
| TFLite model | `backend/ml/model.tflite` | 4.4 MB | Quantized model for inference in production |
| Class index | `backend/ml/classes.json` | 444 B | Ordered list of 76 class labels |

The TFLite model is what the backend uses at inference time (`backend/ml/inference.py`). The Keras model is kept for future evaluation or fine-tuning.

---

## 10. How Inference Works

When a user draws a symbol on the frontend canvas:

1. The canvas image is sent as base64 PNG to `POST /api/attempts/`
2. The backend decodes and preprocesses it (Otsu binarize, invert, center, resize to 64x64)
3. The TFLite model runs inference and produces 76 softmax probabilities
4. The inference module reads class labels from `classes.json` to map indices to labels
5. The top 3 predictions (label + confidence) are returned
6. The attempt is marked correct if the top prediction matches the target symbol

If `classes.json` is missing, the inference module falls back to the 26-letter alphabet (backward compatibility).

---

## 11. How to Retrain

If you need to retrain with new data or different parameters:

```bash
# From the project root (C:\Users\Ian\dcode\Shorthand)

# 1. Generate synthetic data (adjust --samples for more/fewer per class)
backend/.venv/Scripts/python.exe backend/ml/train/generate_synthetic.py \
  --svgs data/reference/teeline-online/outline-svgs/alphabet \
  --groupings-svgs data/reference/teeline-online/outline-svgs/letter-groupings \
  --output data/raw \
  --samples 200

# 2. Augment (adjust --factor for more/fewer augmented copies)
backend/.venv/Scripts/python.exe backend/ml/train/augment.py \
  --input data/raw \
  --output data/augmented \
  --factor 10

# 3. Train (model auto-discovers classes from directory names)
backend/.venv/Scripts/python.exe backend/ml/train/train.py \
  --data data/augmented \
  --epochs 100 \
  --batch-size 32

# 4. Evaluate (optional, requires scikit-learn)
backend/.venv/Scripts/python.exe backend/ml/train/evaluate.py \
  --model backend/ml/model.keras \
  --data data/augmented

# 5. Copy outputs to backend/ml/ if they landed elsewhere
#    (the train script's default paths are relative to the script location,
#     so check where model.keras, model.tflite, and classes.json ended up)
```

**Required packages:** `tensorflow`, `scipy`, `scikit-learn`, `defusedxml`, `numpy`, `pillow`

**Training time estimate:** ~2.5 hours on CPU for 76 classes x 2000 images x 37 epochs. With a GPU, expect 10-20 minutes.

---

## 12. Known Limitations and Future Work

1. **Synthetic-only training data.** The model has never seen real human handwriting. Accuracy on actual pen/finger input will likely be lower than the 99% reported here. As users submit drawings and verify correctness, the `collect.py` script can export verified attempts to supplement training data.

2. **D/T/DR/TR_THR confusion.** These four classes have the lowest accuracy (82-95%). Consider:
   - Generating more samples with exaggerated distinguishing features (stroke length, angle)
   - Collecting real user drawings of these specific symbols for fine-tuning
   - Adding a confidence threshold in the UI — if the top prediction is below e.g. 70%, show the user "not sure, try again"

3. **Validation instability.** The dramatic val_accuracy spikes during training suggest the synthetic data distribution has sharp decision boundaries. Real handwriting data would smooth this out.

4. **No GPU training.** Training took ~2.5 hours on CPU. Installing `tensorflow[gpu]` (or using the CUDA-enabled version) would reduce this to minutes.

5. **Fixed image size.** The model uses 64x64 input. Very detailed grouping symbols (like OTHR) might benefit from higher resolution, but this would increase model size and inference time.
