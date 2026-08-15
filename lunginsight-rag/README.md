# LungInsight AI — RAG Clinical Knowledge Base & Conversational AI

A standalone Retrieval-Augmented Generation service that explains lung
imaging AI predictions and answers follow-up questions using a trusted
clinical knowledge base (WHO / CDC / NIH-style guidance).

**This repo is only the intelligent assistant.** It deliberately contains no
frontend, no backend authentication, no CNN model, and no Grad-CAM
implementation. It is designed to be called by an upstream API layer that
already has prediction data, via:

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
```

## Documentation

- **[docs/RAG.md](docs/RAG.md)** — ingestion pipeline: documents → chunking → embeddings → vector DB
- **[docs/CHATBOT.md](docs/CHATBOT.md)** — LangGraph conversational agent, memory, multi-turn flow
- **[docs/PROMPTS.md](docs/PROMPTS.md)** — exact prompts and the reasoning behind each one

## Stack

- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Vector store**: FAISS (default) or ChromaDB, selectable via env var
- **LLM**: Groq API
- **Agent orchestration**: LangGraph

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in GROQ_API_KEY

python -m ingestion.ingest_pipeline    # build the vector index once
python cli.py                           # interactive REPL to try it out
```

Run the test suite:

```bash
pytest -v
```

## Project Layout

```
config.py                    # all tunable settings, env-var driven
service.py                   # LungInsightRAGService — the single entry point
cli.py                       # manual REPL for local testing

knowledge_base/
  raw/*.md                   # trusted source documents (frontmatter + body)
  sources.json                # machine-readable provenance manifest

ingestion/
  loader.py                   # parses documents + metadata
  chunker.py                   # heading-aware sliding-window chunking
  embedder.py                  # sentence-transformers wrapper
  vector_store.py              # FAISS / Chroma / numpy-fallback facade
  ingest_pipeline.py            # orchestrates the full build

agent/
  state.py                     # LangGraph state schema
  nodes.py                     # graph node functions
  graph.py                     # graph assembly (LangGraph or dependency-free fallback)
  prompts.py                   # all prompt templates
  safety.py                    # prompt-injection detection + output verification
  memory.py                    # per-session conversation memory
  llm_client.py                 # Groq API wrapper

tests/                        # pytest suite (fixtures use fakes — no network needed)
docs/                         # RAG.md, CHATBOT.md, PROMPTS.md
```

## Design Highlights

- **Retrieval-first, always verified.** The LLM never answers from
  parametric knowledge alone — every factual claim must carry a
  `[cite:chunk_id]` tag that resolves to an actually-retrieved chunk, checked
  programmatically after generation (`agent/safety.py::verify_output`), with
  one bounded regeneration attempt before failing safe into a refusal.
- **Refuses when evidence is thin.** A similarity score floor
  (`SIMILARITY_SCORE_FLOOR`) gates generation before the LLM is even called —
  off-topic or under-supported questions get a clear "I don't have enough
  verified information" response instead of a guess.
- **Prompt-injection resistant.** Regex-based pre-screening blocks common
  override/exfiltration attempts before they reach retrieval or the LLM,
  backed by an explicit system-prompt rule to ignore instruction-like content
  embedded in history or retrieved text.
- **Fully testable offline.** `tests/conftest.py` provides a deterministic
  fake embedder and fake LLM client so the entire conversational flow —
  chunking, retrieval ranking, citation verification, refusal routing,
  multi-turn memory — is exercised by `pytest` without any network access or
  API keys. Swap in the real `Embedder`/`GroqLLMClient` for production.
- **No frontend/CNN/GradCAM/auth**, by design — `prediction_context` is
  accepted as a plain dict from whatever upstream system produces it.
