from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import EmbeddingError
from app.services.foundry_service import foundry_provider


def embed_text(text: str) -> list[float]:
    try:
        model = foundry_provider.get_loaded_model(settings.embedding_model_name)
        client = model.get_embedding_client()
        response = client.generate_embedding(text)
        return [float(value) for value in response.data[0].embedding]
    except Exception as exc:
        raise EmbeddingError(str(exc)) from exc


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    try:
        model = foundry_provider.get_loaded_model(settings.embedding_model_name)
        client = model.get_embedding_client()
        response = client.generate_embeddings(texts)
        return [
            [float(value) for value in item.embedding]
            for item in response.data
        ]
    except Exception as exc:
        raise EmbeddingError(str(exc)) from exc
