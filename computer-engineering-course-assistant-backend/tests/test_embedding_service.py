from __future__ import annotations

from app.services import embedding_service


class _FakeEmbeddingItem:
    def __init__(self, embedding):
        self.embedding = embedding


class _FakeEmbeddingResponse:
    def __init__(self, embeddings):
        self.data = [_FakeEmbeddingItem(e) for e in embeddings]


class _FakeEmbeddingClient:
    def generate_embedding(self, text):
        return _FakeEmbeddingResponse([[0.1, 0.2]])

    def generate_embeddings(self, texts):
        return _FakeEmbeddingResponse([[0.1, 0.2] for _ in texts])


class _FakeEmbeddingModel:
    def get_embedding_client(self):
        return _FakeEmbeddingClient()


class _FakeProviderSpy:
    def __init__(self):
        self.unload_calls: list[str] = []

    def get_loaded_model(self, alias):
        return _FakeEmbeddingModel()

    def unload_model(self, alias):
        self.unload_calls.append(alias)


def test_embed_texts_does_not_unload_between_chunks(monkeypatch):
    """F. Document ingestion (embed_texts, used for batch chunk embedding)
    must never trigger a per-chunk/per-batch unload -- unloading between
    every chunk would force the embedding model to reload repeatedly during
    a single PDF's ingestion, which is a severe performance regression."""
    spy = _FakeProviderSpy()
    monkeypatch.setattr(embedding_service, "foundry_provider", spy)

    result = embedding_service.embed_texts(["parça 1", "parça 2", "parça 3"])

    assert len(result) == 3
    assert spy.unload_calls == []


def test_embed_text_does_not_unload(monkeypatch):
    """F (single-text path). The query-embedding helper itself never
    unloads -- unloading after retrieval is the RAG orchestrator's job
    (rag_service), not embedding_service's."""
    spy = _FakeProviderSpy()
    monkeypatch.setattr(embedding_service, "foundry_provider", spy)

    result = embedding_service.embed_text("soru metni")

    assert result == [0.1, 0.2]
    assert spy.unload_calls == []
