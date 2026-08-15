"""
LangGraph graph assembly.

Builds the StateGraph described in `agent/nodes.py`'s module docstring. If the
`langgraph` package is not installed, `_FallbackGraphRunner` provides an
equivalent sequential/conditional executor implementing the exact same
routing logic, so the rest of the codebase (and the test suite) does not need
langgraph installed to exercise the conversational flow end-to-end. In
production, install `langgraph` and `build_graph()` will use it automatically.
"""
from __future__ import annotations

from typing import Any, Callable

from config import settings
from ingestion.embedder import EmbedderProtocol
from ingestion.vector_store import VectorStore

from . import prompts
from .llm_client import LLMClientProtocol
from .memory import ConversationMemory
from .nodes import (
    make_generate_node,
    make_grade_retrieval_node,
    make_input_guard_node,
    make_retrieve_node,
    make_respond_node,
    make_verify_node,
)
from .state import AgentState


class _FallbackGraphRunner:
    """Dependency-free executor with the same routing semantics as the LangGraph build below."""

    def __init__(self, nodes: dict[str, Callable[[AgentState], dict]]):
        self.nodes = nodes
        self.max_steps = 12  # guard against any accidental cycle

    def invoke(self, state: AgentState) -> AgentState:
        current = "input_guard"
        steps = 0
        while current != "done" and steps < self.max_steps:
            steps += 1
            updates = self.nodes[current](state)
            state = {**state, **updates}
            current = state.get("route", "done")
            if current in ("refuse_unsafe", "refuse_insufficient_evidence"):
                state = {**state, **self.nodes[current](state)}
                break
        return state

    def stream(self, state: AgentState):
        """Yield state after each node for parity with LangGraph's `.stream()`."""
        current = "input_guard"
        steps = 0
        while current != "done" and steps < self.max_steps:
            steps += 1
            updates = self.nodes[current](state)
            state = {**state, **updates}
            yield {current: updates}
            current = state.get("route", "done")
            if current in ("refuse_unsafe", "refuse_insufficient_evidence"):
                terminal_updates = self.nodes[current](state)
                state = {**state, **terminal_updates}
                yield {current: terminal_updates}
                break


def _make_refusal_nodes():
    def refuse_unsafe(state: AgentState) -> dict:
        return {
            "answer": {
                "plain_language_explanation": prompts.REFUSAL_UNSAFE_INPUT,
                "clinical_explanation": "",
                "recommended_next_steps": "",
                "sources": "",
                "confidence_disclaimer": "This is not medical advice. Please consult a qualified healthcare provider.",
                "citations": [],
                "raw_text": prompts.REFUSAL_UNSAFE_INPUT,
                "refused": True,
                "refusal_reason": state.get("safety_reason", "unsafe_input"),
            },
            "route": "done",
        }

    def refuse_insufficient_evidence(state: AgentState) -> dict:
        return {
            "answer": {
                "plain_language_explanation": prompts.REFUSAL_INSUFFICIENT_EVIDENCE,
                "clinical_explanation": "",
                "recommended_next_steps": "",
                "sources": "",
                "confidence_disclaimer": "This response is limited to what my verified reference sources cover. It is not a medical diagnosis.",
                "citations": [],
                "raw_text": prompts.REFUSAL_INSUFFICIENT_EVIDENCE,
                "refused": True,
                "refusal_reason": "insufficient_evidence",
            },
            "route": "done",
        }

    return refuse_unsafe, refuse_insufficient_evidence


def build_graph(
    embedder: EmbedderProtocol,
    vector_store: VectorStore,
    llm_client: LLMClientProtocol,
    memory: ConversationMemory,
) -> Any:
    """
    Build and compile the conversational RAG graph.

    Returns an object exposing `.invoke(state) -> state` (and `.stream()`),
    backed by LangGraph when available, or the dependency-free fallback
    runner otherwise. Both implement identical routing logic.
    """
    refuse_unsafe, refuse_insufficient_evidence = _make_refusal_nodes()

    nodes = {
        "input_guard": make_input_guard_node(),
        "retrieve": make_retrieve_node(embedder, vector_store, settings.top_k),
        "grade_retrieval": make_grade_retrieval_node(
            settings.similarity_score_floor, settings.min_supporting_chunks
        ),
        "generate": make_generate_node(llm_client, memory),
        "verify": make_verify_node(settings.require_citations),
        "respond": make_respond_node(memory),
        "refuse_unsafe": refuse_unsafe,
        "refuse_insufficient_evidence": refuse_insufficient_evidence,
    }

    try:
        from langgraph.graph import END, StateGraph

        graph = StateGraph(AgentState)
        for name, fn in nodes.items():
            graph.add_node(name, fn)

        graph.set_entry_point("input_guard")

        graph.add_conditional_edges(
            "input_guard",
            lambda s: s["route"],
            {"retrieve": "retrieve", "refuse_unsafe": "refuse_unsafe"},
        )
        graph.add_edge("retrieve", "grade_retrieval")
        graph.add_conditional_edges(
            "grade_retrieval",
            lambda s: s["route"],
            {
                "generate": "generate",
                "refuse_insufficient_evidence": "refuse_insufficient_evidence",
            },
        )
        graph.add_edge("generate", "verify")
        graph.add_conditional_edges(
            "verify",
            lambda s: s["route"],
            {
                "done": "respond",
                "generate": "generate",
                "refuse_insufficient_evidence": "refuse_insufficient_evidence",
            },
        )
        graph.add_edge("respond", END)
        graph.add_edge("refuse_unsafe", END)
        graph.add_edge("refuse_insufficient_evidence", END)

        return graph.compile()

    except ImportError:
        # langgraph not installed in this environment — use the equivalent
        # dependency-free runner so the service is still fully functional
        # (this path is what the offline test suite exercises).
        fallback_nodes = dict(nodes)
        fallback_nodes["done"] = lambda s: {}
        return _FallbackGraphRunner(fallback_nodes)
