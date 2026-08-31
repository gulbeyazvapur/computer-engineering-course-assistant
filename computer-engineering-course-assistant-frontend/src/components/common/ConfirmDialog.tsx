import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import Button from "./Button";
import Alert from "./Alert";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  detail?: string;
  itemName?: string;
  confirmLabel: string;
  cancelLabel?: string;
  isConfirming?: boolean;
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  detail,
  itemName,
  confirmLabel,
  cancelLabel = "İptal",
  isConfirming = false,
  error,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isConfirming) {
        onCancel();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isConfirming, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal/50 p-4"
      onClick={() => {
        if (!isConfirming) onCancel();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-sm rounded-lg border border-warm-border bg-white p-6 shadow-sm"
      >
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-50 text-red-600">
          <AlertTriangle className="h-5 w-5" />
        </div>

        <h2
          id="confirm-dialog-title"
          className="mt-4 text-lg font-bold text-charcoal"
        >
          {title}
        </h2>

        {itemName && (
          <p className="mt-3 truncate rounded-lg bg-cream-soft px-3 py-2 text-sm font-semibold text-charcoal">
            {itemName}
          </p>
        )}

        <p id="confirm-dialog-description" className="mt-3 text-sm text-warm-gray">
          {message}
        </p>
        {detail && <p className="mt-1 text-sm text-muted-warm">{detail}</p>}

        {error && (
          <div className="mt-3">
            <Alert kind="error">{error}</Alert>
          </div>
        )}

        <div className="mt-6 flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={isConfirming}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant="danger"
            onClick={onConfirm}
            disabled={isConfirming}
          >
            {isConfirming ? "Siliniyor..." : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
