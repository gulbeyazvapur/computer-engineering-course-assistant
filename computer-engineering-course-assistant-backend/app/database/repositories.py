from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.database.db import get_connection


def create_course(
    conn: sqlite3.Connection, name: str, description: str | None
) -> dict[str, Any]:
    cursor = conn.execute(
        "INSERT INTO courses(name, description) VALUES (?, ?)",
        (name, description),
    )
    row = conn.execute(
        "SELECT id, name, description, created_at FROM courses WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return dict(row)


def seed_courses(
    conn: sqlite3.Connection, courses: list[tuple[str, str]]
) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO courses(name, description) VALUES (?, ?)",
        courses,
    )


def list_courses() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id,
                c.name,
                c.description,
                c.created_at,
                COUNT(d.id) AS document_count
            FROM courses c
            LEFT JOIN documents d ON d.course_id = c.id
            GROUP BY c.id
            ORDER BY c.name COLLATE NOCASE
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_course_by_id(course_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, description, created_at
            FROM courses
            WHERE id = ?
            """,
            (course_id,),
        ).fetchone()
    return dict(row) if row else None


def update_course(
    conn: sqlite3.Connection, course_id: int, name: str, description: str | None
) -> dict[str, Any] | None:
    conn.execute(
        "UPDATE courses SET name = ?, description = ? WHERE id = ?",
        (name, description, course_id),
    )
    row = conn.execute(
        "SELECT id, name, description, created_at FROM courses WHERE id = ?",
        (course_id,),
    ).fetchone()
    return dict(row) if row else None


def delete_course(conn: sqlite3.Connection, course_id: int) -> int:
    """Deletes the course row; ``documents``/``document_chunks`` cascade via
    the FK ``ON DELETE CASCADE`` already declared in schema.sql (active
    because get_connection() sets ``PRAGMA foreign_keys = ON`` on every
    connection). Returns the number of course rows deleted (0 or 1)."""
    cursor = conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    return cursor.rowcount


def count_courses(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM courses").fetchone()
    return int(row["c"])


def create_document(
    conn: sqlite3.Connection,
    course_id: int,
    file_name: str,
    stored_path: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO documents(course_id, file_name, stored_path)
        VALUES (?, ?, ?)
        """,
        (course_id, file_name, stored_path),
    )
    return int(cursor.lastrowid)


def update_document_chunk_count(
    conn: sqlite3.Connection, document_id: int, chunk_count: int
) -> None:
    conn.execute(
        """
        UPDATE documents
        SET chunk_count = ?
        WHERE id = ?
        """,
        (chunk_count, document_id),
    )


def insert_chunks(
    conn: sqlite3.Connection,
    document_id: int,
    course_id: int,
    chunks: list[dict[str, Any]],
) -> None:
    values = [
        (
            document_id,
            course_id,
            chunk["chunk_index"],
            chunk["content"],
            json.dumps(chunk["embedding"]),
        )
        for chunk in chunks
    ]
    conn.executemany(
        """
        INSERT INTO document_chunks(
            document_id,
            course_id,
            chunk_index,
            content,
            embedding
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        values,
    )


def delete_chunks_by_document(conn: sqlite3.Connection, document_id: int) -> int:
    """Deletes only the chunk rows for one document, keeping the document
    row itself -- used for reindexing (chunker change), unlike
    delete_document which removes the document entirely."""
    cursor = conn.execute(
        "DELETE FROM document_chunks WHERE document_id = ?",
        (document_id,),
    )
    return cursor.rowcount


def get_document_by_id(document_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, course_id, file_name, stored_path, chunk_count, created_at
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()
    return dict(row) if row else None


def delete_document(conn: sqlite3.Connection, document_id: int) -> int:
    """Deletes the document row; document_chunks cascades via the FK
    ON DELETE CASCADE already declared in schema.sql. Returns the number of
    rows deleted (0 or 1)."""
    cursor = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    return cursor.rowcount


def list_document_paths_by_course(course_id: int) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT stored_path FROM documents WHERE course_id = ?",
            (course_id,),
        ).fetchall()
    return [row["stored_path"] for row in rows]


def list_documents(course_id: int | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT
            d.id,
            d.course_id,
            c.name AS course_name,
            d.file_name,
            d.chunk_count,
            d.created_at
        FROM documents d
        JOIN courses c ON c.id = d.course_id
    """
    params: tuple[Any, ...] = ()
    if course_id is not None:
        query += " WHERE d.course_id = ?"
        params = (course_id,)
    query += " ORDER BY d.created_at DESC, d.id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_chunks_by_course(course_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                dc.id AS chunk_id,
                dc.document_id,
                d.file_name AS document_name,
                dc.chunk_index,
                dc.content,
                dc.embedding
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.course_id = ?
            ORDER BY dc.document_id, dc.chunk_index
            """,
            (course_id,),
        ).fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["embedding"] = json.loads(item["embedding"])
        result.append(item)
    return result
