from app.services.chunking_service import chunk_text, normalize_text


def test_normalize_text():
    text = "A   B\r\n\r\n\r\nC"
    assert normalize_text(text) == "A B\n\nC"


def test_chunk_text_groups_short_paragraphs_up_to_budget():
    text = "P1\n\nP2\n\nP3\n\nP4\n\nP5"

    chunks = chunk_text(text, max_chars=6)

    assert [item["chunk_index"] for item in chunks] == [0, 1, 2]
    assert chunks[0]["content"] == "P1\n\nP2"
    assert chunks[1]["content"] == "P3\n\nP4"
    assert chunks[2]["content"] == "P5"


def test_chunk_text_never_exceeds_budget_when_paragraphs_fit_individually():
    text = "\n\n".join(f"Paragraf numara {i} biraz metin icerir." for i in range(10))

    chunks = chunk_text(text, max_chars=80)

    assert all(len(c["content"]) <= 80 for c in chunks)
    assert len(chunks) > 1


def test_chunk_text_splits_oversized_paragraph_along_line_boundaries():
    """A single paragraph longer than max_chars must be divided into safe
    sub-pieces instead of becoming one oversized, multi-topic chunk (the
    exact real-world failure this chunker replaces: PDF text extraction
    often yields one giant multi-topic 'paragraph' per page)."""
    long_paragraph = "\n".join(f"Bu {i}. satirdir ve biraz icerik tasir." for i in range(20))

    chunks = chunk_text(long_paragraph, max_chars=100)

    assert len(chunks) > 1
    assert all(len(c["content"]) <= 100 for c in chunks)
    # No line's content is lost or duplicated across the split.
    rejoined = "\n".join(c["content"] for c in chunks)
    for i in range(20):
        assert f"Bu {i}. satirdir" in rejoined


def test_chunk_text_hard_slices_a_single_line_longer_than_budget():
    """Last-resort safety net: even a single line with no whitespace to
    break on must never produce a chunk larger than max_chars."""
    long_line = "x" * 250

    chunks = chunk_text(long_line, max_chars=100)

    assert len(chunks) == 3
    assert all(len(c["content"]) <= 100 for c in chunks)
    assert "".join(c["content"] for c in chunks) == long_line


def test_chunk_text_empty():
    assert chunk_text("   ") == []


def test_chunk_text_falls_back_to_lines_when_no_blank_line_paragraphs():
    """Common for single-page PDF extractions: no blank lines exist at all,
    so the whole text would otherwise be treated as one paragraph."""
    text = "\n".join(f"Satir {i} icerik." for i in range(6))

    chunks = chunk_text(text, max_chars=40)

    assert len(chunks) > 1
    assert all(len(c["content"]) <= 40 for c in chunks)


def test_chunk_text_breaks_before_numbered_heading_lines():
    """Generic structural signal (independent of any course's vocabulary):
    a short, standalone 'N. Title' line is treated as a forced paragraph
    boundary, recovering per-topic structure from a page-sized blob that
    has no blank lines at all -- the actual root cause found on the
    İşletim Sistemleri PDF, where a whole page (multiple unrelated topics)
    extracted as a single blank-line-delimited 'paragraph'."""
    page_blob = (
        "1. Konu Bir\n"
        "Konu bir hakkinda aciklama metni burada yer alir.\n"
        "2. Konu Iki\n"
        "Konu iki hakkinda tamamen farkli bir aciklama metni."
    )

    # max_chars small enough that the two heading-delimited paragraphs
    # cannot both fit in one chunk (each fits comfortably alone), so the
    # heading boundary -- not just the size budget -- is what's on test.
    chunks = chunk_text(page_blob, max_chars=65)

    assert len(chunks) == 2
    assert chunks[0]["content"].startswith("1. Konu Bir")
    assert chunks[1]["content"].startswith("2. Konu Iki")
    assert "Konu iki" not in chunks[0]["content"]
    assert "Konu bir" not in chunks[1]["content"]


def test_chunk_text_breaks_before_plain_untitled_heading_lines():
    """Many real course documents use short plain-text section titles with
    no numbering at all (e.g. 'Stack ve Queue', 'Encapsulation') -- these
    must be recognized as topic boundaries too, not just the numbered
    convention. This is the exact regression found on the real
    'Veri Yapıları ve Algoritmalar' PDF, where four unrelated topics (Dizi
    ve Bağlı Liste, Stack ve Queue, Ağaçlar, Hash Table) were merged into
    one chunk because none of the headings were numbered."""
    page_blob = (
        "Konu Bir\n"
        "Konu bir hakkinda aciklama metni burada yer alir.\n"
        "Konu Iki\n"
        "Konu iki hakkinda tamamen farkli bir aciklama metni."
    )

    chunks = chunk_text(page_blob, max_chars=65)

    assert len(chunks) == 2
    assert chunks[0]["content"].startswith("Konu Bir")
    assert chunks[1]["content"].startswith("Konu Iki")
    assert "Konu iki" not in chunks[0]["content"]


def test_chunk_text_does_not_treat_wrapped_body_line_as_heading():
    """A line that is really a (PDF line-wrap width, i.e. long) body
    sentence must not be mistaken for a heading just because a paragraph
    happens to have no blank-line gap around it -- length is the primary
    signal, since real body lines from PDF extraction typically run close
    to the page's line-wrap width, well past a short title's length."""
    text = (
        "Baslik\n"
        "Bu oldukca uzun bir aciklama cumlesidir ve gercek bir PDF satirinin "
        "tipik genisligine yakin bir uzunluktadir boylece\n"
        "yayilir, ancak sonunda noktalama isareti bulunur.\n"
        "Devam eden ayri bir cumle burada baslar."
    )

    chunks = chunk_text(text, max_chars=1000)

    assert len(chunks) == 1
    assert "Devam eden ayri bir cumle" in chunks[0]["content"]


def test_chunk_text_does_not_break_on_heading_like_line_that_is_too_long():
    """The heading heuristic only fires on short, heading-shaped lines --
    an ordinary sentence that happens to start with a number must not be
    mistaken for a section heading."""
    text = (
        "1. Bu cumle bir baslik degildir, sadece rakamla baslayan ve olduka "
        "uzun olan normal bir cumledir ve boluttme tetiklememelidir.\n"
        "Devam eden ikinci satir."
    )

    chunks = chunk_text(text, max_chars=1000)

    assert len(chunks) == 1


def test_chunk_text_preserves_turkish_characters():
    text = "İşletim sistemi süreçleri oluşturur, zamanlar, bekletir ve sonlandırır."

    chunks = chunk_text(text, max_chars=1000)

    assert len(chunks) == 1
    assert chunks[0]["content"] == text


def test_chunk_text_is_deterministic():
    text = "\n\n".join(f"Paragraf {i}." for i in range(15))

    first = chunk_text(text, max_chars=50)
    second = chunk_text(text, max_chars=50)

    assert first == second


def test_chunk_text_chunk_index_is_sequential():
    text = "\n\n".join(f"Paragraf {i} ile biraz daha metin." for i in range(8))

    chunks = chunk_text(text, max_chars=60)

    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))
