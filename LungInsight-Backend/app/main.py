"""
LungInsight AI — Backend application entrypoint.

Wires together: CORS, rate limiting, exception handling, routers, and
OpenAPI/Swagger docs. Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.middleware.rate_limit import limiter
from app.api.routers import auth, predictions, history, feedback, health, chat

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend API for LungInsight AI — authentication, prediction storage, "
        "history, and feedback. Does not run the AI model itself; see the "
        "separate AI/computer-vision module for that."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---- rate limiting --------------------------------------------------

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---- CORS --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- application exception handling --------------------------------------------------

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# ---- routers --------------------------------------------------

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predictions.router)
app.include_router(history.router)
app.include_router(feedback.router)
app.include_router(chat.router)

# ---- static files (Grad-CAM heatmaps) --------------------------------------------------
# HttpInferenceClient saves fetched heatmaps here; Prediction.heatmap_path
# stores the matching "/static/heatmaps/<file>.png" URL for the frontend.

Path(settings.heatmap_dir).mkdir(parents=True, exist_ok=True)
app.mount("/static/heatmaps", StaticFiles(directory=settings.heatmap_dir), name="heatmaps")

# Serves original uploaded X-rays when STORAGE_MODE=local (LocalStorageClient
# returns "/uploads/<filename>" URLs). Not used at all in STORAGE_MODE=supabase,
# where images are fetched via signed URLs directly from Supabase instead --
# mounted unconditionally anyway so switching STORAGE_MODE back to local
# doesn't silently 404 on image URLs.
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }
