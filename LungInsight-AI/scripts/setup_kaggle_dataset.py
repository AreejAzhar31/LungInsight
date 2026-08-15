"""
setup_kaggle_dataset.py — One-shot helper to download the Kaggle "Chest X-Ray
Images (Pneumonia)" dataset and arrange it into this project's expected layout:

    datasets/train/{NORMAL,PNEUMONIA}
    datasets/validation/{NORMAL,PNEUMONIA}
    datasets/test/{NORMAL,PNEUMONIA}

Prerequisites (one-time, on your machine):
    1. pip install kaggle
    2. Get an API token from https://www.kaggle.com/settings -> "Create New Token"
       This downloads a kaggle.json file.
    3. Place kaggle.json at:
         Windows:  C:\\Users\\<you>\\.kaggle\\kaggle.json
         macOS/Linux: ~/.kaggle/kaggle.json

Usage:
    python scripts/setup_kaggle_dataset.py

This script:
    - Downloads paultimothymooney/chest-xray-pneumonia via the Kaggle API
    - Unzips it to a temp folder
    - Copies NORMAL/PNEUMONIA images into datasets/train and datasets/test as-is
    - Re-splits a portion of the (very small, 16-image) original "val" folder
      PLUS some of train into a larger, more usable datasets/validation split
      (since the original Kaggle val split is too small for reliable early stopping)
"""

from __future__ import annotations
import argparse
import random
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_SLUG = "paultimothymooney/chest-xray-pneumonia"
CLASSES = ["NORMAL", "PNEUMONIA"]


def parse_args():
    p = argparse.ArgumentParser(description="Download & organize the Kaggle chest X-ray dataset")
    p.add_argument("--val-fraction", type=float, default=0.12,
                    help="fraction of the ORIGINAL train split to carve out as a proper validation set")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--skip-download", action="store_true",
                    help="reuse an already-downloaded/unzipped kaggle folder at datasets/_kaggle_raw")
    return p.parse_args()


def download_and_unzip(raw_dir: Path):
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / "chest-xray-pneumonia.zip"

    print(f"Downloading {DATASET_SLUG} via the Kaggle API ...")
    result = subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET_SLUG, "-p", str(raw_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print(
            "\nKaggle download failed. Check that:\n"
            "  1) `pip install kaggle` succeeded\n"
            "  2) kaggle.json is placed correctly (see this script's docstring)\n"
            "  3) You've accepted the dataset's terms on kaggle.com at least once\n"
        )
        sys.exit(1)

    print("Unzipping ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(raw_dir)
    print(f"Done -> {raw_dir}")


def find_split_dirs(raw_dir: Path) -> dict[str, Path]:
    """Kaggle's zip nests folders as chest_xray/{train,val,test}/{NORMAL,PNEUMONIA}."""
    candidates = list(raw_dir.rglob("chest_xray"))
    base = candidates[0] if candidates else raw_dir
    splits = {}
    for name, key in [("train", "train"), ("val", "val"), ("test", "test")]:
        match = list(base.rglob(name))
        match = [m for m in match if m.is_dir() and (m / "NORMAL").exists()]
        if match:
            splits[key] = match[0]
    return splits


def copy_class_images(src_dir: Path, dst_dir: Path, cls: str):
    dst_cls = dst_dir / cls
    dst_cls.mkdir(parents=True, exist_ok=True)
    src_cls = src_dir / cls
    count = 0
    for f in src_cls.iterdir():
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"):
            shutil.copy2(f, dst_cls / f.name)
            count += 1
    return count


def main():
    args = parse_args()
    random.seed(args.seed)

    raw_dir = PROJECT_ROOT / "datasets" / "_kaggle_raw"
    if not args.skip_download:
        download_and_unzip(raw_dir)

    splits = find_split_dirs(raw_dir)
    if "train" not in splits or "test" not in splits:
        print(f"Could not locate train/test folders under {raw_dir}. Found: {splits}")
        sys.exit(1)

    train_src = splits["train"]
    test_src = splits["test"]

    out_train = PROJECT_ROOT / "datasets" / "train"
    out_val = PROJECT_ROOT / "datasets" / "validation"
    out_test = PROJECT_ROOT / "datasets" / "test"

    print("\nCopying test split as-is ...")
    for cls in CLASSES:
        n = copy_class_images(test_src, out_test, cls)
        print(f"  test/{cls}: {n} images")

    # Original Kaggle "val" folder only has 16 images total -- too small to be useful.
    # Carve out a proper validation split from the training data instead, and merge
    # in whatever came with the original val/ folder.
    print(f"\nBuilding a real validation split ({args.val_fraction:.0%} of train) ...")
    for cls in CLASSES:
        src_cls_dir = train_src / cls
        files = [f for f in src_cls_dir.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")]
        random.shuffle(files)
        n_val = int(len(files) * args.val_fraction)
        val_files = files[:n_val]
        train_files = files[n_val:]

        (out_train / cls).mkdir(parents=True, exist_ok=True)
        (out_val / cls).mkdir(parents=True, exist_ok=True)

        for f in train_files:
            shutil.copy2(f, out_train / cls / f.name)
        for f in val_files:
            shutil.copy2(f, out_val / cls / f.name)

        # fold in the original tiny val/ split too, if present
        if "val" in splits:
            orig_val_cls = splits["val"] / cls
            if orig_val_cls.exists():
                for f in orig_val_cls.iterdir():
                    if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"):
                        shutil.copy2(f, out_val / cls / f.name)

        print(f"  train/{cls}: {len(train_files)} | validation/{cls}: {n_val + (len(list((splits.get('val', out_val)/cls).iterdir())) if 'val' in splits and (splits['val']/cls).exists() else 0)}")

    print(f"\nDone. Dataset ready under {PROJECT_ROOT / 'datasets'}.")
    print("You can now run: python scripts/train.py")
    print(f"\n(Raw downloaded files kept at {raw_dir} in case you want to inspect them; "
          f"safe to delete once you've confirmed datasets/ looks right.)")


if __name__ == "__main__":
    main()
