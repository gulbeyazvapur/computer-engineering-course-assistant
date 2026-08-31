from __future__ import annotations

import pytest

from app.core.config import settings
from app.core.exceptions import EmbeddingError, LLMError, NoDocumentsError
from app.services import course_service, rag_service


def test_fallback_answer_matches_required_exact_text():
    """The public fallback sentence must match the exact wording required by
    the grounding contract (and already required verbatim of the LLM by
    prompt_service.SYSTEM_PROMPT) -- not a paraphrase of it."""
    assert rag_service.FALLBACK_ANSWER == (
        "Bu bilgi yüklenen ders materyallerinde bulunmuyor."
    )


def test_rag_does_not_call_llm_when_no_chunks_pass_evidence_threshold(
    isolated_db, monkeypatch
):
    """When retrieval finds no chunk meeting the relevance threshold (e.g. a
    question entirely unrelated to the course material), the chat model must
    not be invoked at all -- both for correctness (nothing to ground an
    answer on) and to avoid an unnecessary GPU load/generation cost."""
    course = course_service.create_course("İşletim Sistemleri", None)
    generation_called = False
    evidence_check_called = False

    def fake_generate_answer(messages):
        nonlocal generation_called
        generation_called = True
        return "Cevap"

    def fake_check_evidence(messages):
        nonlocal evidence_check_called
        evidence_check_called = True
        return True

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: [],
    )
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", fake_check_evidence
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)

    result = rag_service.answer_question("Alakasız bir soru", course["id"])

    assert generation_called is False
    assert evidence_check_called is False
    assert result["answer"] == rag_service.FALLBACK_ANSWER
    assert result["sources"] == []


def test_rag_returns_fallback_when_no_relevant_chunks(isolated_db, monkeypatch):
    course = course_service.create_course("İşletim Sistemleri", None)

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: [],
    )

    result = rag_service.answer_question(
        "Ders materyalinde olmayan bir şey",
        course["id"],
    )

    assert result["sources"] == []
    assert "materyallerinde" in result["answer"]


def test_rag_returns_sources(isolated_db, monkeypatch):
    course = course_service.create_course("İşletim Sistemleri", None)

    chunks = [
        {
            "document_name": "Deadlock.pdf",
            "chunk_index": 2,
            "content": "Deadlock bilgisi",
            "score": 0.9,
        }
    ]

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: chunks,
    )
    monkeypatch.setattr(
        rag_service.llm_service,
        "check_evidence_sufficiency",
        lambda messages: True,
    )
    monkeypatch.setattr(
        rag_service.llm_service,
        "generate_answer",
        lambda messages: "Test cevabı",
    )

    result = rag_service.answer_question("Deadlock nedir?", course["id"])

    assert result["answer"] == "Test cevabı"
    assert result["sources"] == [
        {"documentName": "Deadlock.pdf", "chunkIndex": 2}
    ]


def test_rag_calls_generation_when_evidence_sufficient(isolated_db, monkeypatch):
    """A. A YETERLI/True evidence verdict must lead to the real answer
    generation being called, in that order."""
    course = course_service.create_course("İşletim Sistemleri", None)
    call_order: list[str] = []
    chunks = [
        {
            "document_name": "Deadlock.pdf",
            "chunk_index": 0,
            "content": "İçerik",
            "score": 0.9,
        }
    ]

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: chunks,
    )
    monkeypatch.setattr(
        rag_service.llm_service,
        "check_evidence_sufficiency",
        lambda messages: (call_order.append("evidence_check"), True)[1],
    )
    monkeypatch.setattr(
        rag_service.llm_service,
        "generate_answer",
        lambda messages: (call_order.append("generation"), "Cevap")[1],
    )

    result = rag_service.answer_question("Deadlock nedir?", course["id"])

    assert call_order == ["evidence_check", "generation"]
    assert result["answer"] == "Cevap"


