from __future__ import annotations

import threading

from app.core.config import settings
from app.core.exceptions import EmbeddingError, LLMError
from app.services import llm_service, prompt_service, retrieval_service
from app.services.course_service import ensure_course_exists
from app.services.foundry_service import foundry_provider


FALLBACK_ANSWER = "Bu bilgi yüklenen ders materyallerinde bulunmuyor."

# Serializes the whole chat/query lifecycle below: the chat and embedding
# models now swap places on the GPU across several separate Foundry calls
# (chat unload -> embedding load -> retrieval -> embedding unload -> chat
# load -> generation), not a single atomic step. Two concurrent requests
# interleaving their own swaps could each unload the model the other just
# loaded, reintroducing the CUDA OOM / native-crash failure this whole
# lifecycle exists to prevent. This project is single-user/local, so simply
# running one full request at a time is an acceptable, minimal fix -- not a
# general concurrency redesign.
_swap_lock = threading.Lock()


def _sources(chunks: list[dict]) -> list[dict]:
    result: list[dict] = []
    seen: set[tuple[str, int]] = set()

    for chunk in chunks:
        key = (chunk["document_name"], int(chunk["chunk_index"]))
        if key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "documentName": chunk["document_name"],
                "chunkIndex": int(chunk["chunk_index"]),
            }
        )

    return result


def answer_question(question: str, course_id: int) -> dict:
    normalized = question.strip()
    if not normalized:
        return {"answer": FALLBACK_ANSWER, "sources": []}

    ensure_course_exists(course_id)

    with _swap_lock:
        # GPU model swap, step 1: the chat model must not be resident while
        # the embedding model loads for retrieval. If it won't unload, do
        # not proceed to load the embedding model on top of it -- that is
        # exactly the CUDA OOM (and, on repeated attempts, native process
        # crash) this lifecycle exists to prevent.
        if not foundry_provider.unload_model(settings.chat_model_name):
            raise EmbeddingError(
                "Chat modeli GPU belleğinden boşaltılamadı; embedding "
                "modeli güvenli şekilde yüklenemiyor."
            )

        chunks = retrieval_service.get_top_chunks(normalized, course_id)

        # GPU model swap, step 2: query embedding is done; drop it from
        # VRAM before the chat model needs to load back in for generation.
        embedding_unloaded = foundry_provider.unload_model(
            settings.embedding_model_name
        )

        if not chunks:
            return {
                "answer": FALLBACK_ANSWER,
                "sources": [],
            }

        if not embedding_unloaded:
            raise LLMError(
                "Embedding modeli GPU belleğinden boşaltılamadı; chat "
                "modeli güvenli şekilde yüklenemiyor."
            )

        # Evidence-sufficiency gate: a short verdict from the same chat model
        # instance that is about to generate the real answer (no extra
        # unload/reload in between -- see llm_service.check_evidence_sufficiency).
        # Retrieval relevance alone is not proof the material actually
        # supports answering the question, so in principle this should run
        # and reject before the real (expensive) generation call.
        #
        # Restricted to exactly one retrieved chunk: real testing against
        # phi-4-mini showed the classifier is reliable there (repeatable
        # correct verdicts across multiple runs), but becomes unpredictable
        # as soon as a second chunk is added to its context -- including
        # flipping an otherwise-correct YETERLI to YETERSIZ on chunk
        # combinations that are just as short/on-topic as ones that pass,
        # with no clean, addressable pattern (not chunk count alone, not
        # combined size alone). Since TOP_K commonly returns 2+ chunks, the
        # gate would otherwise reject demonstrably answerable questions
        # (observed: A* g(n)/h(n), Authentication/Authorization, vertical
        # vs. horizontal scaling, Deadlock) more often than it catches a
        # real insufficiency. With 2+ chunks, the gate is skipped entirely
        # and SYSTEM_PROMPT's own grounding/anti-fabrication rules (see
        # prompt_service.py) are the only defense -- unchanged from before
        # this whole evidence-gate effort, not weakened by it.
        if len(chunks) == 1:
            evidence_messages = prompt_service.build_evidence_messages(
                normalized, chunks
            )
            if not llm_service.check_evidence_sufficiency(evidence_messages):
                return {
                    "answer": FALLBACK_ANSWER,
                    "sources": _sources(chunks),
                }

        messages = prompt_service.build_messages(normalized, chunks)
        answer = llm_service.generate_answer(messages)

    return {
        "answer": answer,
        "sources": _sources(chunks),
    }
