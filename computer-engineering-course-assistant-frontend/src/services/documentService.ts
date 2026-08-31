import { apiClient } from "./apiClient";
import type {
  CourseDocument,
  DocumentUploadResponse,
} from "../types/document";

export async function getDocuments(
  courseId?: number,
): Promise<CourseDocument[]> {
  const response = await apiClient.get<CourseDocument[]>("/api/documents", {
    params: courseId ? { courseId } : undefined,
  });
  return response.data;
}

export async function uploadDocument(
  courseId: number,
  file: File,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("courseId", String(courseId));
  formData.append("file", file);

  const response = await apiClient.post<DocumentUploadResponse>(
    "/api/documents",
    formData,
    {
      timeout: 120_000,
    },
  );

  return response.data;
}

export async function deleteDocument(documentId: number): Promise<void> {
  await apiClient.delete(`/api/documents/${documentId}`);
}
