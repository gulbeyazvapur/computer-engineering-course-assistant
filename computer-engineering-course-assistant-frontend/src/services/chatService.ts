import { apiClient } from "./apiClient";
import type { ChatRequest, ChatResponse } from "../types/chat";

export async function sendQuestion(
  payload: ChatRequest,
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>("/api/chat", payload, {
    timeout: 180_000,
  });
  return response.data;
}
