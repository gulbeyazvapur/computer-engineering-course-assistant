export interface Source {
  documentName: string;
  chunkIndex?: number;
}

export interface ChatRequest {
  question: string;
  courseId: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

export type MessageRole = "user" | "assistant";

export interface ChatMessageModel {
  id: string;
  role: MessageRole;
  content: string;
  sources?: Source[];
}
