from ingestion.chunker import chunk_document, chunk_documents
from ingestion.loader import Document


def make_doc(text: str, **overrides) -> Document:
    defaults = dict(
        document_id="test-doc-001",
        title="Test Document",
        organization="Test Org",
        topic="test",
        source_url="https://example.org/test",
        retrieved_date="2026-01-01",
        text=text,
        file_path="test.md",
    )
    defaults.update(overrides)
    return Document(**defaults)


def test_chunking_respects_size_bound():
    long_body = " ".join(f"word{i}" for i in range(1000))
    doc = make_doc(f"# Section One\n{long_body}")
    chunks = chunk_document(doc, chunk_size_tokens=100, chunk_overlap_tokens=20)

    assert len(chunks) > 1
    for c in chunks:
        # embedding_text includes a short heading prefix, so allow small slack
        assert c.metadata["word_count"] <= 100


def test_chunking_preserves_overlap():
    long_body = " ".join(f"word{i}" for i in range(300))
    doc = make_doc(f"# Section One\n{long_body}")
    chunks = chunk_document(doc, chunk_size_tokens=100, chunk_overlap_tokens=20)

    first_words = chunks[0].metadata["raw_text"].split()
    second_words = chunks[1].metadata["raw_text"].split()
    overlap = set(first_words[-20:]) & set(second_words[:20])
    assert len(overlap) > 0


def test_chunking_is_heading_aware_no_cross_section_bleed():
    text = (
        "# Risk Factors\n"
        + " ".join(f"riskword{i}" for i in range(50))
        + "\n# Treatment\n"
        + " ".join(f"treatword{i}" for i in range(50))
    )
    doc = make_doc(text)
    chunks = chunk_document(doc, chunk_size_tokens=200, chunk_overlap_tokens=20)

    risk_chunks = [c for c in chunks if c.section_heading == "Risk Factors"]
    treat_chunks = [c for c in chunks if c.section_heading == "Treatment"]

    assert len(risk_chunks) == 1
    assert len(treat_chunks) == 1
    assert "treatword" not in risk_chunks[0].metadata["raw_text"]
    assert "riskword" not in treat_chunks[0].metadata["raw_text"]


def test_chunk_metadata_traces_back_to_document():
    doc = make_doc("# Overview\nSome overview content here.", document_id="abc-123")
    chunks = chunk_document(doc)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.document_id == "abc-123"
    assert chunk.organization == "Test Org"
    assert chunk.source_url == "https://example.org/test"
    assert chunk.chunk_id == "abc-123::chunk-0"


def test_chunk_documents_on_real_knowledge_base(real_documents):
    chunks = chunk_documents(real_documents, chunk_size_tokens=220, chunk_overlap_tokens=40)
    assert len(chunks) >= len(real_documents)  # at least one chunk per doc
    # Every chunk must be traceable to a real source document + org.
    orgs = {c.organization for c in chunks}
    assert "World Health Organization (WHO)" in orgs
    assert "Centers for Disease Control and Prevention (CDC)" in orgs
