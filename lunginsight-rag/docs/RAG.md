# RAG.md — LungInsight AI Retrieval-Augmented Generation Pipeline

## 1. Scope

This document covers the **document ingestion + retrieval pipeline** only.
For the conversational agent built on top of it, see `CHATBOT.md`. For exact
prompt text and rationale, see `PROMPTS.md`.

This service does **not** include: frontend, backend authentication, the
CNN classifier, or Grad-CAM. It assumes an upstream API will call
`LungInsightRAGService.chat(..., prediction_context={...})` with prediction
output already computed.

## 2. Pipeline Overview

```
Documents (knowledge_base/raw/*.md)
        │
        ▼
   Loader (ingestion/loader.py)
        │   parses frontmatter metadata (org, title, topic, source_url, ...)
        ▼
   Chunker (ingestion/chunker.py)
        │   heading-aware, sliding-window, token-bounded
        ▼
   Embedder (ingestion/embedder.py)
        │   sentence-transformers/all-MiniLM-L6-v2 (384-dim, cosine/normalized)
        ▼
   Vector Store (ingestion/vector_store.py)
        │   FAISS (IndexFlatIP) or ChromaDB
        ▼
   Persisted index (storage/vector_index/)
```

Run it with:

```bash
python -m ingestion.ingest_pipeline
```

This is idempotent and safe to re-run whenever `knowledge_base/raw/` changes
— it rebuilds the full index from scratch (no incremental upsert logic is
included, since the reference corpus is small and rebuilding is fast; add
incremental ingestion before this corpus grows beyond a few hundred
documents).

## 3. Knowledge Base

`knowledge_base/raw/*.md` holds trusted clinical guidance documents, one file
per source topic, each with a small frontmatter header:

```markdown
---
title: Lung Cancer Risk Factors
organization: Centers for Disease Control and Prevention (CDC)
topic: risk_factors
license: ...
source_url: https://www.cdc.gov/cancer/lung/
retrieved_date: 2026-01-15
document_id: cdc-lung-riskfactors-001
---
# Lung Cancer Risk Factors
...
```

`knowledge_base/sources.json` is a machine-readable manifest of the same
metadata, useful for a provenance/audit view outside the chat flow.

**Important — replace before production use:** the five seed documents
shipped in `knowledge_base/raw/` are original text *paraphrased* from public
WHO/CDC/NIH guidance for demonstration and testing purposes. They are not a
verbatim, licensed copy of any publisher's text. Before deploying this
service against real users, replace their contents with either (a) properly
licensed/verified excerpts from the source organizations, or (b) short
original summaries that link out to the canonical `source_url` for full text,
confirmed against your organization's legal/compliance review.

Adding a new source is:
1. Drop a new `.md` file into `knowledge_base/raw/` with the same
   frontmatter shape.
2. Add an entry to `knowledge_base/sources.json` (optional but recommended
   for audit trails).
3. Re-run `python -m ingestion.ingest_pipeline`.

## 4. Chunking Strategy

Implemented in `ingestion/chunker.py`. Two-stage:

1. **Heading split** — the document is split on Markdown headings first, so a
   chunk never blends unrelated sections (e.g., "Risk Factors" text bleeding
   into "Treatment" text). This matters a lot for citation precision: a user
   asking about screening should never get a chunk whose top-ranked content
   is actually about treatment just because a sliding window crossed a
   section boundary.
2. **Sliding window within a section** — each section is windowed at
   `chunk_size_tokens` (default 220, ~ the useful input range for
   all-MiniLM-L6-v2 without truncation) with `chunk_overlap_tokens` (default
   40) of overlap, so a fact stated near a chunk boundary is not silently
   split across two low-scoring half-chunks.

Every chunk carries its parent document's `document_id`, `title`,
`organization`, `topic`, `source_url`, and its own `section_heading` and a
generated `chunk_id` of the form `{document_id}::chunk-{n}` — this exact
format is what the generation prompt asks the LLM to cite (see
`agent/safety.py::extract_cited_chunk_ids`), so citations can always be
resolved back to a specific section of a specific trusted source.

Tuning knobs (env vars, see `.env.example`): `CHUNK_SIZE_TOKENS`,
`CHUNK_OVERLAP_TOKENS`.

## 5. Embeddings

`ingestion/embedder.py` wraps `sentence-transformers/all-MiniLM-L6-v2`
(384-dim). Vectors are L2-normalized at encode time so cosine similarity
reduces to a plain dot product — this lets the FAISS backend use the cheaper
`IndexFlatIP` (inner product) index type instead of needing a separate cosine
index type.

The model loads lazily on first `.encode()` call (not at import time), so
importing the package never triggers a network call or slow model download —
useful for fast unit tests that don't need real embeddings (see §8).

## 6. Vector Store

`ingestion/vector_store.py` provides a single `VectorStore` facade over two
selectable backends:

| Backend | Selected via | Notes |
|---|---|---|
| **FAISS** (default) | `VECTOR_STORE_BACKEND=faiss` | `IndexFlatIP`, exact brute-force cosine search. Fine for a corpus of this size (hundreds–low thousands of chunks); swap to an ANN index type if the corpus grows into the millions. |
| **ChromaDB** | `VECTOR_STORE_BACKEND=chroma` | Persistent collection with `hnsw:space=cosine`. Useful if you want built-in persistence/metadata filtering without managing your own pickle files. |

