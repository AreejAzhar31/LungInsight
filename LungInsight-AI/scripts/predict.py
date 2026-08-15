"""
predict.py — Batch prediction CLI.

Runs inference (+ optional Grad-CAM) over every image in a folder and writes
a single predictions.csv summary. For single-image use, prefer inference.py.

Usage:
    python scripts/predict.py --input-dir samples/ --checkpoint checkpoints/best.pt
    python scripts/predict.py --input-dir samples/ --checkpoint checkpoints/best.pt --no-heatmap
"""

from __future__ import annotations
import argparse
import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from scripts.inference import LungInsightPredictor
except ImportError:
    from inference import LungInsightPredictor

IMG_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def parse_args():
    p = argparse.ArgumentParser(description="Batch-predict pneumonia on a folder of chest X-rays")
    p.add_argument("--input-dir", type=str, required=True)
    p.add_argument("--checkpoint", type=str, required=True)
    p.add_argument("--config", type=str, default="configs/config.yaml")
    p.add_argument("--output-csv", type=str, default="outputs/predictions.csv")
    p.add_argument("--no-heatmap", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    image_paths = sorted(
        [p for p in input_dir.iterdir() if p.suffix.lower() in IMG_EXTENSIONS]
    )
    if not image_paths:
        print(f"No images found in {input_dir}")
        return

    predictor = LungInsightPredictor(args.checkpoint, args.config)

    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for img_path in image_paths:
        result = predictor.predict(str(img_path), generate_heatmap=not args.no_heatmap)
        result["image"] = img_path.name
        rows.append(result)
        print(f"{img_path.name}: {result['prediction']} ({result['confidence']}%)")

    predictor.close()

    fieldnames = ["image", "prediction", "confidence", "heatmap"]
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved batch predictions -> {out_csv}")


if __name__ == "__main__":
    main()