def test_rag_returns_fallback_and_skips_generation_when_evidence_insufficient(
    isolated_db, monkeypatch
):
    """B. A YETERSIZ/False evidence verdict must return the exact fallback
    sentence and must never call the real (expensive) answer generation."""
    course = course_service.create_course("İşletim Sistemleri", None)
    generation_called = False
    chunks = [
        {
            "document_name": "Deadlock.pdf",
            "chunk_index": 0,
            "content": "İçerik",
            "score": 0.9,
        }
    ]

    def fake_generate_answer(messages):
        nonlocal generation_called
        generation_called = True
        return "Cevap"

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: chunks,
    )
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", lambda messages: False
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)

    result = rag_service.answer_question(
        "Bir sürecin yaşam döngüsü durumları nelerdir?", course["id"]
    )

    assert generation_called is False
    assert result["answer"] == rag_service.FALLBACK_ANSWER
    assert result["sources"] == [{"documentName": "Deadlock.pdf", "chunkIndex": 0}]


def test_rag_propagates_error_when_evidence_check_raises(isolated_db, monkeypatch):
    """D. A genuine failure inside the evidence check must propagate as a
    proper error (no crash, no state corruption) and must not fall through
    to generation."""
    course = course_service.create_course("İşletim Sistemleri", None)
    generation_called = False
    chunks = [
        {
            "document_name": "Deadlock.pdf",
            "chunk_index": 0,
            "content": "İçerik",
            "score": 0.9,
        }
    ]

    def fake_generate_answer(messages):
        nonlocal generation_called
        generation_called = True
        return "Cevap"

    def raising_check(messages):
        raise LLMError("simulated failure")

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: chunks,
    )
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", raising_check
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)

    with pytest.raises(LLMError):
        rag_service.answer_question("Deadlock nedir?", course["id"])

    assert generation_called is False

    # The lock must be released even after the exception -- a following
    # request must still work normally.
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", lambda messages: True
    )
    result = rag_service.answer_question("Deadlock nedir?", course["id"])
    assert result["answer"] == "Cevap"
    assert generation_called is True


def _two_chunks():
    return [
        {
            "document_name": "notes.pdf",
            "chunk_index": 0,
            "content": "Birinci parça",
            "score": 0.9,
        },
        {
            "document_name": "notes.pdf",
            "chunk_index": 1,
            "content": "İkinci parça",
            "score": 0.8,
        },
    ]


def test_rag_bypasses_evidence_gate_with_two_chunks(isolated_db, monkeypatch):
    """D. Real testing against phi-4-mini showed the evidence classifier is
    unreliable once a second chunk is added to its context (it can flip a
    demonstrably answerable question to YETERSIZ with no clean, addressable
    pattern). Since TOP_K commonly returns 2+ chunks, the classifier must be
    skipped entirely in that case -- generation runs directly, guarded only
    by SYSTEM_PROMPT's existing grounding rules (unchanged from before the
    evidence-gate work)."""
    course = course_service.create_course("İşletim Sistemleri", None)
    evidence_calls = 0
    generation_calls = 0

    def fake_check_evidence(messages):
        nonlocal evidence_calls
        evidence_calls += 1
        return True

    def fake_generate_answer(messages):
        nonlocal generation_calls
        generation_calls += 1
        return "Cevap"

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: _two_chunks(),
    )
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", fake_check_evidence
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)

    result = rag_service.answer_question("Soru", course["id"])

    assert evidence_calls == 0
    assert generation_calls == 1
    assert result["answer"] == "Cevap"


