from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundError,
    FileTooLargeError,
    PdfTextExtractionError,
    UnsupportedFileTypeError,
)
from app.database import repositories
from app.database.db import transaction
from app.services import chunking_service, embedding_service
from app.services.course_service import ensure_course_exists
from app.utils.file_storage import safe_delete_stored_file
from app.utils.pdf_reader import extract_pdf_text


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "document.pdf"


async def ingest_pdf(course_id: int, upload: UploadFile) -> dict:
    ensure_course_exists(course_id)

    original_name = upload.filename or ""
    content_type = (upload.content_type or "").lower()

    if not original_name.lower().endswith(".pdf"):
        raise UnsupportedFileTypeError()

    if content_type and content_type not in {
        "application/pdf",
        "application/octet-stream",
    }:
        raise UnsupportedFileTypeError()

    raw = await upload.read()
    if len(raw) > settings.max_file_size_bytes:
        raise FileTooLargeError(settings.max_file_size_mb)
    if not raw:
        raise PdfTextExtractionError()

    settings.document_storage_path.mkdir(parents=True, exist_ok=True)
    local_name = f"{uuid.uuid4().hex}_{_safe_filename(original_name)}"
    stored_path = settings.document_storage_path / local_name
    stored_path.write_bytes(raw)

    try:
        text = extract_pdf_text(stored_path)
        chunks = chunking_service.chunk_text(text)
        if not chunks:
            raise PdfTextExtractionError()

        embeddings = embedding_service.embed_texts(
            [chunk["content"] for chunk in chunks]
        )
        if len(embeddings) != len(chunks):
            raise RuntimeError("Chunk ve embedding sayıları eşleşmiyor.")

        enriched_chunks = [
            {
                **chunk,
                "embedding": embedding,
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        with transaction() as conn:
            document_id = repositories.create_document(
                conn,
                course_id,
                original_name,
                str(stored_path),
            )
            repositories.insert_chunks(
                conn,
                document_id,
                course_id,
                enriched_chunks,
            )
            repositories.update_document_chunk_count(
                conn,
                document_id,
                len(enriched_chunks),
            )

        return {
            "id": document_id,
            "courseId": course_id,
            "fileName": original_name,
            "chunkCount": len(enriched_chunks),
            "message": "Doküman başarıyla işlendi.",
        }
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise


def reindex_document(document_id: int) -> dict:
    """Re-extracts text from the already-stored PDF and replaces this
    document's chunks/embeddings in place -- used when the chunking
    strategy changes, so existing uploads don't need to be re-uploaded.

    Old chunks are only removed once the new chunks and embeddings have
    been produced successfully, and the delete+insert happens inside one
    transaction: a failure partway through leaves the previous chunk set
    untouched rather than leaving the document without any chunks.
    """
    document = repositories.get_document_by_id(document_id)
    if document is None:
        raise DocumentNotFoundError()

    old_chunk_count = document["chunk_count"]

    stored_path = Path(document["stored_path"])
    if not stored_path.exists():
        raise PdfTextExtractionError()

    text = extract_pdf_text(stored_path)
    chunks = chunking_service.chunk_text(text)
    if not chunks:
        raise PdfTextExtractionError()

    for chunk in chunks:
        if not chunk["content"].strip():
            raise RuntimeError("Boş içerikli chunk üretildi.")
        if len(chunk["content"]) > settings.chunk_max_chars:
            raise RuntimeError(
                f"Chunk {chunk['chunk_index']} sınırı aşıyor: "
                f"{len(chunk['content'])} > {settings.chunk_max_chars}"
            )
    if [c["chunk_index"] for c in chunks] != list(range(len(chunks))):
        raise RuntimeError("chunk_index sırası veya benzersizliği bozuk.")

    embeddings = embedding_service.embed_texts(
        [chunk["content"] for chunk in chunks]
    )
    if len(embeddings) != len(chunks):
        raise RuntimeError("Chunk ve embedding sayıları eşleşmiyor.")

    dimensions = {len(embedding) for embedding in embeddings}
    if len(dimensions) != 1:
        raise RuntimeError(
            f"Embedding boyutları tutarsız: {sorted(dimensions)}"
        )

    enriched_chunks = [
        {**chunk, "embedding": embedding}
        for chunk, embedding in zip(chunks, embeddings)
    ]

    with transaction() as conn:
        repositories.delete_chunks_by_document(conn, document_id)
        repositories.insert_chunks(
            conn,
            document_id,
            document["course_id"],
            enriched_chunks,
        )
        repositories.update_document_chunk_count(
            conn,
            document_id,
            len(enriched_chunks),
        )

    lengths = [len(chunk["content"]) for chunk in chunks]

    return {
        "id": document_id,
        "fileName": document["file_name"],
        "courseId": document["course_id"],
        "oldChunkCount": old_chunk_count,
        "chunkCount": len(enriched_chunks),
        "embeddingCount": len(embeddings),
        "embeddingDim": dimensions.pop(),
        "minChars": min(lengths),
        "maxChars": max(lengths),
        "avgChars": sum(lengths) / len(lengths),
    }


def delete_document(document_id: int) -> None:
    document = repositories.get_document_by_id(document_id)
    if document is None:
        raise DocumentNotFoundError()

    # DB is the source of truth for retrieval correctness, so it's deleted
    # first, inside its own transaction; document_chunks cascades via FK.
    # Physical file cleanup only runs after that commit, and is best-effort
    # (see safe_delete_stored_file) -- a filesystem hiccup here must never
    # look like the (already-successful) deletion failed.
    with transaction() as conn:
        repositories.delete_document(conn, document_id)

    safe_delete_stored_file(document["stored_path"], settings.document_storage_path)


def list_documents(course_id: int | None = None) -> list[dict]:
    if course_id is not None:
        ensure_course_exists(course_id)

    rows = repositories.list_documents(course_id)
    return [
        {
            "id": row["id"],
            "courseId": row["course_id"],
            "courseName": row["course_name"],
            "fileName": row["file_name"],
            "chunkCount": row["chunk_count"],
            "createdAt": row["created_at"],
        }
        for row in rows
    ]
