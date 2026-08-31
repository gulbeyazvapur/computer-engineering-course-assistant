from __future__ import annotations

from app.services.prompt_service import (
    EVIDENCE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_evidence_messages,
    build_messages,
)

# The prompt wraps long sentences across source lines for readability; that
# introduces literal newlines mid-sentence which would break naive substring
# checks even though it means nothing to the model. Normalize whitespace
# before asserting on any multi-word phrase.
_NORMALIZED_PROMPT = " ".join(SYSTEM_PROMPT.split())
_NORMALIZED_EVIDENCE_PROMPT = " ".join(EVIDENCE_SYSTEM_PROMPT.split())


def test_system_prompt_requires_source_grounding():
    """A. Instructs the model to rely only on the given context."""
    assert "YALNIZCA" in SYSTEM_PROMPT
    assert "DERS_MATERYALI" in SYSTEM_PROMPT


def test_system_prompt_forbids_adding_information_outside_context():
    """B. Explicitly forbids adding out-of-context technical content."""
    assert "genel bilgini kullanarak" in SYSTEM_PROMPT
    assert "ekleme" in SYSTEM_PROMPT


def test_system_prompt_forbids_expanding_beyond_the_question():
    """C. Explicitly forbids drifting into topics that weren't asked about --
    this is the direct fix for the observed "prevention/avoidance/detection"
    scope-creep on a question that only asked for the four Coffman
    conditions."""
    assert "Sorulmayan alt konulara" in SYSTEM_PROMPT
    assert "SORU" in SYSTEM_PROMPT


def test_system_prompt_requires_explicit_missing_info_statement():
    """D. Requires a specific, predictable sentence when the answer isn't in
    context, and forbids guessing/filling in from general knowledge."""
    assert "Bu bilgi yüklenen ders materyallerinde bulunmuyor." in _NORMALIZED_PROMPT
    assert "Tahmin etme" in SYSTEM_PROMPT


def test_system_prompt_forbids_reinterpreting_technical_relationships():
    """E. Explicitly forbids flipping a concept's meaning (e.g. a "required
    condition" turning into a "preventive mechanism") -- the direct fix for
    the observed No Preemption misinterpretation."""
    assert "yeniden yorumlama" in _NORMALIZED_PROMPT
    assert "önleyen mekanizma" in _NORMALIZED_PROMPT


def test_system_prompt_requires_turkish():
    """F. Turkish-language instruction preserved."""
    assert "Türkçe" in SYSTEM_PROMPT


def test_system_prompt_forbids_internal_reasoning_leakage():
    """G. <think>/chain-of-thought leakage instruction preserved."""
    assert "<think>" in SYSTEM_PROMPT
    assert "düşünme sürecini" in SYSTEM_PROMPT


def test_system_prompt_forbids_leaking_prompt_delimiters_into_the_answer():
    """A. Explicitly states that the structural delimiters used to separate
    course material/question are only for the model, not for the answer."""
    assert "yapısal" in _NORMALIZED_PROMPT
    assert "yalnızca sana yöneliktir" in _NORMALIZED_PROMPT
    assert "<DERS_MATERYALI>" in SYSTEM_PROMPT
    assert "<SORU>" in SYSTEM_PROMPT


def test_system_prompt_forbids_arbitrary_xml_wrappers_but_allows_requested_ones():
    """B. Forbids inventing wrapper markup around the answer, but the rule
    must be conditional on the user NOT having asked for code/HTML/XML --
    it must not ban '<...>' outright, since a user could legitimately ask
    about HTML tags, XML, or C++ templates. Deliberately avoids naming any
    concrete example tag (e.g. "<CEVAP>") in the instruction itself: doing
    so previously caused the model to imitate that exact literal tag rather
    than treating it as a forbidden example."""
    assert "sarmalayıcı işareti" in _NORMALIZED_PROMPT
    assert "nihai cevabına dahil etme" in _NORMALIZED_PROMPT
    # The exception clause must be present, not an unconditional ban.
    assert "Kullanıcı açıkça kod, HTML veya XML örneği istemediği sürece" in SYSTEM_PROMPT
    # No concrete example tag name should appear -- naming one risks the
    # model imitating that literal tag instead of avoiding the pattern.
    assert "<CEVAP>" not in SYSTEM_PROMPT


def test_system_prompt_output_format_rule_is_course_agnostic():
    """C. The no-wrapper-tags rule must not hardcode any specific course
    topic (e.g. the ACID acronym that triggered this fix)."""
    assert "ACID" not in SYSTEM_PROMPT
    assert "Atomicity" not in SYSTEM_PROMPT


