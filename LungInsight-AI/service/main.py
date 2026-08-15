"""
LungInsight AI — Model Serving Microservice.

Wraps `scripts.inference.LungInsightPredictor` (Module 1) behind a small
HTTP API so the Backend (Module 2) can call it without an in-process
import, keeping the two modules independently deployable — per the
integration decision already made in the project handoff.

Run with:
    uvicorn service.main:app --host 0.0.0.0 --port 8500

Config via environment variables (see .env.example in this folder):
    CHECKPOINT_PATH   - path to trained model weights (required to serve
                         real predictions; service still starts without it
                         so /health can report the problem clearly)
    CONFIG_PATH        - path to configs/config.yaml (default shown below)
    HEATMAP_OUTPUT_DIR - where Grad-CAM PNGs are written (default outputs/gradcam)
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("lunginsight.model_service")

CHECKPOINT_PATH = os.environ.get("CHECKPOINT_PATH", "checkpoints/best.pt")
CONFIG_PATH = os.environ.get("CONFIG_PATH", "configs/config.yaml")
HEATMAP_OUTPUT_DIR = Path(os.environ.get("HEATMAP_OUTPUT_DIR", "outputs/gradcam"))
HEATMAP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="LungInsight AI — Model Serving Service",
    description="Internal microservice: runs EfficientNet-B3 inference + Grad-CAM. Not exposed publicly.",
    version="1.0.0",
)

app.mount("/heatmaps", StaticFiles(directory=str(HEATMAP_OUTPUT_DIR)), name="heatmaps")

_predictor = None
_load_error: str | None = None


def _try_load_predictor():
    """Loads the model once at startup. Failure is stored, not fatal —
    the service still starts so /health can surface a clear error instead
    of the container just crash-looping."""
    global _predictor, _load_error
    try:
        from scripts.inference import LungInsightPredictor  # local import: heavy (torch)

        if not Path(CHECKPOINT_PATH).exists():
            raise FileNotFoundError(
                f"Checkpoint not found at '{CHECKPOINT_PATH}'. Set CHECKPOINT_PATH env var "
                f"to your trained best.pt."
            )

        _predictor = LungInsightPredictor(checkpoint_path=CHECKPOINT_PATH, config_path=CONFIG_PATH)
        logger.info("Model loaded from %s", CHECKPOINT_PATH)
    except Exception as exc:  # noqa: BLE001 — deliberately broad, surfaced via /health
        _load_error = str(exc)
        logger.error("Model failed to load: %s", exc)


@app.on_event("startup")
def on_startup():
    _try_load_predictor()


@app.get("/health")
def health():
    return {
        "status": "ok" if _predictor is not None else "degraded",
        "model_loaded": _predictor is not None,
        "checkpoint_path": CHECKPOINT_PATH,
        "error": _load_error,
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if _predictor is None:
        # Re-attempt a load in case the checkpoint appeared after startup
        # (e.g. dropped in mid-session during local dev).
        _try_load_predictor()
        if _predictor is None:
            raise HTTPException(
                status_code=503,
                detail=f"Model is not loaded: {_load_error or 'unknown error'}",
            )

    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        try:
            result = _predictor.predict(tmp_path, generate_heatmap=True)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=f"Could not read uploaded image: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Inference failed")
            raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    overlay_path = Path(result["heatmap"])
    heatmap_filename = overlay_path.name

    return {
        "prediction": result["prediction"],
        "confidence": result["confidence"],
        "heatmap_filename": heatmap_filename,
        "heatmap_url": f"/heatmaps/{heatmap_filename}",
    }


@app.get("/heatmaps/{filename}")
def get_heatmap(filename: str):
    # Explicit route kept in addition to the StaticFiles mount above so a
    # missing file returns a clean 404 with a useful message rather than
    # StaticFiles' generic one.
    path = HEATMAP_OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Heatmap not found.")
    return FileResponse(path)
