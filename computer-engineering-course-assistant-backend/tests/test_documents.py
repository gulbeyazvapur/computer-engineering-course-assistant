from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import settings
from app.core.exceptions import DocumentNotFoundError, PdfTextExtractionError
from app.database import repositories
from app.database.db import transaction
from app.services import course_service, document_service


def _create_document_with_file(course_id: int, filename: str = "notes.pdf") -> dict:
    settings.document_storage_path.mkdir(parents=True, exist_ok=True)
    stored_path = settings.document_storage_path / filename
    stored_path.write_bytes(b"%PDF-1.4 fake content")

    with transaction() as conn:
        document_id = repositories.create_document(
            conn, course_id, filename, str(stored_path)
        )
        repositories.insert_chunks(
            conn,
            document_id,
            course_id,
            [{"chunk_index": 0, "content": "test", "embedding": [0.1, 0.2]}],
        )
        repositories.update_document_chunk_count(conn, document_id, 1)

    return repositories.get_document_by_id(document_id)


def test_delete_document_succeeds_for_existing_document(isolated_db):
    """A. Deleting an existing document does not raise -- the router
    returns 204 whenever the service call completes without error."""
    course = course_service.create_course("Ders", None)
    document = _create_document_with_file(course["id"])

    document_service.delete_document(document["id"])  # must not raise


def test_delete_nonexistent_document_raises_not_found(isolated_db):
    """B. Deleting a document id that doesn't exist -> DocumentNotFoundError
    (404 via app_error_handler)."""
    with pytest.raises(DocumentNotFoundError):
        document_service.delete_document(999)


def test_delete_document_removes_db_row(isolated_db):
    """C. After delete, the document row is gone."""
    course = course_service.create_course("Ders", None)
    document = _create_document_with_file(course["id"])

    document_service.delete_document(document["id"])

    assert repositories.get_document_by_id(document["id"]) is None


def test_delete_document_removes_chunks(isolated_db):
    """D. After delete, chunks belonging to that document are gone too --
    via FK ON DELETE CASCADE, no manual chunk delete needed."""
    course = course_service.create_course("Ders", None)
    document = _create_document_with_file(course["id"])

    document_service.delete_document(document["id"])

    assert repositories.get_chunks_by_course(course["id"]) == []


def test_delete_document_removes_physical_file(isolated_db):
    """E. The physical PDF file is deleted from disk."""
    course = course_service.create_course("Ders", None)
    document = _create_document_with_file(course["id"])
    stored_path = Path(document["stored_path"])
    assert stored_path.exists()

    document_service.delete_document(document["id"])

    assert not stored_path.exists()


def test_delete_document_when_physical_file_already_missing(isolated_db):
    """F. If the physical file is already gone, delete still succeeds
    cleanly -- the DB is the source of truth, a pre-missing file is not an
    error."""
    course = course_service.create_course("Ders", None)
    document = _create_document_with_file(course["id"])
    Path(document["stored_path"]).unlink()

    document_service.delete_document(document["id"])  # must not raise

    assert repositories.get_document_by_id(document["id"]) is None


def test_reindex_document_replaces_chunks_and_embeddings(isolated_db, monkeypatch):
    """A. Reindexing an existing document drops its old chunks and inserts
    the ones produced by the current chunker/embedder, from the already
    stored PDF (no re-upload needed)."""
    course = course_service.create_course("Ders", None)
    document = _create_document_with_file(course["id"])

    monkeypatch.setattr(
        document_service, "extract_pdf_text", lambda path: "Yeni metin icerigi."
    )
    monkeypatch.setattr(
        document_service.chunking_service,
        "chunk_text",
        lambda text: [
            {"chunk_index": 0, "content": "yeni parca 1"},
            {"chunk_index": 1, "content": "yeni parca 2"},
        ],
    )
    monkeypatch.setattr(
        document_service.embedding_service,
        "embed_texts",
        lambda texts: [[0.5, 0.5] for _ in texts],
    )

    result = document_service.reindex_document(document["id"])

    assert result["chunkCount"] == 2
    chunks = repositories.get_chunks_by_course(course["id"])
    assert sorted(c["content"] for c in chunks) == ["yeni parca 1", "yeni parca 2"]
    assert repositories.get_document_by_id(document["id"])["chunk_count"] == 2


def test_reindex_nonexistent_document_raises_not_found(isolated_db):
    """B. Reindexing a document id that doesn't exist -> DocumentNotFoundError."""
    with pytest.raises(DocumentNotFoundError):
        document_service.reindex_document(999)


def test_reindex_document_missing_physical_file_raises(isolated_db):
    """C. If the stored PDF is gone, reindexing fails loudly instead of
    silently wiping the document's chunks."""
    course = course_service.create_course("Ders", None)
    document = _create_document_with_file(course["id"])
    Path(document["stored_path"]).unlink()

    with pytest.raises(PdfTextExtractionError):
        document_service.reindex_document(document["id"])

    # Old chunks must still be there -- nothing was touched.
    assert len(repositories.get_chunks_by_course(course["id"])) == 1


def test_reindex_document_preserves_old_chunks_when_embedding_fails(
    isolated_db, monkeypatch
):
    """D. If embedding fails partway through, the old chunk set must remain
    intact -- a reindex must never leave a document without any chunks."""
    course = course_service.create_course("Ders", None)
    document = _create_document_with_file(course["id"])

    monkeypatch.setattr(
        document_service, "extract_pdf_text", lambda path: "Yeni metin."
    )
    monkeypatch.setattr(
        document_service.chunking_service,
        "chunk_text",
        lambda text: [{"chunk_index": 0, "content": "yeni parca"}],
    )

    def failing_embed_texts(texts):
        raise RuntimeError("embedding servisi kullanılamıyor")

    monkeypatch.setattr(
        document_service.embedding_service, "embed_texts", failing_embed_texts
    )

    with pytest.raises(RuntimeError):
        document_service.reindex_document(document["id"])

    chunks = repositories.get_chunks_by_course(course["id"])
    assert len(chunks) == 1
    assert chunks[0]["content"] == "test"


def test_delete_document_refuses_path_outside_storage_root(isolated_db, tmp_path):
    """G. A stored_path pointing outside the storage root is never deleted
    on disk, even though the DB row is still cleaned up (defense in depth
    against a corrupted/tampered row)."""
    course = course_service.create_course("Ders", None)

    outside_file = tmp_path / "outside_storage.pdf"
    outside_file.write_bytes(b"should not be touched")

    with transaction() as conn:
        document_id = repositories.create_document(
            conn, course["id"], "notes.pdf", str(outside_file)
        )
        repositories.insert_chunks(
            conn,
            document_id,
            course["id"],
            [{"chunk_index": 0, "content": "test", "embedding": [0.1, 0.2]}],
        )

    document_service.delete_document(document_id)

    assert outside_file.exists()
    assert repositories.get_document_by_id(document_id) is None
