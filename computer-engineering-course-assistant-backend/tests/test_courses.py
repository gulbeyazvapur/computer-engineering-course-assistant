import pytest

from app.core.config import settings
from app.core.exceptions import CourseNotFoundError, DuplicateCourseError
from app.database import repositories
from app.database.db import transaction
from app.services import course_service


def test_create_and_list_course(isolated_db):
    created = course_service.create_course(
        "İşletim Sistemleri",
        "Ders notları",
    )

    assert created["name"] == "İşletim Sistemleri"

    courses = course_service.list_courses()
    assert len(courses) == 1
    assert courses[0]["name"] == "İşletim Sistemleri"


def test_duplicate_course(isolated_db):
    course_service.create_course("Ağlar", None)

    with pytest.raises(DuplicateCourseError):
        course_service.create_course("Ağlar", None)


def test_update_course_renames_it(isolated_db):
    """C. Rename/update changes name and description, keeps the same id."""
    course = course_service.create_course("Ağlar", "Eski açıklama")

    updated = course_service.update_course(
        course["id"], "Bilgisayar Ağları", "Yeni açıklama"
    )

    assert updated["id"] == course["id"]
    assert updated["name"] == "Bilgisayar Ağları"
    assert updated["description"] == "Yeni açıklama"


def test_update_course_rejects_duplicate_name(isolated_db):
    """D. Renaming to a name already used by another course is rejected."""
    course_service.create_course("Ağlar", None)
    other = course_service.create_course("Veritabanları", None)

    with pytest.raises(DuplicateCourseError):
        course_service.update_course(other["id"], "Ağlar", None)


def test_update_nonexistent_course_raises_not_found(isolated_db):
    with pytest.raises(CourseNotFoundError):
        course_service.update_course(999, "Herhangi Bir Ad", None)


def test_delete_course_removes_it(isolated_db):
    """E. Deleting a course removes it from the list."""
    course = course_service.create_course("Geçici Ders", None)

    course_service.delete_course(course["id"])

    assert course_service.list_courses() == []


def test_delete_nonexistent_course_raises_not_found(isolated_db):
    """F. Deleting a course id that doesn't exist raises a clear error."""
    with pytest.raises(CourseNotFoundError):
        course_service.delete_course(999)


def test_delete_course_cascades_to_documents_and_chunks(isolated_db):
    """G. Deleting a course must not leave dangling documents/chunks."""
    course = course_service.create_course("Geçici Ders", None)

    with transaction() as conn:
        document_id = repositories.create_document(
            conn, course["id"], "notes.pdf", "/tmp/notes.pdf"
        )
        repositories.insert_chunks(
            conn,
            document_id,
            course["id"],
            [{"chunk_index": 0, "content": "test", "embedding": [0.1, 0.2]}],
        )
        repositories.update_document_chunk_count(conn, document_id, 1)

    course_service.delete_course(course["id"])

    assert repositories.list_documents(course["id"]) == []
    assert repositories.get_chunks_by_course(course["id"]) == []


def test_delete_course_removes_physical_pdf_files(isolated_db):
    """H. Deleting a course also cleans up the physical PDF files of its
    documents, not just the DB rows/cascade."""
    course = course_service.create_course("Geçici Ders", None)
    settings.document_storage_path.mkdir(parents=True, exist_ok=True)
    stored_path = settings.document_storage_path / "notes.pdf"
    stored_path.write_bytes(b"%PDF-1.4 fake")

    with transaction() as conn:
        document_id = repositories.create_document(
            conn, course["id"], "notes.pdf", str(stored_path)
        )
        repositories.insert_chunks(
            conn,
            document_id,
            course["id"],
            [{"chunk_index": 0, "content": "test", "embedding": [0.1, 0.2]}],
        )

    assert stored_path.exists()

    course_service.delete_course(course["id"])

    assert not stored_path.exists()


def test_delete_course_does_not_affect_other_course_pdfs(isolated_db):
    """I. Deleting one course's PDFs must never touch another course's
    physical files or DB rows."""
    course_a = course_service.create_course("Ders A", None)
    course_b = course_service.create_course("Ders B", None)
    settings.document_storage_path.mkdir(parents=True, exist_ok=True)

    path_a = settings.document_storage_path / "a.pdf"
    path_a.write_bytes(b"a")
    path_b = settings.document_storage_path / "b.pdf"
    path_b.write_bytes(b"b")

    with transaction() as conn:
        doc_a = repositories.create_document(conn, course_a["id"], "a.pdf", str(path_a))
        repositories.insert_chunks(
            conn,
            doc_a,
            course_a["id"],
            [{"chunk_index": 0, "content": "a", "embedding": [0.1]}],
        )
        doc_b = repositories.create_document(conn, course_b["id"], "b.pdf", str(path_b))
        repositories.insert_chunks(
            conn,
            doc_b,
            course_b["id"],
            [{"chunk_index": 0, "content": "b", "embedding": [0.2]}],
        )

    course_service.delete_course(course_a["id"])

    assert not path_a.exists()
    assert path_b.exists()
    assert repositories.get_document_by_id(doc_b) is not None


def test_list_courses_includes_document_count(isolated_db):
    course = course_service.create_course("Geçici Ders", None)

    with transaction() as conn:
        document_id = repositories.create_document(
            conn, course["id"], "notes.pdf", "/tmp/notes.pdf"
        )
        repositories.insert_chunks(
            conn,
            document_id,
            course["id"],
            [{"chunk_index": 0, "content": "test", "embedding": [0.1, 0.2]}],
        )

    courses = course_service.list_courses()
    assert courses[0]["document_count"] == 1
