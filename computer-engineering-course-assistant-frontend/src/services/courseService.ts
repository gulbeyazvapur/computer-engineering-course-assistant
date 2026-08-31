import { apiClient } from "./apiClient";
import type {
  Course,
  CourseCreateRequest,
  CourseUpdateRequest,
} from "../types/course";

export async function getCourses(): Promise<Course[]> {
  const response = await apiClient.get<Course[]>("/api/courses");
  return response.data;
}

export async function createCourse(
  payload: CourseCreateRequest,
): Promise<Course> {
  const response = await apiClient.post<Course>("/api/courses", payload);
  return response.data;
}

export async function updateCourse(
  courseId: number,
  payload: CourseUpdateRequest,
): Promise<Course> {
  const response = await apiClient.put<Course>(
    `/api/courses/${courseId}`,
    payload,
  );
  return response.data;
}

export async function deleteCourse(courseId: number): Promise<void> {
  await apiClient.delete(`/api/courses/${courseId}`);
}
