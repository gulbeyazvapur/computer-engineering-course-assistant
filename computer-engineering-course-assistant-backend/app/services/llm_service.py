from __future__ import annotations

import json
import logging
import re
from difflib import SequenceMatcher

from app.core.config import settings
from app.core.exceptions import LLMError
from app.services.foundry_service import foundry_provider


logger = logging.getLogger(__name__)


# Some catalog models (e.g. qwen3.5-2b-text) have reasoning capability and emit
# their chain-of-thought inline in the streamed content, wrapped in <think>
# tags, instead of a separate field. That reasoning trace must never reach the
# student-facing answer.
_THINK_TAG_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)

# Prompt/delimiter leakage guard (see _clean_prompt_leakage): the internal
# wrapper tags prompt_service.py uses to separate retrieved course material
# and the user's question in the *input* message
# (<DERS_MATERYALI>...</DERS_MATERYALI>, <SORU>...</SORU> -- see
# prompt_service.build_messages/_build_context) are, on rare occasions,
# echoed back verbatim by phi-4-mini in its *output* instead of (or
# alongside) a real answer. Observed for real in a 49-course stress test:
# one answer echoed the entire retrieved context and the question back
# wrapped in these exact tags before trailing into a hallucinated fake
# instruction section; another (milder) case appended a garbled variant of
# the opening tag (<|DERS_MATERYALI|>) after an otherwise complete, correct
# answer. Neither the exact nor the near-duplicate repetition guards can
# see this: both only ever compare parts of the *output* against each
# other, never against what the *input* looked like, and a one-time echo
# is not a repeat.
#
# This targets ONLY these two specific, literal internal tag names (plus
# the exact garbled pipe-wrapped variant actually observed) -- deliberately
# NOT a generic "<...>" tag stripper (e.g. re.sub(r"<.*?>", "", answer)),
# which would also destroy legitimate technical content a student could
# genuinely ask about or receive (<div>, <a>, List<T>, x < y, [0, n],
# JSON/XML/HTML examples).
_INTERNAL_TAG_NAMES = ("DERS_MATERYALI", "SORU")


def _internal_tag_block_pattern(name: str) -> re.Pattern[str]:
    return re.compile(rf"<\|?{name}\|?>.*?</\|?{name}\|?>", re.DOTALL)


def _internal_tag_open_pattern(name: str) -> re.Pattern[str]:
    return re.compile(rf"<\|?{name}\|?>")


# The evidence-sufficiency check (see check_evidence_sufficiency) only ever
# needs a one-word verdict, so it is run with its own small, fixed
# generation budget instead of the configured chat_max_tokens/chat_temperature
# -- those remain reserved for the real answer generation and are not
# touched here.
_EVIDENCE_MAX_TOKENS = 8
_EVIDENCE_TEMPERATURE = 0.0

_JSON_OBJECT_PATTERN = re.compile(r"\{.*?\}", re.DOTALL)

# Repetition guard (see _clean_repetitive_output): splits on the whitespace
# that follows a sentence-ending mark, keeping that whitespace attached to
# the split so the original text can be reassembled exactly.
_SENTENCE_BOUNDARY_PATTERN = re.compile(r"(?<=[.!?])(\s+)")

# A block must repeat at least this many times in total (the first
# occurrence plus this-many-minus-one further repeats) before it's treated
# as a genuine degenerate loop rather than an incidental duplicate sentence
# (real prose occasionally repeats a short phrase once for emphasis; a
# pathological generation loop repeats many times). Chosen from the real
# captured HPA regression case (see tests), where the looping block repeats
# far more than this.
_MIN_REPEAT_OCCURRENCES = 3
# Loops observed in practice repeat a single sentence or a short multi-
# sentence block (the real HPA case is a 2-sentence block); this bounds how
# large a candidate block is worth checking, keeping the scan cheap.
_MAX_REPEAT_BLOCK_LENGTH = 6

