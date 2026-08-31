import { useState } from "react";
import Alert from "../components/common/Alert";
import Loader from "../components/common/Loader";
import DocumentFilter from "../components/documents/DocumentFilter";
import DocumentList from "../components/documents/DocumentList";
import DocumentUpload from "../components/documents/DocumentUpload";
import { useCourses } from "../hooks/useCourses";
import { useDocuments } from "../hooks/useDocuments";

export default function DocumentsPage() {
  const [filterCourseId, setFilterCourseId] = useState<number | undefined>();

  const {
    courses,
    isLoading: coursesLoading,
    error: coursesError,
  } = useCourses();

  const {
    documents,
    isLoading: documentsLoading,
    error: documentsError,
    refreshDocuments,
  } = useDocuments(filterCourseId);

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-charcoal">Kaynaklar</h2>
        <p className="mt-1 text-sm text-warm-gray">
          RAG bilgi tabanına eklenen PDF ders materyallerini görüntüleyin.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-4">
          <DocumentFilter
            courses={courses}
            value={filterCourseId}
            onChange={setFilterCourseId}
          />

          {coursesError && <Alert kind="error">{coursesError}</Alert>}
          {documentsError && <Alert kind="error">{documentsError}</Alert>}

          {documentsLoading ? (
            <Loader label="Dokümanlar yükleniyor..." />
          ) : (
            <DocumentList
              documents={documents}
              onDeleted={refreshDocuments}
            />
          )}
        </div>

        {coursesLoading ? (
          <div className="rounded-lg border border-warm-border bg-white p-5">
            <Loader label="Dersler hazırlanıyor..." />
          </div>
        ) : (
          <DocumentUpload
            courses={courses}
            onUploaded={refreshDocuments}
          />
        )}
      </div>
    </section>
  );
}
