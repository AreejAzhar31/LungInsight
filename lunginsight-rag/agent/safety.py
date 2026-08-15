"""
Prompt safety layer.

Implements the four safety requirements from the spec:

1. Hallucination reduction  -> `verify_output` checks that every citation in
   the answer maps to a chunk_id that was actually retrieved, and flags
   answers with citation-free body claims when `require_citations=True`.
2. Prompt injection protection -> `check_input_safety` screens the raw user
   message for known injection patterns ("ignore previous instructions",
   role-override attempts, attempts to exfiltrate the system prompt, etc.)
   before it ever reaches retrieval or the LLM.
3. Source verification -> `verify_output` cross-checks cited organizations /
   document_ids against the retrieved chunk set (see hallucination reduction);
   nothing is trusted just because the model said it.
4. Retrieval-first responses -> enforced architecturally in `agent/graph.py`:
   the generation node's prompt template (see `agent/prompts.py`) only ever
   includes retrieved context, and the system prompt explicitly forbids
   answering from parametric knowledge when retrieval is empty/weak.

None of this is a replacement for a dedicated moderation model in a real
production deployment — it is a fast, transparent, first line of defense that
is easy to unit test and reason about.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- Prompt injection heuristics -----------------------------------------
# Patterns that indicate an attempt to override system instructions, escape
# the assistant's role, or exfiltrate hidden prompts/config. Case-insensitive.
_INJECTION_PATTERNS = [
    r"ignore\s+(?:\w+\s+){0,3}(instructions|prompt|rules)",
    r"disregard\s+(?:\w+\s+){0,3}(instructions|prompt|rules)",
    r"forget\s+(?:\w+\s+){0,3}(instructions|prompt|rules)",
    r"you are now\b",
    r"act as if you (are|were)\b",
    r"system prompt",
    r"reveal (your|the) (system|hidden|internal) (prompt|instructions)",
    r"print (your|the) (instructions|prompt)",
    r"pretend (you are|to be)",
    r"jailbreak",
    r"dan mode",
    r"developer mode",
    r"do anything now",
    r"override (safety|guardrails|restrictions)",
    r"bypass (safety|guardrails|restrictions|filters)",
    r"\bsudo\b",
    r"repeat (the words|everything) (above|before)",
    r"what (is|are) your (instructions|system prompt)",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# Requests that ask the assistant to act outside its clinical-information
# scope in ways that are unsafe regardless of retrieval (e.g. prescribing
# specific drug dosages, definitive diagnosis, replacing emergency care).
_UNSAFE_SCOPE_PATTERNS = [
    r"exact (dose|dosage) of \w+ (for|to) (me|myself)",
    r"tell me (definitively|for certain|100%) (that )?i have (pneumonia|cancer|lung cancer)",
    r"skip (seeing|going to|visiting) (a|the) doctor",
    r"instead of (calling|going to) (911|emergency|the er|the hospital)",
]
_UNSAFE_SCOPE_RE = re.compile("|".join(_UNSAFE_SCOPE_PATTERNS), re.IGNORECASE)


@dataclass
class InputSafetyResult:
    is_safe: bool
    reason: str | None
    sanitized_message: str
    flags: list[str] = field(default_factory=list)


def _strip_control_and_hidden_chars(text: str) -> str:
    # Remove non-printable / zero-width characters sometimes used to hide
    # injected instructions from human review while an LLM still parses them.
    return re.sub(r"[\u200b-\u200f\u202a-\u202e\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


def check_input_safety(user_message: str, max_chars: int = 4000) -> InputSafetyResult:
    """Screen a raw user message before it reaches retrieval or the LLM."""
    flags: list[str] = []

    if not user_message or not user_message.strip():
        return InputSafetyResult(False, "empty_message", "", ["empty_message"])

    if len(user_message) > max_chars:
        flags.append("message_too_long")
        user_message = user_message[:max_chars]

    cleaned = _strip_control_and_hidden_chars(user_message).strip()

    if _INJECTION_RE.search(cleaned):
        flags.append("prompt_injection_pattern")
        return InputSafetyResult(False, "prompt_injection_detected", cleaned, flags)

    if _UNSAFE_SCOPE_RE.search(cleaned):
        flags.append("unsafe_scope_request")
        return InputSafetyResult(False, "unsafe_scope_request", cleaned, flags)

    is_safe = True
    reason = None if not flags else ",".join(flags)
    return InputSafetyResult(is_safe, reason, cleaned, flags)


# --- Output verification --------------------------------------------------

_CITATION_TAG_RE = re.compile(r"\[cite:([a-zA-Z0-9_\-]+::chunk-\d+)\]")


def extract_cited_chunk_ids(answer_text: str) -> list[str]:
    return _CITATION_TAG_RE.findall(answer_text)


def verify_output(
    answer_text: str,
    retrieved_chunk_ids: list[str],
    require_citations: bool = True,
) -> tuple[bool, list[str]]:
    """
    Validate a generated answer against what was actually retrieved.

    Returns (passed, notes). `passed=False` should trigger either a single
    bounded regeneration attempt or a graceful refusal — never a silent
    pass-through of an unverified answer.
    """
    notes: list[str] = []
    passed = True

    cited_ids = extract_cited_chunk_ids(answer_text)

    if require_citations and not cited_ids:
        passed = False
        notes.append("no_citations_found")

    fabricated = [cid for cid in cited_ids if cid not in retrieved_chunk_ids]
    if fabricated:
        passed = False
        notes.append(f"fabricated_citation_ids:{','.join(fabricated)}")

    # A confidence / disclaimer statement must be present for medical content.
    disclaimer_markers = ("not a diagnosis", "not medical advice", "consult", "clinician", "healthcare provider")
    if not any(marker in answer_text.lower() for marker in disclaimer_markers):
        passed = False
        notes.append("missing_confidence_disclaimer")

    return passed, notes
