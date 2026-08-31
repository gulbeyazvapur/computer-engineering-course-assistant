from __future__ import annotations

import re

from app.core.config import settings


# A short, standalone line that doesn't end like a sentence fragment (no
# trailing '.', '?', '!', ':', ',', ';', ')') is very commonly a section
# title in generated / academic course material -- numbered ("1. Title") or
# not ("Stack ve Queue", "Encapsulation"). Ordinary body text, by contrast,
# almost always either runs well past this length (PDF line-wrap width is
# typically 80-95 characters for this kind of document) or, when a line
# happens to be short, ends the sentence/clause it's wrapping and therefore
# ends in one of the excluded punctuation marks. Treating such a line as a
# forced paragraph boundary lets chunking recover per-topic structure even
# when the PDF's actual paragraph gaps were lost during text extraction
# (see _split_into_paragraphs) -- and it's a purely structural/formatting
# signal, not tied to any specific document's vocabulary.
_MIN_HEADING_LINE_LENGTH = 4
_MAX_HEADING_LINE_LENGTH = 60
_HEADING_TRAILING_PUNCTUATION = ".!?:,;)"


def _looks_like_heading(line: str) -> bool:
    if not (_MIN_HEADING_LINE_LENGTH <= len(line) <= _MAX_HEADING_LINE_LENGTH):
        return False
    if line[-1] in _HEADING_TRAILING_PUNCTUATION:
        return False
    if line.isdigit():
        return False
    return True


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _group_by_heading(part: str) -> list[str]:
    """Splits one text block into groups, forcing a new group to start
    before any line that looks like a section heading."""
    groups: list[str] = []
    current: list[str] = []

    for line in part.splitlines():
        stripped = line.strip()
        if current and _looks_like_heading(stripped):
            groups.append("\n".join(current).strip())
            current = []
        current.append(line)

    if current:
        groups.append("\n".join(current).strip())

    return [g for g in groups if g]


def _split_into_paragraphs(text: str) -> list[str]:
    """Splits normalized text into logical paragraph-like units.

    PDF text extraction is inconsistent about preserving blank lines: some
    documents keep a blank line between every paragraph, others (commonly,
    single-page documents, or documents where the extractor only inserts a
    gap between pages) produce none at all -- in which case a naive
    blank-line split would return the entire document, or a whole page, as
    one "paragraph" spanning many unrelated topics.

    Handles that in two layers, applied in this order so a heading found
    inside an otherwise-unbroken blob is not lost to the line-fallback:
      1. Split on blank lines, then break each resulting part further
         before any line that looks like a section heading (see
         _looks_like_heading) -- a generic structural signal, not tied to
         any document's specific vocabulary.
      2. Only if that still leaves the whole (single-part) document as one
         unbroken unit -- no blank lines and no heading lines found
         anywhere -- fall back to one paragraph per non-empty line, so
         chunk_text's size budget is the last line of defense rather than
         the whole document being one atomic paragraph.
    """
    normalized = normalize_text(text)
    if not normalized:
        return []

    blank_parts = [
        part.strip()
        for part in re.split(r"\n\s*\n", normalized)
        if part.strip()
    ]

    source_parts = blank_parts if len(blank_parts) > 1 else [normalized]

    paragraphs: list[str] = []
    for part in source_parts:
        paragraphs.extend(_group_by_heading(part))

    if len(paragraphs) == 1 and len(source_parts) == 1:
        lines = [line.strip() for line in paragraphs[0].splitlines() if line.strip()]
        if len(lines) > 1:
            paragraphs = lines

    return paragraphs


def _split_oversized_paragraph(paragraph: str, max_chars: int) -> list[str]:
    """Splits a single paragraph that exceeds max_chars into smaller pieces,
    accumulating whole lines up to the budget. A single line longer than
    max_chars (rare) is hard-sliced as a last resort so no piece ever
    exceeds the budget."""
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]

    pieces: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        added_len = len(line) + (1 if current else 0)
        if current and current_len + added_len > max_chars:
            pieces.append("\n".join(current))
            current = []
            current_len = 0

        if len(line) > max_chars:
            for start in range(0, len(line), max_chars):
                pieces.append(line[start : start + max_chars])
            continue

        current.append(line)
        current_len += len(line) + (1 if len(current) > 1 else 0)

    if current:
        pieces.append("\n".join(current))

    return pieces


def chunk_text(
    text: str,
    max_chars: int | None = None,
) -> list[dict]:
    """Paragraph-aware, size-bounded chunking: each chunk holds one or more
    whole paragraphs (never splitting one mid-sentence) up to max_chars,
    except a single paragraph longer than the budget on its own, which is
    divided into safe sub-pieces along line boundaries. This keeps each
    chunk close to a single sub-topic instead of the whole document being
    quantized into a handful of oversized, multi-topic blocks."""
    budget = max_chars or settings.chunk_max_chars

    paragraphs = _split_into_paragraphs(text)

    units: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= budget:
            units.append(paragraph)
        else:
            units.extend(_split_oversized_paragraph(paragraph, budget))

    contents: list[str] = []
    current: list[str] = []
    current_len = 0

    for unit in units:
        added_len = len(unit) + (2 if current else 0)
        if current and current_len + added_len > budget:
            contents.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(unit)
        current_len += len(unit) + (2 if len(current) > 1 else 0)

    if current:
        contents.append("\n\n".join(current))

    return [
        {"chunk_index": index, "content": content}
        for index, content in enumerate(contents)
        if content
    ]