def test_rag_bypasses_evidence_gate_with_three_chunks(isolated_db, monkeypatch):
    """E. Same bypass rule for 3 chunks -- the routing criterion is purely
    len(chunks) == 1 vs. more, not a specific count."""
    course = course_service.create_course("İşletim Sistemleri", None)
    evidence_calls = 0
    generation_calls = 0

    three_chunks = _two_chunks() + [
        {
            "document_name": "notes.pdf",
            "chunk_index": 2,
            "content": "Üçüncü parça",
            "score": 0.7,
        }
    ]

    def fake_check_evidence(messages):
        nonlocal evidence_calls
        evidence_calls += 1
        return True

    def fake_generate_answer(messages):
        nonlocal generation_calls
        generation_calls += 1
        return "Cevap"

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: three_chunks,
    )
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", fake_check_evidence
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)

    result = rag_service.answer_question("Soru", course["id"])

    assert evidence_calls == 0
    assert generation_calls == 1
    assert result["answer"] == "Cevap"


def test_rag_multi_chunk_returns_generation_fallback_text_unchanged(
    isolated_db, monkeypatch
):
    """F. With 2+ chunks the evidence gate is bypassed, so if the grounded
    generation call itself decides (via SYSTEM_PROMPT's own rules) that the
    material is insufficient and produces the exact fallback sentence,
    rag_service must return that answer unchanged -- no extra gate, no
    second-guessing, no rewriting."""
    course = course_service.create_course("İşletim Sistemleri", None)
    evidence_calls = 0

    def fake_check_evidence(messages):
        nonlocal evidence_calls
        evidence_calls += 1
        return True

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: _two_chunks(),
    )
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", fake_check_evidence
    )
    monkeypatch.setattr(
        rag_service.llm_service,
        "generate_answer",
        lambda messages: rag_service.FALLBACK_ANSWER,
    )

    result = rag_service.answer_question("Soru", course["id"])

    assert evidence_calls == 0
    assert result["answer"] == rag_service.FALLBACK_ANSWER


def _fake_swap_provider(call_order=None, chat_unload_ok=True, embedding_unload_ok=True):
    """A minimal stand-in for foundry_provider that tracks unload_model()
    calls per alias (in a shared cache dict, like the real one) and lets
    tests force either unload to fail without touching real GPU/SDK state."""

    class _Fake:
        def __init__(self):
            self._models = {
                settings.chat_model_name: object(),
                settings.embedding_model_name: object(),
            }

        def unload_model(self, alias):
            if call_order is not None:
                call_order.append(f"unload_{alias}")
            ok = (
                chat_unload_ok
                if alias == settings.chat_model_name
                else embedding_unload_ok
            )
            if ok:
                self._models.pop(alias, None)
            return ok

    return _Fake()


def test_rag_unloads_chat_model_before_retrieval_and_embedding_after(
    isolated_db, monkeypatch
):
    """B, C, D, F. Full GPU swap order must be exactly: chat unload ->
    retrieval -> embedding unload -> evidence check -> generation, with no
    extra unload/reload between the evidence check and generation (both run
    against the same resident chat model). The chat and embedding models
    must never both be GPU-resident during a chat request."""
    course = course_service.create_course("İşletim Sistemleri", None)
    call_order: list[str] = []

    chunks = [
        {
            "document_name": "Deadlock.pdf",
            "chunk_index": 2,
            "content": "Deadlock bilgisi",
            "score": 0.9,
        }
    ]

    def fake_get_top_chunks(question, course_id):
        call_order.append("retrieval")
        return chunks

    def fake_check_evidence(messages):
        call_order.append("evidence_check")
        return True

    def fake_generate_answer(messages):
        call_order.append("generation")
        return "Test cevabı"

    fake_provider = _fake_swap_provider(call_order)

    monkeypatch.setattr(
        rag_service.retrieval_service, "get_top_chunks", fake_get_top_chunks
    )
    monkeypatch.setattr(rag_service, "foundry_provider", fake_provider)
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", fake_check_evidence
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)

    rag_service.answer_question("Deadlock nedir?", course["id"])

    assert call_order == [
        f"unload_{settings.chat_model_name}",
        "retrieval",
        f"unload_{settings.embedding_model_name}",
        "evidence_check",
        "generation",
    ]


