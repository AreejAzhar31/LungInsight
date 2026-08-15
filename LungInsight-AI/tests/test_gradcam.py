"""Tests for Grad-CAM heatmap generation and PNG export."""
import sys
from pathlib import Path

import numpy as np
import torch
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.gradcam import GradCAM, denormalize_image, save_gradcam_outputs, get_layer_by_name
from models.efficientnet import PneumoniaClassifier


@pytest.fixture(scope="module")
def tiny_model():
    # pretrained=False for a fast, offline test model
    model = PneumoniaClassifier(num_classes=2, pretrained=False, dropout=0.3)
    model.eval()
    return model


def test_get_layer_by_name_resolves_conv_block(tiny_model):
    layer = get_layer_by_name(tiny_model, "backbone.features.8")
    assert isinstance(layer, torch.nn.Module)


def test_gradcam_generates_valid_heatmap(tiny_model):
    target_layer = get_layer_by_name(tiny_model, "backbone.features.8")
    cam_engine = GradCAM(tiny_model, target_layer)

    dummy_input = torch.randn(1, 3, 64, 64)
    cam, class_idx, confidence = cam_engine.generate(dummy_input)
    cam_engine.remove_hooks()

    assert cam.shape == (64, 64)
    assert cam.min() >= 0.0 and cam.max() <= 1.0 + 1e-6
    assert class_idx in (0, 1)
    assert 0.0 <= confidence <= 1.0


def test_gradcam_png_export(tiny_model, tmp_path):
    target_layer = get_layer_by_name(tiny_model, "backbone.features.8")
    cam_engine = GradCAM(tiny_model, target_layer)

    dummy_input = torch.randn(1, 3, 64, 64)
    cam, _, _ = cam_engine.generate(dummy_input)
    cam_engine.remove_hooks()

    original_rgb = denormalize_image(
        dummy_input.squeeze(0), mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    )
    paths = save_gradcam_outputs(original_rgb, cam, tmp_path, filename_stem="test_img", alpha=0.45)

    for key in ("heatmap", "overlay", "side_by_side"):
        assert Path(paths[key]).exists()
        assert Path(paths[key]).stat().st_size > 0


def test_denormalize_image_range():
    tensor = torch.zeros(3, 32, 32)
    img = denormalize_image(tensor, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    assert img.dtype == np.uint8
    assert img.shape == (32, 32, 3)
    assert img.min() >= 0 and img.max() <= 255
