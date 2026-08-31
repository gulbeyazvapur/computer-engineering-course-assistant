import { Send } from "lucide-react";
import Button from "../common/Button";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
}: ChatInputProps) {
  return (
    <div className="flex items-end gap-3 border-t border-warm-border bg-white p-4">
      <div className="flex-1">
        <label htmlFor="chat-question" className="sr-only">
          Sorunuz
        </label>
        <textarea
          id="chat-question"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault();
              onSubmit();
            }
          }}
          disabled={disabled}
          rows={2}
          placeholder="Ders materyalleriyle ilgili sorunuzu yazın..."
          className="max-h-40 min-h-12 w-full resize-y rounded-lg border border-warm-border px-3 py-3 text-sm text-charcoal outline-none transition placeholder:text-muted-warm focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 disabled:bg-cream-soft"
        />
        <p className="mt-1 text-xs text-muted-warm">
          Enter: gönder • Shift + Enter: yeni satır
        </p>
      </div>

      <Button
        type="button"
        onClick={onSubmit}
        disabled={disabled || !value.trim()}
        className="h-12 px-4"
        aria-label="Soruyu gönder"
      >
        <Send className="h-4 w-4" />
        <span className="hidden sm:inline">Gönder</span>
      </Button>
    </div>
  );
}
