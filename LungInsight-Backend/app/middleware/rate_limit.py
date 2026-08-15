"""
Rate limiting configuration using slowapi (Flask-Limiter-style, adapted for
FastAPI/Starlette). Limits are keyed by client IP address.
"""

from __future__ import annotations
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
