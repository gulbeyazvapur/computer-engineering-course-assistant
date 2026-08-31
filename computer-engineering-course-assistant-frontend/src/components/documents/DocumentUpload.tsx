import { useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  LoaderCircle,
  Upload,
} from "lucide-react";
import type { Course } from "../../types/course";
import Button from "../common/Button";
import Alert from "../common/Alert";
import { uploadDocument } from "../../services/documentService";
import { validatePdfFile } from "../../utils/fileValidation";
import { getErrorMessage } from "../../utils/getErrorMessage";

interface DocumentUploadProps {
  courses: Course[];
  onUploaded: () => Promise<void> | void;
}

type UploadStatus = "pending" | "uploading" | "success" | "error";

interface UploadItem {
  id: string;
  file: File;
  status: UploadStatus;
  error?: string;
}

const statusLabel: Record<UploadStatus, string> = {
  pending: "Bekliyor",
  uploading: "Yükleniyor...",
  success: "Başarılı",
  error: "Başarısız",
};

const statusColor: Record<UploadStatus, string> = {
  pending: "text-muted-warm",
  uploading: "text-terracotta",
  success: "text-olive-hover",
  error: "text-red-600",
};

function StatusIcon({ status }: { status: UploadStatus }) {
  const className = "h-3.5 w-3.5";
  switch (status) {
    case "uploading":
      return <LoaderCircle className={`${className} animate-spin`} />;
    case "success":
      return <CheckCircle2 className={className} />;
    case "error":
      return <AlertCircle className={className} />;
    default:
      return <Clock className={className} />;
  }
}

