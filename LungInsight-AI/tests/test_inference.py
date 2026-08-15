"""
Tests for the inference pipeline (LungInsightPredictor).

Uses pretrained=False and a freshly-initialized model saved as a throwaway
checkpoint, so these tests run fast and offline (no ImageNet weight download,
no GPU required).
"""
import sys
import shutil
from pathlib import Path

import numpy as np
import cv2
import pytest
import yaml

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.config import load_config
from utils.checkpoint import save_checkpoint
from models.efficientnet import build_model
from scripts.inference import LungInsightPredictor


@pytest.fixture()
def tiny_env(tmp_path):
    """Builds a small config (pretrained=False, small image size) + throwaway checkpoint + sample image."""
    base_cfg_path = Path(__file__).resolve().parent.parent / "configs" / "config.yaml"
    with open(base_cfg_path) as f:
        raw_cfg = yaml.safe_load(f)

    raw_cfg["model"]["pretrained"] = False
    raw_cfg["data"]["image_size"] = 64
    raw_cfg["gradcam"]["target_layer"] = "backbone.features.8"
    raw_cfg["gradcam"]["outputs_dir"] = str(tmp_path / "gradcam_out")

    cfg_path = tmp_path / "config.yaml"
    with open(cfg_path, "w") as f:
        yaml.safe_dump(raw_cfg, f)

    cfg = load_config(str(cfg_path))
    model = build_model(cfg)
    ckpt_path = tmp_path / "tiny.pt"
    save_checkpoint(ckpt_path, model, optimizer=None, scheduler=None, scaler=None, epoch=0, best_metric=0.0)

    image_path = tmp_path / "sample.png"
    img = (np.random.rand(120, 120, 3) * 255).astype(np.uint8)
    cv2.imwrite(str(image_path), img)

    return cfg_path, ckpt_path, image_path


def test_predictor_returns_expected_keys(tiny_env):
    cfg_path, ckpt_path, image_path = tiny_env
    predictor = LungInsightPredictor(str(ckpt_path), str(cfg_path))
    result = predictor.predict(str(image_path))
    predictor.close()

    assert "prediction" in result
    assert "confidence" in result
    assert "heatmap" in result
    assert result["prediction"] in ("Normal", "Pneumonia")
    assert 0.0 <= result["confidence"] <= 100.0


def test_predictor_without_heatmap(tiny_env):
    cfg_path, ckpt_path, image_path = tiny_env
    predictor = LungInsightPredictor(str(ckpt_path), str(cfg_path))
    result = predictor.predict(str(image_path), generate_heatmap=False)
    predictor.close()

    assert "heatmap" not in result
    assert "prediction" in result and "confidence" in result


def test_predictor_missing_image_raises(tiny_env):
    cfg_path, ckpt_path, _ = tiny_env
    predictor = LungInsightPredictor(str(ckpt_path), str(cfg_path))
    with pytest.raises(FileNotFoundError):
        predictor.predict("/nonexistent/image.png")
    predictor.close()
