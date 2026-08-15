"""
train.py — Main training entry point for LungInsight AI.

Usage:
    python scripts/train.py --config configs/config.yaml
    python scripts/train.py --config configs/config.yaml --resume checkpoints/last.pt
    python scripts/train.py --epochs 20 --batch-size 32       # override config values

Features:
    - transfer learning (frozen backbone) -> automatic unfreeze + fine-tuning
    - mixed precision (AMP)
    - LR scheduler (reduce-on-plateau / cosine / step)
    - early stopping
    - checkpoint saving (best + last), resumable
    - TensorBoard logging
"""

from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.config import load_config
from utils.common import set_seed, get_device
from utils.augmentation import build_train_transforms, build_eval_transforms
from utils.dataset import build_dataloaders, compute_class_weights
from utils.checkpoint import save_checkpoint, load_checkpoint, EarlyStopping
from utils.metrics import save_training_curves
from models.efficientnet import build_model


def parse_args():
    p = argparse.ArgumentParser(description="Train the LungInsight AI pneumonia classifier")
    p.add_argument("--config", type=str, default="configs/config.yaml")
    p.add_argument("--resume", type=str, default=None, help="path to checkpoint to resume from")
    p.add_argument("--epochs", type=int, default=None, help="override cfg.training.epochs")
    p.add_argument("--batch-size", type=int, default=None, help="override cfg.training.batch_size")
    p.add_argument("--lr", type=float, default=None, help="override cfg.training.lr")
    return p.parse_args()


def build_optimizer(model, cfg, fine_tune: bool = False):
    lr = cfg.training.fine_tune_lr if fine_tune else cfg.training.lr
    params = [p for p in model.parameters() if p.requires_grad]
    if cfg.training.optimizer.lower() == "adamw":
        return torch.optim.AdamW(params, lr=lr, weight_decay=cfg.training.weight_decay)
    return torch.optim.Adam(params, lr=lr, weight_decay=cfg.training.weight_decay)


def build_scheduler(optimizer, cfg):
    kind = cfg.training.lr_scheduler
    if kind == "reduce_on_plateau":
        return torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min",
            factor=cfg.training.lr_scheduler_factor,
            patience=cfg.training.lr_scheduler_patience,
        )
    elif kind == "cosine":
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.training.epochs)
    elif kind == "step":
        return torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=cfg.training.lr_scheduler_factor)
    return None


def run_epoch(model, loader, criterion, optimizer, scaler, device, cfg, train: bool):
    model.train() if train else model.eval()

    total_loss, total_correct, total_samples = 0.0, 0, 0
    context = torch.enable_grad() if train else torch.no_grad()

    with context:
        pbar = tqdm(loader, desc="train" if train else "val", leave=False)
        for images, labels in pbar:
            images, labels = images.to(device), labels.to(device)

            if train:
                optimizer.zero_grad(set_to_none=True)

            with torch.autocast(device_type=device.type, enabled=cfg.training.mixed_precision):
                outputs = model(images)
                loss = criterion(outputs, labels)

            if train:
                if cfg.training.mixed_precision and device.type == "cuda":
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.training.grad_clip_norm)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.training.grad_clip_norm)
                    optimizer.step()

            preds = torch.argmax(outputs, dim=1)
            total_correct += (preds == labels).sum().item()
            total_samples += labels.size(0)
            total_loss += loss.item() * labels.size(0)
            pbar.set_postfix(loss=loss.item())

    return total_loss / total_samples, total_correct / total_samples


