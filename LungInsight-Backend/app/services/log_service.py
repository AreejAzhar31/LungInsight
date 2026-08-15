"""Log service — records user/system actions for audit purposes."""

from __future__ import annotations
import json
import uuid

from app.models.log import Log
from app.repositories.log_repository import LogRepository


class LogService:
    def __init__(self, log_repository: LogRepository):
        self.log_repository = log_repository

    def record(
        self,
        action: str,
        user_id: uuid.UUID | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> Log:
        log = Log(
            user_id=user_id,
            action=action,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
        )
        return self.log_repository.create(log)
