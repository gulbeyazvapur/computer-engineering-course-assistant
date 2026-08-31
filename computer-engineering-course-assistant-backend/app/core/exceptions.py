from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class CourseNotFoundError(AppError):
    def __init__(self):
        super().__init__("COURSE_NOT_FOUND", "Ders bulunamadı.", 404)


class DuplicateCourseError(AppError):
    def __init__(self):
        super().__init__(
            "DUPLICATE_COURSE",
            "Aynı isimde bir ders zaten mevcut.",
            409,
        )


class UnsupportedFileTypeError(AppError):
    def __init__(self):
        super().__init__(
            "UNSUPPORTED_FILE_TYPE",
            "Yalnızca PDF dosyaları desteklenir.",
            400,
        )


class FileTooLargeError(AppError):
    def __init__(self, max_size_mb: int):
        super().__init__(
            "FILE_TOO_LARGE",
            f"Dosya boyutu en fazla {max_size_mb} MB olabilir.",
            400,
        )


class PdfTextExtractionError(AppError):
    def __init__(self):
        super().__init__(
            "PDF_TEXT_EXTRACTION_ERROR",
            "PDF içerisinden kullanılabilir metin çıkarılamadı.",
            422,
        )


class EmbeddingError(AppError):
    """``detail`` is the original low-level error (e.g. a raw CUDA/.NET
    exception string) and is for server-side logging only -- see
    ``app_error_handler`` in app/main.py. It must never be appended to the
    public ``message``, which stays a fixed, safe sentence regardless of
    what the underlying runtime says, since this also covers query-time
    embedding failures during chat retrieval, not just document ingestion.
    """

    def __init__(self, detail: str | None = None):
        super().__init__(
            "EMBEDDING_ERROR",
            "Yerel yapay zeka işlemi tamamlanamadı. Lütfen tekrar deneyin.",
            500,
        )
        self.detail = detail


class LLMError(AppError):
    """``detail`` is the original low-level error, kept for server-side
    logging only -- see ``EmbeddingError``."""

    def __init__(self, detail: str | None = None):
        super().__init__(
            "LLM_ERROR",
            "Yerel dil modeli şu anda yanıt oluşturamadı. Lütfen tekrar deneyin.",
            500,
        )
        self.detail = detail


class NoDocumentsError(AppError):
    def __init__(self):
        super().__init__(
            "NO_DOCUMENTS",
            "Seçilen derse ait işlenmiş doküman bulunamadı.",
            422,
        )


class DocumentNotFoundError(AppError):
    def __init__(self):
        super().__init__("DOCUMENT_NOT_FOUND", "Doküman bulunamadı.", 404)
