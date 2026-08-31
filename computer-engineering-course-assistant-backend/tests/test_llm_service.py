from __future__ import annotations

import time
from pathlib import Path

import pytest

from app.core.exceptions import LLMError
from app.services import llm_service


_FIXTURES_DIR = Path(__file__).parent / "fixtures"


class _FakeDelta:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.delta = _FakeDelta(content)


class _FakeChunk:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeSettings:
    def __init__(self):
        self.temperature = None
        self.max_tokens = None


class _FakeChatClient:
    def __init__(self, response_text):
        self._response_text = response_text
        self.settings = _FakeSettings()

    def complete_streaming_chat(self, messages):
        yield _FakeChunk(self._response_text)


class _RaisingChatClient:
    def complete_streaming_chat(self, messages):
        raise RuntimeError("native runtime failure")


class _FakeModel:
    def __init__(self, client):
        self._client = client

    def get_chat_client(self):
        return self._client


class _FakeProvider:
    def __init__(self, client):
        self._client = client

    def get_loaded_model(self, alias):
        return _FakeModel(self._client)


def _run_check(monkeypatch, response_text=None, client=None):
    fake_client = client if client is not None else _FakeChatClient(response_text)
    monkeypatch.setattr(llm_service, "foundry_provider", _FakeProvider(fake_client))
    return llm_service.check_evidence_sufficiency(
        [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
    )


def test_check_evidence_sufficiency_true_for_yeterli(monkeypatch):
    """A. A clean YETERLI verdict resolves to sufficient=True."""
    assert _run_check(monkeypatch, "YETERLI") is True


def test_check_evidence_sufficiency_false_for_yetersiz(monkeypatch):
    """B. A clean YETERSIZ verdict resolves to sufficient=False."""
    assert _run_check(monkeypatch, "YETERSIZ") is False


def test_check_evidence_sufficiency_accepts_json_true(monkeypatch):
    assert _run_check(monkeypatch, '{"sufficient": true}') is True


def test_check_evidence_sufficiency_accepts_json_false(monkeypatch):
    assert _run_check(monkeypatch, '{"sufficient": false}') is False


def test_check_evidence_sufficiency_is_case_and_diacritic_insensitive(monkeypatch):
    assert _run_check(monkeypatch, "yeterli") is True
    assert _run_check(monkeypatch, "YETERLİ") is True
    assert _run_check(monkeypatch, "yetersiz") is False
    assert _run_check(monkeypatch, "YETERSİZ") is False


@pytest.mark.parametrize(
    "garbage",
    ["", "   ", "bilmiyorum", "Bu konuda emin değilim.", "Evet", "42"],
)
def test_check_evidence_sufficiency_fails_closed_on_unparseable_output(
    monkeypatch, garbage
):
    """C. Any output that isn't an unambiguous positive verdict (empty, free
    text, or otherwise unparseable) must resolve to insufficient -- this
    function must never fail open."""
    assert _run_check(monkeypatch, garbage) is False


def test_check_evidence_sufficiency_propagates_llm_error_on_exception(monkeypatch):
    """D. A genuine runtime/client failure during the evidence check must
    surface as a proper LLMError (existing error-handling contract), not be
    silently swallowed into a false verdict and not crash the process."""
    with pytest.raises(LLMError):
        _run_check(monkeypatch, client=_RaisingChatClient())


# ---------------------------------------------------------------------------
# Repetition guard (_clean_repetitive_output)
#
# All "normal answer" fixtures below are verbatim real phi-4-mini outputs
# captured from this project's own running backend (not hand-written), so
# these tests double as a real-answer regression suite: if the guard ever
# starts trimming any of them, that's a false positive on genuine model
# output, not a hypothetical.
# ---------------------------------------------------------------------------

_REAL_STACK_QUEUE_ANSWER = (
    "Stack ve Queue arasındaki temel fark, çalışma prensipleridir. Stack, "
    "LIFO (Son Eklenen İlk Çıkartılan) prensibine göre çalışır, bu da son "
    "eklenen elemanı ilk çıkaracağınız anlamına gelir. Öte yandan, Queue, "
    "FIFO (İlk Eklenen İlk Çıkartılan) prensibine göre çalışır, bu da ilk "
    "eklenen elemanı ilk çıkaracağınız anlamına gelir. Stack fonksiyon "
    "çağrıları ve geri alma işlemlerinde, Queue ise görev sıralama ve BFS "
    "gibi algoritmalarda kullanılır."
)

_REAL_ASTAR_ANSWER = (
    "g(n) gerçek maliyet, bir noktadan hedefe kadar en kısa yolculuğun "
    "toplam maliyetini ifade eder. h(n) ise hedefe kalan maliyetin tahmini "
    "değeridir. A* algoritması g(n) ve h(n) değerlerini birlikte "
    "değerlendirerek hedefe ulaşmak için en uygun yolu bulmak için "
    "kullanılır."
)

_REAL_AUTH_ANSWER = (
    "Authentication, kullanıcının kimliğini doğrularken, authorization "
    "doğrulanmış kullanıcının hangi kaynaklara erişebileceğini belirler."
)

_REAL_INTERRUPT_ANSWER = (
    "Interrupt, belirli bir olay oluştuğunda normal program akışını "
    "geçici olarak durdurup ISR çalıştıran bir mekanizmadır. ISR, donanım "
    "olaylarını işlemek, girişleri okumak veya belirli bir zaman diliminde "
    "görevleri gerçekleştirmek için kullanılır."
)

_REAL_DEADLOCK_ANSWER = (
    "Deadlock oluşması için gerekli dört koşul Mutual Exclusion, Hold and "
    "Wait, No Preemption ve Circular Wait'dir. Mutual Exclusion, bir "
    "kaynak aynı anda yalnızca bir süreç tarafından kullanılabilir. Hold "
    "and Wait, bir süreç en az bir kaynağı elinde tutarken başka bir "
    "kaynağı bekler. No Preemption, bir sürecin elindeki kaynak zorla "
    "alınamaz; süreç kaynağı kendisi bırakmalıdır. Circular Wait, "
    "süreçler birbirlerinin tuttuğu kaynakları döngüsel bir bekleme "
    "zinciri içinde bekler."
)


@pytest.mark.parametrize(
    "real_answer",
    [
        _REAL_STACK_QUEUE_ANSWER,
        _REAL_ASTAR_ANSWER,
        _REAL_AUTH_ANSWER,
        _REAL_INTERRUPT_ANSWER,
        _REAL_DEADLOCK_ANSWER,
    ],
)
def test_clean_repetitive_output_leaves_real_answers_untouched(real_answer):
    """A, B, C, D. Real captured phi-4-mini answers (distinct sentences,
    a numbered/enumerated list, shared terminology across sentences) must
    come back byte-for-byte identical -- none of them repeats any sentence
    three times in a row, which is the only thing this guard reacts to."""
    assert llm_service._clean_repetitive_output(real_answer) == real_answer


def test_clean_repetitive_output_leaves_fallback_untouched():
    """E. The exact fallback sentence is a single sentence -- never long
    enough to trigger the guard, and must come back unchanged regardless."""
    from app.services.rag_service import FALLBACK_ANSWER

    assert llm_service._clean_repetitive_output(FALLBACK_ANSWER) == FALLBACK_ANSWER


def test_clean_repetitive_output_removes_repeated_single_sentence():
    """F. A single sentence repeated 4x in a row: keep one, drop the rest."""
    text = "Cümle bir.\nCümle iki.\nAynı tekrar.\nAynı tekrar.\nAynı tekrar.\nAynı tekrar."
    expected = "Cümle bir.\nCümle iki.\nAynı tekrar."

    assert llm_service._clean_repetitive_output(text) == expected


def test_clean_repetitive_output_removes_repeated_two_sentence_block():
    """G. A two-sentence block repeated 3x in a row: keep one copy of the
    block, drop the rest."""
    text = (
        "Normal giriş.\n"
        "Tekrar A.\nTekrar B.\nTekrar A.\nTekrar B.\nTekrar A.\nTekrar B."
    )
    expected = "Normal giriş.\nTekrar A.\nTekrar B."

    assert llm_service._clean_repetitive_output(text) == expected


def test_clean_repetitive_output_normalizes_whitespace_before_comparing():
    """H. Irregular internal whitespace must not hide a genuine loop from
    detection -- comparison is whitespace-normalized (the kept text itself
    is still returned with its original spacing, only the removed repeats'
    spacing is irrelevant)."""
    text = "Giriş cümlesi.\nAynı cümle.\nAynı   cümle.\nAynı cümle.\nAynı  cümle."
    result = llm_service._clean_repetitive_output(text)

    assert result.startswith("Giriş cümlesi.\nAynı")
    assert result.count("Aynı") == 1


def test_clean_repetitive_output_preserves_shared_terminology():
    """I. Sentences that legitimately share vocabulary (process/thread) but
    are not themselves identical must all be kept."""
    text = (
        "Process kendi adres alanına sahiptir.\n"
        "Thread aynı process içindeki kaynakları paylaşır.\n"
        "Bir process birden fazla thread içerebilir."
    )

    assert llm_service._clean_repetitive_output(text) == text


def test_clean_repetitive_output_preserves_similar_but_distinct_items():
    """J. High surface-level similarity between two different, single-
    occurrence statements must not be mistaken for repetition."""
    text = (
        "CPU scheduling, işlemcinin hangi sürece ayrılacağını belirler.\n"
        "Disk scheduling, disk erişim isteklerinin sırasını belirler."
    )

    assert llm_service._clean_repetitive_output(text) == text


def test_clean_repetitive_output_preserves_numbered_list_with_distinct_items():
    """Four distinct enumerated items (real shape: Coffman conditions)
    sharing sentence structure/terminology must never be treated as a
    repeat of each other."""
    text = (
        "1. Mutual Exclusion: bir kaynak aynı anda yalnızca bir süreç "
        "tarafından kullanılabilir.\n"
        "2. Hold and Wait: bir süreç en az bir kaynağı elinde tutarken "
        "başka bir kaynağı bekler.\n"
        "3. No Preemption: bir sürecin elindeki kaynak zorla alınamaz.\n"
        "4. Circular Wait: süreçler birbirlerinin tuttuğu kaynakları "
        "döngüsel bir bekleme zinciri içinde bekler."
    )

    assert llm_service._clean_repetitive_output(text) == text


def test_clean_repetitive_output_real_hpa_regression_fixture():
    """The actual real repetition-loop output captured from this backend
    (course: Bulut Bilişim, question about Kubernetes HPA's CPU-based
    scaling algorithm) -- verbatim, including the mid-word truncated final
    repeat. All 3 genuinely unique paragraphs must be kept; the ~8-fold
    repeated 'HPA ayrıca / Bu mekanizma' two-sentence block must collapse
    to a single occurrence, and the trailing truncated fragment must not
    survive as leftover garbage."""
    raw = (_FIXTURES_DIR / "hpa_repetitive_raw.txt").read_text(encoding="utf-8")

    cleaned = llm_service._clean_repetitive_output(raw)

    assert len(cleaned) < len(raw)
    # The 3 genuinely unique paragraphs survive completely.
    assert "HPA'nın ölçekleme algoritması" in cleaned
    assert "HPA, pod başına CPU kullanım raporlarını toplar" in cleaned
    assert "HPA'nın ölçekleme işlemi" in cleaned
    # Only one occurrence of the looping block's opening phrase remains.
    assert cleaned.count("HPA ayrıca") == 1
    # No mid-word truncated fragment left dangling at the end.
    assert not cleaned.endswith("rap")
    assert cleaned.endswith(".")


def test_clean_repetitive_output_is_pure_cpu_string_processing_and_fast():
    """Performance: the guard must be negligible-cost local string
    processing -- no model/embedding call, no GPU interaction. Benchmarked
    against a ~10KB synthetic worst case (many short repeated sentences)."""
    raw = (_FIXTURES_DIR / "hpa_repetitive_raw.txt").read_text(encoding="utf-8")
    big_text = (raw * 4)[:10_000]

    start = time.perf_counter()
    for _ in range(20):
        llm_service._clean_repetitive_output(big_text)
    elapsed_ms = (time.perf_counter() - start) / 20 * 1000

    assert elapsed_ms < 50


def test_clean_repetitive_output_empty_and_whitespace_only():
    assert llm_service._clean_repetitive_output("") == ""
    assert llm_service._clean_repetitive_output("   ") == "   "


def test_generate_answer_applies_repetition_cleaning(monkeypatch):
    """The repetition guard runs automatically as part of generate_answer's
    existing raw-output post-processing (same spot as _strip_reasoning),
    with no extra model call: the fake client here only ever streams once."""
    raw = (_FIXTURES_DIR / "hpa_repetitive_raw.txt").read_text(encoding="utf-8")
    call_count = 0

    class _CountingClient(_FakeChatClient):
        def complete_streaming_chat(self, messages):
            nonlocal call_count
            call_count += 1
            yield from super().complete_streaming_chat(messages)

    monkeypatch.setattr(
        llm_service, "foundry_provider", _FakeProvider(_CountingClient(raw))
    )

    answer = llm_service.generate_answer(
        [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
    )

    assert call_count == 1
    assert len(answer) < len(raw)
    assert answer.count("HPA ayrıca") == 1


def test_generate_answer_does_not_alter_normal_short_answer(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "foundry_provider",
        _FakeProvider(_FakeChatClient(_REAL_AUTH_ANSWER)),
    )

    answer = llm_service.generate_answer(
        [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
    )

    assert answer == _REAL_AUTH_ANSWER


# ---------------------------------------------------------------------------
# Near-duplicate repetition guard (_clean_near_duplicate_repetition)
#
# Second, more permissive pass, run only after the exact-match guard above.
# Catches paraphrased (non-byte-identical) pathological repeats using
# difflib.SequenceMatcher. All "must stay unchanged" fixtures below are
# verbatim real phi-4-mini answers captured from this project's own running
# backend during the 49-course stress test.
# ---------------------------------------------------------------------------

_REAL_STACK_QUEUE_ANSWER_ND = (
    "Stack ve Queue arasındaki temel fark, çalışma prensipleridir. Stack, "
    "LIFO (Son Eklenen İlk Çıkartılan) prensibine göre çalışır, bu da son "
    "eklenen elemanı ilk çıkaracağınız anlamına gelir. Öte yandan, Queue, "
    "FIFO (İlk Eklenen İlk Çıkartılan) prensibine göre çalışır, bu da ilk "
    "eklenen elemanı ilk çıkaracağınız anlamına gelir. Stack fonksiyon "
    "çağrıları ve geri alma işlemlerinde, Queue ise görev sıralama ve BFS "
    "gibi algoritmalarda kullanılır."
)

_REAL_SCALING_ANSWER = (
    "Vertical scaling tek makinenin kaynaklarını artırır, horizontal "
    "scaling yeni instance'lar ekler."
)

_REAL_PROCESS_THREAD_ANSWER = (
    "Process, çalışmakta olan bir program örneğidir ve kendi adres "
    "alanına, program sayacına, register durumuna ve işletim sistemi "
    "tarafından tutulan yönetim bilgilerine sahiptir. Thread, bir süreç "
    "içindeki bağımsız yürütme akışıdır. Aynı süreçteki threadler kod, "
    "veri ve açık dosyalar gibi birçok kaynağı paylaşırken; her thread "
    "kendi program sayacına, register setine ve stack alanına sahiptir."
)


@pytest.mark.parametrize(
    "real_answer",
    [
        _REAL_STACK_QUEUE_ANSWER_ND,
        _REAL_ASTAR_ANSWER,
        _REAL_AUTH_ANSWER,
        _REAL_INTERRUPT_ANSWER,
        _REAL_DEADLOCK_ANSWER,
        _REAL_SCALING_ANSWER,
        _REAL_PROCESS_THREAD_ANSWER,
    ],
)
def test_near_duplicate_guard_leaves_real_answers_untouched(real_answer):
    """C, D, E, F + false-positive coverage. Real captured phi-4-mini
    answers -- including Stack vs. Queue and Vertical vs. Horizontal
    scaling, which deliberately share a sentence template while describing
    opposite things (measured similarity 0.875, below the 0.95 threshold)
    -- must come back byte-for-byte identical."""
    assert llm_service._clean_near_duplicate_repetition(real_answer) == real_answer


def test_near_duplicate_guard_leaves_fallback_untouched():
    """L. The exact fallback sentence must be unaffected."""
    from app.services.rag_service import FALLBACK_ANSWER

    assert (
        llm_service._clean_near_duplicate_repetition(FALLBACK_ANSWER)
        == FALLBACK_ANSWER
    )


def test_near_duplicate_guard_hpa_fixture_unchanged_after_exact_guard():
    """B, 15. The real HPA fixture, after the exact guard already cleaned
    it (2818 -> 1019 chars), must NOT be trimmed further -- even though it
    contains one legitimately-kept adjacent sentence pair that scores 0.935
    similarity (below the 0.95 threshold, and short of the 3-occurrence bar
    for single-sentence blocks either way)."""
    raw = (_FIXTURES_DIR / "hpa_repetitive_raw.txt").read_text(encoding="utf-8")
    after_exact = llm_service._clean_repetitive_output(raw)

    after_near_dup = llm_service._clean_near_duplicate_repetition(after_exact)

    assert after_near_dup == after_exact


def test_near_duplicate_guard_cleans_real_recursion_fixture():
    """A, 10. The real captured 'Recursion' answer, already passed through
    the exact guard (2617 -> 1201 chars per the server log; the 1201-char
    post-exact-guard text is the fixture here), still contains a
    paraphrased repeated block the exact guard could not see. The
    near-duplicate guard must trim it, keep the genuinely unique opening,
    and end on a complete sentence."""
    after_exact = (
        _FIXTURES_DIR / "recursion_after_exact_guard.txt"
    ).read_text(encoding="utf-8")

    cleaned = llm_service._clean_near_duplicate_repetition(after_exact)

    assert len(cleaned) < len(after_exact)
    assert cleaned.endswith(".")
    # The genuinely unique opening content survives completely.
    assert "Fonksiyonlar belirli bir işi yapan" in cleaned
    assert "Recursion (özyineleme), bir fonksiyonun kendisini çağırarak" in cleaned
    # The genuinely distinct sentence (below the 0.95 threshold against the
    # repeated pair, so correctly left standing on its own) plus the first
    # occurrence of the near-duplicate block both legitimately end this way
    # -- but the pathological *second* occurrence of that block (which
    # pushed the count to 3 in the raw answer) must be gone.
    assert cleaned.count("kendini çağırması gibi görünebilir") == 2


def test_near_duplicate_guard_requires_three_occurrences_for_single_sentence():
    """H vs. G-lite. A single sentence repeated only twice (paraphrased)
    must NOT be trimmed -- matches the exact guard's same conservative bar
    for block length 1. Three near-identical repeats must be trimmed."""
    twice = (
        "Giriş cümlesi burada yer alır ve konuyu tanıtır. "
        "Bu konu gerçekten çok önemli bir kavramdır ve dikkatle incelenmelidir. "
        "Bu konu gerçekten çok önemli bir kavramdır, dikkatle incelenmelidir."
    )
    assert llm_service._clean_near_duplicate_repetition(twice) == twice

    three_times = (
        "Giriş cümlesi burada yer alır ve konuyu tanıtır. "
        "Bu konu gerçekten çok önemli bir kavramdır ve dikkatle incelenmelidir. "
        "Bu konu gerçekten çok önemli bir kavramdır ve dikkatle incelenmelidir! "
        "Bu konu gerçekten çok önemli bir kavramdır ve dikkatle incelenmelidir."
    )
    cleaned = llm_service._clean_near_duplicate_repetition(three_times)
    assert cleaned == (
        "Giriş cümlesi burada yer alır ve konuyu tanıtır. "
        "Bu konu gerçekten çok önemli bir kavramdır ve dikkatle incelenmelidir."
    )


def test_near_duplicate_guard_ignores_very_short_sentences():
    """I. Short sentences below the minimum length must never participate
    in near-duplicate comparison, even if repeated several times, since
    short strings can coincidentally score high similarity."""
    text = "Giriş burada. Evet. Evet. Evet. Evet."
    assert llm_service._clean_near_duplicate_repetition(text) == text


def test_near_duplicate_guard_preserves_legitimate_similar_pair():
    """G. A single pair of sentences that share a template but describe
    different, legitimate things (comparable to the real Stack/Queue and
    scaling cases) must not be trimmed."""
    text = (
        "Process kendi bellek alanına sahiptir ve bağımsız olarak yönetilir. "
        "Thread kendi program sayacına sahiptir ve bağımsız olarak zamanlanır."
    )
    assert llm_service._clean_near_duplicate_repetition(text) == text


def test_near_duplicate_guard_preserves_numbered_lists():
    """12. Four distinct enumerated items sharing sentence structure and
    terminology (Coffman conditions shape) must never be treated as
    repeats of each other, matching the exact guard's own list-safety
    guarantee."""
    text = (
        "1. Mutual Exclusion: bir kaynak aynı anda yalnızca bir süreç "
        "tarafından kullanılabilir. "
        "2. Hold and Wait: bir süreç en az bir kaynağı elinde tutarken "
        "başka bir kaynağı bekler. "
        "3. No Preemption: bir sürecin elindeki kaynak zorla alınamaz. "
        "4. Circular Wait: süreçler birbirlerinin tuttuğu kaynakları "
        "döngüsel bir bekleme zinciri içinde bekler."
    )
    assert llm_service._clean_near_duplicate_repetition(text) == text


def test_near_duplicate_guard_catches_punctuation_and_whitespace_variation():
    """J. A genuinely repeated idea must still be caught even when
    punctuation or whitespace differs slightly between repeats (comparison
    is whitespace-normalized; the block-scan still requires 3 occurrences
    for a single-sentence block)."""
    text = (
        "Bu bir giriş cümlesidir ve konuyu tanıtır. "
        "Sistem   aşırı   yüklendiğinde performans belirgin şekilde düşer. "
        "Sistem aşırı yüklendiğinde performans belirgin şekilde düşer! "
        "sistem aşırı yüklendiğinde performans belirgin şekilde düşer."
    )
    cleaned = llm_service._clean_near_duplicate_repetition(text)
    assert cleaned == (
        "Bu bir giriş cümlesidir ve konuyu tanıtır. "
        "Sistem   aşırı   yüklendiğinde performans belirgin şekilde düşer."
    )


def test_near_duplicate_guard_preserves_turkish_characters():
    text = (
        "İşletim sistemi süreçleri oluşturur, zamanlar, bekletir ve "
        "sonlandırır. Çekirdek bileşenleri birbirinden farklı görevler "
        "üstlenir."
    )
    assert llm_service._clean_near_duplicate_repetition(text) == text


def test_near_duplicate_guard_empty_and_single_sentence():
    assert llm_service._clean_near_duplicate_repetition("") == ""
    assert llm_service._clean_near_duplicate_repetition("Tek cümle.") == "Tek cümle."


def test_near_duplicate_guard_is_pure_cpu_string_processing_and_fast():
    """Performance: negligible-cost local string processing, no model or
    GPU interaction. Benchmarked against the real Recursion fixture, a
    10KB synthetic normal-looking answer, and a 10KB synthetic repeated
    answer."""
    recursion = (
        _FIXTURES_DIR / "recursion_after_exact_guard.txt"
    ).read_text(encoding="utf-8")
    normal_10kb = (_REAL_DEADLOCK_ANSWER * 20)[:10_000]
    repeated_10kb = (recursion * 8)[:10_000]

    for sample in (recursion, normal_10kb, repeated_10kb):
        start = time.perf_counter()
        for _ in range(20):
            llm_service._clean_near_duplicate_repetition(sample)
        elapsed_ms = (time.perf_counter() - start) / 20 * 1000
        assert elapsed_ms < 50


def test_generate_answer_applies_near_duplicate_cleaning_after_exact_guard(
    monkeypatch,
):
    """Pipeline order: raw -> _strip_reasoning -> exact guard -> near-
    duplicate guard -> final answer, all within a single generate_answer
    call (no extra model call: the fake client streams once)."""
    after_exact = (
        _FIXTURES_DIR / "recursion_after_exact_guard.txt"
    ).read_text(encoding="utf-8")
    call_count = 0

    class _CountingClient(_FakeChatClient):
        def complete_streaming_chat(self, messages):
            nonlocal call_count
            call_count += 1
            yield from super().complete_streaming_chat(messages)

    monkeypatch.setattr(
        llm_service, "foundry_provider", _FakeProvider(_CountingClient(after_exact))
    )

    answer = llm_service.generate_answer(
        [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
    )

    assert call_count == 1
    assert len(answer) < len(after_exact)
    assert answer.count("kendini çağırması gibi görünebilir") == 2


def test_near_duplicate_guard_failure_falls_back_to_exact_guard_result(monkeypatch):
    """21. If the near-duplicate pass raises unexpectedly, generate_answer
    must keep the exact-guard-cleaned answer and return normally -- never
    surface as a 500 for an otherwise-fine answer."""
    monkeypatch.setattr(
        llm_service,
        "_clean_near_duplicate_repetition",
        lambda text: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        llm_service,
        "foundry_provider",
        _FakeProvider(_FakeChatClient(_REAL_AUTH_ANSWER)),
    )

    answer = llm_service.generate_answer(
        [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
    )

    assert answer == _REAL_AUTH_ANSWER



# ---------------------------------------------------------------------------
# Prompt/delimiter leakage guard (_clean_prompt_leakage)
#
# Runs first in the pipeline (before either repetition pass). The two real
# fixtures below are verbatim phi-4-mini outputs captured during the
# 49-course stress test -- the actual observed leak cases, not synthetic
# approximations.
# ---------------------------------------------------------------------------


def test_leak_guard_removes_full_material_and_question_echo_real_nyp_fixture():
    """21, 13. Real 'Nesne Yönelimli Programlama / SOLID' stress-test
    output: the model echoed the entire <DERS_MATERYALI> context and
    <SORU> question back verbatim before trailing into a hallucinated fake
    instruction section. Both internal blocks -- tags and everything they
    wrap -- must be gone; none of the raw retrieved chunk content or the
    <SORU>/<DERS_MATERYALI> tag literals may reach the final text."""
    raw = (_FIXTURES_DIR / "nyp_solid_leak_raw.txt").read_text(encoding="utf-8")

    cleaned = llm_service._clean_prompt_leakage(raw)

    assert "<DERS_MATERYALI>" not in cleaned
    assert "</DERS_MATERYALI>" not in cleaned
    assert "<SORU>" not in cleaned
    assert "</SORU>" not in cleaned
    # None of the raw retrieved chunk content leaked through either.
    assert "Encapsulation" not in cleaned
    assert "Polymorphism" not in cleaned
    assert "SOURCE:" not in cleaned
    assert len(cleaned) < len(raw)


def test_leak_guard_removes_garbled_tag_real_web_fixture():
    """23. Real 'Web Programlama / GraphQL' stress-test output: an
    otherwise complete, correct refusal answer followed by a garbled
    <|DERS_MATERYALI|> ... </DERS_MATERYALI> fragment. The garbled block
    must be removed and the genuinely good answer before it kept intact."""
    raw = (_FIXTURES_DIR / "web_graphql_leak_raw.txt").read_text(encoding="utf-8")

    cleaned = llm_service._clean_prompt_leakage(raw)

    assert "<|DERS_MATERYALI|>" not in cleaned
    assert "DERS_MATERYALI" not in cleaned
    assert cleaned == (
        "Web programlama, istemci-sunucu model, HTTP metotları, REST "
        "API'ler ve frontend/backend kavramları hakkında bilgi sağladığı "
        "için, soruyu yanıtlamak için gerekli bilgiyi içeriyor. Ancak, "
        "GraphQL sorgu dilinin REST'ten farkını ve resolver mekanizmasını "
        "açıklamak için gerekli ayrıntılar kaynağa dahil edilmemiştir. Bu "
        "bilgi yüklenen ders materyallerinde bulunmuyor."
    )


def test_leak_guard_removes_closed_material_block_keeps_surrounding_text():
    """21. Synthetic version of the required test: a normal answer
    opening followed by a fully-closed internal material block must keep
    the opening and drop the whole block."""
    text = (
        "Normal cevap başlangıcı.\n\n"
        "<DERS_MATERYALI>\n"
        "Internal context text...\n"
        "</DERS_MATERYALI>"
    )

    cleaned = llm_service._clean_prompt_leakage(text)

    assert cleaned == "Normal cevap başlangıcı."


def test_leak_guard_removes_question_echo_keeps_surrounding_text():
    """22. A <SORU> echo block anywhere in the output must be removed,
    with normal surrounding answer text kept."""
    text = "<SORU>\nCAP teoremi nedir?\n</SORU>\n\nNormal cevap burada."

    cleaned = llm_service._clean_prompt_leakage(text)

    assert cleaned == "Normal cevap burada."


def test_leak_guard_truncates_unclosed_material_tag():
    """The echo can be cut off by the token budget before reaching the
    closing tag -- everything from the orphaned opening tag onward must
    still be dropped, not just left dangling with a bare <DERS_MATERYALI>
    visible to the user."""
    text = (
        "Gerçek cevabın başlangıcı burada.\n\n"
        "<DERS_MATERYALI>\nKesilmiş ham bağlam metni buraya kadar"
    )

    cleaned = llm_service._clean_prompt_leakage(text)

    assert cleaned == "Gerçek cevabın başlangıcı burada."
    assert "<DERS_MATERYALI>" not in cleaned


def test_leak_guard_leaves_normal_html_content_untouched():
    """24, 36. Legitimate HTML tags a student could genuinely ask about
    must never be touched -- this guard only recognizes the two literal
    internal tag names, never a generic '<...>' pattern."""
    text = (
        "<div> bir HTML blok elementidir ve içerik gruplamak için "
        "kullanılır. <a> etiketi ise köprü (bağlantı) oluşturur."
    )
    assert llm_service._clean_prompt_leakage(text) == text


def test_leak_guard_leaves_generics_and_comparisons_untouched():
    """25. Angle brackets used for generics or numeric comparisons must
    survive unchanged."""
    text = "List<T> generic bir koleksiyondur. x < y olduğunda işlem yapılır."
    assert llm_service._clean_prompt_leakage(text) == text


def test_leak_guard_leaves_mathematical_brackets_untouched():
    """26. Square-bracket mathematical/interval notation must survive --
    this guard never touches '[...]' content at all, only the two named
    angle-bracket tags."""
    text = "Aralık [0, n-1] olarak ifade edilir ve dizinin tüm elemanlarını kapsar."
    assert llm_service._clean_prompt_leakage(text) == text


def test_leak_guard_leaves_json_xml_examples_untouched():
    text = (
        'Örnek JSON: {"ad": "deger"}. '
        "Örnek XML: <kitap><baslik>Deneme</baslik></kitap>."
    )
    assert llm_service._clean_prompt_leakage(text) == text


def test_leak_guard_leaves_answerable_real_answers_untouched():
    """28. Real captured answers with no leak must come back unchanged."""
    for answer in (
        _REAL_ASTAR_ANSWER,
        _REAL_AUTH_ANSWER,
        _REAL_INTERRUPT_ANSWER,
        _REAL_DEADLOCK_ANSWER,
        _REAL_STACK_QUEUE_ANSWER_ND,
    ):
        assert llm_service._clean_prompt_leakage(answer) == answer


def test_leak_guard_leaves_fallback_untouched():
    """19. The exact fallback sentence must be unaffected."""
    from app.services.rag_service import FALLBACK_ANSWER

    assert llm_service._clean_prompt_leakage(FALLBACK_ANSWER) == FALLBACK_ANSWER


def test_leak_guard_does_not_disturb_repetition_pipeline_hpa():
    """27. Running the leak guard ahead of the repetition guards in the
    real generate_answer pipeline must not change the already-verified
    HPA behavior (2818 -> 1019 chars, no leak content involved at all)."""
    raw = (_FIXTURES_DIR / "hpa_repetitive_raw.txt").read_text(encoding="utf-8")

    after_leak = llm_service._clean_prompt_leakage(raw)
    assert after_leak == raw.strip()  # no internal tags in this fixture at all

    after_exact = llm_service._clean_repetitive_output(after_leak)
    after_near_dup = llm_service._clean_near_duplicate_repetition(after_exact)

    assert len(after_exact) == 1019
    assert after_near_dup == after_exact


def test_leak_guard_does_not_disturb_repetition_pipeline_recursion():
    """27. Same check for the Recursion fixture (2617 -> 1201 -> 965)."""
    after_exact = (
        _FIXTURES_DIR / "recursion_after_exact_guard.txt"
    ).read_text(encoding="utf-8")

    after_leak = llm_service._clean_prompt_leakage(after_exact)
    assert after_leak == after_exact.strip()

    after_near_dup = llm_service._clean_near_duplicate_repetition(after_leak)
    assert len(after_near_dup) == 965


def test_leak_guard_empty_and_no_tags():
    assert llm_service._clean_prompt_leakage("") == ""
    assert llm_service._clean_prompt_leakage("Sıradan bir cevap.") == "Sıradan bir cevap."


def test_leak_guard_is_pure_cpu_string_processing_and_fast():
    """Performance: negligible-cost local string processing, no model or
    GPU interaction. Benchmarked against both real leak fixtures and a
    10KB synthetic HTML-heavy normal answer."""
    nyp = (_FIXTURES_DIR / "nyp_solid_leak_raw.txt").read_text(encoding="utf-8")
    web = (_FIXTURES_DIR / "web_graphql_leak_raw.txt").read_text(encoding="utf-8")
    html_heavy_10kb = (
        "<div>İçerik</div> <a>bağlantı</a> List<T> x < y [0, n] " * 200
    )[:10_000]

    for sample in (nyp, web, html_heavy_10kb):
        start = time.perf_counter()
        for _ in range(20):
            llm_service._clean_prompt_leakage(sample)
        elapsed_ms = (time.perf_counter() - start) / 20 * 1000
        assert elapsed_ms < 50


def test_generate_answer_applies_leak_cleaning_before_repetition_guards(monkeypatch):
    """Pipeline order: raw -> _strip_reasoning -> leak guard -> exact guard
    -> near-duplicate guard -> final answer, all within one generate_answer
    call (no extra model call: the fake client streams once)."""
    raw = (_FIXTURES_DIR / "nyp_solid_leak_raw.txt").read_text(encoding="utf-8")
    call_count = 0

    class _CountingClient(_FakeChatClient):
        def complete_streaming_chat(self, messages):
            nonlocal call_count
            call_count += 1
            yield from super().complete_streaming_chat(messages)

    monkeypatch.setattr(
        llm_service, "foundry_provider", _FakeProvider(_CountingClient(raw))
    )

    answer = llm_service.generate_answer(
        [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
    )

    assert call_count == 1
    assert "<DERS_MATERYALI>" not in answer
    assert "<SORU>" not in answer
    assert "Encapsulation" not in answer


def test_leak_guard_failure_falls_back_to_unchanged_answer(monkeypatch):
    """29. If the leak guard raises unexpectedly, generate_answer must
    keep the reasoning-stripped answer unchanged and return normally --
    never surface as a 500 for an otherwise-fine answer."""
    monkeypatch.setattr(
        llm_service,
        "_clean_prompt_leakage",
        lambda text: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        llm_service,
        "foundry_provider",
        _FakeProvider(_FakeChatClient(_REAL_AUTH_ANSWER)),
    )

    answer = llm_service.generate_answer(
        [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
    )

    assert answer == _REAL_AUTH_ANSWER
