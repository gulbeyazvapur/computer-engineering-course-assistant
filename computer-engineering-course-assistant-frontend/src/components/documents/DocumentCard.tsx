import { useState } from "react";
import { FileText, Trash2 } from "lucide-react";
import type { CourseDocument } from "../../types/document";
import { formatDate } from "../../utils/formatDate";
import ConfirmDialog from "../common/ConfirmDialog";
import { deleteDocument } from "../../services/documentService";
import { getErrorMessage } from "../../utils/getErrorMessage";

interface DocumentCardProps {
  document: CourseDocument;
  onDeleted: () => Promise<void> | void;
}

export default function DocumentCard({
  document,
  onDeleted,
}: DocumentCardProps) {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function openConfirm() {
    setError(null);
    setIsConfirmOpen(true);
  }

  function closeConfirm() {
    if (isDeleting) return;
    setIsConfirmOpen(false);
    setError(null);
  }

  async function handleConfirmDelete() {
    setIsDeleting(true);
    setError(null);

    try {
      await deleteDocument(document.id);
      setIsConfirmOpen(false);
      await onDeleted();
    } catch (err) {
      setError(getErrorMessage(err, "Kaynak silinemedi."));
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <>
      <article className="rounded-lg border border-warm-border bg-white p-4">
        <div className="flex gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-terracotta-soft text-terracotta">
            <FileText className="h-5 w-5" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <h3 className="truncate font-bold text-charcoal">
                {document.fileName}
              </h3>
              <button
                type="button"
                onClick={openConfirm}
                className="shrink-0 rounded-lg p-1.5 text-muted-warm transition hover:bg-red-50 hover:text-red-600"
                aria-label="Kaynağı sil"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-1 text-sm text-warm-gray">{document.courseName}</p>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-warm">
              <span>{document.chunkCount} chunk</span>
              <span>{formatDate(document.createdAt)}</span>
            </div>
          </div>
        </div>
      </article>

      <ConfirmDialog
        isOpen={isConfirmOpen}
        title="Kaynağı sil"
        message="Bu kaynağı silmek istediğinize emin misiniz?"
        detail="Kaynak ve kaynağa ait indekslenmiş veriler kalıcı olarak silinecek."
        itemName={document.fileName}
        confirmLabel="Kaynağı Sil"
        isConfirming={isDeleting}
        error={error}
        onConfirm={() => void handleConfirmDelete()}
        onCancel={closeConfirm}
      />
    </>
  );
}