function formatFileSize(bytes: number): string {
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function fileKey(file: File): string {
  return `${file.name}|${file.size}|${file.lastModified}`;
}

export default function DocumentUpload({
  courses,
  onUploaded,
}: DocumentUploadProps) {
  const [courseId, setCourseId] = useState<number | null>(null);
  const [items, setItems] = useState<UploadItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [courseError, setCourseError] = useState<string | null>(null);
  const [summary, setSummary] = useState<{
    text: string;
    kind: "success" | "error" | "info";
  } | null>(null);

  function handleFilesSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files ?? []);
    const seen = new Set<string>();
    const nextItems: UploadItem[] = [];

    for (const file of selected) {
      const key = fileKey(file);
      if (seen.has(key)) continue;
      seen.add(key);

      const validationError = validatePdfFile(file);
      nextItems.push({
        id: key,
        file,
        status: validationError ? "error" : "pending",
        error: validationError ?? undefined,
      });
    }

    setItems(nextItems);
    setSummary(null);
    setCourseError(null);
  }

  function updateItem(id: string, patch: Partial<UploadItem>) {
    setItems((current) =>
      current.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    );
  }

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();

    if (isUploading) return;

    if (!courseId) {
      setCourseError("Lütfen önce bir ders seçin.");
      return;
    }

    if (items.length === 0) return;

    setCourseError(null);
    setSummary(null);
    setIsUploading(true);

    // Sequential on purpose -- the embedding model uses local GPU memory
    // during ingestion, so uploads must not run concurrently (see
    // rag_service's GPU model swapping: Promise.all here would compete for
    // the same GPU resource this backend serializes).
    let successCount = 0;
    let failureCount = 0;

    for (const item of items) {
      if (item.status === "error") {
        // Already flagged by client-side validation (e.g. oversized file);
        // don't waste a request on it, but it still counts as a failure.
        failureCount += 1;
        continue;
      }

      updateItem(item.id, { status: "uploading", error: undefined });

      try {
        await uploadDocument(courseId, item.file);
        successCount += 1;
        updateItem(item.id, { status: "success" });
      } catch (err) {
        failureCount += 1;
        updateItem(item.id, {
          status: "error",
          error: getErrorMessage(err, "Doküman yüklenemedi."),
        });
      }
    }

    setIsUploading(false);

    if (failureCount === 0) {
      setSummary({
        text: `${successCount} doküman başarıyla işlendi.`,
        kind: "success",
      });
    } else if (successCount === 0) {
      setSummary({ text: "Dokümanlar yüklenemedi.", kind: "error" });
    } else {
      setSummary({
        text: `${successCount} doküman başarıyla işlendi, ${failureCount} doküman yüklenemedi.`,
        kind: "info",
      });
    }

    // Successful files drop out of the list; failed ones stay so the user
    // can retry without reselecting them. The native input is reset either
    // way -- retry uses this component's own state, not input.files.
    setItems((current) => current.filter((item) => item.status !== "success"));

    const input = document.getElementById(
      "document-file",
    ) as HTMLInputElement | null;
    if (input) input.value = "";

    if (successCount > 0) {
      await onUploaded();
    }
  }

  const uploadLabel = items.length === 1 ? "Dokümanı Yükle" : "Dokümanları Yükle";

  return (
    <form
      onSubmit={(event) => void handleUpload(event)}
      className="rounded-lg border border-warm-border bg-white p-5"
    >
      <div className="mb-5">
        <h2 className="font-bold text-charcoal">PDF Yükle</h2>
        <p className="mt-1 text-sm leading-6 text-warm-gray">
          Backend PDF’yi metne dönüştürür, chunk’lara ayırır ve embedding’leri
          yerel bilgi tabanına kaydeder.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label
            htmlFor="document-course"
            className="mb-1.5 block text-sm font-semibold text-charcoal"
          >
            Ders
          </label>
          <select
            id="document-course"
            value={courseId ?? ""}
            onChange={(event) =>
              setCourseId(event.target.value ? Number(event.target.value) : null)
            }
            disabled={isUploading}
            className="w-full rounded-lg border border-warm-border bg-white px-3 py-2.5 text-sm text-charcoal outline-none focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 disabled:bg-cream-soft"
          >
            <option value="">Ders seçin</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            htmlFor="document-file"
            className="mb-1.5 block text-sm font-semibold text-charcoal"
          >
            PDF
          </label>
          <input
            id="document-file"
            type="file"
            multiple
            accept=".pdf,application/pdf"
            onChange={handleFilesSelected}
            disabled={isUploading}
            className="block w-full rounded-lg border border-warm-border bg-white px-3 py-2.5 text-sm text-charcoal file:mr-3 file:rounded-md file:border-0 file:bg-terracotta-soft file:px-3 file:py-1.5 file:font-semibold file:text-terracotta disabled:opacity-60"
          />
          <p className="mt-1 text-xs text-muted-warm">
            Aynı anda birden fazla PDF seçebilirsiniz. Dosya başına maksimum 20 MB.
          </p>
        </div>

        {items.length > 0 && (
          <div className="rounded-lg border border-warm-border bg-cream-soft p-2">
            <ul className="max-h-48 space-y-1 overflow-y-auto">
              {items.map((item) => (
                <li
                  key={item.id}
                  className="flex items-center justify-between gap-2 rounded-lg bg-white px-3 py-2"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-charcoal">
                      {item.file.name}
                    </p>
                    <p className="text-xs text-muted-warm">
                      {formatFileSize(item.file.size)}
                    </p>
                    {item.status === "error" && item.error && (
                      <p className="mt-0.5 truncate text-xs text-red-600">
                        {item.error}
                      </p>
                    )}
                  </div>
                  <span
                    className={`flex shrink-0 items-center gap-1 text-xs font-medium ${statusColor[item.status]}`}
                  >
                    <StatusIcon status={item.status} />
                    {statusLabel[item.status]}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {courseError && <Alert kind="error">{courseError}</Alert>}
        {summary && <Alert kind={summary.kind}>{summary.text}</Alert>}

        <Button
          type="submit"
          disabled={isUploading || courses.length === 0 || items.length === 0}
          className="w-full"
        >
          <Upload className="h-4 w-4" />
          {isUploading ? "Yükleniyor..." : uploadLabel}
        </Button>
      </div>
    </form>
  );
}
