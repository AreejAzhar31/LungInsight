"""
evaluate.py — Evaluates a trained checkpoint on the test set.

Usage:
    python scripts/evaluate.py --checkpoint checkpoints/best.pt
    python scripts/evaluate.py --checkpoint checkpoints/best.pt --split validation

Outputs (written to cfg.evaluation.outputs_dir):
    - metrics.json                (accuracy, precision, recall, f1, roc_auc)
    - confusion_matrix.png
    - roc_curve.png
    - classification_report.txt
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.config import load_config
from utils.common import get_device
from utils.augmentation import build_eval_transforms
from utils.dataset import ChestXrayDataset
from utils.checkpoint import load_checkpoint
from utils.metrics import (
    compute_metrics,
    save_confusion_matrix,
    save_roc_curve,
    save_metrics_json,
    save_classification_report,
)
from models.efficientnet import build_model
from torch.utils.data import DataLoader


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate a trained LungInsight AI checkpoint")
    p.add_argument("--config", type=str, default="configs/config.yaml")
    p.add_argument("--checkpoint", type=str, required=True)
    p.add_argument("--split", type=str, default="test", choices=["test", "validation"])
    return p.parse_args()


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    all_labels, all_preds, all_probs = [], [], []

    for images, labels in tqdm(loader, desc="evaluating"):
        images = images.to(device)
        logits = model(images)
        probs = F.softmax(logits, dim=1)[:, 1]  # probability of PNEUMONIA (class idx 1)
        preds = torch.argmax(logits, dim=1)

        all_labels.extend(labels.numpy().tolist())
        all_preds.extend(preds.cpu().numpy().tolist())
        all_probs.extend(probs.cpu().numpy().tolist())

    return np.array(all_labels), np.array(all_preds), np.array(all_probs)


def main():
    args = parse_args()
    cfg = load_config(args.config)
    device = get_device(cfg.project.device)

    eval_tf = build_eval_transforms(cfg)
    data_dir = cfg.data.test_dir if args.split == "test" else cfg.data.val_dir
    dataset = ChestXrayDataset(data_dir, cfg.data.classes, eval_tf)
    loader = DataLoader(
        dataset, batch_size=cfg.training.batch_size, shuffle=False,
        num_workers=cfg.data.num_workers, pin_memory=cfg.data.pin_memory,
    )
    print(f"Evaluating on {args.split} split: {len(dataset)} samples, {dataset.class_counts()}")

    model = build_model(cfg).to(device)
    load_checkpoint(args.checkpoint, model, map_location=str(device))
    print(f"Loaded checkpoint: {args.checkpoint}")

    y_true, y_pred, y_prob = evaluate(model, loader, device)
    metrics = compute_metrics(y_true, y_pred, y_prob)

    print("\n=== Evaluation Metrics ===")
    for k, v in metrics.items():
        print(f"{k:>10}: {v:.4f}")

    outputs_dir = Path(cfg.evaluation.outputs_dir)
    save_metrics_json(metrics, outputs_dir / "metrics.json")
    save_confusion_matrix(y_true, y_pred, cfg.data.classes, outputs_dir / "confusion_matrix.png")
    save_roc_curve(y_true, y_prob, outputs_dir / "roc_curve.png")
    report = save_classification_report(y_true, y_pred, cfg.data.classes, outputs_dir / "classification_report.txt")

    print(f"\nSaved metrics.json, confusion_matrix.png, roc_curve.png, classification_report.txt -> {outputs_dir}/")
    print("\n" + report)


if __name__ == "__main__":
    main()
