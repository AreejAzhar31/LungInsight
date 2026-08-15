from agent.nodes import parse_structured_answer
from agent.prompts import build_context_block
from tests.conftest import FakeLLMClient


def test_parse_structured_answer_extracts_all_sections():
    raw = (
        "Plain-language explanation: Simple summary here. [cite:doc-1::chunk-0]\n"
        "Clinical explanation: Technical detail here. [cite:doc-1::chunk-0]\n"
        "Recommended next steps: See a specialist.\n"
        "Sources:\n- doc-1::chunk-0\n"
        "Confidence & disclaimer: This is not medical advice. Consult a clinician."
    )
    parsed = parse_structured_answer(raw)

    assert "Simple summary here" in parsed["plain_language_explanation"]
    assert "Technical detail here" in parsed["clinical_explanation"]
    assert "specialist" in parsed["recommended_next_steps"]
    assert "doc-1::chunk-0" in parsed["sources"]
    assert "not medical advice" in parsed["confidence_disclaimer"]
    assert parsed["citations"] == ["doc-1::chunk-0"]


def test_parse_structured_answer_dedupes_and_sorts_citations():
    raw = (
        "Plain-language explanation: A. [cite:doc-2::chunk-1] [cite:doc-1::chunk-0] [cite:doc-1::chunk-0]\n"
        "Confidence & disclaimer: Not medical advice."
    )
    parsed = parse_structured_answer(raw)
    assert parsed["citations"] == ["doc-1::chunk-0", "doc-2::chunk-1"]


def test_context_block_includes_chunk_ids_llm_can_cite(populated_vector_store, fake_embedder):
    query_vec = fake_embedder.encode(["lung cancer risk factors smoking"])[0]
    results = populated_vector_store.search(query_vec, top_k=3)
    chunks_as_dicts = [
        {
            "chunk_id": r.chunk_id,
            "title": r.title,
            "organization": r.organization,
            "section_heading": r.section_heading,
            "source_url": r.source_url,
            "score": r.score,
            "text": r.text,
        }
        for r in results
    ]
    block = build_context_block(chunks_as_dicts)
    for r in results:
        assert f"ID: {r.chunk_id}" in block
        assert r.organization in block


def test_citations_in_generated_answer_map_to_correct_organizations(populated_vector_store, fake_embedder):
    """
    End-to-end citation accuracy check: every chunk_id the (fake) LLM cites
    must resolve back to a real chunk with a real, attributable organization
    — this is what prevents a user-facing answer from citing a source that
    doesn't actually exist or doesn't actually say what's claimed.
    """
    query_vec = fake_embedder.encode(["screening low dose CT nodule follow-up"])[0]
    results = populated_vector_store.search(query_vec, top_k=3)
    chunks_as_dicts = [
        {
            "chunk_id": r.chunk_id,
            "title": r.title,
            "organization": r.organization,
            "section_heading": r.section_heading,
            "source_url": r.source_url,
            "score": r.score,
            "text": r.text,
        }
        for r in results
    ]

    from agent.prompts import build_user_turn_prompt, SYSTEM_PROMPT

    llm = FakeLLMClient(mode="good")
    prompt = build_user_turn_prompt(
        user_message="What does screening involve?",
        retrieved_chunks=chunks_as_dicts,
        prediction_context=None,
        conversation_history="",
    )
    raw_output = llm.chat(SYSTEM_PROMPT, prompt)
    parsed = parse_structured_answer(raw_output)

    chunk_lookup = {c["chunk_id"]: c for c in chunks_as_dicts}
    for cited_id in parsed["citations"]:
        assert cited_id in chunk_lookup, f"Citation {cited_id} does not map to any retrieved chunk"
        org = chunk_lookup[cited_id]["organization"]
        assert org in {
            "World Health Organization (WHO)",
            "Centers for Disease Control and Prevention (CDC)",
            "National Institutes of Health (NIH) / National Cancer Institute",
        }
