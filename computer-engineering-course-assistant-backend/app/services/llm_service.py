from __future__ import annotations

import json
import re

from app.core.config import settings
from app.core.exceptions import LLMError
from app.services.foundry_service import foundry_provider


# Some catalog models (e.g. qwen3.5-2b-text) have reasoning capability and emit
# their chain-of-thought inline in the streamed content, wrapped in <think>
# tags, instead of a separate field. That reasoning trace must never reach the
# student-facing answer.
_THINK_TAG_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)

# The evidence-sufficiency check (see check_evidence_sufficiency) only ever
# needs a one-word verdict, so it is run with its own small, fixed
# generation budget instead of the configured chat_max_tokens/chat_temperature
# -- those remain reserved for the real answer generation and are not
# touched here.
_EVIDENCE_MAX_TOKENS = 8
_EVIDENCE_TEMPERATURE = 0.0

_JSON_OBJECT_PATTERN = re.compile(r"\{.*?\}", re.DOTALL)


def _strip_reasoning(text: str) -> str:
    cleaned = _THINK_TAG_PATTERN.sub("", text)

    # Defensive: if generation was cut off mid-thought, there may be an opening
    # <think> tag with no matching close. Drop everything from that point on
    # rather than leaking a partial reasoning trace to the user.
    open_idx = cleaned.lower().find("<think>")
    if open_idx != -1:
        cleaned = cleaned[:open_idx]

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

        if not answer:
            raise RuntimeError("Model boş cevap döndürdü.")

        return answer

    except Exception as exc:
        raise LLMError(str(exc)) from exc
