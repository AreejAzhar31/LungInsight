"""User feedback on a prediction (e.g. clinician agrees/disagrees)."""

from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False
    )

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g. 1-5, or 1=disagree/5=agree
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="feedback")
    prediction = relationship("Prediction", back_populates="feedback")
