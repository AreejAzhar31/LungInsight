"""
Importing every model here ensures they're all registered on
`Base.metadata` before Alembic autogenerate or `create_all()` runs.
"""

from app.models.user import User
from app.models.uploaded_image import UploadedImage
from app.models.prediction import Prediction
from app.models.feedback import Feedback
from app.models.chat import ChatSession, ChatMessage
from app.models.log import Log
from app.models.knowledge_source import KnowledgeSource

__all__ = [
    "User",
    "UploadedImage",
    "Prediction",
    "Feedback",
    "ChatSession",
    "ChatMessage",
    "Log",
    "KnowledgeSource",
]
