# DATASET.md — LungInsight AI Dataset Guide

## Expected Directory Structure

Place your chest X-ray images in `datasets/` following this exact layout
(an `ImageFolder`-style binary classification structure):

```
datasets/
    train/
        NORMAL/
            person1_normal.jpeg
            person2_normal.jpeg
            ...
        PNEUMONIA/
            person1_bacteria.jpeg
            person2_virus.jpeg
            ...
    validation/
        NORMAL/
        PNEUMONIA/
    test/
        NORMAL/
        PNEUMONIA/
```

The two class folder names **must** match `data.classes` in `configs/config.yaml`
(default: `["NORMAL", "PNEUMONIA"]`). Class index 0 = `NORMAL`, class index 1 =
`PNEUMONIA` — this ordering is fixed throughout training, evaluation, and inference.

Empty placeholder folders for this structure already exist under `datasets/` in this
project — just drop your images into the matching subfolders.

## Supported Image Formats

`.jpg`, `.jpeg`, `.png`, `.bmp` (case-insensitive extensions). Images are read with
OpenCV and converted to RGB internally — grayscale X-rays are automatically
handled (OpenCV reads them as 3-channel by default via `IMREAD_COLOR`).

## Recommended Public Dataset

The most common source for this exact class layout is the **Kaggle "Chest X-Ray
Images (Pneumonia)"** dataset (Kermany et al.), which already ships with
`train/`, `val/`, and `test/` splits and `NORMAL`/`PNEUMONIA` subfolders. If you use
it, just rename `val/` to `validation/` (or update `data.val_dir` in the config) to
match this project's naming.

Note: that dataset's original validation split is very small (16 images). For more
reliable early-stopping / model-selection signal, consider re-splitting the training
set to create a larger validation set (e.g. 85/15 train/validation) while keeping the
official test set untouched for final evaluation.

## Preprocessing & Augmentation

Defined in `utils/augmentation.py`, controlled by the `augmentation:` section of
`configs/config.yaml`:

**Training pipeline** (randomized, re-applied every epoch):
- Random-resized crop (scale jitter) — `random_crop_prob`, `crop_scale_min/max`
- Resize to `data.image_size` (300×300 by default)
- Horizontal flip — `horizontal_flip_prob`
- Slight rotation — `rotation_limit_degrees`
- Brightness/contrast jitter — `brightness_contrast_prob`, `brightness_limit`, `contrast_limit`
- Normalization to ImageNet mean/std (must match the pretrained backbone's expected input)

**Validation / test / inference pipeline** (deterministic, no randomness):
- Resize to `data.image_size`
- Normalization to ImageNet mean/std only

## Class Imbalance

If your dataset has a skewed NORMAL:PNEUMONIA ratio, no manual resampling is required —
`utils/dataset.compute_class_weights` automatically computes inverse-frequency class
weights from the training split and feeds them into the loss function
(see `MODEL.md` → Class Imbalance Handling).

## Adding Your Own Data

1. Collect chest X-ray images labeled `NORMAL` or `PNEUMONIA`.
2. Split them into `train/`, `validation/`, `test/` (a common ratio is 70/15/15 or
   80/10/10) — **make sure images from the same patient don't leak across splits**
   if your source data includes multiple images per patient, to avoid overly
   optimistic evaluation numbers.
3. Drop the images into the matching `datasets/<split>/<class>/` folders.
4. Run `python scripts/train.py` — the dataset loader will pick everything up
   automatically; no manifest or CSV file is needed.

## Validating Your Dataset Is Set Up Correctly

```bash
python -c "from utils.config import load_config; from utils.dataset import ChestXrayDataset; \
cfg = load_config('configs/config.yaml'); \
ds = ChestXrayDataset(cfg.data.train_dir, cfg.data.classes); \
print(len(ds), ds.class_counts())"
```

This should print the total image count and a per-class breakdown for your training
split. The test suite (`tests/test_dataset.py`) also covers this loading logic against
a synthetic dataset, independent of your real data.
