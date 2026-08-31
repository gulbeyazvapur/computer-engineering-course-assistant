import { useCallback, useEffect, useState } from "react";
import { getDocuments } from "../services/documentService";
import type { CourseDocument } from "../types/document";
import { getErrorMessage } from "../utils/getErrorMessage";

export function useDocuments(courseId?: number) {
  const [documents, setDocuments] = useState<CourseDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      setDocuments(await getDocuments(courseId));
    } catch (err) {
      setError(getErrorMessage(err, "Dokümanlar yüklenemedi."));
    } finally {
      setIsLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    void refreshDocuments();
  }, [refreshDocuments]);

  return {
    documents,
    isLoading,
    error,
    refreshDocuments,
  };
}
