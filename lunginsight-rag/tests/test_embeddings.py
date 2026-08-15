import numpy as np


def test_embeddings_are_l2_normalized(fake_embedder):
    vectors = fake_embedder.encode(["lung cancer risk factors", "unrelated text about weather"])
    norms = np.linalg.norm(vectors, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-5)


def test_embeddings_correct_shape(fake_embedder):
    vectors = fake_embedder.encode(["a", "b", "c"])
    assert vectors.shape == (3, fake_embedder.dim)


def test_empty_input_returns_empty_array(fake_embedder):
    vectors = fake_embedder.encode([])
    assert vectors.shape == (0, fake_embedder.dim)


def test_similar_texts_score_higher_than_dissimilar(fake_embedder):
    query = fake_embedder.encode(["lung cancer smoking risk factor"])[0]
    similar = fake_embedder.encode(["smoking is a major lung cancer risk factor"])[0]
    dissimilar = fake_embedder.encode(["weather forecast rain tomorrow afternoon"])[0]

    sim_similar = float(query @ similar)
    sim_dissimilar = float(query @ dissimilar)

    assert sim_similar > sim_dissimilar


def test_embedding_is_deterministic(fake_embedder):
    v1 = fake_embedder.encode(["radon gas exposure"])[0]
    v2 = fake_embedder.encode(["radon gas exposure"])[0]
    np.testing.assert_array_equal(v1, v2)
