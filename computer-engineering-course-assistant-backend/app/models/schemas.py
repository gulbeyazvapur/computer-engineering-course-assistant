from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ders adı boş bırakılamaz.")
        return value


class CourseResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    createdAt: str | None = None
    documentCount: int = 0


class DocumentResponse(BaseModel):
    id: int
    courseId: int
    courseName: str
    fileName: str
    chunkCount: int
    createdAt: str


class DocumentUploadResponse(BaseModel):
    id: int
    courseId: int
    fileName: str
    chunkCount: int
    message: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    courseId: int = Field(gt=0)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Soru boş bırakılamaz.")
        return value


class SourceResponse(BaseModel):
    documentName: str
    chunkIndex: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
