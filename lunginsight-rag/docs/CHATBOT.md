# CHATBOT.md — LungInsight AI Conversational Agent

## 1. Scope

This document covers the **LangGraph conversational agent** built on top of
the retrieval pipeline described in `RAG.md`. It explains the state machine,
conversation memory, and how prediction data from the (external) CNN/Grad-CAM
model flows into an explanation. Prompt text/rationale lives in `PROMPTS.md`.

## 2. Where This Fits

```
             ┌──────────────────────────┐
  (external) │   CNN + Grad-CAM model    │   <- NOT part of this repo
             └────────────┬─────────────┘
                           │ prediction_context (dict)
                           ▼
             ┌──────────────────────────┐
             │  LungInsightRAGService    │   service.py
             │   .chat(session_id,       │
             │         message,          │
             │         prediction_context)│
             └────────────┬─────────────┘
                           │
                           ▼
             ┌──────────────────────────┐
             │      LangGraph agent      │   agent/graph.py
             └──────────────────────────┘
```

`prediction_context` is an arbitrary dict — e.g.
`{"predicted_class": "suspicious_nodule", "confidence": 0.81,
"gradcam_region": "right upper lobe"}`. It is passed into the prompt as
context (see `PROMPTS.md` §3) but is **explicitly labeled as unverified
model output**, never treated as ground truth the LLM can assert on its own
authority — every factual claim in the answer must still come from a
retrieved, citeable chunk.

## 3. Graph / State Machine

Defined in `agent/graph.py` + `agent/nodes.py`, over the state schema in
`agent/state.py`.

```
        ┌────────────┐
        │input_guard │  prompt-injection / unsafe-scope screen, sanitization
        └─────┬──────┘
       safe    │    unsafe
     ┌─────────┴─────────┐
     ▼                    ▼
┌─────────┐        ┌──────────────┐
│ retrieve│         │ refuse_unsafe│──► END
└────┬────┘         └──────────────┘
     ▼
┌────────────────┐
│grade_retrieval  │  score_floor + min_supporting_chunks check
└────────┬────────┘
sufficient│   insufficient
   ┌──────┴──────────────────┐
   ▼                          ▼
┌─────────┐         ┌──────────────────────────────┐
│generate │         │refuse_insufficient_evidence   │──► END
└────┬────┘         └──────────────────────────────┘
     ▼
┌─────────┐   fail (bounded retry)
│ verify  │───────────────┐
└────┬────┘               │
 pass │                    ▼
     ▼              back to generate (max 1 retry)
┌─────────┐                │
│ respond │◄── pass after retry
└────┬────┘         exhausted retries
     ▼                    │
    END  ◄─────────────────┘ (routes to refuse_insufficient_evidence)
```

Every node is a pure function `(state) -> partial_state_update`, matching
LangGraph's contract. If `langgraph` isn't installed, `agent/graph.py`
transparently falls back to `_FallbackGraphRunner`, a dependency-free
executor with **identical routing logic** — this is what the offline test
suite runs against, and it's why the same test file exercises real
production routing code either way.

### Nodes

| Node | Responsibility |
|---|---|
| `input_guard` | Runs `agent/safety.py::check_input_safety` — prompt-injection patterns, unsafe-scope requests, control-character stripping, length capping. Routes to `refuse_unsafe` on failure. |
| `retrieve` | Embeds an enriched query (see `RAG.md` §7) and calls `VectorStore.search()`. |
| `grade_retrieval` | Applies `SIMILARITY_SCORE_FLOOR` / `MIN_SUPPORTING_CHUNKS`. Routes to `refuse_insufficient_evidence` if the retrieved chunks aren't strong enough to ground an answer. |
| `generate` | Builds the full prompt (system + retrieved context + prediction context + conversation history + question) and calls the Groq client. |
| `verify` | Runs `agent/safety.py::verify_output` — checks every `[cite:chunk_id]` tag resolves to an actually-retrieved chunk, that at least one citation exists, and that a confidence/disclaimer statement is present. Routes back to `generate` once (bounded retry) on failure, then to `refuse_insufficient_evidence` if still failing. |
| `respond` | Terminal no-op hook (kept as an explicit node so response-side side effects — e.g. logging/metrics — have a single place to live later). |

## 4. Structured Answer Format

A successful turn's `answer` dict (see `agent/nodes.py::parse_structured_answer`)
always has these keys, matching the four-section + disclaimer structure the
system prompt requires:

