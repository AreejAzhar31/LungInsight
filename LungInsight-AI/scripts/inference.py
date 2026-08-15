"""
inference.py — Core, importable inference function.

This is the module later API/backend layers would import from (not built here,
per project scope). It loads a trained checkpoint once, then exposes
`run_inference(image_path)` which returns a JSON-serializable dict:

    {
        "prediction": "Pneumonia",
        "confidence": 96.4,
        "heatmap": "outputs/gradcam/img1_overlay.png"
    }

Usage as a library:
    from scripts.inference import LungInsightPredictor
    predictor = LungInsightPredictor(checkpoint_path="checkpoints/best.pt")
    result = predictor.predict("some_xray.jpeg")
    print(result)

Usage as a CLI (single image, prints JSON to stdout):
    python scripts/inference.py --image path/to/xray.jpeg --checkpoint checkpoints/best.pt
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import cv2
import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.config import load_config
from utils.common import get_device
from utils.augmentation import build_inference_transform
from utils.checkpoint import load_checkpoint
from utils.gradcam import GradCAM, denormalize_image, save_gradcam_outputs, get_layer_by_name
from models.efficientnet import build_model


class LungInsightPredictor:
    def __init__(self, checkpoint_path: str, config_path: str = "configs/config.yaml"):
        self.cfg = load_config(config_path)
        self.device = get_device(self.cfg.project.device)

        self.model = build_model(self.cfg).to(self.device)
        load_checkpoint(checkpoint_path, self.model, map_location=str(self.device))
        self.model.eval()

        self.transform = build_inference_transform(self.cfg)
        self.class_names = self.cfg.data.classes  # ["NORMAL", "PNEUMONIA"]

        target_layer = get_layer_by_name(self.model, self.cfg.gradcam.target_layer)
        self.gradcam = GradCAM(self.model, target_layer)

    def _preprocess(self, image_path: str):
        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise FileNotFoundError(f"Could not read image at {image_path}")
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        augmented = self.transform(image=image_rgb)
        tensor = augmented["image"].unsqueeze(0).to(self.device)
        return tensor

    def predict(self, image_path: str, generate_heatmap: bool = True, alpha: float | None = None) -> dict:
        image_path = Path(image_path)
        tensor = self._preprocess(image_path)
        alpha = alpha if alpha is not None else self.cfg.gradcam.overlay_alpha

        cam, class_idx, confidence = self.gradcam.generate(tensor)

        result = {
            "prediction": self.class_names[class_idx].capitalize(),
            "confidence": round(confidence * 100, 1),
        }

        if generate_heatmap:
            original_rgb = denormalize_image(
                tensor.squeeze(0), self.cfg.augmentation.normalize_mean, self.cfg.augmentation.normalize_std
            )
            out_dir = Path(self.cfg.gradcam.outputs_dir)
            paths = save_gradcam_outputs(
                original_rgb, cam, out_dir, filename_stem=image_path.stem, alpha=alpha
            )
            result["heatmap"] = paths["overlay"]
            result["heatmap_raw"] = paths["heatmap"]
            result["heatmap_side_by_side"] = paths["side_by_side"]

        return result

    def close(self):
        self.gradcam.remove_hooks()


def parse_args():
    p = argparse.ArgumentParser(description="Run single-image inference with Grad-CAM")
    p.add_argument("--image", type=str, required=True)
    p.add_argument("--checkpoint", type=str, required=True)
    p.add_argument("--config", type=str, default="configs/config.yaml")
    p.add_argument("--no-heatmap", action="store_true")
    p.add_argument("--alpha", type=float, default=None, help="Grad-CAM overlay transparency (0-1)")
    return p.parse_args()


def main():
    args = parse_args()
    predictor = LungInsightPredictor(args.checkpoint, args.config)
    result = predictor.predict(args.image, generate_heatmap=not args.no_heatmap, alpha=args.alpha)
    predictor.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
