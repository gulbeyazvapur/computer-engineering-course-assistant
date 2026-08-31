from __future__ import annotations

import pytest

from app.core.config import settings
from app.database.db import init_database


@pytest.fixture
def isolated_db(tmp_path):
    old_db = settings.database_path
    old_docs = settings.document_storage_path

    settings.database_path = tmp_path / "test.db"
    settings.document_storage_path = tmp_path / "documents"
    init_database()

    yield

    settings.database_path = old_db
    settings.document_storage_path = old_docs
