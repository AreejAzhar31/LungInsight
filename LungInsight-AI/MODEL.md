# MODEL.md — LungInsight AI Model Documentation

## Architecture

**Backbone:** EfficientNet-B3 (`torchvision.models.efficientnet_b3`)
**Pretrained weights:** ImageNet1K (`EfficientNet_B3_Weights.IMAGENET1K_V1`) — the **only**
pretrained weights used anywhere in this project.
**Head:** `Dropout(p=0.3) -> Linear(in_features=1536, out_features=2)`, trained entirely
from scratch on chest X-ray data.
**Input resolution:** 300×300 (EfficientNet-B3's native resolution).
**Output:** 2-class logits — index 0 = `NORMAL`, index 1 = `PNEUMONIA`.

```
Input (3, 300, 300)
      │
      ▼
EfficientNet-B3 feature extractor (backbone.features)   [ImageNet-pretrained]
      │
      ▼
Global Average Pool (backbone.avgpool)
      │
      ▼
Flatten -> Dropout(0.3) -> Linear(1536 -> 2)             [trained from scratch]
      │
      ▼
Softmax -> {NORMAL, PNEUMONIA}
```

## Transfer Learning Strategy

Training happens in two phases, controlled by `model.freeze_backbone_epochs` in
`configs/config.yaml`:

1. **Transfer learning phase** (epochs `0` .. `freeze_backbone_epochs - 1`)
   The EfficientNet-B3 backbone is **frozen**; only the new classifier head is trained,
   at the higher learning rate `training.lr`. This lets the head adapt quickly to
   chest X-rays without disturbing the pretrained ImageNet features.

2. **Fine-tuning phase** (epochs `freeze_backbone_epochs` .. end)
   The backbone is **unfrozen** and the whole network is trained end-to-end at a much
   lower learning rate `training.fine_tune_lr` (10x smaller by default), so the
   pretrained features are adapted gently rather than destroyed.

The transition is automatic inside `scripts/train.py` — no manual intervention needed.
It also transparently handles the case where training is **resumed** mid-fine-tuning
(the optimizer's parameter groups are rebuilt to match the checkpoint's freeze state
before its state dict is loaded).

## Training Configuration

All of the following are controlled from `configs/config.yaml` (`training:` section):

| Feature | Setting |
|---|---|
| Optimizer | AdamW (configurable to Adam) |
| Loss | CrossEntropyLoss with class weighting (inverse frequency) + label smoothing (0.05) |
| Mixed precision (AMP) | `torch.autocast` + `GradScaler`, auto-disabled on CPU |
| LR scheduler | `ReduceLROnPlateau` (default), or `CosineAnnealingLR` / `StepLR` |
| Gradient clipping | max-norm 1.0 |
| Early stopping | patience-based on validation loss |
| Checkpointing | `best.pt` (lowest val loss) + `last.pt` (most recent), both resumable |

## Why EfficientNet-B3?

EfficientNet-B3 sits in a good accuracy/compute sweet spot for medical imaging at
moderate resolution (300×300): it's deep enough to capture the subtle opacity patterns
that distinguish pneumonia from normal lungs, while remaining trainable on a single
consumer GPU with reasonable batch sizes. Its compound scaling (balancing depth, width,
and resolution) tends to generalize better than manually-scaled CNNs on chest X-ray
tasks of this size.

## Class Imbalance Handling

Chest X-ray pneumonia datasets are commonly imbalanced (more PNEUMONIA than NORMAL
samples, or vice versa depending on the source). `utils/dataset.compute_class_weights`
computes inverse-frequency weights per class from the **training split only**, which
are passed into `CrossEntropyLoss(weight=...)` so the minority class isn't drowned out.

## Explainability

See `MODEL.md` → Grad-CAM is implemented in `utils/gradcam.py` and hooks into the last
convolutional block of the backbone (`backbone.features.8` by default — configurable via
`gradcam.target_layer` in the config). Full details are documented in the code
docstrings; usage is described in `TRAINING.md`.

## Model File Locations

| Artifact | Path |
|---|---|
| Best checkpoint | `checkpoints/best.pt` |
| Last checkpoint (for resuming) | `checkpoints/last.pt` |
| TensorBoard logs | `logs/<timestamp>/` |
| Evaluation outputs | `outputs/metrics.json`, `outputs/confusion_matrix.png`, `outputs/roc_curve.png` |
| Grad-CAM outputs | `outputs/gradcam/` |