def main():
    args = parse_args()
    cfg = load_config(args.config)

    if args.epochs is not None:
        cfg.training.epochs = args.epochs
    if args.batch_size is not None:
        cfg.training.batch_size = args.batch_size
    if args.lr is not None:
        cfg.training.lr = args.lr

    set_seed(cfg.project.seed)
    device = get_device(cfg.project.device)
    print(f"[LungInsight AI] Using device: {device}")

    # ---- data ----
    train_tf = build_train_transforms(cfg)
    eval_tf = build_eval_transforms(cfg)
    train_loader, val_loader, test_loader, train_ds, val_ds, _ = build_dataloaders(cfg, train_tf, eval_tf)
    print(f"Train samples: {len(train_ds)} | Class counts: {train_ds.class_counts()}")
    print(f"Val samples:   {len(val_ds)} | Class counts: {val_ds.class_counts()}")

    # ---- model ----
    model = build_model(cfg).to(device)

    class_weights = torch.tensor(compute_class_weights(train_ds), dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=cfg.training.label_smoothing)

    scaler = torch.amp.GradScaler(enabled=(cfg.training.mixed_precision and device.type == "cuda"))

    early_stopper = EarlyStopping(
        patience=cfg.training.early_stopping_patience,
        min_delta=cfg.training.early_stopping_min_delta,
        mode="min",
    )

    start_epoch = 0
    best_metric = float("inf")

    # Peek at the checkpoint's epoch (if resuming) BEFORE building the optimizer, so the
    # model's freeze/unfreeze state -- and therefore the optimizer's parameter groups --
    # match what's stored in the checkpoint. Building the optimizer with the wrong set of
    # trainable parameters first would make `optimizer.load_state_dict(...)` fail below.
    resume_path = args.resume or cfg.training.resume_from
    resume_epoch = None
    if resume_path:
        peek = torch.load(resume_path, map_location="cpu")
        resume_epoch = peek["epoch"] + 1
        best_metric = peek.get("best_metric", best_metric)

    fine_tuning_started = (resume_epoch or 0) >= cfg.model.freeze_backbone_epochs
    if fine_tuning_started and cfg.model.freeze_backbone_epochs > 0:
        model.unfreeze_backbone()
        optimizer = build_optimizer(model, cfg, fine_tune=True)
    else:
        optimizer = build_optimizer(model, cfg, fine_tune=False)
    scheduler = build_scheduler(optimizer, cfg)

    if resume_path:
        print(f"Resuming from checkpoint: {resume_path}")
        load_checkpoint(resume_path, model, optimizer, scheduler, scaler, map_location=str(device))
        start_epoch = resume_epoch

    log_dir = Path(cfg.logging.log_dir) / time.strftime("%Y%m%d-%H%M%S")
    writer = SummaryWriter(log_dir=str(log_dir)) if cfg.logging.tensorboard else None

    ckpt_dir = Path(cfg.training.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

    for epoch in range(start_epoch, cfg.training.epochs):
        # switch from frozen-backbone transfer learning to full fine-tuning
        if not fine_tuning_started and epoch >= cfg.model.freeze_backbone_epochs > 0:
            print(f"[epoch {epoch}] Unfreezing backbone -> fine-tuning phase (lower LR)")
            model.unfreeze_backbone()
            optimizer = build_optimizer(model, cfg, fine_tune=True)
            scheduler = build_scheduler(optimizer, cfg)
            fine_tuning_started = True

        t0 = time.time()
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, scaler, device, cfg, train=True)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, optimizer, scaler, device, cfg, train=False)
        dt = time.time() - t0

        if scheduler is not None:
            if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                scheduler.step(val_loss)
            else:
                scheduler.step()

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)

        current_lr = optimizer.param_groups[0]["lr"]
        print(
            f"Epoch {epoch+1}/{cfg.training.epochs} | "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} | "
            f"lr={current_lr:.2e} | {dt:.1f}s"
        )

        if writer:
            writer.add_scalar("Loss/train", train_loss, epoch)
            writer.add_scalar("Loss/val", val_loss, epoch)
            writer.add_scalar("Accuracy/train", train_acc, epoch)
            writer.add_scalar("Accuracy/val", val_acc, epoch)
            writer.add_scalar("LR", current_lr, epoch)

        is_best = early_stopper.step(val_loss)
        if is_best:
            best_metric = val_loss
            save_checkpoint(
                ckpt_dir / "best.pt", model, optimizer, scheduler, scaler, epoch, best_metric
            )
            print(f"  -> New best model saved (val_loss={val_loss:.4f})")

        if not cfg.training.save_best_only:
            save_checkpoint(
                ckpt_dir / "last.pt", model, optimizer, scheduler, scaler, epoch, best_metric
            )

        if early_stopper.should_stop:
            print(f"Early stopping triggered at epoch {epoch+1} (no improvement for "
                  f"{cfg.training.early_stopping_patience} epochs).")
            break

    outputs_dir = Path(cfg.evaluation.outputs_dir)
    save_training_curves(history, outputs_dir / "training_curves.png")
    print(f"Training complete. Best val_loss={best_metric:.4f}. "
          f"Checkpoints in {ckpt_dir}/, curves in {outputs_dir}/training_curves.png")

    if writer:
        writer.close()


if __name__ == "__main__":
    main()
