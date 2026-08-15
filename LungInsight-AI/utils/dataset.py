"""
Dataset loading for LungInsight AI.

Expected directory layout (ImageFolder-style, binary classification):

    datasets/
        train/
            NORMAL/
                img1.jpeg
                ...
            PNEUMONIA/
                img1.jpeg
                ...
        validation/
            NORMAL/
            PNEUMONIA/
        test/
            NORMAL/
            PNEUMONIA/

Class index mapping is fixed by cfg.data.classes = ["NORMAL", "PNEUMONIA"]
so label 0 = NORMAL, label 1 = PNEUMONIA everywhere in the pipeline
(training, evaluation, inference, Grad-CAM).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
from torch.utils.data import Dataset, DataLoader

IMG_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


class ChestXrayDataset(Dataset):
    """Reads images off disk and applies an Albumentations transform."""

    def __init__(self, root_dir: str, classes: list[str], transform: Optional[Callable] = None):
        self.root_dir = Path(root_dir)
        self.classes = classes
        self.class_to_idx = {c: i for i, c in enumerate(classes)}
        self.transform = transform
        self.samples: list[tuple[Path, int]] = self._index_samples()

        if len(self.samples) == 0:
            raise RuntimeError(
                f"No images found under {self.root_dir}. Expected subfolders: {classes}. "
                f"Populate datasets/ following the layout described in DATASET.md."
            )

    def _index_samples(self) -> list[tuple[Path, int]]:
        samples = []
        for cls in self.classes:
            cls_dir = self.root_dir / cls
            if not cls_dir.is_dir():
                continue
            for fname in sorted(os.listdir(cls_dir)):
                if fname.lower().endswith(IMG_EXTENSIONS):
                    samples.append((cls_dir / fname, self.class_to_idx[cls]))
        return samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"Could not read image at {path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if self.transform is not None:
            augmented = self.transform(image=image)
            image = augmented["image"]

        return image, label

    def class_counts(self) -> dict[str, int]:
        counts = {c: 0 for c in self.classes}
        for _, label in self.samples:
            counts[self.classes[label]] += 1
        return counts


def build_dataloaders(cfg, train_transform, eval_transform):
    """Builds train / validation / test DataLoaders from the config paths."""
    classes = cfg.data.classes

    train_ds = ChestXrayDataset(cfg.data.train_dir, classes, train_transform)
    val_ds = ChestXrayDataset(cfg.data.val_dir, classes, eval_transform)
    test_ds = ChestXrayDataset(cfg.data.test_dir, classes, eval_transform)

    common_kwargs = dict(
        num_workers=cfg.data.num_workers,
        pin_memory=cfg.data.pin_memory,
    )

    train_loader = DataLoader(
        train_ds, batch_size=cfg.training.batch_size, shuffle=True, drop_last=True, **common_kwargs
    )
    val_loader = DataLoader(
        val_ds, batch_size=cfg.training.batch_size, shuffle=False, **common_kwargs
    )
    test_loader = DataLoader(
        test_ds, batch_size=cfg.training.batch_size, shuffle=False, **common_kwargs
    )

    return train_loader, val_loader, test_loader, train_ds, val_ds, test_ds


def compute_class_weights(dataset: ChestXrayDataset) -> np.ndarray:
    """Inverse-frequency class weights, useful for imbalanced pneumonia/normal counts."""
    counts = dataset.class_counts()
    total = sum(counts.values())
    n_classes = len(counts)
    weights = np.array(
        [total / (n_classes * max(counts[c], 1)) for c in dataset.classes], dtype=np.float32
    )
    return weights
