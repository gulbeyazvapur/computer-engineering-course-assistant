from __future__ import annotations

from app.database import repositories
from app.database.db import transaction
from app.database.seed import DEFAULT_COURSES, seed_default_courses
from app.services import course_service


def test_seed_populates_empty_db_with_all_default_courses(isolated_db):
    """A. Empty DB -> all default courses are created."""
    seed_default_courses()

    courses = course_service.list_courses()

    assert len(courses) == len(DEFAULT_COURSES)
    assert {c["name"] for c in courses} == {name for name, _ in DEFAULT_COURSES}


def test_seed_is_idempotent_when_run_twice(isolated_db):
    """B. Running seed a second time does not create duplicates."""
    seed_default_courses()
    seed_default_courses()

    courses = course_service.list_courses()

    assert len(courses) == len(DEFAULT_COURSES)


def test_seed_skips_entirely_when_any_course_already_exists(isolated_db):
    """C (revised for dynamic course management). A single pre-existing
    course -- even just one, even not a default -- must block seeding
    entirely, not just skip that one duplicate name and top up the rest.
    Seeding is a one-time bootstrap for a genuinely empty database; once any
    course exists, the user is managing their own course list and defaults
    must never be backfilled again."""
    existing = course_service.create_course(
        "İşletim Sistemleri", "Önceden var olan açıklama"
    )

    seed_default_courses()

    courses = course_service.list_courses()

    assert len(courses) == 1
    assert courses[0]["id"] == existing["id"]
    assert courses[0]["description"] == "Önceden var olan açıklama"


def test_seed_only_runs_when_courses_table_is_truly_empty(isolated_db):
    """H. Any pre-existing course -- default-named or entirely user-defined
    -- blocks seeding entirely."""
    course_service.create_course("Kullanıcının Kendi Dersi", None)

    seed_default_courses()

    courses = course_service.list_courses()
    assert len(courses) == 1
    assert courses[0]["name"] == "Kullanıcının Kendi Dersi"


def test_deleted_default_course_does_not_return_on_reseed(isolated_db):
    """I. A default course the user deleted must not be recreated by a
    later seed_default_courses() call (e.g. on the next app restart), since
    the courses table is no longer empty."""
    seed_default_courses()
    courses = course_service.list_courses()
    os_course = next(c for c in courses if c["name"] == "İşletim Sistemleri")

    course_service.delete_course(os_course["id"])

    seed_default_courses()

    courses_after = course_service.list_courses()
    names_after = {c["name"] for c in courses_after}

    assert "İşletim Sistemleri" not in names_after
    assert len(courses_after) == len(DEFAULT_COURSES) - 1


def test_seed_preserves_existing_course_id(isolated_db):
    """D. A pre-existing course keeps its original id after seeding."""
    existing = course_service.create_course("İşletim Sistemleri", None)
    original_id = existing["id"]

    seed_default_courses()

    fetched = course_service.ensure_course_exists(original_id)
    assert fetched["name"] == "İşletim Sistemleri"


def test_seed_does_not_touch_existing_documents_or_chunks(isolated_db):
    """E. Documents/chunks already linked to a course must survive seeding."""
    course = course_service.create_course("İşletim Sistemleri", None)

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

    seed_default_courses()

    docs = repositories.list_documents(course["id"])
    assert len(docs) == 1
    assert docs[0]["file_name"] == "notes.pdf"

    chunks = repositories.get_chunks_by_course(course["id"])
    assert len(chunks) == 1
    assert chunks[0]["content"] == "test"


def test_default_courses_have_no_duplicate_names():
    names = [name for name, _ in DEFAULT_COURSES]
    assert len(names) == len(set(names))


def test_default_courses_have_short_distinct_descriptions():
    descriptions = [description for _, description in DEFAULT_COURSES]
    assert len(descriptions) == len(set(descriptions))
    for description in descriptions:
        assert description.strip() == description
        assert len(description) < 200
