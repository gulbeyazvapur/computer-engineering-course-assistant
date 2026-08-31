from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.courses import router as courses_router
from app.api.documents import router as documents_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.database.db import init_database
from app.database.seed import seed_default_courses
from app.services.foundry_service import foundry_provider


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Bilgisayar Mühendisliği Ders Asistanı API",
    version="1.0.0",
    description="Microsoft Foundry Local tabanlı local RAG backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    # exc.detail (set by EmbeddingError/LLMError) and exc.__cause__ (set by
    # the services' `raise ... from exc`) carry the original low-level
    # error -- logged in full here for debugging, but never placed in the
    # client-facing response below, which only ever gets exc.message.
    detail = getattr(exc, "detail", None)
    if detail:
        logger.warning(
            "%s: %s | detail=%s", exc.code, exc.message, detail, exc_info=exc.__cause__
        )
    else:
        logger.warning("%s: %s", exc.code, exc.message)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
        },
    )


@app.on_event("startup")
def startup() -> None:
    settings.document_storage_path.mkdir(parents=True, exist_ok=True)
    init_database()
    seed_default_courses()
    logger.info("Database initialized: %s", settings.database_path)


@app.on_event("shutdown")
def shutdown() -> None:
    foundry_provider.unload_all()


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(courses_router)
app.include_router(documents_router)
app.include_router(chat_router)
