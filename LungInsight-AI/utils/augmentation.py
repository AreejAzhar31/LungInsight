"""
Image preprocessing & augmentation pipelines built with Albumentations.

Train pipeline includes:
    - horizontal flip
    - slight rotation
    - brightness / contrast adjustment
    - random crop (scale jitter)
    - resize
    - normalization (ImageNet stats, matches EfficientNet-B3 pretrained weights)

Validation / test / inference pipeline only resizes + normalizes
(no randomness — must be deterministic and reproducible).
"""

from __future__ import annotations
import albumentations as A
from albumentations.pytorch import ToTensorV2


def build_train_transforms(cfg) -> A.Compose:
    aug = cfg.augmentation
    size = cfg.data.image_size

    return A.Compose(
        [
            # Random-resized-crop style augmentation ("random crop")
            A.RandomResizedCrop(
                size=(size, size),
                scale=(aug.crop_scale_min, aug.crop_scale_max),
                p=aug.random_crop_prob,
            ),
            # Ensure exact size even when the crop above is skipped
            A.Resize(height=size, width=size),
            A.HorizontalFlip(p=aug.horizontal_flip_prob),
            A.Rotate(
                limit=aug.rotation_limit_degrees,
                border_mode=0,
                p=0.7,
            ),
            A.RandomBrightnessContrast(
                brightness_limit=aug.brightness_limit,
                contrast_limit=aug.contrast_limit,
                p=aug.brightness_contrast_prob,
            ),
            A.Normalize(mean=aug.normalize_mean, std=aug.normalize_std),
            ToTensorV2(),
        ]
    )


def build_eval_transforms(cfg) -> A.Compose:
    aug = cfg.augmentation
    size = cfg.data.image_size

    return A.Compose(
        [
            A.Resize(height=size, width=size),
            A.Normalize(mean=aug.normalize_mean, std=aug.normalize_std),
            ToTensorV2(),
        ]
    )


def build_inference_transform(cfg) -> A.Compose:
    """Alias kept for clarity when used from predict.py / inference.py."""
    return build_eval_transforms(cfg)
