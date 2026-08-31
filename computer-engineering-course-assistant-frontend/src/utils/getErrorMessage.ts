import axios from "axios";
import type { ApiErrorPayload } from "../types/api";

export function getErrorMessage(
  error: unknown,
  fallback = "Beklenmeyen bir hata oluştu.",
): string {
  if (axios.isAxiosError<ApiErrorPayload>(error)) {
    if (!error.response) {
      return "Yerel sunucuya bağlanılamadı. Backend uygulamasının çalıştığından emin olun.";
    }

    const payload = error.response.data;
    if (payload?.message && typeof payload.message === "string") {
      return payload.message;
    }

    if (typeof payload?.detail === "string") {
      return payload.detail;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}
