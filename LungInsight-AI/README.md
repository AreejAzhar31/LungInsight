# LungInsight AI — Model Training & Explainable Vision System

An end-to-end deep learning pipeline for classifying chest X-rays as **NORMAL** or
**PNEUMONIA**, built around a transfer-learned + fine-tuned **EfficientNet-B3**, with
full training/evaluation/inference scripts and **Grad-CAM** explainability.

This is the **AI/computer-vision module only** — no frontend, backend API,
authentication, database, chat assistant, or RAG. See `TRAINING.md` for the note on
scope and how a future backend would plug into `scripts/inference.py`.

## Quick Start

```bash
pip install -r requirements.txt
# populate datasets/train, datasets/validation, datasets/test — see DATASET.md
python scripts/train.py
python scripts/evaluate.py --checkpoint checkpoints/best.pt
python scripts/inference.py --image path/to/xray.jpeg --checkpoint checkpoints/best.pt
```

## Documentation

| File | Contents |
|---|---|
| [`DATASET.md`](DATASET.md) | Dataset folder structure, preprocessing/augmentation details, how to add your own data |
| [`MODEL.md`](MODEL.md) | Architecture, transfer learning strategy, training config, explainability |
| [`TRAINING.md`](TRAINING.md) | Full setup + usage guide for every script, project structure reference |

## What's Included

- **Dataset pipeline** — automatic train/val/test loading, resizing, normalization,
  augmentation (flip, rotation, brightness, random crop), batching
- **Model** — EfficientNet-B3 with ImageNet transfer learning + fine-tuning, configurable
  via `configs/config.yaml`
- **Training** — mixed precision, LR scheduling, early stopping, checkpointing (resumable),
  TensorBoard logging
- **Evaluation** — accuracy, precision, recall, F1, ROC AUC, confusion matrix, auto-saved plots
- **Explainability** — Grad-CAM heatmaps, original-vs-overlay images, adjustable transparency, PNG export
- **Tests** — pytest coverage for preprocessing, dataset loading, inference, Grad-CAM
- **Clean project structure** — separated configs / models / scripts / utilities / tests

## Output Contract

`scripts/inference.py`'s `LungInsightPredictor.predict()` returns:

```json
{
  "prediction": "Pneumonia",
  "confidence": 96.4,
  "heatmap": "outputs/gradcam/xray_overlay.png"
}
```
