"""
Prediction results.

This backend does NOT run the AI model itself (that's a separate module).
`InferenceClient` (see app/services/inference_client.py) is the pluggable
interface this table's data is populated through — swap the stub
implementation for a real HTTP call to the model-serving module when it's
ready, with no changes needed here.
"""

from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("uploaded_images.id", ondelete="CASCADE"), nullable=False
    )

    label: Mapped[str] = mapped_column(String(50), nullable=False)  # "Normal" | "Pneumonia"
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    heatmap_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="predictions")
    image = relationship("UploadedImage", back_populates="predictions")
    feedback = relationship("Feedback", back_populates="prediction", cascade="all, delete-orphan")
