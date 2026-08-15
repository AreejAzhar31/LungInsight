"""Tests for augmentation / preprocessing pipelines."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.config import load_config
from utils.augmentation import build_train_transforms, build_eval_transforms


@pytest.fixture(scope="module")
def cfg():
    return load_config(str(Path(__file__).resolve().parent.parent / "configs" / "config.yaml"))


def _dummy_image(size=400):
    return (np.random.rand(size, size, 3) * 255).astype(np.uint8)


def test_train_transform_output_shape(cfg):
    transform = build_train_transforms(cfg)
    image = _dummy_image()
    out = transform(image=image)["image"]
    expected = cfg.data.image_size
    assert out.shape == (3, expected, expected)


def test_eval_transform_output_shape(cfg):
    transform = build_eval_transforms(cfg)
    image = _dummy_image()
    out = transform(image=image)["image"]
    expected = cfg.data.image_size
    assert out.shape == (3, expected, expected)


def test_eval_transform_is_deterministic(cfg):
    transform = build_eval_transforms(cfg)
    image = _dummy_image()
    out1 = transform(image=image)["image"]
    out2 = transform(image=image)["image"]
    assert np.allclose(out1.numpy(), out2.numpy())


def test_normalization_changes_pixel_range(cfg):
    transform = build_eval_transforms(cfg)
    image = np.ones((400, 400, 3), dtype=np.uint8) * 255
    out = transform(image=image)["image"].numpy()
    # After ImageNet normalization, pure-white pixels should not remain in [0,255]
    assert out.max() < 10