def test_rag_multi_chunk_swap_order_skips_evidence_check_step(
    isolated_db, monkeypatch
):
    """Multi-chunk GPU swap order must be: chat unload -> retrieval ->
    embedding unload -> generation, with no evidence_check step and no
    extra model load/unload introduced by the bypass."""
    course = course_service.create_course("İşletim Sistemleri", None)
    call_order: list[str] = []

    def fake_get_top_chunks(question, course_id):
        call_order.append("retrieval")
        return _two_chunks()

    def fake_check_evidence(messages):
        call_order.append("evidence_check")
        return True

    def fake_generate_answer(messages):
        call_order.append("generation")
        return "Cevap"

    fake_provider = _fake_swap_provider(call_order)

    monkeypatch.setattr(
        rag_service.retrieval_service, "get_top_chunks", fake_get_top_chunks
    )
    monkeypatch.setattr(rag_service, "foundry_provider", fake_provider)
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", fake_check_evidence
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)

    rag_service.answer_question("Soru", course["id"])

    assert call_order == [
        f"unload_{settings.chat_model_name}",
        "retrieval",
        f"unload_{settings.embedding_model_name}",
        "generation",
    ]


def test_rag_swap_lifecycle_repeats_identically_on_second_request(
    isolated_db, monkeypatch
):
    """E. The exact same swap sequence must repeat, unchanged, on a second
    request in the same process -- the lifecycle is not a one-time/startup
    thing."""
    course = course_service.create_course("İşletim Sistemleri", None)
    call_order: list[str] = []

    chunks = [
        {
            "document_name": "Deadlock.pdf",
            "chunk_index": 0,
            "content": "İçerik",
            "score": 0.9,
        }
    ]

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: (call_order.append("retrieval"), chunks)[1],
    )
    monkeypatch.setattr(
        rag_service.llm_service,
        "check_evidence_sufficiency",
        lambda messages: (call_order.append("evidence_check"), True)[1],
    )
    monkeypatch.setattr(
        rag_service.llm_service,
        "generate_answer",
        lambda messages: (call_order.append("generation"), "Cevap")[1],
    )
    fake_provider = _fake_swap_provider(call_order)
    monkeypatch.setattr(rag_service, "foundry_provider", fake_provider)

    rag_service.answer_question("Soru 1", course["id"])
    rag_service.answer_question("Soru 2", course["id"])

    expected_cycle = [
        f"unload_{settings.chat_model_name}",
        "retrieval",
        f"unload_{settings.embedding_model_name}",
        "evidence_check",
        "generation",
    ]
    assert call_order == expected_cycle + expected_cycle


def test_rag_chat_model_unaffected_by_embedding_unload(isolated_db, monkeypatch):
    """F. Unloading the embedding model must never touch the chat model's
    cache entry -- swapping one direction must not corrupt the other."""
    course = course_service.create_course("İşletim Sistemleri", None)

    chunks = [
        {
            "document_name": "Deadlock.pdf",
            "chunk_index": 0,
            "content": "İçerik",
            "score": 0.9,
        }
    ]
    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: chunks,
    )
    monkeypatch.setattr(
        rag_service.llm_service, "check_evidence_sufficiency", lambda messages: True
    )
    monkeypatch.setattr(
        rag_service.llm_service, "generate_answer", lambda messages: "Cevap"
    )
    fake_provider = _fake_swap_provider()
    monkeypatch.setattr(rag_service, "foundry_provider", fake_provider)

    rag_service.answer_question("Soru", course["id"])

    # Chat was unloaded (step 1) and never reloaded within this fake, so it's
    # gone from the cache -- but the embedding unload (step 2) must not have
    # raised or otherwise disturbed that independently of its own alias.
    assert settings.chat_model_name not in fake_provider._models
    assert settings.embedding_model_name not in fake_provider._models


