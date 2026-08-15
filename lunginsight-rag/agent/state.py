"""
Shared state passed between LangGraph nodes.

Kept as a plain TypedDict (rather than a pydantic model) because that is what
LangGraph's `StateGraph` expects natively, and it keeps node functions simple:
each node receives the state dict, returns a partial dict of updates, and
LangGraph merges it.
"""
from __future__ import annotations

from typing import Any, TypedDict


class ChatTurn(TypedDict):
    role: str  # "user" | "assistant"
    content: str


class RetrievedChunkDict(TypedDict):
    chunk_id: str
    document_id: str
    title: str
    organization: str
    topic: str
    source_url: str
    section_heading: str
    text: str
    score: float


class AgentState(TypedDict, total=False):
    # --- input -----------------------------------------------------------
    user_message: str
    prediction_context: dict[str, Any] | None  # from the upstream CNN/GradCAM API
    history: list[ChatTurn]

    # --- safety ------------------------------------------------------------
    is_safe: bool
    safety_reason: str | None
    sanitized_message: str

    # --- retrieval --------------------------------------------------------
    retrieval_query: str
    retrieved_chunks: list[RetrievedChunkDict]
    retrieval_sufficient: bool

    # --- generation ------------------------------------------------------
    raw_llm_output: str
    answer: dict[str, Any] | None  # structured final answer
    verification_passed: bool
    verification_notes: list[str]
    regeneration_attempts: int

    # --- routing / terminal -----------------------------------------------
    route: str  # "retrieve" | "refuse_unsafe" | "refuse_insufficient_evidence" | "generate" | "done"
    error: str | None
