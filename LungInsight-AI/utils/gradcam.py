"""
Grad-CAM explainability for the pneumonia classifier.

Implemented from scratch with forward/backward hooks (no external Grad-CAM
dependency required, though `grad-cam` is listed in requirements.txt as an
optional alternative). Produces:
    - a raw heatmap
    - an original-vs-overlay side-by-side image
    - adjustable overlay transparency
    - PNG export
"""

from __future__ import annotations
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F


class GradCAM:
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None

        self._fwd_handle = target_layer.register_forward_hook(self._save_activation)
        self._bwd_handle = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, inp, out):
        self.activations = out.detach()

    def _save_gradient(self, module, grad_in, grad_out):
        self.gradients = grad_out[0].detach()

    def remove_hooks(self):
        self._fwd_handle.remove()
        self._bwd_handle.remove()

    def generate(self, input_tensor: torch.Tensor, class_idx: int | None = None):
        """
        input_tensor: (1, C, H, W), already normalized/preprocessed.
        Returns: heatmap (H, W) in [0, 1], predicted class index, confidence (softmax prob).
        """
        self.model.eval()
        input_tensor = input_tensor.clone().requires_grad_(True)

        logits = self.model(input_tensor)
        probs = F.softmax(logits, dim=1)

        if class_idx is None:
            class_idx = int(torch.argmax(probs, dim=1).item())
        confidence = float(probs[0, class_idx].item())

        self.model.zero_grad()
        score = logits[0, class_idx]
        score.backward()

        # Global-average-pool the gradients -> channel importance weights
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)  # (1, 1, H, W)
        cam = F.relu(cam)

        cam = cam.squeeze().cpu().numpy()
        cam = cv2.resize(cam, (input_tensor.shape[3], input_tensor.shape[2]))
        cam -= cam.min()
        if cam.max() > 0:
            cam /= cam.max()

        return cam, class_idx, confidence


def denormalize_image(tensor: torch.Tensor, mean: list[float], std: list[float]) -> np.ndarray:
    """Converts a normalized (C,H,W) tensor back to a uint8 RGB (H,W,C) numpy image."""
    img = tensor.clone().detach().cpu().numpy().transpose(1, 2, 0)
    mean = np.array(mean)
    std = np.array(std)
    img = (img * std) + mean
    img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
    return img


def overlay_heatmap(
    original_rgb: np.ndarray, cam: np.ndarray, alpha: float = 0.45, colormap: int = cv2.COLORMAP_JET
) -> np.ndarray:
    """Overlays a [0,1] cam heatmap on top of an RGB uint8 original image."""
    heatmap = np.uint8(255 * cam)
    heatmap = cv2.applyColorMap(heatmap, colormap)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    overlay = cv2.addWeighted(original_rgb, 1 - alpha, heatmap, alpha, 0)
    return overlay, heatmap


def save_gradcam_outputs(
    original_rgb: np.ndarray,
    cam: np.ndarray,
    out_dir: str | Path,
    filename_stem: str,
    alpha: float = 0.45,
):
    """
    Saves three PNGs:
        {stem}_heatmap.png   - raw heatmap only
        {stem}_overlay.png   - heatmap overlaid on original
        {stem}_sidebyside.png - original | overlay side by side
    Returns dict of paths.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    overlay, heatmap = overlay_heatmap(original_rgb, cam, alpha=alpha)

    heatmap_path = out_dir / f"{filename_stem}_heatmap.png"
    overlay_path = out_dir / f"{filename_stem}_overlay.png"
    side_path = out_dir / f"{filename_stem}_sidebyside.png"

    cv2.imwrite(str(heatmap_path), cv2.cvtColor(heatmap, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(overlay_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    side_by_side = np.concatenate([original_rgb, overlay], axis=1)
    cv2.imwrite(str(side_path), cv2.cvtColor(side_by_side, cv2.COLOR_RGB2BGR))

    return {
        "heatmap": str(heatmap_path),
        "overlay": str(overlay_path),
        "side_by_side": str(side_path),
    }


def get_layer_by_name(model: torch.nn.Module, layer_name: str) -> torch.nn.Module:
    """Resolves a dotted layer path like 'backbone.features.8' to the actual module."""
    module = model
    for part in layer_name.split("."):
        if part.isdigit():
            module = module[int(part)]
        else:
            module = getattr(module, part)
    return module
