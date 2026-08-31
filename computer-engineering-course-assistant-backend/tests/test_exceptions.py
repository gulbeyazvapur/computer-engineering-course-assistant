from __future__ import annotations

import asyncio
import json
import logging

from app.core.exceptions import CourseNotFoundError, EmbeddingError, LLMError
from app.main import app_error_handler


# A realistic stand-in for the raw .NET/CUDA exception text observed in
# production (Microsoft.ML.OnnxRuntimeGenAI / native interop stack traces).
# Deliberately generic -- no real project paths hardcoded.
_FAKE_TECHNICAL_DETAIL = (
    "Microsoft.ML.OnnxRuntimeGenAI.OnnxRuntimeGenAIException: CUDA error "
    "in IsSupportedCooperative at internal/native/path/cuda_topk_common.cuh:455 "
    "- out of memory\n   at Microsoft.Neutron.OpenAI.Provider.ChatCompletions"
    ".HandleStreamRequestAsync() + 0x1b\n   at Microsoft.AI.Foundry.Local."
    "NativeInterop.ExecuteCommandWithCallbackManaged() + 0x467"
)


def _run_handler(exc):
    return asyncio.run(app_error_handler(None, exc))


def test_llm_error_message_never_contains_raw_technical_detail():
    """A. However long/technical the underlying detail is, LLMError's
    public message must never contain it."""
    exc = LLMError(_FAKE_TECHNICAL_DETAIL)

    assert _FAKE_TECHNICAL_DETAIL not in exc.message
    assert "CUDA" not in exc.message
    assert "Microsoft." not in exc.message
    assert exc.detail == _FAKE_TECHNICAL_DETAIL


def test_embedding_error_message_never_contains_raw_technical_detail():
    """B. Same guarantee for EmbeddingError."""
    exc = EmbeddingError(_FAKE_TECHNICAL_DETAIL)

    assert _FAKE_TECHNICAL_DETAIL not in exc.message
    assert "CUDA" not in exc.message
    assert "Microsoft." not in exc.message
    assert exc.detail == _FAKE_TECHNICAL_DETAIL


def test_llm_error_returns_safe_public_message():
    """C. Public message is the fixed, user-friendly Turkish sentence,
    regardless of what detail is passed."""
    exc = LLMError("herhangi bir teknik detay")

    assert (
        exc.message
        == "Yerel dil modeli şu anda yanıt oluşturamadı. Lütfen tekrar deneyin."
    )


def test_embedding_error_returns_safe_public_message():
    """C. Same guarantee for EmbeddingError."""
    exc = EmbeddingError("herhangi bir teknik detay")

    assert (
        exc.message == "Yerel yapay zeka işlemi tamamlanamadı. Lütfen tekrar deneyin."
    )


def test_error_handler_response_excludes_technical_detail():
    """A/B end-to-end via the actual HTTP response path: the JSON body sent
    to the client must not contain the raw technical detail anywhere."""
    exc = LLMError(_FAKE_TECHNICAL_DETAIL)

    response = _run_handler(exc)
    raw_body = response.body.decode("utf-8")

    assert _FAKE_TECHNICAL_DETAIL not in raw_body
    assert "CUDA" not in raw_body
    assert "Microsoft." not in raw_body
    assert "cuda_topk_common.cuh" not in raw_body
    assert "NativeInterop" not in raw_body


def test_error_handler_preserves_status_code_and_error_code():
    """D, E. HTTP status and the error code field are unchanged."""
    exc = LLMError("detay")

    response = _run_handler(exc)
    body = json.loads(response.body)

    assert response.status_code == 500
    assert body["error"] == "LLM_ERROR"
    assert (
        body["message"]
        == "Yerel dil modeli şu anda yanıt oluşturamadı. Lütfen tekrar deneyin."
    )


def test_error_handler_preserves_embedding_error_code():
    """E. EmbeddingError's code and status are unchanged."""
    exc = EmbeddingError("detay")

    response = _run_handler(exc)
    body = json.loads(response.body)

    assert response.status_code == 500
    assert body["error"] == "EMBEDDING_ERROR"


def test_error_handler_logs_full_technical_detail(caplog):
    """F. The full technical detail must still reach the server-side log,
    even though it never reaches the client response."""
    exc = LLMError(_FAKE_TECHNICAL_DETAIL)

    with caplog.at_level(logging.WARNING, logger="app.main"):
        _run_handler(exc)

    logged_text = " ".join(record.getMessage() for record in caplog.records)
    assert _FAKE_TECHNICAL_DETAIL in logged_text


def test_error_handler_unaffected_for_app_errors_without_detail():
    """Sanity: AppError subclasses with no `detail` concept (e.g.
    CourseNotFoundError) still work through the handler exactly as before."""
    response = _run_handler(CourseNotFoundError())
    body = json.loads(response.body)

    assert response.status_code == 404
    assert body["error"] == "COURSE_NOT_FOUND"
    assert body["message"] == "Ders bulunamadı."