```python
{
  "plain_language_explanation": "...",   # 8th-grade reading level
  "clinical_explanation": "...",         # more technical detail
  "recommended_next_steps": "...",       # general, never a specific Rx
  "sources": "...",                      # bulleted org + title list
  "confidence_disclaimer": "...",        # always present, always says "not a diagnosis"
  "citations": ["doc-id::chunk-3", ...], # de-duplicated, sorted chunk IDs actually cited
  "raw_text": "...",                     # full raw model output, for audit/debug
}
```

A refused turn has the same shape but with `"refused": True` and
`"refusal_reason"` set to one of: `prompt_injection_detected`,
`unsafe_scope_request`, `empty_message`, or `insufficient_evidence`.

## 5. Conversation Memory

`agent/memory.py::ConversationMemory` — an in-process, session-keyed store.
Swappable for Redis/a database later without touching graph nodes, since
nodes only ever see `state["history"]` (a plain list of `{"role", "content"}`
dicts) that `service.py` fills in from memory before invoking the graph.

- **Bounded**: `MAX_TURNS_IN_MEMORY` (default 8) caps both prompt size/cost
  and the chance the LLM drifts toward "recall what we discussed" instead of
  staying retrieval-grounded on the *current* question.
- **Prediction-context stickiness**: `set_prediction_context()` /
  `get_prediction_context()` let a session remember the most recent upstream
  CNN prediction so follow-ups don't need to resend it every turn (see
  `RAG.md` §7 for how this also feeds retrieval-query enrichment).
- **Turn logging is refusal-inclusive**: `service.py::chat()` logs both
  sides of the turn regardless of whether the graph refused, so a repeated
  unsafe/off-topic query doesn't silently vanish from a transcript a
  clinician or auditor might review later.

## 6. Multi-Turn / Follow-Up Support

Handled at two layers:

1. **Memory** (§5) — prior turns are rendered into the prompt as a compact
   transcript (`ConversationMemory.format_history_for_prompt`, or the raw
   `history` list passed straight through the graph state — both paths end
   up in the same "CONVERSATION HISTORY" block the system prompt sees).
2. **Retrieval-query enrichment** (`RAG.md` §7) — short follow-ups pull in
   the stored prediction context and/or the previous user turn so retrieval
   doesn't go in blind on a 4-word question.

The verification step (§3) still applies identically to every turn — a
follow-up doesn't get a weaker citation bar just because it's conversational.

## 7. Refusal Behavior (evidence-insufficiency)

Retrieval always returns its top-k nearest neighbors from a non-empty index
— there's no natural "zero results" signal. Insufficiency is therefore
defined by `grade_retrieval`'s score floor, not an empty list. When it fires
(or when `verify` exhausts its retry budget), the user gets
`agent.prompts.REFUSAL_INSUFFICIENT_EVIDENCE` — a plain statement that the
knowledge base doesn't cover the question confidently, with a suggestion to
rephrase or consult a clinician, never a best-effort guess.

## 8. Running It

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY
python -m ingestion.ingest_pipeline   # build the index once
python cli.py                          # interactive REPL
```

Programmatic usage (this is the shape an upstream API layer would call):

```python
from service import LungInsightRAGService

rag = LungInsightRAGService()
rag.ensure_index_built()

result = rag.chat(
    session_id="user-123",
    message="What does this finding mean?",
    prediction_context={
        "predicted_class": "suspicious_nodule",
        "confidence": 0.81,
        "gradcam_region": "right upper lobe",
    },
)
print(result["answer"]["plain_language_explanation"])
print(result["answer"]["citations"])
```

## 9. Testing

`tests/test_chat_flow.py` exercises the full graph (via the fallback runner,
since `langgraph` may not be installed in every environment) end-to-end using
`FakeEmbedder` + `FakeLLMClient`:

- unsafe input never reaches the LLM at all (`test_prompt_injection_short_circuits_before_retrieval`)
- off-topic input never reaches the LLM either, since it's graded out after retrieval (`test_irrelevant_query_is_refused_with_insufficient_evidence`)
- a well-grounded query produces a fully structured, citation-complete answer whose citations are a subset of what was actually retrieved
- an LLM response missing citations triggers exactly one bounded regeneration attempt, then fails safe rather than returning an unverified answer
- an LLM response citing a fabricated chunk ID is caught and never returned to the user
- session memory and prediction-context stickiness both persist correctly across turns, including into the enriched retrieval query for short follow-ups

Run with:

```bash
pytest tests/test_chat_flow.py -v
```
