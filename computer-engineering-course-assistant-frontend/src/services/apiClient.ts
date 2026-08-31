import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 30_000,
  headers: {
    Accept: "application/json",
  },
});
