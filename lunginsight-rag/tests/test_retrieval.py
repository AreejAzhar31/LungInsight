def test_store_contains_all_real_chunks(populated_vector_store, real_chunks):
    assert len(populated_vector_store) == len(real_chunks)


def test_risk_factor_query_retrieves_risk_factor_content(populated_vector_store, fake_embedder):
    query_vec = fake_embedder.encode(["what are the risk factors for lung cancer smoking radon asbestos"])[0]
    results = populated_vector_store.search(query_vec, top_k=3)

    assert len(results) > 0
    top_orgs_topics = [(r.organization, r.topic) for r in results]
    assert any(topic == "risk_factors" for _, topic in top_orgs_topics)


def test_screening_query_retrieves_screening_content(populated_vector_store, fake_embedder):
    query_vec = fake_embedder.encode(["low dose CT screening pack years nodule Lung-RADS"])[0]
    results = populated_vector_store.search(query_vec, top_k=3)

    assert any(r.topic == "screening" for r in results)


def test_symptom_query_retrieves_symptom_content(populated_vector_store, fake_embedder):
    query_vec = fake_embedder.encode(["persistent cough coughing up blood chest pain symptoms"])[0]
    results = populated_vector_store.search(query_vec, top_k=3)

    assert any(r.topic == "symptoms_diagnosis" for r in results)


def test_treatment_query_retrieves_treatment_content(populated_vector_store, fake_embedder):
    query_vec = fake_embedder.encode(["chemotherapy radiation surgery targeted therapy immunotherapy"])[0]
    results = populated_vector_store.search(query_vec, top_k=3)

    assert any(r.topic == "treatment" for r in results)


def test_results_are_ranked_by_descending_score(populated_vector_store, fake_embedder):
    query_vec = fake_embedder.encode(["lung cancer screening"])[0]
    results = populated_vector_store.search(query_vec, top_k=5)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_irrelevant_query_returns_low_scores(populated_vector_store, fake_embedder):
    query_vec = fake_embedder.encode(["best pizza toppings recipe italian cuisine"])[0]
    results = populated_vector_store.search(query_vec, top_k=3)
    # Nothing in the KB should look highly relevant to a pizza query.
    assert all(r.score < 0.35 for r in results)


def test_every_result_is_citeable(populated_vector_store, fake_embedder):
    query_vec = fake_embedder.encode(["lung cancer overview"])[0]
    results = populated_vector_store.search(query_vec, top_k=3)
    for r in results:
        assert r.organization
        assert r.title
        assert r.chunk_id
