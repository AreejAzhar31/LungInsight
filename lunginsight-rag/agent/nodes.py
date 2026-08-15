"""
Graph nodes.

Each function takes the current `AgentState` and returns a partial-state
dict of updates, matching LangGraph's node contract. Nodes are pure w.r.t.
their explicit dependencies (embedder / vector_store / llm_client / memory
are injected via closures built in `graph.py`, never imported globally) so
they can be unit tested with fakes.

Flow:
    input_guard -> [retrieve -> grade_retrieval -> generate -> verify -> respond]
                (else) -> refuse_unsafe
    grade_retrieval -> refuse_insufficient_evidence (if not enough grounding)
    verify -> generate (bounded retry) -> verify -> respond | refuse_insufficient_evidence
"""
from __future__ import annotations

import re
from typing import Any

from config import settings
from ingestion.embedder import EmbedderProtocol
from ingestion.vector_store import VectorStore

from . import prompts
from .llm_client import LLMClientProtocol
from .memory import ConversationMemory
from .safety import check_input_safety, verify_output
from .state import AgentState

MAX_REGENERATION_ATTEMPTS = 1

_SECTION_HEADERS = {
    "plain_language": "Plain-language explanation:",
    "clinical": "Clinical explanation:",
    "next_steps": "Recommended next steps:",
    "sources": "Sources:",
    "disclaimer": "Confidence & disclaimer:",
}


def parse_structured_answer(raw_text: str) -> dict[str, Any]:
    """Split the LLM's raw text into the five expected sections."""
    positions: list[tuple[str, int]] = []
    for key, header in _SECTION_HEADERS.items():
        idx = raw_text.find(header)
        if idx != -1:
            positions.append((key, idx))
    positions.sort(key=lambda p: p[1])

    sections: dict[str, str] = {}
    for i, (key, start) in enumerate(positions):
        header_len = len(_SECTION_HEADERS[key])
        end = positions[i + 1][1] if i + 1 < len(positions) else len(raw_text)
        sections[key] = raw_text[start + header_len : end].strip()

    citations = re.findall(r"\[cite:([a-zA-Z0-9_\-]+::chunk-\d+)\]", raw_text)

    return {
        "plain_language_explanation": sections.get("plain_language", ""),
        "clinical_explanation": sections.get("clinical", ""),
        "recommended_next_steps": sections.get("next_steps", ""),
        "sources": sections.get("sources", ""),
        "confidence_disclaimer": sections.get("disclaimer", ""),
        "citations": sorted(set(citations)),
        "raw_text": raw_text,
    }


# --------------------------------------------------------------------------
# Node factories — each returns a node function closed over its dependencies.
# --------------------------------------------------------------------------

def make_input_guard_node():
    def input_guard(state: AgentState) -> dict:
        result = check_input_safety(state["user_message"], max_chars=settings.max_user_message_chars)
        if not result.is_safe:
            return {
                "is_safe": False,
                "safety_reason": result.reason,
                "sanitized_message": result.sanitized_message,
                "route": "refuse_unsafe",
            }
        return {
            "is_safe": True,
            "safety_reason": result.reason,
            "sanitized_message": result.sanitized_message,
            "route": "retrieve",
        }

    return input_guard


def _build_retrieval_query(state: AgentState) -> str:
    """
    Enrich the raw user message with prediction-context keywords (and, for
    very short follow-ups, the prior user turn) before embedding it.

    Follow-up questions like "what should I do next?" or "what does this
    mean?" carry almost no retrievable vocabulary on their own — the actual
    topic lives in the upstream CNN prediction (e.g. predicted_class,
    gradcam_region) and/or the previous turn. Folding those signals into the
    *retrieval* query (never into what gets shown to the user, and never
    into the LLM's factual claims) keeps follow-ups grounded without
    weakening the citation/verification guarantees, which still only trust
    what the vector store actually returns.
    """
    parts = [state["sanitized_message"]]

    prediction_context = state.get("prediction_context")
    if prediction_context:
        parts.extend(str(v) for v in prediction_context.values())

    if len(state["sanitized_message"].split()) <= 6:
        history = state.get("history", [])
        prior_user_turns = [t["content"] for t in history if t["role"] == "user"]
        if prior_user_turns:
            parts.append(prior_user_turns[-1])

    return " ".join(parts)


def make_retrieve_node(embedder: EmbedderProtocol, vector_store: VectorStore, top_k: int):
    def retrieve(state: AgentState) -> dict:
        query = _build_retrieval_query(state)
        query_vec = embedder.encode([query])
        results = vector_store.search(query_vec[0], top_k=top_k)
        retrieved = [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "title": r.title,
                "organization": r.organization,
                "topic": r.topic,
                "source_url": r.source_url,
                "section_heading": r.section_heading,
                "text": r.text,
                "score": r.score,
            }
            for r in results
        ]
        return {"retrieval_query": query, "retrieved_chunks": retrieved, "route": "grade_retrieval"}

    return retrieve


def make_grade_retrieval_node(score_floor: float, min_supporting_chunks: int):
    def grade_retrieval(state: AgentState) -> dict:
        chunks = state.get("retrieved_chunks", [])
        strong_chunks = [c for c in chunks if c["score"] >= score_floor]
        sufficient = len(strong_chunks) >= min_supporting_chunks
        return {
            "retrieval_sufficient": sufficient,
            "route": "generate" if sufficient else "refuse_insufficient_evidence",
        }

    return grade_retrieval


def make_generate_node(llm_client: LLMClientProtocol, memory: ConversationMemory):
    def generate(state: AgentState) -> dict:
        session_history = state.get("history", [])
        history_text = "\n".join(
            f"{'Patient/User' if t['role'] == 'user' else 'Assistant'}: {t['content']}"
            for t in session_history
        )

        user_prompt = prompts.build_user_turn_prompt(
            user_message=state["sanitized_message"],
            retrieved_chunks=state.get("retrieved_chunks", []),
            prediction_context=state.get("prediction_context"),
            conversation_history=history_text,
        )

        attempts = state.get("regeneration_attempts", 0)
        if attempts > 0 and state.get("verification_notes"):
            user_prompt += prompts.REGENERATION_INSTRUCTION_SUFFIX.format(
                notes="; ".join(state["verification_notes"])
            )

        raw_output = llm_client.chat(prompts.SYSTEM_PROMPT, user_prompt)
        return {"raw_llm_output": raw_output, "regeneration_attempts": attempts + 1, "route": "verify"}

    return generate


def make_verify_node(require_citations: bool):
    def verify(state: AgentState) -> dict:
        retrieved_ids = [c["chunk_id"] for c in state.get("retrieved_chunks", [])]
        passed, notes = verify_output(
            state["raw_llm_output"], retrieved_ids, require_citations=require_citations
        )

        if passed:
            return {
                "verification_passed": True,
                "verification_notes": notes,
                "answer": parse_structured_answer(state["raw_llm_output"]),
                "route": "done",
            }

        attempts = state.get("regeneration_attempts", 0)
        if attempts <= MAX_REGENERATION_ATTEMPTS:
            return {
                "verification_passed": False,
                "verification_notes": notes,
                "route": "generate",
            }

        # Exhausted retries -> fail safe rather than return an unverified answer.
        return {
            "verification_passed": False,
            "verification_notes": notes,
            "route": "refuse_insufficient_evidence",
        }

    return verify


def make_respond_node(memory: ConversationMemory):
    def respond(state: AgentState) -> dict:
        return {"route": "done"}

    return respond
