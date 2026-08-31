import { useCallback, useEffect, useState } from "react";
import { getCourses } from "../services/courseService";
import type { Course } from "../types/course";
import { getErrorMessage } from "../utils/getErrorMessage";

export function useCourses() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      setCourses(await getCourses());
    } catch (err) {
      setError(getErrorMessage(err, "Dersler yüklenemedi."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshCourses();
  }, [refreshCourses]);

  return {
    courses,
    isLoading,
    error,
    refreshCourses,
  };
}
