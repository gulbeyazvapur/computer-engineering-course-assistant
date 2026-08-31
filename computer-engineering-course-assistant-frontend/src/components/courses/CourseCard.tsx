import { useState } from "react";
import { BookOpen, FileText, Pencil, Trash2 } from "lucide-react";
import type { Course } from "../../types/course";
import Button from "../common/Button";
import Alert from "../common/Alert";
import ConfirmDialog from "../common/ConfirmDialog";
import { deleteCourse, updateCourse } from "../../services/courseService";
import { getErrorMessage } from "../../utils/getErrorMessage";

interface CourseCardProps {
  course: Course;
  onChanged: () => Promise<void> | void;
}

export default function CourseCard({ course, onChanged }: CourseCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(course.name);
  const [description, setDescription] = useState(course.description ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  function startEditing() {
    setName(course.name);
    setDescription(course.description ?? "");
    setError(null);
    setIsEditing(true);
  }

  async function handleSave() {
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Ders adı boş bırakılamaz.");
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      await updateCourse(course.id, {
        name: trimmed,
        description: description.trim() || undefined,
      });
      setIsEditing(false);
      await onChanged();
    } catch (err) {
      setError(getErrorMessage(err, "Ders güncellenemedi."));
    } finally {
      setIsSaving(false);
    }
  }

  function openConfirm() {
    setDeleteError(null);
    setIsConfirmOpen(true);
  }

  function closeConfirm() {
    if (isDeleting) return;
    setIsConfirmOpen(false);
    setDeleteError(null);
  }

  async function handleConfirmDelete() {
    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deleteCourse(course.id);
      setIsConfirmOpen(false);
      await onChanged();
    } catch (err) {
      setDeleteError(getErrorMessage(err, "Ders silinemedi."));
    } finally {
      setIsDeleting(false);
    }
  }

  if (isEditing) {
    return (
      <article className="rounded-lg border border-warm-border bg-white p-5">
        <div className="space-y-3">
          <div>
            <label
              htmlFor={`course-name-${course.id}`}
              className="mb-1.5 block text-sm font-semibold text-charcoal"
            >
              Ders adı
            </label>
            <input
              id={`course-name-${course.id}`}
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={150}
              className="w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-charcoal outline-none focus:border-terracotta focus:ring-2 focus:ring-terracotta/10"
            />
          </div>

          <div>
            <label
              htmlFor={`course-description-${course.id}`}
              className="mb-1.5 block text-sm font-semibold text-charcoal"
            >
              Açıklama
            </label>
            <textarea
              id={`course-description-${course.id}`}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={2}
              maxLength={1000}
              className="w-full resize-y rounded-lg border border-warm-border px-3 py-2 text-sm text-charcoal outline-none focus:border-terracotta focus:ring-2 focus:ring-terracotta/10"
            />
          </div>

          {error && <Alert kind="error">{error}</Alert>}

          <div className="flex gap-2">
            <Button type="button" onClick={() => void handleSave()} disabled={isSaving}>
              {isSaving ? "Kaydediliyor..." : "Kaydet"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsEditing(false);
                setError(null);
              }}
              disabled={isSaving}
            >
              İptal
            </Button>
          </div>
        </div>
      </article>
    );
  }

  return (
    <>
      <article className="rounded-lg border border-warm-border bg-white p-5">
        <div className="mb-4 flex items-start justify-between">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-terracotta-soft text-terracotta">
            <BookOpen className="h-5 w-5" />
          </div>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={startEditing}
              className="rounded-lg p-1.5 text-muted-warm transition hover:bg-cream-soft hover:text-charcoal"
              aria-label="Dersi düzenle"
            >
              <Pencil className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={openConfirm}
              className="rounded-lg p-1.5 text-muted-warm transition hover:bg-red-50 hover:text-red-600"
              aria-label="Dersi sil"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>

        <h3 className="font-bold text-charcoal">{course.name}</h3>
        <p className="mt-2 text-sm leading-6 text-warm-gray">
          {course.description || "Bu ders için açıklama eklenmemiş."}
        </p>

        {typeof course.documentCount === "number" && (
          <p className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-warm-border px-2.5 py-1 text-xs font-medium text-warm-gray">
            <FileText className="h-3.5 w-3.5" />
            {course.documentCount} kaynak
          </p>
        )}
      </article>

      <ConfirmDialog
        isOpen={isConfirmOpen}
        title="Dersi sil"
        message="Bu dersi silmek istediğinize emin misiniz?"
        detail="Bu ders ve derse ait tüm kaynaklar kalıcı olarak silinecek."
        itemName={course.name}
        confirmLabel="Dersi Sil"
        isConfirming={isDeleting}
        error={deleteError}
        onConfirm={() => void handleConfirmDelete()}
        onCancel={closeConfirm}
      />
    </>
  );
}