def test_rag_raises_embedding_error_when_chat_unload_fails(isolated_db, monkeypatch):
    """Failure safety A: if the chat model won't unload, refuse to proceed
    to the embedding load rather than risk both models GPU-resident at once
    (the exact CUDA OOM / native-crash scenario being guarded against)."""
    course = course_service.create_course("İşletim Sistemleri", None)
    retrieval_called = False

    def fake_get_top_chunks(question, course_id):
        nonlocal retrieval_called
        retrieval_called = True
        return []

    monkeypatch.setattr(
        rag_service.retrieval_service, "get_top_chunks", fake_get_top_chunks
    )
    fake_provider = _fake_swap_provider(chat_unload_ok=False)
    monkeypatch.setattr(rag_service, "foundry_provider", fake_provider)

    with pytest.raises(EmbeddingError):
        rag_service.answer_question("Deadlock nedir?", course["id"])

    assert retrieval_called is False


def test_rag_raises_llm_error_when_embedding_unload_fails_and_chunks_found(
    isolated_db, monkeypatch
):
    """Failure safety C: if chunks were found (so generation is about to
    happen) but the embedding model won't unload, refuse to load the chat
    model rather than risk both resident at once."""
    course = course_service.create_course("İşletim Sistemleri", None)
    chunks = [
        {
            "document_name": "Deadlock.pdf",
            "chunk_index": 0,
            "content": "İçerik",
            "score": 0.9,
        }
    ]
    generation_called = False

    def fake_generate_answer(messages):
        nonlocal generation_called
        generation_called = True
        return "Cevap"

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: chunks,
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)
    fake_provider = _fake_swap_provider(embedding_unload_ok=False)
    monkeypatch.setattr(rag_service, "foundry_provider", fake_provider)

    with pytest.raises(LLMError):
        rag_service.answer_question("Deadlock nedir?", course["id"])

    assert generation_called is False


def test_rag_does_not_raise_when_embedding_unload_fails_but_no_chunks_found(
    isolated_db, monkeypatch
):
    """No chat reload is about to happen on the fallback (no-chunks) path,
    so a failed embedding unload there is not a crash risk and must not
    surface as an error -- matches the pre-swap fallback behavior."""
    course = course_service.create_course("İşletim Sistemleri", None)

    monkeypatch.setattr(
        rag_service.retrieval_service,
        "get_top_chunks",
        lambda question, course_id: [],
    )
    fake_provider = _fake_swap_provider(embedding_unload_ok=False)
    monkeypatch.setattr(rag_service, "foundry_provider", fake_provider)

    result = rag_service.answer_question("Ders materyalinde olmayan bir şey", course["id"])

    assert result["sources"] == []
    assert "materyallerinde" in result["answer"]


def test_rag_state_not_corrupted_when_retrieval_raises(isolated_db, monkeypatch):
    """H. If retrieval itself raises after the chat model was already
    unloaded, the exception must propagate unchanged (not be swallowed or
    converted), the embedding-unload/generation steps must never run, and
    no extra unload attempt should occur beyond the one already made for the
    chat model."""
    course = course_service.create_course("İşletim Sistemleri", None)
    call_order: list[str] = []

    def fake_get_top_chunks(question, course_id):
        call_order.append("retrieval")
        raise NoDocumentsError()

    generation_called = False

    def fake_generate_answer(messages):
        nonlocal generation_called
        generation_called = True
        return "Cevap"

    monkeypatch.setattr(
        rag_service.retrieval_service, "get_top_chunks", fake_get_top_chunks
    )
    monkeypatch.setattr(rag_service.llm_service, "generate_answer", fake_generate_answer)
    fake_provider = _fake_swap_provider(call_order)
    monkeypatch.setattr(rag_service, "foundry_provider", fake_provider)

    with pytest.raises(NoDocumentsError):
        rag_service.answer_question("Deadlock nedir?", course["id"])

    assert call_order == [f"unload_{settings.chat_model_name}", "retrieval"]
    assert generation_called is False
