"""
resplit_validation.py — Rebuilds a larger, more reliable validation split
from an already-organized dataset (datasets/train + datasets/validation),
without touching datasets/test at all.

Use this when your current datasets/validation/ is too small (e.g. the
original Kaggle "val" folder with only 14 images), causing noisy val_loss
during training and unreliable early stopping / "best epoch" selection.

What it does:
    1. Moves your current datasets/validation/{NORMAL,PNEUMONIA} images back
       into a temporary holding area (nothing is deleted).
    2. Combines them with datasets/train/{NORMAL,PNEUMONIA}.
    3. Re-splits that combined pool into a new train/validation split at the
       requested fraction (default 12% to validation), shuffled with a fixed
       seed for reproducibility.
    4. Writes the result back into datasets/train/ and datasets/validation/.

datasets/test/ is never read or modified.

Usage:
    python scripts/resplit_validation.py --val-fraction 0.12
    python scripts/resplit_validation.py --val-fraction 0.12 --dry-run   # preview counts only
"""

from __future__ import annotations
import argparse
import random
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLASSES = ["NORMAL", "PNEUMONIA"]
IMG_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def parse_args():
    p = argparse.ArgumentParser(description="Rebuild a properly-sized validation split in place")
    p.add_argument("--val-fraction", type=float, default=0.12)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def list_images(d: Path) -> list[Path]:
    if not d.is_dir():
        return []
    return [f for f in d.iterdir() if f.suffix.lower() in IMG_EXTENSIONS]


def main():
    args = parse_args()
    random.seed(args.seed)

    train_dir = PROJECT_ROOT / "datasets" / "train"
    val_dir = PROJECT_ROOT / "datasets" / "validation"

    print(f"{'DRY RUN -- ' if args.dry_run else ''}Rebuilding validation split "
          f"(target fraction: {args.val_fraction:.0%})\n")

    for cls in CLASSES:
        train_files = list_images(train_dir / cls)
        val_files = list_images(val_dir / cls)
        combined = train_files + val_files
        random.shuffle(combined)

        n_val = max(1, int(len(combined) * args.val_fraction))
        new_val = combined[:n_val]
        new_train = combined[n_val:]

        print(f"{cls}: {len(train_files)} (train) + {len(val_files)} (old val) "
              f"= {len(combined)} total -> new train={len(new_train)}, new val={len(new_val)}")

        if args.dry_run:
            continue

        # Move everything into a staging area first so we never overwrite a file
        # with itself mid-shuffle if a filename happens to collide across folders.
        staging = PROJECT_ROOT / "datasets" / f"_staging_{cls}"
        staging.mkdir(parents=True, exist_ok=True)
        for f in combined:
            shutil.move(str(f), staging / f.name)

        (train_dir / cls).mkdir(parents=True, exist_ok=True)
        (val_dir / cls).mkdir(parents=True, exist_ok=True)

        train_names = {f.name for f in new_train}
        for f in staging.iterdir():
            if f.name in train_names:
                shutil.move(str(f), train_dir / cls / f.name)
            else:
                shutil.move(str(f), val_dir / cls / f.name)

        staging.rmdir()

    if args.dry_run:
        print("\n(dry run -- nothing was moved)")
    else:
        print(f"\nDone. New split written to {train_dir} and {val_dir}. "
              f"datasets/test/ was not touched.")


if __name__ == "__main__":
    main()
