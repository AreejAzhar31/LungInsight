"""
Groq LLM client wrapper.

Thin wrapper around the `groq` Python SDK so the rest of the codebase depends
on a small `.chat()` interface instead of the SDK directly — this keeps
`agent/nodes.py` testable with a fake LLM client (see tests/conftest.py) and
makes it easy to swap providers later.

The client is constructed lazily (no network/SDK import at module import
time) and raises a clear error if `GROQ_API_KEY` is missing when actually
invoked, rather than failing silently.
"""
from __future__ import annotations

from typing import Protocol


class LLMClientProtocol(Protocol):
    def chat(self, system_prompt: str, user_prompt: str) -> str: ...


class GroqLLMClient:
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.2,
        max_tokens: int = 900,
        timeout_s: int = 30,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_s = timeout_s
        self._client = None

    def _load(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "GROQ_API_KEY is not set. Export it or set it in your .env before "
                    "invoking the LLM (see .env.example)."
                )
            try:
                from groq import Groq
            except ImportError as exc:  # pragma: no cover
                raise ImportError(
                    "The 'groq' package is required. Install with: pip install groq"
                ) from exc
            self._client = Groq(api_key=self.api_key, timeout=self.timeout_s)
        return self._client

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        client = self._load()
        response = client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""
