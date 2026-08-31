from __future__ import annotations

from fastapi import APIRouter, status

from app.models.schemas import CourseCreate, CourseResponse
from app.services import course_service


router = APIRouter(prefix="/api/courses", tags=["Courses"])


def _to_response(course: dict) -> CourseResponse:
    return CourseResponse(
        id=course["id"],
        name=course["name"],
        description=course.get("description"),
        createdAt=course.get("created_at"),
        documentCount=course.get("document_count", 0),
    )


@router.get("", response_model=list[CourseResponse])
def get_courses() -> list[CourseResponse]:
    return [_to_response(course) for course in course_service.list_courses()]


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(payload: CourseCreate) -> CourseResponse:
    course = course_service.create_course(
        payload.name,
        payload.description,
    )
    return _to_response(course)


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, payload: CourseCreate) -> CourseResponse:
    course = course_service.update_course(
        course_id,
        payload.name,
        payload.description,
    )
    return _to_response(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int) -> None:
    course_service.delete_course(course_id)
