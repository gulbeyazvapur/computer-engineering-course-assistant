from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from app.core.exceptions import PdfTextExtractionError


def extract_pdf_text(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        page_texts: list[str] = []

        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                page_texts.append(text.strip())

        combined = "\n\n".join(page_texts).strip()
        if not combined:
            raise PdfTextExtractionError()

        return combined
    except PdfTextExtractionError:
        raise
    except Exception as exc:
        raise PdfTextExtractionError() from exc
