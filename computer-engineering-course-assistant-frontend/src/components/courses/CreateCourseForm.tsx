import { useState } from "react";
import { Plus } from "lucide-react";
import Button from "../common/Button";
import Alert from "../common/Alert";
import { createCourse } from "../../services/courseService";
import { getErrorMessage } from "../../utils/getErrorMessage";

interface CreateCourseFormProps {
  onCreated: () => Promise<void> | void;
}

export default function CreateCourseForm({
  onCreated,
}: CreateCourseFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!name.trim()) {
      setError("Ders adı boş bırakılamaz.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await createCourse({
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setName("");
      setDescription("");
      setSuccess("Ders başarıyla oluşturuldu.");
      await onCreated();
    } catch (err) {
      setError(getErrorMessage(err, "Ders oluşturulamadı."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-warm-border bg-white p-5"
    >
      <div className="mb-5">
        <h2 className="font-bold text-charcoal">Yeni Ders</h2>
        <p className="mt-1 text-sm text-warm-gray">
          Dokümanları ilişkilendirmek için önce ders oluşturabilirsiniz.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label
            htmlFor="course-name"
            className="mb-1.5 block text-sm font-semibold text-charcoal"
          >
            Ders adı
          </label>
          <input
            id="course-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={150}
            placeholder="Örn. Bilgisayar Ağları"
            className="w-full rounded-lg border border-warm-border px-3 py-2.5 text-sm text-charcoal outline-none placeholder:text-muted-warm focus:border-terracotta focus:ring-2 focus:ring-terracotta/10"
          />
        </div>

        <div>
          <label
            htmlFor="course-description"
            className="mb-1.5 block text-sm font-semibold text-charcoal"
          >
            Açıklama
          </label>
          <textarea
            id="course-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={3}
            maxLength={1000}
            placeholder="Ders materyallerinin kısa açıklaması"
            className="w-full resize-y rounded-lg border border-warm-border px-3 py-2.5 text-sm text-charcoal outline-none placeholder:text-muted-warm focus:border-terracotta focus:ring-2 focus:ring-terracotta/10"
          />
        </div>

        {error && <Alert kind="error">{error}</Alert>}
        {success && <Alert kind="success">{success}</Alert>}

        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full"
        >
          <Plus className="h-4 w-4" />
          {isSubmitting ? "Oluşturuluyor..." : "Ders Oluştur"}
        </Button>
      </div>
    </form>
  );
}