# Near-duplicate repetition guard (see _clean_near_duplicate_repetition):
# a second, more permissive pass that runs only after the exact-match guard
# above, on whatever text it left behind. Uses difflib.SequenceMatcher
# (stdlib, no new dependency) to catch pathological *paraphrased* repeats
# that are not byte-identical -- e.g. a real captured phi-4-mini answer
# repeated "bir fonksiyonun kendini çağırması", "bir fonksiyonun kendini
# çağırması gibi", "...çağırması, ...çağırması gibi, ...çağırması gibi
# görünebilir" back to back, close enough in wording that a human reads it
# as an obvious stuck loop, but never byte-identical, so the exact guard
# above (correctly) leaves it alone.
#
# Threshold calibrated against real captured answers (see
# tests/test_llm_service.py): the highest incidental similarity measured
# between two *legitimately different* sentences in real answers was 0.935
# (two already-distinct sentences the exact guard correctly kept in the
# HPA fixture) and 0.875 (a Stack vs. Queue sentence pair -- same template,
# opposite meaning). Both sit comfortably below this threshold. The real
# pathological near-duplicates in the Recursion fixture score 0.984-0.996.
_NEAR_DUP_SIMILARITY_THRESHOLD = 0.95
# SequenceMatcher.ratio() is at most 2*min(len(a),len(b)) / (len(a)+len(b));
# solving that bound for the length ratio gives the length-ratio floor below
# which two strings provably cannot reach _NEAR_DUP_SIMILARITY_THRESHOLD,
# regardless of content -- a cheap, exact (no false-negative) pre-filter,
# see _is_near_duplicate_sentence.
_NEAR_DUP_LENGTH_RATIO_FLOOR = _NEAR_DUP_SIMILARITY_THRESHOLD / (
    2 - _NEAR_DUP_SIMILARITY_THRESHOLD
)
# Sentences shorter than this (after whitespace normalization) are excluded
# from near-duplicate comparison entirely: short sentences ("Evet.",
# "Doğru.") can coincidentally score high similarity against each other
# without expressing a genuinely repeated idea.
_NEAR_DUP_MIN_SENTENCE_LENGTH = 20
# A single repeated sentence (block length 1) needs the same conservative
# 3-occurrence bar as the exact guard: an isolated pair of highly similar
# sentences is more plausibly two legitimately different sentences that
# happen to share a template (see the Stack/Queue case above) than a real
# loop. A repeated multi-sentence *block* (length >= 2) matched position-
# for-position is a far less likely coincidence, so 2 occurrences is
# enough once every position in the block clears the threshold -- this is
# exactly the real Recursion pattern (two 2-sentence blocks, matched
# 0.996 and 0.984 position-for-position).
_NEAR_DUP_MIN_OCCURRENCES_SINGLE = 3
_NEAR_DUP_MIN_OCCURRENCES_BLOCK = 2
_NEAR_DUP_MAX_BLOCK_LENGTH = 6


def _clean_repetitive_output(text: str) -> str:
    """Trims a degenerate repetition loop off the tail of a generated
    answer: if some sentence, or short run of consecutive sentences, repeats
    verbatim (whitespace-normalized) at least _MIN_REPEAT_OCCURRENCES times
    in a row, everything from the *second* occurrence of that block onward
    is dropped -- the first occurrence, and everything before it, is kept
    completely unchanged.

    This is deliberately conservative and purely structural (exact,
    whitespace-normalized repeat matching -- no paraphrasing, no semantic
    similarity, no keyword/course-specific logic): a real answer with
    several distinct sentences or list items (even ones that share
    terminology or sentence shape) never contains the same sentence
    verbatim three times in a row, so it is never touched. A genuine
    generation loop, observed in practice to repeat the same block many
    times until the token budget runs out (including ending mid-word on the
    final, truncated repeat), reliably does.

    Only ever removes text; never rewrites, summarizes, or adds anything.
    """
    if not text:
        return text

    parts = _SENTENCE_BOUNDARY_PATTERN.split(text)
    sentences = parts[0::2]
    total = len(sentences)

    if total < _MIN_REPEAT_OCCURRENCES:
        return text

    normalized = [" ".join(s.split()) for s in sentences]

    for start in range(total):
        max_block_length = min(
            _MAX_REPEAT_BLOCK_LENGTH, (total - start) // _MIN_REPEAT_OCCURRENCES
        )
        for block_length in range(1, max_block_length + 1):
            block = normalized[start : start + block_length]
            if not any(block):
                continue

            occurrences = 1
            cursor = start + block_length
            while (
                cursor + block_length <= total
                and normalized[cursor : cursor + block_length] == block
            ):
                occurrences += 1
                cursor += block_length

            if occurrences >= _MIN_REPEAT_OCCURRENCES:
                # Keep everything through the end of the first occurrence of
                # the repeated block; parts[] alternates sentence/separator,
                # so sentence index (start + block_length) begins at
                # parts[2 * (start + block_length)] -- cut right before it.
                cutoff = 2 * (start + block_length) - 1
                return "".join(parts[:cutoff]).rstrip()

    return text


def _normalize_for_similarity(text: str) -> str:
    return " ".join(text.lower().split())


