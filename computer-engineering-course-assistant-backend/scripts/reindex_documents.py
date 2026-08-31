"""Re-chunk and re-embed one or more already-ingested documents in place,
using the current chunking_service strategy, without re-uploading the PDF.

Backs up the SQLite database before touching anything. Each document is
reindexed independently and strictly sequentially -- one failure does not
abort the rest, and a document's old chunks are only replaced after its new
chunks/embeddings were produced and validated successfully (see
document_service.reindex_document).

Usage:
    python scripts/reindex_documents.py <document_id> [<document_id> ...]
    python scripts/reindex_documents.py --all
"""

from __future__ import annotations

import shutil
import sys
import time
from datetime import datetime, timezone

from app.core.config import settings
from app.core.exceptions import AppError
from app.database import repositories
from app.database.db import get_connection
from app.services import document_service


def backup_database() -> str:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = settings.database_path.with_name(
        f"{settings.database_path.stem}.backup-before-full-reindex-{timestamp}"
        f"{settings.database_path.suffix}"
    )
    shutil.copy2(settings.database_path, backup_path)
    return str(backup_path)


def global_counts() -> dict:
    with get_connection() as conn:
        courses = conn.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"]
        documents = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"]
        chunks = conn.execute(
            "SELECT COUNT(*) AS c FROM document_chunks"
        ).fetchone()["c"]
    db_size = settings.database_path.stat().st_size
    return {
        "courses": courses,
        "documents": documents,
        "chunks": chunks,
        "db_size_bytes": db_size,
    }


def size_bucket_counts(lengths: list[int]) -> dict[str, int]:
    buckets = {"<100": 0, "100-300": 0, "300-600": 0, "600-1000": 0, ">1000": 0}
    for length in lengths:
        if length < 100:
            buckets["<100"] += 1
        elif length < 300:
            buckets["100-300"] += 1
        elif length < 600:
            buckets["300-600"] += 1
        elif length <= 1000:
            buckets["600-1000"] += 1
        else:
            buckets[">1000"] += 1
    return buckets


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)

    if args == ["--all"]:
        document_ids = [row["id"] for row in repositories.list_documents()]
    else:
        document_ids = [int(a) for a in args]

    if not document_ids:
        print("Reindex edilecek doküman bulunamadı.")
        return

    documents_by_id = {row["id"]: row for row in repositories.list_documents()}

    before = global_counts()
    print("=== REINDEX ÖNCESİ DURUM ===")
    print(
        f"courses={before['courses']} documents={before['documents']} "
        f"chunks={before['chunks']} db_size={before['db_size_bytes']} bytes"
    )

    backup_path = backup_database()
    print(f"DB yedeği alındı: {backup_path}\n")

    succeeded = 0
    failed: list[tuple[int, str]] = []
    started_at = time.time()

    total = len(document_ids)
    for index, document_id in enumerate(document_ids, start=1):
        meta = documents_by_id.get(document_id)
        course_name = meta["course_name"] if meta else "?"
        file_name = meta["file_name"] if meta else "?"

        t0 = time.time()
        print(f"[{index}/{total}] {course_name} | {file_name}")
        try:
            result = document_service.reindex_document(document_id)
            duration = time.time() - t0
            print(
                f"  old_chunks={result['oldChunkCount']} "
                f"new_chunks={result['chunkCount']} "
                f"min={result['minChars']} max={result['maxChars']} "
                f"avg={result['avgChars']:.0f} "
                f"embeddings={result['embeddingCount']} (dim={result['embeddingDim']}) "
                f"status=OK duration={duration:.1f}s"
            )
            succeeded += 1
        except AppError as exc:
            duration = time.time() - t0
            print(
                f"  status=FAIL code={exc.code} message={exc.message} "
                f"duration={duration:.1f}s (eski chunk'lar korunuyor)"
            )
            failed.append((document_id, f"{exc.code}: {exc.message}"))
        except Exception as exc:
            duration = time.time() - t0
            print(f"  status=FAIL error={exc} duration={duration:.1f}s (eski chunk'lar korunuyor)")
            failed.append((document_id, str(exc)))

    total_duration = time.time() - started_at
    after = global_counts()

    print("\n=== REINDEX SONRASI DURUM ===")
    print(
        f"courses={after['courses']} documents={after['documents']} "
        f"chunks={after['chunks']} db_size={after['db_size_bytes']} bytes"
    )
    print(f"\nToplam: {total}, başarılı: {succeeded}, başarısız: {len(failed)}")
    print(f"Toplam süre: {total_duration:.1f}s")
    if failed:
        print("Başarısız olanlar (eski chunk'ları korunmuştur):")
        for document_id, message in failed:
            print(f"  - {document_id}: {message}")

    placeholders = ",".join("?" for _ in document_ids)
    with get_connection() as conn:
        lengths = [
            row["l"]
            for row in conn.execute(
                f"SELECT length(content) AS l FROM document_chunks "
                f"WHERE document_id IN ({placeholders})",
                document_ids,
            ).fetchall()
        ]
    if lengths:
        buckets = size_bucket_counts(lengths)
        print(f"\nChunk boyut dağılımı (işlenen {len(document_ids)} doküman, {len(lengths)} chunk):")
        for label, count in buckets.items():
            print(f"  {label}: {count}")
        print(
            f"  min={min(lengths)} max={max(lengths)} "
            f"avg={sum(lengths)/len(lengths):.0f}"
        )

    zero_chunk_docs = [
        row["id"]
        for row in repositories.list_documents()
        if row["id"] in document_ids and row["chunk_count"] == 0
    ]
    if zero_chunk_docs:
        print(f"UYARI: chunk_count=0 olan dokümanlar: {zero_chunk_docs}")


if __name__ == "__main__":
    main()
