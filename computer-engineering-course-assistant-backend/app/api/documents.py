from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile, status

from app.models.schemas import DocumentResponse, DocumentUploadResponse
from app.services import document_service


router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=list[DocumentResponse])
def get_documents(courseId: int | None = None) -> list[DocumentResponse]:
    return [
        DocumentResponse(**document)
        for document in document_service.list_documents(courseId)
    ]


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    courseId: int = Form(...),
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    result = await document_service.ingest_pdf(courseId, file)
    return DocumentUploadResponse(**result)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int) -> None:
    document_service.delete_document(document_id)