def test_system_prompt_preserves_all_previous_rules():
    """D. The earlier grounding/scope/missing-info/faithfulness/Turkish/
    internal-reasoning rules must all still be present after this change."""
    assert "YALNIZCA" in SYSTEM_PROMPT
    assert "Sorulmayan alt konulara" in SYSTEM_PROMPT
    assert "Bu bilgi yüklenen ders materyallerinde bulunmuyor." in _NORMALIZED_PROMPT
    assert "yeniden yorumlama" in _NORMALIZED_PROMPT
    assert "Türkçe" in SYSTEM_PROMPT
    assert "<think>" in SYSTEM_PROMPT


def test_system_prompt_is_course_agnostic():
    """No specific course topic (e.g. deadlock/Coffman condition names) is
    hardcoded into the prompt -- it must generalize to any course."""
    forbidden_terms = [
        "Deadlock",
        "Mutual Exclusion",
        "Hold and Wait",
        "No Preemption",
        "Circular Wait",
        "Coffman",
    ]
    for term in forbidden_terms:
        assert term not in SYSTEM_PROMPT


def test_build_messages_wraps_context_and_question_in_delimiters():
    chunks = [
        {"document_name": "notes.pdf", "chunk_index": 0, "content": "Chunk metni A"},
        {"document_name": "notes.pdf", "chunk_index": 1, "content": "Chunk metni B"},
    ]

    messages = build_messages("Bu nedir?", chunks)

    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert messages[1]["role"] == "user"

    user_content = messages[1]["content"]
    assert "<DERS_MATERYALI>" in user_content
    assert "</DERS_MATERYALI>" in user_content
    assert "<SORU>" in user_content
    assert "</SORU>" in user_content

    # Context must appear before the question, and both chunks must be
    # inside the DERS_MATERYALI block.
    materyal_start = user_content.index("<DERS_MATERYALI>")
    materyal_end = user_content.index("</DERS_MATERYALI>")
    soru_start = user_content.index("<SORU>")
    assert materyal_start < materyal_end < soru_start

    assert "Chunk metni A" in user_content[materyal_start:materyal_end]
    assert "Chunk metni B" in user_content[materyal_start:materyal_end]
    assert "Bu nedir?" in user_content[soru_start:]


def test_build_messages_includes_source_and_chunk_markers():
    chunks = [{"document_name": "deadlock.pdf", "chunk_index": 2, "content": "İçerik"}]

    messages = build_messages("Soru", chunks)
    user_content = messages[1]["content"]

    assert "SOURCE: deadlock.pdf" in user_content
    assert "CHUNK: 2" in user_content


def test_system_prompt_forbids_fabricated_examples():
    """A. Explicitly forbids inventing concrete brand/product/company/tool/
    protocol examples that aren't in the context -- the direct fix for the
    observed fabricated "Microsoft Office Online" example on a SaaS
    question."""
    assert "Marka, ürün, şirket, araç, protokol" in _NORMALIZED_PROMPT
    assert "örnek uydurma" in _NORMALIZED_PROMPT


def test_system_prompt_allows_examples_only_when_present_in_context():
    """B. The example rule must be conditional: concrete examples are
    allowed when they genuinely appear in the source material, and the
    model should state absence rather than invent one when asked for an
    example that isn't there."""
    assert "yalnızca <DERS_MATERYALI> içinde açıkça geçiyorsa" in _NORMALIZED_PROMPT
    assert "bunun materyalde bulunmadığını belirt" in _NORMALIZED_PROMPT


def test_system_prompt_forbids_missing_info_statement_when_answer_present():
    """C. Explicit rule against appending the missing-info sentence when the
    context fully answers the question -- the direct fix for the observed
    contradictory closing after an otherwise correct/complete answer."""
    assert "Bu durumda" in _NORMALIZED_PROMPT
    assert "EKLEME" in SYSTEM_PROMPT


def test_system_prompt_preserves_missing_info_behavior_for_fully_absent_info():
    """D. The exact, predictable missing-info sentence must still be
    required when the needed information is genuinely absent from context."""
    assert "Bu bilgi yüklenen ders materyallerinde bulunmuyor." in _NORMALIZED_PROMPT
    assert "Tahmin etme" in SYSTEM_PROMPT


def test_system_prompt_has_partial_info_rule():
    """E. When only part of the question is answerable from context, the
    model must answer the available part and flag only the missing part --
    not claim the whole answer is absent, and not silently omit the gap."""
    assert "yalnızca bir kısmının cevabı" in _NORMALIZED_PROMPT
    assert "eksik kalan kısmın materyalde" in _NORMALIZED_PROMPT


def test_system_prompt_has_self_consistency_rule():
    """F. Explicit non-contradiction rule: don't explain something using the
    material and then say that same thing isn't in the material, and the
    missing-info phrase must not be treated as a generic closing line."""
    assert "çelişkili olmamalı" in _NORMALIZED_PROMPT
    assert "bir kapanış cümlesi değildir" in _NORMALIZED_PROMPT