A third, dependency-free `numpy` fallback backend is used automatically if
neither `faiss` nor `chromadb` is importable — this is what allows the test
suite (`tests/test_retrieval.py`) to run in restricted/offline environments
without the compiled FAISS wheel. It implements the identical brute-force
cosine math as `IndexFlatIP`, so retrieval *quality* is not degraded, only
scale — do not rely on it for a large production corpus.

`VectorStore.persist(path)` / `.load(path)` handle serialization: the FAISS
index binary (or numpy `.npy` fallback) plus a pickled list of `Chunk`
metadata objects, so a restarted process can load a pre-built index instead
of re-embedding the whole corpus on every startup (`service.py` does this
automatically via `ensure_index_built()`).

### Retrieval parameters (`config.py` / `.env.example`)

- `RETRIEVAL_TOP_K` (default 5) — how many chunks come back per query.
- `SIMILARITY_SCORE_FLOOR` (default 0.35) — minimum cosine score for a chunk
  to count as "supporting evidence" (see `agent/nodes.py::make_grade_retrieval_node`).
- `MIN_SUPPORTING_CHUNKS` (default 1) — how many chunks must clear that floor
  before the agent is allowed to generate an answer at all. Below this, the
  conversational graph routes straight to a refusal (see `CHATBOT.md` §3).

These two settings are the main lever for the "refusal when evidence is
insufficient" requirement: retrieval always returns its top-k nearest
neighbors (there's no such thing as "no results" in a non-empty index), so
insufficiency is defined by a **score floor**, not an empty result set.

## 7. Retrieval-Query Enrichment for Follow-Ups

Short follow-ups like *"what should I do next?"* or *"what does this mean?"*
carry almost no retrievable vocabulary on their own. `agent/nodes.py::_build_retrieval_query`
enriches the embedded query (never the user-visible text, and never a fact
source for the LLM) with:

- the current turn's `prediction_context` values (e.g. `predicted_class`,
  `gradcam_region`) if the upstream API supplied one this turn or in a prior
  turn this session, and
- the previous user turn's text, only when the current message is very short
  (≤ 6 words).

This keeps multi-turn "what does *that* mean" conversations grounded in the
right section of the knowledge base without weakening the citation/
verification guarantees downstream — those still only trust whatever the
vector store actually returned for *this* enriched query, never anything
outside it.

## 8. Testing

See `tests/` for the full suite (`test_chunker.py`, `test_embeddings.py`,
`test_retrieval.py`, `test_safety.py`, `test_citations.py`,
`test_chat_flow.py`) and `tests/conftest.py` for fixtures.

**Why fakes, and what they do/don't prove:** `sentence-transformers` and Groq
both require network access (model weights / API calls). `tests/conftest.py`
provides:

- `FakeEmbedder`: a deterministic hashed bag-of-words embedder. It has *no*
  semantic understanding, but cosine similarity between its vectors tracks
  lexical word overlap closely — enough to validate the retrieval **plumbing**
  end-to-end (chunking → embedding → indexing → search → ranking →
  citation-ability) against the *real* knowledge base documents, and to
  assert things like "a risk-factor query's top result is a risk-factor
  chunk, not a treatment chunk." It is **not** a substitute for evaluating
  the real MiniLM model's semantic retrieval quality (e.g., synonym
  understanding, paraphrase matching) — run the eval below with the real
  model before trusting retrieval quality in production.
- `FakeLLMClient`: synthesizes rules-following (and deliberately
  rule-breaking) structured answers referencing only chunk IDs actually
  present in its prompt, so citation-verification logic is tested against
  real parsing code, not a hand-typed string.

Run the suite with the real stack once dependencies are installed:

```bash
pip install -r requirements.txt
export GROQ_API_KEY=...
pytest -v
```

### Manual real-model retrieval quality check

Once `sentence-transformers` is installed (no API key needed — embeddings
run locally):

```python
from ingestion.embedder import Embedder
from ingestion.ingest_pipeline import build_index

store = build_index()  # uses the real Embedder by default
embedder = Embedder()

for query in [
    "what raises my chance of getting lung cancer",
    "when should I get a CT scan for lung cancer",
    "I've been coughing up blood, what could that mean",
]:
    vec = embedder.encode([query])[0]
    for r in store.search(vec, top_k=3):
        print(f"{r.score:.3f}  {r.organization} — {r.title} — {r.section_heading}")
```

Inspect that top results are topically correct and scores clear
`SIMILARITY_SCORE_FLOOR` for genuinely answerable questions, and fall below
it for genuinely off-topic ones (repeat the pizza-question style check from
`test_retrieval.py`).

## 9. Known Limitations / Next Steps

- No incremental re-ingestion (full rebuild only) — fine at this corpus size.
- No re-ranking stage (e.g., cross-encoder) after the initial vector search —
  would improve precision if the corpus grows and top-k=5 starts returning
  more borderline results.
- Seed knowledge base content needs a real licensing/compliance pass before
  production (see §3).
- `numpy` fallback vector backend is for offline/dev use only — always
  install `faiss-cpu` or `chromadb` for production so retrieval matches the
  documented backend's persistence semantics.
