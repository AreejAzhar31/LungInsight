"""Tests for the ChestXrayDataset loader, using a small synthetic dataset on disk."""
import sys
import shutil
from pathlib import Path

import numpy as np
import cv2
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.dataset import ChestXrayDataset, compute_class_weights
from utils.augmentation import build_eval_transforms
from utils.config import load_config


@pytest.fixture()
def synthetic_dataset_dir(tmp_path):
    root = tmp_path / "synthetic"
    classes = {"NORMAL": 5, "PNEUMONIA": 3}
    for cls, n in classes.items():
        cls_dir = root / cls
        cls_dir.mkdir(parents=True)
        for i in range(n):
            img = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
            cv2.imwrite(str(cls_dir / f"img_{i}.png"), img)
    yield root, classes
    shutil.rmtree(root, ignore_errors=True)


def test_dataset_indexes_all_images(synthetic_dataset_dir):
    root, classes = synthetic_dataset_dir
    ds = ChestXrayDataset(str(root), classes=list(classes.keys()))
    assert len(ds) == sum(classes.values())


def test_dataset_class_counts(synthetic_dataset_dir):
    root, classes = synthetic_dataset_dir
    ds = ChestXrayDataset(str(root), classes=list(classes.keys()))
    counts = ds.class_counts()
    assert counts == classes


def test_dataset_getitem_with_transform(synthetic_dataset_dir):
    root, classes = synthetic_dataset_dir
    cfg = load_config(str(Path(__file__).resolve().parent.parent / "configs" / "config.yaml"))
    transform = build_eval_transforms(cfg)
    ds = ChestXrayDataset(str(root), classes=list(classes.keys()), transform=transform)

    image, label = ds[0]
    assert image.shape == (3, cfg.data.image_size, cfg.data.image_size)
    assert label in (0, 1)


def test_missing_directory_raises():
    with pytest.raises(RuntimeError):
        ChestXrayDataset("/nonexistent/path/xyz", classes=["NORMAL", "PNEUMONIA"])


def test_class_weights_favor_minority_class(synthetic_dataset_dir):
    root, classes = synthetic_dataset_dir
    ds = ChestXrayDataset(str(root), classes=list(classes.keys()))
    weights = compute_class_weights(ds)
    # PNEUMONIA (3 samples) is the minority vs NORMAL (5 samples) -> higher weight
    assert weights[1] > weights[0]
