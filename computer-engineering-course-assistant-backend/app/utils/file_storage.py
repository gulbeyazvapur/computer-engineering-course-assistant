from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def safe_delete_stored_file(stored_path: str, storage_root: Path) -> None:
    """Best-effort delete of a file the app itself wrote into storage_root.

    Refuses to touch anything outside storage_root (defense in depth --
    stored_path always comes from our own DB, written by our own upload
    code, but a corrupted/tampered row must never cause a delete outside
    the app's own storage directory). A missing file is treated as already
    cleaned up, not an error: the DB row is the source of truth for
    document/course deletion, and this cleanup step must never raise --
    callers always run it *after* their own DB change has already
    committed, so a filesystem failure here must not look like the deletion
    itself failed.
    """
    try:
        resolved_root = storage_root.resolve()
        file_path = Path(stored_path).resolve()
    except OSError:
        logger.warning("Depolanan dosya yolu çözümlenemedi: %s", stored_path)
        return

    if not file_path.is_relative_to(resolved_root):
        logger.warning(
            "Silinecek dosya storage kök dizini dışında, atlanıyor: %s",
            file_path,
        )
        return

    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        logger.warning(
            "Fiziksel dosya silinemedi: %s", file_path, exc_info=True
        )
