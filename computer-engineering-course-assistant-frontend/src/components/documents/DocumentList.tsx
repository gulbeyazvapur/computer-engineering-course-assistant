import type { CourseDocument } from "../../types/document";
import DocumentCard from "./DocumentCard";

interface DocumentListProps {
  documents: CourseDocument[];
  onDeleted: () => Promise<void> | void;
}

export default function DocumentList({
  documents,
  onDeleted,
}: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-warm-border bg-white p-10 text-center text-sm text-warm-gray">
        Henüz doküman bulunmuyor.
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {documents.map((document) => (
        <DocumentCard
          key={document.id}
          document={document}
          onDeleted={onDeleted}
        />
      ))}
    </div>
  );
}
