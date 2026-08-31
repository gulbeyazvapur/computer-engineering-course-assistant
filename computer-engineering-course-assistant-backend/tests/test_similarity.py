import pytest

from app.utils.similarity import cosine_similarity


def test_same_vector_is_one():
    assert cosine_similarity([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_orthogonal_vectors_are_zero():
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_zero_vector_is_safe():
    assert cosine_similarity([0, 0], [1, 1]) == 0.0


def test_dimension_mismatch():
    with pytest.raises(ValueError):
        cosine_similarity([1, 2], [1, 2, 3])
