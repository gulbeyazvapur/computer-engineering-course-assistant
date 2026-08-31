export interface CourseDocument {
  id: number;
  courseId: number;
  courseName: string;
  fileName: string;
  chunkCount: number;
  createdAt: string;
}

export interface DocumentUploadResponse {
  id: number;
  courseId: number;
  fileName: string;
  chunkCount: number;
  message: string;
}