def test_system_prompt_forbids_filling_specific_detail_from_general_topic_relevance():
    """H. Topical relevance in the retrieved context (e.g. general TCP text)
    must not be treated as license to fabricate a specific requested detail
    (e.g. a particular algorithm's internal behavior) that isn't literally
    present -- the direct fix for the observed TCP Reno / congestion-window
    fabrication when only generic TCP chunks were retrieved."""
    assert "sorunun genel konusuyla ilgili metin bulunması" in _NORMALIZED_PROMPT
    assert "spesifik detayı kendi bilginden tamamlama" in _NORMALIZED_PROMPT
    assert "kendi eğitim bilginden hatırlayarak yazabileceğin" in _NORMALIZED_PROMPT


def test_system_prompt_forbids_inferring_named_lists_from_generic_description():
    """I. A generic description of actions/effects around a concept (e.g.
    "the OS creates, schedules, and terminates processes") must not be
    treated as license to synthesize a named, enumerated breakdown (states,
    stages, types, categories) of that concept that isn't itself literally
    spelled out in the material -- the fix for the observed process
    lifecycle (New/Ready/Running/Waiting/Terminated) fabrication when only a
    generic process-management sentence was retrieved."""
    assert "adlandırılmış aşamalarını, durumlarını, türlerini" in _NORMALIZED_PROMPT
    assert "listeyi kendi bilginden" in _NORMALIZED_PROMPT
    assert "tamamlama" in _NORMALIZED_PROMPT


def test_system_prompt_named_list_rule_is_course_agnostic():
    """J. The named-list inference rule must not hardcode any concrete
    course topic (process lifecycle states, OSI layers, etc.)."""
    forbidden_terms = [
        "yaşam döngüsü",
        "New",
        "Ready",
        "Running",
        "Waiting",
        "Terminated",
        "OSI",
    ]
    for term in forbidden_terms:
        assert term not in SYSTEM_PROMPT


def test_system_prompt_new_rules_are_course_agnostic():
    """G. Neither the anti-fabrication rule nor the missing-info restructure
    hardcodes any concrete course topic, product, or example term."""
    forbidden_terms = [
        "Microsoft Office Online",
        "Microsoft Office",
        "ACID",
        "TCP",
        "UDP",
        "IaaS",
        "PaaS",
        "SaaS",
        "Reno",
        "congestion window",
    ]
    for term in forbidden_terms:
        assert term not in SYSTEM_PROMPT


def test_evidence_prompt_requires_single_word_verdict():
    """The evidence-sufficiency check's only valid outputs are the two
    verdict tokens -- no explanation, no course-specific example."""
    assert "YETERLI" in EVIDENCE_SYSTEM_PROMPT
    assert "YETERSIZ" in EVIDENCE_SYSTEM_PROMPT
    assert "tek bir kelime" in _NORMALIZED_EVIDENCE_PROMPT


def test_evidence_prompt_rejects_topical_relevance_as_sufficient():
    assert "ilişkili olması yeterli değildir" in _NORMALIZED_EVIDENCE_PROMPT
    assert "kendi genel bilgini kullanma" in _NORMALIZED_EVIDENCE_PROMPT


def test_evidence_prompt_defaults_to_insufficient_when_uncertain():
    assert "Emin değilsen YETERSIZ" in EVIDENCE_SYSTEM_PROMPT


def test_evidence_prompt_is_course_agnostic():
    forbidden_terms = [
        "Deadlock",
        "Coffman",
        "process",
        "thread",
        "Banker's",
        "İşletim Sistemleri",
        "yaşam döngüsü",
    ]
    for term in forbidden_terms:
        assert term not in EVIDENCE_SYSTEM_PROMPT


def test_build_evidence_messages_wraps_context_and_asks_for_verdict():
    chunks = [{"document_name": "notes.pdf", "chunk_index": 0, "content": "Chunk metni"}]

    messages = build_evidence_messages("Bu nedir?", chunks)

    assert messages[0] == {"role": "system", "content": EVIDENCE_SYSTEM_PROMPT}
    user_content = messages[1]["content"]
    assert "<DERS_MATERYALI>" in user_content
    assert "Chunk metni" in user_content
    assert "Bu nedir?" in user_content
    assert "YETERLI" in user_content and "YETERSIZ" in user_content


def test_build_evidence_messages_is_independent_from_answer_messages():
    """The evidence-check prompt must never leak into the real answer
    generation call, and vice versa."""
    chunks = [{"document_name": "notes.pdf", "chunk_index": 0, "content": "Chunk metni"}]

    answer_messages = build_messages("Soru", chunks)
    evidence_messages = build_evidence_messages("Soru", chunks)

    assert answer_messages[0]["content"] != evidence_messages[0]["content"]