def _is_near_duplicate_sentence(a: str, b: str) -> bool:
    if len(a) < _NEAR_DUP_MIN_SENTENCE_LENGTH or len(b) < _NEAR_DUP_MIN_SENTENCE_LENGTH:
        return False

    # Cheap, exact pre-filters before the O(len(a)*len(b))-worst-case
    # SequenceMatcher call, so a long non-repeating answer (or a small
    # sentence-count blowup like 10KB of concatenated real answers) doesn't
    # pay for full fuzzy comparison on pairs that provably cannot reach the
    # threshold. Neither prefilter can produce a false negative:
    # SequenceMatcher.ratio() is at most 2*min(len)/(len(a)+len(b)), so if
    # the shorter/longer length ratio is below _NEAR_DUP_LENGTH_RATIO_FLOOR
    # the true ratio provably cannot reach the threshold either; quick_ratio()
    # is documented to always be >= the real ratio().
    shorter_len, longer_len = sorted((len(a), len(b)))
    if shorter_len / longer_len < _NEAR_DUP_LENGTH_RATIO_FLOOR:
        return False

    matcher = SequenceMatcher(None, a, b)
    if matcher.quick_ratio() < _NEAR_DUP_SIMILARITY_THRESHOLD:
        return False

    return matcher.ratio() >= _NEAR_DUP_SIMILARITY_THRESHOLD


def _clean_near_duplicate_repetition(text: str) -> str:
    """Second, more permissive repetition pass, run only after
    _clean_repetitive_output (the exact-match guard) on whatever text it
    left behind: catches a pathological loop that paraphrases the same idea
    each time instead of repeating it byte-for-byte, using the same
    conservative keep-the-first-occurrence-drop-the-rest strategy and the
    same block-scanning structure as the exact guard, just with fuzzy
    (SequenceMatcher-based) instead of exact sentence comparison.

    Deliberately conservative: a real answer with several distinct
    sentences or list items -- even ones sharing a sentence template or
    terminology (e.g. "Vertical scaling ... / Horizontal scaling ...",
    Stack vs. Queue, the four Coffman conditions) -- does not clear the
    similarity threshold at every position of a repeating block enough
    times to trigger this. Only ever removes text; never rewrites,
    summarizes, or adds anything.
    """
    if not text:
        return text

    parts = _SENTENCE_BOUNDARY_PATTERN.split(text)
    sentences = parts[0::2]
    total = len(sentences)

    if total < 2:
        return text

    normalized = [_normalize_for_similarity(s) for s in sentences]

    for start in range(total):
        for block_length in range(1, _NEAR_DUP_MAX_BLOCK_LENGTH + 1):
            min_occurrences = (
                _NEAR_DUP_MIN_OCCURRENCES_SINGLE
                if block_length == 1
                else _NEAR_DUP_MIN_OCCURRENCES_BLOCK
            )
            if start + block_length * min_occurrences > total:
                continue

            block = normalized[start : start + block_length]

            def _block_matches(candidate_start: int, _block=block) -> bool:
                candidate = normalized[candidate_start : candidate_start + block_length]
                return all(
                    _is_near_duplicate_sentence(_block[k], candidate[k])
                    for k in range(block_length)
                )

            occurrences = 1
            cursor = start + block_length
            while cursor + block_length <= total and _block_matches(cursor):
                occurrences += 1
                cursor += block_length

            if occurrences >= min_occurrences:
                cutoff = 2 * (start + block_length) - 1
                return "".join(parts[:cutoff]).rstrip()

    return text


def _strip_reasoning(text: str) -> str:
    cleaned = _THINK_TAG_PATTERN.sub("", text)

    # Defensive: if generation was cut off mid-thought, there may be an opening
    # <think> tag with no matching close. Drop everything from that point on
    # rather than leaking a partial reasoning trace to the user.
    open_idx = cleaned.lower().find("<think>")
    if open_idx != -1:
        cleaned = cleaned[:open_idx]

    return cleaned.strip()


def _clean_prompt_leakage(text: str) -> str:
    """Removes internal prompt-wrapper tags (and everything they wrap) if
    the model echoed them into its output instead of, or around, a real
    answer -- see _INTERNAL_TAG_NAMES above for why this is scoped to
    exactly two literal tag names rather than any general tag pattern.

    For each known internal tag name: first removes every fully-closed
    <NAME>...</NAME> block found anywhere (the open and/or close may each
    be the plain or the observed garbled <|NAME|> form); then, if an
    opening tag for that name still remains with no closing tag after it
    (e.g. the echo was cut off by the token budget before reaching the
    close), drops everything from that opening tag to the end of the text
    -- the same "cut the degenerate tail" approach the repetition guards
    use, applied here to an echoed prompt fragment instead of a repeat.

    Only ever removes text; never rewrites, summarizes, or adds anything.
    """
    if not text:
        return text

    cleaned = text
    for name in _INTERNAL_TAG_NAMES:
        cleaned = _internal_tag_block_pattern(name).sub("", cleaned)
        open_match = _internal_tag_open_pattern(name).search(cleaned)
        if open_match:
            cleaned = cleaned[: open_match.start()]

    return cleaned.strip()


