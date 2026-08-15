"""
organize_local_dataset.py — Extracts an already-downloaded dataset zip and
arranges it into this project's expected layout:

    datasets/train/{NORMAL,PNEUMONIA}
    datasets/validation/{NORMAL,PNEUMONIA}
    datasets/test/{NORMAL,PNEUMONIA}

Works with the common Kaggle "chest-xray-pneumonia" zip layout
(chest_xray/train|val|test/NORMAL|PNEUMONIA/*.jpeg), and is tolerant of the
zip being nested a level or two deeper.

Usage (from the project root):
    python scripts/organize_local_dataset.py --zip "C:\\Users\\you\\Downloads\\chest-xray-pneumonia.zip"

    # If you've already extracted it yourself, point at the folder instead:
    python scripts/organize_local_dataset.py --source-dir "C:\\Users\\you\\Downloads\\chest_xray"

Options:
    --val-fraction   fraction of TRAIN carved out as a proper validation split
                      (default 0.12) -- the original Kaggle "val" folder only has
                      16 images, which is too small for reliable early stopping.
    --dry-run        just print what would happen, copy nothing
"""

from __future__ import annotations
import argparse
import random
import shutil
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLASSES = ["NORMAL", "PNEUMONIA"]
IMG_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def parse_args():
    p = argparse.ArgumentParser(description="Organize a locally-downloaded chest X-ray dataset zip/folder")
    p.add_argument("--zip", type=str, default=None, help="path to the downloaded .zip file")
    p.add_argument("--source-dir", type=str, default=None, help="path to an already-extracted folder")
    p.add_argument("--val-fraction", type=float, default=0.12)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def extract_zip(zip_path: Path, extract_to: Path) -> Path:
    print(f"Extracting {zip_path.name} ...")
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    print(f"Extracted -> {extract_to}")
    return extract_to


def find_split_dirs(root: Path) -> dict[str, Path]:
    """
    Searches recursively for folders literally named train/val(idation)/test that
    directly contain NORMAL and PNEUMONIA subfolders.
    """
    splits = {}
    aliases = {"train": ["train"], "val": ["val", "validation"], "test": ["test"]}
    for key, names in aliases.items():
        for name in names:
            matches = [
                d for d in root.rglob(name)
                if d.is_dir() and (d / "NORMAL").is_dir() and (d / "PNEUMONIA").is_dir()
            ]
            if matches:
                splits[key] = matches[0]
                break
    return splits


def count_images(d: Path) -> int:
    return sum(1 for f in d.iterdir() if f.suffix.lower() in IMG_EXTENSIONS)


def copy_all(src_cls_dir: Path, dst_cls_dir: Path, dry_run: bool) -> int:
    dst_cls_dir.mkdir(parents=True, exist_ok=True)
    files = [f for f in src_cls_dir.iterdir() if f.suffix.lower() in IMG_EXTENSIONS]
    if not dry_run:
        for f in files:
            shutil.copy2(f, dst_cls_dir / f.name)
    return len(files)


def main():
    args = parse_args()
    random.seed(args.seed)

    if not args.zip and not args.source_dir:
        print("Provide either --zip <path to .zip> or --source-dir <already-extracted folder>")
        sys.exit(1)

    if args.zip:
        zip_path = Path(args.zip).expanduser()
        if not zip_path.exists():
            print(f"Zip not found: {zip_path}")
            sys.exit(1)
        extract_root = PROJECT_ROOT / "datasets" / "_raw_extracted"
        source_root = extract_zip(zip_path, extract_root)
    else:
        source_root = Path(args.source_dir).expanduser()
        if not source_root.exists():
            print(f"Folder not found: {source_root}")
            sys.exit(1)

    print("\nScanning for train/val/test folders (with NORMAL + PNEUMONIA subfolders) ...")
    splits = find_split_dirs(source_root)

    if "train" not in splits:
        print(
            "\nCouldn't automatically find a 'train' folder containing NORMAL/ and PNEUMONIA/ subfolders.\n"
            f"Looked under: {source_root}\n"
            "Please check the extracted structure manually, e.g.:\n"
            f"    Get-ChildItem -Recurse -Directory \"{source_root}\" | Select-Object FullName\n"
            "and either rename folders to match, or copy files into datasets/train/NORMAL etc. yourself."
        )
        sys.exit(1)

    print(f"Found: { {k: str(v) for k, v in splits.items()} }")

    out_train = PROJECT_ROOT / "datasets" / "train"
    out_val = PROJECT_ROOT / "datasets" / "validation"
    out_test = PROJECT_ROOT / "datasets" / "test"

    # --- test split: copy as-is if present ---
    if "test" in splits:
        print("\nCopying test split as-is ...")
        for cls in CLASSES:
            n = count_images(splits["test"] / cls) if args.dry_run else copy_all(splits["test"] / cls, out_test / cls, args.dry_run)
            print(f"  test/{cls}: {n} images")
    else:
        print("\nNo test/ folder found -- you'll want to carve one out manually, or point --source-dir "
              "at a location that includes it.")

    # --- train/validation: re-split train for a properly-sized validation set ---
    print(f"\nSplitting train -> train ({1-args.val_fraction:.0%}) / validation ({args.val_fraction:.0%}) ...")
    for cls in CLASSES:
        src_cls_dir = splits["train"] / cls
        files = [f for f in src_cls_dir.iterdir() if f.suffix.lower() in IMG_EXTENSIONS]
        random.shuffle(files)
        n_val = max(1, int(len(files) * args.val_fraction))
        val_files, train_files = files[:n_val], files[n_val:]

        if not args.dry_run:
            (out_train / cls).mkdir(parents=True, exist_ok=True)
            (out_val / cls).mkdir(parents=True, exist_ok=True)
            for f in train_files:
                shutil.copy2(f, out_train / cls / f.name)
            for f in val_files:
                shutil.copy2(f, out_val / cls / f.name)

        # fold in the original val/ split too, if the zip had one
        extra = 0
        if "val" in splits and (splits["val"] / cls).is_dir():
            orig_val_files = [f for f in (splits["val"] / cls).iterdir() if f.suffix.lower() in IMG_EXTENSIONS]
            extra = len(orig_val_files)
            if not args.dry_run:
                for f in orig_val_files:
                    shutil.copy2(f, out_val / cls / f.name)

        print(f"  train/{cls}: {len(train_files)} | validation/{cls}: {len(val_files) + extra}")

    if args.dry_run:
        print("\n(dry run -- nothing was actually copied)")
    else:
        print(f"\nDone. Dataset ready under {PROJECT_ROOT / 'datasets'}.")
        print("Sanity-check counts with:")
        print('  python -c "from utils.config import load_config; from utils.dataset import ChestXrayDataset; '
              "cfg = load_config('configs/config.yaml'); "
              "print({s: ChestXrayDataset(getattr(cfg.data, s+'_dir'), cfg.data.classes).class_counts() "
              "for s in ['train','val','test']})\"")
        print(f"\nRaw extracted files kept at {source_root} in case you want to inspect them; "
              f"safe to delete afterwards.")


if __name__ == "__main__":
    main()
