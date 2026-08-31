from __future__ import annotations

import pytest

from app.core.exceptions import LLMError
from app.services import llm_service


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
