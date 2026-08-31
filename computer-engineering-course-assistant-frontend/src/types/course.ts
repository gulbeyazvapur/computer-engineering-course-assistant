export interface Course {
  id: number;
  name: string;
  description?: string | null;
  createdAt?: string | null;
  documentCount?: number;
}

export interface CourseCreateRequest {
  name: string;
  description?: string;
}

export type CourseUpdateRequest = CourseCreateRequest;
