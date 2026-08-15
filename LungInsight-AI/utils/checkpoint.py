"""
Checkpoint save / load / resume utilities.

Every checkpoint stores enough state to fully resume training:
    - model weights
    - optimizer state
    - scheduler state
    - AMP GradScaler state
    - epoch number
    - best validation metric so far
"""

from __future__ import annotations
import torch
from pathlib import Path
from typing import Optional


def save_checkpoint(
    path: str | Path,
    model,
    optimizer,
    scheduler,
    scaler,
    epoch: int,
    best_metric: float,
    extra: Optional[dict] = None,
):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "epoch": epoch,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict() if optimizer is not None else None,
        "scheduler_state": scheduler.state_dict() if scheduler is not None else None,
        "scaler_state": scaler.state_dict() if scaler is not None else None,
        "best_metric": best_metric,
    }
    if extra:
        state.update(extra)
    torch.save(state, path)


def load_checkpoint(
    path: str | Path,
    model,
    optimizer=None,
    scheduler=None,
    scaler=None,
    map_location: str = "cpu",
) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")

    checkpoint = torch.load(path, map_location=map_location)
    model.load_state_dict(checkpoint["model_state"])

    if optimizer is not None and checkpoint.get("optimizer_state") is not None:
        optimizer.load_state_dict(checkpoint["optimizer_state"])
    if scheduler is not None and checkpoint.get("scheduler_state") is not None:
        scheduler.load_state_dict(checkpoint["scheduler_state"])
    if scaler is not None and checkpoint.get("scaler_state") is not None:
        scaler.load_state_dict(checkpoint["scaler_state"])

    return checkpoint


class EarlyStopping:
    """Stops training when the monitored metric stops improving."""

    def __init__(self, patience: int = 7, min_delta: float = 0.001, mode: str = "min"):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_score: Optional[float] = None
        self.counter = 0
        self.should_stop = False

    def step(self, metric: float) -> bool:
        """Returns True if `metric` is the new best."""
        if self.best_score is None:
            self.best_score = metric
            return True

        improved = (
            (self.mode == "min" and metric < self.best_score - self.min_delta)
            or (self.mode == "max" and metric > self.best_score + self.min_delta)
        )

        if improved:
            self.best_score = metric
            self.counter = 0
            return True
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
            return False