def _parse_sufficiency(raw: str) -> bool:
    """Parses the evidence-check model's verdict. Fail-closed by design: any
    output that isn't an unambiguous positive verdict (JSON ``{"sufficient":
    true}`` or the literal token "YETERLI") is treated as insufficient --
    including empty output, free text, or a response containing both verdict
    words. See check_evidence_sufficiency for why this must never fail open.
    """
    text = raw.strip()
    if not text:
        return False

    json_match = _JSON_OBJECT_PATTERN.search(text)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
        except ValueError:
            data = None
        if isinstance(data, dict) and isinstance(data.get("sufficient"), bool):
            return data["sufficient"]

    # Normalize Turkish dotted/dotless I so "YETERLİ"/"YETERSİZ" match
    # regardless of the model's exact casing.
    normalized = text.upper().replace("İ", "I")

    if "YETERSIZ" in normalized:
        return False
    if "YETERLI" in normalized:
        return True

    return False


def check_evidence_sufficiency(messages: list[dict[str, str]]) -> bool:
    """Asks the already (or about-to-be) resident chat model a short,
    separate question: does the retrieved context actually support answering
    the user's question, as opposed to merely being topically related to it?

    Uses the exact same chat model alias/client as generate_answer, inside
    the same GPU residency window -- this must never trigger its own
    unload/reload cycle. Any ambiguity (parse failure, empty response,
    unexpected text) resolves to False (insufficient) rather than True: an
    unnecessary fallback is a much cheaper mistake here than an ungrounded
    answer reaching the student.
    """
    try:
        model = foundry_provider.get_loaded_model(settings.chat_model_name)
        client = model.get_chat_client()

        if hasattr(client, "settings"):
            client.settings.temperature = _EVIDENCE_TEMPERATURE
            client.settings.max_tokens = _EVIDENCE_MAX_TOKENS

        full_response = ""

        for chunk in client.complete_streaming_chat(messages):
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                full_response += content

        return _parse_sufficiency(_strip_reasoning(full_response))

    except Exception as exc:
        raise LLMError(str(exc)) from exc


def generate_answer(messages: list[dict[str, str]]) -> str:
    try:
        model = foundry_provider.get_loaded_model(settings.chat_model_name)
        client = model.get_chat_client()

        if hasattr(client, "settings"):
            client.settings.temperature = settings.chat_temperature
            client.settings.max_tokens = settings.chat_max_tokens

        full_response = ""

        # complete_chat() has been unreliable against the local Foundry runtime
        # (observed as "Operation was cancelled"); complete_streaming_chat()
        # works reliably, so we always stream and reassemble the full answer
        # before returning it to the caller.
        for chunk in client.complete_streaming_chat(messages):
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                full_response += content

        answer = _strip_reasoning(full_response)

        # Prompt/delimiter leakage guard runs first, before either
        # repetition pass: an echoed prompt fragment is a different kind of
        # content than a repeated answer sentence, and stripping it first
        # keeps the (more expensive, fuzzy-matching) guards below working
        # on just the real remaining answer text. Isolated in its own
        # try/except for the same reason as the near-duplicate guard below:
        # a bug here must degrade to "skip it", never a 500 for an answer
        # that was otherwise fine.
        try:
            leak_cleaned = _clean_prompt_leakage(answer)
        except Exception:
            logger.warning(
                "Prompt leakage guard failed; keeping answer unchanged.",
                exc_info=True,
            )
            leak_cleaned = answer

        if len(leak_cleaned) != len(answer):
            logger.info(
                "Prompt leakage removed from model output: %d -> %d chars",
                len(answer),
                len(leak_cleaned),
            )

        answer = leak_cleaned

        cleaned = _clean_repetitive_output(answer)

        if len(cleaned) != len(answer):
            logger.info(
                "Repetitive model output trimmed: %d -> %d chars",
                len(answer),
                len(cleaned),
            )

        answer = cleaned

        # Second, more permissive pass for paraphrased (non-byte-identical)
        # repetition the exact guard above cannot see -- see
        # _clean_near_duplicate_repetition. Isolated in its own try/except:
        # a bug in this newer, fuzzier pass must degrade to "skip it" (keep
        # the exact-guard-cleaned answer as-is), never turn into a 500 for
        # an answer that was otherwise perfectly fine.
        try:
            near_dup_cleaned = _clean_near_duplicate_repetition(answer)
        except Exception:
            logger.warning(
                "Near-duplicate repetition guard failed; keeping "
                "exact-guard-cleaned answer unchanged.",
                exc_info=True,
            )
            near_dup_cleaned = answer

        if len(near_dup_cleaned) != len(answer):
            logger.info(
                "Near-duplicate model output trimmed: %d -> %d chars",
                len(answer),
                len(near_dup_cleaned),
            )

        answer = near_dup_cleaned

        if not answer:
            raise RuntimeError("Model boş cevap döndürdü.")

        return answer

    except Exception as exc:
        raise LLMError(str(exc)) from exc
