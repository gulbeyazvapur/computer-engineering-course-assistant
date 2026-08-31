from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import NoDocumentsError
from app.database import repositories
from app.services import embedding_service
from app.services.course_service import ensure_course_exists
from app.utils.similarity import cosine_similarity


def get_top_chunks(
    question: str,
    course_id: int,
    top_k: int | None = None,
) -> list[dict]:
    ensure_course_exists(course_id)

    chunks = repositories.get_chunks_by_course(course_id)
    if not chunks:
        raise NoDocumentsError()

    query_embedding = embedding_service.embed_text(question)

    scored: list[dict] = []
    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk["embedding"])
        scored.append(
            {
                **chunk,
                "score": score,
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    k = top_k or settings.top_k
    selected = scored[: max(1, k)]

    return [
        item
        for item in selected
        if item["score"] >= settings.min_similarity_score
    ]
