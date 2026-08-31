from __future__ import annotations

import sqlite3

from app.core.config import settings
from app.core.exceptions import CourseNotFoundError, DuplicateCourseError
from app.database import repositories
from app.database.db import transaction
from app.utils.file_storage import safe_delete_stored_file


def create_course(name: str, description: str | None) -> dict:
    normalized_name = name.strip()
    normalized_description = description.strip() if description else None

    try:
        with transaction() as conn:
            course = repositories.create_course(
                conn,
                normalized_name,
                normalized_description or None,
            )
    except sqlite3.IntegrityError as exc:
        raise DuplicateCourseError() from exc

    return course


def list_courses() -> list[dict]:
    return repositories.list_courses()


def ensure_course_exists(course_id: int) -> dict:
    course = repositories.get_course_by_id(course_id)
    if course is None:
        raise CourseNotFoundError()
    return course


def update_course(course_id: int, name: str, description: str | None) -> dict:
    ensure_course_exists(course_id)

    normalized_name = name.strip()
    normalized_description = description.strip() if description else None

    try:
        with transaction() as conn:
            course = repositories.update_course(
                conn,
                course_id,
                normalized_name,
                normalized_description or None,
            )
    except sqlite3.IntegrityError as exc:
        raise DuplicateCourseError() from exc

    return course


def delete_course(course_id: int) -> None:
    ensure_course_exists(course_id)

    # Stored paths must be read before the DB delete -- once the course row
    # (and its documents, via FK cascade) is gone, there's nothing left to
    # read them from.
    stored_paths = repositories.list_document_paths_by_course(course_id)

    with transaction() as conn:
        repositories.delete_course(conn, course_id)

    for stored_path in stored_paths:
        safe_delete_stored_file(stored_path, settings.document_storage_path)
