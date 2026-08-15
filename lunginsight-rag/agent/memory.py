"""
Conversation memory.

Simple bounded in-process memory keyed by session_id. Swappable for a
Redis/DB-backed store later without touching the graph nodes (they only ever
interact with `ConversationMemory`'s public methods).

We deliberately cap history length (`max_turns`) because:
  - It bounds prompt size / cost sent to Groq.
  - Very old turns are rarely relevant to the current follow-up question, and
    unbounded history increases the chance the LLM drifts from
    retrieval-grounded answers toward "what did we discuss earlier" recall.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .state import ChatTurn


@dataclass
class SessionMemory:
    turns: list[ChatTurn] = field(default_factory=list)
    # Track the most recent prediction context (e.g. CNN model output) so
    # follow-up questions like "what does that mean?" can be resolved without
    # the caller re-sending it every turn.
    last_prediction_context: dict | None = None


class ConversationMemory:
    def __init__(self, max_turns: int = 8):
        self.max_turns = max_turns
        self._sessions: dict[str, SessionMemory] = defaultdict(SessionMemory)

    def get_history(self, session_id: str) -> list[ChatTurn]:
        return list(self._sessions[session_id].turns)

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        session = self._sessions[session_id]
        session.turns.append({"role": role, "content": content})
        # Keep the last `max_turns` turns (each turn = one message).
        if len(session.turns) > self.max_turns:
            session.turns = session.turns[-self.max_turns :]

    def set_prediction_context(self, session_id: str, context: dict) -> None:
        self._sessions[session_id].last_prediction_context = context

    def get_prediction_context(self, session_id: str) -> dict | None:
        return self._sessions[session_id].last_prediction_context

    def clear(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    def format_history_for_prompt(self, session_id: str, max_chars: int = 3000) -> str:
        """Render recent history as a compact transcript for prompt inclusion."""
        turns = self.get_history(session_id)
        lines = []
        for turn in turns:
            speaker = "Patient/User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{speaker}: {turn['content']}")
        transcript = "\n".join(lines)
        if len(transcript) > max_chars:
            transcript = transcript[-max_chars:]
        return transcript
