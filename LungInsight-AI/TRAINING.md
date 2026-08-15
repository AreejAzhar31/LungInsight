# TRAINING.md — LungInsight AI Training & Usage Guide

## 1. Setup

```bash
cd LungInsight-AI
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

> **Windows/PowerShell note:** if `Activate.ps1` is blocked, run PowerShell as
> Administrator once and execute:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

GPU training requires a CUDA-enabled PyTorch build. If `torch.cuda.is_available()`
returns `False`, everything still runs on CPU automatically (just slower) — the config's
`project.device: "cuda"` gracefully falls back via `utils.common.get_device`.

## 2. Add Your Data

Follow `DATASET.md` to populate `datasets/train`, `datasets/validation`, `datasets/test`.

## 3. Train

```bash
python scripts/train.py --config configs/config.yaml
```

Common overrides (no need to edit the YAML for quick experiments):

```bash
python scripts/train.py --epochs 30 --batch-size 32 --lr 0.0005
```

Resume an interrupted run:

```bash
python scripts/train.py --resume checkpoints/last.pt
```

What happens automatically during training:
- **Transfer learning → fine-tuning transition**: backbone starts frozen, unfreezes
  after `model.freeze_backbone_epochs` epochs, optimizer/LR switch accordingly.
- **Mixed precision**: enabled automatically on CUDA if `training.mixed_precision: true`.
- **LR scheduling**: `ReduceLROnPlateau` by default (reduces LR when val loss plateaus).
- **Early stopping**: stops training if val loss doesn't improve for
  `training.early_stopping_patience` epochs.
- **Checkpointing**: `checkpoints/best.pt` (best val loss so far) and
  `checkpoints/last.pt` (always the most recent epoch, for resuming) are both written
  every epoch.
- **TensorBoard logging**: scalars written to `logs/<timestamp>/`.

Monitor training live:

```bash
tensorboard --logdir logs/
```

At the end of training, loss/accuracy curves are saved to
`outputs/training_curves.png`.

## 4. Evaluate

```bash
python scripts/evaluate.py --checkpoint checkpoints/best.pt --split test
```

Produces, in `outputs/`:
- `metrics.json` — accuracy, precision, recall, F1, ROC AUC
- `confusion_matrix.png`
- `roc_curve.png`
- `classification_report.txt`

## 5. Run Inference on a Single Image (with Grad-CAM)

```bash
python scripts/inference.py --image path/to/xray.jpeg --checkpoint checkpoints/best.pt
```

Prints:

```json
{
  "prediction": "Pneumonia",
  "confidence": 96.4,
  "heatmap": "outputs/gradcam/xray_overlay.png",
  "heatmap_raw": "outputs/gradcam/xray_heatmap.png",
  "heatmap_side_by_side": "outputs/gradcam/xray_sidebyside.png"
}
```

This exact `LungInsightPredictor` class (in `scripts/inference.py`) is the intended
integration point for a future backend/API layer — it loads the checkpoint once and
exposes a simple `.predict(image_path)` method.

Adjust Grad-CAM overlay transparency:

```bash
python scripts/inference.py --image xray.jpeg --checkpoint checkpoints/best.pt --alpha 0.6
```

Skip heatmap generation (faster, prediction-only):

```bash
python scripts/inference.py --image xray.jpeg --checkpoint checkpoints/best.pt --no-heatmap
```

## 6. Batch Predictions

```bash
python scripts/predict.py --input-dir samples/ --checkpoint checkpoints/best.pt
```

Writes `outputs/predictions.csv` summarizing every image in the folder, plus
individual Grad-CAM PNGs per image under `outputs/gradcam/`.

## 7. Running Tests

```bash
pytest tests/ -v
```

Covers preprocessing/augmentation shapes & determinism, dataset loading/indexing
against a synthetic dataset, the inference pipeline end-to-end (with a small
randomly-initialized model so it runs fast and offline), and Grad-CAM heatmap
generation + PNG export.

## 8. Project Structure Reference

```
LungInsight-AI/
├── configs/
│   └── config.yaml          # single source of truth for all hyperparameters
├── datasets/                # train/ validation/ test/  (you populate this)
├── models/
│   └── efficientnet.py      # EfficientNet-B3 model definition
├── utils/
│   ├── config.py            # YAML config loader
│   ├── common.py            # seeding, device selection
│   ├── augmentation.py      # train/eval Albumentations pipelines
│   ├── dataset.py           # ChestXrayDataset + DataLoader builders
│   ├── checkpoint.py        # save/load/resume, EarlyStopping
│   ├── metrics.py           # accuracy/precision/recall/F1/ROC-AUC + plots
│   └── gradcam.py           # Grad-CAM implementation
├── scripts/
│   ├── train.py             # main training loop
│   ├── evaluate.py          # test-set evaluation + plots
│   ├── predict.py           # batch prediction over a folder
│   └── inference.py         # single-image inference + Grad-CAM (importable class)
├── tests/                   # pytest suite
├── checkpoints/             # best.pt / last.pt written here
├── logs/                    # TensorBoard event files
├── outputs/                 # metrics, plots, Grad-CAM PNGs, predictions.csv
├── notebooks/                # optional exploratory notebooks
├── MODEL.md
├── DATASET.md
├── TRAINING.md
└── requirements.txt
```

## 9. Known Windows/PowerShell Gotchas

- If `pip install -r requirements.txt` fails building `opencv-python`, the
  `opencv-python-headless` variant pinned here avoids the GUI dependency issues
  common on Windows.
- Use `Get-Content` to sanity-check that a config edit actually saved before
  re-running a script, if PowerShell/your editor has ever silently failed to
  write a file.
- Long paths: if you hit `FileNotFoundError` on deeply nested checkpoint paths,
  enable long path support (`git config --system core.longpaths true` and/or
  the Windows long-paths group policy setting).

## Out of Scope (by design)

This project is the AI/computer-vision layer only. It intentionally does **not**
include a frontend, backend API, authentication, database, chat assistant, or RAG —
those are later modules that would import `scripts/inference.py`'s
`LungInsightPredictor` class as their model-serving layer.
