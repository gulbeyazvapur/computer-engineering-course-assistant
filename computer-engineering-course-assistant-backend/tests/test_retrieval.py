from __future__ import annotations

from app.database import repositories
from app.database.db import transaction
from app.services import course_service, retrieval_service


def test_retrieval_is_scoped_and_ranked(isolated_db, monkeypatch):
    c1 = course_service.create_course("İşletim Sistemleri", None)
    c2 = course_service.create_course("Ağlar", None)

    with transaction() as conn:
        d1 = repositories.create_document(conn, c1["id"], "deadlock.pdf", "x")
        repositories.insert_chunks(
            conn,
            d1,
            c1["id"],
            [
                {
                    "chunk_index": 0,
                    "content": "deadlock",
                    "embedding": [1.0, 0.0],
                },
                {
                    "chunk_index": 1,
                    "content": "memory",
                    "embedding": [0.0, 1.0],
                },
            ],
        )
        repositories.update_document_chunk_count(conn, d1, 2)

        d2 = repositories.create_document(conn, c2["id"], "tcp.pdf", "y")
        repositories.insert_chunks(
            conn,
            d2,
            c2["id"],
            [
                {
                    "chunk_index": 0,
                    "content": "tcp",
                    "embedding": [1.0, 0.0],
                },
            ],
        )
        repositories.update_document_chunk_count(conn, d2, 1)

    monkeypatch.setattr(
        retrieval_service.embedding_service,
        "embed_text",
        lambda _: [1.0, 0.0],
    )

    results = retrieval_service.get_top_chunks(
        "deadlock nedir",
        c1["id"],
        top_k=2,
    )

    assert results[0]["document_name"] == "deadlock.pdf"
    assert results[0]["content"] == "deadlock"
    assert all(item["document_name"] != "tcp.pdf" for item in results)
