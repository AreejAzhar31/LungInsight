"""
Inference client — the integration point with the (separately-built) AI
model module.

This backend does NOT run any model. `InferenceClient` defines the
contract; `StubInferenceClient` is a placeholder implementation so the
backend is fully runnable and testable end-to-end on its own. Swap it for
a real HTTP client (calling the model-serving module's `/predict`
endpoint, or importing `LungInsightPredictor` in-process) by implementing
the same `predict()` signature and updating the dependency wiring in
`app/api/dependencies.py` — no other code needs to change.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from pathlib import Path
import httpx

from app.core.exceptions import InferenceServiceError

logger = logging.getLogger("app.inference_client")

@dataclass
class InferenceResult:
    label: str  # "Normal" | "Pneumonia"
    confidence: float  # 0-100
    heatmap_path: str | None = None


class InferenceClient(ABC):
    @abstractmethod
    def predict(self, image_path: str) -> InferenceResult:
        raise NotImplementedError


class StubInferenceClient(InferenceClient):
    """
    Deterministic placeholder so the API is fully testable without the AI
    module wired up. Replace with a real client before production use.
    """

    def predict(self, image_path: str) -> InferenceResult:
        return InferenceResult(label="Pneumonia", confidence=87.5, heatmap_path=None)

 
class HttpInferenceClient(InferenceClient):
    """
    Real client — calls the Module 1 model-serving microservice
    (ai/service/main.py) over HTTP, per the integration decision to keep
    modules independently deployable (no in-process import of torch/the
    model into this backend).
 
    Downloads the returned Grad-CAM heatmap and re-saves it under this
    backend's own upload_dir/heatmaps/, so `Prediction.heatmap_path` is a
    URL this backend can serve itself (/static/heatmaps/<file>.png) —
    the frontend never needs to know the model service exists.
    """
 
    def __init__(self, base_url: str, heatmap_dir: str, timeout_seconds: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.heatmap_dir = Path(heatmap_dir)
        self.heatmap_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
 
    def predict(self, image_path: str) -> InferenceResult:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                with open(image_path, "rb") as f:
                    response = client.post(
                        f"{self.base_url}/predict",
                        files={"file": (Path(image_path).name, f, "application/octet-stream")},
                    )
                response.raise_for_status()
                data = response.json()
 
                heatmap_path = self._fetch_heatmap(client, data.get("heatmap_url"))
        except httpx.TimeoutException as exc:
            raise InferenceServiceError("The AI model service timed out. Please try again.") from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:300]
            raise InferenceServiceError(f"AI model service returned an error: {detail}") from exc
        except httpx.ConnectError as exc:
            raise InferenceServiceError(
                "Could not reach the AI model service. Make sure it is running "
                f"at {self.base_url}."
            ) from exc
 
        return InferenceResult(
            label=data["prediction"],
            confidence=float(data["confidence"]),
            heatmap_path=heatmap_path,
        )
 
    def _fetch_heatmap(self, client: httpx.Client, heatmap_url: str | None) -> str | None:
        if not heatmap_url:
            return None
        try:
            resp = client.get(f"{self.base_url}{heatmap_url}")
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            # Prediction itself succeeded — don't fail the whole request
            # just because the heatmap couldn't be fetched.
            logger.warning("Failed to fetch heatmap %s: %s", heatmap_url, exc)
            return None
 
        filename = Path(heatmap_url).name
        destination = self.heatmap_dir / filename
        destination.write_bytes(resp.content)
        return f"/static/heatmaps/{filename}"
 

